# FT5009 Member 1

Current baseline: `02_Baseline_Backtesting/`. Original SGX source collection: `01_SGX_Flow_Collection/`. Legacy scaffolds are omitted from this audited package; use the current baseline only.

From the repository root, run:

```bash
python -m pip install -r "member 1/02_Baseline_Backtesting/requirements.txt"
python "member 1/run_member1.py"
```

Or open a terminal inside `02_Baseline_Backtesting` and run `python run_offline_pipeline.py`.

This audited version changes eligibility to a fixed starting sample based only on pre-2019 history. It supersedes the earlier full-sample Y92/YF8 exclusion approach; performance numbers consequently change. All three team strategies must use the same updated inputs and treatment. Read `REQUIREMENTS_AUDIT.md` and the revised report draft before integration. Missing vendor histories, fixed-universe bias, source timestamp uncertainty and residual return flags remain disclosed limitations.
