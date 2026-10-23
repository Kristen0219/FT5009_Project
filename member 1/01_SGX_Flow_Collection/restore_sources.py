"""Restore packaged raw SGX files, refusing path traversal or conflicting files."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
ROOT=Path(__file__).resolve().parent
count=0
for archive in sorted((ROOT/'source_archives').glob('*.zip')):
 with ZipFile(archive) as z:
  for info in z.infolist():
   dest=(ROOT/info.filename).resolve()
   if not dest.is_relative_to(ROOT/'raw') or info.is_dir():raise ValueError('Invalid archive member')
   data=z.read(info)
   if dest.exists() and dest.read_bytes()!=data:raise ValueError(f'Existing raw file differs: {dest.name}')
   dest.parent.mkdir(exist_ok=True);dest.write_bytes(data);count+=1
print('Restored raw reports:',count)
