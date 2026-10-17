"""Blender proof of reopened editable rig/curves and sampled skinned bounds."""
import bpy,json,sys,hashlib,math
from pathlib import Path
import numpy as np
ARGS=sys.argv[sys.argv.index('--')+1:];root=Path(__file__).resolve().parents[4]
def rig_signature(r):return {b.name:dict(parent=b.parent.name if b.parent else None,matrix=[list(x) for x in b.matrix_local]) for b in r.data.bones}
def curves():
    return {a.name.removesuffix('_YugaHeroRig'):hashlib.sha256(json.dumps([(f.data_path,f.array_index,[(list(k.co),list(k.handle_left),list(k.handle_right),k.interpolation) for k in f.keyframe_points]) for f in a.fcurves],sort_keys=True).encode()).hexdigest() for a in bpy.data.actions}
bpy.ops.wm.open_mainfile(filepath=str(root/'games/yuga-native/art/production/reconstruction-rama.blend'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');expected=rig_signature(r);ac=curves()
p=Path(ARGS[0]);bpy.ops.wm.open_mainfile(filepath=str(p));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');assert rig_signature(r)==expected;assert curves()==ac
meshes=[o for o in bpy.data.objects if o.type=='MESH'];assert len(meshes)>100;assert all(im.packed_file for im in bpy.data.images if im.users>0)
r.data.pose_position='POSE';samples=[]
for action in sorted(bpy.data.actions,key=lambda a:a.name):
    r.animation_data.action=action
    for t in (0,.5,1):
        frame=float(action.frame_range[0]+t*(action.frame_range[1]-action.frame_range[0]));bpy.context.scene.frame_set(int(frame),subframe=frame%1);deps=bpy.context.evaluated_depsgraph_get();points=[]
        for o in meshes:
            evaluated=o.evaluated_get(deps)
            points.extend([list(evaluated.matrix_world@__import__('mathutils').Vector(c)) for c in evaluated.bound_box])
        points=np.array(points);assert np.isfinite(points).all();extent=points.max(0)-points.min(0);assert max(extent)<4
        samples.append(dict(clip=action.name,fraction=t,minimum=points.min(0).tolist(),maximum=points.max(0).tolist()))
result=dict(schema=1,editable=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),exactRestMatricesAndParentsPreserved=True,exactBaselineActionCurvesPreserved=True,meshPieces=len(meshes),bones=len(r.data.bones),baselineActionHashes=ac,samples=samples,limitations=['Evaluated bounds are finite deformation checks, not continuous intersection or artistic acceptance.'])
Path(ARGS[1]).write_text(json.dumps(result,indent=2)+'\n');print('EDITABLE_VERIFIED '+str(len(samples))+' samples')
