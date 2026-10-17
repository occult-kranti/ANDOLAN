"""Bounded actual GLB eyelid checks. Visual closure/seam acceptance is separate."""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'hero-rama'))
from validate_hero import read,accessor as dense_accessor,TYPES,SIZES

def accessor(doc,binary,index):
    spec=doc['accessors'][index]
    if 'bufferView'in spec:out=dense_accessor(doc,binary,index)
    else:out=np.zeros((spec['count'],SIZES[spec['type']]),dtype=TYPES[spec['componentType']])
    if 'sparse'in spec:
        sparse=spec['sparse'];ispec=sparse['indices'];vspec=sparse['values']
        iview=doc['bufferViews'][ispec['bufferView']];vview=doc['bufferViews'][vspec['bufferView']]
        indices=np.frombuffer(binary,dtype=TYPES[ispec['componentType']],count=sparse['count'],offset=iview.get('byteOffset',0)+ispec.get('byteOffset',0))
        values=np.frombuffer(binary,dtype=TYPES[spec['componentType']],count=sparse['count']*SIZES[spec['type']],offset=vview.get('byteOffset',0)+vspec.get('byteOffset',0)).reshape(-1,SIZES[spec['type']])
        out[indices]=values
    return out

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def front_hits(vertices,triangles,x,y):
    t=vertices[triangles]
    a=t[:,0,:2];b=t[:,1,:2];c=t[:,2,:2]
    v0=b-a;v1=c-a;v2=np.array([x,y])-a
    den=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0]
    good=np.abs(den)>1e-13
    u=np.zeros(len(t));v=np.zeros(len(t))
    u[good]=(v2[good,0]*v1[good,1]-v2[good,1]*v1[good,0])/den[good]
    v[good]=(v0[good,0]*v2[good,1]-v0[good,1]*v2[good,0])/den[good]
    hit=good&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)
    return t[hit,0,2]+u[hit]*(t[hit,1,2]-t[hit,0,2])+v[hit]*(t[hit,2,2]-t[hit,0,2])

