> LEGACY REFERENCE: superseded by Kelly/02_Baseline_Backtesting/. Do not use these instructions for the current baseline.

# Validation record — 21 October 2026

Executed locally before upload:

- Downloaded 399 eligible weekly reports; zero failed downloads.
- Verified source file SHA256 hashes and reproduced 15,960 extracted rows exactly from the original workbooks.
- Confirmed four recognised Top-10 tables per report, each with 10 rows, signed nonzero S$M flows and no duplicate/conflicting stock direction within an investor's lists.
- Checked ranking order and equality of dates in archive titles versus workbook week labels; no unresolved extraction exceptions in this set.
- Reviewed coverage by ISO natural week. One incorrectly categorised report was added, two Tuesday labels were normalised for coverage checking, and five weeks remain unresolved.
- Recorded three publication-timing anomalies. These are unresolved source metadata issues, not silently corrected execution dates.
- Ran four synthetic baseline tests: publication lag with exact long/short P&L and cost accounting; held-asset missing-return refusal; unavailable borrow exclusion; calendar-day weekend borrowing fees.
- Confirmed empty empirical inputs refuse to run instead of producing made-up results.

Not executed: a real 2019–September 2026 price-based strategy backtest. Daily price, volume and benchmark histories are not present. Synthetic accounting tests do not establish historical trading feasibility or performance.
