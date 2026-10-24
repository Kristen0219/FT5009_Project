"""Part 5b (step 3): daily ex-ante one-day 99% VaR by historical simulation."""
import math
import numpy as np
import pandas as pd
from volatility import HANDOFF, OUT, STRATEGIES

WINDOW = 500                                # preceding aligned daily asset-return observations
CONFIDENCE = .99


def tail_rank(n, confidence=CONFIDENCE):
    """Rank k of the k-th worst outcome: 1% of 500 -> k = 5.

    Rounding avoids 1-0.99 = 0.010000000000000009 in floating point, which would give k = 6.
    """
    return max(1, math.ceil(round(n*(1-confidence), 9)))


def historical_var(simulated, confidence=CONFIDENCE):
    """VaR as a positive loss: minus the k-th worst simulated return (no interpolation)."""
    k = tail_rank(len(simulated), confidence)
    return -float(np.sort(simulated)[k-1])


def strategy_var(asset_returns, weights, daily):
    """One forecast per session t, using only holdings and returns known at the close of t-1.

    asset_returns: aligned daily returns (date x security), including pre-2019 history.
    weights: signed end-of-day weights (date x security); long > 0, short < 0, absent = cash.
    daily: the strategy's net daily path (date, nav, daily_return).
    """
    calendar = asset_returns.index
    nav = daily.set_index('date').nav
    rows = []
    for t, actual in zip(daily.date, daily.daily_return):
        pos = calendar.get_loc(t)
        origin = calendar[pos-1]                                # previous close
        w = weights.loc[origin] if origin in weights.index else pd.Series(dtype=float)
        w = w[w != 0]                                           # held securities only
        row = dict(forecast_date=t.date(), origin_date=origin.date(),
                   nav_origin=nav.get(origin, 1_000_000.),     # first origin is the S$1m start
                   active_securities=len(w), actual_net_return=actual, missing_securities='')
        if w.empty:                                             # all cash: nothing at risk
            rows.append(dict(row, status='cash_only', var_pct=0.))
            continue
        if pos < WINDOW:                                        # fewer than 500 earlier dates
            rows.append(dict(row, status='insufficient_history', var_pct=np.nan))
            continue
        window = asset_returns.iloc[pos-WINDOW:pos][w.index]    # exactly 500 days ending t-1
        missing = window.columns[window.isna().any()]
        if len(missing):                                        # never fill, drop or shorten
            rows.append(dict(row, status='missing_return', var_pct=np.nan,
                             missing_securities=';'.join(missing)))
            continue
        simulated = window.to_numpy() @ w.to_numpy()            # today's holdings, past 500 days
        rows.append(dict(row, status='complete', var_pct=historical_var(simulated)))
    out = pd.DataFrame(rows)
    out['var_sgd'] = out.var_pct * out.nav_origin
    return out


def main():
    asset_returns = pd.read_csv(HANDOFF/'risk_handoff/asset_returns_for_var.csv.gz',
                                parse_dates=['date']).set_index('date').sort_index()
    frames = []
    for s in STRATEGIES:
        daily = pd.read_csv(HANDOFF/f'{s}_net_daily.csv', parse_dates=['date'])
        held = pd.read_csv(HANDOFF/f'risk_handoff/{s}_net_holdings.csv.gz', parse_dates=['date'])
        weights = held.pivot(index='date', columns='security_id', values='end_weight').fillna(0.)
        f = strategy_var(asset_returns, weights, daily)
        f.insert(0, 'strategy', s)
        frames.append(f)
    table = pd.concat(frames, ignore_index=True)
    OUT.mkdir(exist_ok=True)
    table.to_csv(OUT/'var_forecasts.csv', index=False)

    print(table.groupby(['strategy', 'status'], sort=False).size().unstack(fill_value=0).to_string())
    ok = table[table.status.eq('complete')]
    print(ok.groupby('strategy', sort=False).agg(mean_var_pct=('var_pct', 'mean'),
                                                  max_var_pct=('var_pct', 'max'),
                                                  mean_var_sgd=('var_sgd', 'mean'),
                                                  max_var_sgd=('var_sgd', 'max')).round(4).to_string())


if __name__ == '__main__':
    main()
