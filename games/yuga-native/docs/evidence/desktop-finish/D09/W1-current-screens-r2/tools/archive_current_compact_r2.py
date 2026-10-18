from pathlib import Path
import collections,hashlib,importlib.util,json,shutil
from PIL import Image
import numpy as np
root=Path('/workspace/ANDOLAN/games/yuga-native');work=Path('/tmp/yuga-desktop-recovery-r1');before=Path('/tmp/yuga-desktop-current-compact-warm-r1');out=Path('/tmp/yuga-desktop-current-compact-warm-r2');logs=out.with_name(out.name+'-logs');project=work/'compact-current-project-r2';dest=root/'docs/evidence/desktop-finish/D09/W1-current-screens-r2'
assert not dest.exists();dest.mkdir(parents=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cp(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);assert sha(p)==sha(q)
spec=importlib.util.spec_from_file_location('snapshot',root/'tools/graphics-six/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a=m.verify(work/'compact-current-project-r1');b=m.verify(project);delta=sorted(k for k in a['files'].keys()|b['files'].keys() if a['files'].get(k)!=b['files'].get(k));assert delta==['scripts/confluence_world.gd']
r=json.loads((logs/'run.json').read_text());j=json.loads((out/'capture.json').read_text());assert r['complete'] is True and j['complete'] is True and all(x['passed'] is True for x in j['checks']) and len(j['checks'])==14
comparisons=[]
for p in sorted(out.glob('*.png')):
 x=np.asarray(Image.open(before/p.name));y=np.asarray(Image.open(p));d=np.abs(x.astype('int16')-y.astype('int16'));comparisons.append({'file':p.name,'before_sha256':sha(before/p.name),'after_sha256':sha(p),'changed_pixels':int(np.any(d,axis=2).sum()),'max_channel_difference':int(d.max())})
assert sum(x['changed_pixels']==0 for x in comparisons)==8
for p in out.iterdir():
 if p.is_file():cp(p,dest/'originals'/p.name)
for name in ['run.json','godot.log','xvfb.log']:cp(logs/name,dest/name)
cp(project/m.MARKER,dest/'snapshot.json');cp(project/'scripts/confluence_world.gd',dest/'overlay/scripts/confluence_world.gd')
for name in ['stage_compact_current_r2.py','compact-current-r2-source.json']:cp(work/name,dest/'staging'/name)
for name in ['run_focus.py','snapshot.py','capture_compact_screens.gd']:cp((project if name.endswith('.gd') else root)/'tools/graphics-six'/name,dest/'tools'/name)
cp(Path(__file__),dest/'tools/archive_current_compact_r2.py')
for name in ['run.json','godot.log','xvfb.log']:cp(Path('/tmp/yuga-desktop-current-compact-preflight-r2-logs')/name,dest/'preflight'/name)
cp(Path('/tmp/yuga-desktop-current-compact-preflight-r2/preflight.json'),dest/'preflight/preflight.json')
comparison={'passed':True,'source_delta':delta,'pixel_comparison':comparisons,'corrected_card':j['shots'][6]['visible_panels']['compact_world_card'],'scope':'Pixels compared at exact dimensions without resampling. Eight unchanged images, five one-level pixels at125%, and expected150% summary repair. No temporal/hardware-FPS inference.'}
(dest/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
(dest/'REVIEW.md').write_text('''# Repaired first150% compact summary

The unchanged ten-shot fixture completed all ten original960×540 frames and14/14 checks with world6e9d, exit0 in140.424 seconds. The fresh child36351a18 differs from the retained failed310c child only in `scripts/confluence_world.gd`. Helper9a0f, camera, viewport-input sequence, imports and other runtime sources are unchanged. Both source/store inventories and both input cache trees passed their after-run verification.

I directly inspected the new150% and125% world originals. At150%, all four summary rows are now readable inside the665.3333×102 logical card; the previous22-high strip is corrected. It leaves the neutral hero, map and primary ability HUD clear. The125% layout retains its separate cards and complete controls. W4 independently inspected the repaired150% original. Eight of the other corresponding images have exactly equal decoded pixels to the prior take;125% differs at only five pixels by one8-bit channel level. Those eight exact images inherit the prior direct visual review, not a claim of ten newly reviewed images. `comparison.json` binds each before/after PNG and records the complete comparison.

This accepts the bounded first-entry summary correction. The earlier failedtake and its visual rejection remain unchanged in `../W1-current-screens-r1`. The title200% fix remains visible. Dynamic score wrapping was not witnessed by the owner's fresh-entry test, and no recurring sizing mechanism is claimed. Broad environment/hero/art quality, night, continuous motion, terminal states and sound remain outside this ten-screen acceptance.

The engine is the unmodified public4.6.3 template dce0422d, CPU0,1 with two llvmpipe threads. Each run copied the same112 Godot and101 Mesa cache inputs into fresh XDG directories. This is a warm software-rendered capture, not cold-launch or hardware-performance qualification. All logs are retained:120 RGB8→RGBA8 conversion warnings, no engine errors. Headless preflight14/14 also passed with zero PNGs. The final native23-view journey uses a separately frozen current child and starts only after this engine exits.
''')
warnings=dict(collections.Counter(s for s in (logs/'godot.log').read_text().splitlines() if s.startswith(('WARNING:','ERROR:','SCRIPT ERROR:'))))
artifacts={p.relative_to(dest).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(dest.rglob('*')) if p.is_file()}
receipt={'schema':1,'capture_passed':True,'bounded_visual_fix_passed':True,'capture_checks':14,'raw_originals':10,'directly_reviewed_successor_images':2,'previously_reviewed_pixel_identical_images':8,'engine_seconds':r['engine_elapsed_s'],'warnings':warnings,'artifacts':artifacts,'scope':'First150% compact-summary correction, not full product/art acceptance.'}
(dest/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'path':str(dest),'receipt':sha(dest/'receipt.json'),'review':sha(dest/'REVIEW.md'),'artifacts':len(artifacts)},indent=2))
