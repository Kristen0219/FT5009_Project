# Member 1 requirements audit

Audited 23 October 2026 against group_project(1).pdf and GitHub main tree fef899d29ca97b80592be93691772e9fb3e23ab6. Scope: Parts 1 and 2, the Member 1 contribution to reproducible code, and handoff readiness. This is an evidence-based implementation check, not a guarantee of marks or a certificate that every vendor observation is economically correct.

## Actual findings and corrections

1. The uploaded SGX archives held 298 reports, despite a manifest for 399. The 51 reports released in 2022 and 50 released in 2023 were absent. Both yearly ZIPs are restored in this update; all 399 original XLSX SHA256 values and 15,960 extracted rows are now verified.
2. parse_history.py was absent, so verify_dataset.py could not run from the upload. The parser and extracted source table are restored.
3. README commands used Kelly/ after the folder had been renamed member 1/. Commands now quote the actual path, and run_member1.py locates its folders relative to itself.
4. Entire-sample Y92/YF8 exclusions used later-period information. The default baseline now fixes eligibility using only observations before 1 January 2019. Both strategies require at least 500 valid aligned pre-2019 returns and no absolute pre-2019 return above 50%. The threshold is a conservative source-quality screen, not proof that an excluded return is erroneous. It can exclude genuine volatile securities. Rules were not selected by optimising full-period strategy returns.
5. The new starting sample contains 125 canonical histories covering 127 source codes. Thirty candidate histories fail the length rule, 13 trigger the pre-period flag; 66 original codes separately lack candidate histories. New listings and histories outside the fixed starting sample are not admitted later. All excluded signal allocations stay cash; all signals and their original ten-name slots remain in the input.
6. The new six-path results supersede the previous results. Previous summary and scenario metadata are retained under 02_Baseline_Backtesting/docs/previous_* for comparison, not final reporting. All team strategies must use the same updated data eligibility and execution rules.
7. Twenty-nine post-2018 extreme observations remain unverified. Original values remain in asset_returns_aligned.csv, while asset_returns_for_var.csv quarantines these observations as missing. The latter produces 82 retail and 46 institutional forecast-date coverage gaps when exactly 500 aligned preceding returns for current holdings are required. No day is dropped to manufacture 500 observations, and missing returns are not filled with zero. Member 3 may restore an observation only with evidence or disclose the full forecast gap. A large genuine return should not be clipped.

## Requirement by requirement

| PDF requirement | Evidence and implemented treatment | Status |
|---|---|---|
| 1a Available reports released 2019-01-01 to 2026-09-30; consistent Weekly Top 10 | 399 source reports; four tables and ten ranks each; 15,960 exact source rows. Three timing reports excluded from trading gives 396 reports and 15,840 signals. | Implemented and re-extracted |
| 1a Daily prices, volume, benchmark and earlier risk history | Original vendor sources plus 2016-2026 daily prices and volume; official ES3 NAV/distribution benchmark; 125 eligible canonical price histories all have at least 500 pre-2019 numerical returns. | Implemented with coverage restrictions |
| 1b Sources and identifiers | URLs, SHA256 receipts, candidate symbol/name matches, official S51/5E2 and J91U/9A4U relations; source name/code conflicts preserved. | Documented; ordinary historical identities not independently certified |
| 1b Corporate actions and currencies | Vendor adjusted-price total-return exposure, recorded distributions/splits, lagged USD/SGD conversion, explicit unresolved-event flags. Official benchmark reinvests distributions at ex-date NAV. | Implemented with disclosed vendor limitations |
| 1b Missing data, IPOs and delistings | Fixed pre-2019 starting universe; no later admissions; no-history signals stay cash. Missing held return stops run; zero-volume exit freezes existing holding; no invented delisting settlement. | Implemented consistently |
| 1b Exclusions and bias; unreported versus zero | All signals retained; unavailable allocation not redistributed; fixed-universe, availability/survivorship and conservative pre-period-screen bias disclosed. | Included in revised report |
| 1b Avoid future information | Screen consumes pre-2019 data only. Test proves future-price mutations do not change membership. Current archive metadata and current vendor data are not independently observed historical vintages. | Timing rules implemented; source-vintage uncertainty remains |
| 2a Both named baseline strategies | Retail and institutional buy lists go long, sell lists go short; fixed slots, equal weights, holding/exit/rebalance rules. | Implemented and tested |
| 2b Comparable long/short portfolios at S$1m each | 49% target per side, 10% name cap, frozen holdings reserve budget; same rules and inputs. Cash/collateral assumptions and lack of margin/recall modelling stated. | Implemented and disclosed |
| 2b Transaction costs and borrowing | Gross 0/0, net 20 bps plus 3% borrow, doubled transaction cost 40 bps plus same borrow; calendar-day accrual. All borrowable is an assumption, not claimed evidence. | Independently reconciled |
| 2b Weekly after publication | First benchmark-session close strictly after display date; existing holdings earn execution-day returns before the trade. Every trade date independently checked. | Passed execution-date check |
| Reproducible Python contribution | Offline source restoration/extraction, market-input rebuild, six paths, ten tests, accounting and risk-handoff audits through run_member1.py. | Executed from a fresh reconstructed package |
| Report sources and AI disclosure | Revised A4 Word draft covers Parts 1-2, includes human-readable linked references and AI disclosure. | Included; merge into final group PDF |

