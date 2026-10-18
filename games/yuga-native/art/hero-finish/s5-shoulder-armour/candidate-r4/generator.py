#!/usr/bin/env python3
"""Original curved left pauldron. Three finite LODs; no hero data is rewritten."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import numpy as np
from scipy.ndimage import maximum_filter, gaussian_filter
from scipy.interpolate import RegularGridInterpolator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'art/hero-rama-lod'))
from glb_lod import GLB
SOURCE_SHA = '8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c'
MATERIALS = [
    {'name': 'Worked warm gold', 'pbrMetallicRoughness': {'baseColorFactor': [.64,.36,.085,1], 'metallicFactor': .82, 'roughnessFactor': .55}},
    {'name': 'Cobalt handwoven silk', 'pbrMetallicRoughness': {'baseColorFactor': [.018,.085,.29,1], 'metallicFactor': 0, 'roughnessFactor': .82}},
    {'name': 'Recessed antique gold', 'pbrMetallicRoughness': {'baseColorFactor': [.24,.115,.025,1], 'metallicFactor': .8, 'roughnessFactor': .62}}]
ENVELOPE = None
ENVELOPE_RECORD = {}


def fit_envelope(source, inverse):
    """Fit broad authored lofts outside actual body, original cap and drape."""
    global ENVELOPE, ENVELOPE_RECORD
    colliders=[]
    for pi in [2,3,4,5,6,11]:
        p=source.doc['meshes'][2]['primitives'][pi];v=source.array(p['attributes']['POSITION'])
        local=(np.c_[v,np.ones(len(v))]@inverse.T)[:,:3];tri=local[source.array(p['indices']).reshape(-1,3)]
        keep=(tri[:,:,1].min(1)<.26)&(tri[:,:,1].max(1)>-.09)
        colliders.append(tri[keep])
    tri=np.concatenate(colliders);axial=np.linspace(-.085,.255,69);angular=np.linspace(-100,112,73)
    radii=np.zeros((len(axial),len(angular)));beyond=0
    for i,s in enumerate(axial):
        t=tri[(tri[:,:,1].min(1)<=s)&(tri[:,:,1].max(1)>=s)]
        a=t[:,0];e1=t[:,1]-a;e2=t[:,2]-a
        for j,degrees in enumerate(angular):
            angle=math.radians(degrees);direction=np.array([math.sin(angle),0,math.cos(angle)])
            h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.sum(e1*h,axis=1)
            inv=np.divide(1,det,out=np.zeros_like(det),where=abs(det)>1e-12);delta=np.array([0,s,0])-a
            u=np.sum(delta*h,axis=1)*inv;q=np.cross(delta,e1);v=np.sum(q*direction,axis=1)*inv;distance=np.sum(e2*q,axis=1)*inv
            valid=(abs(det)>1e-12)&(u>=0)&(v>=0)&(u+v<=1)&(distance>0)&(distance<.22)
            if valid.any():radii[i,j]=distance[valid].max()
            beyond+=int(radii[i,j]>.17)
    # Retain narrow original gold leaf tips which a regular ray grid may miss.
    for pi in [2,5,6]:
        p=source.doc['meshes'][2]['primitives'][pi];a=p['attributes']
        j=source.array(a['JOINTS_0']);w=source.array(a['WEIGHTS_0']);v=source.array(a['POSITION'])
        selected=np.sum(np.where(j==50,w,0),axis=1)>.999
        local=(np.c_[v[selected],np.ones(int(selected.sum()))]@inverse.T)[:,:3]
        for point in local:
            degrees=math.degrees(math.atan2(point[0],point[2]))
            if axial[0]<=point[1]<=axial[-1] and angular[0]<=degrees<=angular[-1]:
                i=int(np.argmin(abs(axial-point[1])));j=int(np.argmin(abs(angular-degrees)))
                radii[i,j]=max(radii[i,j],float(np.linalg.norm(point[[0,2]])))
    # Coarse outward envelope, not texture-like displacement: expand local
    # support then smooth without going below the exact sampled support.
    dilation=maximum_filter(radii,size=(5,5),mode='nearest')
    smooth=np.maximum(radii,gaussian_filter(dilation,sigma=(2,2),mode='nearest'))
    ENVELOPE=RegularGridInterpolator((axial,angular),smooth,bounds_error=True)
    ENVELOPE_RECORD={'axial_m':axial.tolist(),'angles_degrees':angular.tolist(),'fitted_radius_m':smooth.tolist(),
                     'sampled_radius_max_m':float(radii.max()),'sampled_rays_over170mm':beyond,
                     'collider_triangles':len(tri),'smoothing':'5x5 support maximum, Gaussian sigma2, outward support maximum'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit(v):
    v = np.asarray(v, dtype=float)
    length = np.linalg.norm(v, axis=-1, keepdims=True)
    assert np.all(length > 1e-12)
    return v / length


def frames(vertices, uv, triangles):
    n = np.zeros_like(vertices); tan = np.zeros_like(vertices); bitan = np.zeros_like(vertices)
    p = vertices[triangles]; e1 = p[:,1]-p[:,0]; e2 = p[:,2]-p[:,0]
    face = np.cross(e1, e2)
    assert np.all(np.linalg.norm(face, axis=1) > 1e-12)
    duv1 = uv[triangles[:,1]]-uv[triangles[:,0]]; duv2 = uv[triangles[:,2]]-uv[triangles[:,0]]
    determinant = duv1[:,0]*duv2[:,1]-duv1[:,1]*duv2[:,0]
    good = abs(determinant) > 1e-12
    ta = np.zeros_like(face); bi = np.zeros_like(face)
    ta[good] = (e1[good]*duv2[good,1,None]-e2[good]*duv1[good,1,None])/determinant[good,None]
    bi[good] = (e2[good]*duv1[good,0,None]-e1[good]*duv2[good,0,None])/determinant[good,None]
    for k in range(3):
        np.add.at(n, triangles[:,k], face); np.add.at(tan, triangles[:,k], ta); np.add.at(bitan, triangles[:,k], bi)
    n = unit(n); tan = tan - n * np.sum(tan*n, axis=1)[:,None]
    assert np.all(np.linalg.norm(tan, axis=1)>1e-10), 'Undefined UV derivative'
    tan = unit(tan); sign = np.where(np.sum(np.cross(n,tan)*bitan,axis=1)<0,-1.,1.)
    return n, np.c_[tan,sign], int((~good).sum())


class Shape:
    def __init__(self, name, material):
        self.name = name; self.material = material; self.v=[]; self.uv=[]; self.tri=[]

    def surface(self, points, outward, uv_scale=(1,1)):
        points = np.asarray(points); rows, cols = points.shape[:2]; start=len(self.v)
        for i in range(rows):
            for j in range(cols):
                self.v.append(points[i,j]); self.uv.append([j/(cols-1)*uv_scale[0],i/(rows-1)*uv_scale[1]])
        for i in range(rows-1):
            for j in range(cols-1):
                ids=[start+i*cols+j,start+i*cols+j+1,start+(i+1)*cols+j+1,start+(i+1)*cols+j]
                for tri in [(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])]:
                    p=np.array([self.v[k] for k in tri]); center=p.mean(0)
                    if np.dot(np.cross(p[1]-p[0],p[2]-p[0]),outward(center))<0: tri=(tri[0],tri[2],tri[1])
                    self.tri.append(tri)

    def solid_patch(self, fn, nu, nv, thickness):
        outer=np.array([[fn(j/nu,i/nv) for j in range(nu+1)] for i in range(nv+1)])
        radial=unit(outer*np.array([1.,0.,1.])); inner=outer-radial*thickness
        self.surface(outer,lambda p:p*np.array([1,0,1]))
        self.surface(inner,lambda p:-p*np.array([1,0,1]))
        for edge, edge_inner, direction in [
            (outer[0],inner[0],np.array([0,-1,0])),(outer[-1],inner[-1],np.array([0,1,0])),
            (outer[:,0],inner[:,0],np.array([-1,0,0])),(outer[:,-1],inner[:,-1],np.array([1,0,0]))]:
            self.surface(np.array([edge,edge_inner]),lambda p,d=direction:d)
        return outer

    def tube(self, points, radius, sides):
        points=np.asarray(points); closed=np.linalg.norm(points[0]-points[-1])<1e-8
        assert closed, 'Decorative edge is a closed rolled seam'
        directions=np.array([points[(i+1)%(len(points)-1)]-points[(i-1)%(len(points)-1)] for i in range(len(points)-1)])
        directions=np.r_[directions,directions[:1]]; directions=unit(directions)
        guide=unit(points*np.array([1.,0.,1.])); right=unit(np.cross(directions,guide)); across=unit(np.cross(directions,right))
        ring=np.array([[p+radius*(r*math.cos(2*math.pi*j/sides)+a*math.sin(2*math.pi*j/sides)) for j in range(sides+1)] for p,r,a in zip(points,right,across)])
        def outward(p):
            nearest=np.argmin(np.sum((points-p)**2,axis=1));return p-points[nearest]
        self.surface(ring,outward)

    def arrays(self):
        v=np.array(self.v); uv=np.array(self.uv); tri=np.array(self.tri,dtype='<u4')
        n,t,undefined=frames(v,uv,tri)
        # Check geometric watertightness across duplicated UV/normal seam rows.
        edges={}
        welded=[tuple(np.round(p,9)) for p in v]
        for face in tri:
            for a,b in zip(face,np.roll(face,-1)):
                key=tuple(sorted((welded[a],welded[b])));edges[key]=edges.get(key,0)+1
        assert all(x==2 for x in edges.values()), self.name+' is not a closed two-manifold component'
        return {'POSITION':v.astype('<f4'),'NORMAL':n.astype('<f4'),'TANGENT':t.astype('<f4'),
                'TEXCOORD_0':uv.astype('<f4'),'COLOR_0':np.tile([1,1,1,0],(len(v),1)).astype('<f4'),'indices':tri.ravel()}, {
                'name':self.name,'material':self.material,'vertices':len(v),'triangles':len(tri),'closed_geometric_edges':len(edges),
                'uv_degenerate_triangles':undefined,'bounds_local_m':[v.min(0).tolist(),v.max(0).tolist()]}


def perimeter(grid):
    return np.concatenate([grid[0],grid[1:,-1],grid[-1,-2::-1],grid[-2:0:-1,0],grid[:1,0]])


def surface_fn(layer):
    # Shoulder local +Y follows the arm, +X faces forward, +Z is lateral/up.
    # Broad lofts and three scallops define silhouette, not repeated tiny noise.
    starts=[-.055,.050,.115]; ends=[.092,.157,.200]
    radii=[.111,.091,.076]; angle_pairs=[(-65,90),(-65,90),(-62,88)]
    def point(u,v):
        degrees=angle_pairs[layer][0]*(1-u)+angle_pairs[layer][1]*u
        theta=math.radians(degrees)
        end=ends[layer]+.009*math.cos(3*theta)+.006*math.cos(theta)
        s=starts[layer]*(1-v)+end*v
        radius=radii[layer]+.010*max(math.sin(theta),0)-.009*max(-math.sin(theta),0)
        radius+=.009*math.sin(math.pi*v)-.006*v
        radius+=.004*math.cos(theta)*math.sin(math.pi*v)
        if ENVELOPE is not None:
            # Cap overlaps the lower plates with an actual radial step.
            radius=max(radius,float(ENVELOPE([[s,degrees]])[0])+[.018,.012,.008][layer])
        return np.array([radius*math.sin(theta),s,radius*math.cos(theta)])
    return point


def geometry(level):
    divisions={'near':(30,10,7),'mid':(20,7,6),'far':(12,4,5)}
    nu,nv,sides=divisions[level]; shapes=[]
    for layer in range(3):
        fn=surface_fn(layer)
        shell=Shape(['Domed acromion cap','First overlapping deltoid lame','Second overlapping deltoid lame'][layer],0 if layer==0 else 1)
        grid=shell.solid_patch(fn,nu,nv,.0035 if layer==0 else .003)
        shapes.append(shell)
        edge=Shape('Rolled gold border '+str(layer+1),0)
        edge.tube(perimeter(grid),.0027 if layer==0 else .0023,sides);shapes.append(edge)
    # A single five-petal repousse lotus on the front quadrant of the cap.
    # Each petal follows the cap's curvature; neither floating wires nor decals.
    cap=surface_fn(0)
    for petal in range(5):
        angle=math.radians(-75+petal*37.5)
        center=np.array([.76,.45]);axis=np.array([math.sin(angle),math.cos(angle)])
        across=np.array([axis[1],-axis[0]])
        def leaf(u,v,c=center,ax=axis,ac=across):
            span=math.sin(math.pi*(.04+.92*v))**.8
            q=c+ax*((v-.10)*.20)+ac*((u*2-1)*.040*span)
            p=cap(float(q[0]),float(q[1]));r=unit(p*np.array([1.,0.,1.]))
            return p+r*(.0023+.0045*span*(1-(u*2-1)**2))
        shape=Shape('Raised lotus petal '+str(petal+1),0)
        shape.solid_patch(leaf,max(3,nu//6),max(4,nv),.0017);shapes.append(shape)
    # Recessed backing gives the coherent lotus a readable dark boundary.
    def shield(u,v):
        # Smooth square-to-disc mapping gives a curved oval backing.
        a,b=u*2-1,v*2-1
        q=np.array([.76+a*math.sqrt(1-b*b/2)*.105,.50+b*math.sqrt(1-a*a/2)*.18])
        p=cap(float(q[0]),float(q[1]));r=unit(p*np.array([1.,0.,1.]))
        return p+r*.0015
    backing=Shape('Antique gold recessed lotus field',2)
    backing.solid_patch(shield,max(4,nu//4),max(4,nv//2),.001);shapes.append(backing)
    return shapes


def write_glb(path,shapes,extras):
    binary=bytearray();views=[];accessors=[];primitives=[];stats=[]
    grouped={i:[] for i in range(len(MATERIALS))}
    for shape in shapes:
        arrays,check=shape.arrays();grouped[shape.material].append(arrays);stats.append(check)
    def add(data,kind,component=5126):
        while len(binary)%4:binary.append(0)
        data=np.asarray(data);start=len(binary);binary.extend(data.tobytes())
        views.append({'buffer':0,'byteOffset':start,'byteLength':data.nbytes})
        count=len(data);item={'bufferView':len(views)-1,'componentType':component,'count':count,'type':kind}
        if kind=='VEC3':item.update(min=data.min(0).astype(float).tolist(),max=data.max(0).astype(float).tolist())
        accessors.append(item);return len(accessors)-1
    for material,parts in grouped.items():
        offset=0;indices=[]
        for part in parts:indices.append(part['indices']+offset);offset+=len(part['POSITION'])
        attributes={}
        for name,kind in [('POSITION','VEC3'),('NORMAL','VEC3'),('TANGENT','VEC4'),('TEXCOORD_0','VEC2'),('COLOR_0','VEC4')]:
            attributes[name]=add(np.concatenate([p[name] for p in parts]),kind)
        primitives.append({'attributes':attributes,'indices':add(np.concatenate(indices).astype('<u4'),'SCALAR',5125),'material':material})
    doc={'asset':{'version':'2.0','generator':'YUGA original S5 layered shoulder armour'},'scene':0,'scenes':[{'nodes':[0]}],
         'nodes':[{'name':'OriginalLeftShoulderArmour','mesh':0}],'meshes':[{'name':'Curved cap and overlapping lames','primitives':primitives}],
         'materials':MATERIALS,'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors,'extras':extras}
    raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);binary+=b'\0'*((-len(binary))%4)
    result=struct.pack('<4sII',b'glTF',2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4E4F534A)+raw+struct.pack('<II',len(binary),0x004E4942)+binary
    path.write_bytes(result)
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':len(result),'vertices':sum(s['vertices'] for s in stats),
            'triangles':sum(s['triangles'] for s in stats),'material_draws':3,'components':stats}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output=args.output.resolve()
    assert not args.output.exists(), 'Retain every candidate iteration; fresh output required'
    source=ROOT/'assets/heroes/rama-hero.glb';assert sha(source)==SOURCE_SHA
    original=GLB(source);skin=original.doc['skins'][0];names=[original.doc['nodes'][i]['name'] for i in skin['joints']]
    assert len(names)==164 and names[50]=='upperarm01.L'
    inverse=original.array(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
    rest=np.linalg.inv(inverse[50]);assert np.max(abs(rest[:3,:3].T@rest[:3,:3]-np.eye(3)))<2e-5
    fit_envelope(original,inverse[50])
    args.output.mkdir(parents=True)
    extras={'review_only':True,'default_activation':False,'attachment_bone':'upperarm01.L','source_joint_slot':50,
            'local_frame':'Source upperarm01.L bone-local metres; +Y down arm, +X front, +Z lateral/up.',
            'source_hero_sha256':SOURCE_SHA,'original_geometry':True,'new_bone_writers':0,'secondary_alpha':0}
    levels={}
    for level in ['near','mid','far']:levels[level]=write_glb(args.output/('shoulder-armour-'+level+'.glb'),geometry(level),extras)
    manifest={'schema':1,'generator':str(Path(__file__).relative_to(ROOT)),'generator_sha256':sha(__file__),
              'source_hero_sha256':SOURCE_SHA,'attachment':{**extras,'inverse_bind_matrix':inverse[50].tolist(),'global_rest_matrix':rest.tolist(),'bone_order':names},
              'levels':levels,'original_source_sha256':sha(ROOT/'art/hero-rama/build_hero.py'),
              'source_fitted_envelope':ENVELOPE_RECORD,
              'identity_reference':{'path':'../yuga/art/references/rama-hanuman-sita.png','sha256':sha(ROOT/'../yuga/art/references/rama-hanuman-sita.png'),'use':'Visual form reference only; no sampled image or extracted mesh.'},
              'viewed_current_title':{'path':'docs/evidence/desktop-finish/G0/template-priority-cold-600-r1/00-title-100.png','sha256':sha(ROOT/'docs/evidence/desktop-finish/G0/template-priority-cold-600-r1/00-title-100.png')},
              'scope':'Concrete original inactive 3D candidate. Rest/action clearance, actual rig attachment/import and matched native images remain separate gates.'}
    (args.output/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert sha(source)==SOURCE_SHA
    print(json.dumps({k:{f:v[f] for f in ['sha256','triangles','vertices','bytes']} for k,v in levels.items()},indent=2))


if __name__=='__main__':main()
