"""Fetch metadata snapshots. Run with --enriched to include named call annotations."""
from pathlib import Path
import urllib.request,hashlib,argparse
BASE=Path(__file__).resolve().parents[1]/'data/raw'
BASE.mkdir(parents=True,exist_ok=True)
SOURCES={
 'annotations.csv':('https://raw.githubusercontent.com/JPalmerK/DCLDE_Dataset/2ceee82d0aeb0be45bf95e74806771f35be75f37/dclde_2026_dclde_2026_killer_whales_Annotations.csv','f9b5bca4d276cf46259063b9a0e5b47433b0123fa1cdb0e0b0a2766b4eb7ac88'),
 'enriched.csv':('https://storage.googleapis.com/esp-data-274503/dclde2026/v0.1.0/raw/2026/dclde_2026_killer_whales/processed_enriched_v2.csv','3f428d361008666c42369d471e12c8f05412057af547a42bdf5dd560e5912bf9')}
parser=argparse.ArgumentParser();parser.add_argument('--enriched',action='store_true');args=parser.parse_args()
for name,(url,expected) in SOURCES.items():
 if name=='enriched.csv' and not args.enriched:continue
 target=BASE/name;temp=target.with_suffix('.download')
 with urllib.request.urlopen(url,timeout=120) as response, temp.open('wb') as output:
  while block:=response.read(1024*1024):output.write(block)
 digest=hashlib.sha256(temp.read_bytes()).hexdigest()
 if digest!=expected:
  temp.unlink();raise SystemExit(f'{name}: upstream bytes changed. Expected {expected}, got {digest}. Review the new schema before updating this project; the previous snapshot was preserved.')
 temp.replace(target);print(name,digest)
print('Verified snapshots ready. Run python3 scripts/ingest.py.')
