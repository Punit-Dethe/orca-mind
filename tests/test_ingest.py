import unittest,sys,json,sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ingest import number,clean,valid_interval,transitions
ROOT=Path(__file__).resolve().parents[1]
class ParsingTests(unittest.TestCase):
 def test_missing_nonfinite_and_zero(self):
  self.assertIsNone(number('NA')); self.assertIsNone(number('nan'));self.assertEqual(number('0'),0); self.assertEqual(clean('NA'),'');self.assertEqual(clean('0'),'0')
 def test_intervals(self):
  self.assertTrue(valid_interval(0,2));self.assertFalse(valid_interval(-1,2));self.assertFalse(valid_interval(2,1));self.assertFalse(valid_interval(None,2))
 def test_sequence_omits_unknown_retains_overlap_and_stable_ties(self):
  def e(id,start,end,call,species='Killer whale'):return dict(id=id,start=start,end=end,call=call,species=species)
  data=[e('3',2,4,'B'),e('1',0,3,'A'),e('2',1,2,'Unknown'),e('4',2,5,'A'),e('5',7,8,'A','Humpback whale'),e('6',-1,1,'C')]
  pairs=transitions(data)
  self.assertEqual([(a['id'],b['id']) for a,b,_,_ in pairs],[('1','3'),('3','4')]);self.assertEqual(pairs[0][2:],(2,-1));self.assertEqual(pairs[1][2:],(0,-2))
@unittest.skipUnless((ROOT/'data/warehouse.sqlite').exists(),'Build the local warehouse for SQL integration tests')
class WarehouseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.db=sqlite3.connect(ROOT/'data/warehouse.sqlite')
 @classmethod
 def tearDownClass(cls):cls.db.close()
 def test_sources_are_separate_and_aggregates_conserve_rows(self):
  for source,expected in [('compiled',207574),('enriched',186972)]:
   d=json.loads((ROOT/f'dist/data/{source}/summary.json').read_text())
   n=self.db.execute('select count(*) from Fact_CallEvent where source=?',(source,)).fetchone()[0]
   self.assertEqual(n,expected);self.assertEqual(sum(r['count'] for r in d['cube']),n)
   self.assertEqual(sum(r['count'] for r in d['transitions']),self.db.execute('select count(*) from Fact_CallTransition where source=?',(source,)).fetchone()[0])
 def test_compiled_has_no_fabricated_call_types(self):
  self.assertEqual(self.db.execute('select count(*) from Fact_CallEvent where source="compiled" and call_type!=""').fetchone()[0],0)
  self.assertEqual(self.db.execute('select count(*) from Fact_CallTransition where source="compiled"').fetchone()[0],0)
 def test_recording_counts_and_buckets_match(self):
  for source in ['compiled','enriched']:
   rs=json.loads((ROOT/f'dist/data/{source}/recordings.json').read_text());self.assertEqual(sum(r['count'] for r in rs),self.db.execute('select count(*) from Fact_CallEvent where source=?',(source,)).fetchone()[0])
   for r in [rs[0],max(rs,key=lambda r:r['count']),rs[-1]]:
    bucket=json.loads((ROOT/f'dist/data/{source}/events-{r["id"]%64}.json').read_text());self.assertEqual(len(bucket[str(r['id'])]['events']),r['count'])
class PrecomputedTests(unittest.TestCase):
 def test_recording_cube_event_totals_match_for_each_source(self):
  for source in ['compiled','enriched']:
   d=json.loads((ROOT/f'dist/data/{source}/summary.json').read_text())
   rs=json.loads((ROOT/f'dist/data/{source}/recordings.json').read_text())
   self.assertEqual(sum(r['count'] for r in d['cube']),d['meta']['events'])
   self.assertEqual(sum(r['count'] for r in rs),d['meta']['events'])
   self.assertEqual(len(rs),d['meta']['recordings'])
   self.assertEqual(sum(p['count'] for p in d['transitions']),d['meta']['transition_pairs'])
 def test_original_csv_never_produces_named_calls(self):
  d=json.loads((ROOT/'dist/data/compiled/summary.json').read_text())
  self.assertTrue(all(not r['call'] for r in d['cube']))
  self.assertEqual(d['transitions'],[])
if __name__=='__main__':unittest.main()
