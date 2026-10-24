"""Regression checks for chronology, fixed slots, risk metrics and accounting."""
from pathlib import Path
import sys
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from enhancement import filter_institutional
from evaluation import metrics, evaluate, liquidity
from run_member2 import engine_module, verify_result


class EnhancementTests(unittest.TestCase):
    def fixture(self):
        dates = pd.bdate_range('2018-01-01', periods=140)
        prices = pd.DataFrame([dict(date=d, security_id=s, total_return_index=v)
            for s, trend in [('UP',1.01),('DOWN',.99)]
            for i,d in enumerate(dates) for v in [100*trend**i]])
        flows = pd.DataFrame([dict(report_id='R', publication_date=dates[130],
            investor=inv, side=side, security_id=s, rank=rank)
            for inv in ['retail','institutional'] for side in ['buy','sell']
            for rank,s in [(1,'UP'),(2,'DOWN')]])
        return flows, prices, dates

    def test_direction_and_strict_release_cutoff(self):
        f,p,c = self.fixture()
        out,a = filter_institutional(f,p,c)
        self.assertEqual(len(out),len(f))
        self.assertTrue((a.information_date < a.publication_date).all())
        self.assertEqual(a.accepted.tolist(),[True,False,False,True])
        pd.testing.assert_frame_equal(out[out.investor.eq('retail')],f[f.investor.eq('retail')])

    def test_release_day_and_future_prices_cannot_change_signal(self):
        f,p,c = self.fixture()
        before,a = filter_institutional(f,p,c)
        p.loc[p.date >= f.publication_date.iloc[0], 'total_return_index'] *= .0001
        after,b = filter_institutional(f,p,c)
        pd.testing.assert_frame_equal(a,b)
        pd.testing.assert_frame_equal(before,after)

    def test_interior_gap_not_bridged(self):
        f,p,c = self.fixture()
        p = p[~((p.date == c[50]) & (p.security_id == 'UP'))]
        _,a = filter_institutional(f,p,c)
        self.assertFalse(a[a.security_id.eq('UP')].accepted.any())
        self.assertTrue(a[a.security_id.eq('UP')].reason.eq('missing_history').all())

    def test_price_equal_to_average_is_rejected(self):
        f,p,c = self.fixture()
        p['total_return_index'] = 100.
        _,a = filter_institutional(f,p,c)
        self.assertFalse(a.accepted.any())

    def test_uses_average_not_endpoint_return(self):
        f,p,c = self.fixture()
        # Positive endpoint return but price below its recent mean: reject buy.
        p.loc[p.security_id.eq('UP'),'total_return_index'] = 200.
        p.loc[p.security_id.eq('UP') & p.date.eq(c[4]),'total_return_index'] = 50.
        p.loc[p.security_id.eq('UP') & p.date.eq(c[129]),'total_return_index'] = 100.
        _,a = filter_institutional(f,p,c)
        self.assertFalse(a[a.security_id.eq('UP') & a.side.eq('buy')].accepted.iloc[0])
        expected=100/((50+124*200+100)/126)-1
        self.assertAlmostEqual(a[a.security_id.eq('UP')].price_to_sma126_minus_one.iloc[0],expected)

    def test_insufficient_history_is_rejected(self):
        f,p,c = self.fixture()
        f['publication_date'] = c[20]
        _,a = filter_institutional(f,p,c)
        self.assertFalse(a.accepted.any())

    def test_no_quote_history_is_rejected(self):
        f,p,c = self.fixture()
        p = p[p.security_id.ne('DOWN')]
        _,a = filter_institutional(f,p,c)
        self.assertFalse(a[a.security_id.eq('DOWN')].accepted.any())

    def test_ten_slots_are_not_redistributed_and_rejected_holding_exits(self):
        engine = engine_module()
        dates = pd.bdate_range('2019-01-02', periods=4)
        benchmark = pd.DataFrame({'total_return_index':100.}, index=dates)
        prices = pd.DataFrame([dict(date=d,security_id=s,close=100.,total_return_index=100.,volume=1e6,short_available=1)
            for d in dates for s in ['A','B']])
        flows = pd.DataFrame([dict(report_id=rid,investor='institutional',side=side,security_id=s)
            for rid in ['R1','R2'] for side in ['buy','sell']
            for s in (['A']+[f'FILTERED::L{i}' for i in range(9)] if side=='buy'
                      else ['B']+[f'FILTERED::S{i}' for i in range(9)])])
        flows.loc[flows.report_id.eq('R2') & flows.security_id.eq('A'),'security_id']='FILTERED::A'
        reports = pd.DataFrame([dict(report_id='R1',publication_date=dates[0],status='complete'),
                                dict(report_id='R2',publication_date=dates[2],status='complete')])
        result = engine.simulate(flows,prices,reports,benchmark,'institutional',0,0)
        self.assertAlmostEqual(result['daily'].iloc[1].gross_exposure,.098)
        t = result['trades']
        self.assertAlmostEqual(t.loc[t.security_id.eq('A') & t.report_id.eq('R2'),'notional_sgd'].iloc[0],-49000)
        verify_result(result,0,0,benchmark)


