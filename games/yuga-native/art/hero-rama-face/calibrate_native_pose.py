"""Measure actual seated-globe coverage while tuning CC0 pose-unit gains."""
from pathlib import Path
import json,math,sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_native_face as native

body=bpy.data.objects['RamaAnatomy'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.data.pose_position='REST';rig.animation_data.action=None
for bone in rig.pose.bones:bone.matrix_basis.identity()
data=native.capture_body(body);c=rig.data.bones['eye.L'].head_local.copy();c.y-=.003
selected=[]
for index,face in enumerate(data['faces']):
 p=sum((data['vertices'][i]for i in face['vertices']),Vector())/len(face['vertices'])
 if p.y<-.106 and ((p.x-c.x)/.033)**2+((p.z-c.z)/.031)**2<1:selected.append(index)
unselected=set(range(len(data['faces'])))-set(selected)
face,used,remap=native.partition_mesh('RamaFace calibration',data,selected,rig)
boundary=set(used)&{i for f in unselected for i in data['faces'][f]['vertices']};held=set(boundary)
for f in selected:
 ids=set(data['faces'][f]['vertices'])
 if ids&boundary:held|=ids
rest=native.bake_native_pose(face,rig,[],0.)
source=native.source_pose_units()['L'];polys=[list(p.vertices)for p in face.data.polygons];results=[]
for upper in [.45,.50,.55,.60,.65,.70,.75,.80]:
 for lower in [.0,.1,.2,.3,.4,.5]:
  units=[(bone,angle*(upper if '03.'in bone else lower))for bone,angle in source]
  baked=native.bake_native_pose(face,rig,units,1.)
  points=[data['vertices'][old]+(baked[local]-rest[local])if old not in held else data['vertices'][old]for local,old in enumerate(used)]
  tree=BVHTree.FromPolygons(points,polys)
  uncovered=[];margins=[]
  for ix in range(9):
   dx=-.01+ix*.0025
   for iz in range(7):
    dz=-.003+iz*(.007/6)
    hit,n,ind,dist=tree.ray_cast(Vector((c.x+dx,-.7,c.z+dz)),Vector((0,1,0)),1.)
    globe=c.y-math.sqrt(max(0,.0153**2-dx*dx-dz*dz))
    margin=globe-hit.y if hit is not None else -1
    if margin<-.0002:uncovered.append([dx,dz])
    margins.append(margin)
  results.append({'upper_gain':upper,'lower_gain':lower,'uncovered':len(uncovered),'minimum_margin_m':min(margins),'max_displacement_m':max((points[i]-data['vertices'][old]).length for i,old in enumerate(used))})
Path('/workspace/scratch/rama-native-pose-calibration.json').write_text(json.dumps({'source_units':source,'samples_per_candidate':63,'results':results},indent=2)+'\n')
print('NATIVE_POSE_COVERAGE '+json.dumps([r for r in results if r['uncovered']==0]),flush=True)
