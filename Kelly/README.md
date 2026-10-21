# FT5009 Project — Member 1

SGX institutional and retail flow strategies: source collection, data checks and baseline backtesting code.

**Current status:** 399 real SGX weekly reports downloaded; 15,960 Top-10 signals extracted, covering 236 distinct SGX stock codes. Source checksums and exact re-extraction checks pass. Daily prices, volume, benchmark data and historical security mapping are still pending, so no empirical backtest performance is claimed.

## What is included

| Path | Contents |
|---|---|
| `data/sgx/flows_extracted.csv` | Four Weekly Top 10 tables per report, with direction, rank, signed S$M flow and cell-level provenance |
| `data/sgx/source_archives/` | All 399 original Excel reports, compressed by displayed publication year |
| `data/sgx/security_codes_to_map.csv` | 236 historical codes/names to resolve before requesting daily market data |
| `data/sgx/report_checks.csv` | Extraction, ordering and timing diagnostics |
| `data/sgx/timing_anomalies.csv` | 3 displayed publication dates inconsistent with completed observation weeks |
| `data/sgx/weeks_to_investigate.csv` | 5 natural weeks for which a matching report was not found |
| `data/sgx/README.md` | Detailed sources, coverage and limitations |
| `member1/backtest.py` | Retail and institutional baseline accounting; gross, net and doubled transaction-cost scenarios |
| `member1/tests/` | Synthetic accounting tests, not empirical performance evidence |
| `member1/data/input/` | Empty schemas for verified backtest inputs |
| `member1/docs/` | Methodology draft and handoff checklist |
| `docs/VALIDATION.md` | Checks actually executed and remaining work |

## Reproduce the flow dataset checks (offline)

Only Python's standard library is needed for these steps:

```bash
python data/sgx/restore_sources.py
python data/sgx/parse_history.py
python data/sgx/coverage.py
python data/sgx/build_overview.py
python data/sgx/verify_dataset.py
```

The raw reports are kept in ZIP archives for compact storage. `restore_sources.py` restores the exact original bytes into the ignored `data/sgx/raw/` directory. It does not download anything.

To repeat downloads from the recorded official URLs:

```bash
python data/sgx/collect_history.py
```

The archive snapshots were obtained from the visible SGX website on 21 October 2026. The downloader reuses that recorded inventory; it does not refresh the website inventory automatically. One report was recovered from the Institutional Newsletter category. Two Tuesday week labels were aligned to their corresponding ISO weeks for coverage checking.

## Baseline accounting tests

```bash
python -m pip install -r member1/requirements.txt
python -m unittest discover -s member1/tests -v
```

After collecting and validating daily market data, resolving identifiers and publication timing, and populating the input schemas:

```bash
cd member1
python audit.py --input data/input
python backtest.py --input data/input --output output
```

The current empty price/benchmark inputs intentionally prevent a historical run. Do not copy extracted flow rows directly into a final backtest while ignoring the documented issues.

## Fixed research assumptions

Each baseline starts with S$1,000,000; targets are 49% long and 49% short, with a 10% per-name target cap. Execution is the first trading close strictly after the verified local publication date. One-way transaction costs are assumed at 20 bps (40 bps in the doubled-cost scenario); annual short borrowing is assumed at 3%. Cash and restricted short collateral earn zero interest. These are modelling choices, not assignment-prescribed parameters or verified historical broker terms. See the Member 1 README for full accounting and limitations.

## Remaining work

1. Investigate the 3 timing anomalies and 5 missing-report weeks; document the treatment without inventing dates or zero flows.
2. Resolve the 236 codes to historical securities, listing currencies and corporate actions, including delisted names.
3. Acquire daily prices, share volume, SGD total returns and a suitable benchmark, including sufficient earlier prices for 500 aligned daily returns before initial VaR forecasts.
4. Run verified historical baselines and provide daily returns, holdings and trades to Members 2 and 3.
5. Replace draft report coverage/assumptions with verified final choices and results. The group report is not complete.

## Source and AI assistance

Source: [SGX Data Reports](https://www.sgx.com/stock-exchange/data-reports?reportType=203). Individual official URLs, displayed publication dates and SHA256 hashes are retained with the dataset. Current website dates are not independent proof of historical information availability or absence of revisions.

ChatGPT assisted with source collection, extraction, baseline implementation and documentation. Source-data and methodology review remains part of the group's work. No strategy returns were fabricated.
