"""Deterministic metadata ETL. Standard library only; never downloads audio."""
import csv, json, math, hashlib, sqlite3, argparse, io
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(20_000_000)
SOURCE_URL='https://raw.githubusercontent.com/JPalmerK/DCLDE_Dataset/2ceee82d0aeb0be45bf95e74806771f35be75f37/dclde_2026_dclde_2026_killer_whales_Annotations.csv'

def clean(v):
    s=str(v or '').strip()
    return '' if s.lower() in ('na','nan','null','none') else s

def number(v):
    try:
        n=float(v)
        return n if math.isfinite(n) else None
    except (TypeError,ValueError): return None

def valid_interval(start,end):
    return start is not None and end is not None and start>=0 and end>=start

def transitions(events):
    """Typed killer whale events, sorted start then source row; unlabeled events omitted.
    Overlaps are retained with signed end-to-start gap. No maximum gap cutoff.
    """
    seq=sorted((e for e in events if e['species']=='Killer whale' and e['call'].lower() not in ('','unk','unknown') and valid_interval(e['start'],e['end'])),key=lambda e:(e['start'],e['id']))
    return [(a,b,round(b['start']-a['start'],6),round(b['start']-a['end'],6)) for a,b in zip(seq,seq[1:])]

def compiled(path):
    species={'KW':'Killer whale','HW':'Humpback whale','AB':'AB (source code)','UndBio':'Unknown biological'}
    with path.open() as f:
        for r in csv.DictReader(f):
            yield {'id':r[''],'recording':r['FilePath'],'name':r['Soundfile'],'provider':clean(r['Provider']),'population':clean(r['Ecotype']) or 'Unassigned','location':clean(r['Dataset']),'species':species.get(r['ClassSpecies'],r['ClassSpecies']),'class':r['ClassSpecies'],'call':'','start':number(r['FileBeginSec']),'end':number(r['FileEndSec']),'low':number(r['LowFreqHz']),'high':number(r['HighFreqHz']),'utc':clean(r['UTC']),'level':clean(r['AnnotationLevel']),'confidence':clean(r['KW_certain'])}

def enriched(path):
    with path.open() as f:
        for ri,r in enumerate(csv.DictReader(f)):
            for ei,a in enumerate(csv.DictReader(io.StringIO(r['selection_table']),delimiter='\t')):
                yield {'id':f'{ri}:{ei}','recording':r.get('audio_path') or f'manifest-{ri}','name':Path(r.get('audio_path','')).name,'provider':clean(r.get('provider')),'population':clean(a.get('ecotype')) or 'Unassigned','location':'Unavailable','species':clean(a.get('species')) or 'Unassigned','class':clean(a.get('species')) or 'Unassigned','call':clean(a.get('call_type')),'start':number(a.get('Begin Time (s)')),'end':number(a.get('End Time (s)')),'low':number(a.get('Low Freq (Hz)')),'high':number(a.get('High Freq (Hz)')),'utc':'','level':clean(a.get('annotation_level')),'confidence':clean(a.get('confidence'))}

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,separators=(',',':'),allow_nan=False))

