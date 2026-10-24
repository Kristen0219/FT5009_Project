"""Part 5a (step 1): annualised realised volatility of each strategy's daily net returns."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
HANDOFF = ROOT.parent/'member 2/results'   # Member 2's net daily paths
OUT = ROOT/'results'
STRATEGIES = ['retail', 'institutional', 'enhanced']
TRADING_DAYS = 252                          # same annualisation convention as Member 2


def annualised_volatility(daily_returns):
    """Sample standard deviation of daily returns (ddof=1), scaled by sqrt(252)."""
    return daily_returns.std(ddof=1) * np.sqrt(TRADING_DAYS)


def main():
    rows = []
    for s in STRATEGIES:
        daily = pd.read_csv(HANDOFF/f'{s}_net_daily.csv', parse_dates=['date'])
        r = daily.daily_return                # net of transaction costs and borrow
        rows.append(dict(strategy=s, sessions=len(r),
                         first_date=daily.date.min().date(), last_date=daily.date.max().date(),
                         daily_volatility=r.std(ddof=1),
                         annualised_volatility=annualised_volatility(r)))
    table = pd.DataFrame(rows)
    OUT.mkdir(exist_ok=True)
    table.to_csv(OUT/'annualised_volatility.csv', index=False)
    print(table.to_string(index=False))


if __name__ == '__main__':
    main()
