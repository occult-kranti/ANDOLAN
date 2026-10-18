from pathlib import Path
import os,json,hashlib,shutil
from PIL import Image
W=Path('/workspace/scratch/yuga-impeccable-ui-r1');D=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/impeccable/W1-actual-r1')
assert not D.exists();assert shutil.disk_usage(W).free>500*1024**2
D.mkdir();mapping={};checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(src,rel):
 dst=D/rel;dst.parent.mkdir(parents=True,exist_ok=True);os.link(src,dst);mapping[rel]={'source':str(src),'sha256':sha(src),'bytes':src.stat().st_size,'same_inode':src.stat().st_ino==dst.stat().st_ino}
def check(n,v):checks.append({'name':n,'passed':bool(v)});assert v,n
cases=[('title100-r1','title100','title100-execution-r1',1,6,0),('title200-r1','title200','title200-execution-r1',2,6,0),('recovery-r1','recovery-first-failed','recovery-execution-r1',1,8,1),('cancel-r2','cancel-fixed','cancel-execution-r2',1,2,0)]
for raw,name,ex,scale,count,code in cases:
 p=W/raw;r=json.loads((p/'run.json').read_text());e=json.loads((W/ex/'execution.json').read_text());pngs=sorted(p.glob('*.png'))
 check(name+' frame count',len(pngs)==count);check(name+' execution/source identity',e['exit_code']==code and e['source_stable'] and e['observed_scale_assertion'] and r['source_unchanged'])
 check(name+' exact runtime',r['engine_sha256']=='e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e')
 for f in pngs:
  s=json.loads(f.with_suffix('.json').read_text());check(name+'/'+f.name+' PNG/scale/dimensions',sha(f)==s['sha256'] and s['content_scale_factor']==scale and Image.open(f).size==(960,540))
 for f in sorted(p.iterdir()):
  if f.is_file():put(f,name+'/'+f.name)
 for f in sorted((W/ex).iterdir()):
  if f.is_file():put(f,'execution/'+name+'/'+f.name)
 if name.startswith('title'):
  check(name+' complete native Quit/imports',r['complete'] and r['verified_exit_code']==0 and r['cleanup_exit']==0 and r['import_cache_unchanged'])
  for f in pngs[:3]:
   s=json.loads(f.with_suffix('.json').read_text());check(name+'/'+f.name+' factual offline description','Offline practice' in s['launch']['description_text'])
 if name=='recovery-first-failed':check('Recovery failure retained exactly',r['complete'] and r['verified_exit_code']==0 and not e['complete'] and 'Could not load global script cache.' in (p/'godot.log').read_text())
 if name=='cancel-fixed':
  s=json.loads((p/'02-queued-cancel-return.json').read_text());check('Actual queued cancel returns active caller',s['transition']['phase']=='cancelled' and not s['transition_owner_present'] and s['scene_can_process'] and s['focus_name']=='OpenLocalSample');check('Fixed tiny fixture has no engine error','\nERROR:' not in (p/'godot.log').read_text() and 'SCRIPT ERROR:' not in (p/'godot.log').read_text())
for f in sorted((W/'preparation').iterdir()):
 if f.is_file():put(f,'preparation/'+f.name)
for n in ['scripts/launch_shell.gd','scripts/loading_presentation.gd','scripts/hero_ui_theme.gd','scripts/scene_transition.gd','scripts/boot.gd','tools/ui-campaign/boot-recovery-plan.json','.godot/global_script_class_cache.cfg','.graphics-six-snapshot.json']:
 put(W/'project'/n,'source/'+n)
put(Path(__file__),'preparation/seal_first_batch.py')
(D/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');(D/'validation.json').write_text(json.dumps({'passed':all(x['passed'] for x in checks),'count':len(checks),'checks':checks,'scope':'Source/framebuffer/input integrity. The initial recovery outer failure is intentionally expected and retained; this is not all-runs-clean acceptance.'},indent=2)+'\n')
(D/'REVIEW.md').write_text('''# Impeccable first changed-surface batch

The six title originals at 100% and 200% support the factual offline clarification. Both mode descriptions, selected mode, primary action and keyboard focus remain visible. The complete hero stays in frame. Root and W5 independently viewed all six; title requires no correction.

The six automatic real boot originals show queued, resource-loading and constructing at both scales. At 100%, the one operation sentence, resource scope and focused Cancel are visible. At 200%, the operation and action remain visible, but resource progress/scope is below the body scroll fold. This incumbent limitation prompted the one separately declared compact-loading correction; this first batch remains unchanged. It does not establish that all progress text was initially visible at 200%.

The missing-scene recovery fixture produced five legible manual endpoints and three queued originals, including actual Retry, return to usable boot, reopen and native Quit 0. Its outer run FAILED with the preserved global-script-cache error. The tiny fixture omitted an existing five-byte cache metadata file. The corrected external transport adds that exact file and hardlinks only immutable font payloads; it changes no product runtime. The subsequent actual native queued-cancel fixture passed, returned focus to its active caller and released transition ownership. Its process ended through declared runner cleanup (-15), not native Quit. Both tiny GL runs retain the expected V-Sync warning; title logs are clean.

All 22 original PNGs decode to 960×540 and match their sidecars. Their observed scales are asserted, not inferred. The title uses the public patched e69 Forward+ runtime with declared copied shader caches; the small recovery/cancel fixtures use the same runtime with GL compatibility and no world. Sampled source/import identities remain exact. This is changed-surface review, not a new export, package qualification, full menu journey or 3D quality acceptance.

W1 directly reviewed all 12 title/loading originals, all five manual recovery endpoints, one representative queued-recovery original and both cancel originals. The two other queued-recovery PNGs are byte-identical to the directly viewed representative. Recovery stills alone do not prove cancellation responsiveness; the separate native burst and recorded controller/owner/caller state do.

The archive hardlinks closed originals and logs without duplicating cache data. Original sources, observer changes, transport correction and the failed run are retained. W5 title visual companion: ../W5-title-visual-r1/receipt.json (c77d93779ac949f9fffa2d9210ea401f153b48503f43dea05ded94781ba34fa1).
''')
arts={str(f.relative_to(D)):{'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(D.rglob('*')) if f.is_file()}
receipt={'scope':'One first-batch changed-title/loading review; compact correction remains separate','disposition':'Title bounded ACCEPT; loading100 PASS; loading200 scroll disclosure requires one correction; recovery outer failure retained; cancel fixture PASS','originals':22,'integrity_checks':len(checks),'artifacts':arts}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'path':str(D),'sha256':sha(D/'receipt.json'),'artifacts':len(arts),'checks':len(checks),'free':shutil.disk_usage(W).free}))
