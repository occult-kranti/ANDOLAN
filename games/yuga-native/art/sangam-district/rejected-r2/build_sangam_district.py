#!/usr/bin/env python3
"""Original Sangam civic quarter, authored in Blender with existing CC0 YUGA PBR.

Run only in the lead's serialized export lane:
  blender4.3 --background --threads 8 --python tools/studio/build_sangam_district.py

All mesh coordinates are authored in metres, Godot Y-up. The conversion to
Blender Z-up is a proper rotation, and glTF exports back to Godot coordinates.
No downloaded game geometry, photos, procedural runtime mesh builders or add-ons.
"""
from pathlib import Path
import hashlib
import json
import math
import sys

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "games/yuga-native"
ART = PROJECT / "art/sangam-district"
ASSET = PROJECT / "assets/world/sangam-district.glb"
SPEC = PROJECT / "assets/world/sangam-district.json"
MAP = PROJECT / "assets/world/confluence-map.json"
ART.mkdir(parents=True, exist_ok=True)
SOURCE_MAP = json.loads(MAP.read_text())
MATERIALS = []
IMAGE_SOURCES = {}
MODULES = []
GROUND_BOXES = []
OVERHEAD_BOXES = []
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def material(name, color, texture=None, roughness=.8, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if texture:
        for suffix, target in [("albedo", "Base Color"), ("roughness", "Roughness"), ("normal", "Normal")]:
            path = PROJECT / f"assets/environment/lanka_courtyard_{texture}_{suffix}.png"
            image = bpy.data.images.load(str(path), check_existing=True)
            if suffix != "albedo": image.colorspace_settings.name = "Non-Color"
            image.pack()
            tex = nodes.new("ShaderNodeTexImage"); tex.image = image
            tex.interpolation = "Linear"; tex.extension = "REPEAT"
            if suffix == "normal":
                normal = nodes.new("ShaderNodeNormalMap")
                normal.inputs["Strength"].default_value = .55
                links.new(tex.outputs["Color"], normal.inputs["Color"])
                links.new(normal.outputs["Normal"], bsdf.inputs[target])
            else:
                links.new(tex.outputs["Color"], bsdf.inputs[target])
            IMAGE_SOURCES[str(path.relative_to(ROOT))] = digest(path)
    MATERIALS.append(mat)
    return len(MATERIALS) - 1


SAND = material("Sangam / carved warm sandstone", (.65, .47, .30), "Warm_carved_sandstone")
PALE = material("Sangam / dressed limestone", (.73, .67, .53), "Pale_limestone")
BLUE = material("Sangam / glazed indigo", (.055, .10, .18), "Indigo_glazed_stone", .7)
BRASS = material("Sangam / weathered worked brass", (.46, .28, .10), "Aged_brass", .56, .62)
WOOD = material("Sangam / oiled timber", (.105, .057, .029), None, .82)
SHADE = material("Sangam / recessed shutter shadow", (.055, .064, .070), None, .95)
CLAY = material("Sangam / fired terracotta", (.33, .14, .071), None, .89)
LEAF = material("Sangam / garden leaves", (.18, .265, .10), None, .95)


class MeshBuilder:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.faces = []
        self.material_ids = []

    def poly(self, points, material):
        start = len(self.vertices)
        self.vertices.extend(tuple(p) for p in points)
        self.faces.append(tuple(range(start, start + len(points))))
        self.material_ids.append(material)

    def solid(self, points, faces, material):
        start = len(self.vertices)
        self.vertices.extend(tuple(p) for p in points)
        self.faces.extend(tuple(start + i for i in face) for face in faces)
        self.material_ids.extend([material] * len(faces))

    def box(self, x, y, z, w, h, d, material):
        points = [(x + a*w/2, y + b*h/2, z + c*d/2)
                  for b in [-1, 1] for c in [-1, 1] for a in [-1, 1]]
        self.solid(points, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                            (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)], material)

    def lathe(self, x, z, profile, material, segments=24):
        points = [(x + radius*math.cos(2*math.pi*i/segments), y,
                   z + radius*math.sin(2*math.pi*i/segments))
                  for radius, y in profile for i in range(segments)]
        faces = []
        for row in range(len(profile)-1):
            for i in range(segments):
                j = (i+1) % segments
                faces.append((row*segments+i, row*segments+j, (row+1)*segments+j, (row+1)*segments+i))
        faces.append(tuple(reversed(range(segments))))
        faces.append(tuple((len(profile)-1)*segments+i for i in range(segments)))
        self.solid(points, faces, material)

    def beam(self, a, b, width, material):
        a, b = Vector(a), Vector(b)
        direction = (b-a).normalized()
        side = direction.cross(Vector((0, 1, 0)))
        if side.length < .1: side = direction.cross(Vector((1, 0, 0)))
        side.normalize(); up = side.cross(direction).normalized()
        points = [p + side*s*width/2 + up*t*width/2 for p in [a, b] for t in [-1, 1] for s in [-1, 1]]
        self.solid(points, [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)], material)

    def hip(self, x, y, z, w, d, height, material):
        points = [(x+a*w/2, y, z+b*d/2) for b in [-1, 1] for a in [-1, 1]]
        points += [(x+a*w*.34, y+height, z+b*d*.34) for b in [-1, 1] for a in [-1, 1]]
        self.solid(points, [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)], material)

    def export_object(self):
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata([(x, -z, y) for x, y, z in self.vertices], [], self.faces)
        mesh.update()
        for mat in MATERIALS: mesh.materials.append(mat)
        for polygon, mat in zip(mesh.polygons, self.material_ids): polygon.material_index = mat
        edit = bmesh.new(); edit.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(edit, faces=list(edit.faces))
        edit.to_mesh(mesh); edit.free()
        # Stable metre-scale planar UVs use each face's major axis. This keeps
        # stone grain/damage human scale instead of stretching a tile per hall.
        uv = mesh.uv_layers.new(name="MetreScaleUV")
        for face in mesh.polygons:
            axis = max(range(3), key=lambda i: abs(face.normal[i]))
            for index in face.loop_indices:
                point = mesh.vertices[mesh.loops[index].vertex_index].co
                coords = (point.y, point.z) if axis == 0 else ((point.x, point.z) if axis == 1 else (point.x, point.y))
                uv.data[index].uv = (coords[0]/2.4, coords[1]/2.4)
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        return obj


