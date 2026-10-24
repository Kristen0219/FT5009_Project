# Course References

Page numbers refer to PDF pages rather than printed slide numbers.

| Source | Verified concept | Application |
| --- | --- | --- |
| `FT5009_L08.pdf`, PDF p.16, Simple moving average | Average of n observed closes, equal weights and smoothing delay | Fixed SMA126 on aligned daily SGD total-return index; no missing-value interpolation |
| `FT5009_L08.pdf`, PDF p.21, A strategy using price and its average | Close above SMA produces a long holding state; state change produces an order | Institutional buy slot only if index > SMA, sell slot only if index < SMA; reject equality. This is trend confirmation, not an expected-return estimate. |
| `FT5009_L08.pdf`, PDF pp.42–44 | Compound returns, CAGR, drawdown from prior wealth peak | Daily-return compounding, 252/n annualisation, initial capital included in peak. Tables/plots use signed negative drawdowns; lecture positive loss magnitudes are their absolute values. |
| `FT5009_L08.pdf`, PDF pp.46–47 | Sharpe uses sample standard deviation; Sortino includes zero downside deviations | Zero risk-free/target assumption, sample SD, all sessions in downside denominator, sqrt(252) annualisation |
| `FT5009_L08.pdf`, PDF pp.52–54 | Look-ahead, survivorship, overfitting and ignoring costs | Information cut-off strictly before publication, unchanged restricted sample disclosed, no parameter sweep, 20/40bps cost paths rerun with borrow |
| `FT5009_L02.pdf`, PDF pp.16–18 | Missing-data causes, real outliers versus bad ticks, point-in-time data | No silent fill/drop of price gaps; missing history means cash; source flags remain disclosed; no post-release observations in SMA decision |
| `FT5009_L07_upload.pdf`, PDF p.12 and pp.16–17 | Impact, limit-order-book depth and liquidity | Actual-day participation and strictly lagged ADV21 diagnostics; neither is a measured spread/depth model. Orders exceeding reported daily volume expose unconstrained fills, not executable trades. |

## Strategy adaptations

Lecture 8 demonstrates a short-window price/SMA long-or-cash rule. Here, the SMA confirms weekly institutional flow signals: the index must be above the average for a buy and below it for a short. The window is fixed at 126 daily observations, using the SGD total-return index to account for distributions. Execution follows Member 1's first benchmark close strictly after publication.

The window was not selected through a parameter search. The results are descriptive full-sample comparisons; no out-of-sample performance is reported. Data coverage, execution and borrowing limitations remain as documented in the report.
