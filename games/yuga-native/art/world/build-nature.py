#!/usr/bin/env python3
"""Build YUGA's original bounded swamp and light kit with Blender 4.3.2.

Run: blender -b -t 1 --python games/yuga-native/art/world/build-nature.py
Authoring helpers use Godot metres, Y up. Exported mesh nodes have base-centred
unit bounds; the map's explicit scale supplies their final world dimensions.
No imported commercial models, textures, generated colliders, or hidden lights.
"""
import hashlib
import json
import math
import random
import struct
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/world/nature.glb"
MANIFEST = Path(__file__).with_name("nature-manifest.json")
SEED = 73141
random.seed(SEED)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def material(name, color, roughness=0.8, metallic=0, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = roughness
    p.inputs["Metallic"].default_value = metallic
    if emission:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emission
    return m


MATS = [
    material("bark_umber", (.12, .075, .042)),
    material("bark_sunlit_ridge", (.27, .18, .10)),
    material("leaf_jade", (.045, .21, .085)),
    material("leaf_copper_green", (.16, .32, .105)),
    material("leaf_silver_tip", (.30, .43, .17)),
    material("reed_gold", (.40, .32, .12)),
    material("reed_seed_head", (.18, .105, .045)),
    material("basalt_wet", (.10, .15, .16), .55),
    material("sandstone_carved", (.49, .36, .22)),
    material("stone_moss", (.21, .28, .135)),
    material("antique_brass", (.58, .32, .085), .31, .76),
    material("terracotta", (.40, .125, .045)),
    material("lotus_petal_ivory", (.91, .64, .40), .5),
    material("lotus_petal_rose", (.57, .15, .22), .5),
    material("oil_dark", (.035, .024, .013), .15),
    material("diya_flame_amber", (1, .32, .035), .28, emission=3.5),
    material("lantern_cobalt", (.025, .13, .24), .32, .45),
    material("lantern_frosted_gold", (1, .57, .18), .5, emission=1.7),
]
BARK, RIDGE, LEAF, LEAF2, LEAF3, REED, SEED_HEAD, ROCK, STONE, MOSS, BRASS, CLAY, IVORY, ROSE, OIL, FLAME, COBALT, GLASS = range(len(MATS))


class MeshBuilder:
    def __init__(self, name, natural_size, purpose):
        self.name, self.natural_size, self.purpose = name, natural_size, purpose
        self.v, self.f, self.mi = [], [], []

    def add(self, verts, faces, mat):
        start = len(self.v)
        self.v.extend([tuple(v) for v in verts])
        self.f.extend([tuple(start + i for i in f) for f in faces])
        self.mi.extend([mat] * len(faces))

    def tube(self, points, radii, mat, sides=8, ridge=0):
        verts = []
        for i, point in enumerate(points):
            tangent = Vector(points[min(i + 1, len(points) - 1)]) - Vector(points[max(i - 1, 0)])
            tangent.normalize()
            reference = Vector((0, 1, 0)) if abs(tangent.y) < .9 else Vector((1, 0, 0))
            a = tangent.cross(reference).normalized()
            b = tangent.cross(a).normalized()
            for j in range(sides):
                t = j * math.tau / sides
                rr = radii[i] * (1 + ridge * math.sin(j * 2.7 + i * .6))
                verts.append(Vector(point) + rr * (math.cos(t) * a + math.sin(t) * b))
        faces = [tuple(reversed(range(sides)))]
        for i in range(len(points) - 1):
            for j in range(sides):
                faces.append((i*sides+j, i*sides+(j+1)%sides, (i+1)*sides+(j+1)%sides, (i+1)*sides+j))
        faces.append(tuple((len(points)-1)*sides+j for j in range(sides)))
        self.add(verts, faces, mat)

    def ellipsoid(self, pos, size, mat, rings=6, sides=12, twist=0):
        verts = []
        for i in range(rings + 1):
            phi = math.pi * (.001 + .998*i/rings)
            for j in range(sides):
                theta = math.tau*j/sides + twist
                verts.append((pos[0]+size[0]*math.sin(phi)*math.cos(theta), pos[1]+size[1]*math.cos(phi), pos[2]+size[2]*math.sin(phi)*math.sin(theta)))
        faces = []
        for i in range(rings):
            for j in range(sides):
                faces.append((i*sides+j, i*sides+(j+1)%sides, (i+1)*sides+(j+1)%sides, (i+1)*sides+j))
        self.add(verts, faces, mat)

    def box(self, center, size, mat):
        x, y, z = center
        a, b, c = (s/2 for s in size)
        self.add([(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
                  (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)],
                 [(0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2)], mat)

    def lathe(self, profile, mat, sides=24, pos=(0,0,0)):
        verts = [(pos[0]+r*math.cos(j*math.tau/sides),pos[1]+y,pos[2]+r*math.sin(j*math.tau/sides)) for y,r in profile for j in range(sides)]
        faces = []
        for i in range(len(profile)-1):
            for j in range(sides):
                faces.append((i*sides+j,(i+1)*sides+j,(i+1)*sides+(j+1)%sides,i*sides+(j+1)%sides))
        self.add(verts,faces,mat)

    def leaf(self, start, end, width, mat, bend=.1):
        a,b = Vector(start),Vector(end)
        side=(b-a).cross(Vector((0,1,0))).normalized()*width
        if side.length < .001:
            side=Vector((width,0,0))
        verts=[a]
        for t in (.25,.55,.82):
            mid=a.lerp(b,t)+Vector((0,math.sin(t*math.pi)*bend,0))
            w=math.sin(t*math.pi)
            verts += [mid-side*w,mid+Vector((0,width*.12,0)),mid+side*w]
        verts += [b]
        faces=[(0,1,2),(0,2,3),(1,4,5,2),(2,5,6,3),(4,7,8,5),(5,8,9,6),(7,10,8),(8,10,9)]
        # Opaque double-sided material avoids alpha sorting and duplicate mesh faces.
        self.add(verts,faces,mat)

    def finish(self):
        mins=[min(v[i] for v in self.v) for i in range(3)]
        maxs=[max(v[i] for v in self.v) for i in range(3)]
        ext=[maxs[i]-mins[i] for i in range(3)]
        assert all(v > 0 and math.isfinite(v) for v in ext)
        normalized=[((v[0]-mins[0])/ext[0]-.5,(v[1]-mins[1])/ext[1],(v[2]-mins[2])/ext[2]-.5) for v in self.v]
        # Blender x/y/z = Godot x/-z/y; glTF export returns Godot x/y/z.
        verts=[(v[0],-v[2],v[1]) for v in normalized]
        mesh=bpy.data.meshes.new(self.name+"_mesh")
        mesh.from_pydata(verts,[],self.f)
        mesh.update()
        if mesh.validate(verbose=True):
            raise RuntimeError(f"Invalid generated mesh topology: {self.name}")
        obj=bpy.data.objects.new(self.name,mesh)
        bpy.context.collection.objects.link(obj)
        for m in MATS: mesh.materials.append(m)
        for polygon,mat in zip(mesh.polygons,self.mi):
            polygon.material_index=mat
            polygon.use_smooth=mat not in (STONE,COBALT)
        obj["purpose"]=self.purpose
        obj["collision"]="none"
        obj["anchor"]="base_center"
        mesh.calc_loop_triangles()
        return {"preset":self.name,"node":self.name,"natural_dimensions_metres":self.natural_size,
                "vertices":len(mesh.vertices),"triangles":len(mesh.loop_triangles),
                "material_slots_used":len(set(self.mi)),"purpose":self.purpose,
                "bounds":{"min":[-.5,0,-.5],"max":[.5,1,.5]},"collision":"none"}


def reeds():
    b=MeshBuilder("reed_cluster",[2.2,2.4,1.8],"Layered narrow reeds with seed heads, kept away from cross-mid sightline")
    for i in range(21):
        angle=i*2.399963
        radius=.72*math.sqrt((i+.5)/21)
        x,z=radius*math.cos(angle),radius*.65*math.sin(angle)
        h=random.uniform(1.1,2.25)
        lean=random.uniform(-.22,.22)
        b.tube([(x,0,z),(x+lean*.2,h*.35,z),(x+lean*.6,h*.7,z+.03),(x+lean,h,z+.1)], [.025,.022,.017,.012],REED,6)
        b.ellipsoid((x+lean,h-.12,z+.1),(.05,.17,.05),SEED_HEAD,5,8)
        for k in range(3):
            t=.22+k*.19
            a=angle+k*2.0
            start=(x+lean*t,h*t,z)
            end=(x+math.cos(a)*.55,h*(t+.22),z+math.sin(a)*.55)
            b.leaf(start,end,.055,(LEAF,LEAF2,REED)[k],.16)
    return b.finish()


def mangrove():
    b=MeshBuilder("mangrove_roots",[8,8.5,7],"Lush layered mangrove/banyan canopy with visible buttress roots and broad leaf sprays")
    trunk=[(0,.15,0),(.12,1.3,.05),(-.13,2.7,.15),(.23,4.0,.03),(.15,5.1,.1)]
    b.tube(trunk,[.62,.48,.40,.30,.17],BARK,12,.13)
    for j in range(10):
        a=j*math.tau/10
        p=[(.1,1.8,.1),(math.cos(a)*.6,1.1,math.sin(a)*.6),(math.cos(a)*1.25,.35,math.sin(a)*1.25),(math.cos(a)*2.0,.04,math.sin(a)*2.0)]
        b.tube(p,[.20,.18,.12,.035],BARK if j%2 else RIDGE,8,.12)
    for j in range(11):
        a=j*2.399963
        level=3.2+(j%4)*.42
        reach=2.0+(j%3)*.35
        end=Vector((math.cos(a)*reach,level+1.7,math.sin(a)*reach))
        b.tube([(.05,level,0),(math.cos(a)*.8,level+.6,math.sin(a)*.8),end],[.21,.13,.025],BARK,8,.1)
        # R2: opaque overlapping lobes preserve a legible green canopy at gameplay
        # distance; broad individual leaves break their edge instead of becoming
        # subpixel horizontal lines. These remain original mesh geometry.
        b.ellipsoid(end+Vector((0,.25,0)),(.94,.57,.84),LEAF if j%3==0 else LEAF2,6,12,j*.3)
        for twig in range(3):
            a2=a+(twig-1)*.7
            twig_end=end+Vector((math.cos(a2)*.7,.35+twig*.12,math.sin(a2)*.7))
            b.tube([end-Vector((0,.15,0)),twig_end],[.045,.008],RIDGE,5)
            b.ellipsoid(twig_end+Vector((0,.12,0)),(.57,.37,.52),LEAF2 if twig%2 else LEAF,5,10,j*.2)
            for k in range(15):
                t=k/15
                origin=end.lerp(twig_end,t)
                la=a2+(-1 if k%2 else 1)*1.05
                tip=origin+Vector((math.cos(la)*random.uniform(.45,.85),random.uniform(-.23,.42),math.sin(la)*random.uniform(.45,.85)))
                b.leaf(origin,tip,.17,(LEAF,LEAF2,LEAF3)[(j+k)%3],.12)
            for k in range(8):
                la=k*2.399963+twig
                origin=twig_end+Vector((math.cos(la)*.41,.19+(k%3)*.06,math.sin(la)*.36))
                tip=origin+Vector((math.cos(la)*.45,-.12+(k%3)*.23,math.sin(la)*.40))
                b.leaf(origin,tip,.19,(LEAF2,LEAF3,LEAF2)[k%3],.14)
        if j%3==0:
            x,z=end.x*.65,end.z*.65
            b.tube([(x,level+.9,z),(x+.05,2.0,z+.03),(x+.12,.10,z-.05)],[.035,.023,.012],RIDGE,5)
    return b.finish()


def lotus_leaf(b,x,z,r,rot):
    verts=[(x,.06,z)]
    for j in range(23):
        a=rot+.15+j*(math.tau-.30)/22
        verts.append((x+r*math.cos(a),.055+.025*math.cos(a*3),z+r*math.sin(a)))
    faces=[(0,j,j+1) for j in range(1,23)]
    b.add(verts,faces,LEAF2)
    for k in range(7):
        a=rot+.2+k*(math.tau-.4)/6
        b.tube([(x,.069,z),(x+r*.92*math.cos(a),.075,z+r*.92*math.sin(a))],[.006,.001],LEAF3,4)


def flower(b,center,r):
    x,y,z=center
    b.ellipsoid((x,y+.10,z),(r*.28,.12,r*.28),BRASS,4,10)
    for ring in range(2):
        for j in range(9):
            a=(j+ring*.5)*math.tau/9
            start=(x+math.cos(a)*r*.08,y+.07,z+math.sin(a)*r*.08)
            tip=(x+math.cos(a)*r*(1-ring*.3),y+.12+ring*.23,z+math.sin(a)*r*(1-ring*.3))
            b.leaf(start,tip,r*.19,IVORY if ring else ROSE,.24)


def lotus():
    b=MeshBuilder("lotus_cluster",[2.8,.65,2.3],"Low lotus pads with sculpted rose/ivory flowers; no alpha planes")
    for x,z,r,rot in [(-.7,-.25,.65,.2),(.3,.4,.72,1.2),(.75,-.45,.5,2.9),(-.55,.65,.42,.7)]:
        lotus_leaf(b,x,z,r,rot)
    flower(b,(-.35,.11,-.05),.42)
    flower(b,(.65,.10,.27),.29)
    return b.finish()


def diya():
    b=MeshBuilder("diya_niche",[.8,1.3,.60],"Carved pointed niche, terracotta oil bowl and warm emissive flame")
    b.box((0,.15,0),(.70,.30,.52),STONE)
    b.box((0,.68,-.16),(.66,1.04,.13),ROCK)
    for x in (-.29,.29):
        b.box((x,.66,-.04),(.10,.96,.24),STONE)
        for y in (.36,.66,.96):
            b.box((x,y,.085),(.12,.035,.045),BRASS)
    arc=[]
    for i in range(13):
        t=i/12
        arc.append((-.29+.58*t,1.10+.22*math.sin(math.pi*t),-.025))
    b.tube(arc,[.055]*13,STONE,8)
    b.lathe([(0,.02),(.04,.17),(.12,.24),(.15,.25),(.17,.23),(.10,.18),(.07,.03)],CLAY,24,(0,.3,.06))
    b.lathe([(0,.195),(0,.0)],OIL,24,(0,.421,.06))
    b.ellipsoid((0,.54,.07),(.045,.13,.045),FLAME,8,10)
    b.tube([(0,.43,.10),(.012,.50,.11)],[.011,.007],SEED_HEAD,6)
    return b.finish()


def lantern():
    b=MeshBuilder("transit_lantern",[.72,1.45,.72],"Ornate hanging lantern with brass cage, cobalt canopy and warm glass")
    b.lathe([(0,.08),(.06,.18),(.14,.28),(.18,.27)],BRASS,16)
    b.lathe([(.18,.22),(.28,.30),(.68,.30),(.82,.22)],GLASS,8)
    for j in range(8):
        a=j*math.tau/8
        b.tube([(math.cos(a)*r,y,math.sin(a)*r) for y,r in[(.14,.27),(.28,.31),(.68,.31),(.83,.24)]],[.025]*4,BRASS,6)
    b.lathe([(.80,.23),(.85,.37),(.90,.34),(1.05,.13),(1.09,.06)],COBALT,16)
    b.lathe([(.84,.36),(.87,.36)],BRASS,16)
    b.tube([(0,1.07,0),(0,1.36,0)],[.025,.025],BRASS,8)
    b.lathe([(1.10,.05),(1.14,.08),(1.18,.05)],BRASS,12)
    b.lathe([(1.25,.04),(1.29,.075),(1.33,.04)],BRASS,12)
    return b.finish()


def shrine():
    b=MeshBuilder("swamp_shrine",[3.4,4.6,3.2],"Original mossed serpent shrine, fluted pillars and layered lotus crown")
    for y,w in[(.12,3.2),(.35,2.8),(.58,2.4)]:
        b.box((0,y,0),(w,.22,w*.85),STONE)
    b.box((0,1.55,-.50),(2.1,1.8,.65),ROCK)
    for x in(-.9,.9):
        b.lathe([(.7,.23),(.83,.27),(.95,.19),(2.4,.14),(2.5,.26),(2.65,.25)],STONE,12,(x,0,.50))
        for j in range(8):
            a=j*math.tau/8
            b.tube([(x+.16*math.cos(a),1,.50+.16*math.sin(a)),(x+.13*math.cos(a),2.35,.50+.13*math.sin(a))],[.022,.017],RIDGE,4)
    for y,w in[(2.65,2.55),(2.87,2.30),(3.08,1.95),(3.30,1.60),(3.51,1.20)]:
        b.box((0,y,0),(w,.21,w*.8),STONE)
        b.box((0,y+.06,0),(w+.10,.04,w*.8+.10),BRASS)
    b.lathe([(3.6,.48),(3.84,.32),(4.10,.15),(4.32,0)],BRASS,16)
    serpent=[(-.18,.7,.35),(.26,.95,.36),(-.25,1.25,.36),(.18,1.57,.36),(0,1.9,.36)]
    b.tube(serpent,[.09,.10,.09,.085,.06],BRASS,10)
    b.ellipsoid((0,2.12,.37),(.28,.30,.07),BRASS,6,12)
    b.ellipsoid((0,2.12,.44),(.12,.22,.055),ROCK,5,10)
    for x,z in[(-1.1,-.9),(.9,-.7),(-.8,.5)]:
        b.ellipsoid((x,.6,z),(.32,.065,.25),MOSS,3,8)
    return b.finish()


def rocks():
    b=MeshBuilder("rock_island",[3.0,1.2,2.5],"Faceted wet rocks with moss and a small emergent lotus")
    for i in range(7):
        a=i*2.39996
        rr=.6*math.sqrt(i/7)
        b.ellipsoid((rr*math.cos(a),.18+(i%3)*.06,rr*math.sin(a)),(.60+(i%2)*.2,.30+(i%3)*.08,.51),ROCK,4,9,i*.2)
    for x,z in[(-.4,-.1),(.4,.3)]:
        b.ellipsoid((x,.55,z),(.3,.04,.22),MOSS,3,9)
    flower(b,(-.20,.56,.02),.26)
    return b.finish()


presets=[reeds(),mangrove(),lotus(),diya(),lantern(),shrine(),rocks()]
assert sum(p["triangles"] for p in presets)<45000, "Nature kit triangle budget exceeded"
OUT.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT),export_format="GLB",export_yup=True,
                         export_animations=False,export_cameras=False,export_lights=False,
                         export_extras=True,export_materials="EXPORT")


