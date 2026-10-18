from pathlib import Path
import os,json,importlib.util,shutil,hashlib
root=Path('/workspace/ANDOLAN/games/yuga-native');base=Path('/tmp/yuga-final-s2-render-project-r1');dst=Path('/tmp/yuga-s3-lead-paving-project-r1');out=Path('/tmp/yuga-s3-lead-paving-r1');assert not dst.exists()
spec=importlib.util.spec_from_file_location('snapshot',root/'tools/graphics-six/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=m.verify(base);assert m.digest(base/m.MARKER)=='dec4acea9c7b300d6673e295517319d206d61e37bf990d1d10a4dc8707e55046'
name='scripts/environment_surface_finish.gd';before=(base/name).read_text();after=before
pairs=[('Vector3(0.68,0.73,0.73)','Vector3(0.64,0.665,0.64)'),('Vector3(0.75,0.75,0.67)','Vector3(0.65,0.66,0.625)'),('Vector3(0.64,0.72,0.72)','Vector3(0.63,0.655,0.64)'),('Vector3(0.78,0.74,0.63)','Vector3(0.65,0.65,0.615)')]
for a,b in pairs:
 assert after.count(a)==1,a
 after=after.replace(a,b)
for n in old['files']:
 target=dst/n;target.parent.mkdir(parents=True,exist_ok=True)
 if n==name:target.write_text(after)
 else:os.link(base/n,target)
new=m.inventory(dst);assert [n for n in new if new[n]!=old['files'].get(n)]==[name]
seal=dict(old);seal.update(project=str(dst),round='G2-S3-paving-palette-candidate-r1',files=new,validated_imports=m.imports(dst),previous_receipt_sha256=m.digest(base/m.MARKER),changed_paths=[name],diagnostic_derivative={'palette_only':pairs,'scope':'Staged four courtyard stone tint vectors only. All source maps, shader, geometry, rig, game clocks, light, camera, exposure and controls unchanged. Warm copied cache, not cold qualification.'})
(dst/m.MARKER).write_text(json.dumps(seal,indent=2)+'\n');m.verify(dst);m.verify(base)
shutil.copyfile(base/name,out/'environment_surface_finish.before.gd');shutil.copyfile(dst/name,out/'environment_surface_finish.candidate.gd')
receipt={'parent_snapshot_sha256':m.digest(base/m.MARKER),'candidate_snapshot_sha256':m.digest(dst/m.MARKER),'changed_source':name,'before':old['files'][name],'after':new[name],'pairs':pairs,'files':len(new),'scope':seal['diagnostic_derivative']['scope']}
(out/'derivative.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
