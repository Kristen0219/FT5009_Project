"""Verify saved sources against checksums and exact CSV extraction."""
import csv,json,hashlib
from collections import Counter
from pathlib import Path
from parse_history import extract
ROOT=Path(__file__).resolve().parent

def main():
 manifest=json.loads((ROOT/'download_manifest_combined.json').read_text())
 saved=list(csv.DictReader((ROOT/'flows_extracted.csv').open()))
 expected=[];skipped=[]
 for r in manifest:
  if r['download_status']!='downloaded':skipped.append(r['report_id']);continue
  assert hashlib.sha256((ROOT/r['local_file']).read_bytes()).hexdigest()==r['sha256'],r['report_id']
  try:rows,*_=extract(r);expected.extend(rows)
  except Exception:skipped.append(r['report_id'])
 key=lambda r:(r['report_id'],r['investor'],r['side'],int(r['rank']))
 canon=lambda r:{k:str(v) for k,v in r.items()}
 assert sorted(map(canon,expected),key=key)==sorted(saved,key=key),'CSV differs from source re-extraction'
 counts=Counter(r['report_id'] for r in saved)
 assert all(n==40 for n in counts.values())
 assert len({key(r) for r in saved})==len(saved)
 print('Verified source checksums:',sum(r['download_status']=='downloaded' for r in manifest))
 print('Verified exact signal rows:',len(saved),'reports:',len(counts),'manual review:',len(skipped))
if __name__=='__main__':main()
