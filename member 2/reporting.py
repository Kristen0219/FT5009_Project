"""Generate portable English report text, A4 report extract and publication figures."""
from pathlib import Path
import json
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

LABELS = {'retail':'Smart Retail Flow FT5009', 'institutional':'Smart Insti Flow FT5009',
          'enhanced':'Enhanced Insti: trend confirmation', 'benchmark':'ES3 NAV total-return proxy'}
COLORS = {'retail':'#bc4b51','institutional':'#2b6cb0','enhanced':'#20856b','benchmark':'#555555'}
ORDER = ['retail','institutional','enhanced','benchmark']


def pct(v):return f'{v:.2%}'


def markdown_table(frame, percent_cols=()):
    f = frame.copy()
    for col in percent_cols:
        f[col] = f[col].map(lambda x:pct(x) if pd.notna(x) else 'N/A')
    for col in f.select_dtypes('float'):
        f[col] = f[col].map(lambda x:f'{x:.3f}' if pd.notna(x) else 'N/A')
    return '| ' + ' | '.join(f.columns) + ' |\n|' + '|'.join(['---']*len(f.columns)) + '|\n' + '\n'.join('| '+' | '.join(map(str,row))+' |' for row in f.itertuples(index=False,name=None))


def plot_paths(paths, benchmark):
    fig, axes = plt.subplots(2,1,figsize=(10,7),sharex=True,layout='constrained')
    all_series = {s:paths[s,'net'][['date','daily_return']] for s in ORDER[:-1]}
    all_series['benchmark'] = benchmark[['date','daily_return']]
    initial = pd.Timestamp('2018-12-31')
    for s,d in all_series.items():
        wealth = np.r_[1.,(1+d.daily_return).cumprod().to_numpy()]
        dates = [initial,*d.date]
        dd = wealth/np.maximum.accumulate(wealth)-1
        axes[0].plot(dates,wealth-1,label=LABELS[s],color=COLORS[s],lw=1.4)
        axes[1].plot(dates,dd,color=COLORS[s],lw=1.2)
    axes[0].set_title('Net cumulative returns: unchanged rules, common calendar')
    axes[1].set_title('Drawdowns (initial S$1m included in running peak)')
    for ax in axes:
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=8,loc='best')
    return fig


def plot_costs(summary):
    fig, ax = plt.subplots(figsize=(9,4),layout='constrained')
    full = summary[summary.period.eq('full')]
    x = np.arange(3)
    for i,(case,label) in enumerate([('gross','Gross: no fees/borrow'),('net','Net: 20 bps + 3% borrow'),('double_cost','Double: 40 bps + 3% borrow')]):
        values = [full[(full.strategy.eq(s)) & full.scenario.eq(case)].cumulative_return.iloc[0] for s in ORDER[:-1]]
        ax.bar(x+(i-1)*.24,values,width=.24,label=label)
    ax.set_xticks(x,['Retail','Institutional','Enhanced institutional'])
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title('Full-period cumulative returns: cost stress')
    ax.axhline(0,color='black',lw=.6)
    ax.legend(fontsize=8)
    ax.grid(axis='y',alpha=.2)
    return fig


def pdf_text(ax,x,y,text,width=105,size=9,spacing=.021):
    for paragraph in text.split('\n'):
        for line in textwrap.wrap(paragraph,width=width) or ['']:
            ax.text(x,y,line,fontsize=size,va='top',transform=ax.transAxes)
            y-=spacing
        y-=spacing*.3
    return y


