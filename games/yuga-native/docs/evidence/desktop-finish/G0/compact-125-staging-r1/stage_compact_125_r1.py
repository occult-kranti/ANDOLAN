import importlib.util, json
from pathlib import Path
root=Path('/workspace/ANDOLAN/games/yuga-native')
work=Path('/tmp/yuga-desktop-recovery-r1')
spec=importlib.util.spec_from_file_location('snapshot',root/'tools/graphics-six/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
base=work/'current-project';old=work/'compact-project-r1';child=work/'compact-125-project-r1'
expected_base='6349218e2507bbf2ed7fd7d82543d464deb7c261defed2930f87995742513a19'
expected_old='a02bc44bcb09cd9b80c0afd4d5a18d42a72664e23aa4961875cb572bfb39e2b5'
assert m.digest(base/m.MARKER)==expected_base
assert m.digest(old/m.MARKER)==expected_old
base_record=m.verify(base);m.verify(old)
overlays={'scripts/confluence_world.gd':'b03c682669af55ca26b1dc44676850c40106ce794f2f20eb407c6e64e841f0f1','tools/graphics-six/capture_compact_screens.gd':'9a0fb75c6fab298f0babb19c1c7d6aa7e5234b94b9472971086e34a54391c51e'}
for name,want in overlays.items():assert m.digest(root/name)==want,(name,'source pin mismatch')
assert not child.exists()
r=m.refresh(base,child,work/'store','G2-desktop-compact-125-r1',work/'compact-125-initial-source.json')
for name in overlays:m.atomic_copy(root/name,child/name)
actual=m.inventory(child)
delta=sorted(k for k in actual.keys()|base_record['files'].keys() if actual.get(k)!=base_record['files'].get(k))
assert delta==sorted(overlays),delta
r.update(files=actual,canonical_files=base_record['files'],parent_snapshot_sha256=expected_base,parent_snapshot=str(base),changed_paths=delta,declared_runtime_overlay={'scripts/confluence_world.gd':m.metadata(child/'scripts/confluence_world.gd')},harness_overlays={'tools/graphics-six/capture_compact_screens.gd':m.metadata(child/'tools/graphics-six/capture_compact_screens.gd')},source_bytes=sum(v['bytes'] for k,v in actual.items() if not k.startswith('.godot/')),scope='Declared ten-shot child: only world b03 runtime and helper9a0f differ from base6349218; original eight-shot engine fixturea02 unchanged. Never import into this project or alter shared read-only imported blobs.')
receipt=work/'compact-125-source.json';receipt.write_text(json.dumps(r,indent=2)+'\n');m.atomic_copy(receipt,child/m.MARKER)
m.verify(child);m.verify(base);m.verify(old)
assert m.digest(base/m.MARKER)==expected_base and m.digest(old/m.MARKER)==expected_old
for name,want in overlays.items():assert m.digest(root/name)==want
print(json.dumps({'passed':True,'project':str(child),'marker_sha256':m.digest(child/m.MARKER),'delta':delta,'files':len(actual),'imports':len(r['validated_imports']),'outer_runner_sha256':m.digest(root/'tools/graphics-six/run_focus.py')},indent=2))
