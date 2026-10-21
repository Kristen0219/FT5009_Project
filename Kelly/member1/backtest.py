"""Weekly flow strategy research engine. See README for accounting and assumptions."""
from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd

START, END = pd.Timestamp('2019-01-01'), pd.Timestamp('2026-09-30')

def load(root):
    root = Path(root)
    flows = pd.read_csv(root/'flows.csv', dtype={'security_id':str,'report_id':str})
    prices = pd.read_csv(root/'prices.csv', dtype={'security_id':str})
    reports = pd.read_csv(root/'reports.csv', dtype={'report_id':str})
    bench = pd.read_csv(root/'benchmark.csv')
    if any(x.empty for x in [flows,prices,reports,bench]):
        raise ValueError('Input is empty. Collect real data first; demo is not coursework evidence.')
    for frame, cols in [(flows,['publication_date']), (reports,['publication_date','week_end']),
                        (prices,['date']), (bench,['date'])]:
        for c in cols: frame[c] = pd.to_datetime(frame[c], errors='raise')
    if prices.duplicated(['date','security_id']).any() or bench.duplicated('date').any():
        raise ValueError('Duplicate price or benchmark keys')
    if reports.report_id.duplicated().any() or flows.duplicated(['report_id','investor','side','security_id']).any():
        raise ValueError('Duplicate report/signal keys')
    if not set(flows.investor)<= {'retail','institutional'} or not set(flows.side)<= {'buy','sell'}:
        raise ValueError('Invalid investor or side')
    if not set(flows.report_id)<=set(reports.report_id): raise ValueError('Unregistered report')
    meta=reports.set_index('report_id')
    for rid,g in flows.groupby('report_id'):
        if not (g.publication_date==meta.loc[rid,'publication_date']).all(): raise ValueError('Publication dates disagree')
        if meta.loc[rid,'status']!='complete': raise ValueError('Signals from incomplete report')
        if set(g.groupby(['investor','side']).groups)!=set((i,s) for i in ['retail','institutional'] for s in ['buy','sell']):
            raise ValueError('All four investor/side tables are required per complete report')
        for _,table in g.groupby(['investor','side']):
            if sorted(table['rank'].tolist()) != list(range(1,len(table)+1)):
                raise ValueError('Invalid ranks')
        if (g.groupby(['investor','side']).size()>10).any(): raise ValueError('Not Weekly Top 10')
        if g.duplicated(['investor','security_id']).any(): raise ValueError('Conflicting weekly directions')
    if (reports.publication_date<reports.week_end).any(): raise ValueError('Publication before observation period ends')
    if reports.source_url.isna().any(): raise ValueError('Missing report provenance')
    if not prices.currency.eq('SGD').all(): raise ValueError('Normalize prices and TRI to SGD first')
    for c in ['close','total_return_index']:
        if prices[c].isna().any() or not (prices[c]>0).all(): raise ValueError('Invalid price/TRI')
    if prices.volume.isna().any() or (prices.volume<0).any(): raise ValueError('Invalid volume')
    if not prices.short_available.isin([0,1]).all(): raise ValueError('Short availability must be 0/1')
    if not (bench.total_return_index>0).all(): raise ValueError('Invalid benchmark TRI')
    if ((flows.side.eq('buy') & flows.flow_sgd_m.le(0)) | (flows.side.eq('sell') & flows.flow_sgd_m.ge(0))).any():
        raise ValueError('Flow sign disagrees with table')
    if flows.flow_sgd_m.isna().any(): raise ValueError('Unknown flow is not zero')
    # Only the release window specified in the assignment is eligible.
    reports=reports[reports.publication_date.between(START,END)].copy()
    flows=flows[flows.report_id.isin(reports.report_id)].copy()
    if not reports.status.eq('complete').all():
        raise ValueError('Known missing/incomplete reports in sample; resolve or explicitly define a restricted sample before running')
    if set(reports.report_id)!=set(flows.report_id):
        raise ValueError('A complete report has no extracted signals')
    prices=prices.sort_values(['security_id','date'])
    bench=bench.sort_values('date').set_index('date')
    return flows,prices,reports,bench

