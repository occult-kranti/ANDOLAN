"""Focused independent GLB checks for the staged Rama mesh, materials and rig."""
import sys,json,struct,math,hashlib
from pathlib import Path
import numpy as np
TYPES={5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}
SIZES={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def read(path):
    raw=Path(path).read_bytes();assert raw[:4]==b'glTF';ln,kind=struct.unpack_from('<II',raw,12);d=json.loads(raw[20:20+ln]);off=20+ln;blen,btype=struct.unpack_from('<II',raw,off);return raw,d,raw[off+8:off+8+blen]
def accessor(doc,binary,i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dtype=np.dtype(TYPES[a['componentType']]);n=SIZES[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dtype.itemsize*n)
    arr=np.ndarray((a['count'],n),dtype=dtype,buffer=binary,offset=off,strides=(stride,dtype.itemsize)).copy()
    if a.get('normalized'):
        info=np.iinfo(dtype);arr=arr.astype(float)/info.max
    return arr

def main():
    p=Path(sys.argv[1]);raw,d,b=read(p);prims=[x for m in d['meshes'] for x in m['primitives']];checks=[]
    assert all(len(s['joints'])==164 for s in d['skins']);checks.append('164 joints in each exported skin')
    joints={d['nodes'][i]['name'] for s in d['skins'] for i in s['joints']};assert {'wrist.R','wrist.L','bowstring','eye.L','eye.R','spine05','foot.L','foot.R'}<=joints
    assert {'RamaHero','RamaBow'}<={n.get('name') for n in d['nodes']};checks.append('Separate hero and bow nodes; required contact bones present')
    expected={'idle','run','jump','fire','cast','cast1','cast2','cast3','defeat'};assert {a['name'] for a in d['animations']}==expected;checks.append('Nine retained baseline action names')
    triangles=verts=0;normerr=weighterr=0
    for p0 in prims:
        a=p0['attributes'];assert {'POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0'}<=set(a)
        positions=accessor(d,b,a['POSITION']);normals=accessor(d,b,a['NORMAL']);weights=accessor(d,b,a['WEIGHTS_0']);js=accessor(d,b,a['JOINTS_0']);idx=accessor(d,b,p0['indices'])
        assert np.isfinite(positions).all() and np.isfinite(normals).all() and np.isfinite(weights).all();assert np.min(weights)>=0 and np.max(js)<164;assert np.max(idx)<len(positions)
        err=float(np.max(np.abs(weights.sum(axis=1)-1)));assert err<.0001;weighterr=max(weighterr,err)
        ne=float(np.max(np.abs(np.linalg.norm(normals,axis=1)-1)));assert ne<.001;normerr=max(normerr,ne)
        if 'normalTexture' in d['materials'][p0['material']]:assert 'TANGENT' in a
        triangles+=len(idx)//3;verts+=len(positions)
    checks.extend(['Finite geometry, bounded indices and unit normals','Normalized four-influence skin weights','Normal-mapped primitives have tangent frames'])
    for image in d['images']:
        v=d['bufferViews'][image['bufferView']];payload=b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];assert payload.startswith((b'\x89PNG',b'\xff\xd8\xff'))
    checks.append('All image payloads embedded and recognized')
    result=dict(asset=str(p),sha256=hashlib.sha256(raw).hexdigest(),checks=checks,triangles=triangles,vertices=verts,materials=len(d['materials']),images=len(d['images']),joints=len(joints),maximumWeightSumError=weighterr,maximumNormalLengthError=normerr,limitations=['Structural tests do not accept likeness, deformation intersections or performance.'])
    print(json.dumps(result,indent=2));(p.parent/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