def generate(out, summary, liq, paths, benchmark, decisions, audit):
    figs = out/'figures'
    figs.mkdir(exist_ok=True)
    full = summary[summary.period.eq('full')]
    net = full[full.scenario.isin(['net','reference'])].set_index('strategy').loc[ORDER]
    gross = full[full.scenario.eq('gross')].set_index('strategy')
    double = full[full.scenario.eq('double_cost')].set_index('strategy')
    lnet = liq[(liq.period.eq('full')) & liq.scenario.eq('net')].set_index('strategy')
    difference = net.loc['enhanced','cumulative_return']-net.loc['institutional','cumulative_return']
    winner = 'institutional' if net.loc['institutional','cumulative_return']>net.loc['retail','cumulative_return'] else 'retail'
    text = (
        f"On this restricted sample, {winner} flow has the higher full-period net cumulative return. "
        f"The enhancement changes institutional net cumulative return by {difference*100:.2f} percentage points "
        f"({pct(net.loc['institutional','cumulative_return'])} to {pct(net.loc['enhanced','cumulative_return'])}). "
        f"Its annualised volatility is {pct(net.loc['enhanced','annualised_volatility'])} "
        f"versus original {pct(net.loc['institutional','annualised_volatility'])}; maximum drawdown is "
        f"{pct(net.loc['enhanced','maximum_drawdown'])}, Sharpe {net.loc['enhanced','sharpe']:.3f} and "
        f"Sortino {net.loc['enhanced','sortino']:.3f}, versus original institutional Sharpe "
        f"{net.loc['institutional','sharpe']:.3f}. All three strategies lose money after base costs; "
        f"the enhancement reduces losses and drawdown but does not make this trading rule viable. "
        f"Its mean gross exposure falls from {pct(net.loc['institutional','mean_gross_exposure'])} "
        f"to {pct(net.loc['enhanced','mean_gross_exposure'])}; lower exposure need not improve signal alpha."
    )
    cost_text = ' '.join(
        f"{s.title()}: gross {pct(gross.loc[s,'cumulative_return'])}, net {pct(net.loc[s,'cumulative_return'])}, "
        f"doubled-cost {pct(double.loc[s,'cumulative_return'])}; annual one-way turnover "
        f"{net.loc[s,'annualised_one_way_turnover']:.2f}x NAV, mean gross exposure {pct(net.loc[s,'mean_gross_exposure'])}."
        for s in ORDER[:-1])
    liq_text = ' '.join(
        f"{s.title()}: {int(lnet.loc[s,'actual_above_1pct_count'])}/{int(lnet.loc[s,'trade_count'])} trades exceed "
        f"1% of execution-day vendor volume; maximum {pct(lnet.loc[s,'max_actual_participation'])}; "
        f"lagged ADV21 maximum {pct(lnet.loc[s,'max_adv21_participation'])}; "
        f"{int(lnet.loc[s,'actual_above_100pct_count'])} orders exceed 100% of reported daily volume."
        for s in ORDER[:-1])
    periods = summary[summary.scenario.isin(['net','reference'])].pivot(index='strategy',columns='period',values='cumulative_return').loc[ORDER]
    rules = (
        'One fixed rule, adapted from FT5009 Lecture 8 (physical PDF pp. 16 and 21): confirm institutional '
        'Weekly Top 10 buys when the SGD total-return index is above its 126-session simple moving average '
        '(SMA), and sells when it is below. Both the current index and its SMA end on the last benchmark '
        'session strictly before the report publication date. Require 126 aligned nonmissing closes; equality '
        'or missing history rejects the slot. The total-return index avoids mechanical dividend-date price '
        'drops. Six months is a fixed medium-term smoothing horizon, not selected by maximising this sample. '
        'The lecture illustrates long/cash price-versus-SMA; we extend it symmetrically to the required '
        'long/short institutional flow slots, retaining weekly publication-driven execution. No parameter '
        'sweep or full-period optimisation is performed.'
    )
    execution = (
        'All strategies retain Member 1\'s same 125 fixed pre-2019 canonical histories, 396 reports and '
        '15,840 signals; S$1m initial NAV each; 49% per side, ten 4.9% slots, 10% name cap; no redistribution '
        'of rejected/unavailable slots. Existing holdings earn execution-day returns, then rebalance at the '
        'first benchmark close strictly after publication. A rejected old holding exits at that rebalance '
        'unless zero-volume rules freeze it. Frozen holdings reserve their side budget. Cash/short proceeds '
        'earn zero, fractional total-return units and no final liquidation. All borrowable is assumed, '
        'with 3% annual calendar-day borrow on prior-close short value. No margin calls or market impact are modelled.'
    )
    conventions = (
        'Returns are simple daily SGD portfolio returns on a common 1,945-session calendar. Cumulative '
        'return = product(1+r)-1; annualised return = product(1+r)^(252/n)-1. Realised volatility uses '
        'sample standard deviation times sqrt(252). Maximum drawdown includes initial wealth in the peak; '
        'we report signed negative drawdowns, equivalent to the lecture\'s positive loss magnitude. '
        'Sharpe = mean(r)/sd(r)*sqrt(252), with zero risk-free rate. Sortino = mean(r)/sqrt(mean(min(r,0)^2))*sqrt(252), '
        'zero daily target and all n sessions in the downside denominator. Ratios with zero denominators '
        'are undefined. Ratios use arithmetic mean, not CAGR. Each subperiod compounds the existing daily '
        'path (including its first daily return); strategies are not reset or retuned at period boundaries. '
        'Subperiod drawdowns use local initial wealth; actual dollar fees retain the continuing portfolio scale.'
    )
    limitations = (
        'These are descriptive restricted-sample results, not a causal test that investor type predicts returns. '
        'No development/test split is required by the assignment; no claim of out-of-sample validation is made. '
        'The ES3 official NAV/distribution reinvestment proxy is suitable SGD market context but is long-only, '
        'has different market exposure, and is neither the official STI total-return index nor an executable '
        'ETF-price portfolio. The strategies\' Sharpe comparisons do not adjust for beta or unequal realised exposure. '
        'Inherited missing/delisted histories, fixed-universe/survivorship bias, candidate identities, current '
        'vendor vintages, uncertain publication timestamps, corporate actions and lagged FX remain. '
        'Vendor split-adjusted price/volume pairs approximate turnover capacity, not certified exchange '
        'dollar volume. Execution-day participation is ex-post; strictly lagged 21-session mean dollar volume '
        'is a separate planning proxy. No liquidity filter is silently imposed. Fixed fees omit spread '
        'variation, nonlinear impact, borrow recalls and actual availability. Profitable cost-stress paths '
        'are therefore not proof of implementability, and negative paths fail this simplified viability test. '
        'Orders exceeding 100% of reported daily volume could not be fully executed within that day on '
        'the recorded volume basis. They expose an unconstrained-fill limitation or a vendor-basis issue '
        'requiring investigation, not merely a modest slippage adjustment; see liquidity_extreme_trades.csv. '
        'No claim of executable profits is justified.'
    )
    stability = []
    for period in ['2019–2021','2022–2023','2024–Sep2026']:
        inst,enh = periods.loc['institutional',period],periods.loc['enhanced',period]
        stability.append(f'{period}: institutional {pct(inst)}, enhanced {pct(enh)} ({(enh-inst)*100:+.2f} percentage points).')
    stable = all(periods.loc['enhanced',p]>=periods.loc['institutional',p] for p in ['2019–2021','2022–2023','2024–Sep2026'])
    stability_text = ' '.join(stability) + (' The enhancement improves cumulative return in every prescribed subperiod.' if stable else ' The enhancement does not improve cumulative return in every prescribed subperiod; full-period rankings mask instability.')
    main_cols = ['cumulative_return','annualised_return','annualised_volatility','maximum_drawdown','sharpe','sortino']
    report = f'''# Member 2 — Institutional enhancement and performance evaluation

This chapter covers the institutional strategy enhancement and performance evaluation in Parts 3–4.

## 3. Fixed enhancement and common execution

{rules}

{execution}

The filter accepted {int(decisions.accepted.sum())} of {len(decisions)} institutional source slots, including unavailable-history slots in the denominator. Decisions and information dates are in enhancement_decisions.csv. Retail and original institutional NAV paths independently match every Member 1 daily NAV across gross/net/doubled costs. Filtering uses a unique absent quote key to preserve ten slots; it never changes vendor prices or source data. Apparent filtered quote exclusions are intentional cash slots, not missing real tickers.

## 4a. Full-period performance

{conventions}

Net strategy returns and the benchmark reference:

{markdown_table(net[main_cols].reset_index(),main_cols[:4])}

{text}

![Net cumulative returns and drawdowns](figures/net_returns_drawdowns.png)

## 4b. Prescribed subperiods, unchanged rules

{markdown_table(periods.reset_index(),periods.columns)}

{stability_text}

The complete period and scenario results are in performance.csv. Annualised measures account for the different period lengths. Full-period drawdowns can span period boundaries.

## 4c. Costs, turnover and trading feasibility

Gross removes both transaction and borrow fees. Net charges 20 bps of absolute traded notional per side plus 3% annual borrowing; stress doubles transaction cost to 40 bps and keeps borrowing at 3%. All nine paths are rerun rather than subtracting a terminal fee estimate, so costs affect later NAV, sizing and borrow. Gross-to-net includes borrowing, not only transaction costs. Turnover is sum(abs(trade notional)/pre-cost rebalance NAV), annualised by 252/n; no division by two.

{cost_text}

{liq_text}

Execution-day participation = abs(SGD notional)/(SGD vendor close * vendor share volume). ADV21 participation uses the mean of 21 aligned preceding sessions of vendor dollar volume, shifted one session; missing/zero ADV is unavailable, not zero. We report 1%/5% flags as diagnostic levels, not guaranteed executable limits. Full trade-level figures, period summaries, notional-weighted 1% exceedance shares and missing-ADV counts are in trades_and_liquidity.csv.gz and liquidity_summary.csv. Exposure reduction partly explains changed performance and turnover; this is not a constant-exposure alpha comparison.

![Gross/net/cost stress](figures/cost_stress.png)

## Limitations, conclusion and Member 3 handoff

{limitations}

The SMA filter reduces net losses in all three subperiods, but the enhanced strategy remains unprofitable after costs. Its smaller drawdown comes with slightly higher realised volatility than the original institutional strategy. Lower exposure and turnover account for part of the difference.

There are {audit['active_flagged_return_rows']} active start-of-day positions on the flagged >50% daily returns. The risk inputs retain Member 1's quarantine of unverified observations. The 500-session coverage gaps are {json.dumps(audit['var_history_gaps'])}. Signed holdings, daily NAV and aligned risk returns are provided for Member 3's rolling volatility and 99% historical VaR calculations. Missing observations remain missing.

## Sources, attribution and reproducibility

- Assignment: FT5009 Group Project AY2026/27, group_project.pdf, Parts 3–4 and 6.
- SGX Weekly Top 10 source reports, official ES3 NAV/distributions, vendor prices and source checksums: Member 1's collected data, README.md and REQUIREMENTS_AUDIT.md. Source portal: https://www.sgx.com/stock-exchange/data-reports?reportType=203 .
- FT5009 Lecture 8, FT5009_L08.pdf: physical PDF pp. 16 and 21 (SMA and price-versus-average strategy), pp. 42–47 (performance formulas), pp. 52–54 (bias, overfitting and realistic costs). The lecture illustrates short windows and a long/cash rule; 126 daily sessions, SGD total-return inputs and symmetric short confirmation are our stated adaptations.
- FT5009 Lecture 2, FT5009_L02.pdf, physical PDF pp. 16–18: missing data, outlier review and point-in-time information. FT5009 Lecture 7, FT5009_L07_upload.pdf, physical PDF pp. 12 and 16–17: impact, order-book depth and execution liquidity.
- Contributions: Member 1 collected the data and developed the baseline engine. Member 2 added the enhancement, evaluation, figures and tests.
- AI assistance: OpenAI Codex was used for coding, analysis and drafting.

Run instructions are in [README.md](../README.md). Source hashes and checks are recorded in validation.json; output checksums are in artifact_sha256.json.
'''
    (out/'MEMBER2_REPORT.md').write_text(report)
    handoff = '''# Member 3 risk handoff

These files are generated from the same current Member 1 fixed pre-2019 universe. `retail`, `institutional`, `enhanced` identify the three strategies. `../*_net_daily.csv` supplies dates, NAV, realised net return, costs and signed exposures. `*_net_holdings.csv.gz` supplies `start_weight` (prior-close value / prior NAV), `end_weight` (current close / current NAV) and signed `end_value_sgd` for each security/date. An omitted security has zero holding, not zero asset return. All dates use the common benchmark calendar.

For forecast session t, use holdings at close t-1, NAV at t-1, and exactly the 500 aligned daily asset-return observations ending t-1, including pre-2019 observations. For the first 2019 session the portfolio is cash. Use `asset_returns_for_var.csv.gz`; the original 29 unverified extreme returns have been set missing by Member 1. `forecast_coverage.csv` reports complete windows for the actual current holdings; an unavailable required return invalidates that date's whole forecast. Do not drop rows to manufacture 500 observations, fill missing returns with zero or clip genuine tails. Use signed weights for long/short historical-simulation portfolio returns; state quantile interpolation and whether predictable next-day borrow/transaction costs are included. VaR dollar forecasts use the previous-close net NAV. Actual-next-day net return used in any comparison includes costs and may change holdings at that close; explain this distinction.

`active_flagged_returns.csv` identifies actual strategy P&L exposed to unverified extremes. An empty file is a useful check, not certification of all data. Member 2 provides coverage only, not 99% VaR estimates, risk backtesting or the Part 5 discussion. Compute rolling 21-session net realised volatility and the required VaR in Member 3's own contribution. Preserve all calendar dates, including documented gaps.
'''
    (out/'risk_handoff/README.md').write_text(handoff)
    fig = plot_paths(paths,benchmark)
    fig.savefig(figs/'net_returns_drawdowns.png',dpi=180)
    fig.savefig(figs/'net_returns_drawdowns.pdf')
    plt.close(fig)
    fig = plot_costs(summary)
    fig.savefig(figs/'cost_stress.png',dpi=180)
    fig.savefig(figs/'cost_stress.pdf')
    plt.close(fig)
    with PdfPages(out/'MEMBER2_REPORT_A4.pdf') as pdf:
        fig = plt.figure(figsize=(8.27,11.69))
        ax = fig.add_axes([.07,.05,.86,.9]);ax.axis('off')
        y=pdf_text(ax,0,.99,'Member 2 | Parts 3–4: Enhancement and performance',size=14,width=75,spacing=.03)
        y=pdf_text(ax,0,y-.01,rules,width=106,size=8.6,spacing=.019)
        y=pdf_text(ax,0,y-.01,execution,width=106,size=8.6,spacing=.019)
        y=pdf_text(ax,0,y-.01,'Full-period NET performance (2019–September 2026)',size=10,spacing=.024)
        cells=[]
        for s in ORDER:
            row=net.loc[s]
            cells.append([s.title(),*[pct(row[c]) for c in main_cols[:4]],f'{row.sharpe:.2f}',f'{row.sortino:.2f}'])
        table=ax.table(cellText=cells,colLabels=['Strategy','Cum.','Ann.','Vol.','MDD','Sharpe','Sortino'],
                       bbox=[0,y-.145,1,.13],cellLoc='center')
        table.auto_set_font_size(False);table.set_fontsize(8)
        y-=.17
        y=pdf_text(ax,0,y,text,width=106,size=8.6,spacing=.019)
        y=pdf_text(ax,0,y-.01,conventions,width=110,size=7.8,spacing=.017)
        pdf_text(ax,0,.025,'FT5009 | Institutional strategy enhancement and performance evaluation  |  1/3',size=7,width=120)
        pdf.savefig(fig);plt.close(fig)
        fig=plot_paths(paths,benchmark)
        fig.set_size_inches(8.27,11.69)
        fig.suptitle('Member 2 | Common-period net return paths and drawdowns',fontsize=12)
        pdf.savefig(fig);plt.close(fig)
        fig=plt.figure(figsize=(8.27,11.69))
        ax=fig.add_axes([.07,.05,.86,.9]);ax.axis('off')
        y=pdf_text(ax,0,.99,'Period stability, cost stress and trading feasibility',size=13,width=80,spacing=.028)
        pcols=['2019–2021','2022–2023','2024–Sep2026']
        cells=[[s.title(),*[pct(periods.loc[s,p]) for p in pcols]] for s in ORDER]
        table=ax.table(cellText=cells,colLabels=['Net / benchmark',*pcols],bbox=[0,y-.16,1,.14],cellLoc='center')
        table.auto_set_font_size(False);table.set_fontsize(8)
        y-=.19
        y=pdf_text(ax,0,y,stability_text,width=108,size=8.4,spacing=.018)
        y=pdf_text(ax,0,y-.01,cost_text,width=108,size=8.4,spacing=.018)
        y=pdf_text(ax,0,y-.01,liq_text,width=108,size=8.4,spacing=.018)
        y=pdf_text(ax,0,y-.01,'Gross: zero fees/borrow. Net: 20 bps one-way transaction cost + 3% annual borrow. Stress: 40 bps + unchanged borrow. Turnover sums absolute traded notional / pre-cost NAV; annualised 252/n. All cost scenarios rerun the accounting. Liquidity is a vendor-volume proxy; actual-day volume is ex-post, ADV21 is strictly lagged. Missing slots remain cash; lower exposure is not isolated alpha.',width=108,size=8.1,spacing=.0175)
        pdf_limitations = ('The enhancement reduces losses in all three subperiods but remains negative after costs. '
            'The fixed sample, missing/delisted histories, candidate identifiers, vendor corporate actions, '
            'current data vintages and uncertain historical publication timestamps limit inference. '
            'ES3 official NAV total return is long-only market context, not STI total return or an executable ETF-price path. '
            'No causal investor-skill or out-of-sample claim is made. Unequal realised exposure matters. '
            'Volume uses vendor price/volume pairs: orders above 100% of daily volume cannot be fully filled '
            'within that day on the recorded basis. This requires execution constraints or vendor investigation; '
            'the current paths are unconstrained accounting simulations. Lagged ADV is a proxy, not guaranteed liquidity. '
            'Assumed universal borrow, zero cash interest, no recalls, margin or nonlinear impact further limit realism. '
            'All three net strategies and doubled-cost paths lose money: none establishes trading viability.')
        y=pdf_text(ax,0,y-.01,pdf_limitations,width=112,size=7.5,spacing=.016)
        y=pdf_text(ax,0,y-.008,'Sources: FT5009 AY2026/27 assignment; SGX Weekly Top 10 and Member 1 collected data/audit; FT5009 L08 physical PDF pp. 16/21 (SMA rule), 42–47 (performance), 52–54 (pitfalls); L02 pp. 16–18 (data/PIT); L07 pp. 12/16–17 (impact/depth). AI: OpenAI Codex assisted with code, analysis and text. Full formulas, tables and risk inputs accompany this chapter.',width=112,size=7.1,spacing=.015)
        pdf_text(ax,0,.025,'FT5009 | Institutional strategy enhancement and performance evaluation  |  3/3',size=7,width=120)
        pdf.savefig(fig);plt.close(fig)
