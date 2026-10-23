# SGX Weekly Top 10 source collection

This folder contains the original collection and extraction record, distinct from the current baseline in ../02_Baseline_Backtesting.

## Offline reproduction

Open a terminal in this folder and run:

```bash
python restore_sources.py
python parse_history.py
python verify_dataset.py
```

The eight source_archives ZIPs restore 399 original XLSX reports released in 2019 through September 2026, including 51 reports released in 2022 and 50 in 2023. SHA256 and URLs are recorded in download_manifest_combined.json. parse_history.py reproduces 15,960 observations from the four Weekly Top 10 tables and verifies structure, signs, ranks and dates. An unreported security is not a zero flow. Timing anomalies are recorded without inventing release dates. Five unlocated observation weeks are recorded in weeks_to_investigate.csv; the archive search is not proof that a report was never published.

The current strategy uses 396 reports after excluding three timing anomalies. Daily price preparation, fixed pre-2019 data eligibility, baseline execution and remaining limitations are documented in ../02_Baseline_Backtesting. Historical source metadata do not prove original publication timestamps or independently verify all security identities.

collect_history.py can refresh downloads using recorded inventory URLs, but is not required for offline reproduction. coverage.py and build_overview.py are original collection-stage utilities; the latter generates historical collection notes rather than the current backtest methodology.

Source: https://www.sgx.com/stock-exchange/data-reports?reportType=203 . Original collection recorded 21 October 2026. ChatGPT assisted with collection, extraction and documentation.
