"""Independent full-triangle narrow phase on posed candidate nape/neck/collar."""
from pathlib import Path
import sys,json,hashlib,time
sys.path.insert(0,str(Path(__file__).parents[1]/'role09'))
from glb_read import GLB,sha
import numpy as np
from scipy.spatial import cKDTree
OUT=Path(__file__).parent;MAN=Path('/workspace/scratch/visual-round3/role-08/groom-r6/groom-manifest.json');POSE=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/visual-rounds/round3/role10/actual-imported-pose-tape.json')
def point_tri(p,t):
 a,b,c=t[:,0],t[:,1],t[:,2];ab=b-a;ac=c-a;n=np.cross(ab,ac);n2=(n*n).sum(1);signed=((p-a)*n).sum(1);q=p-n*np.divide(signed,n2,out=np.zeros_like(n2),where=n2>1e-24)[:,None]
 v0=ab;v1=ac;v2=q-a;d00=(v0*v0).sum(1);d01=(v0*v1).sum(1);d11=(v1*v1).sum(1);d20=(v2*v0).sum(1);d21=(v2*v1).sum(1);den=d00*d11-d01*d01
 u=np.divide(d11*d20-d01*d21,den,out=np.full_like(den,-1),where=abs(den)>1e-24);v=np.divide(d00*d21-d01*d20,den,out=np.full_like(den,-1),where=abs(den)>1e-24)
 distance=np.where((u>=0)&(v>=0)&(u+v<=1)&(n2>1e-24),abs(signed)/np.sqrt(np.maximum(n2,1e-24)),np.inf)
 for x,y in [(a,b),(b,c),(c,a)]:
  e=y-x;s=np.clip(((p-x)*e).sum(1)/np.maximum((e*e).sum(1),1e-24),0,1);distance=np.minimum(distance,np.linalg.norm(p-x-s[:,None]*e,axis=1))
 return distance

def edge_edge(a,b,c,d):
 u=b-a;v=d-c;w=a-c;aa=(u*u).sum(1);bb=(u*v).sum(1);cc=(v*v).sum(1);dd=(u*w).sum(1);ee=(v*w).sum(1);den=aa*cc-bb*bb
 s=np.divide(bb*ee-cc*dd,den,out=np.full_like(den,-1),where=den>1e-24);t=np.divide(aa*ee-bb*dd,den,out=np.full_like(den,-1),where=den>1e-24)
 distance=np.where((s>=0)&(s<=1)&(t>=0)&(t<=1)&(den>1e-24),np.linalg.norm(w+s[:,None]*u-t[:,None]*v,axis=1),np.inf)
 for p,x,y in [(a,c,d),(b,c,d),(c,a,b),(d,a,b)]:
  edge=y-x;at=np.clip(((p-x)*edge).sum(1)/np.maximum((edge*edge).sum(1),1e-24),0,1);distance=np.minimum(distance,np.linalg.norm(p-x-at[:,None]*edge,axis=1))
 return distance

def edge_cross(a,b,t):
 d=b-a;e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0];h=np.cross(d,e2);det=(e1*h).sum(1);inv=np.divide(1,det,out=np.zeros_like(det),where=abs(det)>1e-14);s=a-t[:,0];u=(s*h).sum(1)*inv;q=np.cross(s,e1);v=(d*q).sum(1)*inv;at=(e2*q).sum(1)*inv
 return (abs(det)>1e-14)&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(at>=-1e-9)&(at<=1+1e-9)

def narrow(a,b):
 distance=np.full(len(a),np.inf);cross=np.zeros(len(a),bool)
 for k in range(3):
  distance=np.minimum(distance,point_tri(a[:,k],b));distance=np.minimum(distance,point_tri(b[:,k],a));cross|=edge_cross(a[:,k],a[:,(k+1)%3],b)|edge_cross(b[:,k],b[:,(k+1)%3],a)
  for j in range(3):distance=np.minimum(distance,edge_edge(a[:,k],a[:,(k+1)%3],b[:,j],b[:,(j+1)%3]))
 distance[cross]=0
 return distance,cross