def build(key,path,iterator,db):
    out=ROOT/'dist/data'/key
    events=list(iterator(path)); groups=defaultdict(list); nulls=Counter(); issues=Counter(); fingerprints=Counter()
    for e in events:
        groups[e['recording']].append(e)
        for k,v in e.items():
            if v is None or v=='' or v=='Unassigned': nulls[k]+=1
        if not valid_interval(e['start'],e['end']): issues['invalid_interval']+=1
        if e['low'] is not None and e['high'] is not None and (e['low']<0 or e['high']<e['low']): issues['invalid_frequency_bounds']+=1
        fp=tuple(e[k] for k in ('recording','start','end','species','call','population','level','low','high'))
        fingerprints[fp]+=1
    issues['duplicate_candidates']=sum(n-1 for n in fingerprints.values() if n>1)
    cubes={}; record_index=[]; buckets=[{} for _ in range(64)]; pairgroups={}; durations=[]
    db.execute('CREATE TABLE IF NOT EXISTS Fact_CallEvent (source TEXT, event_id TEXT, recording_id INTEGER, provider TEXT, population TEXT, location TEXT, species TEXT, call_type TEXT, start REAL, end REAL, duration REAL, low_hz REAL, high_hz REAL, utc TEXT, annotation_level TEXT, confidence TEXT, valid_interval INTEGER)')
    db.execute('CREATE TABLE IF NOT EXISTS Fact_CallTransition (source TEXT, recording_id INTEGER, from_event TEXT, to_event TEXT, from_call TEXT, to_call TEXT, start_spacing REAL, end_gap REAL, same_type INTEGER)')
    for rid,(recording,es) in enumerate(sorted(groups.items())):
        es.sort(key=lambda e:(e['start'] if e['start'] is not None else math.inf,e['id']))
        by_cube=defaultdict(list)
        for e in es:
            dur=round(e['end']-e['start'],6) if valid_interval(e['start'],e['end']) else None
            ck=tuple(e[k] for k in ('provider','population','location','species','call','level'))
            if ck not in cubes: cubes[ck]={'count':0,'recordings':set(),'durations':[]}
            c=cubes[ck]; c['count']+=1;c['recordings'].add(rid)
            if dur is not None: c['durations'].append(dur)
            db.execute('INSERT INTO Fact_CallEvent VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(key,e['id'],rid,e['provider'],e['population'],e['location'],e['species'],e['call'],e['start'],e['end'],dur,e['low'],e['high'],e['utc'],e['level'],e['confidence'],int(dur is not None)))
        pairs=transitions(es)
        for a,b,spacing,gap in pairs:
            pk=(a['provider'],a['population'],a['call'],b['call'])
            if pk not in pairgroups: pairgroups[pk]=[0,0,0]
            g=pairgroups[pk];g[0]+=1;g[1]+=spacing;g[2]+=int(gap<0)
            db.execute('INSERT INTO Fact_CallTransition VALUES (?,?,?,?,?,?,?,?,?)',(key,rid,a['id'],b['id'],a['call'],b['call'],spacing,gap,int(a['call']==b['call'])))
        end=max((e['end'] for e in es if e['end'] is not None),default=0)
        begin=min((e['start'] for e in es if e['start'] is not None),default=0)
        record_index.append({'id':rid,'name':es[0]['name'],'provider':es[0]['provider'],'populations':sorted({e['population'] for e in es}),'species':sorted({e['species'] for e in es}),'calls':sorted({e['call'] for e in es if e['call']}),'count':len(es),'begin':begin,'end':end,'typed':sum(bool(e['call']) and e['species']=='Killer whale' for e in es),'pairs':len(pairs),'invalid':sum(not valid_interval(e['start'],e['end']) for e in es),'location':es[0]['location']})
        buckets[rid%64][rid]={'path':recording,'provider':es[0]['provider'],'events':[[e[k] for k in ('id','start','end','species','call','population','level','low','high','utc','confidence')] for e in es]}
    cube_rows=[]
    for ck,c in cubes.items():
        ds=sorted(c['durations']); hist=[0]*8
        for d in ds:
            for j,upper in enumerate([.25,.5,1,2,5,10,30,math.inf]):
                if d<=upper:hist[j]+=1;break
        cube_rows.append(dict(zip(['provider','population','location','species','call','level'],ck),count=c['count'],recordings=sorted(c['recordings']),duration_count=len(ds),duration_sum=round(sum(ds),6),histogram=hist))
    raw_fields=list(next(csv.DictReader(path.open())).keys())
    selection_fields=[]
    if key=='enriched':
        with path.open() as f: selection_fields=list(next(csv.DictReader(io.StringIO(next(csv.DictReader(f))['selection_table']),delimiter='\t')).keys())
    meta={'key':key,'status':'Dataset-derived','source_url':SOURCE_URL if key=='compiled' else 'https://github.com/earthspecies/alp-data/blob/main/alp_data/datasets/dclde2026.py','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'selection_fields':selection_fields,'download_url':SOURCE_URL if key=='compiled' else 'https://storage.googleapis.com/esp-data-274503/dclde2026/v0.1.0/raw/2026/dclde_2026_killer_whales/processed_enriched_v2.csv','raw_bytes':path.stat().st_size,'events':len(events),'recordings':len(groups),'fields':raw_fields,'missing':dict(nulls),'issues':dict(issues),'transition_pairs':sum(v[0] for v in pairgroups.values()),'named_kw_events':sum(e['species']=='Killer whale' and e['call'].lower() not in ('','unk','unknown') for e in events),'utc_min':min((e['utc'] for e in events if e['utc']),default=None),'utc_max':max((e['utc'] for e in events if e['utc']),default=None),'etl':[{'step':'Extract original annotations','rows':len(events)},{'step':'Normalize missing-value tokens; preserve all rows','rows':len(events)},{'step':'Retain invalid intervals with quality flag','rows':len(events)},{'step':'Materialize event fact table','rows':len(events)},{'step':'Build eligible within-recording typed pairs','rows':sum(v[0] for v in pairgroups.values())}]}
    dump(out/'summary.json',{'meta':meta,'cube':cube_rows,'transitions':[dict(zip(['provider','population','from','to'],k),count=v[0],spacing_sum=round(v[1],6),overlaps=v[2]) for k,v in pairgroups.items()]})
    dump(out/'recordings.json',record_index)
    for i,b in enumerate(buckets):dump(out/f'events-{i}.json',b)
    dump(ROOT/'docs'/f'{key}-schema.json',meta)
    print(key,meta['events'],'events',meta['recordings'],'recordings',meta['transition_pairs'],'pairs',flush=True)
    return meta

def main():
    target=ROOT/'data/warehouse.sqlite';target.parent.mkdir(exist_ok=True)
    if target.exists():target.unlink()
    db=sqlite3.connect(target); metas=[]
    for key,file,fn in [('compiled','annotations.csv',compiled),('enriched','enriched.csv',enriched)]:
        path=ROOT/'data/raw'/file
        if path.exists():metas.append(build(key,path,fn,db))
    db.executescript('CREATE VIEW Dim_Recording AS SELECT DISTINCT source,recording_id,provider,location FROM Fact_CallEvent; CREATE VIEW Dim_CallType AS SELECT DISTINCT source,call_type FROM Fact_CallEvent WHERE call_type != ""; CREATE VIEW Dim_Population AS SELECT DISTINCT source,population FROM Fact_CallEvent; CREATE VIEW Dim_Provider AS SELECT DISTINCT source,provider FROM Fact_CallEvent; CREATE VIEW Dim_Location AS SELECT DISTINCT source,location FROM Fact_CallEvent; CREATE INDEX event_recording ON Fact_CallEvent(source,recording_id);')
    db.commit();db.close();dump(ROOT/'dist/data/catalog.json',metas)
    refs={}
    for f in ['EXPLORATORY_FINDINGS_RESULTS.json','PATTERN_FINDINGS_RESULTS.json']:
        refs[f]=json.loads((ROOT/'references'/f).read_text())
    dump(ROOT/'dist/data/reported.json',refs)
if __name__=='__main__':main()