def audit_export(path):
    """Read actual exported accessors rather than trusting authoring mesh bounds."""
    data=path.read_bytes()
    magic,version,size=struct.unpack_from("<III",data)
    assert (magic,version,size)==(0x46546c67,2,len(data))
    json_size,json_kind=struct.unpack_from("<II",data,12)
    assert json_kind==0x4e4f534a
    document=json.loads(data[20:20+json_size])
    binary_offset=20+json_size
    bin_size,bin_kind=struct.unpack_from("<II",data,binary_offset)
    assert bin_kind==0x004e4942
    binary=data[binary_offset+8:binary_offset+8+bin_size]
    assert not document.get("animations") and not document.get("skins") and not document.get("cameras")
    assert all(not node.get("children") for node in document["nodes"])
    assert len(document["nodes"])==7

    def accessor(index):
        a=document["accessors"][index]
        view=document["bufferViews"][a["bufferView"]]
        fmt={5123:"H",5125:"I",5126:"f"}[a["componentType"]]
        width={"SCALAR":1,"VEC3":3}[a["type"]]
        item=struct.Struct("<"+fmt*width)
        stride=view.get("byteStride",item.size)
        start=view.get("byteOffset",0)+a.get("byteOffset",0)
        result=[item.unpack_from(binary,start+i*stride) for i in range(a["count"])]
        assert all(math.isfinite(n) for entry in result for n in entry)
        return result

    audit=[]
    for node in document["nodes"]:
        assert node["name"] in [p["preset"] for p in presets]
        assert not any(k in node for k in ("matrix","translation","rotation","scale"))
        positions=[]
        triangles=0
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            points=accessor(primitive["attributes"]["POSITION"])
            normals=accessor(primitive["attributes"]["NORMAL"])
            indices=accessor(primitive["indices"])
            assert all(0<=i[0]<len(points) for i in indices)
            assert len(indices)%3==0
            assert all(abs(sum(n*n for n in normal)-1)<.001 for normal in normals)
            triangles+=len(indices)//3
            positions.extend(points)
        mins=[min(v[i] for v in positions) for i in range(3)]
        maxs=[max(v[i] for v in positions) for i in range(3)]
        assert max(abs(v-e) for v,e in zip(mins,[-.5,0,-.5]))<.000001
        assert max(abs(v-e) for v,e in zip(maxs,[.5,1,.5]))<.000001
        audit.append({"node":node["name"],"triangles":triangles,"bounds_min":mins,"bounds_max":maxs,
                      "finite_positions_and_unit_normals":True,"valid_indices":True})
    assert sum(a["triangles"] for a in audit)==sum(p["triangles"] for p in presets)
    return {"passed":True,"scope":"Actual GLB nodes, bounds, triangle counts, finite positions, unit normals, valid indices and no transform/animation/camera children", "nodes":audit}


