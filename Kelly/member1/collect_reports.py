"""Download only URLs actually recorded in a verified SGX report inventory.
Does not guess publication dates or scrape unverified Top-10 tables.
"""
import csv, hashlib, argparse, urllib.request, time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',default='data/input/reports.csv');a=p.parse_args()
    manifest=Path(a.manifest);rows=list(csv.DictReader(manifest.open()))
    if not rows:raise SystemExit('First populate reports.csv from the SGX archive, including actual publication dates and direct report URLs.')
    root=Path('data/raw');root.mkdir(parents=True,exist_ok=True)
    for row in rows:
        target=root/(row['report_id']+'.pdf')
        if not target.exists():
            req=urllib.request.Request(row['source_url'],headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=30) as r:body=r.read()
            if not body.startswith(b'%PDF'):raise ValueError(f"Not a PDF: {row['report_id']}")
            target.write_bytes(body);time.sleep(.5)
        row['local_file']=str(target);row['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        # Save after each successful download so interrupted collection can resume.
        with manifest.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
        print(row['report_id'],row['sha256'])
if __name__=='__main__':main()
