"""Synthetic accounting tests only, not historical evidence."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from backtest import simulate

class EngineTests(unittest.TestCase):
    def fixture(self):
        ds=pd.to_datetime(['2019-01-02','2019-01-03','2019-01-04','2019-01-07'])
        b=pd.DataFrame({'total_return_index':[100]*4},index=ds)
        p=pd.DataFrame([dict(date=d,security_id=s,close=v,total_return_index=v,volume=10000000,short_available=1)
            for s,vs in [('L',[100,100,110,110]),('S',[100,100,90,90])] for d,v in zip(ds,vs)])
        r=pd.DataFrame([dict(report_id='R',publication_date=ds[0],status='complete')])
        f=pd.DataFrame([dict(report_id='R',investor='retail',side=side,security_id=s) for side,s in [('buy','L'),('sell','S')]])
        return f,p,r,b
    def test_lag_pnl_and_cost(self):
        f,p,r,b=self.fixture();result=simulate(f,p,r,b,'retail',20,0)
        d=result['daily'];t=result['trades']
        self.assertEqual(str(t.date.min().date()),'2019-01-03')
        # One name each side hits 10% cap: 200k turnover, 400 SGD cost.
        self.assertAlmostEqual(d.iloc[1].nav,999600)
        self.assertAlmostEqual(d.iloc[2].nav,1019600)
        self.assertAlmostEqual(t.cost_sgd.sum(),400)
    def test_missing_held_price_fails(self):
        f,p,r,b=self.fixture();p=p[~((p.security_id=='L')&(p.date==b.index[2]))]
        with self.assertRaisesRegex(ValueError,'Missing held-asset return'):simulate(f,p,r,b,'retail')
    def test_no_borrow_no_short(self):
        f,p,r,b=self.fixture();p.loc[p.security_id=='S','short_available']=0
        result=simulate(f,p,r,b,'retail',0,0)
        self.assertFalse((result['trades'].security_id=='S').any())
        self.assertEqual(result['exclusions'].iloc[0].reason,'borrow_unavailable')
    def test_weekend_borrow(self):
        f,p,r,b=self.fixture();d=simulate(f,p,r,b,'retail',0,.03)['daily']
        self.assertAlmostEqual(d.iloc[-1].borrow_sgd,90000*.03*3/365)

if __name__=='__main__':unittest.main()