def simulate(flows, prices, reports, benchmark, investor, tc_bps=20., borrow_rate=.03):
    """Close execution on first benchmark session STRICTLY AFTER publication date.
    49% long / 49% short target; 10% per-name cap; unfilled allocation stays cash.
    Rebalance only on new reports, holding synthetic total-return units between closes.
    Cash includes restricted short proceeds, earns 0%; no interest on margin/collateral.
    """
    calendar=benchmark.index
    dates=calendar[(calendar>=START)&(calendar<=END)]
    byday={d:g.set_index('security_id') for d,g in prices.groupby('date')}
    tri=prices.pivot(index='date',columns='security_id',values='total_return_index').reindex(calendar)
    returns=tri.pct_change(fill_method=None)
    releases={}
    complete=reports[reports.status.eq('complete')].sort_values(['publication_date','report_id'])
    for r in complete.itertuples():
        eligible=dates[dates>r.publication_date]
        if len(eligible):
            d=eligible[0]
            if d in releases: raise ValueError('Multiple releases for same execution close; resolve explicitly')
            releases[d]=r.report_id
    nav=1_000_000.; cash=nav; values={}; previous_date=None
    daily=[]; weights=[]; trades=[]; exclusions=[]
    for d in dates:
        before=nav; old=values.copy()
        start_weights={s:v/before for s,v in old.items()}
        elapsed=(d-previous_date).days if previous_date is not None else 0
        borrow=sum(-v for v in old.values() if v<0)*borrow_rate*elapsed/365
        for s,v in old.items():
            r=returns.loc[d,s] if s in returns else np.nan
            if not np.isfinite(r):
                raise ValueError(f'Missing held-asset return {s} {d.date()}. Resolve suspension/delisting; never forward-fill silently.')
            values[s]=v*(1+r)
        cash-=borrow
        nav=cash+sum(values.values())
        cost=turnover=0.
        if d in releases:
            rid=releases[d]
            g=flows[(flows.report_id==rid)&flows.investor.eq(investor)]
            if g.empty: raise ValueError(f'Missing {investor} table in {rid}')
            today=byday.get(d,pd.DataFrame())
            target={}
            for side,sign in [('buy',1),('sell',-1)]:
                selected=g[g.side.eq(side)].security_id.tolist()
                # Fixed slots: exclusions reduce exposure; never backfill from non-Top-10.
                w=min(.10,.49/len(selected)) if selected else 0
                for s in selected:
                    reason=None
                    if s not in today.index: reason='missing_execution_quote'
                    elif today.loc[s,'volume']<=0: reason='zero_volume'
                    elif sign<0 and today.loc[s,'short_available']!=1: reason='borrow_unavailable'
                    if reason:
                        exclusions.append(dict(date=d,report_id=rid,security_id=s,reason=reason));continue
                    target[s]=sign*w*nav
            for s in sorted(set(values)|set(target)):
                delta=target.get(s,0)-values.get(s,0)
                if abs(delta)<1e-8:continue
                if s not in today.index or today.loc[s,'volume']<=0:
                    raise ValueError(f'Cannot execute exit {s} on {d.date()}; resolve explicitly')
                fee=abs(delta)*tc_bps/10000
                cost+=fee; turnover+=abs(delta)/nav
                trades.append(dict(date=d,report_id=rid,security_id=s,notional_sgd=delta,
                    cost_sgd=fee,shares_equivalent=abs(delta)/today.loc[s,'close'],
                    participation=abs(delta)/(today.loc[s,'close']*today.loc[s,'volume'])))
                cash-=delta+fee
            values={s:v for s,v in target.items() if abs(v)>1e-8}
            nav=cash+sum(values.values())
        if nav<=0: raise ValueError('Portfolio insolvent')
        for s in sorted(set(start_weights)|set(values)):
            weights.append(dict(date=d,security_id=s,start_weight=start_weights.get(s,0),
                end_weight=values.get(s,0)/nav,end_value_sgd=values.get(s,0)))
        daily.append(dict(date=d,nav=nav,daily_return=nav/before-1,cost_sgd=cost,
            borrow_sgd=borrow,turnover=turnover,cash_sgd=cash,
            gross_exposure=sum(abs(v) for v in values.values())/nav,
            net_exposure=sum(values.values())/nav))
        previous_date=d
    return { 'daily':pd.DataFrame(daily), 'holdings':pd.DataFrame(weights),
             'trades':pd.DataFrame(trades), 'exclusions':pd.DataFrame(exclusions)}

def run(input_dir, output_dir):
    flows,prices,reports,bench=load(input_dir)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    for investor in ['retail','institutional']:
        for name,cost,borrow in [('gross',0,0),('net',20,.03),('double_cost',40,.03)]:
            result=simulate(flows,prices,reports,bench,investor,cost,borrow)
            for kind,frame in result.items():frame.to_csv(out/f'{investor}_{name}_{kind}.csv',index=False)
    # Pre-2019 aligned daily returns retained for Member 3; missing histories remain NaN.
    aligned=prices.pivot(index='date',columns='security_id',values='total_return_index').reindex(bench.index)
    aligned.pct_change(fill_method=None).to_csv(out/'asset_returns_aligned.csv',index_label='date')
    b=bench.copy();b['daily_return']=b.total_return_index.pct_change(fill_method=None)
    b.to_csv(out/'benchmark_daily.csv',index_label='date')
    reports.to_csv(out/'report_coverage.csv',index=False)
    (out/'assumptions.json').write_text(json.dumps(dict(initial_nav=1000000,long_target=.49,
        short_target=.49,name_cap=.10,transaction_cost_bps_one_way=20,borrow_rate_annual=.03,
        execution='first trading close strictly after local publication date',cash_rate=0,
        reinvested_total_return=True,terminal_liquidation=False),indent=2))
    print('Completed. Verify report coverage and assumptions before interpreting results.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',default='data/input');p.add_argument('--output',default='output')
    a=p.parse_args();run(a.input,a.output)
