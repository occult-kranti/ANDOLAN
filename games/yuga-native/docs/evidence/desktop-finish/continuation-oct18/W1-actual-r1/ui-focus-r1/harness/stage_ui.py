from pathlib import Path
import hashlib,json,os,shutil
W=Path(__file__).parent.parent;H=W/'harness';R=Path('/workspace/ANDOLAN/games/yuga-native');P=W/'world-candidate-project';B=Path('/workspace/scratch/yuga-continuation-W2-r1/audit-project/scripts');E=R/'docs/evidence/desktop-finish/continuation-oct18/W2-screens-r1';SOURCE=Path('/workspace/scratch/yuga-impeccable-loading-confirm-r1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(E/'board.gd')=='f72ebc91ab8cfee8a64df193607c1c6618e33aaaa79f91dccfa05416b2aaf2e6';assert sha(E/'native-plan.json')=='a7795da3fe20c702461ef19fb7bcc7f02c5525489aaa56551e3760621ab55902'
runner=(SOURCE/'preparation/run_fixture.py').read_text();needle="files=['scripts/launch_shell.gd'";runner=runner.replace(needle,"files=['scripts/controls_overlay.gd','scripts/rama_hero_panel.gd','scripts/input_bindings.gd','scripts/rama_ability_glyph.gd','scripts/ui_scroll_focus.gd','assets/design/rama-ability-kit.json','scripts/launch_shell.gd'")
(H/'run_ui_fixture.py').write_text(runner)
observer=(SOURCE/'source/tools/ui-campaign/observer.gd').read_text().replace(' and is_instance_valid(current_scene.loader):',':')
(H/'ui_observer.gd').write_text(observer)
records={}
for role in ['baseline','candidate']:
 out=W/('ui-'+role+'-source');assert not out.exists();out.mkdir()
 names=['scripts/launch_shell.gd','scripts/hero_ui_theme.gd','scripts/scene_transition.gd','scripts/loading_presentation.gd','tools/ui-campaign/run.py','tests/ui_campaign_flow_cases.gd','.godot/global_script_class_cache.cfg','assets/design/rama-ability-kit.json','scripts/controls_overlay.gd','scripts/rama_hero_panel.gd','scripts/input_bindings.gd','scripts/rama_ability_glyph.gd','scripts/ui_scroll_focus.gd']
 names += [str(p.relative_to(P)) for p in (P/'assets/fonts').glob('*') if p.is_file()]
 names += [str(p.relative_to(P)) for p in (P/'.godot/imported').glob('*.ttf-*') if p.is_file()]
 for n in names:
  origin=P/n
  if n=='tests/ui_campaign_flow_cases.gd':origin=SOURCE/'source'/n
  if n.startswith('scripts/') and (R/n).is_file():origin=R/n
  if role=='baseline' and n in ['scripts/controls_overlay.gd','scripts/rama_hero_panel.gd']:origin=B/Path(n).name
  target=out/n;target.parent.mkdir(parents=True,exist_ok=True)
  if n.startswith(('assets/fonts/','.godot/imported/')):
   assert not origin.stat().st_mode & 0o222
   os.link(origin,target)
  else:shutil.copyfile(origin,target)
 for n,origin in [('tools/ui-campaign/board.gd',E/'board.gd'),('tools/ui-campaign/observer.gd',H/'ui_observer.gd')]:
  target=out/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(origin,target)
 plan=json.loads((E/'native-plan.json').read_text())
 keep={'01-controls-capture-100','02-controls-capture-200','04-guide-selection-100','05-guide-selection-200'} if role=='baseline' else {'02-controls-capture-200','05-guide-selection-200'}
 for step in plan:
  if step.get('capture') not in keep:step.pop('capture',None)
 (H/('ui-'+role+'-plan.json')).write_text(json.dumps(plan,indent=2)+'\n')
 record={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()};records[role]={'source':str(out),'files':record,'plan_sha256':sha(H/('ui-'+role+'-plan.json'))}
(W/'ui-source-freeze.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({r:{'files':len(v['files']),'source':v['source']} for r,v in records.items()}))
