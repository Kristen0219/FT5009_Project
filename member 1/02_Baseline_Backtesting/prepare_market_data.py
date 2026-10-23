"""Prepare auditable vendor data; never certify current symbols as historical IDs."""
from pathlib import Path
from datetime import datetime,date,timedelta,timezone
from zoneinfo import ZoneInfo
from collections import Counter,defaultdict
import csv,json,math,re
ROOT=Path(__file__).resolve().parent
END=date(2026,9,30);START=date(2016,1,1)

def write(path,rows,fields=None):
 if fields is None:fields=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def number(v,positive=False):
 try:v=float(v)
 except (ValueError,TypeError):return None
 return v if math.isfinite(v) and (not positive or v>0) else None

def read_chart(receipt):
 r=json.loads((ROOT/receipt['local_file']).read_text())['chart']['result'][0]
 meta=r['meta'];tz=ZoneInfo(meta.get('exchangeTimezoneName','UTC'))
 q=r['indicators']['quote'][0];adj=r['indicators'].get('adjclose',[{}])[0].get('adjclose',[])
 rows=[]
 for i,ts in enumerate(r['timestamp']):
  day=datetime.fromtimestamp(ts,tz).date()
  if not START<=day<=END:continue
  val=lambda k:number(q.get(k,[None]*len(r['timestamp']))[i])
  rows.append(dict(date=day.isoformat(),symbol=receipt['symbol'],vendor_name=receipt.get('vendor_name',''),currency=meta.get('currency',''),
   open_vendor=val('open'),high_vendor=val('high'),low_vendor=val('low'),close_vendor=val('close'),
   adj_close_vendor=number(adj[i],True) if i<len(adj) else None,volume_vendor=val('volume'),source_url=receipt['source_url']))
 events=[]
 for kind,items in r.get('events',{}).items():
  for event in items.values():
   events.append(dict(symbol=receipt['symbol'],currency=meta.get('currency',''),event_type=kind,
    date=datetime.fromtimestamp(event['date'],tz).date().isoformat(),amount=event.get('amount',''),
    numerator=event.get('numerator',''),denominator=event.get('denominator',''),split_ratio=event.get('splitRatio',''),source_url=receipt['source_url']))
 return rows,events,meta

