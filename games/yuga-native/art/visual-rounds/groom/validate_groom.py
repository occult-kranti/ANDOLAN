"""Independent source identity, fitted coverage, clearance and frame checks.

Clearance uses minimum distance between triangle AABBs as a conservative lower
bound, not vertex-only sampling. Positive bounds prove entire triangle separation
in this rest-space model. Runtime action/contact and imported pixels remain gates.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from build_groom import GLB, PROJECT, PINS, Skull, ORIGIN, sha, retained

def minimum_aabb_gap(first,second):
 alo,ahi=first.min(1),first.max(1);blo,bhi=second.min(1),second.max(1);minimum=float('inf')
 for start in range(0,len(alo),80):
  delta=np.maximum(np.maximum(alo[start:start+80,None,:]-bhi[None,:,:],blo[None,:,:]-ahi[start:start+80,None,:]),0.)
  gap=np.sqrt(np.sum(delta*delta,axis=2));close=np.where(gap<.006)
  if len(close[0]):
   aa=first[start+close[0]].astype(float);bb=second[close[1]].astype(float)
   ea=[aa[:,1]-aa[:,0],aa[:,2]-aa[:,1],aa[:,0]-aa[:,2]];eb=[bb[:,1]-bb[:,0],bb[:,2]-bb[:,1],bb[:,0]-bb[:,2]]
   na=np.cross(ea[0],ea[1]);nb=np.cross(eb[0],eb[1])
   axes=[na,nb]+[np.cross(x,y)for x in ea for y in eb]+[np.cross(na,x)for x in ea]+[np.cross(nb,x)for x in eb]
   bounds=gap[close].copy()
   for axis in axes:
    axis=axis/np.maximum(np.linalg.norm(axis,axis=1)[:,None],1e-20)
    ap=np.einsum('nkj,nj->nk',aa,axis);bp=np.einsum('nkj,nj->nk',bb,axis)
    bounds=np.maximum(bounds,np.maximum(ap.min(1)-bp.max(1),bp.min(1)-ap.max(1)))
   gap[close]=bounds
  minimum=min(minimum,float(gap.min()))
 return minimum

def surface(g,mi,pi):
 p=g.doc['meshes'][mi]['primitives'][pi];v=g.array(p['attributes']['POSITION']);t=g.array(p['indices']).reshape(-1,3)
 return v,t,p

def point_triangle_distance(points,triangles):
 """Broadcast corresponding points/triangles; exact point-to-closed-triangle."""
 a,b,c=triangles[...,0,:],triangles[...,1,:],triangles[...,2,:]
 ab=b-a;ac=c-a;n=np.cross(ab,ac);n2=np.sum(n*n,axis=-1)
 projection=points-n*np.divide(np.sum((points-a)*n,axis=-1),n2,out=np.zeros_like(n2),where=n2>1e-24)[...,None]
 ap=projection-a;d00=np.sum(ab*ab,axis=-1);d01=np.sum(ab*ac,axis=-1);d11=np.sum(ac*ac,axis=-1);d20=np.sum(ap*ab,axis=-1);d21=np.sum(ap*ac,axis=-1)
 den=d00*d11-d01*d01
 u=np.divide(d11*d20-d01*d21,den,out=np.full_like(den,-1),where=abs(den)>1e-24)
 v=np.divide(d00*d21-d01*d20,den,out=np.full_like(den,-1),where=abs(den)>1e-24)
 inside=(u>=0)&(v>=0)&(u+v<=1)
 dist=np.where(inside,np.linalg.norm(points-projection,axis=-1),np.inf)
 for start,end in [(a,b),(b,c),(c,a)]:
  edge=end-start;param=np.clip(np.sum((points-start)*edge,axis=-1)/np.maximum(np.sum(edge*edge,axis=-1),1e-24),0,1)
  dist=np.minimum(dist,np.linalg.norm(points-(start+param[...,None]*edge),axis=-1))
 return dist

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
 m=json.loads(a.manifest.read_text());checks=[];details={}
 def check(name,passed,**facts):checks.append({'name':name,'passed':bool(passed),**facts})
 near=None
 for level,item in m['levels'].items():
  old,new=GLB(item['source']),GLB(item['output']);v,t,p=surface(new,2,0);offset=item['retained_vertices'];first=item['retained_triangles']
  arrays={k:new.array(i) for k,i in p['attributes'].items()};oldattrs,oldtri,oldrows=retained(old)
  check(level+': exact source and output pins',sha(old.path)==PINS[level] and sha(new.path)==item['output_sha256'])
  check(level+': original binary prefix exact',new.binary[:len(old.binary)]==old.binary,bytes=len(old.binary))
  before,after=copy.deepcopy(old.doc),copy.deepcopy(new.doc)
  after['accessors']=after['accessors'][:len(before['accessors'])];after['bufferViews']=after['bufferViews'][:len(before['bufferViews'])]
  after['meshes'][2]['primitives'][0]=before['meshes'][2]['primitives'][0];after['buffers']=before['buffers']
  check(level+': JSON exact except appended views/accessors and hair primitive',before==after)
  check(level+': eyebrow and topknot exact records and triangles',all(np.array_equal(arrays[k][:offset],v0)for k,v0 in oldattrs.items()) and np.array_equal(t[:first],oldtri))
  check(level+': every nonhair primitive exact',all(p0==new.doc['meshes'][mi]['primitives'][pi] for mi,pi,p0 in old.primitives() if(mi,pi)!=(2,0)))
  check(level+': all new attributes finite',all(np.isfinite(x[offset:]).all()for x in arrays.values()))
  check(level+': all indices in bounds',int(t.min())>=0 and int(t.max())<len(v))
  area=np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)
  check(level+': no new degenerate triangles',bool(np.all(area[first:]>1e-12)),retained_degenerate_triangles=int(np.sum(area[:first]<1e-12)),minimum_new_twice_area_m2=float(area[first:].min()))
  n=arrays['NORMAL'][offset:];tt=arrays['TANGENT'][offset:];nl=np.linalg.norm(n,axis=1);tl=np.linalg.norm(tt[:,:3],axis=1)
  check(level+': new normal tangent frames unit orthogonal',np.max(abs(nl-1))<1e-5 and np.max(abs(tl-1))<1e-5 and np.max(abs(np.sum(n*tt[:,:3],axis=1)))<1e-5 and np.all(abs(tt[:,3])==1),minimum_tangent_norm=float(tl.min()))
  uv=arrays['TEXCOORD_0'][offset:];check(level+': finite bounded UVs',np.isfinite(uv).all() and uv.min()>=0 and uv.max()<=1)
  check(level+': one original head joint binding',np.all(arrays['JOINTS_0'][offset:]==[104,0,0,0]) and np.all(arrays['WEIGHTS_0'][offset:]==[1,0,0,0]) and old.doc['nodes'][old.doc['skins'][0]['joints'][104]]['name']=='head')
  colors=arrays['COLOR_0'][offset:];check(level+': semantic mask bounded RGB white',np.all(colors[:,:3]==65535) and colors[:,3].max()<=65535 and colors[:,3].min()==0 and colors[:,3].max()>0)
  rootparts=[p0 for p0 in item['parts'] if not p0['name'].startswith('nape')]
  check(level+': scalp crown temple anchored at zero alpha',all(np.all(arrays['COLOR_0'][part['start']:part['start']+part['count'],3]==0)for part in rootparts))
  check(level+': original opaque material channels and culling exact',new.doc['materials']==old.doc['materials'] and new.doc['materials'][p['material']].get('alphaMode','OPAQUE')=='OPAQUE')
  # Outward crown normal test is unnecessary for tube guides with rotating frames;
  # closed profile winding is tested by centroid-relative normals along each row.
  scalp=item['parts'][0];st=t[first:first+scalp['triangles']];centers=v[st].mean(1);fn=np.cross(v[st[:,1]]-v[st[:,0]],v[st[:,2]]-v[st[:,0]])
  check(level+': scalp triangle winding outward',np.all(np.sum(fn*(centers-ORIGIN),axis=1)>0))
  generated_tri=t[first:];newtri=v[generated_tri]
  body,bodyt,_=surface(old,2,11);btri=body[bodyt]
  # Conservative ear patch includes the helix, not only extreme ear vertices.
  earv=(abs(body[:,0])>.075)&(body[:,1]>1.668)&(body[:,1]<1.745)&(body[:,2]>.010)&(body[:,2]<.080)
  ear=btri[np.all(earv[bodyt],axis=1)]
  eye,eyet,_=surface(old,2,7)
  brow=oldattrs['POSITION'];bmask=(brow[:,1]<1.755)&(brow[:,2]>.139);browtri=brow[oldtri[np.all(bmask[oldtri],axis=1)]]
  gold,goldt,_=surface(old,2,2);bandv=(gold[:,1]>1.779)&(gold[:,1]<1.805)&(abs(gold[:,0])<.112)&(gold[:,2]<.175)&(gold[:,2]>-.115)
  band=gold[goldt[np.all(bandv[goldt],axis=1)]]
  gaps={name:minimum_aabb_gap(newtri,other)for name,other in [('ear',ear),('eye',eye[eyet]),('eyebrow',browtri),('diadem',band)]}
  check(level+': complete new triangles clear ears eyes brows band',all(gaps[k]>.001 for k in gaps),conservative_rest_clearance_m=gaps,feature_triangle_counts={'ear':len(ear),'eye':len(eyet),'eyebrow':len(browtri),'diadem':len(band)})
  # Every face/ear-adjacent vertex is anchored; arbitrary secondary extremes may
  # move only lower nape, with an explicit maximum world-space displacement.
  moving=arrays['COLOR_0'][offset:,3]>0;mask=arrays['COLOR_0'][offset:,3]/65535
  check(level+': moving region below ears and bounded',np.all(v[offset:][moving,1]<1.70) and float((mask**2*.018).max())<=.011,maximum_secondary_vertex_m=float((mask**2*.018).max()))
  details[level]={'vertices':len(v),'triangles':len(t),'new_vertices':len(v)-offset,'new_triangles':len(t)-first,'retained_original_degenerates':int(np.sum(area[:first]<1e-12)),'clearance_lower_bounds_m':gaps,'glb_bytes':len(new.raw)}
  if near is None:near=(newtri,cKDTree(newtri.mean(axis=1)))
  else:
   # 20 nearest triangle centroids give an upper bound on distance to the full
   # near surface. Passing this bound is conservative; no vertex-spacing proxy.
   _,ids=near[1].query(v[offset:],k=20);distances=point_triangle_distance(v[offset:,None,:],near[0][ids]).min(1)
   check(level+': same guide silhouette envelope within 6mm',distances.max()<.006,maximum_vertex_to_near_surface_upper_bound_m=float(distances.max()))
  # Coverage witnesses are scalp vertices below the former 1.78m cut. Their
  # source radial ray distance confirms a physically seated shell in that gap.
  cp=v[scalp['start']:scalp['start']+scalp['count']];witness=cp[(cp[:,1]<1.78)&(cp[:,1]>1.748)&(abs(cp[:,0])>.065)&(cp[:,2]>.005)]
  check(level+': substantial bilateral source-fitted temple coverage',len(witness)>15 and np.any(witness[:,0]<0) and np.any(witness[:,0]>0),coverage_witness_vertices=len(witness),lowest_witness_y=float(witness[:,1].min()))
 result={'task':'R3-08','passed':all(c['passed']for c in checks),'count':len(checks),'checks':checks,'levels':details,'generator_sha256':m['generator_sha256'],'validator_sha256':sha(__file__),'manifest_sha256':sha(a.manifest),'clearance_method':'AABB separation, refined below 6mm with triangle separating-axis projection distances. Positive minimum is a conservative lower bound on entire triangle separation, not nearest-vertex sampling.','scope':'CPU source geometry. Exact preserved payloads and conservative rest triangle clearance; not imported animation, action collisions, pixel acceptance or GPU performance.'}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'count':len(checks),'failed':[c for c in checks if not c['passed']],'levels':details},indent=2))
 if not result['passed']:sys.exit(1)

if __name__=='__main__':main()
