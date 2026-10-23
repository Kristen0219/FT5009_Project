"""Preserve vendor returns and quarantine unverified extreme observations for VaR.
No return clipping or zero imputation; a flagged observation creates a risk-history gap.
"""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parent

def main():
 out=ROOT/'research_backtest_output'
 raw=pd.read_csv(out/'asset_returns_aligned.csv',index_col='date')
 flags=pd.read_csv(ROOT/'large_return_review.csv')
 safe=raw.copy()
 for x in flags.itertuples():
  assert abs(x.daily_return)>.5
  safe.loc[x.date,x.security_id]=float('nan')
 safe.to_csv(out/'asset_returns_for_var.csv',index_label='date')
 review=flags.copy();review['treatment']='missing_in_VaR_input_pending_review; original_return_preserved'
 review['reason']='unverified_abs_daily_return_over_50pct; may_be_genuine'
 review.loc[(review.security_id=='SGX_1MZ')&(review.date=='2024-02-01'),'reason']='vendor_100fold_price_jump_during_documented_suspension; no_reliable_economic_return_reconstructed'
 review.to_csv(ROOT/'risk_return_quarantine.csv',index=False)
 complete=safe.notna().rolling(500,min_periods=500).sum().eq(500)
 calendar=list(raw.index);next_date={d:calendar[i+1] if i+1<len(calendar) else '' for i,d in enumerate(calendar)}
 result=[]
 for inv in ['retail','institutional']:
  h=pd.read_csv(out/f'{inv}_net_holdings.csv');h=h[h.end_value_sgd.abs()>1e-8]
  groups={d:g.security_id.unique() for d,g in h.groupby('date')}
  daily=pd.read_csv(out/f'{inv}_net_daily.csv')
  first=daily.date.iloc[0];previous=calendar[calendar.index(first)-1]
  result.append(dict(strategy=inv,forecast_origin_date=previous,forecast_date=first,active_securities=0,complete_500_return_window=True,reason='initial_cash_only'))
  for d in daily.date:
   if not next_date[d]:continue
   names=groups.get(d,[])
   valid=not len(names) or bool(complete.loc[d,names].all())
   result.append(dict(strategy=inv,forecast_origin_date=d,forecast_date=next_date[d],active_securities=len(names),complete_500_return_window=valid,reason='cash_only' if not len(names) else 'complete' if valid else 'unverified_or_missing_asset_return_in_preceding_500_sessions'))
 coverage=pd.DataFrame(result);coverage.to_csv(out/'risk_handoff_coverage.csv',index=False)
 counts=coverage[coverage.forecast_date.ne('')].groupby('strategy').complete_500_return_window.apply(lambda x:int((~x).sum())).to_dict()
 status=json.loads((ROOT/'REPORTING_STATUS.json').read_text())
 status['risk_input']='research_backtest_output/asset_returns_for_var.csv'
 status['unverified_risk_return_observations_quarantined']=len(review)
 status['risk_forecasts_with_history_gap']=counts
 status['risk_instruction']='Use exactly 500 preceding aligned observations for current signed holdings. If any required observation is missing, disclose the whole forecast as unavailable; do not drop days or fill zero. Review genuine flagged returns to restore coverage with evidence.'
 (ROOT/'REPORTING_STATUS.json').write_text(json.dumps(status,indent=2))
 print('VaR handoff gaps:',counts,'quarantined observations:',len(review))
if __name__=='__main__':main()
