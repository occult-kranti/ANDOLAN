from pathlib import Path
import importlib.util,json
root=Path('/workspace/ANDOLAN/games/yuga-native');work=Path('/tmp/yuga-desktop-recovery-r1');base=work/'compact-current-project-r1';child=work/'compact-current-project-r2'
spec=importlib.util.spec_from_file_location('snapshot',root/'tools/graphics-six/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
pin='310c20002ae016f6927c3dad9d72194a9541f9c6f91c70d59d5f4768bae0da3b';world='6e9d88657b5b3a69b67e0bc93e4f45988faa65d5206d9cabdaea45543e2d19bf';name='scripts/confluence_world.gd'
assert m.digest(base/m.MARKER)==pin;before=m.verify(base);assert m.digest(root/name)==world;assert not child.exists()
record=m.refresh(base,child,work/'store','G4-desktop-current-compact-r2',work/'compact-current-r2-initial-source.json')
m.atomic_copy(root/name,child/name);actual=m.inventory(child);delta=sorted(k for k in actual.keys()|before['files'].keys() if actual.get(k)!=before['files'].get(k));assert delta==[name]
record.update(files=actual,canonical_files=before['files'],parent_snapshot_sha256=pin,parent_snapshot=str(base),changed_paths=delta,declared_runtime_overlay={name:m.metadata(child/name)},source_bytes=sum(v['bytes'] for k,v in actual.items() if not k.startswith('.godot/')),scope='World-only source successor after retained actual150% summary clipping. Same ten-shot helper, assets, compiled imports, camera, clocks and UI/FX source as310c. No import; no edits to earlier child.')
receipt=work/'compact-current-r2-source.json';receipt.write_text(json.dumps(record,indent=2)+'\n');m.atomic_copy(receipt,child/m.MARKER)
m.verify(child);m.verify(base);assert m.digest(base/m.MARKER)==pin and m.digest(root/name)==world
print(json.dumps({'passed':True,'project':str(child),'marker_sha256':m.digest(child/m.MARKER),'changed_paths':delta,'world_sha256':world,'source_files':len(actual),'imports':len(record['validated_imports'])},indent=2))