def face_point(x, z, w, d, face, u, y, out):
    if face == 0: return (x+u, y, z+d/2+out)
    if face == 1: return (x-u, y, z-d/2-out)
    if face == 2: return (x+w/2+out, y, z-u)
    return (x-w/2-out, y, z+u)


def face_box(mesh, x, z, w, d, face, u, y, out, breadth, height, depth, mat):
    p = face_point(x, z, w, d, face, u, y, out)
    mesh.box(*p, breadth if face < 2 else depth, height, depth if face < 2 else breadth, mat)


def arch(mesh, point, u, spring, radius, rise, depth, mat, scalloped=False):
    # Closed voussoir ring with visible depth and optional gentle cusp rhythm.
    segments = 12
    for i in range(segments):
        angles = [math.pi*i/segments, math.pi*(i+1)/segments]
        points = []
        for out in [-depth, 0]:
            for r, h in [(radius-.14, rise-.15), (radius, rise)]:
                for angle in angles:
                    cusp = .035*math.sin(angle*10)**2 if scalloped else 0
                    points.append(point(u+math.cos(angle)*(r-cusp), spring+math.sin(angle)*(h-cusp), out))
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)]
        if i == 0: faces.append((0, 2, 6, 4))
        if i == segments-1: faces.append((1, 5, 7, 3))
        mesh.solid(points, faces, mat)


def rosette(mesh, point, u, y, radius, material):
    for petal in range(8):
        angle = math.pi*petal/4
        points = []
        for a, distance in [(angle-.18, radius*.3), (angle-.14, radius*.78), (angle, radius), (angle+.14, radius*.78), (angle+.18, radius*.3)]:
            points.append(point(u+math.sin(a)*distance, y+math.cos(a)*distance, .012))
        mesh.poly(points, material)


