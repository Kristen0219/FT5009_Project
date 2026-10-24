"""Part 5b (step 3, figures): VaR forecasts against realised net returns, and dollar VaR."""
from rolling_volatility import OUT, STRATEGIES, LABELS, COLORS, plt   # also sets up matplotlib
import pandas as pd


def load():
    """Read var.py's output; run var.py first."""
    return pd.read_csv(OUT/'var_forecasts.csv', parse_dates=['forecast_date'])


def plot_pct(table):
    """One panel per strategy: daily net return, -VaR line, losses beyond VaR, shaded gaps."""
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True, layout='constrained')
    for ax, s in zip(axes, STRATEGIES):
        f = table[table.strategy == s]
        gap = f.status.isin(['missing_return', 'insufficient_history'])
        complete = f.status.eq('complete')                           # cash-only days carry no VaR
        beyond = f[complete & (f.actual_net_return < -f.var_pct)]
        ax.scatter(f.forecast_date, f.actual_net_return*100, s=3, color='#9a9a9a',
                   label='Actual net return')
        ax.plot(f.forecast_date, -f.var_pct*100, color=COLORS[s], lw=1.1,
                label='−99% VaR')                                    # gaps break the line
        ax.scatter(beyond.forecast_date, beyond.actual_net_return*100, s=18, marker='x',
                   color='black', zorder=3, label=f'Loss beyond VaR ({len(beyond)})')
        for d in f.forecast_date[gap]:
            ax.axvspan(d, d + pd.Timedelta(days=1), color='#f2b134', alpha=.4, lw=0)
        ax.axhline(0, color='black', lw=.5)
        ax.set_title(f'{LABELS[s]}  ({int(gap.sum())} coverage-gap sessions shaded)')
        ax.set_ylabel('% of previous NAV')
        ax.grid(alpha=.25)
        ax.legend(frameon=False, ncol=3, fontsize=8, loc='lower left')
    fig.suptitle('Daily ex-ante one-day 99% historical-simulation VaR and realised net returns')
    return fig


def plot_sgd(table):
    """Dollar VaR = VaR % x previous-close net NAV, all strategies on one axis."""
    fig, ax = plt.subplots(figsize=(10, 4), layout='constrained')
    for s in STRATEGIES:
        f = table[table.strategy == s]
        ax.plot(f.forecast_date, f.var_sgd/1000, color=COLORS[s], lw=1.1, label=LABELS[s])
    ax.set_title('Daily ex-ante one-day 99% VaR in Singapore dollars')
    ax.set_ylabel('SGD thousand')
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.25)
    ax.legend(frameon=False, fontsize=8)
    return fig


def save(fig, name):
    (OUT/'figures').mkdir(exist_ok=True)
    fig.savefig(OUT/'figures'/f'{name}.png', dpi=180)
    fig.savefig(OUT/'figures'/f'{name}.pdf')
    plt.close(fig)


def main():
    table = load()
    save(plot_pct(table), 'var_forecasts_pct')
    save(plot_sgd(table), 'var_forecasts_sgd')
    print('Saved var_forecasts_pct and var_forecasts_sgd (.png, .pdf)')


if __name__ == '__main__':
    main()
