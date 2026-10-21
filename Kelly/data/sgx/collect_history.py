"""Download observed SGX archive links; no guessed URLs. Resume by content checks."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,date
import csv,json,urllib.request,urllib.parse,hashlib,time
ROOT=Path(__file__).resolve().parent

def inventory():
 rows=json.loads((ROOT/'archive_all.json').read_text())
 supplement=ROOT/'supplementary_weekly_reports.json'
 if supplement.exists():rows+=json.loads(supplement.read_text())
 selected=[];excluded=[]
 for r in rows:
  r=r.copy();d=datetime.strptime(r['publication_date'],'%d %b %Y').date()
  r['publication_date']=d.isoformat()
  if not date(2019,1,1)<=d<=date(2026,9,30):r['reason']='outside_release_window';excluded.append(r);continue
  if 'week' not in r['title'].lower() or 'flow' not in r['title'].lower():r['reason']='not_weekly_fund_flow';excluded.append(r);continue
  r['report_id']='SGX_'+hashlib.sha256(r['url'].encode()).hexdigest()[:12]
  r['local_file']='raw/'+r['report_id']+Path(urllib.parse.urlparse(r['url']).path).suffix
  selected.append(r)
 (ROOT/'excluded_archive_entries.json').write_text(json.dumps(excluded,indent=2))
 return selected

def download(r):
 p=ROOT/r['local_file'];p.parent.mkdir(exist_ok=True)
 try:
  if not p.exists():
   req=urllib.request.Request(r['url'],headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=25) as f:b=f.read()
   if not b.startswith((b'PK',b'%PDF')):raise ValueError('Unexpected content; not workbook/PDF')
   p.write_bytes(b)
  b=p.read_bytes();r.update(download_status='downloaded',sha256=hashlib.sha256(b).hexdigest(),size_bytes=len(b))
 except Exception as e:r.update(download_status='failed',download_error=str(e))
 return r

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--reverse',action='store_true');a=p.parse_args()
 rows=inventory();rows=rows[::-1] if a.reverse else rows
 manifest_name='download_manifest_reverse.json' if a.reverse else 'download_manifest.json';print('Eligible archive entries:',len(rows),flush=True);out=[]
 with ThreadPoolExecutor(max_workers=6) as ex:
  futures=[ex.submit(download,r) for r in rows]
  for f in as_completed(futures):
   out.append(f.result())
   if len(out)%25==0:print('Downloaded/attempted',len(out),'failures',sum(x['download_status']=='failed' for x in out),flush=True)
   (ROOT/manifest_name).write_text(json.dumps(sorted(out,key=lambda r:r['publication_date']),indent=2))
 print('Finished:',len(out),'Failed:',sum(x['download_status']=='failed' for x in out),flush=True)
if __name__=='__main__':main()