def shutter(mesh, x, z, w, d, face, u, bottom, family):
    point = lambda a, b, c: face_point(x, z, w, d, face, a, b, c)
    radius = .96 if family != 3 else .88
    rise = 1.0 if family != 1 else 1.15
    spring = bottom+1.35
    panel = [point(u-radius+.15, bottom, -.18), point(u+radius-.15, bottom, -.18)]
    panel += [point(u+math.cos(math.pi*i/16)*(radius-.15), spring+math.sin(math.pi*i/16)*(rise-.16), -.18) for i in range(17)]
    mesh.poly(panel, SHADE)
    arch(mesh, point, u, spring, radius, rise, .18, PALE if family == 1 else SAND, family in [0, 2])
    for direction in [-1, 1]:
        face_box(mesh, x,z,w,d,face,u+direction*(radius-.07),bottom+.67,-.06,.14,1.34,.12,PALE if family == 1 else SAND)
    face_box(mesh,x,z,w,d,face,u,bottom-.08,-.06,radius*2+.20,.16,.18,PALE)
    for i in range(7):
        bar_u = u+(i-3)*.22
        face_box(mesh,x,z,w,d,face,bar_u,bottom+.65,-.135,.11,1.28,.035,WOOD if family in [0, 2] else BRASS)
    # Small diagonal jali elements in the arched cap have no doorway semantics.
    for shift in [-.48, -.24, 0, .24, .48]:
        mesh.beam(point(u+shift-.16,spring+.13,-.12),point(u+shift+.16,spring+.50,-.12),.038,BRASS)
        mesh.beam(point(u+shift+.16,spring+.13,-.12),point(u+shift-.16,spring+.50,-.12),.038,BRASS)


def pavilion(mesh, x, z, base, radius, family):
    mesh.lathe(x,z,[(radius*1.08,base),(radius*1.08,base+.18),(radius*.94,base+.27)],PALE,24)
    height = 2.2
    for i in range(8):
        angle = math.pi*i/4
        px,pz = x+math.cos(angle)*radius*.77,z+math.sin(angle)*radius*.77
        mesh.lathe(px,pz,[(.19,base+.25),(.19,base+.44),(.12,base+.54),(.115,base+height-.25),(.22,base+height-.13),(.22,base+height)],SAND,12)
    mesh.lathe(x,z,[(radius,base+height),(radius*1.12,base+height+.12),(radius*1.12,base+height+.25)],PALE,24)
    profile=[(radius*1.04,base+height+.25),(radius*.99,base+height+.40),(radius*.86,base+height+.72),(radius*.65,base+height+.99),(radius*.36,base+height+1.19),(.08,base+height+1.33)]
    mesh.lathe(x,z,profile,BLUE if family in [1,2] else CLAY,32)
    for i in range(12):
        angle=2*math.pi*i/12
        for (r1,y1),(r2,y2) in zip(profile[:-1],profile[1:]):
            mesh.beam((x+r1*math.cos(angle),y1+.02,z+r1*math.sin(angle)),(x+r2*math.cos(angle),y2+.02,z+r2*math.sin(angle)),.036,BRASS)
    mesh.lathe(x,z,[(.12,base+height+1.32),(.2,base+height+1.45),(.09,base+height+1.60),(.02,base+height+1.93)],BRASS,16)


