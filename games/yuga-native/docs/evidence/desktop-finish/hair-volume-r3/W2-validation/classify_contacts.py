"""Classify rest-space contact locations; orientation is a heuristic, not visibility."""
from pathlib import Path
import argparse,importlib.util,json,time
import numpy as np
from scipy.spatial import cKDTree
import validate_geometry as base

def classify(a,b,refmap,faceids,probe):
 ac=a.mean(1);bc=b.mean(1);ar=np.linalg.norm(a-ac[:,None],axis=2).max(1);br=np.linalg.norm(b-bc[:,None],axis=2).max(1)
 groups={};pairs=0
 for low,high in zip([0,.005,.01,.02,.05,.1],[.005,.01,.02,.05,.1,np.inf]):
  selected=np.flatnonzero((br>=low)&(br<high))
  if not len(selected):continue
  tree=cKDTree(bc[selected])
  for begin in range(0,len(a),256):
   lists=tree.query_ball_point(ac[begin:begin+256],ar[begin:begin+256]+br[selected].max()+1e-8)
   ia=np.repeat(np.arange(begin,min(begin+256,len(a))),[len(x)for x in lists])
   if not len(ia):continue
   ib=selected[np.concatenate(lists).astype(int)]
   lo=np.maximum(a[ia].min(1)-b[ib].max(1),b[ib].min(1)-a[ia].max(1));keep=np.all(lo<=1e-8,axis=1);ia=ia[keep];ib=ib[keep]
   for start in range(0,len(ia),8192):
    aa=ia[start:start+8192];bb=ib[start:start+8192];at=a[aa];bt=b[bb];cross=np.zeros(len(aa),bool)
    for k in range(3):cross|=probe.edge_cross(at[:,k],at[:,(k+1)%3],bt)|probe.edge_cross(bt[:,k],bt[:,(k+1)%3],at)
    for i,j in zip(aa[cross],bb[cross]):
     pairs+=1;hair=a[i];other=b[j];center=hair.mean(0);normal=np.cross(hair[1]-hair[0],hair[2]-hair[0]);normal/=np.linalg.norm(normal)
     radial=center-np.array([0,1.765,.045]);radial/=np.linalg.norm(radial);dot=float(normal@radial);category='inward'if dot<-.3 else'outward'if dot>.3 else'tangential'
     name,rindex=refmap[j];key=name+' | '+category;depth=(other-center)@normal*1000
     row=groups.setdefault(key,dict(reference_name=name,orientation_heuristic=category,crossing_pairs=0,unique_hair_triangles=set(),bounds_min=center.copy(),bounds_max=center.copy(),max_local_plane_span_mm=0,witness=None))
     row['crossing_pairs']+=1;row['unique_hair_triangles'].add(int(i));row['bounds_min']=np.minimum(row['bounds_min'],center);row['bounds_max']=np.maximum(row['bounds_max'],center)
     span=float(depth.max()-depth.min())
     if row['witness']is None or span>row['max_local_plane_span_mm']:
      row['max_local_plane_span_mm']=span;row['witness']=dict(hair_triangle_index=int(i),source_face_index=int(faceids[i]),reference_triangle_index=int(rindex),centroid_m=center.tolist(),hair_normal=normal.tolist(),radial_dot=dot,reference_vertex_signed_offsets_mm=depth.tolist(),hair_triangle=hair.tolist(),reference_triangle=other.tolist())
 for row in groups.values():row['unique_hair_triangles']=len(row['unique_hair_triangles']);row['bounds_min']=row['bounds_min'].tolist();row['bounds_max']=row['bounds_max'].tolist()
 return dict(crossing_pairs=pairs,groups=list(groups.values()))

def main():
 p=argparse.ArgumentParser();p.add_argument('--geometry',type=Path,required=True);p.add_argument('--part',type=int);p.add_argument('--output',type=Path,required=True);args=p.parse_args();assert not args.output.exists();started=time.monotonic()
 data=base.read(args.geometry);part=data['parts'][args.part]if'parts'in data else data;v=np.array(part['vertices']);t,f=base.triangulate(part['faces']);refs=base.read(base.REFERENCE)['reference_meshes'];targets=[];mapping=[]
 for ref in refs:
  rv=np.array(ref['vertices']);rt=np.array(ref['faces']);targets.append(rv[rt]);mapping.extend((ref['name'],i)for i in range(len(rt)))
 spec=importlib.util.spec_from_file_location('contact_probe',base.PROBE);probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
 result=classify(v[t],np.concatenate(targets),mapping,f,probe)
 result.update(geometry_sha256=base.sha(args.geometry),checker_sha256=base.sha(__file__),reference_sha256=base.sha(base.REFERENCE),probe_sha256=base.sha(base.PROBE),part=part['name'],elapsed_seconds=time.monotonic()-started,scope='Rest-space crossing location census. Radial normal classification is a head-centered orientation heuristic, not visibility, enclosure or global penetration depth. Local signed plane span is not penetration depth. Hardware contacts remain diagnostic until actual views. No model edits, pose or art acceptance.')
 args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['part','crossing_pairs','elapsed_seconds']}));print([(r['reference_name'],r['orientation_heuristic'],r['crossing_pairs'])for r in result['groups']])
if __name__=='__main__':main()
