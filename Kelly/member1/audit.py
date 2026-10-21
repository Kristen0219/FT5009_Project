"""Input readiness checks. These do not establish that the archive is exhaustive."""
from pathlib import Path
import argparse
import pandas as pd
from backtest import load,START,END

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='data/input');a=p.parse_args()
    flows,prices,reports,b=load(a.input)
    problems=[]
    if not reports.status.eq('complete').all(): problems.append('Incomplete/missing reports: resolve before full-period submission')
    for rid,g in flows.groupby('report_id'):
        counts=g.groupby(['investor','side']).size()
        if len(counts)!=4:problems.append(f'{rid}: four Top-10 tables not present')
        if len(g)!=40:problems.append(f'{rid}: {len(g)} rows, verify against original tables (do not fabricate to reach 40)')
        for key,table in g.groupby(['investor','side']):
            if sorted(table['rank'].tolist())!=list(range(1,len(table)+1)):problems.append(f'{rid} {key}: invalid ranks')
    ds=reports.publication_date.sort_values().drop_duplicates()
    if ds.empty or ds.min()>START+pd.Timedelta(days=14) or ds.max()<END-pd.Timedelta(days=14):problems.append('Publication coverage does not span requested interval')
    if ds.diff().gt(pd.Timedelta(days=14)).any():problems.append('Report gap >14 days: inspect archive and document actual availability')
    pre=b.index[b.index<START]
    if len(pre)<501:problems.append('Benchmark has fewer than 501 pre-2019 closes; insufficient for 500 initial returns')
    if b.index.max()<END:problems.append('Benchmark ends before 2026-09-30')
    for s,g in prices.groupby('security_id'):
        aligned=g.set_index('date').total_return_index.reindex(b.index)
        n=aligned.pct_change(fill_method=None).loc[pre].notna().sum()
        if n<500:problems.append(f'{s}: only {n} valid pre-2019 aligned returns; Member 3 must apply documented insufficient-history rule')
    out=Path('audit_findings.txt');out.write_text('\n'.join(problems) if problems else 'Automated checks passed; manual source/coverage review still required.')
    print(out.read_text())
    if problems:raise SystemExit(1)
if __name__=='__main__':main()
