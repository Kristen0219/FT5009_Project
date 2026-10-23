# Current Member 1 baseline with fixed pre-2019 eligibility

Read ../REQUIREMENTS_AUDIT.md before integration. This version supersedes the full-period Y92/YF8 exclusion scenario. It uses no post-2018 returns to select the starting price-history sample.

## Run offline

From this folder:

```bash
python -m pip install -r requirements.txt
python run_offline_pipeline.py
python -m unittest discover -s tests -v
python audit_requirements.py
```

For full source extraction and all checks from the repository root, run `python "member 1/run_member1.py"`. The parent launcher uses relative paths; it also works if the parent folder is renamed. Its command-line path must be quoted when it contains spaces.

## Data rules and sample

399 original weekly SGX reports produce 15,960 rows. Excluding three timing-inconsistent reports leaves 396 reports and 15,840 signals. Five unlocated observation weeks do not create zero flows or trades.

There are 236 source codes and 170 codes with candidate history, corresponding to 168 canonical histories. Among those histories, 30 have fewer than 500 valid pre-2019 returns and 13 have an absolute pre-2019 return above 50%. Both strategies use the same remaining 125 canonical histories (127 source codes), fixed for the whole trading period. No later IPO or other ineligible history is admitted. This conservative screen can exclude genuine volatile securities; it is not proof of a source error. Missing slots remain cash and are never redistributed.

All strategies start with SGD 1m. Each side targets 49% of pre-cost NAV, with a 10% name cap. Reports trade at the first session close after publication; holdings earn that day's returns before trades. Frozen zero-volume holdings reserve their side's budget. Missing held-asset returns stop the run. Gross, net (20 bps plus 3% annual borrow) and doubled-transaction-cost (40 bps plus 3% borrow) paths are supplied. All borrowable is an explicit assumption; cash interest is zero. No forced final liquidation.

## Results and risk handoff

- baseline_handoff_summary.csv is the revised baseline result, not the earlier one. Previous summary/scenario files remain in docs/previous_* for reference only.
- research_backtest_output/ contains daily NAV, signed holdings, trades, exclusions and asset returns after restoration/run.
- asset_returns_aligned.csv preserves vendor-based returns. For VaR, use the separate asset_returns_for_var.csv and risk_handoff_coverage.csv: 29 unverified extreme observations are marked missing, not clipped or filled zero. This creates 82 retail and 46 institutional forecast gaps under the strict 500-return rule. Do not drop historical dates to obtain 500 surviving values. Verified genuine observations can later be reinstated with documented evidence.
- The official ES3 NAV/distribution total-return proxy is not the official STI total-return index or an executable ETF price. Pre-2019 data are retained for risk estimation.
- Remaining limitations include historical identity candidates, current archive/vendor data vintages, corporate actions, lagged FX approximations, unverified split/volume basis, fixed-universe and survivorship bias, and trading assumptions. No claim of unbiased whole-market performance or complete source certification is made.

The three archives are checksum-verified and restored automatically. Do not upload restored large CSVs (especially prices_vendor.csv); keep them in the inner archives. Sources, download checksums, fixed eligibility decisions and risk quarantine are machine-readable. Detailed methods and report text are in ../FT5009_Member1_Report_Audited.docx and docs/member1_data_methods_update.md.
