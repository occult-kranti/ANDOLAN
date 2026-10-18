from pathlib import Path
import hashlib, json, gzip, importlib.util
W=Path(__file__).parent
D=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/world-lane-frontage/W1-actual-r2')
B=D.parent/'W1-actual-r1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert not D.exists()
assert sha(B/'receipt.json')=='9f90513e9f38c2c51f4c4f8b8057447713aab4aa388ea53b659ab2f3dc96c755'
checks=[]
def check(name,ok):
 checks.append({'label':name,'passed':bool(ok)})
 assert ok,name
spec=importlib.util.spec_from_file_location('snapshot',W/'harness/snapshot.py');snap=importlib.util.module_from_spec(spec);spec.loader.exec_module(snap)
verified={}
for name,path in {'candidate':W/'candidate-project','retained_baseline':Path('/workspace/scratch/yuga-frontage-review-r1/baseline-r4'),'retained_r1_candidate':Path('/workspace/scratch/yuga-frontage-review-r1/candidate-r4')}.items():
 seal=snap.verify(path);verified[name]={'path':str(path),'marker_sha256':sha(path/snap.MARKER),'files':len(seal['files'])};check(name+' complete inventory after actual',True)
r=json.loads((W/'candidate-originals-r1/capture.json').read_text());run=json.loads((W/'candidate-originals-r1-logs/run.json').read_text())
check('candidate complete30/30 clean exit3images',r['complete'] and not r['failure'] and len(r['checks'])==30 and all(c['passed'] for c in r['checks']) and run['complete'] and run['engine_exit']==0 and run['raw_pngs']==3)
check('actual strict3view match',json.loads((W/'actual-comparison-r1.json').read_text())['passed'])
check('source admission controls',all(c['passed'] for c in json.loads((W/'source-admission-controls.json').read_text())['checks']))
log=(W/'candidate-originals-r1-logs/godot.log').read_text();check('no engine warnings/errors',not any(x in log for x in ('ERROR:','WARNING:','SCRIPT ERROR:','leaked at exit')))
for s in r['shots']:
 check(s['id']+' final pose draw correlation',s['pose_correlation']['process_age']==s['pose_correlation']['physics_age']==0 and s['pose_correlation']['post_draw_age']==1 and not s['pose_correlation']['preflight_no_draw'] and len(s['hero_skeleton']['bone_global_poses'])==164)
 check(s['id']+' original PNG hash',sha(W/'candidate-originals-r1'/(s['id']+'.png'))==s['sha256'])
D.mkdir(parents=True);mapping=[]
def copy(src,rel):
 data=src.read_bytes();dst=D/rel;compressed=len(data)>1000000 and src.suffix in ('.json','.log')
 if compressed:dst=dst.with_name(dst.name+'.gz')
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(gzip.compress(data,compresslevel=9,mtime=0) if compressed else data)
 decoded=gzip.decompress(dst.read_bytes()) if compressed else dst.read_bytes();check('archive exact '+str(dst.relative_to(D)),decoded==data)
 mapping.append({'source':str(src),'source_bytes':len(data),'source_sha256':hashlib.sha256(data).hexdigest(),'artifact':str(dst.relative_to(D)),'encoding':'gzip-lossless' if compressed else 'original'})
for p in sorted(W.iterdir()):
 if p.is_file() and p.suffix in ('.py','.json','.patch','.log'):copy(p,'preparation/'+p.name)
for p in sorted((W/'harness').rglob('*')):
 if p.is_file() and '__pycache__' not in str(p):copy(p,'harness/'+str(p.relative_to(W/'harness')))
copy(W/'candidate-project/tools/graphics-six/capture_scene_anchors.gd','harness/capture_frontage.gd')
copy(W/'candidate-project/.graphics-six-snapshot.json','source-marker.json')
for phase in ('candidate-preflight-r1','candidate-originals-r1'):
 for p in sorted((W/phase).iterdir()):
  if p.is_file():copy(p,'runs/'+phase+'/'+p.name)
 for name in ('run.json','godot.log','xvfb.log'):copy(W/(phase+'-logs')/name,'runs/'+phase+'/logs/'+name)
