"""Locate the two distinct dense-pose contacts before a bounded shape repair."""
import argparse,gzip,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from build_armour import ROOT,GLB,sha
from check_source import candidate,transform,collider_parts
sys.path.insert(0,str(HERE.parent/'articulated-r5'))
from verify_bind_space import skin
from diagnose_contacts import crossing_faces

def main():
 out=HERE/'dense-contact-location-r2.json';assert not out.exists()
 source=Path('/tmp/yuga-desktop-recovery-r1/current-project/assets/heroes/rama-hero.glb');g=GLB(source);ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rest=np.linalg.inv(ib)
 v,t=candidate(GLB(HERE/'candidate-r2/shoulder-armour-near.glb'));local=transform(v,ib[50]@rest[49]);manifest=json.loads((HERE/'candidate-r2/source-manifest.json').read_text());groups=[];offset=0
 for material in range(3):
  for c in manifest['levels']['near']['components']:
   if c['material']!=material:continue
   faces=t[np.all((t>=offset)&(t<offset+c['vertices']),axis=1)];groups.append((c['name'],faces));offset+=c['vertices']
 body=collider_parts(g)['Rama warm skin'];tape=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()))['samples'];rows=[]
 for sample in [s for s in tape if s['id']in ['piercing_dawn-pitch0.0-step23','dawn_volley-pitch0.0-step33']]:
  poses=np.array(sample['bone_globals']);posed=skin(body['v'],body['j'],body['w'],poses@ib)[body['tri']];moved=transform(v,poses[49])
  for name,faces in groups:
   ids,count=crossing_faces(moved[faces],posed)
   if len(ids):
    p=local[np.unique(faces[ids])];angles=np.degrees(np.arctan2(p[:,0],p[:,2]));r={'pose':sample['id'],'component':name,'pairs':count,'axial_range_m':[float(p[:,1].min()),float(p[:,1].max())],'angle_range_degrees':[float(angles.min()),float(angles.max())]};rows.append(r);print(r,flush=True)
 out.write_text(json.dumps({'schema':1,'script_sha256':sha(__file__),'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