## Independent verification

- 399 SGX workbook checksums; exact re-extraction of 15,960 source rows, no duplicate signal keys, all four table directions present, all rank/sign checks pass.
- 172 downloaded market JSON checksums; official benchmark NAV formula and date calendar; 2026 benchmark check within issuer rounding precision.
- 336,916 normalized SGD price rows for 125 canonical histories; no duplicate date/security keys, positive prices and non-negative volume; lagged FX labels are strictly before stock dates and no older than five calendar days.
- Six daily paths with 1,945 sessions each. Cash/positions/NAV, daily returns, transaction fees and borrow fees reconcile. Position roll-forward maximum gap is approximately 2.91e-11 SGD. All trades execute after publication on the first eligible calendar session.
- Ten tests cover accounting, missing held returns, borrow restrictions, weekend fees, non-executable positions, frozen allocation budgets, and initial eligibility that is independent of future observations.
- The two baseline holdings panels have no active start-of-day exposure on the remaining flagged daily returns. That does not validate the flags as risk-history observations; the separate risk input and coverage log address this distinction.

## Interpretation and remaining team work

Missing histories do not by themselves fail the assignment: the PDF explicitly asks for consistent unavailable-history rules and disclosure of exclusions and bias. Nevertheless, no audit of this package can prove that all archived release dates were original, that every current symbol matches its historical issuer, or that every vendor corporate action is correct. Zero-volume holdings use available vendor marks, which may be stale; a frozen quote is not an executable price or independent proof of zero economic risk. Prices/volume are vendor-basis proxies; assume-all-borrowable, zero cash interest, fractional units and absent market impact/margin calls limit trading realism. Results must be described as those of a restricted fixed-starting-sample backtest.

The 50% threshold is a review/eligibility policy, not an economically proven bound. Quarantining post-period extremes also sacrifices valid-tail observations until they are verified; do not compute VaR from fewer than the required 500 aligned observations. Document forecast coverage gaps rather than present a truncated tail as complete risk coverage.

Parts 3-4 still require the institutional enhancement, all performance measures/plots, period comparisons, turnover and liquidity assessment. Part 5 still requires actual rolling volatility and signed-holdings 99% historical-simulation VaR, including the enhanced strategy and coverage disclosure. Part 6 still requires the integrated <=10-page A4 PDF, all names/matriculation numbers/contributions, overall conclusions, and the final group ZIP. This update alone is not the complete group submission.

## Primary evidence for a remaining corporate-action concern

The vendor shows a 100-fold 1MZ adjusted-price jump on 2024-02-01. Nam Cheong's official 2 February 2024 SGX announcement states that its shares had been voluntarily suspended since 28 April 2020. This is a reason to quarantine and review the recorded return, not justification for inserting an invented 100:1 correction on the vendor's jump date. The source PDF and checksum are retained in docs/source_quality/; the source URL is https://links.sgx.com/1.0.0/corporate-announcements/26A1TUAGQ49R6T0E/785808_NCL_ApprovalofTRPCircularALA_Final.pdf . Other flagged returns may be genuine.

## Apply this update

This complete Member 1 package includes the source collection, all three market archives, current code, revised report and audit evidence. Extract the outer ZIP and replace the existing member 1/ folder with its member 1/ folder. Keep inner data ZIPs compressed. The two 99_Legacy folders are omitted because they are not needed to reproduce current results. Other group members’ work is outside this package and must be retained separately. The remote repository has not been modified by this audit.

From the repository root:

```bash
python -m pip install -r "member 1/02_Baseline_Backtesting/requirements.txt"
python "member 1/run_member1.py"
```

Use FT5009_Member1_Report_Audited.docx in place of the earlier draft. Read the revised baseline_handoff_summary.csv; do not mix old results or an enhanced strategy run on old inputs with this version.
