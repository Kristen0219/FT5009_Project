"""Fetch Yahoo chart data for explicit candidate symbols; retain errors/provenance.
SGX code + .SI is a CANDIDATE mapping, not verified historical security identity.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import urllib.request,urllib.parse,urllib.error,json,time,csv,threading,argparse,hashlib
ROOT=Path(__file__).resolve().parent
START=int(datetime(2016,1,1,tzinfo=timezone.utc).timestamp())
END=int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp())
stop=threading.Event()

def fetch(symbol):
 path=ROOT/'raw'/(symbol.replace('^','INDEX_').replace('=','_')+'.json')
 url='https://query2.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol,safe='')+'?'+urllib.parse.urlencode(dict(period1=START,period2=END,interval='1d',events='div,splits',includeAdjustedClose='true'))
 receipt=dict(symbol=symbol,source_url=url,retrieved_date='2026-10-21',local_file=str(path.relative_to(ROOT)),status='pending')
 try:
  if path.exists():body=path.read_bytes()
  else:
   if stop.is_set():receipt['status']='not_attempted_after_rate_limit';return receipt
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=30) as r:body=r.read()
  data=json.loads(body);error=data.get('chart',{}).get('error')
  if error:raise ValueError(str(error))
  result=data['chart']['result'][0]
  if not result.get('timestamp'):raise ValueError('No price timestamps')
  if not path.exists():path.write_bytes(body)
  receipt.update(status='downloaded',sha256=hashlib.sha256(body).hexdigest(),rows=len(result['timestamp']),currency=result['meta'].get('currency'),vendor_name=result['meta'].get('longName',result['meta'].get('shortName')),exchange=result['meta'].get('exchangeName'))
 except urllib.error.HTTPError as e:
  receipt.update(status='http_error',http_status=e.code,error=str(e),retry_after=e.headers.get('Retry-After'))
  if e.code==429:stop.set()
 except Exception as e:receipt.update(status='error',error=str(e))
 finally:
  if receipt['status']!='pending':
   (ROOT/'receipts'/(path.stem+'.json')).write_text(json.dumps(receipt,indent=2))
 return receipt

def main():
 p=argparse.ArgumentParser();p.add_argument('--symbols',nargs='*');p.add_argument('--workers',type=int,default=4);a=p.parse_args()
 codes=list(csv.DictReader((ROOT/'security_codes_to_map.csv').open()))
 symbols=a.symbols or sorted({r['sgx_code']+'.SI' for r in codes}|{'ES3.SI','^STI'})
 print('Candidates:',len(symbols),flush=True)
 results=[]
 with ThreadPoolExecutor(max_workers=a.workers) as ex:
  futures=[ex.submit(fetch,s) for s in symbols]
  for f in as_completed(futures):
   r=f.result();results.append(r)
   if len(results)%10==0 or r['status']!='downloaded':print(len(results),r['symbol'],r['status'],flush=True)
 # Merge with existing receipts; never silently discard failed/unattempted candidates.
 allreceipts=[json.loads(p.read_text()) for p in (ROOT/'receipts').glob('*.json')]
 (ROOT/'market_download_manifest.json').write_text(json.dumps(sorted(allreceipts,key=lambda x:x['symbol']),indent=2))
 print('Complete',dict((s,sum(r['status']==s for r in results)) for s in sorted({r['status'] for r in results})),flush=True)
if __name__=='__main__':main()
