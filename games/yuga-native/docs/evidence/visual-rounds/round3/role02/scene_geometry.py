import json, struct, math, hashlib
from pathlib import Path
import numpy as np

ROOT=Path('/workspace/ANDOLAN/games/yuga-native')
def glb(path):
    b=(ROOT/path).read_bytes(); n=struct.unpack_from('<I',b,12)[0]
    j=json.loads(b[20:20+n]); data=b[28+n:]
    def accessor(i):
        a=j['accessors'][i]; v=j['bufferViews'][a['bufferView']]
        dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.ndarray((a['count'],width),dtype=dt,buffer=data,offset=offset,strides=(v.get('byteStride',np.dtype(dt).itemsize*width),np.dtype(dt).itemsize))
    out={}
    for node in j['nodes']:
        if 'mesh' not in node: continue
        assert not any(k in node for k in ['matrix','rotation','scale','translation'])
        parts=[]
        for p in j['meshes'][node['mesh']]['primitives']:
            v=accessor(p['attributes']['POSITION']); idx=accessor(p['indices']).ravel()
            parts.append((v[idx].reshape(-1,3,3).astype(float),j['materials'][p['material']]['name']))
        out[node['name']]=parts
    return out

def rotate(v,yaw):
    t=math.radians(yaw); c=math.cos(t);s=math.sin(t)
    return np.asarray(v)@np.array([[c,0,-s],[0,1,0],[s,0,c]])

def ray_hits(parts,o,d):
    o=np.asarray(o);d=np.asarray(d);d=d/np.linalg.norm(d);hits=[]
    for tri,material,label in parts:
        e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];h=np.cross(d,e2);a=np.einsum('ij,ij->i',e1,h)
        valid=np.abs(a)>1e-9; f=np.zeros_like(a);f[valid]=1/a[valid]
        s=o-tri[:,0];u=f*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1)
        v=f*np.einsum('j,ij->i',d,q);t=f*np.einsum('ij,ij->i',e2,q)
        valid &= (u>=0)&(v>=0)&(u+v<=1)&(t>1e-6)
        if valid.any():
            dist=float(t[valid].min());hits.append({'distance_m':dist,'material':material,'object':label,'point':(o+d*dist).tolist()})
    return sorted(hits,key=lambda x:x['distance_m'])

if __name__=='__main__':
    nature=glb('assets/world/nature.glb');arch=glb('assets/world/architecture.glb');court=glb('assets/environment/lanka_courtyard.glb')
    manifest=json.loads((ROOT/'assets/world/confluence-map.json').read_text())
    parts=[]
    for prop in manifest['props']:
        lib=nature if prop['preset'] in nature else arch
        if prop['preset'] not in lib:continue
        for tri,mat in lib[prop['preset']]:
            tri=rotate(tri*np.array(prop['scale']),prop['yaw_degrees'])+np.array(prop['position'])
            parts.append((tri,mat,prop['id']))
    courtyard=[(tri,mat,name) for name,values in court.items() for tri,mat in values]
    for p,yaw,vertical in [([-20,.05,14],180,.04),([-54,.05,0],18.627274488929288,-.06)]:
        c=np.array(p)+[0,1.7522,0];off=rotate([-.64,vertical,-.62],yaw-180)
        hits=ray_hits(parts,c,-off)
        print('WORLD',p,yaw,'center',c.tolist(),'offset',off.tolist(),'hit',hits[:2])
    for x in [7,8,9,10,11,12,13,14]:
        c=np.array([x,1.7522,-16]);off=np.array([.64,.04,.62])
        print('COURT',x,ray_hits(courtyard,c,-off)[:1])
