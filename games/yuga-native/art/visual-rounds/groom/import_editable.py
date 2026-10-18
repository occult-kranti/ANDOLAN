"""Capture-owner Blender slot only: inspect native groom and save/reopen R3.

No export occurs. Original candidate bytes remain the runtime source. Native
mesh geometry is editable; hidden guide curves and exact guide JSON retain the
procedural authoring intent without claiming a historical modeling stack.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def summary():
 return {'bones':[len(o.data.bones)for o in bpy.data.objects if o.type=='ARMATURE'],
  'meshes':{o.name:{'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'morphs':[k.name for k in o.data.shape_keys.key_blocks]if o.data.shape_keys else []}for o in bpy.data.objects if o.type=='MESH'},
  'actions':[a.name for a in bpy.data.actions],
  'packed_images':[i.name for i in bpy.data.images if i.type=='IMAGE' and i.packed_file]}
p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--native-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
if a.output.exists():raise ValueError('Fresh editable path required')
m=json.loads(a.manifest.read_text());candidate=Path(m['levels']['near']['output'])
assert sha(candidate)==m['levels']['near']['output_sha256']
bpy.ops.wm.open_mainfile(filepath=str(a.native_source.resolve()))
original={o.name:{'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)}for o in bpy.data.objects if o.type=='MESH' and any(s in o.name.lower() for s in ['hair','lock','tendril','filament','eyebrow'])}
report={'candidate_sha256':sha(candidate),'native_source_sha256':sha(a.native_source),'original_native_groom_objects':original,'importer_sha256':sha(__file__),'blender':bpy.app.version_string}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(candidate.resolve()))
before=summary();assert before['bones']==[164] and len(before['actions'])==9 and len(before['packed_images'])==17
assert before['meshes']['RamaFace']['morphs']==['Basis','rama_blink_left','rama_blink_right','rama_blink_half_left','rama_blink_half_right']
text=bpy.data.texts.new('R3 groom exact authoring manifest.json');text.write(a.manifest.read_text())
collection=bpy.data.collections.new('R3 groom control guides - hidden in render');bpy.context.scene.collection.children.link(collection)
for guide in m['guides']:
 curve=bpy.data.curves.new(guide['name'],'CURVE');curve.dimensions='3D';spline=curve.splines.new('POLY');spline.points.add(len(guide['points'])-1)
 for point,(x,y,z)in zip(spline.points,guide['points']):
  if 'clearance_warp' in guide:
   warp=guide['clearance_warp'];t=max(0.,min(1.,(y-warp['start_y'])/(warp['full_y']-warp['start_y'])));weight=t*t*(3-2*t)
   y+=warp['lift_m']*weight;z-=warp['posterior_m']*weight
  point.co=(x,-z,y,1)
 obj=bpy.data.objects.new(guide['name'],curve);collection.objects.link(obj);obj.hide_render=True;obj['authoring_note']='Control polygon after the declared clearance warp; exact original cubic controls and warp recipe remain in manifest text, not a rendered fiber';obj['width_m']=guide['width'];obj['depth_m']=guide['depth']
for o in bpy.data.objects:
 if o.type=='ARMATURE':o.animation_data.action=None;o.data.pose_position='REST'
a.output.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(a.output.resolve()),compress=True);bpy.ops.wm.open_mainfile(filepath=str(a.output.resolve()))
after=summary();assert before==after
report.update(candidate_import=before,reopened=after,guide_curves=len(m['guides']),editable_sha256=sha(a.output),scope='Saved/reopened imported editable with hidden source control polygons. No runtime re-export or automatic Blender-to-generator guide roundtrip claim.')
a.output.with_suffix('.inspection.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['candidate_sha256','editable_sha256','guide_curves','blender']}))
