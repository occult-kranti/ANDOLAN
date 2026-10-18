"""External plate hinges derived from existing shoulder frame; rigid form."""
import gzip,json
from pathlib import Path
import sys,time
import numpy as np
from fit_articulation import ROOT,GLB,prepare_geometry,transform,collider_parts,skin,contacts,deform,sha
HERE=Path(__file__).resolve().parent

def main():
    out=HERE/'hinge-trials-r1.json';assert not out.exists();started=time.monotonic()
    g=GLB(ROOT/'assets/heroes/rama-hero.glb');ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rest=np.linalg.inv(ib)
    _,groups=prepare_geometry('far',g,ib)
    source=collider_parts(g);parts={k:v for k,v in source.items() if k in ['Rama warm skin','Cobalt handwoven silk','Cobalt lotus brocade']}
    tape=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()));samples=[tape['samples'][i] for i in sorted(set([0,347]+list(range(0,348,29))))]
    prepared=[(s['id'],np.array(s['bone_globals']),{name:skin(p['v'],p['j'],p['w'],np.array(s['bone_globals'])@ib) for name,p in parts.items()}) for s in samples]
    rows=[]
    # Cap spine attachment is tested separately; no claim that it is final.
    for plate in range(3):
        v,t=groups[plate]
        options=[(47,0.,0.),(48,0.,0.)] if plate==0 else [(49,offset,weight) for offset in [.03,.06,.09] for weight in [.65,1.]]
        for parent,offset,weight in options:
            witness=[]
            for label,poses,posed in prepared:
                if plate==0:matrix=poses[parent]@ib[parent]
                else:
                    matrix=deform(poses,ib,weight,'swing')
                    hinge=transform(np.array([[0,.025 if plate==1 else .11,offset]]),rest[50])[0]
                    parent_matrix=poses[parent]@ib[parent]
                    matrix[:3,3]=transform(hinge[None,:],parent_matrix)[0]-matrix[:3,:3]@hinge
                result=contacts(transform(v,matrix),t,parts,posed)
                witness.append({'pose':label,'contacts':result})
            counts={name:sum(row['contacts'][name]['crossings'] for row in witness) for name in parts}
            row={'plate':plate,'parent':parent,'hinge_radial_offset_m':offset,'swing_weight':weight,'crossing_pairs':counts,'poses':witness};rows.append(row)
            print(plate,parent,offset,weight,counts,flush=True)
            out.write_text(json.dumps({'schema':1,'complete':False,'script_sha256':sha(__file__),'rows':rows},indent=2)+'\n')
    out.write_text(json.dumps({'schema':1,'complete':True,'script_sha256':sha(__file__),'rows':rows,'elapsed_s':time.monotonic()-started,'scope':'Rigid existing-frame hinge diagnostic on13poses/far geometry. No asset or runtime acceptance.'},indent=2)+'\n')
if __name__=='__main__':main()
