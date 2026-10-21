# Member 1 — Report Sections (method draft; empirical coverage pending)

**Do not submit unchanged. Populate verified data coverage/exclusions and replace assumptions if the group chooses different fixed parameters. No empirical result is asserted here.**

## 1. Data Collection and Cleaning

The sample is defined by SGX report publication dates from 1 January 2019 to 30 September 2026. For each available report, we use only the Weekly Top 10 institutional net-buy, institutional net-sell, retail net-buy and retail net-sell tables. We do not mix weekly rankings with year-to-date rankings or infer zero flows for securities absent from these tables. The report inventory records observation periods, actual publication dates, source URLs, raw documents and file hashes.

Daily SGD total-return indices, unadjusted closing prices and share volumes are required for the union of securities appearing in the historical signal tables. A stable security identifier links historical SGX codes and corporate identities. A suitable benchmark is the STI total-return index, or a documented investable STI ETF total-return proxy. Benchmark trading dates form the common calendar. Earlier prices are retained to provide at least 500 aligned prior daily returns for initial risk forecasts where available.

Corporate-action adjustments must be verified against the data vendor's total-return methodology. Foreign-currency assets require contemporaneous SGD conversion. IPOs, delistings, code changes, suspensions and unavailable histories are recorded individually. Newly listed securities may enter the trading strategy when a valid signal and executable price exist, but can lack the history needed for VaR; this is disclosed separately rather than silently excluding them from all trading. Missing held-asset returns or settlement prices must be resolved explicitly before backtesting continues. No missing return is automatically replaced by zero.

**Insert after collection:** number of reports by year, earliest/latest release, missing/unavailable reports with reasons, number of unique securities, price-source/export details, benchmark identity, corporate actions handled, exclusions by reason and their potential survivorship/coverage bias. If report gaps are unresolved, restrict and label the actual sample rather than claiming full-period results.

## 2. Baseline Backtesting Methodology

Smart Retail Flow FT5009 and Smart Insti Flow FT5009 each start with S$1,000,000 and follow their respective investors' weekly net-buy and net-sell lists. At each rebalance, the target allocation is 49% long and 49% short, equally weighted within each side and capped at 10% of NAV per security. Unavailable allocations remain in cash. Both strategies use identical rules; signal source is the principal difference.

To avoid trading on unpublished information, orders execute at the close of the first benchmark trading session strictly after the actual local publication date. This conservative convention does not assume that a report was available before the opening auction. Daily returns before that execution close accrue to previous holdings. Securities absent from the next report exit, continuing names rebalance and opposite-direction signals reverse the position. Holdings remain unchanged in synthetic total-return units between rebalances. Exposure caps apply at rebalance targets and may drift thereafter. The final NAV is marked to market without mandatory liquidation.

A one-way transaction-cost assumption of 20 basis points is applied to absolute traded notional, including opening, closing and reversal trades. Shorts incur an assumed annual borrow fee of 3%, accrued on previous-close short notional using calendar days/365. Cash and restricted short-sale collateral earn zero interest. Short-sale proceeds are not reused to increase target gross exposure. Historical borrow availability must be documented; where unavailable, an all-borrowable assumption must be explicitly labelled and tested as a limitation. The model does not simulate recalls or broker-specific margin calls.

Net returns include transaction and borrow costs. A gross counterfactual removes both, while a doubled-cost scenario raises transaction costs to 40 basis points and retains the same borrowing assumption. Daily signed holdings, returns, NAV, trades, exclusions and turnover are exported for performance and risk analysis. Trade notional divided by closing price times daily share volume provides an ex-post liquidity diagnostic, rather than a filter using information unavailable before execution.

The implementation uses fractional total-return units as an economic portfolio approximation. It therefore captures adjusted-price returns and short dividend exposure, but does not reproduce actual board-lot trades, dividend cash timing, execution slippage or market impact. The selected cost and borrowing values are modelling assumptions, not verified historical brokerage quotes. These limitations affect interpretation of trading feasibility.

## References to complete

- FT5009 Group Project AY2026/27 assignment brief (course material).
- Singapore Exchange. Data Reports: Fund Flow Weekly Trackers. https://www.sgx.com/stock-exchange/data-reports?reportType=203 (add access date and individual report references).
- Add actual daily-price, benchmark, FX, corporate-action and borrowing sources after collection; do not list an unused vendor as a used source.

## Contribution / AI assistance

Member 1: report inventory and Weekly Top 10 extraction; security mapping and daily data cleaning; baseline long/short backtesting; data and accounting validation; Sections 1–2 and handoff files. Only claim collection/verification after it is done.

Disclose AI assistance with implementation and drafting, and accurately describe the group's independent validation.
