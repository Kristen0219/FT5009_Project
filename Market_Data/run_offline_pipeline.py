"""Reproduce extraction and diagnostic accounting only. No live downloads are needed."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parent
from restore_market_data import restore_sources
restore_sources()
steps=[['prepare_market_data.py'],['build_official_benchmark.py'],['build_research_inputs.py'],
 ['backtest.py','--input',str(ROOT/'research_inputs'),'--output',str(ROOT/'research_backtest_output')],
 ['audit_and_validate.py']]
for step in steps:subprocess.run([sys.executable,str(ROOT/step[0]),*step[1:]],check=True)
# Rebuild active flags used in the handoff.
import pandas as pd
flags=pd.read_csv(ROOT/'large_return_review.csv')
for investor in ['retail','institutional']:
 h=pd.read_csv(ROOT/f'research_backtest_output/{investor}_net_holdings.csv');h=h[h.start_weight.abs()>1e-9]
 flags.merge(h[['date','security_id','start_weight']],on=['date','security_id']).to_csv(ROOT/f'{investor}_active_large_return_review.csv',index=False)
subprocess.run([sys.executable,str(ROOT/'build_handoff.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'summarize_baselines.py')],check=True)
print('Available-data baseline completed. Read README.md and REPORTING_STATUS.json for mandatory limitations.')
