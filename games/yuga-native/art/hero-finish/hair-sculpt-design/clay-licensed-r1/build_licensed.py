"""One private CC-BY4 hair adaptation from explicit inspected source geometry.

No new ring/loft/block hair geometry, renderer, GLB or canonical change. Multiple
closed source clumps remain separate as root permits; fixed context is exact.
"""
import argparse,gzip,hashlib,json,math,os,shutil,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'clay-framing-r3'))
from scene_semantics import snapshot,differences
from projection_contract import points,census,fits
HAIR='EDITABLE_WholeHair_CoarseClay'
PARENT='e41417ff09dd5d22de35b0f3b0b7dd5db3711057fe11ffe1f6b3fd819f044aee'
SOURCE='92b8d760a03bf90878f0fe304031cd65928857bb24c5bd90c8a2d41682c4d95e'
DATA='b5d4c7372770c59f17615fce0ac973178da1cb6db57494de96a9470489636f7c'
SCALP=[28,29,30,31,32,33,34,35,36,37,38,39,40,42,44,55,59,60,70,72,74,75,76,77,78,79,80]
MIRROR=[28,29,30,31,32,33,34,35,36,37,38,39,40,59,60]
BUN=[0,2,4,6,7,9,11,13,14,18,21,25]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def gz(p,v):
    with gzip.GzipFile(filename=str(p),mode='wb',mtime=0)as f:f.write(json.dumps(v,separators=(',',':')).encode())
def gltf(v):return Vector((v.x,v.z,-v.y))
def blender(v):return (v[0],-v[2],v[1])

