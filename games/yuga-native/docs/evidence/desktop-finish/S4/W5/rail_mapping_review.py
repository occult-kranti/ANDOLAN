"""Bind retained indexed bone names to the exact imported resource used by the pose tape."""
from pathlib import Path
import gzip,hashlib,json,re,struct
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).parent
sha=lambda data:hashlib.sha256(data).hexdigest()
capture_path=ROOT/'docs/evidence/visual-rounds/round4/role06/originals/capture.json'
capture_raw=capture_path.read_bytes();capture=json.loads(capture_raw)
native_path=ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz';native=json.loads(gzip.decompress(native_path.read_bytes()))
glb_path=ROOT/'assets/heroes/rama-hero.glb';raw=glb_path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);names=[doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]
paths=['res://assets/heroes/rama-hero.glb','res://assets/heroes/rama-hero.glb.import','res://.godot/imported/rama-hero.glb-e90b8f8a0719fdd1ab2b89459efcbdac.scn']
checks=[]
for p in paths:
 values=[capture['source_sha256'][p],capture['source_after_sha256'][p],native['source_before'][p],native['source_after'][p],sha((ROOT/p.removeprefix('res://')).read_bytes())]
 checks.append({'name':'Exact shared imported identity: '+p,'passed':len(set(values))==1,'sha256':values[0]})
checks.append({'name':'All164 recorded imported indices equal glTF skin joint names','passed':len(names)==164 and capture['bone_names']==names,'head_index':names.index('head'),'recorded_head_name':capture['bone_names'][104]})
# Source authority here concerns immutable loaded Skeleton3D indexing only, not motion equivalence.
producer=ROOT/'docs/evidence/visual-rounds/round4/role06/originals/harness/capture_motion.gd'
code=producer.read_text();checks.append({'name':'Retained observer obtains names from actual imported rig in index order','passed':'for index in player.rama_motion.rig.get_bone_count():report.bone_names.append(String(player.rama_motion.rig.get_bone_name(index)))' in code})
kit='res://assets/design/rama-ability-kit.json';checks.append({'name':'Independent sample timing census uses the exact taped ability definitions','passed':native['source_before'][kit]==native['source_after'][kit]==sha((ROOT/kit.removeprefix('res://')).read_bytes())})
result={'schema':1,'passed':all(x['passed'] for x in checks),'checks':checks,'script_sha256':sha(Path(__file__).read_bytes()),'sources':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [capture_path,native_path,glb_path,producer]},'bone_names':names,'scope':'Existing recorded imported-name receipt bound by exact raw GLB/descriptor/SCN bytes to native-r5. No new import/engine execution. Old R4 motion behavior is not transferred; only immutable skeleton index identity is reused. New candidate import and current continuous motion remain separate.'}
(OUT/'rail-mapping-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[x for x in checks if not x['passed']]},indent=2));raise SystemExit(0 if result['passed'] else 1)
