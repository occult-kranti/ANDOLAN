"""Actual archived pose replay and conservative complete-triangle clearances."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'art/hero-rama-lod'));from glb_lod import GLB
sys.path.insert(0,str(ROOT/'art/visual-rounds/groom'));from replay_motion import skin
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
g=GLB('/workspace/scratch/visual-round3/role-08/groom-r6/rama-hero.glb');rp=Path('/workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json');runtime=json.loads(rp.read_text());kitp=ROOT/'assets/design/rama-ability-kit.json';kit=json.loads(kitp.read_text());ids=[a['id']for a in kit['abilities']]
def aabb_gap(a,b):return float(np.linalg.norm(np.maximum(np.maximum(a.min((0,1))-b.max((0,1)),b.min((0,1))-a.max((0,1))),0)))
def separation(a,b,threshold=.080):
 whole=aabb_gap(a,b)
 if whole>=threshold:return {'lower_bound_m':whole,'method':'whole-group AABB','near_triangle_pairs':0}
 ac=a.mean(1);bc=b.mean(1);ar=np.linalg.norm(a-ac[:,None,:],axis=2).max(1);br=np.linalg.norm(b-bc[:,None,:],axis=2).max(1);tree=cKDTree(bc);minimum=threshold;count=0;witness=None
 for start in range(0,len(a),400):
  nearby=tree.query_ball_point(ac[start:start+400],ar[start:start+400]+br.max()+threshold,workers=1)
  ai=np.repeat(np.arange(start,start+len(nearby)),[len(x)for x in nearby]);bi=np.array([i for x in nearby for i in x],dtype=int)
  if not len(ai):continue
  aa=a[ai];bb=b[bi];delta=np.maximum(np.maximum(aa.min(1)-bb.max(1),bb.min(1)-aa.max(1)),0);bounds=np.linalg.norm(delta,axis=1);sel=bounds<threshold
  if not sel.any():continue
  aa=aa[sel];bb=bb[sel];ai=ai[sel];bi=bi[sel];bounds=bounds[sel];count+=len(aa)
  ea=[aa[:,1]-aa[:,0],aa[:,2]-aa[:,1],aa[:,0]-aa[:,2]];eb=[bb[:,1]-bb[:,0],bb[:,2]-bb[:,1],bb[:,0]-bb[:,2]];na=np.cross(ea[0],ea[1]);nb=np.cross(eb[0],eb[1]);axes=[na,nb]+[np.cross(x,y)for x in ea for y in eb]+[np.cross(na,x)for x in ea]+[np.cross(nb,x)for x in eb]
  for axis in axes:
   axis=axis/np.maximum(np.linalg.norm(axis,axis=1)[:,None],1e-20);ap=np.einsum('nkj,nj->nk',aa,axis);bp=np.einsum('nkj,nj->nk',bb,axis);bounds=np.maximum(bounds,np.maximum(ap.min(1)-bp.max(1),bp.min(1)-ap.max(1)))
  ix=bounds.argmin()
  if bounds[ix]<minimum:minimum=float(bounds[ix]);witness={'first_triangle':int(ai[ix]),'bow_triangle':int(bi[ix]),'first_xyz':aa[ix].tolist(),'bow_xyz':bb[ix].tolist()}
 return {'lower_bound_m':minimum,'method':'whole triangle AABB + normalized triangle separating axes; unqueried sphere pairs exceed .08m','near_triangle_pairs':count,'minimum_bound_pair':witness,'limit':'Zero bound is unresolved overlap, not proof of penetration; positive is conservative separation.'}
tri1=np.array([[[0,0,0],[1,0,0],[0,1,0]]],float);tri2=tri1+[0,0,.04]
algorithm_checks={'parallel_triangle_40mm':abs(separation(tri1,tri2)['lower_bound_m']-.04)<1e-10,'identical_triangle_zero':separation(tri1,tri1)['lower_bound_m']==0,'far_triangle_lower_bound':separation(tri1,tri1+[0,0,1])['lower_bound_m']>=1}
assert all(algorithm_checks.values())
primitives=[]
for mi,pi,p in g.primitives():
 v=g.array(p['attributes']['POSITION']).astype(float);t=g.array(p['indices']).reshape(-1,3);mat=g.doc['materials'][p['material']]['name'];kind='bow'if mi==0 else 'hair'if mi==2 and pi==0 else 'cloth'if mi==2 and mat in ['Cobalt handwoven silk','Cobalt lotus brocade','Ivory silk']else'other'
 primitives.append((mi,pi,p,v,t,kind))
def projection(points):
 # Three-quarter fullbody camera shared by all poses, front-facing at visual yaw PI.
 world=points*np.array([-1,1,-1]);cam=np.array([-3.,2.2,-4.]);target=np.array([0.,1.,0.]);f=target-cam;f/=np.linalg.norm(f);r=np.cross(f,[0,1,0]);r/=np.linalg.norm(r);u=np.cross(r,f);d=world-cam;z=d@f;s=960/(2*math.tan(math.radians(50)/2));pix=np.c_[640+s*(d@r)/z,480-s*(d@u)/z]
 return {'min':pix.min(0).tolist(),'max':pix.max(0).tolist(),'min_depth_m':float(z.min()),'margin24_pass':bool(z.min()>.05 and np.all(pix.min(0)>=24)and np.all(pix.max(0)<=[1256,936]))}
rows=[]
for sample in runtime['samples']:
 if sample['id']not in [a+'_'+p for a in ids for p in ['windup','release','recoil']]:continue
 groups={k:[]for k in ['bow','hair','cloth']};allpoints=[]
 for mi,pi,p,v,t,kind in primitives:
  posed=skin(g,p,v,sample['bone_global_poses']);allpoints.append(posed)
  if kind in groups:groups[kind].append(posed[t])
 groups={k:np.concatenate(v)for k,v in groups.items()};gaps={k:separation(groups[k],groups['bow'])for k in ['hair','cloth']};row={'id':sample['id'],'motion':sample['motion'],'authority_extra':sample['extra'],'triangle_counts':{k:len(v)for k,v in groups.items()},'gaps':gaps,'projection':projection(np.vstack(allpoints))}
 for name,limit in [('hair',.018),('cloth',.075)]:
  row['gaps'][name]['secondary_envelope_m']=limit;row['gaps'][name]['guaranteed_after_maximum_offset_m']=max(0,gaps[name]['lower_bound_m']-limit);row['gaps'][name]['one_mm_clearance_proven_for_all_offsets']=gaps[name]['lower_bound_m']>limit+.001
 rows.append(row);print(sample['id'],{k:round(v['lower_bound_m'],6)for k,v in gaps.items()},flush=True)
report={'task':'R3-04','source_commit':'0437ea91edf6989ff78c1eeadb3661f4825b60f2','algorithm_checks':algorithm_checks,'samples':rows,'sample_count':len(rows),'all_five_abilities_three_phases_present':len(rows)==15,'source_sha256':{str(p):sha(p)for p in [Path(__file__),g.path,rp,kitp,ROOT/'scripts/rama_ability_kit.gd',ROOT/'scripts/rama_motion.gd',ROOT/'scripts/rama_secondary_motion.gd',ROOT/'art/visual-rounds/groom/replay_motion.py']},'source_projection_passed':all(r['projection']['margin24_pass']for r in rows),'clearance_gate_passed':all(v['one_mm_clearance_proven_for_all_offsets']for r in rows for v in r['gaps'].values()),'scope':'Previously executed runtime poses, replayed offline on actual current source triangles. No newly executed runtime/collision/render. Secondary offsets were not captured in this old tape; subtract full allowed bounds rather than invent actual offsets. Includes all bow primitives and selected actual cloth/hair triangles; quiver integrated gold/cloth classification and dynamic arrow/string sweeps remain separate.'}
(OUT/'action-clearance.json').write_text(json.dumps(report,indent=2)+'\n');assert len(rows)==15 and all(algorithm_checks.values());print(json.dumps({k:report[k]for k in ['sample_count','source_projection_passed','clearance_gate_passed']}))
