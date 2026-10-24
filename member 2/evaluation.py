"""Daily-return performance, common period boundaries and ex-post liquidity."""
import numpy as np
import pandas as pd

PERIODS = {'full': ('2019-01-01', '2026-09-30'),
           '2019–2021': ('2019-01-01', '2021-12-31'),
           '2022–2023': ('2022-01-01', '2023-12-31'),
           '2024–Sep2026': ('2024-01-01', '2026-09-30')}


def metrics(returns):
    r = pd.Series(returns, dtype=float)
    if r.empty or not np.isfinite(r).all() or (r <= -1).any():
        raise ValueError('Metrics require nonempty finite simple returns above -100%')
    wealth = np.r_[1., (1 + r).cumprod().to_numpy()]
    std = r.std(ddof=1)
    downside = np.sqrt(np.mean(np.minimum(r.to_numpy(), 0.) ** 2))
    return dict(sessions=len(r), cumulative_return=wealth[-1]-1,
                annualised_return=wealth[-1] ** (252/len(r))-1,
                annualised_volatility=std*np.sqrt(252),
                maximum_drawdown=float((wealth/np.maximum.accumulate(wealth)-1).min()),
                sharpe=float(r.mean()/std*np.sqrt(252)) if std > 0 else np.nan,
                sortino=float(r.mean()/downside*np.sqrt(252)) if downside > 0 else np.nan)


def evaluate(paths, benchmark):
    rows = []
    for (strategy, scenario), daily in paths.items():
        for period, (lo, hi) in PERIODS.items():
            d = daily[daily.date.between(lo, hi)]
            rows.append(dict(strategy=strategy, scenario=scenario, period=period,
                             **metrics(d.daily_return),
                             annualised_one_way_turnover=d.turnover.sum()*252/len(d),
                             transaction_cost_sgd=d.cost_sgd.sum(), borrow_cost_sgd=d.borrow_sgd.sum(),
                             mean_gross_exposure=d.gross_exposure.mean()))
    for period, (lo, hi) in PERIODS.items():
        b = benchmark[benchmark.date.between(lo, hi)]
        rows.append(dict(strategy='benchmark', scenario='reference', period=period,
                         **metrics(b.daily_return)))
    return pd.DataFrame(rows)


def liquidity(trades, prices, calendar):
    """Ex-post actual-day participation and strictly lagged 21-session ADV proxy."""
    pv = prices.assign(dollar_volume=prices.close*prices.volume).pivot(
        index='date', columns='security_id', values='dollar_volume').reindex(calendar)
    adv = pv.rolling(21, min_periods=21).mean().shift(1)
    t = trades.copy()
    t['lagged_adv21_sgd'] = [adv.loc[x.date, x.security_id] for x in t.itertuples()]
    t['participation_adv21'] = t.notional_sgd.abs()/t.lagged_adv21_sgd.replace(0, np.nan)
    t['above_1pct_actual_volume'] = t.participation > .01
    t['above_5pct_actual_volume'] = t.participation > .05
    return t


def liquidity_summary(trades):
    rows = []
    for (strategy, scenario), t in trades.groupby(['strategy', 'scenario']):
        for period, (lo, hi) in PERIODS.items():
            x = t[t.date.between(lo, hi)]
            rows.append(dict(strategy=strategy, scenario=scenario, period=period,
                trade_count=len(x), total_absolute_notional_sgd=x.notional_sgd.abs().sum(),
                median_actual_participation=x.participation.median(),
                p95_actual_participation=x.participation.quantile(.95),
                max_actual_participation=x.participation.max(),
                actual_above_1pct_count=int(x.above_1pct_actual_volume.sum()),
                actual_above_5pct_count=int(x.above_5pct_actual_volume.sum()),
                actual_above_100pct_count=int(x.participation.gt(1).sum()),
                notional_fraction_above_1pct=float(x.loc[x.above_1pct_actual_volume, 'notional_sgd'].abs().sum()/x.notional_sgd.abs().sum()) if len(x) else np.nan,
                p95_adv21_participation=x.participation_adv21.quantile(.95),
                max_adv21_participation=x.participation_adv21.max(),
                missing_adv21_count=int(x.participation_adv21.isna().sum())))
    return pd.DataFrame(rows)
