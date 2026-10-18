"""Source groom replay on 37 already captured actual Godot pose matrices.

This does not claim candidate import. Also independently measures alpha-squared
normal changes, separating unchanged original knot from newly authored geometry.
"""
import argparse,json,sys
from pathlib import Path
import numpy as np
from build_groom import GLB,sha
from validate_groom import surface

def skin(g,primitive,points,poses):
 joints=g.array(primitive['attributes']['JOINTS_0']);weights=g.array(primitive['attributes']['WEIGHTS_0'])
 inverse=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
 matrices=np.array([poses[g.doc['nodes'][i]['name']] for i in g.doc['skins'][0]['joints']])@inverse
 p=np.c_[points,np.ones(len(points))];out=np.zeros((len(points),3))
 for slot in range(4):out+=np.einsum('nij,nj->ni',matrices[joints[:,slot]],p)[:,:3]*weights[:,slot,None]
 return out

def stress(points,tri,masks):
 p=points[tri].astype(float);norm=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);length=np.linalg.norm(norm,axis=1);valid=length>1e-12
 p=p[valid];tri=tri[valid];norm=norm[valid]/length[valid,None];turns=[];minimum_area=float('inf');finite=True
 for axis in range(3):
  for sign in [-1,1]:
   q=p.copy();q[:,:,axis]+=sign*.018*masks[tri]**2
   n=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);area=np.linalg.norm(n,axis=1);minimum_area=min(minimum_area,float(area.min()));finite=finite and np.isfinite(q).all() and np.all(area>1e-12)
   n/=area[:,None];turns.extend(np.degrees(np.arccos(np.clip(np.sum(n*norm,axis=1),-1,1))))
 return {'finite_nondegenerate_deformed_samples':bool(finite),'original_degenerate_triangles':int(np.sum(~valid)),'p95_normal_turn_degrees':float(np.percentile(turns,95)),'maximum_normal_turn_degrees':float(max(turns)),'samples_above_90_degrees':int(np.sum(np.array(turns)>90)),'sample_count':len(turns),'minimum_twice_area_m2':minimum_area}

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 manifest=json.loads(a.manifest.read_text());runtime=json.loads(a.runtime.read_text());item=manifest['levels']['near'];g=GLB(item['output']);v,t,hair=surface(g,2,0);offset=item['retained_vertices'];first=item['retained_triangles'];rest=np.array(runtime['bone_global_rests']['head'])
 body,bt,bp=surface(g,2,11);eye,et,ep=surface(g,2,7);gold,gt,gp=surface(g,2,2)
 ear=(abs(body[:,0])>.075)&(body[:,1]>1.668)&(body[:,1]<1.745)&(body[:,2]>.010)&(body[:,2]<.080)
 band=(gold[:,1]>1.779)&(gold[:,1]<1.805)&(abs(gold[:,0])<.112)&(gold[:,2]<.175)&(gold[:,2]>-.115)
 brow=(v[:,1]>1.740)&(v[:,1]<1.755)&(v[:,2]>.139)&(abs(v[:,0])<.060)
 rows=[]
 for sample in runtime['samples']:
  poses=sample['bone_global_poses'];canon=rest@np.linalg.inv(np.array(poses['head']))
  posed=skin(g,hair,v,poses);canonical=(np.c_[posed,np.ones(len(posed))]@canon.T)[:,:3]
  drift=float(np.max(np.linalg.norm(canonical[offset:]-v[offset:],axis=1)))
  features={}
  for name,points,primitive,sel in [('ear',body,bp,ear),('eye',eye,ep,np.ones(len(eye),bool)),('diadem',gold,gp,band),('brow',v,hair,brow)]:
   evaluated=skin(g,primitive,points,poses);local=(np.c_[evaluated,np.ones(len(evaluated))]@canon.T)[:,:3]
   features[name]=float(np.max(np.linalg.norm(local[sel]-points[sel],axis=1)))
  rows.append({'id':sample['id'],'finite':bool(np.isfinite(posed).all()),'new_hair_head_relative_drift_m':drift,'feature_head_relative_displacement_m':features})
 masks=g.array(hair['attributes']['COLOR_0'])[:,3]/65535
 newstress=stress(v,t[first:],masks);oldstress=stress(v,t[:first],masks)
 maximum={name:max(row['feature_head_relative_displacement_m'][name]for row in rows)for name in ['ear','eye','diadem','brow']}
 result={'task':'R3-08','source_glb_sha256':sha(g.path),'runtime_sha256':sha(a.runtime),'replay_script_sha256':sha(__file__),'actual_baseline_pose_samples':len(rows),'samples':rows,
  'maximum_feature_head_relative_motion_m':maximum,'new_geometry_six_axis_secondary_stress':newstress,'exact_retained_geometry_six_axis_secondary_stress':oldstress,
  'passed':len(rows)==37 and all(r['finite'] and r['new_hair_head_relative_drift_m']<2e-6 for r in rows) and newstress['finite_nondegenerate_deformed_samples'] and newstress['samples_above_90_degrees']==0,
  'scope':'Actual previously captured baseline pose matrices applied to source candidate with original inverse binds. Does not claim actual groom import, new runtime update execution, weapon contact, pixels or all locomotion. Six-axis offsets are stress samples, not arbitrary-direction maximum. Retained knot behavior remains unchanged and is reported separately.'}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['passed','actual_baseline_pose_samples','maximum_feature_head_relative_motion_m','new_geometry_six_axis_secondary_stress','exact_retained_geometry_six_axis_secondary_stress']},indent=2))
 if not result['passed']:sys.exit(1)

if __name__=='__main__':main()
