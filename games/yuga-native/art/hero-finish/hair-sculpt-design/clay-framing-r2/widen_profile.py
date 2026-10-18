"""Root-authorized lens-only successor; no geometry/render/export."""
from pathlib import Path
import json,sys
import bpy
BASE=Path('/workspace/scratch/yuga-hair-clay-r1/profile-framing-r2')
sys.path.insert(0,str(BASE))
from scene_semantics import snapshot,differences,sha
source=Path(bpy.data.filepath);assert sha(source)=='b2bcea87e5aacf7ec49dae44df915063223bfa4b990ccb448457385008470475'
before=snapshot();camera=bpy.data.objects['VIEW_anatomical-left-profile'];assert camera.data.lens==55
camera.data.lens=55*.98
after=snapshot();delta=differences(before,after)
assert len(delta)==1 and delta[0][0]=='.cameras.anatomical-left-profile.lens',delta
assert abs(camera.data.lens-53.9)<1e-5
(BASE/'semantic-before.json').write_text(json.dumps(before,sort_keys=True,separators=(',',':'))+'\n')
(BASE/'semantic-after.json').write_text(json.dumps(after,sort_keys=True,separators=(',',':'))+'\n')
dest=BASE/'whole-hair-clay-profile-r2.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
proof=dict(scope='Exactly one authoring camera lens change; original scene and every checked geometry/material/light/object/other camera field preserved.',source_path=str(source),source_sha256=sha(source),successor_path=str(dest),successor_sha256=sha(dest),differences=delta,semantic_before_sha256=sha(BASE/'semantic-before.json'),semantic_after_sha256=sha(BASE/'semantic-after.json'),rendered=False,imported=False,exported=False)
(BASE/'lens-only-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print('EXACT_CAMERA_LENS_ONLY',delta,sha(dest),flush=True)
