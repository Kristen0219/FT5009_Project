"""Independent reconciliation and data-quality audit; no imputation or identity repair."""
from pathlib import Path
from collections import defaultdict,Counter
import json,csv,hashlib,math,bisect
import pandas as pd
from prepare_market_data import read_chart,write
ROOT=Path(__file__).resolve().parent

def main():
 receipts=json.loads((ROOT/'market_download_manifest.json').read_text());verified=0
 for r in receipts:
  if r['status']=='downloaded':
   assert hashlib.sha256((ROOT/r['local_file']).read_bytes()).hexdigest()==r['sha256'];verified+=1
 b=pd.read_csv(ROOT/'benchmark_official_es3_nav_total_return.csv');assert not b.date.duplicated().any()
 independent=(b.nav_sgd+b.distribution_sgd)/b.nav_sgd.shift()-1
 assert (independent.dropna()-b.daily_return.dropna()).abs().max()<1e-12
 assert abs(json.loads((ROOT/'official_benchmark_validation.json').read_text())['ytd_difference_bps'])<1
 official_dates=set(b.date);sti_dates=set(pd.read_csv(ROOT/'sti_price_index.csv').date)
 assert official_dates==sti_dates,'Calendar mismatch between official NAV and valid STI price-index bars'
 # Flag raw source names appearing against different code identities, excluding two sourced aliases.
 alias={r['historical_code']:r['canonical_security_id'] for r in csv.DictReader((ROOT/'verified_code_lineage.csv').open())}
 flows=list(csv.DictReader((ROOT/'flows_extracted.csv').open()));byname=defaultdict(list)
 for r in flows:byname[r['security_name'].strip().lower()].append(r)
 conflicts=[]
 for name,items in byname.items():
  if len({alias.get(r['sgx_code'],'SGX_'+r['sgx_code']) for r in items})>1:
   for code in sorted({r['sgx_code'] for r in items}):
    subset=[r for r in items if r['sgx_code']==code]
    conflicts.append(dict(source_name=name,sgx_code=code,occurrences=len(subset),report_ids=';'.join(sorted({r['report_id'] for r in subset})),treatment='unresolved; research prioritises source code, not name; no automatic correction'))
 write(ROOT/'source_name_code_conflicts.csv',conflicts,['source_name','sgx_code','occurrences','report_ids','treatment'])
 prices=pd.read_csv(ROOT/'research_inputs/prices.csv',dtype={'security_id':str});assert not prices.duplicated(['date','security_id']).any()
 assert (prices[['close','total_return_index']]>0).all().all();assert (prices.volume>=0).all();assert prices.currency.eq('SGD').all()
 tri=prices.pivot(index='date',columns='security_id',values='total_return_index').reindex(b.date)
 ret=tri.pct_change(fill_method=None)
 outliers=ret.stack();outliers=outliers[outliers.abs()>.5].rename('daily_return').reset_index()
 outliers.to_csv(ROOT/'large_return_review.csv',index=False)
 fx=pd.read_csv(ROOT/'fx_conversion_audit.csv');assert (fx.fx_label_date<fx.date).all();assert (pd.to_datetime(fx.date)-pd.to_datetime(fx.fx_label_date)).dt.days.le(5).all()
 # Independently reconcile recorded NAV to prior holdings marked with input returns.
 summaries=[]
 for investor in ['retail','institutional']:
  for scenario in ['gross','net','double_cost']:
   prefix=ROOT/'research_backtest_output'/f'{investor}_{scenario}'
   daily=pd.read_csv(str(prefix)+'_daily.csv').set_index('date');hold=pd.read_csv(str(prefix)+'_holdings.csv')
   h=hold.pivot(index='date',columns='security_id',values='end_value_sgd').reindex(daily.index).fillna(0)
   prior=h.shift().fillna(0);r=ret.reindex(index=daily.index,columns=h.columns)
   active=prior.abs()>1e-6
   assert not (active&r.isna()).any().any(),'Unresolved active holding return'
   pnl=(prior*r.fillna(0)).sum(axis=1)
   prevnav=daily.nav.shift().fillna(1000000.)
   expected=prevnav+pnl-daily.cost_sgd-daily.borrow_sgd
   gap=(daily.nav-expected).abs().max();assert gap<1e-6,(investor,scenario,gap)
   assert (daily.daily_return-(daily.nav/prevnav-1)).abs().max()<1e-12
   assert (daily.nav-daily.cash_sgd-h.sum(axis=1)).abs().max()<1e-6
   trades=pd.read_csv(str(prefix)+'_trades.csv')
   fee=0 if scenario=='gross' else .002 if scenario=='net' else .004
   assert (trades.cost_sgd-trades.notional_sgd.abs()*fee).abs().max()<1e-7
   exclusion=pd.read_csv(str(prefix)+'_exclusions.csv')
   summaries.append(dict(strategy=investor,scenario=scenario,status='DATA_LIMITED_RESEARCH_ONLY',daily_rows=len(daily),trade_rows=len(trades),exclusion_rows=len(exclusion),blocked_rebalance_rows=sum(exclusion.reason=='rebalance_blocked_hold_existing'),max_nav_reconciliation_error_sgd=gap))
 write(ROOT/'research_execution_coverage.csv',summaries)
 summary=dict(verified_raw_json_checksums=verified,official_nav_calendar_matches_sti=True,official_benchmark_ytd_difference_bps=json.loads((ROOT/'official_benchmark_validation.json').read_text())['ytd_difference_bps'],
   positive_sgd_prices=True,unique_price_keys=True,strictly_lagged_fx=True,backtest_paths_reconciled=len(summaries),source_name_conflict_rows=len(conflicts),large_return_review_rows=len(outliers),
   status='PASSED NUMERICAL CHECKS; incomplete historical universe, identity/source issues and trading assumptions unresolved')
 (ROOT/'validation_results.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
