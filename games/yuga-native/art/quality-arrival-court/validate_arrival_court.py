"""Source-independent exported glTF checks. Appearance remains a rendered gate."""
from pathlib import Path
import struct
import json
import hashlib
import sys
import math
from collections import Counter

HERE=Path(__file__).resolve().parent
COMPONENTS={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
WIDTHS={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}


def read(path):
    raw=path.read_bytes()
    magic,version,length=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and length==len(raw)
    offset=12;doc=None;binary=None
    while offset<len(raw):
        size,typ=struct.unpack_from('<I4s',raw,offset);offset+=8
        data=raw[offset:offset+size];offset+=size
        if typ==b'JSON':doc=json.loads(data)
        elif typ==b'BIN\0':binary=data
    assert doc and binary
    return raw,doc,binary


def accessor(doc,binary,index):
    a=doc['accessors'][index]
    assert 'sparse' not in a
    v=doc['bufferViews'][a['bufferView']]
    fmt,unit=COMPONENTS[a['componentType']]
    width=WIDTHS[a['type']]
    stride=v.get('byteStride',width*unit)
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from('<'+fmt*width,binary,offset+i*stride) for i in range(a['count'])]


def main():
    path=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'lotus-arrival-court.glb'
    raw,doc,binary=read(path)
    checks=[]
    assert not doc.get('skins') and not doc.get('animations') and not doc.get('cameras')
    assert 'KHR_lights_punctual' not in doc.get('extensions',{})
    checks.append('Static modular environment; no skin/animation/camera/embedded lights')
    names={n.get('name') for n in doc['nodes']}
    assert {'LotusGate','DiyaLeft','DiyaRight','Threshold'}<=names
    checks.append('Four named independent modules, with unchanged local origin')
    assert len(doc['materials'])==5
    material_names={m['name'] for m in doc['materials']}
    assert material_names=={'Honed warm limestone','Cast aged bronze','Quiet teal ceramic','Recess and oil','Warm oil flame'}
    for m in doc['materials']:
        assert m.get('alphaMode','OPAQUE')=='OPAQUE'
        assert not m.get('doubleSided',False),m['name']
        pbr=m['pbrMetallicRoughness']
        if m['name'] not in ['Cast aged bronze']:
            assert pbr.get('metallicFactor',1)==0,m['name']
        else:assert .75<=pbr['metallicFactor']<=.9
        if m['name'] in ['Cast aged bronze','Honed warm limestone']:
            assert 'baseColorTexture' in pbr and 'metallicRoughnessTexture' in pbr and 'normalTexture' in m
            assert pbr['baseColorTexture']['index']!=pbr['metallicRoughnessTexture']['index']
    checks.append('Five opaque one-sided PBR materials; stone is dielectric; metal/data colour roles explicit')
    tris=verts=degenerate=0;module_tris=Counter();primitives=[]
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert primitive.get('mode',4)==4
            attrs=primitive['attributes']
            assert {'POSITION','NORMAL','TEXCOORD_0','TANGENT'}<=set(attrs)
            points=accessor(doc,binary,attrs['POSITION'])
            normals=accessor(doc,binary,attrs['NORMAL'])
            tangent=accessor(doc,binary,attrs['TANGENT'])
            uv=accessor(doc,binary,attrs['TEXCOORD_0'])
            assert len(points)==len(normals)==len(tangent)==len(uv)
            assert all(math.isfinite(c) for block in [points,normals,tangent,uv] for row in block for c in row)
            assert all(.95<=sum(c*c for c in n)<=1.05 for n in normals)
            assert all(.95<=sum(c*c for c in n[:3])<=1.05 and abs(abs(n[3])-1)<1e-4 for n in tangent)
            assert all(-.001<=c<=1.001 for row in uv for c in row)
            inds=[x[0] for x in accessor(doc,binary,primitive['indices'])]
            assert len(inds)%3==0 and max(inds)<len(points)
            for i in range(0,len(inds),3):
                a,b,c=[points[inds[i+j]] for j in range(3)]
                u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
                cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
                if sum(x*x for x in cross)<1e-18:degenerate+=1
            count=len(inds)//3
            tris+=count;verts+=len(points);module_tris[mesh['name'].split('__')[0]]+=count
            primitives.append({'mesh':mesh['name'],'triangles':count,'vertices':len(points),'material':doc['materials'][primitive['material']]['name']})
    assert 0<tris<=110000 and degenerate==0,(tris,degenerate)
    checks.append('All exported triangles finite/nondegenerate; normal/tangent frames unit; UVs in bounds')
    manifest=json.loads((HERE/'manifest.json').read_text())
    assert manifest['triangles']==tris,(manifest['triangles'],tris)
    assert manifest['materials']==5 and len(manifest['textures'])==6
    assert manifest['glb']['sha256']==hashlib.sha256(raw).hexdigest()
    for tex in manifest['textures']:
        file=HERE/tex['path']
        assert hashlib.sha256(file.read_bytes()).hexdigest()==tex['sha256']
        assert tex['size']==[1024,1024]
    for image in doc.get('images',[]):
        assert 'bufferView' in image and 'uri' not in image
        view=doc['bufferViews'][image['bufferView']]
        start=view.get('byteOffset',0);data=binary[start:start+view['byteLength']]
        assert data[:8]==b'\x89PNG\r\n\x1a\n'
        w,h=struct.unpack_from('>II',data,16)
        assert w<=1024 and h<=1024
    checks.append('Pinned six original 1024² source maps; all exported maps embedded PNG at or below 1024²')
    report={'schema_version':1,'status':'structural PASS; actual appearance UNRUN','glb':str(path),
      'sha256':hashlib.sha256(raw).hexdigest(),'triangles':tris,'vertices':verts,'materials':len(doc['materials']),
      'embedded_images':len(doc.get('images',[])),'degenerate_triangles':degenerate,'checks':checks,
      'module_triangles':dict(module_tris),'primitives':primitives,
      'limitations':['This does not approve architecture/art quality, runtime collision, native import, shader appearance, renderer compatibility or hardware performance.']}
    out=HERE/'validation.json';out.write_text(json.dumps(report,indent=2)+'\n')
    evidence=HERE.parents[1]/'docs/evidence/rama-quality/environment/validation-r1.json'
    evidence.parent.mkdir(parents=True,exist_ok=True);evidence.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