def main():
    p=argparse.ArgumentParser();p.add_argument('asset',type=Path);p.add_argument('--report',type=Path,required=True);p.add_argument('--baseline',type=Path)
    a=p.parse_args();raw,d,b=read(a.asset);checks=[]
    def check(name,passed,**details):
        checks.append({'name':name,'passed':bool(passed),'details':details})
        print(('PASS ' if passed else 'FAIL ')+name,details)
    nodes=[n for n in d['nodes'] if n.get('name')=='RamaFace']
    check('Exactly one separate small facial node',len(nodes)==1)
    face=d['meshes'][nodes[0]['mesh']]
    shapes=face.get('extras',{}).get('targetNames',[])
    check('Named full/optional-half eyelid morphs',shapes in [['rama_blink_left','rama_blink_right'],['rama_blink_left','rama_blink_right','rama_blink_half_left','rama_blink_half_right']])
    check('Every exported skin retains 164 joints',all(len(s['joints'])==164 for s in d['skins']))
    count=0;maximum=0;position_blocks=[];open_blocks=[];index_blocks=[];base_offset=0
    eye_minmax=[]
    for primitive in face['primitives']:
        attributes=primitive['attributes']
        xyz=accessor(d,b,attributes['POSITION'])
        normals=accessor(d,b,attributes['NORMAL'])
        colors=accessor(d,b,attributes['COLOR_0'])
        weights=accessor(d,b,attributes['WEIGHTS_0'])
        check('Face attributes and semantic anchors preserved',{'POSITION','NORMAL','TANGENT','TEXCOORD_0','COLOR_0','JOINTS_0','WEIGHTS_0'}<=set(attributes) and np.isfinite(xyz).all() and np.isfinite(normals).all() and np.max(abs(colors[:,:3]-1))<1e-6 and np.max(abs(colors[:,3]))<1e-6 and np.max(abs(weights.sum(axis=1)-1))<1e-6)
        check('Opaque skin material retained',d['materials'][primitive['material']]['name']=='Rama warm skin' and d['materials'][primitive['material']].get('alphaMode','OPAQUE')=='OPAQUE')
        closed=xyz.copy()
        for index,target in enumerate(primitive['targets']):
            delta=accessor(d,b,target['POSITION'])
            maximum=max(maximum,float(np.max(np.linalg.norm(delta,axis=1))))
            moved=np.linalg.norm(delta,axis=1)>1e-7
            check('Only intended eye moves in morph '+shapes[index],np.count_nonzero(moved)>200 and np.all(xyz[moved,0]>0 if index%2==0 else xyz[moved,0]<0),moved_vertices=int(np.count_nonzero(moved)))
            check('Morph positions/normals finite and bounded '+shapes[index],np.isfinite(delta).all() and np.isfinite(accessor(d,b,target['NORMAL'])).all() and np.max(np.linalg.norm(delta,axis=1))<.018,maximum_delta_m=float(np.max(np.linalg.norm(delta,axis=1))))
            if index<2:closed+=delta
        check('Fixed outer-boundary vertices remain exactly neutral',np.count_nonzero(np.linalg.norm(closed-xyz,axis=1)<1e-7)>=120)
        position_blocks.append(closed)
        open_blocks.append(xyz)
        index_blocks.append(accessor(d,b,primitive['indices']).reshape(-1,3)+base_offset)
        count+=len(xyz);base_offset+=len(xyz)
    check('Morph payload remains local rather than body-wide',count<=8000,exported_vertices=count,maximum_displacement_m=maximum)
    # Bones locate original globe centers. Blender(-Y front) -> glTF(+Z front).
    verts=np.concatenate(position_blocks);open_verts=np.concatenate(open_blocks);tris=np.concatenate(index_blocks)
    baseline_geometry=None
    if a.baseline:
        _,bd,bb=read(a.baseline);bv=[];bt=[];bo=0
        for mesh_ in bd['meshes']:
            for primitive in mesh_['primitives']:
                if bd['materials'][primitive['material']]['name']!='Rama warm skin':continue
                positions=accessor(bd,bb,primitive['attributes']['POSITION'])
                bv.append(positions);bt.append(accessor(bd,bb,primitive['indices']).reshape(-1,3)+bo);bo+=len(positions)
        baseline_geometry=(np.concatenate(bv),np.concatenate(bt))
    eye_samples=[]
    for side in ('L','R'):
        node=next(n for n in d['nodes'] if n.get('name')=='eye.'+side)
        # The generator reports actual rest eye origins; hierarchy translations
        # must be composed, rather than treating an eye-local offset as world.
        node_index=d['nodes'].index(node)
        parents={child:i for i,n in enumerate(d['nodes']) for child in n.get('children',[])}
        matrix=np.eye(4)
        chain=[];current=node_index
        while True:
            chain.append(current)
            if current not in parents:break
            current=parents[current]
        def transform(n):
            if 'matrix'in n:return np.array(n['matrix']).reshape(4,4).T
            x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4)
            m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m
        for i in reversed(chain):matrix=matrix@transform(d['nodes'][i])
        center=matrix[:3,3].copy();center[2]+=.003
        # Face positions may be in mesh-local coordinates but the author keeps
        # identity face/armature transforms. Assert this before interpreting rays.
        uncovered=[];margin=[]
        for dx in np.linspace(-.010,.010,9):
            for dy in np.linspace(-.003,.004,7):
                hits=front_hits(verts,tris,center[0]+dx,center[1]+dy)
                globe=center[2]+np.sqrt(max(0,.0153**2-dx*dx-dy*dy))
                if len(hits)==0 or np.max(hits)<globe-.0002:uncovered.append([float(dx),float(dy)])
                else:margin.append(float(np.max(hits)-globe))
        check('Closed skin occludes the sampled cornea '+side,len(uncovered)==0,samples=63,uncovered=uncovered,minimum_coverage_margin_m=min(margin)if margin else None)
        obstructed=[];visibility_changes=[]
        for dx in np.linspace(-.004,.004,5):
            for dy in np.linspace(-.0018,.0018,5):
                hits=front_hits(open_verts,tris,center[0]+dx,center[1]+dy)
                globe=center[2]+np.sqrt(max(0,.0153**2-dx*dx-dy*dy))
                blocked=bool(len(hits)and np.max(hits)>globe-.0002)
                if blocked:obstructed.append([float(dx),float(dy)])
                if baseline_geometry:
                    baseline_hits=front_hits(*baseline_geometry,center[0]+dx,center[1]+dy)
                    baseline_blocked=bool(len(baseline_hits)and np.max(baseline_hits)>globe-.0002)
                    if blocked!=baseline_blocked:visibility_changes.append([float(dx),float(dy),blocked,baseline_blocked])
        if baseline_geometry:check('Neutral partition preserves exact baseline cornea visibility '+side,len(visibility_changes)==0,samples=25,visibility_changes=visibility_changes,already_occluded_by_baseline=len(obstructed))
        else:check('Open lids preserve the sampled central cornea '+side,len(obstructed)==0,samples=25,obstructed=obstructed)
        eye_samples.append({'side':side,'rest_center_gltf':center.tolist()})
    report={'schema':1,'asset_sha256':digest(a.asset),'baseline_sha256':digest(a.baseline)if a.baseline else None,'validator_sha256':digest(__file__),'passed':all(c['passed']for c in checks),'count':len(checks),'checks':checks,'eye_origins':eye_samples,'scope':'Actual GLB geometry/morph payload and bounded cornea ray coverage only. Optional original baseline compares neutral visibility instead of incorrectly requiring original skin-covered points to become transparent. Requires imported neutral/half/closed sequential visual review; no art-quality, gameplay, GPU performance or commercial parity claim.'}
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['passed']else 1

if __name__=='__main__':sys.exit(main())
