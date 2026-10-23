"""Data-availability research scenario, NOT a complete/unbiased assignment backtest.
Unknown historical identities and missing histories are retained in exclusions.
"""
from pathlib import Path
from datetime import date
from collections import Counter,defaultdict
from bisect import bisect_left
import json,csv,sys
from prepare_market_data import read_chart,write
ROOT=Path(__file__).resolve().parent

def main():
 p=ROOT/'research_inputs';p.mkdir(exist_ok=True)
 receipts={r['symbol']:r for r in json.loads((ROOT/'market_download_manifest.json').read_text())}
 codes=list(csv.DictReader((ROOT/'security_codes_to_map.csv').open()))
 aliases={r['historical_code']:r for r in csv.DictReader((ROOT/'verified_code_lineage.csv').open())}
 # All ordinary .SI mappings remain candidate mappings; two code-change relations are sourced.
 mapping={r['sgx_code']:dict(price_symbol=r['sgx_code']+'.SI',canonical_security_id='SGX_'+r['sgx_code'],relation_status='same_code_candidate') for r in codes}
 for code,a in aliases.items():mapping[code]=dict(price_symbol=a['price_symbol'],canonical_security_id=a['canonical_security_id'],relation_status=a['event_relation_status'])
 benchmark=list(csv.DictReader((ROOT/'benchmark_official_es3_nav_total_return.csv').open()));calendar=[r['date'] for r in benchmark]
 fxrows,*_=read_chart(receipts['SGD=X']);fx={r['date']:r['close_vendor'] for r in fxrows if r['close_vendor'] and r['close_vendor']>0};fxdates=sorted(fx)
 def fx_rate(currency,d):
  if currency=='SGD':return 1.,''
  if currency!='USD':raise ValueError('Unsupported FX currency '+currency)
  # Strictly previous daily FX label: no same-day NY FX close used at SGX close.
  i=bisect_left(fxdates,d)-1
  if i<0:return None,''
  fd=fxdates[i]
  if (date.fromisoformat(d)-date.fromisoformat(fd)).days>5:return None,fd
  return fx[fd],fd
 quarantine={r['security_id']:r for r in csv.DictReader((ROOT/'data_quality_exclusions.csv').open())}
 available={};allprice={};fxuses=[]
 for code,m in mapping.items():
  r=receipts.get(m['price_symbol'],{})
  if r.get('status')!='downloaded':continue
  available[code]=m
  sid=m['canonical_security_id']
  if sid in quarantine:continue
  if sid in allprice:continue
  rows,events,meta=read_chart(r);data={}
  for x in rows:
   d=x['date']
   if d not in calendar or not x['close_vendor'] or not x['adj_close_vendor'] or x['volume_vendor'] is None:continue
   rate,fd=fx_rate(x['currency'],d)
   if rate is None:continue
   data[d]=dict(date=d,security_id=sid,close=x['close_vendor']*rate,total_return_index=x['adj_close_vendor']*rate,
      volume=x['volume_vendor'],currency='SGD',short_available=1,source_url=r['source_url'])
   if fd:fxuses.append(dict(date=d,security_id=sid,local_currency=x['currency'],fx_label_date=fd,fx_to_sgd=rate))
  allprice[sid]=data
 prices=[x for data in allprice.values() for x in data.values()];prices.sort(key=lambda x:(x['date'],x['security_id']))
 write(p/'prices.csv',prices,['date','security_id','close','total_return_index','volume','currency','short_available','source_url'])
 write(ROOT/'fx_conversion_audit.csv',fxuses,['date','security_id','local_currency','fx_label_date','fx_to_sgd'])
 # Keep all signals in included reports, including securities with no usable history.
 checks=list(csv.DictReader((ROOT/'report_checks.csv').open()));eligible={r['report_id']:r for r in checks if r['timing_status']!='review_required'}
 excluded=[dict(report_id=r['report_id'],reason='unresolved_publication_timing',displayed_publication_date=r['publication_date'],week_start=r['week_start']) for r in checks if r['report_id'] not in eligible]
 write(ROOT/'research_excluded_reports.csv',excluded,['report_id','reason','displayed_publication_date','week_start'])
 flows=[];exclusions=[]
 for r in csv.DictReader((ROOT/'flows_extracted.csv').open()):
  code=r['sgx_code'];m=mapping[code]
  if r['report_id'] not in eligible:continue
  flows.append(dict(report_id=r['report_id'],publication_date=r['publication_date'],investor=r['investor'],side=r['side'],security_id=m['canonical_security_id'],rank=r['rank'],flow_sgd_m=r['flow_sgd_m'],source_page=r['source_page']))
  if code not in available:exclusions.append(dict(report_id=r['report_id'],publication_date=r['publication_date'],sgx_code=code,security_name=r['security_name'],investor=r['investor'],side=r['side'],rank=r['rank'],reason='no_history_for_candidate_symbol'))
 write(p/'flows.csv',flows);write(ROOT/'research_missing_history_signals.csv',exclusions,['report_id','publication_date','sgx_code','security_name','investor','side','rank','reason'])
 reports=[dict(report_id=r['report_id'],week_end=r['week_end_derived'],publication_date=r['publication_date'],status='complete',source_url=r['source_url'],local_file=r['local_file'],sha256=r['sha256'],notes='research: displayed publication date used; archive not proof of historical availability') for r in eligible.values()]
 write(p/'reports.csv',reports)
 write(p/'benchmark.csv',[dict(date=r['date'],total_return_index=r['total_return_index'],source_url=r['source_url']) for r in benchmark],['date','total_return_index','source_url'])
 write(ROOT/'research_security_mapping.csv',[dict(historical_code=c,**m,has_candidate_history=int(c in available)) for c,m in mapping.items()])
 summary=dict(scenario='AVAILABLE_DATA_BASELINE_WITH_DISCLOSED_EXCLUSIONS',quarantined_securities=list(quarantine),data_quality_selection='Retrospective source-quality audit, not a point-in-time universe; selection bias disclosed',source_codes=len(codes),direct_candidate_histories=len(available)-len(aliases),
   sourced_code_change_relations=len(aliases),codes_with_candidate_history=len(available),codes_without_candidate_history=len(codes)-len(available),
   retained_reports=len(reports),excluded_timing_reports=len(excluded),retained_signal_rows=len(flows),missing_history_signal_rows=len(exclusions),
   candidate_price_rows=len(prices),unfilled_allocation_treatment='cash; no redistribution',missing_report_treatment='hold to next observed usable release',
   fx='USD daily quote strictly prior label, max age 5 calendar days; SGD unchanged; timing approximation disclosed',
   benchmark='ES3 official NAV total return reconstructed with issuer distributions',
   short_availability='ALL BORROWABLE ASSUMPTION, not historical evidence',costs='20 bps one-way; 3% annual borrow; 40 bps doubled-cost scenario',
   liquidity='vendor split-adjusted price/volume pair; split/volume basis not independently verified',
   unresolved='missing delisted histories, current-vendor identity mapping, rights/merger adjustments, borrow availability, raw publication metadata')
 (ROOT/'research_scenario.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