def compare(a,b,band=.012):
 ac=a.mean(1);bc=b.mean(1);ar=np.linalg.norm(a-ac[:,None],axis=2).max(1);br=np.linalg.norm(b-bc[:,None],axis=2).max(1)
 ap=[];bp=[]
 # Radius buckets prevent one long trim triangle from making every hair
 # triangle query the entire neck/collar mesh; retain complete pair coverage.
 for low,high in zip([0,.005,.01,.02,.05,.1],[.005,.01,.02,.05,.1,np.inf]):
  selected=np.flatnonzero((br>=low)&(br<high))
  if not len(selected):continue
  tree=cKDTree(bc[selected])
  for begin in range(0,len(a),256):
   lists=tree.query_ball_point(ac[begin:begin+256],ar[begin:begin+256]+br[selected].max()+band)
   ia=np.repeat(np.arange(begin,min(begin+256,len(a))),[len(x) for x in lists])
   if not len(ia):continue
   ib=selected[np.concatenate(lists).astype(int)]
   lo=np.maximum(a[ia].min(1)-b[ib].max(1),b[ib].min(1)-a[ia].max(1));keep=np.linalg.norm(np.maximum(lo,0),axis=1)<=band
   ap.append(ia[keep]);bp.append(ib[keep])
 aa=np.concatenate(ap) if ap else np.array([],int);bb=np.concatenate(bp) if bp else np.array([],int)
 if not len(aa):return {'minimum_distance_m':None,'guaranteed_lower_bound_m':band,'near_pairs':0,'crossings':0}
 lo=np.maximum(a[aa].min(1)-b[bb].max(1),b[bb].min(1)-a[aa].max(1));keep=np.linalg.norm(np.maximum(lo,0),axis=1)<=band;aa=aa[keep];bb=bb[keep]
 if not len(aa):return {'minimum_distance_m':None,'guaranteed_lower_bound_m':band,'near_pairs':0,'crossings':0}
 distances=np.empty(len(aa));cross=np.empty(len(aa),bool)
 for begin in range(0,len(aa),8192):distances[begin:begin+8192],cross[begin:begin+8192]=narrow(a[aa[begin:begin+8192]],b[bb[begin:begin+8192]])
 best=int(distances.argmin());return {'minimum_distance_m':float(distances[best]),'guaranteed_lower_bound_m':float(min(band,distances[best])),'near_pairs':len(aa),'crossings':int(cross.sum()),'witness_triangles':[int(aa[best]),int(bb[best])],'witness_hair_triangle':a[aa[best]].tolist(),'witness_other_triangle':b[bb[best]].tolist()}

def selfcheck():
 t=np.array([[[0.,0,0],[1,0,0],[0,1,0]]]);separated=t+[0,0,.005];cross=np.array([[[.2,.2,-1],[.2,.2,1],[.8,.2,0]]]);d,c=narrow(t,separated);e,x=narrow(t,cross)
 assert abs(d[0]-.005)<1e-10 and not c[0] and e[0]==0 and x[0]
 return {'separated_parallel_triangle_gap_m':float(d[0]),'edge_through_face_crossing':bool(x[0])}

