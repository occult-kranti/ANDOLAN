"""Reopened source proof against R7. Run in Blender after source freeze."""
from pathlib import Path
import bpy, sys, json, hashlib
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
args=sys.argv[sys.argv.index('--')+1:]
path=Path(args[0]);out=Path(args[1])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def curves():
 return {a.name:hashlib.sha256(json.dumps([(f.data_path,f.array_index,[(list(k.co),list(k.handle_left),list(k.handle_right),k.interpolation) for k in f.keyframe_points]) for f in a.fcurves],sort_keys=True).encode()).hexdigest() for a in bpy.data.actions}
def capture():
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 result={'rig':{b.name:{'parent':b.parent.name if b.parent else None,'rest':[list(r) for r in b.matrix_local]} for b in rig.data.bones},'curves':curves(),'meshes':{}}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  result['meshes'][o.name]={'positions':np.array([list(v.co) for v in o.data.vertices]),'topology':hashlib.sha256(json.dumps([list(p.vertices) for p in o.data.polygons]).encode()).hexdigest(),'uv':hashlib.sha256(json.dumps([list(x.uv) for x in o.data.uv_layers.active.data]).encode()).hexdigest(),'skin':hashlib.sha256(json.dumps([[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]).encode()).hexdigest(),'materials':[m.name for m in o.data.materials]}
 return result
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'games/yuga-native/art/hero-rama/rama-hero.blend'));old=capture()
bpy.ops.wm.open_mainfile(filepath=str(path));new=capture()
assert old['rig']==new['rig'] and len(new['rig'])==164
assert old['curves']==new['curves']
checks=['Exact 164 bone names, parents and rest matrices preserved','Every original action F-curve/handle/interpolation is unchanged']
changed={'RamaAnatomy','Layered ivory dhoti','Folded cobalt cross sash'};proof=[]
for name,before in old['meshes'].items():
 if name=='Unified swept hair sculpture':
  assert name not in new['meshes'];continue
 after=new['meshes'][name]
 for field in ('topology','uv','skin','materials'):assert before[field]==after[field],(name,field)
 a=before['positions'];b=after['positions'];assert a.shape==b.shape
 delta=b-a;maximum=float(np.max(np.linalg.norm(delta,axis=1)))
 if name not in changed:assert np.array_equal(a,b),(name,maximum)
 elif name=='RamaAnatomy':
  region=(a[:,2]>1.61)&(a[:,2]<1.76)&(a[:,1]<-.07)&~((np.abs(a[:,0])>.016)&(a[:,2]>1.712))
  assert np.array_equal(a[~region],b[~region])
  assert maximum<=.003
 else:
  assert np.array_equal(a[:,[0,2]],b[:,[0,2]])
  assert np.max(delta[:,1])<=0 and np.min(delta[:,1])>=-.015
 proof.append({'mesh':name,'maximumRestDisplacementM':maximum,'topologyUvSkinAndMaterialsPreserved':True})
checks.extend(['Every original non-hair topology, UV, skin record and material assignment is identical','Only bounded face sculpt and two fabric surfaces change rest coordinates','Eyes, eyebrows, lid rims, hands, feet, bow, string and ornaments retain exact rest geometry'])
locks=[o for o in bpy.data.objects if o.type=='MESH' and o.get('yuga_semantic')=='hair_clump'];assert len(locks)==68
outward=0;total=0
for o in locks:
 rows=len(o.data.vertices)//12
 centers=[sum((o.data.vertices[i*12+j].co for j in range(12)),__import__('mathutils').Vector())/12 for i in range(rows)]
 for poly in list(o.data.polygons)[:-2]:
  row=poly.vertices[0]//12
  if row>=rows-1:continue
  center=(centers[row]+centers[row+1])/2
  radial=poly.center-center
  if radial.length<1e-8:continue
  total+=1;outward+=int(poly.normal.dot(radial)>0)
assert outward/total>.98,(outward,total)
checks.append('At least 98% of nondegenerate clump side faces have outward winding')
report={'schema':1,'editableSha256':sha(path),'baselineEditableSha256':sha(ROOT/'games/yuga-native/art/hero-rama/rama-hero.blend'),'checks':checks,'originalMeshProof':proof,'newHairLocks':len(locks),'outwardHairSideFaces':outward,'testedHairSideFaces':total,'limitations':['This exact source proof does not accept cloth/skin intersections in all poses, visual likeness or physical GPU performance.']}
out.write_text(json.dumps(report,indent=2)+'\n');print('QUALITY_EDITABLE_PASS',len(checks),'checks')
