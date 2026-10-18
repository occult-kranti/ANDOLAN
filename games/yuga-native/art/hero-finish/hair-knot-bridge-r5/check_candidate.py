"""Incremental R5 source identity and complete-triangle attachment/clearance."""
import argparse,copy,importlib.util,json
from pathlib import Path
import numpy as np
from build_candidate import PROJECT,GLB,PINS,sha
p=PROJECT/'docs/evidence/visual-rounds/round3/role10/geometry_probe.py';spec=importlib.util.spec_from_file_location('triangles',p);narrow=importlib.util.module_from_spec(spec);spec.loader.exec_module(narrow)

def piece(g,mi,pi,select=None):
 pr=g.doc['meshes'][mi]['primitives'][pi];v=g.array(pr['attributes']['POSITION']).astype(float);t=g.array(pr['indices']).reshape(-1,3)
 if select is not None:t=t[select(v,t)]
 used,inv=np.unique(t,return_inverse=True)
 return {'v':v[used],'tri':inv.reshape(-1,3),'j':g.array(pr['attributes']['JOINTS_0'])[used],'w':g.array(pr['attributes']['WEIGHTS_0'])[used],'alpha':g.array(pr['attributes']['COLOR_0'],True)[used,3]}

def posed(part,matrices,offset=None):
 v=np.c_[part['v'],np.ones(len(part['v']))];result=np.zeros((len(v),3))
 for slot in range(4):result+=np.einsum('nij,nj->ni',matrices[part['j'][:,slot]],v)[:,:3]*part['w'][:,slot,None]
 if offset is not None:result+=offset*part['alpha'][:,None]**2
 return result[part['tri']]

def setup(row):
 old=GLB(row['source']);g=GLB(row['output']);assert sha(old.path)==row['source_sha256'] and sha(g.path)==row['output_sha256']
 pr=g.doc['meshes'][2]['primitives'][0];v=g.array(pr['attributes']['POSITION']);t=g.array(pr['indices']).reshape(-1,3)
 new=piece(g,2,0,lambda v,t:np.arange(len(t))>=row['preserved_triangles'])
 return old,g,v,t,new

