from pathlib import Path
import collections,hashlib,importlib.util,json,shutil
root=Path('/workspace/ANDOLAN/games/yuga-native');work=Path('/tmp/yuga-desktop-recovery-r1');out=Path('/tmp/yuga-desktop-current-compact-warm-r1');logs=out.with_name(out.name+'-logs');project=work/'compact-current-project-r1';dest=root/'docs/evidence/desktop-finish/D09/W1-current-screens-r1'
assert not dest.exists();dest.mkdir(parents=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cp(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);assert sha(p)==sha(q)
spec=importlib.util.spec_from_file_location('snap',root/'tools/graphics-six/snapshot.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
for name in ['current-project','compact-project-r1','compact-125-project-r1','compact-current-project-r1']:s.verify(work/name)
j=json.loads((out/'capture.json').read_text());r=json.loads((logs/'run.json').read_text());assert j['complete'] is True and r['complete'] is True and len(j['shots'])==10 and len(j['checks'])==14 and all(x['passed'] is True for x in j['checks'])
for p in out.iterdir():
 if p.is_file():cp(p,dest/'originals'/p.name)
for name in ['run.json','godot.log','xvfb.log']:cp(logs/name,dest/name)
cp(project/s.MARKER,dest/'snapshot.json')
for name in ['stage_compact_current_r1.py','compact-current-source.json','compact-current-staging-first-rejection.json']:cp(work/name,dest/'staging'/name)
for rel in ['scripts/launch_shell.gd','scripts/confluence_world.gd','scripts/rama_ability_effects.gd','tools/graphics-six/capture_compact_screens.gd']:cp(project/rel,dest/'overlay'/rel)
for name in ['run_focus.py','snapshot.py']:cp(root/'tools/graphics-six'/name,dest/'tools'/name)
cp(Path(__file__),dest/'tools/archive_current_compact_r1.py')
for name in ['run.json','godot.log','xvfb.log']:cp(Path('/tmp/yuga-desktop-current-compact-preflight-r1-logs')/name,dest/'preflight'/name)
cp(Path('/tmp/yuga-desktop-current-compact-preflight-r1/preflight.json'),dest/'preflight/preflight.json')
warnings=dict(collections.Counter(x for x in (logs/'godot.log').read_text().splitlines() if x.startswith(('WARNING:','ERROR:','SCRIPT ERROR:'))))
review='''# Current ten-screen take: title fixed, 150% world summary rejected

The exact current child completed ten original 960×540 Forward+ llvmpipe frames and all fourteen capture predicates in 137.954 seconds, engine exit0. It uses the unmodified public 4.6.3 template engine, CPU0,1, two llvmpipe threads and fresh copies of the successful unmodified control's Godot and Mesa caches. Fixed30 simulation sampling is not hardware FPS. The installed editor and diagnostic priority-patched engine were not used.

I directly inspected all ten originals. Title100/125/150/200 keeps the mode choice and primary action readable; the new200% fixed identity keeps YUGA and the hero label visible with the focused primary, resolving the retained initial-focus crop. Lower navigation at150/200 remains in the indicated scroll region. Hero/camera composition is retained. World100/125 shows the intended cards and controls;200 shows its compact four-line state and ability icon/ready controls. Overview200 preserves the heading and visible scroll cue, and the guide200 retains Bow/selected primary/Back with scrollable content.

**The150% world view fails visual acceptance.** `originals/06-world-150.png` shows the compact state as a thin strip, clipping the first line and hiding its objective/travel information. Its exact sidecar records `CompactWorldState` at665.3333×22 logical pixels at853.3333×480 logical viewport. This is not intentional scrolling. All fourteen structural capture checks still pass, so they do not establish text containment. The failure was routed to W4/root with the original and source pin; no runtime repair or automatic retake was made by W1. The completed take remains an immutable counterexample.

The existing stippled paving, small auxiliary text at100%, simplified infantry and hero hair/material limitations remain open. These ordinary-camera stills do not accept continuous motion, nighttime, sound, terminal outcomes or product-wide visual quality. The viewport-key fixture performs real boot/navigation and observes live world clocks, but is distinct from OS XTest input; the separately prepared full journey has not run here.

The child marker310c20002ae016f6927c3dad9d72194a9541f9c6f91c70d59d5f4768bae0da3b differs from base6349218 only in launch794266, world7570, FX119353 and helper9a0f. Base, original a02 engine fixture and prior b03/04c1 ten-shot child remain verified unchanged. Exact four overlay sources and staging recipe are retained. The first staging label was rejected before copying by the existing G1–G6 identifier rule; the corrected G4 label is recorded without changing product inputs.

Raw logs retain120 RGB8-to-RGBA8 conversion warnings and no engine errors. Source/private-store and seed before/after checks passed. All ten PNG/JSON pairs, complete reports/logs, exact runner/helpers and source inventory are archived. The successful headless preflight also passed14/14 with zero PNGs. Cache provenance is `../../G0/template-baseline-cold-600-r1/cache-preservation.json` plus its text clarification; warm caches are an explicit input, not cold launch qualification.
'''
(dest/'REVIEW.md').write_text(review)
artifacts={p.relative_to(dest).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(dest.rglob('*')) if p.is_file()}
receipt={'schema':1,'capture_passed':True,'visual_acceptance_passed':False,'capture_checks':14,'original_pngs':10,'reviewed_pngs':10,'engine_exit':0,'engine_elapsed_s':r['engine_elapsed_s'],'rejected_view':'06-world-150','warnings':warnings,'artifacts':artifacts,'scope':'Title crop correction visually accepted in four-scale take;150% world summary explicitly rejected; no product-wide acceptance.'}
(dest/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print({'path':str(dest),'receipt_sha256':sha(dest/'receipt.json'),'review_sha256':sha(dest/'REVIEW.md'),'artifacts':len(artifacts)})
