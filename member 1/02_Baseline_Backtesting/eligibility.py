"""Fixed initial data eligibility. No post-2018 observation enters this decision."""
import numpy as np
import pandas as pd
CUTOFF='2019-01-01'
MIN_RETURNS=500
MAX_ABS_RETURN=0.50

def assess_history(total_return_index):
 s=total_return_index.copy()
 s.index=pd.to_datetime(s.index)
 s=s.sort_index().loc[lambda x:x.index<pd.Timestamp(CUTOFF)]
 r=s.pct_change(fill_method=None).replace([np.inf,-np.inf],np.nan)
 n=int(r.notna().sum());extreme=int(r.abs().gt(MAX_ABS_RETURN).sum())
 reasons=[]
 if n<MIN_RETURNS:reasons.append('fewer_than_500_valid_pre2019_returns')
 if extreme:reasons.append('pre2019_abs_daily_return_over_50pct_unreconciled')
 return dict(eligible=not reasons,valid_pre2019_returns=n,pre2019_large_return_flags=extreme,reason=';'.join(reasons) or 'passes_fixed_initial_screen')
