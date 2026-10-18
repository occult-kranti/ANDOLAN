from pathlib import Path
import hashlib,importlib.util,json,os,shutil,difflib
W=Path(__file__).parent;P=Path('/workspace/scratch/yuga-frontage-review-r1');ART=Path('/workspace/ANDOLAN/games/yuga-native/art/world-finish/lane-frontage-r2')
assert shutil.disk_usage(W).free>550*1024**2
oldadapter=P/'harness/snapshot.py';s=oldadapter.read_text();t=s.replace("ROOT_FILES = ('project.godot',", "ROOT_FILES = ('art/world-finish/lane-frontage-r2/candidate.gd',\n              'art/world-finish/lane-frontage-r2/candidate-mesh.json', 'project.godot',")
(W/'harness/snapshot.py').write_text(t);(W/'harness/snapshot-added-inputs.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile=str(oldadapter),tofile='snapshot.py')))
shutil.copyfile(P/'harness/run_focus.py',W/'harness/run_focus.py')
spec=importlib.util.spec_from_file_location('snapshot',W/'harness/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=P/'candidate-r4';base=P/'baseline-r4';prior=m.verify(old);m.verify(base);new=W/'candidate-project';assert not new.exists();new.mkdir()
overlays={'art/world-finish/lane-frontage-r2/candidate.gd':(ART/'candidate.gd','b0b6027d551835ffe5f7f99898ec80511426e51de77c6a6016e888f13de98f79'),'art/world-finish/lane-frontage-r2/candidate-mesh.json':(ART/'candidate-mesh.json','67950a68d7b6384b8b114987a27efff1f113d44f8fb1b7df8632f3e9217406a2'),'tools/graphics-six/capture_scene_anchors.gd':(ART/'capture_frontage.gd','a052a33ed086ec713546021b2a9a3b77ee75ee7fa1e560685b465ec1b92cd43d')}
expected=dict(prior['files']);origins={}
for n,(p,sha) in overlays.items():
 item=m.metadata(p);assert item['sha256']==sha;blob=P/'store/sources'/sha
 if not blob.exists():shutil.copyfile(p,blob);blob.chmod(0o444)
 assert m.metadata(blob)==item;expected[n]=item;origins[n]=blob
for n,item in expected.items():
 dest=new/n;dest.parent.mkdir(parents=True,exist_ok=True);origin=origins.get(n,old/n)
 if n in m.AUX_FILES or n=='tools/visual-rounds/frontage-review.json':shutil.copyfile(origin,dest)
 else:os.link(origin,dest)
record=dict(prior);record.update(project=str(new),round='frontage-r2-candidate-only',files=expected,previous_marker_sha256=m.digest(old/m.MARKER),source_bytes=sum(v['bytes'] for n,v in expected.items() if not n.startswith('.godot/')),declared_frontage_r2_overlays={n:expected[n] for n in overlays});record['common_harness_overlay']=dict(record['common_harness_overlay']);record['common_harness_overlay']['tools/graphics-six/capture_scene_anchors.gd']=expected['tools/graphics-six/capture_scene_anchors.gd']
(new/m.MARKER).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');m.verify(new);m.verify(old);m.verify(base)
receipt={'passed':True,'old_candidate':str(old),'retained_actual_baseline':str(base),'parent_marker':m.digest(old/m.MARKER),'baseline_marker':m.digest(base/m.MARKER),'new_candidate':str(new),'marker':m.digest(new/m.MARKER),'files':len(expected),'imports':len(record['validated_imports']),'only_deltas':{n:{'before':prior['files'].get(n),'after':expected[n]} for n in overlays},'retained_source_unchanged':True,'no_import':True,'new_raw_objects_bytes':sum(expected[n]['bytes'] for n in overlays)};(W/'staging.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