def surfaces(g,kind):
 out=[]
 for mi,mesh in enumerate(g.doc['meshes']):
  for pi,pr in enumerate(mesh['primitives']):
   name=g.doc['materials'][pr['material']]['name']
   match=name in ['Rama warm skin','Natural lips','Warm sclera','Deep brown iris','Pupil'] if kind=='head' else name in ['Worked warm gold','Recessed antique gold','Polished sapphire']
   if match:
    part=piece(g,mi,pi,lambda v,t:np.any(v[t,1]>(1.65 if kind=='head' else 1.75),axis=1))
    if len(part['tri']):out.append(part)
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--mode',choices=['rest','poses'],default='rest');ap.add_argument('--poses',type=Path);ap.add_argument('--level',choices=['near','mid','far','all'],default='all');a=ap.parse_args();assert not a.output.exists();m=json.loads(a.manifest.read_text());checks=[];rows=[]
 def check(name,okay,**facts):checks.append({'name':name,'passed':bool(okay),**facts})
 tape=json.loads(a.poses.read_text())if a.poses else None
 if tape:assert tape['passed']and len(tape['samples'])==37
 result={'scope':'R5 incremental new attachment triangles plus exact inherited R4 identity. Source/offline declared-pose checks only, not candidate import or visible continuity.','manifest_sha256':sha(a.manifest),'checker_sha256':sha(__file__),'narrow_phase_sha256':sha(p),'triangle_selfcheck':narrow.selfcheck(),'mode':a.mode,'checks':checks,'levels':rows}
 for level,row in m['levels'].items():
  if a.level!='all' and level!=a.level:continue
  old,g,v,t,new=setup(row);assert sha(old.path)==PINS[level]
  hp=g.doc['meshes'][2]['primitives'][0];op=old.doc['meshes'][2]['primitives'][0];n=row['preserved_vertices'];nt=row['preserved_triangles']
  if a.mode=='rest':
   check(level+':complete R4 binary prefix exact',g.binary[:len(old.binary)]==old.binary)
   before,after=copy.deepcopy(old.doc),copy.deepcopy(g.doc);after['accessors']=after['accessors'][:len(before['accessors'])];after['bufferViews']=after['bufferViews'][:len(before['bufferViews'])];after['meshes'][2]['primitives'][0]=before['meshes'][2]['primitives'][0];after['buffers']=before['buffers'];check(level+':nonhair and all prior JSON exact',before==after)
   for key,index in op['attributes'].items():check(level+':unchanged active R4 '+key,old.array(index).tobytes()==g.array(hp['attributes'][key])[:n].tobytes())
   check(level+':unchanged active R4 indices',old.array(op['indices']).tobytes()==t[:nt].astype('<u4').reshape(-1,1).tobytes())
   attributes={key:g.array(index)[n:]for key,index in hp['attributes'].items()};normal=attributes['NORMAL'];tan=attributes['TANGENT']
   check(level+':new arrays finite',all(np.isfinite(x).all()for x in attributes.values()))
   check(level+':unit orthogonal TBN',np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-5 and np.max(abs(np.linalg.norm(tan[:,:3],axis=1)-1))<1e-5 and np.max(abs(np.sum(normal*tan[:,:3],axis=1)))<1e-5 and np.all(abs(tan[:,3])==1))
   check(level+':white anchored head binding',np.all(attributes['COLOR_0'][:,:3]==65535)and np.all(attributes['COLOR_0'][:,3]==0)and np.all(attributes['JOINTS_0']==[104,0,0,0])and np.all(attributes['WEIGHTS_0']==[1,0,0,0]))
   uv=attributes['TEXCOORD_0'];check(level+':bounded UVs',uv.min()>=0 and uv.max()<=1)
   triangles=v[t[nt:]];area=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)*.5
   check(level+':nondegenerate new triangles',area.min()>1e-12,minimum_area_m2=float(area.min()))
   lo,hi=v[n:].min(0),v[n:].max(0);check(level+':compact stored envelope',np.max(abs(v[n:,0]))<.030 and lo[1]>1.80 and hi[1]<1.865 and lo[2]>-.070 and hi[2]<.025,minimum=lo.tolist(),maximum=hi.tolist())
   heads=surfaces(old,'head');gold=surfaces(old,'gold');identity=np.repeat(np.eye(4)[None],164,axis=0)
   for label,parts in [('full_head_and_features',heads),('all_head_gold_and_gems',gold)]:
    contact=narrow.compare(triangles,np.concatenate([posed(part,identity)for part in parts]),band=.012);check(level+':complete new triangles clear '+label,contact['crossings']==0 and contact['guaranteed_lower_bound_m']>.0002,comparison=contact)
   r4manifest=json.loads((PROJECT/'art/hero-finish/hair-silhouette-r1/candidate-r4/groom-manifest.json').read_text());ret=r4manifest['levels'][level]['retained_triangles'];ov=old.array(op['attributes']['POSITION']);ot=old.array(op['indices']).reshape(-1,3);knot=(np.arange(len(ot))<ret)&np.all(ov[ot,1]>1.854,axis=1);root=(np.arange(len(ot))>=ret)&np.any(ov[ot,1]>1.80,axis=1)
   for label,mask in [('unchanged_knot',knot),('unchanged_reduced_crown',root)]:
    c=narrow.compare(triangles,ov[ot[mask]],band=.012);check(level+':positive hair overlap '+label,c['crossings']>0,comparison=c)
   rows.append({'level':level,'stored_min':lo.tolist(),'stored_max':hi.tolist(),'new_triangles':len(triangles)})
  else:
   assert tape is not None
   reference=GLB(PROJECT/'art/hero-finish/s4-diadem-smooth/candidate-r2'/old.path.name)
   for key in ['skins','nodes','animations','materials']:assert old.doc.get(key)==reference.doc.get(key)
   for mi,pi,pr in reference.primitives():
    if(mi,pi)==(2,0):continue
    op=old.doc['meshes'][mi]['primitives'][pi]
    for key in ['POSITION','NORMAL','JOINTS_0','WEIGHTS_0']:assert reference.array(pr['attributes'][key]).tobytes()==old.array(op['attributes'][key]).tobytes()
    assert reference.array(pr['indices']).tobytes()==old.array(op['indices']).tobytes()
   assert tape['source_pins']['res://assets/heroes/rama-hero.glb']=='e98c9110161e49b653e98b6f4ca1dda997ad891cf73b737abd18f319bb3c2b82'
   result['pose_transfer']='Exact R2-source skeleton/nodes/materials/animations/nonhair collision geometry; accepted UV and R4 hair changes do not alter those matrices or surfaces.'
   ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);names=[g.doc['nodes'][i]['name']for i in g.doc['skins'][0]['joints']];assert names[104]=='head'and len(names)==164
   targets={kind:surfaces(old,kind)for kind in ['head','gold']}
   for sample in tape['samples']:
    transforms=np.array([sample['bone_global_poses'][name]for name in names])@ib;triangles=posed(new,transforms)
    comparisons={kind:narrow.compare(triangles,np.concatenate([posed(part,transforms)for part in parts]),band=.012)for kind,parts in targets.items()}
    okay=all(c['crossings']==0 and c['guaranteed_lower_bound_m']>.0002 for c in comparisons.values());check(level+':'+sample['id'],okay,comparisons=comparisons)
   rows.append({'level':level,'pose_count':37})
 result['passed']=all(c['passed']for c in checks);result['complete']=True
 if a.poses:result['pose_tape_sha256']=sha(a.poses)
 a.output.write_text(json.dumps(result,indent=2)+'\n');print('passed',result['passed'],'checks',len(checks),'failures',[(c['name'],c.get('comparison',{}).get('crossings'))for c in checks if not c['passed']]);raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
