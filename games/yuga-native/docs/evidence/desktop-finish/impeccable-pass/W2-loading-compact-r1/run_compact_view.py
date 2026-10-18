"""Same observable view regression against exact original and candidate; no import/render."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
PROJECT=Path(__file__).resolve().parents[5]
BASE=Path('/workspace/scratch/yuga-impeccable-w2-loading-compact-r2')
assert not BASE.exists();BASE.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original=Path('/workspace/scratch/yuga-impeccable-w2-loading-r1/candidate/project/scripts/loading_presentation.gd').read_bytes()
assert hashlib.sha256(original).hexdigest()=='bdd5c139e9eb70e709aff2b3bbfb396cd9633e073739435fc30898ed30dda1e5'
(BASE/'baseline-loading_presentation.gd').write_bytes(original)
engine=Path(shutil.which('godot')).resolve();reports=[]
files=['scripts/loading_presentation.gd','scripts/hero_ui_theme.gd','tests/desktop_finish_s2_loading_view_cases.gd']
files +=[str(p.relative_to(PROJECT))for p in (PROJECT/'assets/fonts').glob('*')if p.is_file()]
files +=[str(p.relative_to(PROJECT))for p in (PROJECT/'.godot/imported').glob('*.ttf-*')if p.is_file()]
for variant in ['baseline','candidate']:
 out=BASE/variant;project=out/'project';project.mkdir(parents=True)
 for name in files:
  source=BASE/'baseline-loading_presentation.gd'if variant=='baseline'and name=='scripts/loading_presentation.gd'else PROJECT/name
  dest=project/name;dest.parent.mkdir(parents=True,exist_ok=True)
  if name.startswith(('assets/fonts/','.godot/imported/')):
   immutable=Path('/workspace/scratch/yuga-impeccable-w2-loading-r1/candidate/project')/name
   assert sha(immutable)==sha(source);os.link(immutable,dest)
  else:shutil.copyfile(source,dest)
 (project/'project.godot').write_text('config_version=5\n[application]\nconfig/name="YUGA loading view regression"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
 pins={name:sha(project/name)for name in files};env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',XDG_DATA_HOME=str(out/'data'),XDG_CONFIG_HOME=str(out/'config'))
 command=[str(engine),'--headless','--path',str(project),'--script','res://tests/desktop_finish_s2_loading_view_cases.gd','--','--report='+str(out/'report.json')]
 started=time.monotonic();result=subprocess.run(command,capture_output=True,text=True,env=env,timeout=20);elapsed=time.monotonic()-started
 (out/'run.log').write_text(result.stdout+result.stderr)
 report=json.loads((out/'report.json').read_text())if(out/'report.json').exists()else{}
 receipt=dict(variant=variant,command=command,exit_code=result.returncode,elapsed_seconds=elapsed,cpu_affinity=sorted(os.sched_getaffinity(0)),engine_sha256=sha(engine),sources=pins,sources_unchanged=all(sha(project/n)==h for n,h in pins.items()),count=report.get('count'),passed=report.get('passed'),log_sha256=sha(out/'run.log'),warnings=[s for s in (result.stdout+result.stderr).splitlines()if any(k in s for k in ['WARNING:','ERROR:','leaked'])])
 (out/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n');reports.append(receipt);print(json.dumps({k:receipt[k]for k in ['variant','exit_code','elapsed_seconds','count','passed','warnings']}),flush=True)
assert reports[0]['exit_code']==1 and reports[0]['passed']is False
assert reports[1]['exit_code']==0 and reports[1]['passed']is True and not reports[1]['warnings']
assert all(r['sources_unchanged']for r in reports)
