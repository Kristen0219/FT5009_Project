"""Eligibility must not change when future prices or future events change."""
import sys,unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from eligibility import assess_history

class InitialEligibilityTests(unittest.TestCase):
 def clean_history(self):return pd.Series(100.,index=pd.bdate_range('2016-01-01','2018-12-31'))
 def test_future_return_does_not_change_membership(self):
  s=self.clean_history();expected=assess_history(s)
  s.loc[pd.Timestamp('2025-11-10')]=0.001
  self.assertEqual(assess_history(s),expected)
  self.assertTrue(expected['eligible'])
 def test_pre2019_jump_rejected(self):
  s=self.clean_history();s.iloc[100]=200.
  self.assertFalse(assess_history(s)['eligible'])
 def test_new_listing_not_admitted(self):
  s=pd.Series(100.,index=pd.bdate_range('2020-01-01','2026-09-30'))
  self.assertFalse(assess_history(s)['eligible'])
 def test_missing_prices_not_bridged(self):
  s=pd.Series(100.,index=pd.bdate_range('2016-01-01',periods=501));s.iloc[100]=float('nan')
  self.assertEqual(assess_history(s)['valid_pre2019_returns'],498)
  self.assertFalse(assess_history(s)['eligible'])
if __name__=='__main__':unittest.main()
