"""Only root-authorized remaining-camera lens repairs. No render/export."""
from pathlib import Path
import json,sys
import bpy
BASE=Path('/workspace/scratch/yuga-hair-clay-r1/framing-r3');sys.path.insert(0,str(BASE))
from scene_semantics import snapshot,differences,sha
from projection_contract import points,census,fits,bounds
source=Path(bpy.data.filepath);assert sha(source)=='538180be0f2eee096535c4414909c8d4543622b53c334fc046e7ac8f3b779cbb'
scene=bpy.context.scene;before=snapshot();hair,context=points(scene)
initial=census(scene,hair,context)
(BASE/'projection-before.json').write_text(json.dumps(initial,indent=2)+'\n')
rear=bpy.data.objects['VIEW_rear'];assert rear.data.lens==55;rear.data.lens=44
cast=bpy.data.objects['VIEW_cast-angle-authoring'];cast_bounds=bounds(scene,cast,hair+context)
calculation=dict(original_cast_lens_mm=cast.data.lens,before_bounds=cast_bounds)
if not fits(cast_bounds,.02):
    low,high=cast_bounds;ratios=[1.]
    for i in [0,1]:
        if low[i]<.021:ratios.append((.5-.021)/(.5-low[i]))
        if high[i]>.979:ratios.append((.979-.5)/(high[i]-.5))
    ratio=min(ratios);calculation.update(computed_scale=ratio,safety_target_padding=.021,maximum_reduction=.25)
    (BASE/'cast-framing-calculation.json').write_text(json.dumps(calculation,indent=2)+'\n')
    assert .75<=ratio<=1.,('Required fourth-camera lens reduction exceeds root limit',calculation)
    cast.data.lens*=ratio
else:
    calculation.update(computed_scale=1.,note='Fourth camera already meets .02 padding; no change')
(BASE/'cast-framing-calculation.json').write_text(json.dumps(calculation,indent=2)+'\n')
final=census(scene,hair,context)
(BASE/'projection-after.json').write_text(json.dumps(final,indent=2)+'\n')
for case,row in final.items():
    for label,b in row.items():assert fits(b),('Camera remains outside padding',case,label,b)
after=snapshot();delta=differences(before,after)
allowed=['.cameras.rear.lens','.cameras.cast-angle-authoring.lens']
assert delta and all(row[0]in allowed for row in delta),delta
assert any(row[0]=='.cameras.rear.lens'and row[1]==55 and row[2]==44 for row in delta)
(BASE/'semantic-before.json').write_text(json.dumps(before,sort_keys=True,separators=(',',':'))+'\n')
(BASE/'semantic-after.json').write_text(json.dumps(after,sort_keys=True,separators=(',',':'))+'\n')
dest=BASE/'whole-hair-clay-framing-r3.blend';assert not dest.exists();bpy.ops.wm.save_as_mainfile(filepath=str(dest))
(BASE/'lens-only-proof.json').write_text(json.dumps(dict(source_sha256=sha(source),successor_sha256=sha(dest),differences=delta,geometry_material_light_object_transforms_unchanged=True,other_cameras_unchanged=True,rendered=False,exported=False),indent=2)+'\n')
print('CAMERA_ONLY_SUCCESSOR',delta,sha(dest),flush=True)