def source_head(source):
    # Read original helper only in memory, then remove every newly loaded
    # datablock. Its geometry is reference for fitting, never part of the asset.
    collections=[bpy.data.objects,bpy.data.meshes,bpy.data.materials,bpy.data.images,bpy.data.curves,bpy.data.armatures]
    old=[{x.as_pointer()for x in c}for c in collections]
    with bpy.data.libraries.load(str(source),link=False)as(a,b):
        assert 'mh_helper'in a.objects;b.objects=['mh_helper']
    obj=b.objects[0];body=obj.vertex_groups['body'].index
    indices={v.index for v in obj.data.vertices if any(g.group==body and g.weight>.5 for g in v.groups)}
    faces=[list(f.vertices)for f in obj.data.polygons if all(i in indices for i in f.vertices)]
    assert len(indices)==13380
    tree=BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],faces,all_triangles=False)
    for c,known in zip(collections,old):
        for item in list(c):
            if item.as_pointer()not in known:c.remove(item,do_unlink=True)
    return tree

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-blend',type=Path,required=True);p.add_argument('--source-geometry',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.output.exists()
    assert a.output.is_absolute()and a.output.is_relative_to(Path('/workspace/scratch'))
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    assert sha(bpy.data.filepath)==PARENT and sha(a.source_blend)==SOURCE and sha(a.source_geometry)==DATA
    assert shutil.disk_usage('/workspace').free>=500*1024**2
    before=snapshot();clay=bpy.data.objects[HAIR].data.materials[0]
    source=json.loads(gzip.decompress(a.source_geometry.read_bytes()))
    body=source_head(a.source_blend)
    headobj=bpy.data.objects['LOCKED_2_11_Rama warm skin']
    head=BVHTree.FromPolygons([gltf(headobj.matrix_world@v.co)for v in headobj.data.vertices],[list(f.vertices)for f in headobj.data.polygons],all_triangles=False)
    src_origin=Vector((0,-.10,6.90));dst_origin=Vector((0,1.765,.045))
    vertices=[];faces=[];groups={};records=[];ray_misses=[]
    def part(part_id):
        c=source['components'][part_id];assert c['closed_manifold'],part_id
        ids=c['vertex_indices'];mapping={v:i for i,v in enumerate(ids)};pool=set(ids)
        return np.array([source['vertices'][i]for i in ids]),[[mapping[i]for i in f]for f in source['faces']if f[0]in pool]
    def add(name,part_id,positions,polys,operation):
        first=len(vertices);vertices.extend([list(map(float,p))for p in positions]);faces.extend([[i+first for i in f]for f in polys]);groups[name]=list(range(first,len(vertices)));records.append(dict(name=name,source_component=part_id,vertices=len(positions),faces=len(polys),operation=operation))
    def seat(p,mirror=False):
        q=Vector((-p[0]if mirror else p[0],p[1],p[2]));direction=q-src_origin;length=direction.length;direction.normalize()
        sh,_,_,_=body.ray_cast(src_origin,direction,5)
        target_direction=Vector((direction.x,direction.z,-direction.y))
        dh,_,_,_=head.ray_cast(dst_origin,target_direction,.5)
        assert sh is not None and dh is not None,('head fitting ray miss',list(q))
        # Preserve source volume relative to its actual helper body surface,
        # with a modest radial widening/seating lift; no coverage hemisphere.
        relative=(length-(sh-src_origin).length)*.1
        return dh+target_direction*(relative*1.35+.0030)
    for i in SCALP:
        v,f=part(i);add('Scalp source '+str(i),i,[seat(p)for p in v],f,'Original source clump ray-registered from hm08 body to fixed Rama head; radial thickness1.35 +3mm seating')
    for i in MIRROR:
        v,f=part(i);add('Mirrored scalp '+str(i),i,[seat(p,True)for p in v],[list(reversed(face))for face in f],'Mirrored closed source clump then same head registration; finite coverage counterpart for discarded invalid source pieces')

    bun_points=np.array([source['vertices'][i]for k in BUN for i in source['components'][k]['vertex_indices']]);bun_center=bun_points.mean(axis=0)
    for j,i in enumerate(BUN):
        v,f=part(i);out=[]
        for p in v:
            q=(p-bun_center)*.1
            x=q[0]*.50;yy=q[2]*.36;zz=-q[1]*.53
            # Tilt the authored curled forms across the gather, then return
            # their roots into scalp volume without an artificial connector.
            angle=math.radians(-12);x,yy=math.cos(angle)*x-math.sin(angle)*yy,math.sin(angle)*x+math.cos(angle)*yy
            target=Vector((x-.005,1.864+yy,zz-.040))
            dy=abs(target.y-1.868)
            if dy<.010:
                radial=math.hypot(target.x,target.z+.04);limit=.0305+.25*dy
                if radial>limit:
                    target.x*=limit/radial;target.z=-.04+(target.z+.04)*limit/radial
            out.append(target)
        add('Authored folded loc '+str(i),i,out,f,'Subset of original curled bun geometry; x.50/yup.36/z.53, oblique12degree turn and low gather placement; tie corridor seating')

    falls=[(35,.013,1.805,.275,.025,.30,1.8),(36,-.015,1.795,.245,-.022,.28,1.9),(37,.038,1.785,.195,.014,.26,1.7),(38,-.042,1.780,.195,-.013,.26,1.8),(77,.005,1.785,.225,-.017,.28,1.7),(78,-.025,1.790,.250,.018,.27,1.8)]
    for n,(i,cx,root,length,bend,width_scale,depth_scale)in enumerate(falls):
        v,f=part(i);center=v.mean(axis=0);_,axes=np.linalg.eigh(np.cov(v.T));q=(v-center)@axes*.1
        lo,hi=q[:,2].min(),q[:,2].max();out=[]
        for local in q:
            t=(local[2]-lo)/(hi-lo);yy=root-length*t
            taper=1-.60*max(0,(t-.63)/.37)**1.3
            xx=cx+local[1]*width_scale*taper+bend*4*t*(1-t)*(1-2*t)
            # Follow the actual occiput/nape surface, keeping a modest depth
            # gap rather than the rejected large open C behind the neck.
            hit,_,_,_=head.ray_cast(Vector((xx,yy,.045)),Vector((0,0,-1)),.3)
            if hit is None:
                hit,_,_,_=head.ray_cast(Vector((max(-.04,min(.04,xx)),yy,.045)),Vector((0,0,-1)),.3)
            assert hit is not None,('nape seating ray miss',n,xx,yy)
            zz=hit.z-.010-local[0]*depth_scale*taper-.003*math.sin(math.pi*t)
            out.append((xx,yy,zz))
        add('Grouped falling source '+str(i),i,out,f,'Existing closed artist clump reoriented by principal axes, elongated and bent with two broad opposite pushes; taper and fixed-nape following; original vertices/faces retained')

    allowed=[]
    for old in list(bpy.data.objects):
        if old.name!=HAIR and not old.name.startswith('SOURCE_LOFT_'):continue
        m=old.data;allowed+=['.objects.'+old.name,'.meshes.'+m.name];bpy.data.objects.remove(old,do_unlink=True);bpy.data.meshes.remove(m)
    mesh=bpy.data.meshes.new(HAIR);mesh.from_pydata([blender(v)for v in vertices],[],faces);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);assert bad==0,bad;bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(HAIR,mesh);bpy.context.scene.collection.objects.link(obj);mesh.materials.append(clay)
    for poly in mesh.polygons:poly.use_smooth=True
    for name,ids in groups.items():obj.vertex_groups.new(name=name).add(ids,1,'REPLACE')
    obj['role']='Private CC-BY4 BraidStrands adaptation; intentional separate closed rounded source clumps'
    obj['upstream_author']='Dennis Ploeger / deep-entertainment';obj['upstream_license']='CC-BY-4.0';obj['upstream_sha256']=SOURCE;obj['not_runtime']=True
    sub=obj.modifiers.new('Source clump subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
    allowed+=['.objects.'+HAIR,'.meshes.'+mesh.name];bpy.context.view_layer.update()
    after=snapshot();delta=differences(before,after)
    unexpected=[row[0]for row in delta if not any(row[0]==q or row[0].startswith(q+'.')for q in allowed)and not row[0].endswith('.properties.users')]
    assert not unexpected,unexpected
    h,c=points(bpy.context.scene);projection=census(bpy.context.scene,h,c);assert all(fits(b)for row in projection.values()for b in row.values()),projection
    a.output.mkdir(parents=True);gz(a.output/'source-cage.json.gz',dict(vertices=vertices,faces=faces,groups=groups));gz(a.output/'semantic-before.json.gz',before);gz(a.output/'semantic-after.json.gz',after)
    js(a.output/'derivative-changes.json',dict(source_blend_sha256=SOURCE,source_geometry_sha256=DATA,license='CC-BY-4.0',source_components_selected=records,components=len(records),source_invalid_components_omitted=True,no_source_body_photo_or_materials_reused=True,no_cap_or_connector_geometry=True))
    js(a.output/'projection.json',dict(views=projection,passed=True))
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();gz(a.output/'evaluated-clay.json.gz',dict(vertices=[list(gltf(v.co))for v in em.vertices],faces=[list(f.vertices)for f in em.polygons]));ev.to_mesh_clear()
    js(a.output/'construction-receipt.json',dict(parent_sha256=PARENT,builder_sha256=sha(__file__),upstream_blend_sha256=SOURCE,vertices=len(vertices),faces=len(faces),closed_components=len(records),nonmanifold_edges=bad,protected_reference_changes=unexpected,allowed_difference_prefixes=allowed,projection_passed=True,subdivision=1,no_render=True,no_export=True,actual_review='pending',scope='Private licensed rounded-clump adaptation; source checks are not visible-fit, animation or artistic acceptance'))
    assert shutil.disk_usage('/workspace').free>=500*1024**2
    destination=a.output/'whole-hair-licensed-r1.blend';bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
    js(a.output/'manifest.json',{f.name:dict(bytes=f.stat().st_size,sha256=sha(f))for f in sorted(a.output.iterdir())if f.is_file()})
    print('LICENSED_CLUMP_SOURCE_SAVED',destination,sha(destination),flush=True)
if __name__=='__main__':main()
