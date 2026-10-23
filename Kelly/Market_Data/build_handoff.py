"""Document collected data and concrete blockers without presenting faulty returns as results."""
from pathlib import Path
from collections import Counter
import json,csv
import pandas as pd
ROOT=Path(__file__).resolve().parent

def main():
 scenario=json.loads((ROOT/'research_scenario.json').read_text());summary=json.loads((ROOT/'market_summary.json').read_text())
 mapping={r['historical_code']:r for r in csv.DictReader((ROOT/'research_security_mapping.csv').open())}
 raw={r['sgx_code']:r for r in csv.DictReader((ROOT/'security_codes_to_map.csv').open())}
 outliers=pd.read_csv(ROOT/'large_return_review.csv');counts=Counter(outliers.security_id)
 request=[]
 for code,m in mapping.items():
  reasons=[]
  if m['has_candidate_history']=='0':reasons.append('candidate_daily_history_unavailable')
  n=counts.get(m['canonical_security_id'],0)
  if n:reasons.append('large_adjusted_return_requires_source_or_corporate_action_review')
  if code=='BQF':reasons.append('vendor_history_starts_after_historical_signal')
  if reasons:request.append(dict(historical_sgx_code=code,source_names=raw[code]['names'],candidate_vendor_symbol=m['price_symbol'],
   reasons=';'.join(reasons),signal_rows=raw[code]['signal_rows'],large_return_flags=n,
   first_signal_week=raw[code]['first_signal_week'],last_signal_week=raw[code]['last_signal_week'],
   requested_start='2016-01-01',requested_end='2026-09-30',
   required_fields='historical identifier/ISIN; currency; unadjusted daily close; share volume; total-return series; cash dividends; splits/rights/spin-offs; delisting settlement'))
 request.sort(key=lambda r:(r['reasons']!='candidate_daily_history_unavailable',-int(r['signal_rows'])))
 with (ROOT/'data_provider_request.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=request[0].keys());w.writeheader();w.writerows(request)
 gaps=[dict(historical_sgx_code=code,source_names=raw[code]['names'],signal_rows=raw[code]['signal_rows'],first_signal_week=raw[code]['first_signal_week'],last_signal_week=raw[code]['last_signal_week']) for code,m in mapping.items() if m['has_candidate_history']=='0']
 with (ROOT/'remaining_history_gaps.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=gaps[0].keys());w.writeheader();w.writerows(sorted(gaps,key=lambda x:-int(x['signal_rows'])))
 active=[]
 for inv in ['retail','institutional']:
  x=pd.read_csv(ROOT/f'{inv}_active_large_return_review.csv');x['strategy']=inv;active.extend(x.to_dict('records'))
 status=dict(reporting_allowed=True,reason='Available-data baseline only; two diagnosed unreliable histories quarantined symmetrically. Not an unbiased full-universe backtest',publication_scope='Member 1 restricted-sample baseline with mandatory limitations; remaining return flags must be reviewed before final VaR',quarantined_securities=scenario['quarantined_securities'],retrospective_quality_selection_bias=True,
  direct_downloaded_sgx_symbols=summary['successful_sgx_symbols'],codes_with_candidate_history_including_two_sourced_code_changes=scenario['codes_with_candidate_history'],remaining_history_gaps=len(gaps),
  large_return_flags=len(outliers),flagged_canonical_securities=len(counts),active_large_return_observations=len(active),
  active_observations=active,data_provider_request_rows=len(request),
  raw_data_preserved=True,automatic_return_clipping=False,automatic_missing_return_zero_fill=False,
  numbers_are='restricted-sample strategy outputs; arithmetic verified, vendor histories not independently certified')
 (ROOT/'REPORTING_STATUS.json').write_text(json.dumps(status,indent=2))
 (ROOT/'research_backtest_output/DO_NOT_USE_FOR_REPORT.txt').unlink(missing_ok=True)
 (ROOT/'research_backtest_output/READ_BEFORE_USE.txt').write_text('Restricted available-data baseline. Use only with the exclusions and retrospective quality-selection bias disclosed in docs/member1_data_methods_update.md. Remaining large-return flags require review before final asset-based VaR. No full-universe or causal claim is supported.\n')
 print(json.dumps({k:v for k,v in status.items() if k!='active_observations'},indent=2))
if __name__=='__main__':main()
