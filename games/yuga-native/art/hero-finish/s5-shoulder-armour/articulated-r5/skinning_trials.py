"""Ordinary four-weight shoulder transfer; metal strain remains an explicit gate."""
import gzip,json,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from fit_articulation import ROOT,GLB,prepare_geometry,transform,collider_parts,skin,contacts,sha
HERE=Path(__file__).resolve().parent

def point_barycentric(points,triangles):
 points=np.asarray(points,dtype=float);triangles=np.asarray(triangles,dtype=float)
 # Exact closest point is either the valid plane projection or an edge point.
 a,b,c=triangles[:,0],triangles[:,1],triangles[:,2];ab=b-a;ac=c-a;ap=points-a
 d00=np.sum(ab*ab,1);d01=np.sum(ab*ac,1);d11=np.sum(ac*ac,1);d20=np.sum(ap*ab,1);d21=np.sum(ap*ac,1);den=d00*d11-d01*d01
 v=np.divide(d11*d20-d01*d21,den,out=np.zeros_like(den),where=abs(den)>1e-20);w=np.divide(d00*d21-d01*d20,den,out=np.zeros_like(den),where=abs(den)>1e-20)
 bary=np.c_[1-v-w,v,w];q=np.einsum('ni,nij->nj',bary,triangles);distance=np.sum((q-points)**2,1);distance[(bary.min(1)<0)|(abs(den)<=1e-20)]=np.inf
 for i,j in [(0,1),(1,2),(2,0)]:
  edge=triangles[:,j]-triangles[:,i];lens=np.sum(edge*edge,1);t=np.clip(np.divide(np.sum((points-triangles[:,i])*edge,1),lens,out=np.zeros_like(lens),where=lens>0),0,1)
  p=triangles[:,i]+t[:,None]*edge;d=np.sum((p-points)**2,1);better=d<distance
  candidate=np.zeros_like(bary);candidate[:,i]=1-t;candidate[:,j]=t;bary[better]=candidate[better];distance[better]=d[better]
 return distance,bary

def transfer(v,part):
 tri=part['v'][part['tri']];centers=tri.mean(1);radius=np.linalg.norm(tri-centers[:,None],axis=2).max(1);tree=cKDTree(centers)
 upper,_=cKDTree(part['v']).query(v);near=tree.query_ball_point(v,upper+radius.max()+1e-7)
 outj=np.zeros((len(v),4),np.uint16);outw=np.zeros((len(v),4),np.float64);dropped=[];distances=[];source_faces=[];barys=[]
 for i,ids in enumerate(near):
  ids=np.array(ids,int);d,b=point_barycentric(np.repeat(v[i,None],len(ids),axis=0),tri[ids]);best=int(np.argmin(d));face=int(ids[best]);bary=b[best];weights={}
  for corner,amount in zip(part['tri'][face],bary):
   for joint,weight in zip(part['j'][corner],part['w'][corner]):weights[int(joint)]=weights.get(int(joint),0)+float(amount*weight)
  ordered=sorted(weights.items(),key=lambda x:(-x[1],x[0]));keep=ordered[:4];total=sum(x[1] for x in keep);assert total>0
  for k,(joint,weight) in enumerate(keep):outj[i,k]=joint;outw[i,k]=weight/total
  dropped.append(sum(x[1] for x in ordered[4:]));distances.append(float(np.sqrt(d[best])));source_faces.append(face);barys.append(bary.tolist())
 return outj,outw,{'maximum_dropped_weight':max(dropped),'maximum_transfer_distance_m':max(distances),'source_triangles':source_faces,'source_barycentrics':barys}

def strain(v,moved,t):
 old=v[t];new=moved[t];a=np.linalg.norm(np.cross(old[:,1]-old[:,0],old[:,2]-old[:,0]),axis=1);b=np.linalg.norm(np.cross(new[:,1]-new[:,0],new[:,2]-new[:,0]),axis=1)
 ratios=[]
 for i,j in [(0,1),(1,2),(2,0)]:ratios.append(np.linalg.norm(new[:,i]-new[:,j],axis=1)/np.linalg.norm(old[:,i]-old[:,j],axis=1))
 r=np.concatenate(ratios)
 return {'minimum_edge_ratio':float(r.min()),'maximum_edge_ratio':float(r.max()),'p95_absolute_edge_strain':float(np.percentile(abs(r-1),95)),'minimum_area_ratio':float((b/a).min()),'maximum_area_ratio':float((b/a).max())}

def main():
 out=HERE/'skinning-trials-r1.json';assert not out.exists();began=time.monotonic()
 g=GLB(ROOT/'assets/heroes/rama-hero.glb');ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
 _,groups=prepare_geometry('far',g,ib);source=collider_parts(g);parts={n:p for n,p in source.items() if n in ['Rama warm skin','Cobalt handwoven silk','Cobalt lotus brocade']}
 tape=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()));samples=[tape['samples'][i] for i in sorted(set([0,347]+list(range(0,348,29))))]
 prepared=[(s['id'],np.array(s['bone_globals']),{n:skin(p['v'],p['j'],p['w'],np.array(s['bone_globals'])@ib) for n,p in parts.items()}) for s in samples];rows=[]
 for plate,(v,t) in enumerate(groups):
  for mode in ['body-barycentric','clavicle-to-arm']:
   if mode=='body-barycentric':j,w,info=transfer(v,parts['Rama warm skin'])
   else:
    local=transform(v,ib[50]);blend=np.clip((local[:,1]+.005)/.22,0,1);blend=blend*blend*(3-2*blend)
    j=np.tile([49,50,0,0],(len(v),1));w=np.c_[1-blend,blend,np.zeros((len(v),2))];info={'method':'Smoothstep source axial -.005 to .215m, existing49/50 only.'}
   witness=[]
   for label,poses,posed in prepared:
    moved=skin(v,j,w,poses@ib);result=contacts(moved,t,parts,posed)
    witness.append({'pose':label,'contacts':result,'deformation':strain(v,moved,t)})
   counts={n:sum(row['contacts'][n]['crossings'] for row in witness) for n in parts}
   row={'plate':plate,'mode':mode,'transfer':info,'crossing_pairs':counts,'poses':witness};rows.append(row)
   print(plate,mode,counts,'strain',max(r['deformation']['p95_absolute_edge_strain'] for r in witness),flush=True)
   out.write_text(json.dumps({'schema':1,'complete':False,'script_sha256':sha(__file__),'rows':rows},indent=2)+'\n')
 out.write_text(json.dumps({'schema':1,'complete':True,'script_sha256':sha(__file__),'rows':rows,'elapsed_s':time.monotonic()-began,'scope':'Ordinary LBS diagnostic on actual existing rig with transferred or distributed weights. Metal deformation and actual contacts reported; no asset/controller/render acceptance.'},indent=2)+'\n')
if __name__=='__main__':main()
