"""Restore compactly packaged source, derived-data and diagnostic archives."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
ROOT=Path(__file__).resolve().parent

def restore_sources():
 manifest=ROOT/'archive_manifest.json'
 if not manifest.exists():return
 restored=0
 for item in json.loads(manifest.read_text()):
  p=ROOT/item['file']
  if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Archive checksum mismatch: '+item['file'])
  with ZipFile(p) as z:
   for info in z.infolist():
    target=(ROOT/info.filename).resolve()
    if info.is_dir():continue
    if not target.is_relative_to(ROOT) or target.suffix not in ['.csv','.json','.xlsx','.txt']:raise ValueError('Unsafe archive member')
    if target.exists():
     # Outputs may have been regenerated legitimately; never overwrite an existing file.
     continue
    target.parent.mkdir(parents=True,exist_ok=True)
    with z.open(info) as source,target.open('wb') as dest:
     while block:=source.read(1024*1024):dest.write(block)
    restored+=1
 print('Restored packaged data files:',restored)
if __name__=='__main__':restore_sources()
