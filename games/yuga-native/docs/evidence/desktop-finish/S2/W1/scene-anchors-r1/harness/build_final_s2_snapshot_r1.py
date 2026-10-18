from pathlib import Path
import os,json,hashlib,importlib.util,shutil
root=Path('/workspace/ANDOLAN/games/yuga-native');base=Path('/tmp/yuga-graphics-six-project');dst=Path('/tmp/yuga-final-s2-render-project-r1');overlay=Path('/tmp/yuga-final-s2-overlay-freeze-r1');assert not dst.exists()
spec=importlib.util.spec_from_file_location('snapshot',root/'tools/graphics-six/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=m.verify(base);assert m.digest(base/m.MARKER)=='5d94a7b64b2387f9f8899e82b6a499fb28a93a3ac0a4ace921496af5b589a8ca'
receipt=json.loads((overlay/'receipt.json').read_text());assert m.digest(overlay/'receipt.json')=='13c04ed273bdb553332c0501634d7e463ecc0150fb945b5dfc2b24abd4766f5b'
changes={}
for name,meta in receipt['files'].items():
 p=overlay/name;assert m.digest(p)==meta['sha256'];assert p.stat().st_size==meta['size'];changes[name]=p
for n in ['capture_scene_anchors.gd','run_focus.py']:
 changes['tools/graphics-six/'+n]=root/'tools/graphics-six'/n
for suffix in ['ctex','md5']:
 n='.godot/imported/s1-hammered-gold-roughness.png-c93c92f35fe086748d0140298caef508.'+suffix
 changes[n]=Path('/tmp/yuga-s1-gold-candidate-project')/n
for name in old['files']:
 target=dst/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name not in changes:os.link(base/name,target)
for name,p in changes.items():
 target=dst/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name.startswith('.godot/imported/'):
  meta=m.metadata(p);blob=Path(old['store'])/'imports'/meta['sha256'];m.retain(p,blob,meta);os.link(blob,target)
 else:shutil.copyfile(p,target)
new=m.inventory(dst);imports=m.imports(dst)
shaders=[n for n in new if n.endswith('masonry.gdshader')];assert len(shaders)==1;assert new[shaders[0]]['sha256']=='6e532916f3313c197408710a6a7fa3f786ebf09a770c67b60ed8fd4b1598509e'
assert new['scripts/environment_surface_finish.gd']['sha256']=='0eea1b70b677705d39e7eb4dfc37f92e46429f2b9ebea5b3f45f0bf91a166eaf'
seal=dict(old);seal.update(project=str(dst),round='G2-final-S2-seeded-render-r1',files=new,validated_imports=imports,previous_receipt_sha256=m.digest(base/m.MARKER),changed_paths=sorted(n for n in new if new[n]!=old['files'].get(n)),diagnostic_derivative={'runtime_overlay_receipt_sha256':m.digest(overlay/'receipt.json'),'runtime_overlay_paths':list(receipt['files']),'harness_overlays':['tools/graphics-six/capture_scene_anchors.gd','tools/graphics-six/run_focus.py'],'compiled_gold_imports_from':'/tmp/yuga-s1-gold-candidate-project','shader_overrides':[],'scope':'Exact final S2 overlay on sealed G2. Full original G2 masonry, no diagnostic environment shader. Cache seed is external launch variable.'})
(dst/m.MARKER).write_text(json.dumps(seal,indent=2)+'\n');m.verify(dst);m.verify(base)
result={'project':str(dst),'snapshot_sha256':m.digest(dst/m.MARKER),'base_snapshot_sha256':m.digest(base/m.MARKER),'overlay_receipt_sha256':m.digest(overlay/'receipt.json'),'files':len(new),'validated_imports':len(imports),'changes':[{'path':n,'before':old['files'].get(n),'after':new[n]} for n in seal['changed_paths']],'original_masonry':shaders[0],'original_masonry_sha256':new[shaders[0]]['sha256']}
Path('/tmp/yuga-g0-source-research-r1/final-s2-snapshot-r1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='changes'},indent=2))
