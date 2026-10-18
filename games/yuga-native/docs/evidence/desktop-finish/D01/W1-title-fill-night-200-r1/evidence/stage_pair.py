from pathlib import Path
import json,importlib.util
R=Path('/workspace/ANDOLAN/games/yuga-native');E=Path(__file__).resolve().parent;B=E.parent;T=R/'docs/evidence/desktop-finish/G0/workspace-recovery-r1/tools';P=Path('/tmp/yuga-desktop-recovery-r1/current-project')
spec=importlib.util.spec_from_file_location('snapshot',T/'snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
parent=m.verify(P);parent_sha=m.digest(P/m.MARKER);assert parent_sha=='6349218e2507bbf2ed7fd7d82543d464deb7c261defed2930f87995742513a19'
launch=R/'scripts/launch_shell.gd';assert m.digest(launch)=='794266aa6b559e128b0eb1d61b4a019d65dd5f46593fa275a0ed48cda31a858e'
helper=E/'capture_scene_anchors.gd';light=R/'art/lookdev/title-portrait-fill-r1/courtyard.candidate.gd';assert m.digest(light)=='43f512dc6509aba77c1d7055f0fd8404054df07fc700d6261f05a725c4e80a57'
rows={}
for branch in ['baseline','candidate']:
 child=B/(branch+'-project');r=m.refresh(P,child,Path(parent['store']),'G2-title-fill-night-200-'+branch,E/(branch+'-initial.json'))
 overlays={'scripts/launch_shell.gd':launch,'tools/graphics-six/capture_scene_anchors.gd':helper}
 if branch=='candidate':overlays['scripts/courtyard.gd']=light
 for n,p in overlays.items():m.atomic_copy(p,child/n)
 actual=m.inventory(child);delta=sorted(k for k in actual.keys()|parent['files'].keys() if actual.get(k)!=parent['files'].get(k));assert delta==sorted(overlays)
 r.update(files=actual,canonical_files=parent['files'],parent_snapshot_sha256=parent_sha,parent_project=str(P),changed_paths=delta,declared_runtime_overlay={n:{'path':str(p),**actual[n]} for n,p in overlays.items()},source_bytes=sum(v['bytes'] for k,v in actual.items() if not k.startswith('.godot/')),scope='Common latest title794 and same two-view review helper; candidate alone changes three title-light assignments. No import or canonical activation.')
 out=E/(branch+'-source.json');out.write_text(json.dumps(r,indent=2)+'\n');m.atomic_copy(out,child/m.MARKER);m.verify(child)
 rows[branch]={'project':str(child),'snapshot_sha256':m.digest(child/m.MARKER),'changed_paths':delta,'files':len(actual),'imports':len(r['validated_imports'])}
a=m.inventory(B/'baseline-project');b=m.inventory(B/'candidate-project');pair_delta=sorted(k for k in a.keys()|b.keys() if a.get(k)!=b.get(k));assert pair_delta==['scripts/courtyard.gd'];m.verify(P)
result={'passed':True,'parent_snapshot_sha256':parent_sha,'branches':rows,'pair_delta':pair_delta,'helper_sha256':m.digest(helper),'launch_sha256':m.digest(launch),'external_runner_sha256':m.digest(T/'run_focus.py'),'snapshot_api_sha256':m.digest(T/'snapshot.py'),'canonical_activated':False}
(E/'stage-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
