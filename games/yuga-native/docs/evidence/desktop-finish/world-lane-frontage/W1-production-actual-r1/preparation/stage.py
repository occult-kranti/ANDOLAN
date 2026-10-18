from pathlib import Path
import hashlib, importlib.util, json, os, shutil
W=Path(__file__).parent;ROOT=Path('/workspace/ANDOLAN/games/yuga-native');P=Path('/workspace/scratch/yuga-frontage-review-r2/candidate-project');H=Path('/workspace/scratch/yuga-frontage-production-helper-r1')
assert shutil.disk_usage(W).free>600*1024**2
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(H/'receipt.json')=='22c7ed6ae0c21d211a51b508ccd20801bbcbb96c04722cd7e4d068cbc216b1e1'
pins=json.loads((H/'receipt.json').read_text())['runtime_sources']
spec=importlib.util.spec_from_file_location('snapshot',W/'harness/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=m.verify(P);assert h(P/m.MARKER)=='c8fa3783bdc9a86b347b9f2d923c4587db82677d6b333cf4a400df1a23245762'
overlays={n:ROOT/n for n in pins};overlays['tools/graphics-six/capture_scene_anchors.gd']=H/'capture_frontage.gd';pins=dict(pins);pins['tools/graphics-six/capture_scene_anchors.gd']='f35ef9ef674a0f9cce725245898da07ec14fee462361d1459eff7bf5ee7f742f'
for n,p in overlays.items():assert h(p)==pins[n]
runtime_deltas=[]
for n,item in old['files'].items():
 if n.startswith(('scripts/','scenes/','shaders/','assets/')) or n=='project.godot':
  if not (ROOT/n).is_file() or h(ROOT/n)!=item['sha256']:runtime_deltas.append(n)
assert runtime_deltas==['scripts/confluence_world.gd']
new=W/'project';assert not new.exists();new.mkdir();expected=dict(old['files']);origins={};store=Path(old['store'])/'sources'
for n,p in overlays.items():
 item=m.metadata(p);blob=store/item['sha256']
 if not blob.exists():shutil.copyfile(p,blob);blob.chmod(0o444)
 assert m.metadata(blob)==item;expected[n]=item;origins[n]=blob
for n,item in expected.items():
 dest=new/n;dest.parent.mkdir(parents=True,exist_ok=True);origin=origins.get(n,P/n)
 if n in m.AUX_FILES or n=='tools/visual-rounds/frontage-review.json':shutil.copyfile(origin,dest)
 else:os.link(origin,dest)
record=dict(old);record.update(project=str(new),round='frontage-production-observer-r1',files=expected,previous_marker_sha256=h(P/m.MARKER),source_bytes=sum(v['bytes'] for n,v in expected.items() if not n.startswith('.godot/')),declared_production_overlays={n:expected[n] for n in overlays});record['common_harness_overlay']=dict(old['common_harness_overlay']);record['common_harness_overlay']['tools/graphics-six/capture_scene_anchors.gd']=expected['tools/graphics-six/capture_scene_anchors.gd']
(new/m.MARKER).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');m.verify(new);m.verify(P)
receipt={'passed':True,'parent':str(P),'parent_marker_sha256':h(P/m.MARKER),'project':str(new),'marker_sha256':h(new/m.MARKER),'files':len(expected),'imports':len(record['validated_imports']),'runtime_overlay_pins':{n:pins[n] for n in pins if n!='tools/graphics-six/capture_scene_anchors.gd'},'only_changes':{n:{'before':old['files'].get(n),'after':expected[n]} for n in overlays},'all_other_existing_runtime_files_equal_current_canonical':True,'no_import_or_full_clone':True,'base_store_unchanged':True,'workspace_free_after':shutil.disk_usage(W).free}
(W/'staging.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
