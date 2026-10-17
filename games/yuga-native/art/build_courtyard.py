"""Build YUGA's original Lanka-inspired coastal training court.

Run: blender --background --python games/yuga-native/art/build_courtyard.py
No external assets, network, add-ons or proprietary game files are required.
Blender 4.3+. Units are metres. GLB exports Y-up; authoring coordinates are Z-up.
"""
import bpy
import math
import json
import time
import hashlib
import struct
from pathlib import Path
from collections import defaultdict
import numpy as np
from mathutils import Vector

START = time.monotonic()
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "environment"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 241016
RNG = np.random.default_rng(SEED)
GROUPS = defaultdict(list)
MATERIALS = {}
LAMPS = []
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
print("YUGA courtyard: authoring original PBR materials", flush=True)


def texture(name, color, grain=.12, metallic=False):
    """Original periodic stone/metal albedo, roughness and tangent normal maps."""
    n = 512
    y, x = np.mgrid[0:n, 0:n].astype(np.float32) / n
    field = np.zeros((n, n), dtype=np.float32)
    for freq, amplitude in [(2, .35), (5, .2), (13, .12), (37, .065), (89, .03)]:
        for _ in range(3):
            a, b = RNG.integers(1, freq + 1, size=2)
            phase = RNG.uniform(0, 2 * math.pi)
            field += np.sin(2 * math.pi * (a * x + b * y) + phase) * amplitude / 3
    field += (RNG.random((n, n)).astype(np.float32) - .5) * .08
    field = np.clip(field, -.7, .7)
    # Fine veins/pits are authored height variation, not a photo-derived texture.
    veins = np.power(np.maximum(0, np.cos(2 * math.pi * (3*x + 2*y) + field * 3)), 18)
    height = field * .65 + veins * .07
    rgb = np.clip(np.array(color)[None, None, :] * (1 + field[:, :, None]*grain*3)
                  - veins[:, :, None] * grain * .12, 0, 1)
    rough = np.clip((.48 if metallic else .79) + field*.16, .2, .95)
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 1.6
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 1.6
    normals = np.stack([-dx, -dy, np.ones_like(dx)], axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    normals = normals * .5 + .5
    def image(suffix, pixels, noncolor=False):
        im = bpy.data.images.new(name + "_" + suffix, width=n, height=n, alpha=False)
        if noncolor:
            im.colorspace_settings.name = "Non-Color"
        rgba = np.concatenate([pixels, np.ones((n,n,1))], axis=-1)
        im.pixels.foreach_set(rgba.astype(np.float32).ravel())
        im.pack()
        return im
    images = [image("albedo", rgb), image("normal", normals, True),
              image("roughness", np.repeat(rough[:, :, None], 3, axis=2), True)]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value = .75 if metallic else 0
    bsdf.inputs["Roughness"].default_value = .7
    for idx, im in enumerate(images):
        node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = im
        if idx == 0:
            mat.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
        elif idx == 1:
            normal = mat.node_tree.nodes.new("ShaderNodeNormalMap")
            normal.inputs["Strength"].default_value = .4
            mat.node_tree.links.new(node.outputs["Color"], normal.inputs["Color"])
            mat.node_tree.links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
        else:
            mat.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Roughness"])
    MATERIALS[name] = mat
    return mat


def flat(name, color, roughness=.65, metallic=0, emission=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    MATERIALS[name] = mat
    return mat


STONE = texture("Warm_carved_sandstone", (.43,.36,.27), .11)
PALE = texture("Pale_limestone", (.58,.54,.44), .07)
INDIGO = texture("Indigo_glazed_stone", (.035,.075,.12), .10)
GOLD = texture("Aged_brass", (.38,.25,.105), .06, True)
FLOOR = [flat("Courtyard_stone_%d" % i, (.30+i*.007,.28+i*.007,.24+i*.006), .88) for i in range(4)]
GROUT = flat("Limestone_mortar", (.30,.285,.25), .94)
INLAY = flat("Quiet_stone_inlay", (.28,.255,.205), .91)
RECESS = flat("Recessed_gate_soffit", (.11,.12,.115), .94)
for floor_mat in FLOOR:
    # Share the authored limestone detail maps while retaining the paving tones.
    nodes=floor_mat.node_tree.nodes
    links=floor_mat.node_tree.links
    shader=nodes.get("Principled BSDF")
    normal_tex=nodes.new("ShaderNodeTexImage")
    normal_tex.image=bpy.data.images["Pale_limestone_normal"]
    normal_map=nodes.new("ShaderNodeNormalMap")
    normal_map.inputs["Strength"].default_value=.55
    links.new(normal_tex.outputs["Color"],normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"],shader.inputs["Normal"])
    rough_tex=nodes.new("ShaderNodeTexImage")
    rough_tex.image=bpy.data.images["Pale_limestone_roughness"]
    links.new(rough_tex.outputs["Color"],shader.inputs["Roughness"])
GLOW = flat("Diyas_warm_emission", (1,.32,.055), .28, emission=5)
WATER = flat("Coastal_water", (.018,.15,.14), .19, .36)
REEDS = flat("Marsh_reeds", (.11,.20,.075), .83)
LOTUS = flat("Lotus_petal", (.54,.13,.21), .62)
DISTANT = flat("Distant_indigo_silhouettes", (.055,.085,.11), .88)


def p(x, z, h):
    return (x, -z, h)


def register(obj, name, mat, group="DECOR", smooth=False):
    obj.name = name
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    if smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    GROUPS[group + "_" + mat.name].append(obj)
    return obj


def box(name, x, z, h, sx, sz, sh, mat=STONE, group="COL", bevel=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=p(x,z,h))
    obj = bpy.context.object
    obj.scale = (sx,sz,sh)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    register(obj, name, mat, group + ("_BEVEL" if bevel else ""))
    return obj


def cylinder(name, x, z, h, radius, depth, mat=STONE, vertices=16, group="COL", r2=None):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
        radius2=radius if r2 is None else r2, depth=depth, location=p(x,z,h))
    return register(bpy.context.object, name, mat, group, smooth=True)


def orb(name, x, z, h, scale, mat=GOLD, group="DECOR", segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
        radius=1, location=p(x,z,h))
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return register(obj,name,mat,group,smooth=True)


def torus(name, x, z, h, radius, minor, mat=GOLD, group="DECOR", segments=32):
    bpy.ops.mesh.primitive_torus_add(major_segments=segments, minor_segments=6,
        major_radius=radius, minor_radius=minor, location=p(x,z,h))
    return register(bpy.context.object,name,mat,group,smooth=True)


def mesh(name, verts, faces, mat, group="DECOR", smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    register(obj,name,mat,group,smooth)
    return obj


def arch(name, x, z, bottom, radius, band, depth, mat=STONE, group="COL", angle=0, scallop=.035):
    # Voussoir ring; front/back radial faces and proper normals, open passage below.
    verts=[]
    faces=[]
    n=48
    for side in [-depth/2,depth/2]:
        for rr in [radius, radius+band]:
            for i in range(n+1):
                t=math.pi*i/n
                r=rr*(1+scallop*math.sin(9*t)**2)
                xx=math.cos(t)*r
                zz=side
                verts.append(p(x+xx*math.cos(angle)-zz*math.sin(angle),
                               z+xx*math.sin(angle)+zz*math.cos(angle),bottom+math.sin(t)*r))
    k=n+1
    for i in range(n):
        faces += [(i,i+1,k+i+1,k+i), (2*k+i,3*k+i,3*k+i+1,2*k+i+1),
                  (i,2*k+i,2*k+i+1,i+1), (k+i,k+i+1,3*k+i+1,3*k+i)]
    faces += [(0,k,3*k,2*k), (n,2*k+n,3*k+n,k+n)]
    return mesh(name,verts,faces,mat,group)


def petal(name,x,z,h,length,width,angle,mat=GOLD,vertical=False,relief=.045):
    # Eight-sided raised petal relief, actual geometry rather than a decal.
    pts=[(0,0),(.28*length,-width/2),(.72*length,-width*.42),(length,0),
         (.72*length,width*.42),(.28*length,width/2)]
    verts=[]
    for lift in [0,relief]:
        for a,b in pts:
            dx=a*math.cos(angle)-b*math.sin(angle)
            dz=a*math.sin(angle)+b*math.cos(angle)
            verts.append(p(x+dx,z+(.02+lift if vertical else dz),h+(dz if vertical else lift)))
    faces=[tuple(range(5,-1,-1)),tuple(range(6,12))]
    faces += [(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
    return mesh(name,verts,faces,mat)


def lotus(name,x,z,h,radius,mat=GOLD,vertical=False,relief=.045):
    for i in range(8):
        petal(name+"_petal",x,z,h,radius,radius*.43,i*math.pi/4,mat,vertical,relief)
    if not vertical:
        cylinder(name+"_heart",x,z,h+relief/2,radius*.16,relief,mat,16,"DECOR")


def column(x,z,height=5.4,r=.46):
    box("Column_square_foot",x,z,.18,r*3,r*3,.36,PALE,bevel=True)
    cylinder("Column_base",x,z,.46,r*1.28,.2,PALE)
    cylinder("Fluted_shaft",x,z,height*.48+.4,r,height*.88,STONE,16)
    # Repeated thin vertical flutes and ornamental capital leaves.
    for i in range(12):
        t=2*math.pi*i/12
        cylinder("Column_flute",x+math.cos(t)*r*.94,z+math.sin(t)*r*.94,
                 height*.48+.4,.035,height*.80,PALE,6,"DECOR")
    for hh,rr in [(.8,1.08),(height-.45,1.1),(height-.2,1.38)]:
        cylinder("Column_belt",x,z,hh,r*rr,.14,PALE,24,"DECOR")
    box("Carved_capital",x,z,height,r*3.2,r*3.2,.42,PALE,bevel=True)


def dome(name,x,z,h,radius,mat=INDIGO):
    # Lathed lotus-profile dome with slight ribs and a gold finial.
    profile=[(1,0),(1.04,.12),(1.02,.27),(.96,.45),(.87,.67),(.72,.90),
             (.54,1.12),(.33,1.28),(.15,1.4),(.035,1.48)]
    verts=[]
    n=40
    for rr,hh in profile:
        for i in range(n):
            t=2*math.pi*i/n
            r=radius*rr*(1+.018*math.cos(t*10))
            verts.append(p(x+r*math.cos(t),z+r*math.sin(t),h+radius*hh))
    faces=[]
    for j in range(len(profile)-1):
        for i in range(n):
            faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces.append(tuple(range(n-1,-1,-1)))
    mesh(name,verts,faces,mat,"COL",True)
    torus(name+"_rim",x,z,h+.15,radius*1.04,.09,GOLD)
    cylinder(name+"_spire",x,z,h+radius*1.63,.13,radius*.40,GOLD,12,"DECOR",.025)
    orb(name+"_finial",x,z,h+radius*1.53,(.19,.19,.22),GOLD)


def lantern(x,z,h=1.5,scale=1):
    cylinder("Lantern_pedestal",x,z,h*.43,.24*scale,h*.86,INDIGO,12)
    cylinder("Lantern_bowl",x,z,h,.34*scale,.13*scale,GOLD,16,"DECOR",.46*scale)
    orb("Lantern_flame",x,z,h+.25*scale,(.13*scale,.13*scale,.27*scale),GLOW)
    for i in range(6):
        t=i*math.pi/3
        cylinder("Lantern_cage",x+math.cos(t)*.28*scale,z+math.sin(t)*.28*scale,
                 h+.31*scale,.025*scale,.58*scale,GOLD,6,"DECOR")
    cylinder("Lantern_cap",x,z,h+.66*scale,.42*scale,.24*scale,GOLD,12,"DECOR",.05*scale)
    LAMPS.append([round(x,3),round(h+.25*scale,3),round(z,3)])


# Ground: individual bevelled slabs, visible joins, broad borders and lotus inlays.
print("YUGA courtyard: authoring paving and gate", flush=True)
box("Courtyard_foundation",0,0,-.202,44,50,.4,GROUT)
for ix in range(22):
    for iz in range(25):
        box("Honed_stone_paving",-21+ix*2,-24+iz*2,-.045,1.990,1.990,.09,
            FLOOR[(ix*7+iz*3)%4],"FLOOR_BEVEL")
for x in [-13.3,13.3]:
    box("Processional_indigo_border",x,0,.006,.30,45,.015,INDIGO,"DECOR")
    box("Processional_brass_line",x+(-.20 if x<0 else .20),0,.012,.055,45,.02,GOLD,"DECOR")
for z in [-15.5,15.5]:
    box("Court_cross_border",0,z,.01,27,.20,.02,INDIGO,"DECOR")
for x,z,r in [(0,0,1.0),(0,11,.62),(0,-11,.75)]:
    lotus("Court_lotus_inlay",x,z,.002,r,INLAY,relief=.008)
    torus("Court_mandala",x,z,.004,r*1.21,.009,INLAY,segments=64)
    torus("Court_mandala_outer",x,z,.004,r*1.30,.006,INLAY,segments=64)

# Gate: open arch, stepped towers, indigo niches and carved relief crowns.
for side in [-1,1]:
    x=side*9
    for hh,sx,sz,sh in [(.24,8,5,.48),(.62,7.6,4.7,.28),(5.1,6.8,4.1,8.7),
                        (9.6,7.2,4.5,.38),(10,7.6,4.9,.24)]:
        # Add depth behind the existing facade: a substantial occupied stone pier.
        box("Gate_tower_mass",x,-24.8,hh,sx,sz+3.6,sh,STONE,bevel=True)
    for z in [-20.87]:
        box("Gate_indigo_panel",x,z,5.3,4.6,.06,5.4,INDIGO,"DECOR")
        for xx in [-2.48,2.48]:
            box("Gate_panel_trim",x+xx,z-.05,5.3,.11,.16,5.7,PALE,"DECOR")
        for hh in [2.4,8.2]:
            box("Gate_panel_cross_trim",x,z-.05,hh,5.1,.16,.11,PALE,"DECOR")
        lotus("Gate_lotus_relief",x,z+.11,5.3,1.10,PALE,True)
    for hh in [1.2,8.8,9.9]:
        box("Gate_carved_frieze",x,-20.8,hh,7,.22,.22,PALE,"DECOR")
        for i in range(6):
            cylinder("Gate_frieze_bead",x-2.8+i*1.12,-20.65,hh,.085,.14,STONE,8,"DECOR")
    dome("Gate_lotus_dome",x,-24.8,10.2,3.45)
    for xx in [-2.7,2.7]:
        column(x+xx,-20.5,8.8,.31)
arch("Grand_scalloped_arch",0,-24.8,4.2,5.6,.74,7.5,STONE)
arch("Grand_recessed_shadow_vault",0,-25.3,4.2,5.55,.12,5.7,RECESS)
arch("Grand_arch_gold_reveal",0,-20.96,4.2,5.66,.045,.09,GOLD,"DECOR")
arch("Grand_arch_indigo_reveal",0,-20.87,4.2,6.0,.08,.09,INDIGO,"DECOR")
for x in [-5.6,5.6]:
    column(x,-21.4,4.2,.48)
box("Grand_arch_crown",0,-24.8,10.9,13.3,7.9,.45,PALE,bevel=True)
for x in range(-6,7):
    cylinder("Crown_merlon",x,-23,11.35,.30,.52,STONE,8)
    orb("Crown_bud",x,-23,11.7,(.22,.22,.30),GOLD)
dome("Central_gate_cupola",0,-23,11.3,1.55)

# Side colonnades: shallow raised galleries and repeated scalloped archways.
print("YUGA courtyard: authoring colonnades and coastal details", flush=True)
for side in [-1,1]:
    x=side*18.2
    box("Gallery_plinth",x,0,.22,5.7,35,.44,INDIGO,bevel=True)
    box("Gallery_step",side*15.1,0,.09,.8,35,.18,PALE,bevel=True)
    box("Gallery_back_wall",side*21.3,0,2.8,.5,35,5.6,STONE,bevel=True)
    for z in [-16,-10,-4,2,8,14]:
        column(side*15.8,z,5.3,.42)
        column(side*20.7,z,5.3,.35)
    for z in [-13,-7,-1,5,11]:
        arch("Gallery_scalloped_arch",side*15.8,z,3.1,2.7,.36,.65,
             STONE,"COL",math.pi/2)
        arch("Gallery_arch_reveal",side*15.4,z,3.1,2.72,.065,.09,
             PALE,"DECOR",math.pi/2)
        box("Gallery_niche",side*20.99,z,2.9,.025,2.4,2.9,INDIGO,"DECOR")
    for hh,depth in [(5.72,.30),(5.98,.15)]:
        box("Gallery_cornice",x,-1,hh,6.2,36,depth,PALE,bevel=True)
    for z in range(-17,17,4):
        box("Gallery_roof_crest",x,z,6.28,5.7,.25,.30,STONE,"DECOR")
    for z in [-12,0,12]:
        lantern(side*14.7,z,1.65,.90)
    dome("Gallery_corner_dome",x,-17,6.13,1.9)

# Shallow channels and swamp edge beyond the movement court.
for side in [-1,1]:
    box("Channel_raised_bank",side*23,0,-.3,2,55,.7,STONE)
    box("Coastal_channel",side*29,0,-.18,10,70,.12,WATER,"WATER")
    for j in range(27):
        x=side*float(RNG.uniform(24,32))
        z=float(RNG.uniform(-29,27))
        if j%3==0:
            cylinder("Lotus_leaf",x,z,-.10,float(RNG.uniform(.30,.65)),.025,REEDS,10,"DECOR")
            lotus("Marsh_lotus",x+.15,z,-.065,.24,LOTUS)
        for k in range(3):
            xx=x+float(RNG.uniform(-.18,.18)); zz=z+float(RNG.uniform(-.18,.18))
            cylinder("Marsh_reed",xx,zz,.20,.018,float(RNG.uniform(.4,.9)),REEDS,5,"DECOR",.005)
    # Low, rounded river stones at water's edge.
    for j in range(18):
        orb("Channel_stone",side*float(RNG.uniform(23.5,25)),float(RNG.uniform(-28,25)),
            -.03,(float(RNG.uniform(.3,.65)),float(RNG.uniform(.4,.8)),.25),STONE,"DECOR",12,6)

# Coastal skyline and terrace silhouettes, outside play bounds and separated from collision.
box("Sea_horizon",0,-93,-.35,320,150,.12,WATER,"WATER")
for i in range(19):
    x=-55+i*6.1
    z=-46-float(RNG.uniform(0,25))
    h=float(RNG.uniform(6,15))
    width=float(RNG.uniform(3.4,6.2))
    box("Distant_palace",x,z,h/2,width,width*.8,h,DISTANT,"SKYLINE")
    for step in range(4):
        w=width*(1-step*.18)
        box("Distant_stepped_roof",x,z,h+step*.65,w,w*.8,.68,DISTANT,"SKYLINE")
    cylinder("Distant_spire",x,z,h+3.2,.24,2,DISTANT,8,"SKYLINE",.02)

# Front corners frame the third-person camera without crossing the clear central lane.
for side in [-1,1]:
    for z in [20,23]:
        column(side*18,z,3.1,.40)
    lantern(side*12.7,20,1.25,1.0)
    for x in [side*9.4]:
        lantern(x,-20.0,1.65,1.1)

# Give all mesh surfaces deterministic world-scale box UVs, and recalculate winding.
print("YUGA courtyard: grouping geometry and building UVs", flush=True)
for group, objects in GROUPS.items():
    for obj in objects:
        data=obj.data
        uv=data.uv_layers.active or data.uv_layers.new(name="UVMap")
        for poly in data.polygons:
            axis=max(range(3),key=lambda i:abs(poly.normal[i]))
            pair=[(1,2),(0,2),(0,1)][axis]
            for li in poly.loop_indices:
                co=obj.matrix_world @ data.vertices[data.loops[li].vertex_index].co
                uv.data[li].uv=(co[pair[0]]*.5,co[pair[1]]*.5)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    obj=bpy.context.object
    obj.name=group
    # One joined mesh per collision/material group keeps import draw calls bounded.
    if "BEVEL" in group:
        mod=obj.modifiers.new("Small_chamfers","BEVEL")
        mod.width=.004 if "FLOOR" in group else .055
        mod.segments=2
        mod.affect="EDGES"
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    # Explicit triangulation is required for tangent export on carved n-gons.
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY",ngon_method="BEAUTY")
    bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.object.select_all(action="SELECT")
bpy.context.scene.unit_settings.system="METRIC"
bpy.context.scene.unit_settings.scale_length=1
path=OUT / "lanka_courtyard.glb"
print("YUGA courtyard: exporting GLB", flush=True)
bpy.ops.export_scene.gltf(filepath=str(path),export_format="GLB",use_selection=True,
    export_yup=True,export_apply=True,export_animations=False,export_cameras=False,
    export_lights=False,export_materials="EXPORT",export_texcoords=True,
    export_normals=True,export_tangents=True,export_image_format="AUTO")
objects=[o for o in bpy.context.scene.objects if o.type=="MESH"]
triangles=0
vertices=0
for obj in objects:
    obj.data.calc_loop_triangles()
    triangles += len(obj.data.loop_triangles)
    vertices += len(obj.data.vertices)
assert path.stat().st_size < 25*1024*1024, "Courtyard exceeds 25 MiB budget"
assert triangles < 300_000, "Courtyard exceeds triangle budget"
glb=path.read_bytes()
json_length=struct.unpack_from("<I",glb,12)[0]
document=json.loads(glb[20:20+json_length])
primitives=[primitive for mesh in document["meshes"] for primitive in mesh["primitives"]]
assert all("TANGENT" in primitive["attributes"] for primitive in primitives), "Missing exported tangent data"
assert all("NORMAL" in primitive["attributes"] for primitive in primitives), "Missing exported normals"
assert all("TEXCOORD_0" in primitive["attributes"] for primitive in primitives), "Missing exported UVs"
metadata={
    "name":"Original Lanka-inspired coastal training courtyard",
    "revision":"courtyard-material-refinement-v2",
    "supersedes_glb_sha256":"d1f7346aad37cecf3a8202022daea0d37cc773ba980a1a582b100540babe13da",
    "refinement_basis":"Actual native game frame build/visual-initial/frame-3.png at git 3f1b782; software-agent art review, not a concept image",
    "refinements":{"paving_joint_metres":{"before":.035,"after":.010},
        "mortar_recess_metres":{"before":.020,"after":.002},
        "paving_chamfer_metres":{"before":.018,"after":.004},
        "spawn_lotus_radius_metres":{"before":2.1,"after":.62},
        "central_lotus_radius_metres":{"before":2.1,"after":1.0},
        "arch_depth_metres":{"before":3.9,"after":7.5},
        "materials":"Pale mortar, matte stone floor inlay, quieter sandstone/gallery trim, burnished selective brass, recessed dark soffit"},
    "generator":"art/build_courtyard.py","blender_version":bpy.app.version_string,
    "seed":SEED,"coordinate_system":"metres; GLB Y-up; XZ ground, y=0 walking surface",
    "authorship":"Original procedurally authored meshes and PBR texture maps; no commercial game data or third-party assets",
    "license":"CC0-1.0 for this generated courtyard geometry and textures; generator uses repository license",
    "visual_scope":"Native training environment foundation, not a commercial-game reconstruction or parity claim",
    "play_bounds":{"x":[-22,22],"z":[-25,25]},
    "clear_central_plaza":{"x":[-12,12],"z":[-14,14],"floor_y":0},
    "spawn_feet":[0,.05,12],"target_positions":[[x,0,-8] for x in [-8,-4,0,4,8]],
    "collision":"Nodes prefixed COL_ contain structural geometry suitable for static trimesh collision. FLOOR_ paving is visual; runtime provides y=0 floor. DECOR_, WATER_ and SKYLINE_ require no collision.",
    "lantern_emission_centres":LAMPS,
    "lights":"No embedded point lights. Runtime may pool a small subset of lantern lights.",
    "mesh_objects":len(objects),"authoring_vertices":vertices,"triangles":triangles,
    "exported_vertices":sum(document["accessors"][p["attributes"]["POSITION"]]["count"] for p in primitives),
    "materials":sorted(m["name"] for m in document["materials"]),"embedded_textures":len(document["images"]),
    "all_primitives_have_normals_uvs_tangents":True,
    "glb_bytes":path.stat().st_size,"glb_sha256":hashlib.sha256(glb).hexdigest(),
    "generator_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "build_seconds":round(time.monotonic()-START,3),
}
(OUT / "lanka_courtyard.metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
print("YUGA_COURTYARD_BUILD="+json.dumps(metadata,separators=(",",":")))
