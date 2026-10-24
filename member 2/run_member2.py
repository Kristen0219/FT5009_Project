"""Offline Parts 3–4 reproduction; source files in member 1 are never rewritten."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent/'work/matplotlib'))
import numpy as np
import pandas as pd
from enhancement import filter_institutional, LOOKBACK
from evaluation import evaluate, liquidity, liquidity_summary

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def source_fingerprint():
    """Hash the actual source/data bytes, including local edits, without Git metadata."""
    paths = sorted(p for p in (REPO/'member 1').rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts and p.suffix != '.pyc')
    return {str(p.relative_to(REPO)): sha256(p) for p in paths}


def engine_module():
    path = REPO/'member 1/02_Baseline_Backtesting/backtest.py'
    spec = importlib.util.spec_from_file_location('member1_engine', path)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    return engine


def prepare(rebuild=False):
    """Reuse only a fingerprinted, successfully reconstructed local cache."""
    work = ROOT/'work'
    work.mkdir(exist_ok=True)
    baseline = work/'member 1/02_Baseline_Backtesting'
    receipt = work/'prepared.json'
    fingerprint = source_fingerprint()
    reusable = False
    if receipt.exists() and not rebuild:
        saved = json.loads(receipt.read_text())
        reusable = saved.get('source_sha256') == fingerprint
        reusable = reusable and all((baseline/p).exists() and sha256(baseline/p) == digest
                                    for p, digest in saved.get('prepared_sha256', {}).items())
        reusable = reusable and bool(saved.get('prepared_sha256'))
    if not reusable:
        # Never delete unknown/user files to refresh a cache. Keep old runs separately.
        if (work/'member 1').exists():
            import datetime
            backup = work/('previous-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
            (work/'member 1').rename(backup)
        shutil.copytree(REPO/'member 1', work/'member 1', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        with (work/'member1_reproduction.log').open('w') as log:
            subprocess.run([sys.executable, str(work/'member 1/run_member1.py')],
                           cwd=REPO, stdout=log, stderr=subprocess.STDOUT, check=True)
        required = list((baseline/'research_inputs').glob('*.csv'))
        required += list((baseline/'research_backtest_output').glob('*'))
        required += [baseline/'large_return_review.csv', baseline/'initial_eligibility_audit.csv',
                     baseline/'independent_requirement_audit.json', baseline/'baseline_handoff_summary.csv']
        receipt.write_text(json.dumps(dict(source_sha256=fingerprint,
            prepared_sha256={str(p.relative_to(baseline)): sha256(p) for p in required if p.is_file()}), indent=2))
    return baseline, fingerprint


def verify_result(result, tc, borrow_rate, benchmark):
    """Independent cash ledger, cost and NAV checks; reject silent nonfinite paths."""
    d, h, t = result['daily'], result['holdings'], result['trades']
    expected_dates = benchmark.index[(benchmark.index >= '2019-01-01') & (benchmark.index <= '2026-09-30')]
    assert list(d.date) == list(expected_dates)
    assert np.isfinite(d.select_dtypes('number')).all().all()
    assert np.allclose(d.daily_return, d.nav/pd.Series(np.r_[1e6, d.nav.to_numpy()[:-1]], index=d.index)-1, atol=1e-12)
    assert np.allclose(t.cost_sgd, t.notional_sgd.abs()*tc/10000, atol=1e-9)
    costs = t.groupby('date').cost_sgd.sum().reindex(d.date, fill_value=0).to_numpy()
    assert np.allclose(d.cost_sgd, costs, atol=1e-7)
    delta = t.groupby('date').notional_sgd.sum().reindex(d.date, fill_value=0).to_numpy()
    cash = 1e6-np.cumsum(delta+costs+d.borrow_sgd.to_numpy())
    assert np.allclose(d.cash_sgd, cash, atol=1e-6, rtol=1e-10)
    positions = h.groupby('date').end_value_sgd.sum().reindex(d.date, fill_value=0).to_numpy()
    assert np.allclose(d.nav, cash+positions, atol=1e-6, rtol=1e-10)
    short_value = h.assign(short_value=(-h.end_value_sgd).clip(lower=0)).groupby('date').short_value.sum().reindex(d.date, fill_value=0)
    elapsed = d.date.diff().dt.days.fillna(0).to_numpy()
    assert np.allclose(d.borrow_sgd, short_value.shift(1, fill_value=0).to_numpy()*borrow_rate*elapsed/365, atol=1e-7)


def risk_handoff(results, prepared, benchmark, output):
    """Current signed holdings and exact 500-session coverage; VaR belongs to Member 3."""
    risk = output/'risk_handoff'
    risk.mkdir(exist_ok=True)
    safe = pd.read_csv(prepared/'research_backtest_output/asset_returns_for_var.csv', index_col='date', parse_dates=True)
    safe.to_csv(risk/'asset_returns_for_var.csv.gz', index_label='date', compression={'method':'gzip', 'mtime':0})
    complete = safe.notna().rolling(500, min_periods=500).sum().eq(500)
    flags = pd.read_csv(prepared/'large_return_review.csv', parse_dates=['date'])
    coverage, active = [], []
    for strategy, result in results.items():
        daily, holdings = result['daily'], result['holdings']
        holdings.to_csv(risk/f'{strategy}_net_holdings.csv.gz', index=False, compression={'method':'gzip', 'mtime':0})
        start = holdings[holdings.start_weight.abs()>1e-9]
        joined = start.merge(flags, on=['date', 'security_id'])
        if len(joined):
            joined['strategy'] = strategy
            active.append(joined)
        groups = {date:g.security_id.unique() for date,g in holdings[holdings.end_value_sgd.abs()>1e-8].groupby('date')}
        for i, date in enumerate(daily.date):
            pos = benchmark.index.get_loc(date)
            origin = benchmark.index[pos-1]
            names = groups.get(origin, []) if i else []
            valid = not len(names) or bool(complete.loc[origin, names].all())
            coverage.append(dict(strategy=strategy, forecast_origin_date=origin, forecast_date=date,
                active_securities=len(names), complete_500_return_window=valid,
                reason='cash_only' if not len(names) else 'complete' if valid else 'missing_or_quarantined_return'))
    coverage = pd.DataFrame(coverage)
    coverage.to_csv(risk/'forecast_coverage.csv', index=False)
    active_frame = pd.concat(active, ignore_index=True) if active else pd.DataFrame(columns=['strategy','date','security_id','start_weight','daily_return'])
    active_frame.to_csv(risk/'active_flagged_returns.csv', index=False)
    return coverage, active_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild-inputs', action='store_true', help='Reconstruct fresh Member 1 copy and verify its original tests/audit')
    args = parser.parse_args()
    prepared, fingerprint = prepare(args.rebuild_inputs)
    engine = engine_module()
    flows, prices, reports, benchmark = engine.load(prepared/'research_inputs')
    filtered, decisions = filter_institutional(flows, prices, benchmark.index)
    assert len(filtered) == len(flows) == 15840
    assert decisions.information_date.lt(decisions.publication_date).all()
    out = ROOT/'results'
    out.mkdir(exist_ok=True)
    decisions.to_csv(out/'enhancement_decisions.csv', index=False)
    paths, all_trades, net_results, checks = {}, [], {}, []
    specs = [('retail', 'retail', flows), ('institutional', 'institutional', flows),
             ('enhanced', 'institutional', filtered)]
    references = pd.read_csv(prepared/'baseline_handoff_summary.csv')
    for strategy, investor, signal in specs:
        for scenario, tc, borrow in [('gross',0.,0.), ('net',20.,.03), ('double_cost',40.,.03)]:
            print(f'Running {strategy} / {scenario}', flush=True)
            result = engine.simulate(signal, prices, reports, benchmark, investor, tc, borrow)
            verify_result(result, tc, borrow, benchmark)
            d, h, t = result['daily'], result['holdings'], result['trades']
            trade_dates = reports.set_index('report_id').publication_date.map(
                lambda release: benchmark.index[benchmark.index > release][0])
            assert t.date.eq(t.report_id.map(trade_dates)).all()
            if strategy != 'enhanced':
                ref = references[(references.strategy.eq(strategy)) & references.scenario.eq(scenario)].iloc[0]
                assert np.isclose(d.nav.iloc[-1], ref.final_nav_sgd, rtol=1e-12, atol=1e-6)
                # Compare whole daily paths, not just final wealth.
                original = pd.read_csv(prepared/f'research_backtest_output/{strategy}_{scenario}_daily.csv')
                assert np.allclose(d.nav, original.nav, rtol=1e-12, atol=1e-6)
            d.to_csv(out/f'{strategy}_{scenario}_daily.csv', index=False)
            result['exclusions'].to_csv(out/f'{strategy}_{scenario}_exclusions.csv', index=False)
            tl = liquidity(t, prices, benchmark.index)
            tl['strategy'], tl['scenario'] = strategy, scenario
            all_trades.append(tl)
            paths[strategy,scenario] = d
            checks.append(dict(strategy=strategy, scenario=scenario, sessions=len(d),
                               accounting_passed=True, execution_timing_passed=True,
                               baseline_path_match=True if strategy!='enhanced' else None))
            if scenario == 'net':
                net_results[strategy] = result
    trades = pd.concat(all_trades, ignore_index=True)
    trades.to_csv(out/'trades_and_liquidity.csv.gz', index=False, compression={'method':'gzip','mtime':0})
    trades[trades.scenario.eq('net')].sort_values('participation', ascending=False).groupby('strategy', sort=False).head(20).to_csv(out/'liquidity_extreme_trades.csv', index=False)
    bench = benchmark.copy()
    bench['daily_return'] = bench.total_return_index.pct_change(fill_method=None)
    bench = bench.loc['2019-01-01':'2026-09-30'].reset_index()
    assert np.isfinite(bench.daily_return).all()
    bench.to_csv(out/'benchmark_daily.csv', index=False)
    summary = evaluate(paths, bench)
    liq = liquidity_summary(trades)
    summary.to_csv(out/'performance.csv', index=False)
    liq.to_csv(out/'liquidity_summary.csv', index=False)
    coverage, active = risk_handoff(net_results, prepared, benchmark, out)
    audit = dict(paths=checks, source_sha256=fingerprint, lookback_sessions=LOOKBACK,
        enhancement='publication-prior SGD total-return index relative to 126-close SMA',
        lecture_reference='FT5009_L08.pdf physical PDF pages 16 and 21',
        decision_count=len(decisions), accepted_count=int(decisions.accepted.sum()),
        active_flagged_return_rows=len(active),
        var_history_gaps=coverage.groupby('strategy').complete_500_return_window.apply(lambda s:int((~s).sum())).to_dict(),
        versions=dict(python=sys.version.split()[0], pandas=pd.__version__, numpy=np.__version__,
                      matplotlib=__import__('matplotlib').__version__),
        conventions=dict(annual_sessions=252, risk_free_rate=0, sortino_target_daily=0,
            volatility_ddof=1, downside_denominator='all_sessions',
            period_returns='compound actual sliced daily returns; do not restart portfolios',
            gross='zero transaction AND borrow costs', net='20bps transaction + 3% calendar-day borrow',
            double_cost='40bps transaction + 3% calendar-day borrow'))
    (out/'validation.json').write_text(json.dumps(audit, indent=2))
    from reporting import generate
    generate(out, summary, liq, paths, bench, decisions, audit)
    subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'], cwd=REPO, check=True)
    assert fingerprint == source_fingerprint(), 'Member 1 files changed during reproduction'
    artifact_hashes = {str(p.relative_to(out)):sha256(p) for p in out.rglob('*') if p.is_file() and p.name != 'artifact_sha256.json'}
    (out/'artifact_sha256.json').write_text(json.dumps(artifact_hashes, indent=2))
    print(summary[summary.period.eq('full')].to_string(index=False))
    print('Completed Parts 3–4. Review results/MEMBER2_REPORT.md and risk_handoff/README.md.')


if __name__ == '__main__':
    main()
