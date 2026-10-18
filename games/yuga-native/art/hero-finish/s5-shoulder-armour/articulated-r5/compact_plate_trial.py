"""Simplified cap and short overlapping lames; ordinary bone attachments only."""
import gzip,json,math,time
from pathlib import Path
import numpy as np
import fit_articulation as fit
from fit_articulation import ROOT,GLB,transform,collider_parts,skin,contacts,sha
HERE=Path(__file__).resolve().parent

def compact_surface(layer):
 starts=[-.005,.050,.088];ends=[.082,.112,.142];radii=[.111,.091,.076]
 def point(u,v):
  degrees=-5+50*u;theta=math.radians(degrees);end=ends[layer]+.005*math.cos(3*theta)+.004*math.cos(theta);s=starts[layer]*(1-v)+end*v
  radius=radii[layer]+.010*max(math.sin(theta),0)-.009*max(-math.sin(theta),0)+.009*math.sin(math.pi*v)-.006*v+.004*math.cos(theta)*math.sin(math.pi*v)
  radius=max(radius,float(fit.original.ENVELOPE([[s,degrees]])[0])+[.018,.012,.008][layer])
  return np.array([radius*math.sin(theta),s,radius*math.cos(theta)])
 return point

def main():
 out=HERE/'compact-plate-trial-r1.json';assert not out.exists();began=time.monotonic()
 g=GLB(ROOT/'assets/heroes/rama-hero.glb');ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
 fit.surface_fn=compact_surface;shapes,groups=fit.prepare_geometry('far',g,ib);source=collider_parts(g);parts={n:p for n,p in source.items() if n in ['Rama warm skin','Cobalt handwoven silk','Cobalt lotus brocade']}
 tape=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()));samples=[tape['samples'][i] for i in sorted(set([0,347]+list(range(0,348,29))))]
 prepared=[(s['id'],np.array(s['bone_globals']),{n:skin(p['v'],p['j'],p['w'],np.array(s['bone_globals'])@ib) for n,p in parts.items()}) for s in samples];rows=[]
 for plate,(v,t) in enumerate(groups):
  for bone in [49,50]:
   witness=[]
   for label,poses,posed in prepared:
    moved=transform(v,poses[bone]@ib[bone]);result=contacts(moved,t,parts,posed);witness.append({'pose':label,'contacts':result})
   counts={n:sum(row['contacts'][n]['crossings'] for row in witness) for n in parts};row={'plate':plate,'bone':bone,'crossing_pairs':counts,'poses':witness};rows.append(row);print(plate,bone,counts,flush=True)
   out.write_text(json.dumps({'schema':1,'complete':False,'script_sha256':sha(__file__),'rows':rows},indent=2)+'\n')
 out.write_text(json.dumps({'schema':1,'complete':True,'script_sha256':sha(__file__),'rows':rows,'elapsed_s':time.monotonic()-began,'shape':'Ordinary fixed-radius relief.50-degree outer arc; axial cap-.005..+.091, lames.050..+.121/.088..+.151m. No enlarged envelope, solver, or accepted art.'},indent=2)+'\n')
if __name__=='__main__':main()