def building(entry):
    index = entry["source_index"]
    family = index//2
    x,_,z = entry["position"]
    w,h,d = entry["size"]
    body = MeshBuilder(f"BASE_Block_{index}")
    overhead = MeshBuilder(f"SOLID_Overhead_{index}")
    main = SAND if family in [0,2] else BLUE
    trim = PALE if family != 3 else BRASS
    # Exact inherited solid envelope; closed windows are relief, not interiors.
    body.box(x,h/2,z,w-.36,h,d-.36,main)
    for y,breadth,height in [(.12,0,.24),(.40,.12,.28),(.66,.24,.24),(h-.38,.12,.26),(h-.10,0,.20)]:
        body.box(x,y,z,w-breadth,height,d-breadth,SAND if y<1 else trim)
    floors=max(1,int((h-.8)/3.6))
    for face in range(4):
        width=w if face<2 else d
        bays=max(3,int(width/3.2))
        spacing=(width-1.6)/bays
        point=lambda a,b,c,face=face:face_point(x,z,w,d,face,a,b,c)
        for bay in range(bays+1):
            u=(bay-bays/2)*spacing
            face_box(body,x,z,w,d,face,u,h/2,-.06,.30,h-.7,.12,PALE if family==1 else SAND)
            for y in [.94,h-.78]:
                face_box(body,x,z,w,d,face,u,y,-.035,.45,.24,.07,trim)
        for level in range(floors):
            bottom=.95+level*3.6
            if bottom+2.6>h-.5: continue
            for bay in range(bays):
                u=(bay-(bays-1)/2)*spacing
                shutter(body,x,z,w,d,face,u,bottom,family)
                rosette(body,point,u,bottom+2.77,.17,BRASS)
            for y in [bottom+2.92,bottom+3.08]:
                face_box(body,x,z,w,d,face,0,y,-.025,width-.4,.065,.05,trim)
        # Bracket-supported chajja is real overhead cover along a ground route.
        # Three-metre eaves stop short of the central lane's +/-4m clear band.
        projection=2.8 if index<4 else 2.1
        roof_y=4.72
        face_box(overhead,x,z,w,d,face,0,roof_y,projection/2-.15,width+.18,.24,projection+.30,SAND)
        face_box(overhead,x,z,w,d,face,0,roof_y+.17,projection/2-.12,width+.36,.10,projection+.44,CLAY if family in [0,2] else BRASS)
        for bay in range(bays+1):
            u=(bay-bays/2)*spacing
            start=point(u,3.35,-.08);end=point(u,4.54,projection-.3)
            overhead.beam(start,end,.22,SAND)
            overhead.beam(point(u,4.46,-.08),end,.19,WOOD)
            face_box(overhead,x,z,w,d,face,u,4.16,.25,.45,.46,.5,trim)
        # Tiled eave rhythm; no floating decals or emissive decorative glyphs.
        for step in range(int(width/.5)):
            u=-width/2+(step+.5)*.5
            face_box(overhead,x,z,w,d,face,u,roof_y+.25,projection-.02,.36,.08,.27,CLAY if family in [0,2] else BRASS)
        # Deliberately closed indigo banners on upper masonry, clear of targets.
        if face<2 and family in [0,2] and h>=9:
            for u in [-width*.32,width*.32]:
                face_box(body,x,z,w,d,face,u,h-2.0,-.04,.74,2.1,.045,BLUE)
                for v in [-.34,.34]:face_box(body,x,z,w,d,face,u+v,h-2,-.005,.04,2.1,.03,BRASS)
                rosette(body,point,u,h-1.9,.23,BRASS)
    # Rooftop courtyard caps and recognisable family silhouettes are actual solids.
    overhead.box(x,h+.18,z,w-.35,.36,d-.35,PALE)
    for sign in [-1,1]:
        overhead.box(x+sign*(w/2-.35),h+.72,z,.32,.72,d-.4,SAND)
        overhead.box(x,h+.72,z+sign*(d/2-.35),w-.4,.72,.32,SAND)
    if family==0:
        for sx in [-1,1]:
            for sz in [-1,1]:pavilion(overhead,x+sx*w*.30,z+sz*d*.30,h+.4,1.22,family)
        overhead.hip(x,h+.4,z,w*.42,d*.42,.72,CLAY)
    elif family==1:
        overhead.box(x,h+1.12,z,w*.56,1.52,d*.45,BLUE)
        overhead.hip(x,h+1.9,z,w*.64,d*.54,.8,BRASS)
        for sign in [-1,1]:pavilion(overhead,x+sign*w*.33,z,h+.4,1.08,family)
    elif family==2:
        pavilion(overhead,x,z,h+.4,2.25,family)
        for sign in [-1,1]:overhead.hip(x,h+.4,z+sign*d*.34,w*.65,d*.16,.7,CLAY)
    else:
        # Long brass-roofed gallery: posts and roof are truthful collision.
        for sx in [-1,1]:
            for sz in [-.35,0,.35]:
                px,pz=x+sx*w*.28,z+sz*d
                overhead.lathe(px,pz,[(.22,h+.4),(.15,h+.65),(.15,h+2.1),(.27,h+2.25)],SAND,12)
        overhead.box(x,h+2.3,z,w*.7,.24,d*.84,PALE)
        overhead.hip(x,h+2.43,z,w*.78,d*.91,.65,BRASS)
    a,b=body.export_object(),overhead.export_object()
    MODULES.append({"id":f"block-{index}","family":["ghat-colonnade","indigo-archive","observatory-chhatri","brass-eave-gallery"][family],"base_mesh":a.name,"overhead_mesh":b.name,"position":entry["position"],"inherited_ground_size":entry["size"],"canopy_bottom_y":4.6,"canopy_projection_m":projection,"ground_collision":"existing_authority_solid","upper_collision":"exact_overhead_render_triangles"})


