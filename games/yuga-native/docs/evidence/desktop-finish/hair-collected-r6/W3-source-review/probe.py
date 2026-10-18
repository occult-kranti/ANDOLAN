"""Small independent stored-array/plane/one-contact check; no engine or broad replay."""
from pathlib import Path
import collections, copy, hashlib, json, struct
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ART = ROOT / 'art/hero-finish/hair-collected-r6'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class Glb:
    def __init__(self, p):
        self.path=p;data=p.read_bytes();magic,version,length=struct.unpack_from('<III',data)
        assert magic==0x46546c67 and version==2 and length==len(data)
        count,kind=struct.unpack_from('<II',data,12);assert kind==0x4e4f534a
        self.doc=json.loads(data[20:20+count]);offset=20+count
        n,kind=struct.unpack_from('<II',data,offset);assert kind==0x004e4942
        self.bin=data[offset+8:offset+8+n]
    def array(self, i):
        a=self.doc['accessors'][i];v=self.doc['bufferViews'][a['bufferView']]
        assert 'sparse' not in a
        dtype=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        start=v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.ndarray((a['count'],n),dtype,buffer=self.bin,offset=start,strides=(v.get('byteStride',n*dtype.itemsize),dtype.itemsize)).copy()
def plane_loop(v,t,y):
    segments=[]
    for triangle in v[t]:
        hits=[]
        for i in range(3):
            a,b=triangle[i],triangle[(i+1)%3]
            if (a[1]-y)*(b[1]-y)<0:
                hits.append(a+(b-a)*(y-a[1])/(b[1]-a[1]))
        if len(hits)==2:segments.append(hits)
    graph=collections.defaultdict(set)
    for a,b in segments:
        ka,kb=tuple(np.round(a,8)),tuple(np.round(b,8))
        if ka!=kb: graph[ka].add(kb);graph[kb].add(ka)
    unseen=set(graph);components=[]
    while unseen:
        stack=[unseen.pop()];seen=set(stack)
        while stack:
            for p in graph[stack.pop()]:
                if p not in seen:seen.add(p);unseen.discard(p);stack.append(p)
        components.append(seen)
    points=np.array([p for s in segments for p in s])
    return dict(plane_y_m=y,width_m=float(np.ptp(points[:,0])),depth_m=float(np.ptp(points[:,2])),
        segments=len(segments),connected_components=len(components),endpoint_degrees=sorted(set(map(len,graph.values()))),
        graph_merge_precision_m=1e-8,closed_single_loop=len(components)==1 and all(len(x)==2 for x in graph.values()))
def crossing(a,b):
    for source,target,reverse in [(a,b,False),(b,a,True)]:
        for edge in range(3):
            p,q=source[edge],source[(edge+1)%3];e1,e2=target[1]-target[0],target[2]-target[0]
            mat=np.column_stack([q-p,-e1,-e2])
            if abs(np.linalg.det(mat))<1e-14:continue
            x=np.linalg.solve(mat,target[0]-p);tt,u,w=x
            if 1e-7<tt<1-1e-7 and u>1e-7 and w>1e-7 and u+w<1-1e-7:
                return dict(edge=int(edge),edge_on_knot=reverse,t=float(tt),barycentric=[float(1-u-w),float(u),float(w)],point=(p+tt*(q-p)).tolist())
    return None
