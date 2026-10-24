# Uploaded lecture alignment

The user supplied FT5009 Lectures 1–9 during implementation. They are reference material for the requested project, not instructions to execute lecture exercises or change the assignment's weekly strategy requirements. The private lecture PDFs are not republished in this repository. **Page numbers below refer to physical PDF pages, not printed slide numbers**, which differ in Lecture 8.

| Source | Verified concept | Application |
| --- | --- | --- |
| `FT5009_L08.pdf`, PDF p.16, Simple moving average | Average of n observed closes, equal weights and smoothing delay | Fixed SMA126 on aligned daily SGD total-return index; no missing-value interpolation |
| `FT5009_L08.pdf`, PDF p.21, A strategy using price and its average | Close above SMA produces a long holding state; state change produces an order | Institutional buy slot only if index > SMA, sell slot only if index < SMA; reject equality. This is trend confirmation, not an expected-return estimate. |
| `FT5009_L08.pdf`, PDF pp.42–44 | Compound returns, CAGR, drawdown from prior wealth peak | Daily-return compounding, 252/n annualisation, initial capital included in peak. Tables/plots use signed negative drawdowns; lecture positive loss magnitudes are their absolute values. |
| `FT5009_L08.pdf`, PDF pp.46–47 | Sharpe uses sample standard deviation; Sortino includes zero downside deviations | Zero risk-free/target assumption, sample SD, all sessions in downside denominator, sqrt(252) annualisation |
| `FT5009_L08.pdf`, PDF pp.52–54 | Look-ahead, survivorship, overfitting and ignoring costs | Information cut-off strictly before publication, unchanged restricted sample disclosed, no parameter sweep, 20/40bps cost paths rerun with borrow |
| `FT5009_L02.pdf`, PDF pp.16–18 | Missing-data causes, real outliers versus bad ticks, point-in-time data | No silent fill/drop of price gaps; missing history means cash; source flags remain disclosed; no post-release observations in SMA decision |
| `FT5009_L07_upload.pdf`, PDF p.12 and pp.16–17 | Impact, limit-order-book depth and liquidity | Actual-day participation and strictly lagged ADV21 diagnostics; neither is a measured spread/depth model. Orders exceeding reported daily volume expose unconstrained fills, not executable trades. |

## Explicit adaptations rather than claims about the lecture

The lecture demonstrates a short-window price/SMA long/cash rule and next-open execution. This project needs weekly institutional/retail long/short flow strategies with Member 1's execution convention. Our single enhancement therefore **filters institutional flow slots** rather than replacing them with standalone daily SMA trading. It uses 126 aligned daily index levels (approximately half a year), symmetric short confirmation, SGD total-return inputs to avoid mechanical dividend-price drops, and the unchanged first benchmark close strictly after report publication. There is no daily rebalance between reports.

The 126-session horizon is an explicit design choice, not a lecture-prescribed parameter or a claim of an optimal setting. The SMA implementation was fixed in response to the supplied lecture's direct price-versus-average teaching, then simulated; no grid search or selection of whichever lookback produces the best full-period result is performed. Earlier prototype endpoint-return figures are not the final SMA results and must not be mixed into the report. Final audit metadata and decision columns identify the SMA rule explicitly.

The assignment says a development/test split is not required. The lecture's walk-forward recommendation motivates a limitation disclosure, not an invented claim that out-of-sample testing was performed. The supplied slides do not certify data quality, actual borrow availability or profitability. Names, matriculation numbers, lecture authorship and student review are not invented.