for block in SOURCE_MAP["authority_collision_boxes"]: building(block)


def connector(z):
    mesh=MeshBuilder("SOLID_AvenueGallery_"+("South" if z<0 else "North"))
    # Exact 22m span meets both existing inner-building walls at X=-11/+11.
    mesh.box(0,8.2,z,22,.4,4.8,SAND)
    mesh.box(0,8.48,z,22,.16,5.1,PALE)
    for side in [-1,1]:
        for x in [-10,-6,-2,2,6,10]:
            mesh.lathe(x,z+side*2.1,[(.26,8.55),(.26,8.8),(.17,8.9),(.17,11.0),(.3,11.15)],SAND,12)
        mesh.box(0,11.3,z+side*2.1,22,.3,.54,PALE)
        mesh.box(0,9.05,z+side*2.28,22,.55,.15,BLUE)
        for x in range(-10,11):mesh.box(x,9.6,z+side*2.28,.09,.65,.09,BRASS)
    mesh.hip(0,11.48,z,22.5,5.5,.7,CLAY)
    mesh.export_object()
    OVERHEAD_BOXES.append({"id":"avenue-gallery-"+str(z),"position":[0,8,z],"size":[22,.4,4.8],"ground_route_below_m":8,"collision":"exact_visible_triangles"})


for z in [-28,28]:connector(z)


def cover(x,z):
    name=f"SOLID_Cover_{'West' if x<0 else 'East'}_{'South' if z<0 else 'North'}"
    mesh=MeshBuilder(name)
    mesh.box(x,1.35,z,3,2.7,6,SAND)
    for y,height in [(.14,.22),(.52,.16),(2.38,.16),(2.65,.1)]:mesh.box(x,y,z,3,height,6,PALE)
    for face in range(4):
        span=3 if face<2 else 6
        p=lambda a,b,c,face=face:face_point(x,z,3,6,face,a,b,c)
        for u in ([-.75,.75] if span<4 else [-2,-.7,.7,2]):
            face_box(mesh,x,z,3,6,face,u,1.42,-.008,.63,1.32,.018,BLUE)
            rosette(mesh,p,u,1.42,.25,BRASS)
            for y in [.72,2.12]:rosette(mesh,p,u,y,.12,BRASS)
    mesh.export_object()
    GROUND_BOXES.append({"id":"sangam-cover-"+name.removeprefix("SOLID_Cover_"),"kind":"solid_civic_cover_monument","mesh":name,"position":[x,0,z],"size":[3,2.7,6],"anchor":"base_center","collision_layer":1,"native_only":True})


for x in [-8,8]:
    for z in [-60,60]:cover(x,z)


def distant_gallery(side):
    mesh=MeshBuilder("VISTA_"+("West" if side<0 else "East"))
    x=side*77
    mesh.box(x,7,0,12,14,204,SAND)
    for z in range(-96,97,12):
        mesh.box(x-side*5.7,7.3,z,.55,12.6,.65,PALE)
        mesh.box(x-side*5.6,4.5,z,.30,.22,11.8,BRASS)
        for y in [2,6,10]:
            point=lambda u,v,o,x=x,z=z: (x-side*(5.84+o),v,z+u)
            for u in [-3,0,3]:
                panel=[point(u-.9,y,0),point(u+.9,y,0),point(u+.9,y+1.4,0),point(u-.9,y+1.4,0)]
                mesh.poly(panel,BLUE)
                arch(mesh,point,u,y+1.4,1.08,.8,.12,PALE,True)
        if z%24==0:
            pavilion(mesh,x-side*2,z,14,2.6,2 if side>0 else 0)
    mesh.box(x,14.15,0,12.8,.3,205,PALE)
    mesh.hip(x,14.35,0,11,203,1.2,CLAY)
    mesh.export_object()


