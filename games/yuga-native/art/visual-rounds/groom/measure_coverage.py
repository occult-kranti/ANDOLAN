"""Deterministic source-geometry witnesses for the original exposed temple gap."""
import argparse,json,math
from pathlib import Path
import numpy as np
from build_groom import GLB,Skull,ORIGIN,sha
from validate_groom import surface

def hits(tri,d):
 a=tri[:,0];e1=tri[:,1]-a;e2=tri[:,2]-a;t=ORIGIN-a;h=np.cross(d,e2);det=np.sum(e1*h,axis=1)
 inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-12);u=np.sum(t*h,axis=1)*inv;q=np.cross(t,e1);v=(q@d)*inv;dist=np.sum(e2*q,axis=1)*inv
 return dist[(abs(det)>1e-12)&(u>=0)&(v>=0)&(u+v<=1)&(dist>0)]

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();m=json.loads(a.manifest.read_text());item=m['levels']['near'];base=GLB(item['source']);candidate=GLB(item['output']);skull=Skull(base)
 directions=[]
 for side in [-1,1]:
  for theta in np.linspace(1.25,1.85,13):
   for elevation in np.linspace(.025,.17,8):directions.append([side*math.sin(theta)*math.cos(elevation),math.sin(elevation),math.cos(theta)*math.cos(elevation)])
 directions=np.array(directions);body=skull.rays(directions);radius=np.linalg.norm(body-ORIGIN,axis=1);rows=[]
 for name,g in [('baseline',base),('candidate',candidate)]:
  v,t,_=surface(g,2,0);tri=v[t];tri=tri[np.any(tri[:,:,1]>1.76,axis=1)];distance=[];covered=[]
  for d,r in zip(directions,radius):
   h=hits(tri,d);within=h[(h>=r-.0005)&(h<=r+.025)]
   distance.append(float(within.min()-r)if len(within)else None);covered.append(bool(len(within)))
  rows.append({'name':name,'sha256':sha(g.path),'rays':len(directions),'covered_within_25mm_of_actual_skull':sum(covered),'coverage':covered,'nearest_offset_m':distance})
 result={'task':'R3-08','passed':rows[1]['covered_within_25mm_of_actual_skull']>rows[0]['covered_within_25mm_of_actual_skull'] and rows[1]['covered_within_25mm_of_actual_skull']==len(directions),'measurements':rows,'target':'Bilateral temple angle 1.25..1.85rad, elevation .025.. .17rad from actual skull interior','directions':directions.tolist(),'actual_skull_witness_bounds':[body.min(0).tolist(),body.max(0).tolist()],'scope':'208 predetermined rays address the baseline bare temple wedge. This is a geometry coverage measure, not a pixel review, visible strand quality metric or whole-head coverage proof.','script_sha256':sha(__file__)}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'coverage_counts':[r['covered_within_25mm_of_actual_skull']for r in rows],'rays':len(directions)}))
 if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
