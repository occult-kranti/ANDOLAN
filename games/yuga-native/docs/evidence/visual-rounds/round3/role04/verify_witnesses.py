from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'art/hero-rama-lod'));from glb_lod import GLB
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cuts(a,b):
 out=[]
 for side,(edges,tri)in enumerate([(a,b),(b,a)]):
  for edge in range(3):
   origin=edges[edge];direction=edges[(edge+1)%3]-origin;e1=tri[1]-tri[0];e2=tri[2]-tri[0];h=np.cross(direction,e2);det=e1@h
   if abs(det)<1e-15:continue
   diff=origin-tri[0];u=(diff@h)/det;q=np.cross(diff,e1);v=(direction@q)/det;t=(e2@q)/det
   if 1e-8<t<1-1e-8 and u>1e-8 and v>1e-8 and u+v<1-1e-8:out.append({'edge_side':side,'edge_index':edge,'t':float(t),'barycentric':[float(1-u-v),float(u),float(v)],'point':(origin+t*direction).tolist()})
 return out
old=GLB('/workspace/scratch/visual-round2/role-08/face-form-candidate-r6/candidate.glb');new=GLB('/workspace/scratch/visual-round3/role-08/groom-r6/rama-hero.glb');preserve=[]
for mi,pi,p in old.primitives():
 if mi==0 or(mi==2 and pi in [1,3,4]):
  n=new.doc['meshes'][mi]['primitives'][pi];same=p==n and all(np.array_equal(old.array(idx),new.array(n['attributes'][name]))for name,idx in p['attributes'].items())and np.array_equal(old.array(p['indices']),new.array(n['indices']));preserve.append({'mesh':mi,'primitive':pi,'exact':same})
j=json.loads((OUT/'action-clearance.json').read_text());rows=[]
for s in j['samples']:
 w=s['gaps']['cloth'].get('minimum_bound_pair')
 if s['gaps']['cloth']['lower_bound_m']!=0:continue
 hits=cuts(np.array(w['first_xyz']),np.array(w['bow_xyz']));idx=w['first_triangle'];material='Ivory silk'if idx<32504 else 'Cobalt handwoven silk'if idx<74308 else 'Cobalt lotus brocade'
 rows.append({'sample':s['id'],'cloth_material':material,'strict_segment_triangle_intersections':hits,'confirmed_source_triangle_crossing':bool(hits)})
report={'task':'R3-04','source_sha256':{str(p):sha(p)for p in [Path(__file__),OUT/'action-clearance.json',old.path,new.path]},'preserved_primitive_arrays':preserve,'all_checked_cloth_bow_source_arrays_exact':all(r['exact']for r in preserve),'witnesses':rows,'confirmed_crossings':sum(r['confirmed_source_triangle_crossing']for r in rows),'scope':'Strict segment/triangle intersection of actual source-pose witness triangles; no secondary uniforms, runtime collision or pixel visibility claim. Original R2 and R3 cloth/bow arrays are exact, so these source replay crossings predate groom/material changes.'}
(OUT/'intersection-witnesses.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'confirmed_crossings':report['confirmed_crossings'],'source_exact':report['all_checked_cloth_bow_source_arrays_exact'],'samples':[r['sample']for r in rows]},indent=2))