for side in [-1,1]:distant_gallery(side)
for sign in [-1,1]:
    mesh=MeshBuilder("VISTA_"+("SouthCourt" if sign<0 else "NorthCourt"))
    z=sign*145
    mesh.box(0,9,z,148,18,8,SAND)
    for x in [-60,-36,-12,12,36,60]:
        mesh.box(x,9,z-sign*4.05,1.1,18,.3,PALE)
        pavilion(mesh,x,z,18,2.4,0 if sign<0 else 1)
    mesh.box(0,18.25,z,150,.5,9,PALE)
    mesh.export_object()


objects=[obj for obj in bpy.context.scene.objects if obj.type=="MESH"]
triangles=sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in objects)
print("SANGAM_MODULE_TRIANGLES",json.dumps({obj.name:sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in objects}))
assert triangles<320000, triangles
assert len(MATERIALS)==8
assert len(MODULES)==8 and len(GROUND_BOXES)==4
for cover_box in GROUND_BOXES:
    assert abs(cover_box["position"][0])-cover_box["size"][0]/2>=6.5
    assert cover_box["size"][1]==2.7
for obj in objects:
    assert all(math.isfinite(v) for vertex in obj.data.vertices for v in vertex.co)

bpy.ops.object.select_all(action="DESELECT")
for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(ASSET),export_format="GLB",use_selection=True,
                          export_cameras=False,export_lights=False,export_extras=True)
scene=bpy.context.scene
scene.render.engine="CYCLES";scene.cycles.device="CPU";scene.cycles.samples=24
scene.render.threads_mode="FIXED";scene.render.threads=8
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.20,.24,.30)
bpy.ops.object.light_add(type="SUN",location=(0,0,100))
bpy.context.object.rotation_euler=(math.radians(35),math.radians(-25),math.radians(-25))
bpy.context.object.data.energy=2.2
bpy.ops.object.light_add(type="AREA",location=(0,0,85))
bpy.context.object.data.energy=140000;bpy.context.object.data.size=150
bpy.ops.object.camera_add(location=(115,150,95))
camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,7))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.lens=35;scene.camera=camera
scene.view_settings.view_transform="AgX"
scene.render.filepath=str(ART/"blender-overview.png")
bpy.ops.wm.save_as_mainfile(filepath=str(ART/"sangam-district.blend"))

report={"schema_version":1,"id":"sangam-civic-quarter-v1","product":"YUGA native offline Confluence",
        "scope":"Original full-district visual replacement, true overhead collision and four additional grounded cover footprints. Existing eight ground solids, three lanes, gate/garden and relays retained; no online or elevated-cast claim.",
        "source_commit":"7162b5d0b666e4422b0bc73100e1fba947d3323f","source_map_sha256":digest(MAP),
        "authoring_script":"tools/studio/build_sangam_district.py","authoring_script_sha256":digest(__file__),
        "blender_version":bpy.app.version_string,"asset_sha256":digest(ASSET),"blend_sha256":digest(ART/"sangam-district.blend"),
        "materials":[m.name for m in MATERIALS],"texture_sources":IMAGE_SOURCES,"triangles":triangles,
        "mesh_objects":len(objects),"modules":MODULES,"ground_footprints":GROUND_BOXES,"overhead_routes":OVERHEAD_BOXES,
        "coordinate_contract":"metres Godot +Y-up; Blender [x,-z,y] proper rotation; glTF converts back",
        "hide_original_nodes":["CityArt/block-"+str(i) for i in range(8)]+["CityArt/block-"+str(i)+"-roof" for i in range(8)]+["CityArt/skyline-"+str(i) for i in range(8)]+["ReviewBlock2Frontage","ReviewBlock2RoofLoggia"],
        "reference_scope":"Original invented South Asian civic architecture; historical references guide massing, eaves, galleries and jali rhythm, not archaeological reconstruction. No external photographs or game assets used.",
        "budget_scope":"Measured authored counts only; physical GPU performance and human visual acceptance remain unrun."}
SPEC.write_text(json.dumps(report,indent=2)+"\n")
(ART/"manifest.json").write_text(json.dumps(report,indent=2)+"\n")
print("SANGAM_DISTRICT",json.dumps({k:report[k] for k in ["triangles","mesh_objects","asset_sha256","blender_version"]}))
if "--render" in sys.argv:bpy.ops.render.render(write_still=True)
