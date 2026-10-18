"""Rigid plate frames from actual skinned support points, no source edits."""
import gzip,json,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from fit_articulation import ROOT,GLB,prepare_geometry,transform,collider_parts,skin,contacts,sha
HERE=Path(__file__).resolve().parent

def rigid_fit(a,b):
 ac=a.mean(0);bc=b.mean(0);u,_,vt=np.linalg.svd((a-ac).T@(b-bc));r=vt.T@u.T
 if np.linalg.det(r)<0:vt[-1]*=-1;r=vt.T@u.T
 m=np.eye(4);m[:3,:3]=r;m[:3,3]=bc-r@ac
 return m

def main():
 out=HERE/'support-frame-trials-r1.json';assert not out.exists();began=time.monotonic()
 g=GLB(ROOT/'assets/heroes/rama-hero.glb');ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
 _,groups=prepare_geometry('far',g,ib);source=collider_parts(g)
 parts={n:p for n,p in source.items() if n in ['Rama warm skin','Cobalt handwoven silk','Cobalt lotus brocade']};body=parts['Rama warm skin']
 tape=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()));samples=[tape['samples'][i] for i in sorted(set([0,347]+list(range(0,348,29))))]
 prepared=[(s['id'],np.array(s['bone_globals']),{n:skin(p['v'],p['j'],p['w'],np.array(s['bone_globals'])@ib) for n,p in parts.items()}) for s in samples]
 rows=[]
 for plate,(v,t) in enumerate(groups):
  for mode in ['nearest-body','nearest-upperarm']:
   valid=np.ones(len(body['v']),bool) if mode=='nearest-body' else np.sum(np.where(np.isin(body['j'],[50,51]),body['w'],0),axis=1)>.25
   ids=np.flatnonzero(valid);tree=cKDTree(body['v'][valid]);_,near=tree.query(v,k=1);anchors=np.unique(ids[near])
   # Bound diagnostic anchor count with a deterministic coordinate-order subset.
   anchors=anchors[np.linspace(0,len(anchors)-1,min(len(anchors),96)).astype(int)];a=body['v'][anchors].astype(float)
   witness=[]
   for label,poses,posed in prepared:
    b=posed['Rama warm skin'][anchors];matrix=rigid_fit(a,b);moved=transform(v,matrix)
    residual=np.linalg.norm(transform(a,matrix)-b,axis=1);result=contacts(moved,t,parts,posed)
    witness.append({'pose':label,'contacts':result,'support_maximum_rigid_residual_m':float(residual.max()),'maximum_distance_from_rigid50_m':float(np.linalg.norm(moved-transform(v,poses[50]@ib[50]),axis=1).max()),'matrix':matrix.tolist()})
   counts={n:sum(row['contacts'][n]['crossings'] for row in witness) for n in parts}
   row={'plate':plate,'mode':mode,'source_support_vertex_ids':anchors.tolist(),'crossing_pairs':counts,'poses':witness};rows.append(row)
   print(plate,mode,len(anchors),counts,flush=True)
   out.write_text(json.dumps({'schema':1,'complete':False,'script_sha256':sha(__file__),'rows':rows},indent=2)+'\n')
 out.write_text(json.dumps({'schema':1,'complete':True,'script_sha256':sha(__file__),'rows':rows,'elapsed_s':time.monotonic()-began,'scope':'Rigid least-squares support-frame diagnostic; no new asset/controller/clearance acceptance.'},indent=2)+'\n')
if __name__=='__main__':main()
