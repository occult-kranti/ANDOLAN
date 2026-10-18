from pathlib import Path
import hashlib,json
from PIL import Image
W=Path(__file__).parent.parent
BASE=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish')
D=BASE/'hair-volume-r3/W1-actual-r1';assert not D.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(n,ok):checks.append({'label':n,'passed':bool(ok)});assert ok,n
r=json.loads((W/'actual-r1/capture.json').read_text());e=json.loads((W/'actual-execution-r1/execution.json').read_text())
oldpath=BASE/'hair-sculpt-design/W1-clay-actual-r2';old=json.loads((oldpath/'originals/capture.json').read_text())
check('priorC2 sealed owner',sha(oldpath/'receipt.json')=='800a5fd2e82b38c715f06f24e46a0f2641a878dc5fffc42242e11fcde3e3ee58')
check('C3 four actual views complete exit0 unchanged',r['complete'] and r['saved_scene_unchanged'] and not r['preflight_only'] and e['complete'] and e['exit_code']==0 and e['source_unchanged'] and len(r['views'])==4)
check('raw32 sample same policy',r['samples']==old['samples']==32 and r['use_denoising']==old['use_denoising']==False)
viewed=[]
for a,b in zip(old['views'],r['views']):
 check(b['id']+' exact camera/lens/context',a['id']==b['id'] and a['camera_matrix_world']==b['camera_matrix_world'] and a['lens_mm']==b['lens_mm'] and a['head_context_normalized_bounds']==b['projection']['head_context'])
 p=W/'actual-r1'/(b['id']+'.png');check(b['id']+' PNG identity/dimensions',sha(p)==b['png_sha256'] and Image.open(p).size==(1024,1024))
 viewed.append({'id':b['id'],'artifact':'originals/'+p.name,'sha256':sha(p),'opened_directly_by_W1':True})
check('actual log no warning/error',not any(x in (W/'actual-execution-r1/run.log').read_text().lower() for x in ('warning:','error:','traceback')))
companions={}
for name,expected in [('W2-validation','66a52a7241620a3224a880e8c51cb53c5fbcfd16d86730ee18acdd441e245b65'),('W2-visual-r1','5b7251e3868028587fd852bda518f9fe5831ec28909bf192eacd6a1f1e8ef02c')]:
 p=D.parent/name/'receipt.json';check(name+' exact reference',sha(p)==expected);companions[name]={'path':str(p),'sha256':sha(p)}
D.mkdir(parents=True);mapping=[]
def copy(p,relative):
 dest=D/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());check('archive '+relative,sha(dest)==sha(p));mapping.append({'source':str(p),'artifact':relative,'sha256':sha(p),'bytes':p.stat().st_size})
for p in sorted((W/'actual-r1').iterdir()):
 if p.is_file():copy(p,'originals/'+p.name)
for n in ('run.py','run.log','execution.json','seal.py'):copy(W/'actual-execution-r1'/n,'execution/'+n)
for p in e['source_before']:
 p=Path(p)
 if p.suffix=='.py':copy(p,'source/'+p.name)
for n in ('construction-receipt.json','manifest.json','projection.json'):copy(W/'build-r1'/n,'source/'+n)
(D/'artifact-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
(D/'REVIEW.md').write_text('''# C3 diagnostic clay: revised volumes visible; coarse shape not approved

W1 directly opened all four1024×1024 originals. C3 has thicker overlapping masses and a lower bent loop, addressing part of C2's flat-sheet/upright-cap direction. However, large exposed scalp channels, sparse broad leaf-shaped sweeps and blunt heavy rear locks remain dominant. The rear and profile do not yet read as the intended gathered continuous hair flow. W1 withholds coarse-form approval; W2 independently viewed all four plus the concept and rejected the shape. Face and crown are recognizable, but hardware fit is not qualified by these images.

The diagnostic was explicitly allowed despite the retained crossing census. W2 reports closed, consistently wound source/union volumes and a protected semantic census; head intersections are inward/tangential rather than visible outward breakthrough. Gold contacts include temples and the fixed tie, with outward witnesses. The actual side rail crosses the hair region and the tie enters/exits the folded mass; these views do not establish clean hardware seating or quantify penetration depth. No blanket zero-root-intersection requirement was imposed, and no fit acceptance is inferred from the render succeeding. W2's exact finite validation and visual companion receipts are linked in this owner receipt. Its semantic comparison is a pinned exported census, not an independent Blender reload.

All four authoring images completed cleanly in89.554s, native exit0, Blender4.3.2 CPU Cycles32 samples/no denoising onCPU0,1. The saved scene, helper and projection dependency remain exact before/after. Camera matrices, lenses, locked-head projections and1024 resolution agree with the C2 actual views. The helper checks actual projection framing before rendering and retains a500MiB workspace reserve. No geometry, material, light, camera or runtime source was changed by W1.

These are editable coarse authoring views; the fourth is an unanimated oblique authoring angle. They are not Godot frames, animation/secondary/rig validation, final material quality, a GLB import, hardware-performance evidence or canonical promotion. No new export was made. The editable scene remains pinned by1d4a2f77b09a721655145c120ec58c72f2752ec72d464c0fd27c1fc1913646b3 in the director's source packet. This archive keeps exact originals, actual command/log/metadata, helper and source construction/projection references without another scene copy.
''')
(D/'integrity.json').write_text(json.dumps({'passed':all(c['passed'] for c in checks),'checks':checks},indent=2)+'\n')
files={str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file()}
receipt={'schema':1,'disposition':'DIAGNOSTIC complete; W1/W2 coarse-shape rejection/withheld approval; hardware fit unresolved; no promotion','scene_sha256':r['scene_sha256'],'helper_sha256':r['helper_sha256'],'elapsed_seconds':e['elapsed_seconds'],'priorC2_receipt_sha256':sha(oldpath/'receipt.json'),'companions':companions,'originals':viewed,'artifacts':files,'artifact_count':len(files),'integrity_checks':len(checks),'immutable_after_seal':True}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'receipt':str(D/'receipt.json'),'sha256':sha(D/'receipt.json'),'artifacts':len(files),'checks':len(checks),'bytes':sum(x['bytes'] for x in files.values())}))
