"""Read-only bounded floor topology and recorded-camera depth audit. No engine."""
from pathlib import Path
from collections import defaultdict
import hashlib, itertools, json, math, struct
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GLB = ROOT / 'assets/environment/lanka_courtyard.glb'
CAMERA = ROOT / 'docs/evidence/desktop-finish/G0/W1-title-floor-normal-r1/baseline/originals/00-title.json'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def triangles():
    raw = GLB.read_bytes()
    length, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    document = json.loads(raw[20:20+length])
    offset = 20+length
    size, kind = struct.unpack_from('<II', raw, offset)
    assert kind == 0x004E4942
    binary = raw[offset+8:offset+8+size]
    def accessor(index):
        a = document['accessors'][index]; v = document['bufferViews'][a['bufferView']]
        dtype = {5121:'u1', 5123:'<u2', 5125:'<u4', 5126:'<f4'}[a['componentType']]
        width = {'SCALAR':1, 'VEC2':2, 'VEC3':3, 'VEC4':4}[a['type']]
        assert 'sparse' not in a and 'byteStride' not in v
        return np.frombuffer(binary, dtype=dtype, count=a['count']*width,
                             offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape((-1,width))
    result = []
    # Exported source has identity transforms: verify rather than assuming TRS.
    for node in document['nodes']:
        if not any(part in node.get('name','') for part in ['FLOOR_', 'Limestone_mortar', 'Quiet_stone_inlay']): continue
        assert not any(k in node for k in ['translation','rotation','scale','matrix','children'])
        for primitive in document['meshes'][node['mesh']]['primitives']:
            assert primitive.get('mode',4) == 4
            positions = accessor(primitive['attributes']['POSITION']).astype(np.float64)
            indices = accessor(primitive['indices']).reshape(-1,3)
            result.append((node['name'], positions[indices]))
    return result

def key(triangle):
    return tuple(sorted(tuple(int(round(float(c)*1e6)) for c in point) for point in triangle))

def duplicate_faces(groups):
    seen = {}; duplicates = []
    for name, faces in groups:
        for index, tri in enumerate(faces):
            k = key(tri)
            if k in seen: duplicates.append([seen[k], [name,index]])
            else: seen[k] = [name,index]
    return duplicates

def cross(a,b):return a[0]*b[1]-a[1]*b[0]

def area(poly):
    return abs(sum(cross(poly[(i+1)%len(poly)]-poly[0],poly[i]-poly[0]) for i in range(1,len(poly)-1))*.5) if len(poly)>2 else 0.

def intersection_area(a,b):
    # Sutherland-Hodgman, CCW clipping triangle. Boundary contact has zero area.
    b = list(b)
    if float(cross(b[1]-b[0],b[2]-b[0])) < 0: b.reverse()
    poly = list(a)
    for index in range(3):
        edge0,edge1 = b[index],b[(index+1)%3]
        result=[]
        for j in range(len(poly)):
            start,end = poly[j-1],poly[j]
            ds=float(cross(edge1-edge0,start-edge0)); de=float(cross(edge1-edge0,end-edge0))
            if (ds>=-1e-10) != (de>=-1e-10): result.append(start+(end-start)*(ds/(ds-de)))
            if de>=-1e-10: result.append(end)
        poly=result
        if not poly: break
    return float(area(poly))

def coplanar_top_overlaps(groups):
    records=[]; cells=defaultdict(list); pairs=set(); hits=[]
    for name,faces in groups:
        for index,tri in enumerate(faces):
            # Horizontal surfaces only. Explicitly excludes bevel/sloped-inlay intersections.
            if np.ptp(tri[:,1])>1e-6: continue
            projected=tri[:,[0,2]]
            if area(list(projected)) < 1e-10: continue
            y=round(float(tri[0,1])*1e6)
            lo=np.floor(projected.min(axis=0)/2).astype(int); hi=np.floor(projected.max(axis=0)/2).astype(int)
            row=len(records); records.append((name,index,projected))
            for x in range(lo[0],hi[0]+1):
                for z in range(lo[1],hi[1]+1):cells[(y,x,z)].append(row)
    for entries in cells.values():
        for i,j in itertools.combinations(entries,2):
            pair=(i,j)
            if pair in pairs: continue
            pairs.add(pair)
            a,b=records[i],records[j]
            if np.any(a[2].max(axis=0)<=b[2].min(axis=0)+1e-7) or np.any(b[2].max(axis=0)<=a[2].min(axis=0)+1e-7):continue
            overlap=intersection_area(a[2],b[2])
            if overlap>1e-8:hits.append({'a':[a[0],a[1]],'b':[b[0],b[1]],'area_m2':overlap})
    return {'horizontal_triangles':len(records),'unique_nearby_pairs':len(pairs),'positive_area_hits':hits}

def depths(groups):
    original=json.loads(CAMERA.read_text()); camera=original['camera']
    basis=np.array(camera['transform'][:3],dtype=float).T; origin=np.array(camera['transform'][3],dtype=float)
    width,height=original['framebuffer_size']; tangent=math.tan(math.radians(camera['fov'])*.5)
    floor=0.; foundation=max(float(tri[:,:,1].max()) for name,tri in groups if 'mortar' in name)
    near,far=camera['near'],camera['far']
    def reverse(z):return near*(far-z)/(z*(far-near))
    samples=[]
    def project(point):
        local=basis.T@(point-origin); z=-local[2]
        return np.array([(local[0]/(z*tangent*(width/height))+1)*width*.5,(1-local[1]/(z*tangent))*height*.5])
    for x,y in [(500,320),(900,320),(900,450),(530,490)]:
        direction=basis@np.array([(2*(x+.5)/width-1)*(width/height)*tangent,(1-2*(y+.5)/height)*tangent,-1.])
        z0=(floor-origin[1])/direction[1];z1=(foundation-origin[1])/direction[1]
        d0,d1=reverse(z0),reverse(z1)
        ulps=abs(struct.unpack('<I',struct.pack('<f',d0))[0]-struct.unpack('<I',struct.pack('<f',d1))[0])
        point=origin+direction*z0
        footprints={str(size):{axis:float(np.linalg.norm(project(point+vector*size)-project(point))) for axis,vector in [('world_X',np.array([1.,0.,0.])),('world_Z',np.array([0.,0.,1.]))]} for size in [.004,.01,.018]}
        samples.append({'pixel':[x,y],'floor_world':(origin+direction*z0).tolist(),'eye_depth_m':[z0,z1],
                        'projected_world_widths_px':footprints,'reverse_Z_depth':[d0,d1],'D32_float32_ULPs':ulps,'D24_UNORM_steps':abs(d0-d1)*(2**24-1)})
    return {'camera_receipt':str(CAMERA.relative_to(ROOT)),'camera_sha256':sha(CAMERA),'camera':camera,
            'framebuffer_size':[width,height],'floor_y':floor,'foundation_top_y':foundation,
            'formula':'KEEP_HEIGHT perspective pixel-centre ray, local z=-1; reverseZ=n*(f-z)/(z*(f-n)); assumes recorded perspective Camera3D, no jitter. Actual depth attachment not logged: bound D32 float and D24 UNORM, do not identify actual format.',
            'samples':samples}

def main():
    groups=triangles()
    trial=np.array([[0.,0.,0.],[1.,0.,0.],[0.,0.,1.]])
    assert len(duplicate_faces([('original',np.array([trial])),('injected',np.array([trial]))]))==1
    assert abs(intersection_area(trial[:,[0,2]],trial[:,[0,2]])-.5)<1e-9
    assert intersection_area(trial[:,[0,2]],trial[:,[0,2]]+10)==0
    shifted=trial.copy();shifted[:,0]+=.1
    assert coplanar_top_overlaps([('a',np.array([trial])),('injected',np.array([shifted]))])['positive_area_hits']
    rows=[]
    for name,faces in groups:
        rows.append({'node':name,'triangles':len(faces),'bounds_min':faces.min(axis=(0,1)).tolist(),'bounds_max':faces.max(axis=(0,1)).tolist()})
    overlaps=coplanar_top_overlaps(groups)
    result={'source_glb':str(GLB.relative_to(ROOT)),'source_sha256':sha(GLB),'geometry':rows,
            'duplicate_triangles_quantized_1um':duplicate_faces(groups),'horizontal_coplanar_audit':overlaps,
            'counterexamples':'Injected exact duplicate, shifted positive-area coplanar triangle, and separated triangle all detected correctly.',
            'projection':depths(groups),
            'limits':'No arbitrary sloped triangle self-intersection scan, driver raster trace, temporal shimmer or actual depth-format proof. Inlay crossings of y=0 are local noncoplanar geometry, reported separately in prior bounds audit. No scene, shader, AA, lighting, normal or foundation edits.'}
    (HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'nodes':len(rows),'triangles':sum(r['triangles'] for r in rows),'duplicates':len(result['duplicate_triangles_quantized_1um']),'coplanar_positive_area':len(overlaps['positive_area_hits'])}))

if __name__=='__main__':main()