def main():
 started=time.time();m=json.loads(MAN.read_text());item=m['levels']['near'];g=GLB(item['output']);old=GLB(item['source']);runtime=json.loads(POSE.read_text());inverse=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);names=[g.doc['nodes'][i]['name'] for i in g.doc['skins'][0]['joints']]
 parts={};cache={}
 for pi,label in [(0,'new_hair'),(2,'gold_collar'),(3,'silk_collar'),(4,'brocade_collar'),(11,'neck_chest')]:
  p=g.doc['meshes'][2]['primitives'][pi];v=g.array(p['attributes']['POSITION']);tri=g.array(p['indices']).reshape(-1,3)
  if pi==0:tri=tri[item['retained_triangles']:];select=np.any(v[tri,1]<1.71,axis=1)
  else:select=np.any((v[tri,1]>1.45)&(v[tri,1]<1.70),axis=1)&np.all(abs(v[tri,0])<.28,axis=1)
  tri=tri[select];used,index=np.unique(tri,return_inverse=True);alpha=g.array(p['attributes']['COLOR_0'],True)[used,3] if 'COLOR_0' in p['attributes'] else np.zeros(len(used));parts[label]={'v':v[used],'tri':index.reshape(-1,3),'j':g.array(p['attributes']['JOINTS_0'])[used],'w':g.array(p['attributes']['WEIGHTS_0'])[used],'alpha':alpha,'source_triangle_count':len(tri)}
 def posed(part,poses):
  transforms=np.array([poses[n] for n in names])@inverse;p=np.c_[part['v'],np.ones(len(part['v']))];result=np.zeros((len(p),3))
  for slot in range(4):result+=(np.einsum('nij,nj->ni',transforms[part['j'][:,slot]],p)[:,:3])*part['w'][:,slot,None]
  return result
 rows=[]
 for sample in runtime['samples']:
  geom={name:posed(part,sample['bone_global_poses']) for name,part in parts.items()};key=hashlib.sha256(b''.join(v.astype('<f4').tobytes() for v in geom.values())).hexdigest()
  if key in cache:rows.append({'pose':sample['id'],'identical_geometry_to':cache[key]});continue
  cache[key]=sample['id'];hair=geom['new_hair'][parts['new_hair']['tri']];comparisons={name:compare(hair,geom[name][parts[name]['tri']]) for name in parts if name!='new_hair'};rows.append({'pose':sample['id'],'comparisons':comparisons});print(sample['id'],{k:round(v['guaranteed_lower_bound_m']*1000,3) for k,v in comparisons.items()},flush=True)
 # Secondary offsets are mesh-local after skinning, so apply them to final
 # geometry, not to rest-space inputs. Test independent opposing diagonal fields.
 stress=[]
 for sample in []:
  geom={name:posed(part,sample['bone_global_poses']) for name,part in parts.items()}
  for direction in [np.array([1,0,0]),np.array([0,1,0]),np.array([0,0,1]),np.array([1,1,1])/np.sqrt(3)]:
   for sign in [-1,1]:
    moved={name:v+direction*sign*(.018 if name=='new_hair' else -.075)*parts[name]['alpha'][:,None]**2 for name,v in geom.items()};hair=moved['new_hair'][parts['new_hair']['tri']];comparisons={name:compare(hair,moved[name][parts[name]['tri']]) for name in parts if name!='new_hair'};stress.append({'pose':sample['id'],'direction':(direction*sign).tolist(),'comparisons':comparisons})
  print('stress',sample['id'],flush=True)
 preserved=True
 for mi,mesh in enumerate(old.doc['meshes']):
  for pi,p in enumerate(mesh['primitives']):
   if (mi,pi)==(2,0):continue
   q=g.doc['meshes'][mi]['primitives'][pi];preserved=preserved and p==q and all(np.array_equal(old.array(index),g.array(index)) for index in list(p['attributes'].values())+[p['indices']])
 result={'task':'R3-10','source_glb_sha256':sha(g.path),'source_pose_sha256':sha(POSE),'reader_sha256':sha(OUT.parent/'role09/glb_read.py'),'probe_sha256':sha(__file__),'selfcheck':selfcheck(),'region_triangle_counts':{name:part['source_triangle_count'] for name,part in parts.items()},'source_poses':len(runtime['samples']),'unique_posed_geometry':len(cache),'poses':rows,'secondary_stress':stress,'nonhair_geometry_exact':preserved,'elapsed_seconds':time.time()-started,'scope':'Independent full-triangle intersection/distance test for new lower groom against rest-selected neck/chest/collar regions. Uses 39 newly executed actual imported poses at 30/60/120 Hz; no secondary stress in this report. Existing separate replay report contains opposing secondary stress. Nonhair geometry is exact; separate imported-motion-contact.json executes actual hand/string/sole checks. No import or rendering.'}
 (OUT/'actual-imported-geometry.json').write_text(json.dumps(result,indent=2)+'\n');print('done',result['elapsed_seconds'],flush=True)
if __name__=='__main__':main()