artifact_audit=audit_export(OUT)
payload={"schema_version":1,"kit":"yuga-original-nature","source_script":"art/world/build-nature.py",
         "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         "asset":"assets/world/nature.glb","asset_sha256":hashlib.sha256(OUT.read_bytes()).hexdigest(),
         "asset_bytes":OUT.stat().st_size,"seed":SEED,"blender_version":bpy.app.version_string,
         "coordinate_contract":"Godot metres Y-up; base-centred unit bounds; map scale is final dimensions",
         "provenance":"Original procedural geometry and authored material colors; no imported models, textures or commercial game assets",
         "license":"Repository licensing applies to this original authored kit; no third-party asset attribution required",
         "placements":"Canonical confluence-map.json owns placements. Meshes add no collision or scene lights.",
         "triangle_budget":45000,"triangles_total":sum(p["triangles"] for p in presets),
         "render_cost_note":"One mesh node per preset; separate primitives per used material; opaque geometry, no alpha cards. Canopies should be used sparingly.",
         "presets":presets,
         "artifact_audit":artifact_audit,
         "quality_status":"Original modular environment prototype; actual integrated renderer review remains required"}
MANIFEST.write_text(json.dumps(payload,indent=2)+"\n")
print(json.dumps({"asset":str(OUT),"bytes":OUT.stat().st_size,"triangles":payload["triangles_total"],"presets":len(presets)}))
