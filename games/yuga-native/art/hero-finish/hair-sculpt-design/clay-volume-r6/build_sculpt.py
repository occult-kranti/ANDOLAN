"""C6 direct coarse polygon block sculpt in the fixed reference scene.

No inherited hair vertices, axial-section/loft generator, voxel union, render,
export or runtime write. A scalp quad net is seated against actual head rays;
closed box cages are edited in three dimensions and bridged at buried roots.
"""
import argparse, gzip, hashlib, json, math, os, shutil, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'clay-framing-r3'))
from scene_semantics import snapshot,differences
from projection_contract import points,census,fits
PARENT_SHA='beb880db906dc429520215eafd8f3106d408cc8de28dde84f1e2cda08b5a4f57'
HAIR='EDITABLE_WholeHair_CoarseClay'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def gz(p,value):
    with gzip.GzipFile(filename=str(p),mode='wb',mtime=0)as f:
        f.write(json.dumps(value,separators=(',',':')).encode())
def js(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def gltf(v):return Vector((v.x,v.z,-v.y))
def blender(v):return (v[0],-v[2],v[1])

class Cage:
    def __init__(self):self.v=[];self.f=[];self.groups={};self.parts={}
    def vertex(self,p,group):
        i=len(self.v);self.v.append(list(p));self.groups.setdefault(group,[]).append(i);return i
    def bridge_root(self,part,anchor,occupied):
        """Join only buried inner scalp faces; visible lobes stay independently editable."""
        def center(face):return Vector([sum(self.v[i][a]for i in face)/4 for a in range(3)])
        choices=[i for i in self.parts[part]if i not in occupied]
        a=min(choices,key=lambda i:(center(self.f[i])-Vector(anchor)).length_squared)
        b=min([i for i in self.parts['Buried scalp interior']if i not in occupied],key=lambda i:(center(self.f[i])-center(self.f[a])).length_squared)
        va,vb=self.f[a],self.f[b]
        options=[]
        for direction in [vb,list(reversed(vb))]:
            for shift in range(4):
                candidate=direction[shift:]+direction[:shift]
                score=sum((Vector(self.v[x])-Vector(self.v[y])).length_squared for x,y in zip(va,candidate))
                options.append((score,candidate))
        match=min(options,key=lambda x:x[0])[1]
        for i in range(4):self.f.append([va[i],va[(i+1)%4],match[(i+1)%4],match[i]])
        occupied.update([a,b])
        return dict(part=part,part_face=a,buried_scalp_face=b,control_face_center_gltf=list(center(va)))

def author(head):
    cage=Cage();origin=Vector((0,1.765,.045))
    # Seven hand-shaped forehead/crown/occiput profiles. These are open quad
    # surface control rows, not closed hair cross sections or an old cap mesh.
    # central Z, central Y, side X, side Y, side Z, sweep of the central part.
    profiles=[
        (.147,1.783,.066,1.763,.106,-.014),
        (.120,1.829,.087,1.775,.075,-.010),
        (.074,1.854,.094,1.771,.028,-.004),
        (.021,1.852,.093,1.751,-.012,.010),
        (-.027,1.832,.084,1.726,-.046,.013),
        (-.060,1.785,.070,1.708,-.068,.004),
        (-.073,1.727,.055,1.704,-.072,-.004),
    ]
    across=[-1,-.94,-.80,-.60,-.30,0,.30,.60,.80,.94,1]
    # Millimetres of broad sculpt lift per control point: deliberate diagonal
    # sweeps and an unequal crest, authored with the cage rather than grooves.
    lifts=[
        [0,1,3,5,8,5,1,3,4,1,0],
        [0,2,4,8,10,3,1,6,5,2,0],
        [0,3,7,9,4,0,6,9,4,1,0],
        [0,6,8,3,0,5,9,5,1,2,0],
        [0,7,4,0,4,8,6,1,3,5,0],
        [0,4,0,4,8,5,0,4,6,2,0],
        [0,1,4,6,3,0,3,5,2,0,0],
    ]
    outer=[];inner=[]
    for j,(cz,top,w,side,sz,part)in enumerate(profiles):
        oo=[];ii=[]
        for i,u in enumerate(across):
            dome=math.sqrt(max(0,1-u*u))
            target=Vector((w*u+part*dome,side+(top-side)*dome,cz+(sz-cz)*u*u))
            if j==0:target.y+=.004*u-.003*math.exp(-((u+.3)/.24)**2)
            direction=(target-origin).normalized()
            hit,normal,_,_=head.ray_cast(origin,direction,.4)
            assert hit is not None,('head seating ray missed',j,i)
            # Keep coverage close; the long ridges belong to this newly edited
            # surface. The inner faces are seating, never a zero-contact gate.
            lift=.0055+lifts[j][i]*.001
            oo.append(cage.vertex(hit+direction*lift,'Scalp diagonal flow control'))
            ii.append(cage.vertex(hit+direction*.0005,'Buried scalp interior'))
        outer.append(oo);inner.append(ii)
    for grid,name in [(outer,'Scalp diagonal flow control'),(inner,'Buried scalp interior')]:
        first=len(cage.f)
        for j in range(len(grid)-1):
            for i in range(len(across)-1):cage.f.append([grid[j][i],grid[j+1][i],grid[j+1][i+1],grid[j][i+1]])
        cage.parts[name]=list(range(first,len(cage.f)))
    boundary=[(j,0)for j in range(7)]+[(6,i)for i in range(1,11)]+[(j,10)for j in range(5,-1,-1)]+[(0,i)for i in range(9,0,-1)]
    for (j,i),(jj,ii)in zip(boundary,boundary[1:]+boundary[:1]):cage.f.append([outer[j][i],outer[jj][ii],inner[jj][ii],inner[j][i]])

    # Explicit authored polygon control points, individually edited in all
    # three axes then frozen as geometry. No swept path/section constructor
    # remains as an authoring loop.
    net_path=HERE/'control-nets.json.gz'
    assert sha(net_path)=='e5a2550dd91a5883d3d6ec1c0e78a25d67ac0f0190ec0a4aaa8425facccddca1'
    nets=json.loads(gzip.decompress(net_path.read_bytes()))['parts']
    for part in nets:
        first_vertex=len(cage.v);first_face=len(cage.f)
        for v in part['vertices']:cage.vertex(v,part['name'])
        cage.f.extend([[i+first_vertex for i in f]for f in part['faces']])
        cage.parts[part['name']]=list(range(first_face,len(cage.f)))
    occupied=set();bridges=[]
    for name,anchor in [(part['name'],part['buried_root_anchor'])for part in nets]:
        bridges.append(cage.bridge_root(name,anchor,occupied))
    cage.f=[f for i,f in enumerate(cage.f)if i not in occupied]
    return cage,dict(method='New low-resolution polygon control net and directly edited closed box cages; buried shared-edge bridges; no inherited hair mesh, ring/loft construction, voxel union or post-detail grooves',head_seated_profiles=profiles,scalp_control_lifts_mm=lifts,explicit_control_net_sha256=sha(net_path),directly_edited_control_nodes=sum(len(p['direct_vertex_edits'])for p in nets),buried_bridges=bridges,tie_inner_radius_m=.032075216,fold_passage_control_halfwidth_m=.030)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert not a.output.exists()
    assert a.output.is_absolute()and a.output.is_relative_to(Path('/workspace/scratch'))
    assert shutil.disk_usage('/workspace').free>=500*1024**2
    assert sha(bpy.data.filepath)==PARENT_SHA
    before=snapshot();material=bpy.data.objects[HAIR].data.materials[0]
    head_obj=bpy.data.objects['LOCKED_2_11_Rama warm skin']
    head=BVHTree.FromPolygons([gltf(head_obj.matrix_world@v.co)for v in head_obj.data.vertices],[list(f.vertices)for f in head_obj.data.polygons],all_triangles=False)
    cage,design=author(head);allowed=[]
    for old in list(bpy.data.objects):
        if old.name!=HAIR and not old.name.startswith('SOURCE_LOFT_'):continue
        mesh=old.data;allowed+=['.objects.'+old.name,'.meshes.'+mesh.name]
        bpy.data.objects.remove(old,do_unlink=True);bpy.data.meshes.remove(mesh)
    mesh=bpy.data.meshes.new(HAIR);mesh.from_pydata([blender(p)for p in cage.v],[],cage.f);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    topology=dict(vertices=len(bm.verts),faces=len(bm.faces),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges))
    assert not topology['nonmanifold_edges'],topology
    bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(HAIR,mesh);bpy.context.scene.collection.objects.link(obj);mesh.materials.append(material)
    for poly in mesh.polygons:poly.use_smooth=True
    for name,indices in cage.groups.items():obj.vertex_groups.new(name=name).add(indices,1,'REPLACE')
    obj['role']='C6 original direct polygon block sculpt; coarse neutral-clay authoring only'
    obj['not_runtime']=True
    sub=obj.modifiers.new('Editable coarse sculpt subdivision','SUBSURF');sub.levels=2;sub.render_levels=2
    allowed+=['.objects.'+HAIR,'.meshes.'+mesh.name]
    bpy.context.view_layer.update();after=snapshot();delta=differences(before,after)
    unexpected=[row[0]for row in delta if not any(row[0]==q or row[0].startswith(q+'.')for q in allowed)and not row[0].endswith('.properties.users')]
    assert not unexpected,unexpected
    h,c=points(bpy.context.scene);projection=census(bpy.context.scene,h,c)
    assert all(fits(b)for row in projection.values()for b in row.values()),projection
    a.output.mkdir(parents=True)
    gz(a.output/'source-cage.json.gz',dict(vertices=cage.v,faces=cage.f,groups=cage.groups))
    gz(a.output/'semantic-before.json.gz',before);gz(a.output/'semantic-after.json.gz',after)
    js(a.output/'shape-design.json',design);js(a.output/'projection.json',dict(views=projection,passed=True))
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());evaluated=ev.to_mesh()
    gz(a.output/'evaluated-clay.json.gz',dict(vertices=[list(gltf(v.co))for v in evaluated.vertices],faces=[list(f.vertices)for f in evaluated.polygons]))
    evaluated_counts=dict(vertices=len(evaluated.vertices),faces=len(evaluated.polygons));ev.to_mesh_clear()
    js(a.output/'construction-receipt.json',dict(parent_sha256=PARENT_SHA,builder_sha256=sha(__file__),source_topology=topology,evaluated_topology=evaluated_counts,protected_reference_changes=unexpected,allowed_difference_prefixes=allowed,reference_geometry_preserved=True,projection_passed=True,subdivision=2,original_hair_vertices_reused=0,voxel_union=False,no_render=True,no_export=True,actual_review='pending',scope='Direct coarse editable polygon sculpt against locked head/crown/tie; source check does not establish visible fit, art or runtime acceptance'))
    assert shutil.disk_usage('/workspace').free>=500*1024**2
    destination=a.output/'whole-hair-sculpt-r6.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
    js(a.output/'manifest.json',{f.name:dict(bytes=f.stat().st_size,sha256=sha(f))for f in sorted(a.output.iterdir())if f.is_file()})
    print('C6_DIRECT_CAGE_SAVED',destination,sha(destination),flush=True)
if __name__=='__main__':main()
