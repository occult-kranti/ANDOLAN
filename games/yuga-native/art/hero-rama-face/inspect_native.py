"""Inspect the actual anatomical quad surface around the eye openings."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

body=bpy.data.objects['RamaAnatomy'];mesh=body.data
region={v.index for v in mesh.vertices if 1.69<v.co.z<1.765 and abs(v.co.x)<.083 and v.co.y<-.105}
data={'vertices':[{'index':v.index,'co':list(v.co),'normal':list(v.normal),'weights':[(body.vertex_groups[g.group].name,g.weight)for g in v.groups]}for v in mesh.vertices if v.index in region],
      'polygons':[{'index':p.index,'vertices':list(p.vertices)}for p in mesh.polygons if all(i in region for i in p.vertices)],
      'edges':[list(e.vertices)for e in mesh.edges if all(i in region for i in e.vertices)]}
tree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
c=bpy.data.objects['YugaHeroRig'].data.bones['eye.L'].head_local.copy();c.y-=.003
samples=[]
for zstep in range(-10,11):
 for xstep in range(-16,17):
  x=c.x+xstep*.001;z=c.z+zstep*.001
  co,n,ix,dist=tree.ray_cast(Vector((x,-.7,z)),Vector((0,1,0)),1.)
  samples.append({'dx':xstep*.001,'dz':zstep*.001,'y':float(co.y)if co is not None else None,'face':ix})
data['raySamples']=samples
Path('/workspace/scratch/rama-native-orbit-topology.json').write_text(json.dumps(data))
print('NATIVE_ORBIT',len(data['vertices']),len(data['polygons']))
