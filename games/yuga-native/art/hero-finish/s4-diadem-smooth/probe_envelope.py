"""Diagnostic global arc clearance, without GLB writes or envelope reshaping."""
import argparse,json
from pathlib import Path
import numpy as np
from build_candidate import ROOT,GLB,head_surfaces,ray_distance,unit
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
g=GLB(ROOT/'assets/heroes/rama-hero.glb');tri=head_surfaces(g)
rows=[]
for xr,zr,zc in [(.096,.125,.044),(.100,.130,.044),(.102,.132,.044),(.104,.134,.044)]:
 theta=np.linspace(0,2*np.pi,81);old=np.c_[.105*np.cos(theta),1.792+.003*np.cos(6*theta),.029-.137*np.sin(theta)]
 direction=unit(old-np.c_[np.zeros(81),old[:,1],np.full(81,.045)])
 front=np.clip((direction[:,2]+.05)/.90,0,1);front=front**3*(front*(6*front-15)+10)
 arc=np.c_[xr*np.cos(theta),np.full(81,1.792),zc-zr*np.sin(theta)];curve=arc*(1-front[:,None])+old*front[:,None]
 origins=np.c_[np.zeros(81),curve[:,1],np.full(81,.045)];r=np.linalg.norm(curve-origins,axis=1);directions=unit(curve-origins)
 support=np.array([ray_distance(o,d,tri) for o,d in zip(origins,directions)]);gap=r-support
 rows.append({'x_radius_m':xr,'z_radius_m':zr,'z_center_m':zc,'centerline_radial_gap_quantiles_m':np.quantile(gap,[0,.5,.95,1]).tolist(),'worst_rings':np.argsort(gap)[:8].tolist(),'centerline_radial_gaps_m':gap.tolist()})
 print(xr,zr,zc,'min_center_gap_mm',gap.min()*1000,'rings',np.argsort(gap)[:8].tolist(),flush=True)
a.output.write_text(json.dumps({'scope':'Ray diagnostic only; not full triangle acceptance. Global shape choices, no pointwise curve deformation.','rows':rows},indent=2)+'\n')
