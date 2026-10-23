from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,zipfile,bisect
ROOT=Path(__file__).resolve().parent
b=pd.read_csv(ROOT/'benchmark_official_es3_nav_total_return.csv');p=pd.read_csv(ROOT/'research_inputs/prices.csv');f=pd.read_csv(ROOT/'research_inputs/flows.csv');r=pd.read_csv(ROOT/'research_inputs/reports.csv')
assert not p.duplicated(['date','security_id']).any()
assert not f.duplicated(['report_id','investor','security_id']).any()
assert len(r)==396 and len(f)==15840 and r.status.eq('complete').all()
assert (pd.to_datetime(r.publication_date)>pd.to_datetime(r.week_end)).all()
assert f.groupby(['report_id','investor','side']).size().eq(10).all()
assert set(p.security_id).isdisjoint({'SGX_Y92','SGX_YF8'})
eligibility=pd.read_csv(ROOT/'initial_eligibility_audit.csv')
assert set(p.security_id)==set(eligibility[eligibility.eligible].security_id)
assert (eligibility[eligibility.eligible].valid_pre2019_returns>=500).all()
assert eligibility[eligibility.eligible].pre2019_large_return_flags.eq(0).all()
cal=list(b.date);reports=r.set_index('report_id');evidence={}
ret=p.pivot(index='date',columns='security_id',values='total_return_index').reindex(cal).pct_change(fill_method=None)
pre=ret.loc[ret.index<'2019-01-01'].notna().sum()
evidence['source_codes']=236;evidence['eligible_canonical_histories']=p.security_id.nunique();evidence['eligible_histories_with_500_pre2019_returns']=int(pre.ge(500).sum())
evidence['price_rows']=len(p);evidence['retained_reports']=len(r);evidence['signal_rows']=len(f)
flags=pd.read_csv(ROOT/'large_return_review.csv')
assert (flags.daily_return.abs()>.5).all()
evidence['remaining_abs_daily_return_over_50pct_flags']=len(flags)
for inv in ['retail','institutional']:
 t=pd.read_csv(ROOT/f'research_backtest_output/{inv}_net_trades.csv');h=pd.read_csv(ROOT/f'research_backtest_output/{inv}_net_holdings.csv');d=pd.read_csv(ROOT/f'research_backtest_output/{inv}_net_daily.csv')
 times=t.report_id.map(reports.publication_date);expected=times.map(lambda s:cal[bisect.bisect_right(cal,s)])
 assert (t.date==expected).all()
 joined=t.merge(f[f.investor.eq(inv)][['report_id','security_id','side']],on=['report_id','security_id'],how='left')
 # First entry direction is checked against release signal; reductions/exits need not have that sign.
 h=h.sort_values(['security_id','date']);end=h.pivot(index='date',columns='security_id',values='end_value_sgd').reindex(d.date).fillna(0)
 tradepivot=t.pivot_table(index='date',columns='security_id',values='notional_sgd',aggfunc='sum').reindex(index=d.date,columns=end.columns).fillna(0)
 prior=end.shift(fill_value=0);rr=ret.reindex(index=d.date,columns=end.columns)
 marked=prior*(1+rr.fillna(0));gap=(end-marked-tradepivot).abs().to_numpy().max();assert gap<1e-6
 for _,x in joined.iterrows():
  if x.notional_sgd==0:continue
  previous=marked.loc[x.date,x.security_id]
  if abs(previous)<1e-7:
   assert (x.side=='buy' and x.notional_sgd>0) or (x.side=='sell' and x.notional_sgd<0)
 # Flag past outliers that can enter a later current-holdings 500-observation simulation.
 hactive=h[h.end_value_sgd.abs()>1e-8];hit=[]
 for x in flags.itertuples():
  i=bisect.bisect_left(cal,x.date)
  candidates=hactive[(hactive.security_id==x.security_id)&(hactive.date>x.date)&(hactive.date<=cal[min(len(cal)-1,i+500)])]
  hit.extend((a.date,a.security_id,x.date) for a in candidates.itertuples())
 # Define forecast t+1 using t close holdings and preceding 500 asset returns through t.
 insufficient=[]
 for date,group in hactive.groupby('date'):
  i=bisect.bisect_right(cal,date);window=ret.iloc[max(0,i-500):i][group.security_id.unique()]
  if len(window)<500 or window.isna().any().any():insufficient.append(date)
 evidence[inv]=dict(trade_rows=len(t),daily_rows=len(d),first_trade_date=t.date.min(),last_trade_date=t.date.max(),all_trade_dates_after_release=True,max_position_rollforward_gap_sgd=float(gap),forecast_origin_dates_with_insufficient_500_complete_returns=len(set(insufficient)),forecast_origin_dates_with_past_abs_return_flags=len(set(a[0] for a in hit)))
 pd.DataFrame(hit,columns=['forecast_origin_date','security_id','flagged_historical_date']).to_csv(ROOT/f'{inv}_var_history_flag_exposure.csv',index=False)
raw=pd.read_csv(ROOT/'research_backtest_output/asset_returns_aligned.csv',index_col='date')
safe=pd.read_csv(ROOT/'research_backtest_output/asset_returns_for_var.csv',index_col='date')
new_missing=raw.notna() & safe.isna()
assert int(new_missing.to_numpy().sum())==len(flags)
assert ((raw-safe).abs().stack()<1e-10).all()
for x in flags.itertuples():assert pd.isna(safe.loc[x.date,x.security_id])
coverage=pd.read_csv(ROOT/'research_backtest_output/risk_handoff_coverage.csv')
for inv in ['retail','institutional']:
 dates=set(pd.read_csv(ROOT/f'research_backtest_output/{inv}_net_daily.csv').date)
 c=coverage[coverage.strategy.eq(inv)]
 assert len(c)==len(dates) and c.forecast_date.nunique()==len(dates)
 assert set(c.forecast_date)==dates
 assert (c.forecast_origin_date<c.forecast_date).all()
 assert c[c.forecast_date.eq(min(dates))].reason.eq('initial_cash_only').all()
evidence['risk_return_quarantine_count']=len(flags)
evidence['risk_forecast_history_gaps']=coverage[coverage.forecast_date.notna()].groupby('strategy').complete_500_return_window.apply(lambda x:int((~x).sum())).to_dict()
(ROOT/'independent_requirement_audit.json').write_text(json.dumps(evidence,indent=2))
print(json.dumps(evidence,indent=2))
