from pathlib import Path
import json,hashlib
W=Path(__file__).parent.parent
D=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/hair-sculpt-design/W1-clay-actual-r2')
assert not D.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,ok):checks.append({'label':name,'passed':bool(ok)});assert ok,name
r=json.loads((W/'actual-r1/capture.json').read_text());e=json.loads((W/'actual-execution-r1/execution.json').read_text())
prior=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/hair-sculpt-design/W1-clay-actual-r1')
check('prior actual receipt unchanged',sha(prior/'receipt.json')=='c269232822c5dc7b4ac8b4528fd0df0b8cf63133e2e98aa01322244579f30c0a')
old=json.loads((prior/'actual-execution-r2/render-r1/capture.json').read_text())
check('complete actual4 exit0 sourceunchanged',e['complete'] and e['exit_code']==0 and e['source_unchanged'] and r['complete'] and not r['preflight_only'] and r['scene_unchanged_after'] and len(r['views'])==4)
check('32raw samples1024 unchanged render settings',r['render_engine']==old['render_engine']=='CYCLES' and r['samples']==old['samples']==32 and r['use_denoising']==old['use_denoising']==False and r['resolution']==old['resolution']==[1024,1024])
controls=[]
for a,b in zip(old['views'],r['views']):
 same=all(a[k]==b[k] for k in ('id','camera_matrix_world','lens_mm','view_scope','head_context_normalized_bounds'))
 check(b['id']+' actual camera/context unchanged',same)
 check(b['id']+' full evaluated hair/head framing',b['full_hair_framed'] and b['head_context_framed'])
 check(b['id']+' original hash',sha(W/'actual-r1'/(b['id']+'.png'))==b['png_sha256'])
 controls.append({'id':b['id'],'camera_and_locked_context_equal':same,'png_sha256':b['png_sha256'],'viewed_by_W1':True})
log=(W/'actual-execution-r1/run.log').read_text();check('actual render log no exception/error/warning',not any(x in log.lower() for x in ('traceback','error:','warning:')))
proof=json.loads((W/'saved-final-r1/hair-only-proof.json').read_text())
check('hair-only scene proof correct parent/current',proof['parent_scene_sha256']==old['blend_sha256'] and proof['scene_sha256']==r['blend_sha256'] and all(any(x.startswith(p) for p in proof['allowed_difference_prefixes']) for x in proof['difference_paths']))
D.mkdir(parents=True);mapping=[]
def copy(p,rel):
 dest=D/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());check('archive exact '+rel,sha(dest)==sha(p));mapping.append({'source':str(p),'artifact':rel,'sha256':sha(p),'bytes':p.stat().st_size})
for p in sorted((W/'actual-r1').iterdir()):
 if p.is_file():copy(p,'originals/'+p.name)
for n in ('run.py','run.log','execution.json','seal.py'):copy(W/'actual-execution-r1'/n,'execution/'+n)
for n in ('capture_sculpt_r2.py','projection_contract.py','helper-delta.json'):copy(W/'render-preparation-final-r1'/n,'source/'+n)
for n in ('hair-only-proof.json','semantic-before.json','semantic-after.json'):copy(W/'saved-final-r1'/n,'source/'+n)
(D/'comparison.json').write_text(json.dumps({'passed':True,'scope':'Matched actual authoring settings/cameras/locked reference; changed coarse hair shape, not runtime or animation.','prior_receipt_sha256':sha(prior/'receipt.json'),'views':controls},indent=2)+'\n')
(D/'artifact-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
(D/'REVIEW.md').write_text('''# C2 authoring clay — revise coarse shape; no promotion

W1 directly opened all four1024×1024 originals. The previous rear diamond-shaped gap is closed and the lower mass is fuller. Those gains do not resolve the overall silhouette: the front/profile still read as a smooth helmet cap with a sharp continuous lower rim, and the knot remains an upright extension above the gathering. The rear is a broad curtain with merged pendant ends; the profile and oblique view expose a large sheet edge and folded/faceted underside instead of gathered, overlapping S-shaped hair volumes. W2 independently opened all four and reached the same coarse-shape rejection. No detail pass, UV, rigging, GLB export or canonical promotion is approved by this evidence.

All four images completed in85.328s, Blender4.3.2 CPU Cycles32 samples, raw/no denoising, two threads onCPU0,1. Native exit0, clean actual log, source scene/helper/dependency unchanged before/after. These are editable authoring-clay views with locked reference head/crown. The fourth camera is a rest-space oblique authoring angle; it is not a public animated cast or runtime frame. Noise is an explicit rendering limitation; the disposition concerns the visible large forms.

Actual camera matrices, lenses, reference-head projections, resolution and render settings match the first four-view clay take exactly. The source semantic proof admits only the editable hair cage and localized depth/modifier changes; materials, lighting, reference geometry and cameras remain matched. All four evaluated-hair/reference framing checks pass. Prior scene/helper/render failures and rejected C1 originals remain untouched in their separate packets.

The scene is pinned by SHA161233be93ed7b340707d8f267d85bf3b174880361ed1124b92561abf2593368 and remains under the W2 source/recovery packet. This owner archive retains the four original PNGs, full actual log/command/metadata, exact helper and source semantic proof without duplicating the editable scene. Source-rest/projection checks are not aesthetic acceptance or runtime collision/motion qualification.
''')
(D/'integrity.json').write_text(json.dumps({'passed':all(c['passed'] for c in checks),'checks':checks},indent=2)+'\n')
files={str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file()}
receipt={'schema':1,'disposition':'REVISE coarse authoring shape; no detail/UV/rig/GLB/runtime promotion','elapsed_seconds':e['elapsed_seconds'],'scene_sha256':r['blend_sha256'],'helper_sha256':r['helper_sha256'],'projection_dependency_sha256':e['source_before']['projection_contract.py'],'prior_receipt_sha256':sha(prior/'receipt.json'),'originals':controls,'artifacts':files,'artifact_count':len(files),'integrity_checks':len(checks),'immutable_after_seal':True}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'receipt':str(D/'receipt.json'),'sha256':sha(D/'receipt.json'),'artifacts':len(files),'checks':len(checks),'bytes':sum(x['bytes'] for x in files.values())}))
