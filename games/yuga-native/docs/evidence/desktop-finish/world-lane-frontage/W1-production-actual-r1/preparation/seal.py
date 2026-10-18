from pathlib import Path
import hashlib,json,gzip,importlib.util
W=Path(__file__).parent;D=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/world-lane-frontage/W1-production-actual-r1');assert not D.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(n,ok):checks.append({'label':n,'passed':bool(ok)});assert ok,n
accepted=D.parent/'W1-actual-r2/receipt.json';check('accepted owner unchanged',sha(accepted)=='141828c95e8c5c832f1bd8b08c108132deb02ea9a08dc0a9b5552aeba7341d6d')
spec=importlib.util.spec_from_file_location('snapshot',W/'harness/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source_after={}
for label,p in [('production',W/'project'),('accepted',Path('/workspace/scratch/yuga-frontage-review-r2/candidate-project'))]:
 s=m.verify(p);source_after[label]={'marker_sha256':sha(p/m.MARKER),'files':len(s['files']),'path':str(p)};check(label+' inventory exact afteractual',True)
r=json.loads((W/'actual-r1/capture.json').read_text());run=json.loads((W/'actual-r1-logs/run.json').read_text())
check('actual31/31 complete exit0 threeimages',r['complete'] and not r['failure'] and len(r['checks'])==31 and all(c['passed'] for c in r['checks']) and run['complete'] and run['engine_exit']==0 and run['raw_pngs']==3)
check('strict actual3/3 no control differences',json.loads((W/'actual-comparison-r1.json').read_text())['passed'])
check('five realpair/negative guards',all(c['passed'] for c in json.loads((W/'comparison-controls.json').read_text())['checks']))
log=(W/'actual-r1-logs/godot.log').read_text();check('clean native log',not any(s in log for s in ('ERROR:','WARNING:','SCRIPT ERROR:','leaked at exit')))
for s in r['shots']:check(s['id']+' original hash',sha(W/'actual-r1'/(s['id']+'.png'))==s['sha256'])
D.mkdir(parents=True);mapping=[]
def copy(p,relative):
 data=p.read_bytes();dest=D/relative;compressed=len(data)>1000000 and p.suffix in ('.json','.log')
 if compressed:dest=dest.with_name(dest.name+'.gz')
 dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(gzip.compress(data,compresslevel=9,mtime=0) if compressed else data);decoded=gzip.decompress(dest.read_bytes()) if compressed else dest.read_bytes();check('archive '+str(dest.relative_to(D)),decoded==data)
 mapping.append({'source':str(p),'artifact':str(dest.relative_to(D)),'source_sha256':hashlib.sha256(data).hexdigest(),'source_bytes':len(data),'encoding':'gzip-lossless' if compressed else 'original'})
for p in sorted(W.iterdir()):
 if p.is_file() and p.suffix in ('.py','.json','.patch','.log'):copy(p,'preparation/'+p.name)
for p in sorted((W/'harness').rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts:copy(p,'harness/'+str(p.relative_to(W/'harness')))
for n in ('scripts/confluence_world.gd','scripts/world_lane_frontage.gd','scripts/world_lane_frontage.gd.uid','assets/world/block2-frontage.json','tools/graphics-six/capture_scene_anchors.gd','.graphics-six-snapshot.json'):copy(W/'project'/n,'source/'+n)
H=Path('/workspace/scratch/yuga-frontage-production-helper-r1')
for p in sorted(H.iterdir()):
 if p.is_file():copy(p,'helper-provenance/'+p.name)
for phase in ('preflight-r1','actual-r1'):
 for p in sorted((W/phase).iterdir()):
  if p.is_file():copy(p,phase+'/'+p.name)
 for n in ('run.json','godot.log','xvfb.log'):copy(W/(phase+'-logs')/n,phase+'/logs/'+n)
(D/'artifact-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');(D/'source-after.json').write_text(json.dumps(source_after,indent=2)+'\n')
(D/'REVIEW.md').write_text('''# Default production frontage: bounded appearance preserved

The actual product-startup capture completed31/31 native checks in217.261s, exit0, with three originals and clean logs. W1 and root directly opened the product-camera, staged eye-height contact and native overview views. The accepted floor bands, closed entrance and articulated side/rear bays remain visible through the production caller. This accepts the one-block integration in these views; flat prototype materials, sparse/repetitive broader city, temporal/LOD coverage and hardware performance remain open.

The helper never calls configure. It observes the already-present production root, visible mesh, effective materials and matching published Concave shape before connecting the final-pose observer, with no simulation step between admission and connection. Exact production caller1301701f, module dcd0c73d, UID7506c284 and default assets/world/block2-frontage.json67950a68 are pinned. The caller invokes the default module during ordinary world startup after the roof and before the player. These four runtime files and a read-only observer replace/add files over the verified96d5 closure; all other existing runtime source bytes match current canonical. No full clone, editor import, cache mutation or canonical edit was performed by W1.

Comparison with the accepted R2 candidate passes all three views with no state differences: full164 final-modifier poses, hero/army, clocks, camera/UI, geometry, detailed collider, material properties/uniforms, lighting/environment, navigation and overview return. There is no geometry or collision exception in this production comparison. Named absolute counters and the previously reviewed single process-local finish-owner metadata key remain the only observation normalization. Scene arrays are compared by their unique paths. Five focused controls accept the real preflight pair and reject missing startup admission, altered caller, material renderer property and collider transform. Native preflight also passed31/31; affected route27/27 and atlas15/15 are independently sealed in W4-production-world-support-r1.

The contact PNG is byte-identical to accepted R2. The product image differs in one RGB pixel by1/255, and overview in1305pixels with maximum1/255 channel difference; no causal explanation is inferred. The first auxiliary RGBA bounding-box check returned null because alpha differences were zero despite its correct false-equality flags. That report is preserved; the successor explicitly compares RGB and records the real bounds/counts. This utility correction did not change any input, renderer, image or control assertion.

The same e69 source-project engine,112 Godot/101 Mesa seeds copied to fresh user directories, CPU0,1/LP2 and software llvmpipe were used. This is a source integration capture, not a new exported-package qualification, release claim or GPU FPS result. Original accepted R2 remains pinned by receipt141828c95e8c5c832f1bd8b08c108132deb02ea9a08dc0a9b5552aeba7341d6d. Current source and its parent were reverified after execution. Large raw reports are losslessly gzipped with original-byte mappings; mutable generated caches remain outside this owner archive.
''')
(D/'integrity.json').write_text(json.dumps({'passed':all(c['passed'] for c in checks),'checks':checks},indent=2)+'\n')
files={str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file()}
receipt={'schema':1,'disposition':'ACCEPT bounded default production single-block integration; no new package/fullmap/hardware claim','accepted_receipt_sha256':sha(accepted),'source_base':'96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12','runtime_overlays':json.loads((W/'staging.json').read_text())['runtime_overlay_pins'],'engine_sha256':run['engine_sha256'],'helper_sha256':sha(W/'project/tools/graphics-six/capture_scene_anchors.gd'),'comparator_sha256':sha(W/'compare_production.py'),'elapsed_seconds':run['engine_elapsed_s'],'native_checks':31,'matched_views':3,'originals':[{'id':s['id'],'artifact':'actual-r1/'+s['id']+'.png','sha256':s['sha256'],'viewed_by_W1':True} for s in r['shots']],'artifacts':files,'artifact_count':len(files),'integrity_checks':len(checks),'immutable_after_seal':True}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'receipt':str(D/'receipt.json'),'sha256':sha(D/'receipt.json'),'artifacts':len(files),'checks':len(checks),'bytes':sum(x['bytes'] for x in files.values())}))
