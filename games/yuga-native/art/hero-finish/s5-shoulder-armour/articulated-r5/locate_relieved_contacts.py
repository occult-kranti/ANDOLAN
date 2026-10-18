"""Find contact locations on relieved plates with ordinary rigid attachments."""
import gzip,json,sys,time
from pathlib import Path
import numpy as np
from fit_articulation import ROOT,GLB,prepare_geometry,transform,collider_parts,skin,sha
from diagnose_contacts import crossing_faces
HERE=Path(__file__).resolve().parent

def main():
 out=HERE/'relieved-contact-locations-r1.json';assert not out.exists();began=time.monotonic()
 g=GLB(ROOT/'assets/heroes/rama-hero.glb');ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
 _,groups=prepare_geometry('far',g,ib);parts=collider_parts(g)
 selected={n:p for n,p in parts.items() if n in ['Rama warm skin','Cobalt handwoven silk','Cobalt lotus brocade']}
 tape=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()))
 samples=[tape['samples'][i] for i in sorted(set([0,347]+list(range(0,348,29))))];rows=[]
 for s in samples:
  poses=np.array(s['bone_globals']);posed={n:skin(p['v'],p['j'],p['w'],poses@ib)[p['tri']] for n,p in selected.items()}
  for plate,(v,t) in enumerate(groups):
   for bone in ([49,50] if plate==0 else [50,51]):
    moved=transform(v,poses[bone]@ib[bone]);local=transform(v,ib[50]);found={}
    for name,tri in posed.items():
     ids,count=crossing_faces(moved[t],tri)
     if len(ids):
      p=local[np.unique(t[ids])];angles=np.degrees(np.arctan2(p[:,0],p[:,2]))
      found[name]={'crossings':count,'axial_m':[float(p[:,1].min()),float(p[:,1].max())],'angular_degrees':[float(angles.min()),float(angles.max())]}
    rows.append({'pose':s['id'],'plate':plate,'bone':bone,'contacts':found})
    if found:print(s['id'],plate,bone,found,flush=True)
 out.write_text(json.dumps({'schema':1,'script_sha256':sha(__file__),'rows':rows,'elapsed_s':time.monotonic()-began},indent=2)+'\n')
if __name__=='__main__':main()
