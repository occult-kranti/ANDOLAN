#!/usr/bin/env python3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,os,subprocess,time
ROOT=Path('/workspaces/ANDOLAN');BASE=Path(__file__).resolve().parent
old=json.loads((BASE/'sources-before.json').read_text())
paths=list(old)+['games/yuga-native/tests/ui_pause_navigation_cases.gd','docs/research/video-study/integration-qa/shop-result-counterexamples.gd']
def hashes(): return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
before=hashes()
JOBS=[('ui_pause_navigation_cases-r4','res://tests/ui_pause_navigation_cases.gd'),('siege_ui_cases-r3','res://tests/siege_ui_cases.gd'),('shop-result-counterexamples-r2',str(BASE/'shop-result-counterexamples.gd'))]
def run(job):
 name,script=job;folder=BASE/name;folder.mkdir(exist_ok=False);env=os.environ.copy();env['XDG_DATA_HOME']=str(folder/'user-data')
 command=['godot','--headless','--path','games/yuga-native','--script',script,'--',f'--report={folder}/report.json'];start=time.monotonic()
 with (folder/'run.log').open('w') as log:r=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 data=json.loads((folder/'report.json').read_text());checks=data['checks']
 result={'suite':name,'command':command,'environment':{'XDG_DATA_HOME':env['XDG_DATA_HOME']},'exit_code':r.returncode,'passed':r.returncode==0 and data['passed'],'checks':len(checks),'failed_checks':[c for c in checks if not c['passed']],'wall_s':round(time.monotonic()-start,3),'report_sha256':hashlib.sha256((folder/'report.json').read_bytes()).hexdigest(),'log_sha256':hashlib.sha256((folder/'run.log').read_bytes()).hexdigest()}
 (folder/'execution.json').write_text(json.dumps(result,indent=2)+'\n');return result
results=[]
with ThreadPoolExecutor(max_workers=2) as pool:
 for f in as_completed([pool.submit(run,j) for j in JOBS]):
  r=f.result();results.append(r);print(json.dumps(r),flush=True)
after=hashes();index={'passed':all(r['passed'] for r in results) and before==after,'source_unchanged':before==after,'sources_before':before,'sources_after':after,'results':results,'scope':'Independent headless UI/siege shop boundary reruns after root fresh-pause scroll correction. No rendering/import/export/OS-window input.'}
(BASE/'final-boundaries-index.json').write_text(json.dumps(index,indent=2)+'\n');print(json.dumps({'passed':index['passed'],'source_unchanged':index['source_unchanged'],'checks':sum(r['checks'] for r in results)}),flush=True)
