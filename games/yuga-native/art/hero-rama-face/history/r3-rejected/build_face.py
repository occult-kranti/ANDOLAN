"""Author real two-lid blink surfaces on a frozen Rama quality editable source.

blender -b -t 2 --python build_face.py -- --input SOURCE.blend --output DIR
Candidate only: neutral/half/closed Blender and imported Godot review are required.
No commercial game meshes, eye scaling, body morphs, or extra skeletons.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys, time
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'games/yuga-native/art/hero-rama'))
import build_hero as hero

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fingerprint(obj):
    h = hashlib.sha256()
    for v in obj.data.vertices:
        h.update(repr(tuple(v.co)).encode())
        h.update(repr([(obj.vertex_groups[w.group].name,w.weight) for w in v.groups]).encode())
    for p in obj.data.polygons: h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

def rig_signature(rig):
    return [(b.name,b.parent.name if b.parent else '',list(sum((list(r) for r in b.matrix_local),[]))) for b in rig.data.bones]

class FaceSampler:
    def __init__(self, body):
        self.mesh = body.data
        self.mesh.calc_loop_triangles()
        self.tris = list(self.mesh.loop_triangles)
        self.tree = BVHTree.FromPolygons([v.co for v in self.mesh.vertices], [tuple(t.vertices) for t in self.tris], all_triangles=True)

    def sample(self, x, z):
        co, normal, index, distance = self.tree.ray_cast(Vector((x,-.7,z)),Vector((0,1,0)),1.0)
        if co is None: raise RuntimeError('Missing original face sample: %r' % ((x,z),))
        tri = self.tris[index]
        points = [self.mesh.vertices[v].co for v in tri.vertices]
        uv_layer = self.mesh.uv_layers.active
        values = [Vector((*uv_layer.data[li].uv,0)) for li in tri.loops]
        uv = barycentric_transform(co,*points,*values)
        ns = [self.mesh.vertices[v].normal for v in tri.vertices]
        normal = barycentric_transform(co,*points,*ns).normalized()
        return co,normal,(uv.x,uv.y)

def author(rig, body):
    sampler = FaceSampler(body)
    vertices,closed,faces,uv,normals,labels = [],[],[],[],[],[]
    eyes = {}
    for side in ('L','R'):
        c = rig.data.bones['eye.'+side].head_local.copy()
        c.y -= .003
        eyes[side] = c
    boundary_errors = []
    # Four small layered lid patches. Their stationary outer border lies on the
    # original body surface; no face/body partition or duplicated head seam.
    for side,c in eyes.items():
        for upper in (True,False):
            offset = len(vertices)
            for row in range(9):
                f = row/8
                blend = f*f*(3-2*f)
                for col in range(33):
                    t = col/32
                    wave = math.sin(math.pi*t)
                    dx = (t-.5) * (.032*(1-f)+.043*f)
                    edge_open = (.0065 if upper else -.0047)*wave
                    edge_closed = -.0011*wave
                    outer = (.016 if upper else -.013)*wave
                    positions = []
                    sampled_normal = None
                    sampled_uv = None
                    for edge in (edge_open,edge_closed):
                        dz = edge*(1-blend)+outer*blend
                        co,normal,texture = sampler.sample(c.x+dx,c.z+dz)
                        radial = .0158**2-dx*dx-dz*dz
                        # Outer boundary is copied exactly from the body ray.
                        # Interior skin wraps the globe; blend has zero end slope.
                        # This is a layered skin patch, not a partitioned head.
                        # Bury its stationary outer attachment 0.35 mm beneath
                        # existing skin to avoid coplanar shadow/z-fighting.
                        y = co.y-.00015*(1-blend)+.00035*blend
                        if radial>0 and row<8:
                            # Interpolating sphere depth toward an eye-socket
                            # sample can pass through the globe at half closure.
                            # Enforce the actual outer globe envelope instead.
                            y = min(y,c.y-math.sqrt(radial)-.00055)
                        point = Vector((co.x,y,co.z))
                        if row==8:
                            point = co+Vector((0,.00035,0))
                            boundary_errors.append((point-(co+Vector((0,.00035,0)))).length)
                        positions.append(point)
                        sampled_normal,sampled_uv = normal,texture
                    vertices.append(positions[0]);closed.append(positions[1]);uv.append(sampled_uv)
                    normals.append(sampled_normal if row==8 else None)
                    labels.append(side)
            for row in range(8):
                for col in range(32):
                    a = offset+row*33+col
                    indices = (a,a+1,a+34,a+33)
                    # Surface faces the same forward direction on each lid.
                    faces.append(tuple(reversed(indices)) if upper else indices)

    # Existing integrated rim tubes retain their exact neutral geometry/UVs.
    # They travel with the true closing skin, so no static second lid remains.
    rim_objects = [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Integrated upper eyelid','Integrated lower eyelid'))]
    assert len(rim_objects)==4, [o.name for o in rim_objects]
    for obj in rim_objects:
        assert len(obj.data.vertices)==330, (obj.name,len(obj.data.vertices))
        upper = obj.name.startswith('Integrated upper')
        middle = sum(v.co.x for v in obj.data.vertices)/len(obj.data.vertices)
        side = min(eyes,key=lambda side: abs(eyes[side].x-middle))
        c = eyes[side]
        offset = len(vertices)
        uv_by_vertex = {}
        for loop in obj.data.loops: uv_by_vertex[loop.vertex_index] = tuple(obj.data.uv_layers.active.data[loop.index].uv)
        for index,v in enumerate(obj.data.vertices):
            t = (index//10)/32
            dx = (t-.5)*.032
            dz = (.0065 if upper else -.0047)*math.sin(math.pi*t)
            new_z = -.0011*math.sin(math.pi*t)
            y = -math.sqrt(max(.00002,.0158**2-dx*dx-dz*dz))-.0005
            new_y = -math.sqrt(max(.00002,.0158**2-dx*dx-new_z*new_z))-.0005
            old_center = c+Vector((dx,y,dz))
            new_center = c+Vector((dx,new_y,new_z))
            closed_point = new_center + (v.co-old_center)*(.78 if upper else .72)
            vertices.append(v.co.copy());closed.append(closed_point);uv.append(uv_by_vertex[index]);normals.append(None);labels.append(side)
        for polygon in obj.data.polygons:
            indices = tuple(offset+i for i in polygon.vertices)
            if len(indices)<=4: faces.append(indices)
            else: faces.extend((indices[0],indices[j],indices[j+1]) for j in range(1,len(indices)-1))
        bpy.data.objects.remove(obj,do_unlink=True)

    mesh = bpy.data.meshes.new('RamaFace authored eyelids')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj = bpy.data.objects.new('RamaFace',mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(bpy.data.materials['Rama warm skin'])
    uv_layer = mesh.uv_layers.new(name='UVMap')
    color = mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
    for entry in color.data: entry.color = (1,1,1,0)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for li in polygon.loop_indices: uv_layer.data[li].uv = uv[mesh.loops[li].vertex_index]
    obj.vertex_groups.new(name='head').add(list(range(len(vertices))),1,'REPLACE')
    modifier = obj.modifiers.new('Same original skeleton','ARMATURE')
    modifier.object = rig
    obj.parent = rig
    basis = obj.shape_key_add(name='Basis')
    for side,name in [('L','rama_blink_left'),('R','rama_blink_right')]:
        shape = obj.shape_key_add(name=name)
        for index,v in enumerate(shape.data): v.co = closed[index] if labels[index]==side else vertices[index]
        shape.value = 0
        shape.slider_min = 0
        shape.slider_max = 1
    # Match the original outer face normal exactly, without changing any body
    # vertex, skin weight, UV or shared material. Inner shell normals are smooth.
    custom = []
    for loop in mesh.loops:
        n = normals[loop.vertex_index]
        custom.append(n if n is not None else loop.normal)
    mesh.normals_split_custom_set(custom)
    obj['yuga_face_contract'] = 'authored two-lid shell; no body morph or extra skeleton'
    return obj, {'vertices':len(vertices),'polygons':len(faces),'morphNames':['rama_blink_left','rama_blink_right'],'maximumAttachmentPositionErrorM':max(boundary_errors),'stationaryOuterBoundarySamples':len(boundary_errors),'outerAttachmentInsetM':.00035,'neutralRimVerticesCopied':1320,'bodySplit':False,'eyeScaleWrites':False}

def export(rig,face,path):
    objects = [o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('Review')]
    bowterms = ['Forged recurved bow limbs','Cobalt bow inset','Bow pierced leaf scroll','Bow sapphire setting','Swept bow tip flourish','Leather bound grip','Grip chased wire','Skinned bowstring']
    bows = [o for o in objects if any(o.name.startswith(t) for t in bowterms)]
    assert len(bows)>15
    body = hero.join_group([o for o in objects if o not in bows and o!=face],'RamaHero')
    bow = hero.join_group(bows,'RamaBow')
    hero.activate(rig)
    for obj in (body,bow,face): obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_skins=True,export_all_influences=False,export_yup=True,export_tangents=True,export_image_format='AUTO',export_vertex_color='ACTIVE',export_morph=True,export_morph_normal=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    a.output.mkdir(parents=True,exist_ok=True)
    started = time.monotonic()
    bpy.ops.wm.open_mainfile(filepath=str(a.input))
    # Candidate editable is saved before the artist merges geometry for export.
    rig = next(o for o in bpy.data.objects if o.type=='ARMATURE')
    body = bpy.data.objects['RamaAnatomy']
    before_rig = rig_signature(rig)
    before_body = fingerprint(body)
    eyes = [o for o in bpy.data.objects if o.name.startswith(('Seated sclera','Brown iris','Dark pupil'))]
    eye_hashes = {o.name:fingerprint(o) for o in eyes}
    rig.data.pose_position = 'REST'
    rig.animation_data.action = None
    for bone in rig.pose.bones: bone.matrix_basis.identity()
    face,stats = author(rig,body)
    assert before_rig==rig_signature(rig)
    assert before_body==fingerprint(body)
    assert eye_hashes=={o.name:fingerprint(o) for o in eyes}
    assert len(rig.data.bones)==164
    assert len(face.data.vertices)<=8000
    rig.data.pose_position = 'POSE'
    rig.animation_data.action = bpy.data.actions.get('idle')
    bpy.context.scene.frame_set(1)
    editable = a.output/'rama-hero-face.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(editable),compress=True)
    output = a.output/'rama-hero-face.glb'
    export(rig,face,output)
    stats.update({'schema':1,'task':'Rama proper eyelid candidate','inputBlendSha256':sha(a.input),'generatorSha256':sha(__file__),'outputSha256':sha(output),'editableSha256':sha(editable),'originalBodyUnchanged':True,'originalEyesUnchanged':True,'rigRestPreserved':True,'bones':len(rig.data.bones),'elapsedSeconds':round(time.monotonic()-started,2),'status':'CANDIDATE_UNREVIEWED','limitations':['Proper closure morphology requires open/half/closed imported mesh and sequential visual acceptance.','No brow/jaw/gaze/mouth expressions.','No Deadlock quality or gameplay integration claim.']})
    (a.output/'candidate.json').write_text(json.dumps(stats,indent=2)+'\n')
    print('RAMA_FACE_CANDIDATE '+json.dumps(stats),flush=True)

if __name__=='__main__': main()
