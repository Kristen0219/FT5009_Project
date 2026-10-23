"""Audit archive inventory against Monday-labelled observation weeks; no gap filling."""
import json,csv
from pathlib import Path
from collections import Counter
from datetime import date,timedelta
from collect_history import inventory
from parse_history import weekdate,write_csv
ROOT=Path(__file__).resolve().parent

def main():
 rows=inventory();weeks={};unknown=[]
 for r in rows:
  w=weekdate(r['title'])
  if w:weeks.setdefault(w-timedelta(days=w.weekday()),[]).append(r)
  else:unknown.append(r)
 start=date(2018,12,31);end=date(2026,9,21);missing=[];d=start
 while d<=end:
  if d not in weeks:missing.append(dict(expected_week_start=d.isoformat(),status='not_found_in_selected_archive_titles',note='Check original archive and neighbouring files; not proof that no report was published.'))
  d+=timedelta(days=7)
 write_csv(ROOT/'weeks_to_investigate.csv',missing,['expected_week_start','status','note'])
 write_csv(ROOT/'archive_titles_unparsed.csv',unknown,['publication_date','title','url'])
 year=Counter(r['publication_date'][:4] for r in rows)
 print('Selected entries by displayed publication year:',dict(sorted(year.items())))
 print('Unparsed title dates:',len(unknown),'missing labelled Mondays:',len(missing))
 print(missing)
if __name__=='__main__':main()
