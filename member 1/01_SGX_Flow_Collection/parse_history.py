"""Strict extraction from observed Weekly Top 10 worksheets; exceptions retained."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as E
from datetime import datetime,timedelta
from decimal import Decimal
from collections import Counter,defaultdict
import re,csv,json
ROOT=Path(__file__).resolve().parent
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def workbook_cells(path):
 with ZipFile(path) as z:
  ss=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
  rels={x.attrib['Id']:x.attrib['Target'] for x in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  for sheet in E.fromstring(z.read('xl/workbook.xml')).find('m:sheets',NS):
   name=sheet.attrib['name']
   if 'weekly' not in name.lower() or '10' not in name:continue
   rel=rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
   target=rel.lstrip('/') if rel.startswith('/') else 'xl/'+rel
   cells={}
   for c in E.fromstring(z.read(target)).findall('.//m:sheetData/m:row/m:c',NS):
    v=c.find('m:v',NS)
    if v is not None:cells[c.attrib['r']]=ss[int(v.text)] if c.attrib.get('t')=='s' else v.text
    elif c.attrib.get('t')=='inlineStr':cells[c.attrib['r']]=''.join(c.find('m:is',NS).itertext())
   return name,cells
 raise ValueError('No Weekly Top 10 sheet; manual review required')

def colnum(a):
 n=0
 for c in a:n=n*26+ord(c)-64
 return n

def colname(n):
 s=''
 while n:n,r=divmod(n-1,26);s=chr(65+r)+s
 return s

def weekdate(text):
 # Parse only an explicit date after "Week of"; no guessing from download folder.
 m=re.search(r'week\s+of\s+(\d{1,2})\s+([A-Za-z]+)\s*(20\d{2})',text,re.I)
 if not m:return None
 for fmt in ['%d %B %Y','%d %b %Y']:
  try:return datetime.strptime(' '.join(m.groups()),fmt).date()
  except ValueError:pass
 return None

def extract(meta):
 sheet,cells=workbook_cells(ROOT/meta['local_file']);headers=[]
 for addr,value in cells.items():
  t=re.sub(r'\s+',' ',str(value)).lower()
  if re.search(r'top\s*10',t) and 'net' in t and ('buy' in t or 'sell' in t):
   investor='institutional' if 'institut' in t else 'retail' if 'retail' in t else None
   if investor:headers.append((addr,investor,'buy' if 'buy' in t else 'sell',value))
 if len(headers)!=4:raise ValueError(f'Expected 4 headers; found {len(headers)}')
 weeks={weekdate(str(v)) for v in list(cells.values())[:35]};weeks.discard(None)
 if len(weeks)!=1:raise ValueError(f'Ambiguous week labels: {weeks}')
 week=next(iter(weeks));pub=datetime.fromisoformat(meta['publication_date']).date()
 # Friday is derived; actual holiday-adjusted endpoint needs calendar verification.
 end=week+timedelta(days=4-week.weekday())
 timing='review_required' if pub<=end else 'page_date_after_week_end_unverified'
 rows=[]
 for addr,investor,side,title in headers:
  if 's$m' not in title.lower().replace(' ',''):raise ValueError('Unverified flow currency/unit')
  m=re.fullmatch(r'([A-Z]+)(\d+)',addr);c=colnum(m[1]);r=int(m[2])
  if 'code' not in str(cells.get(f'{colname(c+1)}{r}','')).lower():raise ValueError('Unexpected stock-code column')
  for rank in range(1,11):
   rr=r+rank;name=cells.get(f'{colname(c)}{rr}');code=cells.get(f'{colname(c+1)}{rr}');v=cells.get(f'{colname(c+2)}{rr}')
   if name is None or code is None or v is None:raise ValueError(f'Missing rank {rank} at {addr}')
   value=Decimal(v)
   if not value.is_finite() or (value<=0 if side=='buy' else value>=0):raise ValueError('Non-finite/wrong sign flow')
   code=str(code).strip()
   # Numeric codes are identities, never treated as magnitudes.
   rows.append(dict(report_id=meta['report_id'],publication_date=meta['publication_date'],
    week_start=week.isoformat(),iso_week_start=(week-timedelta(days=week.weekday())).isoformat(),week_end_derived=end.isoformat(),timing_status=timing,
    investor=investor,side=side,security_id='SGX_'+code,sgx_code=code,security_name=str(name).strip(),
    rank=rank,flow_sgd_m=str(value),source_page=sheet,source_cells=f'{colname(c)}{rr}:{colname(c+2)}{rr}',source_url=meta['url']))
 if len({(x['investor'],x['side']) for x in rows})!=4:raise ValueError('Duplicate table direction')
 if len({(x['investor'],x['sgx_code']) for x in rows})!=40:raise ValueError('Duplicate/conflicting stock direction')
 return rows,week,end,timing

def write_csv(path,rows,fields=None):
 if fields is None:fields=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
 manifest=json.loads((ROOT/'download_manifest.json').read_text())
 reverse=ROOT/'download_manifest_reverse.json'
 if reverse.exists():
  merged={r['report_id']:r for r in manifest}
  for r in json.loads(reverse.read_text()):
   if r['report_id'] not in merged or r['download_status']=='downloaded':merged[r['report_id']]=r
  manifest=sorted(merged.values(),key=lambda r:r['publication_date'])
 allrows=[];checks=[]
 for meta in manifest:
  record=dict(report_id=meta['report_id'],publication_date=meta['publication_date'],title=meta['title'],source_url=meta['url'],local_file=meta['local_file'],sha256=meta.get('sha256',''))
  try:
   if meta['download_status']!='downloaded':raise ValueError(meta.get('download_error','Not downloaded'))
   rows,week,end,timing=extract(meta);allrows.extend(rows)
   record.update(extraction_status='parsed_40_rows',week_start=week.isoformat(),iso_week_start=(week-timedelta(days=week.weekday())).isoformat(),week_end_derived=end.isoformat(),timing_status=timing)
   title_week=weekdate(meta['title'])
   record['title_week_start']=title_week.isoformat() if title_week else ''
   record['title_sheet_week_match']='yes' if title_week==week else 'review_required'
   order_flags=[]
   for inv in ['institutional','retail']:
    for side in ['buy','sell']:
     vals=[Decimal(x['flow_sgd_m']) for x in rows if x['investor']==inv and x['side']==side]
     if vals!=sorted(vals,reverse=side=='buy'):order_flags.append(inv+'_'+side)
   record['rank_order_review']=';'.join(order_flags)
  except Exception as e:record.update(extraction_status='manual_review',error=str(e))
  checks.append(record)
 write_csv(ROOT/'flows_extracted.csv',allrows);write_csv(ROOT/'report_checks.csv',checks)
 master={}
 for r in allrows:
  code=r['sgx_code'];d=master.setdefault(code,{'sgx_code':code,'names':set(),'first_signal_week':r['week_start'],'last_signal_week':r['week_start'],'signal_rows':0})
  d['names'].add(r['security_name']);d['first_signal_week']=min(d['first_signal_week'],r['week_start']);d['last_signal_week']=max(d['last_signal_week'],r['week_start']);d['signal_rows']+=1
 for d in master.values():d['names']=' / '.join(sorted(d['names']))
 write_csv(ROOT/'security_codes_to_map.csv',list(master.values()))
 counter=Counter(x.get('week_start') for x in checks if x.get('week_start'))
 duplicates=[x for x in checks if counter.get(x.get('week_start'),0)>1]
 write_csv(ROOT/'duplicate_weeks.csv',duplicates, list(dict.fromkeys(k for r in checks for k in r)))
 summary=dict(archive_entries=472,download_attempts=len(manifest),downloaded=sum(x['download_status']=='downloaded' for x in manifest),
  reports_parsed=sum(x['extraction_status']=='parsed_40_rows' for x in checks),signal_rows=len(allrows),unique_sgx_codes=len(master),
  manual_review=sum(x['extraction_status']=='manual_review' for x in checks),timing_anomalies=sum(x.get('timing_status')=='review_required' for x in checks),
  duplicate_week_records=len(duplicates),title_sheet_mismatches=sum(x.get('title_sheet_week_match')=='review_required' for x in checks),ranking_reviews=sum(bool(x.get('rank_order_review')) for x in checks),by_publication_year=dict(Counter(x['publication_date'][:4] for x in checks)))
 (ROOT/'download_manifest_combined.json').write_text(json.dumps(manifest,indent=2))
 (ROOT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
