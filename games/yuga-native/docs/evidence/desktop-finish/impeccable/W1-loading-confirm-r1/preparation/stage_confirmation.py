from pathlib import Path
import os,hashlib,json,shutil,difflib
W=Path('/workspace/scratch/yuga-impeccable-loading-confirm-r1');P=W/'source';PRE=W/'preparation';B=Path('/workspace/scratch/yuga-impeccable-ui-r1/project');C=Path('/workspace/ANDOLAN/games/yuga-native');Q=C/'docs/evidence/desktop-finish/impeccable-pass/W2-loading-compact-r1'
assert not W.exists();assert shutil.disk_usage(B).free>500*1024**2+2*1024**2
P.mkdir(parents=True);PRE.mkdir()
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
files=['scripts/launch_shell.gd','scripts/hero_ui_theme.gd','scripts/scene_transition.gd','scripts/loading_presentation.gd','tools/ui-campaign/board.gd','tools/ui-campaign/observer.gd','tools/ui-campaign/run.py','tests/ui_campaign_flow_cases.gd','.godot/global_script_class_cache.cfg']
files += [str(f.relative_to(B)) for f in (B/'assets/fonts').glob('*') if f.is_file()]
files += [str(f.relative_to(B)) for f in (B/'.godot/imported').glob('*.ttf-*') if f.is_file()]
for rel in files:
 dst=P/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if rel in ['scripts/loading_presentation.gd','tools/ui-campaign/board.gd','tools/ui-campaign/observer.gd']:continue
 os.link(B/rel,dst)
assert sha(C/'scripts/loading_presentation.gd')=='c3c785b8fe73876510109601b0a4f80c3567ced2ba6fb12ed38b54d1182088d7'
shutil.copy2(C/'scripts/loading_presentation.gd',P/'scripts/loading_presentation.gd')
assert sha(Q/'board.gd')=='7e3d918779bece536896af50344b52716a037107f7dd2fee780a66c416c38c61'
shutil.copy2(Q/'board.gd',P/'tools/ui-campaign/board.gd');shutil.copy2(Q/'plan.json',PRE/'plan.json')
old=(B/'tools/ui-campaign/observer.gd').read_text();needle='\treturn result\n\nfunc _walk';assert old.count(needle)==1
new=old.replace(needle,'\tif current_scene and current_scene.has_method("fixture_report") and is_instance_valid(current_scene.loader):\n\t\tresult.fixture_review = current_scene.fixture_report()\n\treturn result\n\nfunc _walk')
(P/'tools/ui-campaign/observer.gd').write_text(new);(PRE/'observer.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='first-batch-observer',tofile='fixture-observer')))
oldrunner=Path('/workspace/scratch/yuga-impeccable-ui-r1/preparation/run_fixture_r2.py').read_text();needle="window/size/viewport_width='+str(a.width)+'\\nwindow/size/viewport_height='+str(a.height)+'\\n[rendering]"
replacement="window/size/viewport_width=1280\\nwindow/size/viewport_height=720\\nwindow/stretch/mode=\"canvas_items\"\\n[rendering]"
assert oldrunner.count(needle)==1
newrunner=oldrunner.replace(needle,replacement);(PRE/'run_fixture.py').write_text(newrunner);(PRE/'fixture-canvas.patch').write_text(''.join(difflib.unified_diff(oldrunner.splitlines(True),newrunner.splitlines(True),fromfile='fixed-tiny-runner',tofile='matching-canvas-runner')))
for f in P.rglob('*'):
 if f.is_file() and f.stat().st_nlink==1:f.chmod(0o444)
pins={str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file()};(PRE/'source.json').write_text(json.dumps({'files':pins,'scope':'Tiny explicit visual sample fixture. Exact runtime view/controller; source canvas1280x720, window960x540 and scale1/2. No world or 3D shader seeds.'},indent=2)+'\n')
shutil.copy2(__file__,PRE/'stage_confirmation.py');print(json.dumps({'source_files':len(pins),'observer':sha(P/'tools/ui-campaign/observer.gd'),'runner':sha(PRE/'run_fixture.py'),'free':shutil.disk_usage(W).free}))
