"""Reconstruct an ETF NAV total-return proxy from issuer NAVs and distributions.
This is not the STI total-return index or a market-price ETF return series.
"""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as E
from datetime import datetime,date
import csv,json,hashlib
ROOT=Path(__file__).resolve().parent
NAV_URL='https://www.ssga.com/library-content/products/fund-data/etfs/apac/navhist-sg-en-es3.xlsx'
DIST_URL='https://www.ssga.com/sg/en/institutional/etfs/state-street-spdr-straits-times-index-etf-es3'
DIST=[('2016-01-29',.051),('2016-07-29',.042),('2017-02-02',.053),('2017-07-28',.048),('2018-02-01',.053),('2018-08-02',.06),('2019-02-04',.056),('2019-08-05',.064),('2020-02-10',.056),('2020-08-11',.059),('2021-02-09',.04),('2021-08-11',.043),('2022-02-11',.051),('2022-08-11',.061),('2023-02-10',.06),('2023-08-11',.073),('2024-02-13',.073),('2024-08-13',.086),('2025-02-12',.091),('2025-08-12',.089),('2026-02-11',.085),('2026-08-13',.093)]

def main():
 p=ROOT/'raw/ES3_official_nav_history.xlsx';n={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 with ZipFile(p) as z:
  ss=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml'))]
  rows=E.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//m:sheetData/m:row',n);nav={}
  for r in rows:
   cells={}
   for c in r.findall('m:c',n):
    v=c.find('m:v',n)
    if v is not None:cells[''.join(a for a in c.attrib['r'] if a.isalpha())]=ss[int(v.text)] if c.attrib.get('t')=='s' else v.text
   try:d=datetime.strptime(cells['A'],'%d-%b-%Y').date()
   except (KeyError,ValueError):continue
   if date(2016,1,1)<=d<=date(2026,9,30):
    if d.isoformat() in nav:raise ValueError('Duplicate issuer NAV date')
    nav[d.isoformat()]=float(cells['B'])
 dividends=dict(DIST)
 missing=[d for d in dividends if d not in nav]
 if missing:raise ValueError('Distribution ex-dates not in issuer NAV calendar: '+str(missing))
 chain=100.;previous=None;result=[]
 for d,v in sorted(nav.items()):
  if v<=0:raise ValueError('Nonpositive NAV')
  div=dividends.get(d,0);ret=(v+div)/previous-1 if previous is not None else None
  if ret is not None:chain*=1+ret
  result.append(dict(date=d,total_return_index=chain,daily_return=ret,nav_sgd=v,distribution_sgd=div,benchmark='ES3 issuer NAV total-return proxy',source_url=NAV_URL,distribution_source_url=DIST_URL))
  previous=v
 with (ROOT/'benchmark_official_es3_nav_total_return.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=result[0].keys());w.writeheader();w.writerows(result)
 with (ROOT/'official_es3_distributions.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['ex_dividend_date','distribution_sgd','source_url']);w.writeheader();w.writerows(dict(ex_dividend_date=d,distribution_sgd=a,source_url=DIST_URL) for d,a in DIST)
 summary=dict(source_url=NAV_URL,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),distribution_source_url=DIST_URL,distribution_rows=len(DIST),
  observations=len(result),first_date=result[0]['date'],last_date=result[-1]['date'],weekend_dates=[r['date'] for r in result if date.fromisoformat(r['date']).weekday()>4],
  methodology='(NAV_t + distribution_on_ex_date)/NAV_previous - 1; reinvest at ex-date closing NAV; no splits in 2016-2026 according to vendor events; issuer published YTD comparison recorded below')
 prior=[r for r in result if r['date']<'2026-01-01'][-1]['total_return_index'];last=result[-1]['total_return_index'];summary['reconstructed_2026_ytd']=last/prior-1
 # Published issuer NAV total return to 30 Sep 2026 on issuer page retrieved 21 Oct 2026.
 summary['issuer_published_2026_ytd']=.2584;summary['ytd_difference_bps']=(summary['reconstructed_2026_ytd']-.2584)*10000
 (ROOT/'official_benchmark_validation.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