class EvaluationTests(unittest.TestCase):
    def test_adv_excludes_execution_day_and_preserves_calendar_gaps(self):
        c = pd.bdate_range('2019-01-01',periods=25)
        p = pd.DataFrame(dict(date=c,security_id='A',close=10.,volume=100.))
        t = pd.DataFrame([dict(date=c[-1],security_id='A',notional_sgd=500.,participation=.5)])
        first = liquidity(t,p,c)
        self.assertAlmostEqual(first.participation_adv21.iloc[0],.5)
        p.loc[p.date.eq(c[-1]),'volume'] = 1e10
        changed = liquidity(t,p,c)
        self.assertEqual(first.lagged_adv21_sgd.iloc[0],changed.lagged_adv21_sgd.iloc[0])
        missing = liquidity(t,p[p.date.ne(c[10])],c)
        self.assertTrue(np.isnan(missing.lagged_adv21_sgd.iloc[0]))

    def test_initial_loss_in_drawdown(self):
        m = metrics([-.1,.1])
        self.assertAlmostEqual(m['maximum_drawdown'],-.1)
        self.assertAlmostEqual(m['cumulative_return'],-.01)

    def test_sortino_uses_all_sessions(self):
        r = np.array([-.02,.04,0.,.01])
        m = metrics(r)
        self.assertAlmostEqual(m['sortino'],r.mean()/np.sqrt((.02**2)/4)*np.sqrt(252))

    def test_volatility_sample_standard_deviation(self):
        r = [.01,-.01,.02]
        self.assertAlmostEqual(metrics(r)['annualised_volatility'],np.std(r,ddof=1)*np.sqrt(252))

    def test_zero_variation_ratios_undefined(self):
        m = metrics([0.,0.,0.])
        self.assertTrue(np.isnan(m['sharpe']))
        self.assertTrue(np.isnan(m['sortino']))

    def test_bad_returns_fail(self):
        for r in [[],[np.nan],[np.inf],[-1.]]:
            with self.assertRaises(ValueError):metrics(r)

    def test_subperiod_keeps_first_day_actual_return(self):
        d = pd.DataFrame(dict(date=pd.to_datetime(['2021-12-31','2022-01-03','2024-01-02']),
                             daily_return=[.1,-.2,.3],turnover=[0.,0.,0.],cost_sgd=[0.,0.,0.],
                             borrow_sgd=[0.,0.,0.],gross_exposure=[0.,0.,0.]))
        rows = evaluate({('enhanced','net'):d},d[['date','daily_return']])
        self.assertAlmostEqual(rows.loc[rows.strategy.eq('enhanced') & rows.period.eq('2022–2023'),'cumulative_return'].iloc[0],-.2)
        total = rows[rows.strategy.eq('enhanced')].set_index('period').cumulative_return
        self.assertAlmostEqual((1+total['2019–2021'])*(1+total['2022–2023'])*(1+total['2024–Sep2026']),1+total['full'])


if __name__ == '__main__':
    unittest.main()
