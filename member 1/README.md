# FT5009 — Member 1 (Kelly)

## Use these folders

| Folder | Purpose |
|---|---|
| `01_SGX_Flow_Collection/` | Original SGX weekly flow collection, provenance and source reports. |
| `02_Baseline_Backtesting/` | Current market-data preparation, baseline strategies, outputs and report methods. Start here. |
| `99_Legacy_Backtest_Scaffold/` | Earlier engine and empty input templates, retained for reference. Do not use for current results. |
| `99_Legacy_Validation/` | Earlier validation notes, retained for reference. |

From the repository root:

```bash
python -m pip install -r Kelly/02_Baseline_Backtesting/requirements.txt
python Kelly/02_Baseline_Backtesting/run_offline_pipeline.py
python -m unittest discover -s Kelly/02_Baseline_Backtesting/tests -v
```

The SGX collection and current backtesting package intentionally share small input metadata files (`report_checks.csv`, `security_codes_to_map.csv`). These keep the backtesting package self-contained. The legacy scaffold also repeats some code and documentation; its name now makes its status explicit.

The current baseline is a restricted available-data sample. Read `02_Baseline_Backtesting/docs/member1_data_methods_update.md` for exclusions, retrospective quality-selection bias and remaining asset-return review requirements before final VaR. Arithmetic checks do not certify all vendor corporate actions.

