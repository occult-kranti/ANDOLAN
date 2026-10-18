#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,os,subprocess,time
OWNER=Path(__file__).resolve().parent
ROOT=Path('/workspace/scratch/yuga-continuation-W5-anticipation-r1')
STAGE=Path('/workspace/scratch/yuga-continuation-W5-r1/project-r2')
ENGINE=Path('/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority')
CANONICAL=Path('/workspace/ANDOLAN/games/yuga-native/scripts/rama_motion.gd')
def pin(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert pin(ENGINE)=='e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'
assert pin(CANONICAL)=='5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5'
for fixture_name,case,timeout in [('component_descent.gd','component-r1',180),('preparation_guards.gd','guards-r1',90)]:
 out=ROOT/case;out.mkdir();fixture=OWNER/fixture_name
 pins={str(p):pin(p) for p in [fixture,OWNER/'rama_motion.gd',STAGE/'scripts/rama_motion.gd',CANONICAL,Path('/workspace/ANDOLAN/games/yuga-native/tests/graphics_g2_support_cases.gd'),ENGINE]}
 cmd=['taskset','-c','3',str(ENGINE),'--headless','--path',str(STAGE),'--script',str(fixture),'--','--report='+str(out/'report.json')]
 env=os.environ.copy();env.update({k:'1' for k in ['LP_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']});env.update({k:str(out/k) for k in ['XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME']});t=time.time()
 with (out/'godot.log').open('wb') as log:
  try:code=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout).returncode
  except subprocess.TimeoutExpired:code=124
 report=json.loads((out/'report.json').read_text()) if (out/'report.json').exists() else {};diagnostics=[s for s in (out/'godot.log').read_text().splitlines() if any(x in s for x in ['SCRIPT ERROR','ERROR:','WARNING:'])]
 receipt={'command':cmd,'timeout_s':timeout,'elapsed_s':time.time()-t,'exit_code':code,'source_before':pins,'source_after':{p:pin(Path(p)) for p in pins},'engine_diagnostics':diagnostics,'report_sha256':pin(out/'report.json') if report else None,'passed':code==0 and report.get('passed',False) and not diagnostics}
 (out/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'case':case,'passed':receipt['passed'],'elapsed_s':receipt['elapsed_s'],'checks':report.get('count'),'failures':[c['name'] for c in report.get('checks',[]) if not c['passed']],'diagnostics':diagnostics}),flush=True)
