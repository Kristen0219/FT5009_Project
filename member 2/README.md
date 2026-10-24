# FT5009 Member 2

Institutional strategy enhancement and performance evaluation (Parts 3–4). Uses Member 1's current data and backtesting engine. Results and the report are in `results/`; risk inputs for Member 3 are in `results/risk_handoff/`.

From the repository root, run with Python 3.12:

```bash
python -m pip install -r "member 2/requirements-lock.txt"
python "member 2/run_member2.py"
```

The enhancement confirms institutional flow signals using a fixed 126-day simple moving average, based on Lecture 8. All strategies use the same eligibility, execution and cost rules. The evaluation includes the benchmark, required subperiods, gross/net returns, doubled transaction costs, turnover and liquidity.

The pipeline runs offline after installation and prepares a working copy under `work/`, leaving Member 1 unchanged. It regenerates `results/`. Read [the report](results/MEMBER2_REPORT.md) and Member 1's `REQUIREMENTS_AUDIT.md` before integration; the data-coverage and trading limitations apply to all results.
