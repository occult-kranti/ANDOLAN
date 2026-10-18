"""Independent closed-volume topology/rest-reference tests; no Blender/render."""
from pathlib import Path
import argparse,gzip,hashlib,importlib.util,json,time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
PROJECT=Path(__file__).resolve().parents[5]
REFERENCE=PROJECT/'art/hero-finish/hair-sculpt-design/clay-r1/authoring-payload/seated-cage.json'
REFERENCE_SHA='b0a8ee2213b9ee7fc21285ab4884e6b270ff396d1abfaf94a7db8cab7f35eb99'
PROBE=PROJECT/'docs/evidence/visual-rounds/round3/role10/geometry_probe.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes())
def triangulate(faces):
    triangles=[];source=[]
    for i,f in enumerate(faces):
        for j in range(1,len(f)-1):triangles.append([f[0],f[j],f[j+1]]);source.append(i)
    return np.asarray(triangles,dtype=np.int64),np.asarray(source,dtype=np.int64)
def topology(v,t):
    edges=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);keys=np.sort(edges,axis=1)
    unique,inv,counts=np.unique(keys,axis=0,return_inverse=True,return_counts=True)
    balance=np.bincount(inv,weights=np.where(edges[:,0]<edges[:,1],1,-1),minlength=len(unique))
    graph=coo_matrix((np.ones(len(unique)),(unique[:,0],unique[:,1])),shape=(len(v),len(v)))
    components,_=connected_components(graph,directed=False)
    area=np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)*.5
    volume=float(np.einsum('ij,ij->i',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]])).sum()/6)
    return dict(components=int(components),boundary_edges=int(np.sum(counts==1)),nonmanifold_edges=int(np.sum(counts>2)),
                inconsistent_winding_edges=int(np.sum((counts==2)&(balance!=0))),minimum_triangle_area_m2=float(area.min()),
                degenerate_triangles=int(np.sum(area<=1e-12)),signed_volume_m3=volume)
def prepare_ray(tri,direction):
    d=np.array(direction,dtype=float);d/=np.linalg.norm(d);u=np.cross(d,[0,0,1.]);u/=np.linalg.norm(u);w=np.cross(d,u)
    axes=np.stack([d,u,w],axis=1);rotated=tri@axes
    e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h)
    inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-15)
    return dict(d=d,axes=axes,lo=rotated.min(1),hi=rotated.max(1),a=tri[:,0],e1=e1,e2=e2,h=h,det=det,inv=inv)
def inside(point,tri,direction,prepared=None):
    cache=prepare_ray(tri,direction)if prepared is None else prepared
    d,lo,hi=cache['d'],cache['lo'],cache['hi'];p=point@cache['axes']
    select=(hi[:,0]>p[0]+1e-9)&(lo[:,1]<=p[1]+1e-10)&(hi[:,1]>=p[1]-1e-10)&(lo[:,2]<=p[2]+1e-10)&(hi[:,2]>=p[2]-1e-10)
    if not np.any(select):return False
    e1,e2,h,det,inv=[cache[k][select]for k in ['e1','e2','h','det','inv']];s=point-cache['a'][select]
    a=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1);b=(q@d)*inv;t=np.einsum('ij,ij->i',e2,q)*inv
    valid=(abs(det)>1e-15)&(a>=-1e-9)&(b>=-1e-9)&(a+b<=1+1e-9)&(t>1e-8)
    distances=np.sort(t[valid]);count=0 if not len(distances)else 1+int(np.sum(np.diff(distances)>1e-7))
    return bool(count%2)
def reference_samples(ref):
    v=np.array(ref['vertices']);t=np.array(ref['faces']);_,weld=np.unique(np.round(v,7),axis=0,return_inverse=True);wt=weld[t]
    edges=np.concatenate([wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]]);n=int(weld.max()+1)
    _,labels=connected_components(coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(n,n)),directed=False)
    components=labels[wt[:,0]];area=np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)
    samples=[]
    for component in np.unique(components):
        eligible=np.flatnonzero((components==component)&(area>1e-12))
        if len(eligible):
            i=int(eligible[0]);samples.append(dict(reference_name=ref['name'],triangle_index=i,point=v[t[i]].mean(0).tolist()))
    return samples
