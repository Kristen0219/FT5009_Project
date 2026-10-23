"""Small handoff table, not a replacement for Member 2 evaluation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent

def main():
 rows=[]
 for investor in ['retail','institutional']:
  for case in ['gross','net','double_cost']:
   d=pd.read_csv(ROOT/f'research_backtest_output/{investor}_{case}_daily.csv')
   nav=d.nav; running=np.maximum.accumulate(np.r_[1_000_000.,nav.to_numpy()])[1:]
   rows.append(dict(strategy=investor,scenario=case,start_date=d.date.iloc[0],end_date=d.date.iloc[-1],trading_days=len(d),initial_nav_sgd=1_000_000.,final_nav_sgd=nav.iloc[-1],cumulative_return=nav.iloc[-1]/1_000_000.-1,max_drawdown=float((nav/running-1).min()),transaction_cost_sgd=d.cost_sgd.sum(),borrow_cost_sgd=d.borrow_sgd.sum(),average_gross_exposure=d.gross_exposure.mean()))
 pd.DataFrame(rows).to_csv(ROOT/'baseline_handoff_summary.csv',index=False)
 f=pd.read_csv(ROOT/'flows_extracted.csv'); q=pd.read_csv(ROOT/'data_quality_exclusions.csv'); ids=set(q.security_id.str.removeprefix('SGX_'))
 counts=f[f.sgx_code.isin(ids)].groupby(['sgx_code','investor']).size().rename('source_signal_rows').reset_index()
 counts.to_csv(ROOT/'quarantined_signal_counts.csv',index=False)
 for investor in ['retail','institutional']:
  flags=pd.read_csv(ROOT/f'{investor}_active_large_return_review.csv')
  assert flags.empty, 'An active holding still has an unresolved >50% daily return; review before handoff'
 status=json.loads((ROOT/'REPORTING_STATUS.json').read_text())
 status['no_remaining_active_abs_daily_return_over_50pct']=True
 (ROOT/'REPORTING_STATUS.json').write_text(json.dumps(status,indent=2))
 print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':main()
