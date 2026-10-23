"""Reproduce extraction, current baseline, quality handoff and tests offline."""
from pathlib import Path
import subprocess,sys,shutil
root=Path(__file__).resolve().parent
source=root/'01_SGX_Flow_Collection';baseline=root/'02_Baseline_Backtesting'
for script in ['restore_sources.py','parse_history.py','verify_dataset.py']:
 subprocess.run([sys.executable,str(source/script)],check=True)
for name in ['flows_extracted.csv','report_checks.csv','security_codes_to_map.csv']:
 shutil.copy2(source/name,baseline/name)
subprocess.run([sys.executable,str(baseline/'run_offline_pipeline.py')],check=True)
subprocess.run([sys.executable,'-m','unittest','discover','-s',str(baseline/'tests'),'-v'],check=True)
subprocess.run([sys.executable,str(baseline/'audit_requirements.py')],check=True)