(D/'artifact-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
(D/'source-after.json').write_text(json.dumps(verified,indent=2)+'\n')
review='''# Frontage r2 — accepted bounded single-block improvement

W1 directly opened all three new originals and the three retained original baseline views. Floor bands, cornice and window bays now articulate every face, repairing the blank side/rear mass seen in rejected r1. At ordinary gameplay distance the floor rhythm is readable; the close view now identifies a closed two-leaf doorway with a meeting stile and transom. The overview retains building-wide coherence. Root and W4 independently accept this limited improvement. Flat prototype materials, pale tonal patches, a simple doorway and the repetitive broader city remain limitations; these images do not qualify a finished map, temporal transitions, all LODs or GPU performance.

The actual candidate completed30/30 native gates in228.465s, exit0, with three originals and clean full logs. Strict comparison against the original retained baseline passes3/3. Full164 final-modifier bone poses, hero/army state, cameras, clocks, UI, material properties/uniforms, lighting/environment, navigation and retained geometry/colliders match. All shots have process/physics age0 and completed-post-draw age1. The intentional one-block mesh and same-body detailed collider contain4824 triangles/3 reused materials, within the approved bounds. The close camera is a staged eye-height inspection; this is not a continuous collision traversal or an interior-entry claim.

Baseline reuse is explicit: its original images and report are preserved in W1-actual-r1, receipt9f90513e9f38c2c51f4c4f8b8057447713aab4aa388ea53b659ab2f3dc96c755. The successor helper differs only in candidate preload path and admitted triangle count. The comparator admits the exact two added art source identities, helper hash/alias, declared data hash and detailed geometry count. Every other rendering/control comparison remains strict. The inherited normalization of one process-local surface-finish owner metadata key is retained with its raw IDs/hash audit; it is not an exclusion of rendering material properties or independent proof of the finish Node identity.

One preflight comparator failure is retained: the new helper's duplicate res:// source alias was initially absent from the source admission list. The narrow correction requires both helper hash aliases equal and admits only that exact changed alias. Four actual-report source controls pass, including rejection of altered candidate code, helper alias and unchanged runtime pins. No engine take was repeated for this correction. Earlier r1 failures remain untouched in their own packet.

This review uses the immutable96d5 source closure plus declared review-only art/helper overlays and explicit e69 source-project runtime, not a new extracted-package execution. Both the original baseline and new candidate use fresh copies of the same112 Godot/101 Mesa seeds, CPU0,1/LP2 and software llvmpipe. No canonical runtime was changed by W1. Root authorized separate production integration following the independent art disposition; integrated source/CI qualification remains separate.

Only the new candidate originals are duplicated here. Raw JSON/logs are losslessly compressed where large, with exact original-byte mapping; source cache stores and raw assets remain separately pinned. The new candidate, original baseline and rejected r1 candidate inventories were reverified after this run.
'''
(D/'REVIEW.md').write_text(review)
(D/'integrity.json').write_text(json.dumps({'passed':all(c['passed'] for c in checks),'checks':checks},indent=2)+'\n')
files={str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file()}
receipt={'schema':1,'disposition':'ACCEPT bounded single-block architecture; production integration and new source qualification separate','source_commit':'96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12','engine_sha256':run['engine_sha256'],'baseline_receipt':{'path':str(B/'receipt.json'),'sha256':sha(B/'receipt.json')},'candidate_elapsed_seconds':run['engine_elapsed_s'],'candidate_native_checks':30,'actual_matched_views':3,'helper_sha256':sha(W/'candidate-project/tools/graphics-six/capture_scene_anchors.gd'),'comparator_sha256':sha(W/'compare_frontage_r2.py'),'originals':[{'id':s['id'],'artifact':'runs/candidate-originals-r1/'+s['id']+'.png','sha256':s['sha256'],'viewed_by_W1':True} for s in r['shots']],'artifacts':files,'artifact_count':len(files),'integrity_checks':len(checks),'immutable_after_seal':True}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'receipt':str(D/'receipt.json'),'sha256':sha(D/'receipt.json'),'artifacts':len(files),'checks':len(checks),'bytes':sum(x['bytes'] for x in files.values())}))
