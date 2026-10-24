# Member 2 assignment mapping

Source of requirements: the user's supplied `group_project.pdf`, FT5009 Group Project AY2026/27. The screenshot assigns Member 2 to Parts 3–4 and their own report/code chapter. The inaccessible shared chat is not treated as evidence for additional requirements.

| Requirement | Implementation/evidence |
| --- | --- |
| 3a One justified course-concept enhancement | `enhancement.py`: fixed 126-session price-versus-SMA confirmation, directly adapted from supplied Lecture 8 physical PDF pp. 16/21; symmetric short and total-return adaptations stated. `LECTURE_ALIGNMENT.md` identifies verified course references. No parameter optimisation. |
| 3b Implement, compare with original, fix rules | `run_member2.py`: all nine original/enhanced and cost paths; common universe and unchanged Member 1 execution engine. `enhancement_decisions.csv` logs every information date and accepted/rejected slot. No tuning API or parameter sweep. |
| 4a All three strategies and suitable benchmark, cumulative returns/drawdowns | `figures/net_returns_drawdowns.png` and `.pdf`: net paths and ES3 NAV/distribution total-return proxy on identical dates, with initial capital in drawdown peaks. |
| 4a Cumulative/annual return, annual realised vol, max drawdown, Sharpe, Sortino | `performance.csv` plus report tables. Formulas, 252-session convention, zero risk-free/target and downside denominator stated explicitly. |
| 4b 2019–2021, 2022–2023, Jan2024–Sep2026, full period | All metrics for every period and scenario in `performance.csv`; unchanged full-period holdings/returns sliced at boundaries. Report discusses stability. |
| 4c Gross/net, turnover, volume-based liquidity, doubled transaction cost | All cost paths rerun: 0/0, 20bps/3% borrow, 40bps/3%. Turnover per pre-cost NAV; same-day vendor volume and strictly lagged ADV21 diagnostics in trade-level archive and `liquidity_summary.csv`. No invented market-impact or borrow data. |
| 6a Member 2 methods/results/limitations and conclusions | Generated English Markdown chapter and three-page A4 PDF. Results interpreted together with volatility, drawdown, fees, exposure and subperiod instability. |
| 6b Executable documented code reproducing from collected data | README commands, locked dependencies, original packaged Member 1 data restored in an ignored copy, nine simulations, baseline daily-path comparisons, accounting checks, original tests plus Member 2 regression tests. |
| Member 3 integration | Three net signed-holdings panels, net daily NAV/cost paths, quarantined aligned asset returns, exact 500-session coverage and flags; no claim of completed VaR. |
| Final group submission rules | Group must supply real names/matriculation numbers/contributions, merge to <=10 A4 pages with references, complete Member 3 risk analysis and submit `FT5009_groupXX_group_project.zip`. No fictitious student identifiers or final submission claims. |

Run `python "member 2/run_member2.py"` to regenerate current evidence. Large restored raw data stay in Member 1's existing archives; do not upload `work/` or duplicate expanded vendor CSVs.