def main():
 receipts=[json.loads(p.read_text()) for p in (ROOT/'receipts').glob('*.json')]
 (ROOT/'market_download_manifest.json').write_text(json.dumps(sorted(receipts,key=lambda r:r['symbol']),indent=2))
 codes=list(csv.DictReader((ROOT/'security_codes_to_map.csv').open()))
 source={r['sgx_code']:r for r in codes}
 allmeta=[];events=[];series={};bad=[];rows_n=0
 fields=['date','sgx_code','symbol','vendor_name','currency','open_vendor','high_vendor','low_vendor','close_vendor','adj_close_vendor','volume_vendor','source_url']
 with (ROOT/'prices_vendor.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader()
  for receipt in sorted(receipts,key=lambda r:r['symbol']):
   if receipt['status']!='downloaded':continue
   try:
    rows,ev,meta=read_chart(receipt)
    if len({r['date'] for r in rows})!=len(rows):raise ValueError('duplicate local-date bars')
    for row in rows:
     row['sgx_code']=receipt['symbol'][:-3] if receipt['symbol'].endswith('.SI') else ''
     if row['close_vendor'] is None or row['close_vendor']<=0 or row['adj_close_vendor'] is None:bad.append(dict(symbol=receipt['symbol'],date=row['date'],issue='missing_or_invalid_close_or_adjusted_close'))
     if row['volume_vendor'] is None or row['volume_vendor']<0:bad.append(dict(symbol=receipt['symbol'],date=row['date'],issue='missing_or_negative_volume'))
    writer.writerows(rows);rows_n+=len(rows);events.extend(ev);series[receipt['symbol']]={r['date']:r for r in rows}
    valid=[r['date'] for r in rows if r['adj_close_vendor'] is not None]
    code=receipt['symbol'][:-3] if receipt['symbol'].endswith('.SI') else ''
    allmeta.append(dict(symbol=receipt['symbol'],sgx_code=code,vendor_name=receipt.get('vendor_name',''),source_names=source.get(code,{}).get('names',''),
     currency=meta.get('currency',''),exchange=meta.get('exchangeName',''),instrument_type=meta.get('instrumentType',''),
     vendor_first_trade_date=datetime.fromtimestamp(meta['firstTradeDate'],ZoneInfo(meta.get('exchangeTimezoneName','UTC'))).date().isoformat() if meta.get('firstTradeDate') else '',
     first_valid_price=min(valid) if valid else '',last_valid_price=max(valid) if valid else '',valid_adjusted_prices=len(valid),
     first_signal_week=source.get(code,{}).get('first_signal_week',''),last_signal_week=source.get(code,{}).get('last_signal_week',''),
     mapping_status='candidate_not_independently_verified',source_url=receipt['source_url']))
   except Exception as e:bad.append(dict(symbol=receipt['symbol'],date='',issue='parse_error: '+str(e)))
 write(ROOT/'corporate_actions_vendor.csv',events,['symbol','currency','event_type','date','amount','numerator','denominator','split_ratio','source_url'])
 write(ROOT/'price_data_issues.csv',bad,['symbol','date','issue']);write(ROOT/'security_mapping_candidates.csv',allmeta)
 downloaded={r['symbol']:r for r in receipts}
 failures=[dict(sgx_code=r['sgx_code'],source_names=r['names'],candidate_symbol=r['sgx_code']+'.SI',**{k:v for k,v in downloaded.get(r['sgx_code']+'.SI',{'status':'not_attempted'}).items() if k not in ['symbol']}) for r in codes if downloaded.get(r['sgx_code']+'.SI',{}).get('status')!='downloaded']
 write(ROOT/'unavailable_symbols.csv',failures,['sgx_code','source_names','candidate_symbol','status','http_status','error','source_url'])
 # A price index calendar; do not present STI price-index returns as total returns.
 sti=series.get('^STI',{});calendar=sorted(d for d,r in sti.items() if r['close_vendor'] is not None and r['close_vendor']>0)
 write(ROOT/'sti_price_index.csv',[dict(date=d,price_index=sti[d]['close_vendor'],source_url=sti[d]['source_url']) for d in calendar],['date','price_index','source_url'])
 # Investable benchmark proxy, adjusted-price total return, with explicit identity.
 es3=series.get('ES3.SI',{});base=next((es3[d]['adj_close_vendor'] for d in calendar if d in es3 and es3[d]['adj_close_vendor']),None)
 benchmark=[];prev=None
 for d in calendar:
  price=es3.get(d,{}).get('adj_close_vendor');ret=price/prev-1 if price and prev else None
  benchmark.append(dict(date=d,total_return_index=price/base*100 if price and base else None,daily_return=ret,benchmark_symbol='ES3.SI',source_url=es3.get(d,{}).get('source_url','')))
  prev=price
 write(ROOT/'benchmark_es3_total_return_proxy.csv',benchmark,['date','total_return_index','daily_return','benchmark_symbol','source_url'])
 # Preserve missing daily observations; do not bridge gaps with pct_change defaults.
 return_fields=['date']+[r['sgx_code'] for r in codes if r['sgx_code']+'.SI' in series]
 with (ROOT/'asset_returns_local_currency.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=return_fields);w.writeheader();previous={}
  for d in calendar:
   row={'date':d}
   for code in return_fields[1:]:
    val=series[code+'.SI'].get(d,{}).get('adj_close_vendor');old=previous.get(code)
    row[code]=val/old-1 if val and old else None;previous[code]=val
   w.writerow(row)
 coverage=[]
 for r in allmeta:
  if r['sgx_code'] not in source:continue
  code=r['sgx_code'];s=series[r['symbol']];pre=[d for d in calendar if d<'2019-01-01'];n=0
  for i,d in enumerate(pre):
   if i and s.get(d,{}).get('adj_close_vendor') and s.get(pre[i-1],{}).get('adj_close_vendor'):n+=1
  coverage.append(dict(sgx_code=code,symbol=r['symbol'],currency=r['currency'],valid_pre2019_aligned_returns=n,
   initial_500_return_history='available_numerically' if n>=500 else 'insufficient',first_valid_price=r['first_valid_price'],last_valid_price=r['last_valid_price'],
   first_signal_week=r['first_signal_week'],last_signal_week=r['last_signal_week'],identity_status=r['mapping_status'],
   missing_adjusted_prices_on_sti_calendar=sum(not s.get(d,{}).get('adj_close_vendor') for d in calendar)))
 write(ROOT/'history_coverage.csv',coverage)
 summary=dict(candidate_sgx_codes=len(codes),requested_symbols=len(codes)+2,successful_sgx_symbols=sum(r['sgx_code'] in source for r in allmeta),
  successful_series=len(series),unavailable_sgx_candidates=len(failures),vendor_price_rows=rows_n,corporate_action_records=len(events),
  price_issue_rows=len(bad),currencies=dict(Counter(r['currency'] for r in allmeta if r['sgx_code'] in source)),
  calendar_sessions=len(calendar),calendar_start=calendar[0] if calendar else None,calendar_end=calendar[-1] if calendar else None,
  mapped_identities_independently_verified=0,initial_500_return_history_count=sum(r['valid_pre2019_aligned_returns']>=500 for r in coverage))
 (ROOT/'market_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