def main():
    receipt=ROOT/'docs/evidence/desktop-finish/hair-collected-r6/W2/receipt.json'
    assert sha(receipt)=='4e2c12b95c9e02cc1822a26c6b2f2acde31abf34eec863327472ca0b61777059'
    m=json.loads((ART/'candidate-r1/manifest.json').read_text());rows=[]
    for level,row in m['levels'].items():
        old,g=Glb(Path(row['source'])),Glb(Path(row['output']))
        assert sha(g.path)==row['output_sha256'] and sha(old.path)==row['source_sha256']
        assert g.bin[:len(old.bin)]==old.bin
        before,after=copy.deepcopy(old.doc),copy.deepcopy(g.doc)
        after['accessors']=after['accessors'][:len(before['accessors'])];after['bufferViews']=after['bufferViews'][:len(before['bufferViews'])]
        after['meshes'][2]['primitives'][0]=before['meshes'][2]['primitives'][0];after['buffers']=before['buffers'];assert before==after
        pr=g.doc['meshes'][2]['primitives'][0];oldpr=old.doc['meshes'][2]['primitives'][0]
        attrs={k:g.array(i)for k,i in pr['attributes'].items()};n=row['retained_vertices'];used=np.array(row['retained_source_rows']);nt=row['retained_triangles']
        assert all(attrs[k][:n].tobytes()==old.array(i)[used].tobytes()for k,i in oldpr['attributes'].items())
        skin=g.doc['skins'][0];names=[g.doc['nodes'][i]['name']for i in skin['joints']];assert len(names)==164 and names[104]=='head'
        assert np.all(attrs['JOINTS_0'][n:]==[104,0,0,0]) and np.all(attrs['WEIGHTS_0'][n:]==[1,0,0,0])
        v=attrs['POSITION'].astype(float);tri=g.array(pr['indices']).reshape(-1,3);scalp=tri[nt:nt+row['parts'][0]['triangles']]
        knot=tri[:nt][np.all(v[tri[:nt],1]>1.854,axis=1)];knot_y=float(v[np.unique(knot),1].min())
        section=plane_loop(v,scalp,knot_y);assert section['closed_single_loop'] and section['width_m']>.06
        # Challenge the first far report witness, which has a degenerate knot face.
        a=v[scalp];b=v[knot];area_a=np.linalg.norm(np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]),axis=1)/2
        area_b=np.linalg.norm(np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]),axis=1)/2
        valid_a=np.flatnonzero(area_a>1e-12);valid_b=np.flatnonzero(area_b>1e-12)
        lo=b.min(1);hi=b.max(1);witness=None;examined=0
        for i in valid_a:
            options=valid_b[np.all(hi[valid_b]>=a[i].min(0),axis=1)&np.all(lo[valid_b]<=a[i].max(0),axis=1)]
            for j in options:
                examined+=1;hit=crossing(a[i],b[j])
                if hit:
                    ids=np.r_[scalp[i],knot[j]]
                    assert np.all(attrs['JOINTS_0'][ids]==[104,0,0,0]) and np.all(attrs['WEIGHTS_0'][ids]==[1,0,0,0]) and np.all(attrs['COLOR_0'][ids,3]==0)
                    witness=dict(**hit,scalp_triangle=int(i),knot_triangle=int(j),scalp_vertices=scalp[i].tolist(),knot_vertices=knot[j].tolist(),
                        scalp_area_m2=float(area_a[i]),knot_area_m2=float(area_b[j]),scalp_points=a[i].tolist(),knot_points=b[j].tolist(),
                        both_fully_anchored_head104=True,strict_interior_edge_crossing=True)
                    break
            if witness:break
        assert witness
        rows.append(dict(level=level,candidate_sha256=sha(g.path),parent_sha256=sha(old.path),accepted_parent_BIN_prefix_exact=True,
            nonhair_JSON_exact=True,retained_attribute_byte_fields=len(attrs),retained_attributes_exact=True,skin_head_name=names[104],joint_count=len(names),
            exact_plane=section,nondegenerate_attachment_witness=witness,candidate_pairs_examined=examined,
            inherited_degenerate_knot_triangles=int((area_b<=1e-12).sum())))
    (HERE/'stored-review.json').write_text(json.dumps(dict(scope='Independent small read-only stored-array preservation, one connected knot-plane section and one nondegenerate anchored attachment witness perLOD. No broad contacts/pose/engine/import/pixel rerun.',
        source_receipt_sha256=sha(receipt),reviewer_script_sha256=sha(Path(__file__)),passed=True,levels=rows),indent=2)+'\n')
    print(json.dumps([dict(level=r['level'],width_mm=r['exact_plane']['width_m']*1000,connected=r['exact_plane']['closed_single_loop'],pairs_examined=r['candidate_pairs_examined'],nondegenerate_join=True)for r in rows]))
if __name__=='__main__':main()
