# Member 2 — Strategy Enhancement and Performance Evaluation

Parts 3–4 of the FT5009 group project: an enhanced institutional strategy and a comparison of all three strategies with the benchmark. Data and the backtesting engine come from Member 1.

## Strategy

Institutional buy signals are followed only when the SGD total-return index is above its 126-day simple moving average; sell signals require it to be below. The rule uses observations strictly before publication, with no parameter search. Rejected allocations remain in cash. Position limits, weekly execution and cost assumptions follow the original strategies.

The rule adapts the price-versus-SMA example in Lecture 8, PDF pages 16 and 21. See [course references](LECTURE_ALIGNMENT.md).

## Results

- [Report](results/MEMBER2_REPORT.md) · [Three-page A4 PDF](results/MEMBER2_REPORT_A4.pdf)
- [Cumulative returns and drawdowns](results/figures/net_returns_drawdowns.png) · [Cost comparison](results/figures/cost_stress.png)
- [Performance by period](results/performance.csv) · [Liquidity summary](results/liquidity_summary.csv)
- [Trade records](results/trades_and_liquidity.csv.gz) · [Validation records](results/validation.json)
- [Risk inputs for Member 3](results/risk_handoff/README.md)

The comparison covers gross, net and doubled transaction costs over the full sample and the three required subperiods. Results inherit the data-coverage and execution limitations documented by Member 1.

## Run

Use Python 3.12 and run from the repository root:

```bash
python3 -m venv /tmp/ft5009-member2-venv
source /tmp/ft5009-member2-venv/bin/activate
python -m pip install -r "member 2/requirements-lock.txt"
python "member 2/run_member2.py"
```

After dependency installation, the pipeline runs offline. It prepares a local copy of Member 1 under `work/`, runs the backtests and tests, and regenerates `results/`. Allow a few minutes and at least 1 GB of disk space. Save any manual edits to generated results elsewhere before running.

To rebuild inputs, append `--rebuild-inputs`. To run only the Member 2 tests:

```bash
python -m unittest discover -s "member 2/tests" -v
```

Member 3 will use the supplied holdings and returns for Part 5 and integrate this chapter into the final report. See the [requirements checklist](REQUIREMENTS_CHECKLIST.md) for the file mapping.

AI assistance: OpenAI Codex was used for coding, analysis and drafting.
