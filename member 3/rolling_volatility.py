"""Part 5a (step 2): rolling 21-trading-day annualised volatility of daily net returns."""
import os
from volatility import ROOT, HANDOFF, OUT, STRATEGIES, TRADING_DAYS

os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')                       # write files only; no display window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WINDOW = 21                                 # about one trading month
LABELS = {'retail': 'Smart Retail Flow FT5009', 'institutional': 'Smart Insti Flow FT5009',
          'enhanced': 'Enhanced Insti: trend confirmation'}
COLORS = {'retail': '#bc4b51', 'institutional': '#2b6cb0', 'enhanced': '#20856b'}  # as Member 2


def rolling_volatility(daily_returns, window=WINDOW):
    """Sample SD of the latest `window` daily returns (ending on day t), scaled by sqrt(252).

    The first window-1 dates have too few observations and stay NaN.
    """
    return daily_returns.rolling(window, min_periods=window).std(ddof=1) * np.sqrt(TRADING_DAYS)


def main():
    rolling = {}
    for s in STRATEGIES:
        daily = pd.read_csv(HANDOFF/f'{s}_net_daily.csv', parse_dates=['date']).set_index('date')
        rolling[s] = rolling_volatility(daily.daily_return)
    rolling = pd.DataFrame(rolling)

    OUT.mkdir(exist_ok=True)
    rolling.to_csv(OUT/'rolling_volatility.csv', index_label='date')

    fig, ax = plt.subplots(figsize=(10, 4.5), layout='constrained')
    for s in STRATEGIES:
        ax.plot(rolling.index, rolling[s]*100, color=COLORS[s], lw=1.2, label=LABELS[s])
    ax.set_title(f'Rolling {WINDOW}-trading-day annualised volatility of daily net returns')
    ax.set_ylabel('Annualised volatility (%)')
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.25)
    ax.legend(frameon=False, fontsize=8)
    (OUT/'figures').mkdir(exist_ok=True)
    fig.savefig(OUT/'figures/rolling_volatility.png', dpi=180)
    fig.savefig(OUT/'figures/rolling_volatility.pdf')
    plt.close(fig)

    summary = pd.DataFrame({'mean': rolling.mean(), 'min': rolling.min(), 'max': rolling.max(),
                            'max_date': rolling.idxmax().dt.date})
    print((summary[['mean', 'min', 'max']]*100).round(2).join(summary.max_date).to_string())


if __name__ == '__main__':
    main()
