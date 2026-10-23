"""Targeted re-queries for observed missing benchmark bars; retain original responses."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor
import urllib.request,urllib.parse,json
ROOT=Path(__file__).resolve().parent

def fetch(task):
 symbol,day=task;d=datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
 u='https://query2.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol)+'?'+urllib.parse.urlencode(dict(period1=int((d-timedelta(days=3)).timestamp()),period2=int((d+timedelta(days=4)).timestamp()),interval='1d',events='div,splits',includeAdjustedClose='true'))
 name=f'{symbol}_{day}.json'
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:b=r.read()
  (ROOT/'repair_queries'/name).write_bytes(b)
  r=json.loads(b)['chart']['result'][0]
  vals=list(zip([datetime.fromtimestamp(t,timezone.utc).isoformat() for t in r['timestamp']],r['indicators']['quote'][0]['close'],r['indicators']['adjclose'][0]['adjclose']))
  return dict(symbol=symbol,gap_date=day,source_url=u,local_file='repair_queries/'+name,bars=vals)
 except Exception as e:return dict(symbol=symbol,gap_date=day,error=str(e),source_url=u)
if __name__=='__main__':
 tasks=[('ES3.SI','2025-10-24'),('ES3.SI','2026-08-21'),('G3B.SI','2025-10-24')]
 with ThreadPoolExecutor(max_workers=2) as ex:r=list(ex.map(fetch,tasks))
 (ROOT/'benchmark_gap_requery_results.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