def calibration(probe):
    v=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],dtype=float)
    t,_=triangulate([[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]])
    for direction in [[1,.371,.529],[.281,1,.613]]:
        assert inside(np.array([0.,0,0]),v[t],direction)
        assert not inside(np.array([2.,0,0]),v[t],direction)
    assert topology(v,t)['signed_volume_m3']==8
    return dict(triangle_distance=probe.selfcheck(),closed_cube_volume_m3=8,inside_outside_two_rays=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--geometry',type=Path,required=True);p.add_argument('--part',type=int);p.add_argument('--output',type=Path,required=True);p.add_argument('--topology-only',action='store_true');a=p.parse_args();assert not a.output.exists()
    started=time.monotonic();assert sha(REFERENCE)==REFERENCE_SHA;refs=read(REFERENCE)['reference_meshes'];d=read(a.geometry)
    part=d['parts'][a.part]if'parts'in d else d
    if'parts'in d:assert a.part is not None and len(d['parts'])==6
    v=np.asarray(part['vertices'],dtype=float);t,face_ids=triangulate(part['faces'])
    spec=importlib.util.spec_from_file_location('independent_triangle_narrow',PROBE);probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    result=dict(scope='Independent rest-space closed source/visible volume check; intentional hair-to-hair source overlap is excluded. No visual, pose, rig or runtime acceptance.',
                part=part['name'],geometry_sha256=sha(a.geometry),reference_sha256=REFERENCE_SHA,checker_sha256=sha(__file__),probe_sha256=sha(PROBE),
                calibration=calibration(probe),checks=[],complete=False)
    def checkpoint(name,passed,**facts):
        result['checks'].append(dict(name=name,passed=bool(passed),**facts));a.output.write_text(json.dumps(result,indent=2)+'\n')
    finite=np.isfinite(v).all();bounded=t.min()>=0 and t.max()<len(v)
    checkpoint('finite bounded complete triangles',finite and bounded,vertices=len(v),triangles=len(t))
    assert finite and bounded
    topo=topology(v,t);result['topology']=topo
    checkpoint('one closed consistently wound nondegenerate positive volume',topo['components']==1 and topo['boundary_edges']==0 and topo['nonmanifold_edges']==0 and topo['inconsistent_winding_edges']==0 and topo['degenerate_triangles']==0 and topo['signed_volume_m3']>0,**topo)
    if not a.topology_only:
        reference_triangles=[];reference_map=[];samples=[]
        for ref in refs:
            rv=np.array(ref['vertices']);rt=np.array(ref['faces']);reference_triangles.append(rv[rt]);reference_map.extend((ref['name'],i)for i in range(len(rt)));samples.extend(reference_samples(ref))
        targets=np.concatenate(reference_triangles);comparison=probe.compare(v[t],targets,band=.004)
        if comparison.get('witness_triangles'):
            i,j=comparison['witness_triangles'];comparison.update(source_face_index=int(face_ids[i]),reference_name=reference_map[j][0],reference_triangle_index=reference_map[j][1])
        result['reference_comparison']=comparison
        checkpoint('all protected parent reference triangles clear in rest',comparison['crossings']==0 and comparison['guaranteed_lower_bound_m']>=.0002,comparison=comparison)
        enclosed=[];ambiguous=[]
        if comparison['crossings']==0 and topo['boundary_edges']==0 and topo['nonmanifold_edges']==0:
            low,high=v.min(0),v.max(0)
            rays=[prepare_ray(v[t],direction)for direction in [[1,.371,.529],[.281,1,.613]]]
            for sample in samples:
                point=np.array(sample['point'])
                if np.any(point<low)or np.any(point>high):continue
                one=inside(point,v[t],[1,.371,.529],rays[0]);two=inside(point,v[t],[.281,1,.613],rays[1])
                if one and two:enclosed.append(sample)
                elif one!=two:ambiguous.append(sample)
            checkpoint('no protected connected reference surface enclosed without crossing',not enclosed and not ambiguous,enclosed=enclosed,ambiguous=ambiguous,protected_components_sampled=len(samples))
        else:result['containment']='Not classified because surface crossing or nonclosed geometry already fails.'
    result.update(complete=True,passed=all(c['passed']for c in result['checks']),elapsed_seconds=time.monotonic()-started)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(part=result['part'],passed=result['passed'],topology=topo,contact=result.get('reference_comparison'),elapsed_seconds=result['elapsed_seconds'])))
    raise SystemExit(0 if result['passed']else 1)
if __name__=='__main__':main()
