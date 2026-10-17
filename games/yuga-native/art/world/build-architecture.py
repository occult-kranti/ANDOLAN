"""Original Confluence modular architecture, authored with Blender 4.3+.

Run from any directory:
  blender --background --threads 1 --python .../build-architecture.py

Eight root nodes form a library, not a scene to display in its entirety. The
native map instantiates a named root at base centre with world-dimension scale.
All geometry, palette and small PBR textures are authored here. No source game
assets, downloaded models, add-ons or external textures are used.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import time

import bpy
import bmesh
import numpy as np
from mathutils import Vector

START = time.monotonic()
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "assets/world/architecture.glb"
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
MATS = []


def material(name, color, rough=.8, metal=0, emit=0, stone=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metal
    if emit:
        shader.inputs["Emission Color"].default_value = (*color, 1)
        shader.inputs["Emission Strength"].default_value = emit
    if stone:
        size = 256
        yy, xx = np.mgrid[:size, :size].astype(np.float32) / size
        field = np.zeros_like(xx)
        # R1 renderer review exposed broad, high-contrast camouflage bands.
        # Keep architecture readable: gentle mineral colour variation, not
        # metre-scale stains competing with cornices and shallow carvings.
        for frequency, strength in [(2, .012), (7, .007), (23, .004), (59, .002)]:
            field += np.sin(2 * math.pi * (xx * frequency + yy * (frequency+1))) * strength
            field += np.cos(2 * math.pi * (xx * (frequency+2) - yy * frequency)) * strength * .6
        rgb = np.clip(np.asarray(color)[None, None, :] * (1 + field[..., None]), 0, 1)
        dx = (np.roll(field, -1, axis=1) - np.roll(field, 1, axis=1)) * .10
        dy = (np.roll(field, -1, axis=0) - np.roll(field, 1, axis=0)) * .10
        normal = np.stack([-dx, -dy, np.ones_like(dx)], axis=-1)
        normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
        for suffix, pixels, noncolor in [("albedo", rgb, False), ("normal", normal*.5+.5, True)]:
            image = bpy.data.images.new(name+"_"+suffix, width=size, height=size, alpha=False)
            if noncolor:
                image.colorspace_settings.name = "Non-Color"
            rgba = np.concatenate([pixels, np.ones((size, size, 1))], axis=-1)
            image.pixels.foreach_set(rgba.astype(np.float32).ravel())
            image.pack()
            node = mat.node_tree.nodes.new("ShaderNodeTexImage")
            node.image = image
            if noncolor:
                n = mat.node_tree.nodes.new("ShaderNodeNormalMap")
                n.inputs["Strength"].default_value = .12
                mat.node_tree.links.new(node.outputs["Color"], n.inputs["Color"])
                mat.node_tree.links.new(n.outputs["Normal"], shader.inputs["Normal"])
            else:
                mat.node_tree.links.new(node.outputs["Color"], shader.inputs["Base Color"])
    MATS.append(mat)
    return len(MATS)-1


SAND = material("Confluence_honey_sandstone", (.53,.415,.29), stone=True)
LIME = material("Confluence_carved_limestone", (.70,.635,.50), stone=True)
DARK = material("Confluence_closed_recess", (.055,.067,.071), .94)
BRASS = material("Confluence_aged_brass", (.43,.255,.079), .39, .72)
TEAL = material("Confluence_teal_ceramic", (.035,.21,.20), .36)
PLASTER = material("Confluence_warm_ivory", (.64,.63,.53), stone=True)
INDIGO = material("Confluence_transit_indigo", (.045,.087,.17), .46)
GLASS = material("Confluence_opaque_blue_glass", (.035,.115,.18), .23, .42)
LEAF = material("Confluence_roof_planting", (.12,.235,.12), .89)
LIGHT = material("Confluence_warm_window", (.74,.36,.095), .5, emit=.45)


class Builder:
    def __init__(self, name):
        self.name = name
        self.vertices, self.faces, self.materials, self.smooth = [], [], [], []
        self.components = {}

    def mesh(self, vertices, faces, mat, smooth=False, label="detail", yaw=0, offset=(0,0,0)):
        """Inputs use shared X,Y-up,Z; convert once to Blender X,Y,Z-up."""
        start = len(self.vertices)
        c, s = math.cos(yaw), math.sin(yaw)
        for x, y, z in vertices:
            x, z = x*c+z*s+offset[0], -x*s+z*c+offset[2]
            self.vertices.append((x, -z, y+offset[1]))
        self.faces.extend(tuple(start+i for i in face) for face in faces)
        self.materials.extend([mat]*len(faces))
        self.smooth.extend([smooth]*len(faces))
        self.components[label] = self.components.get(label, 0)+1

    def box(self, pos, size, mat, bevel=.0, yaw=0, label="masonry"):
        x, y, z = [d/2 for d in size]
        b = min(bevel, x*.4, y*.4, z*.4)
        if b <= 0:
            vertices = [(sx*x, sy*y, sz*z) for sy in [-1,1] for sz in [-1,1] for sx in [-1,1]]
            faces = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
        else:
            # Four eight-sided rings produce chamfered edges and corners.
            vertices=[]
            for height, hx, hz in [(-y,x-b,z-b),(-y+b,x,z),(y-b,x,z),(y,x-b,z-b)]:
                bb = b*.7
                vertices += [(a,height,c) for a,c in [(-hx+bb,-hz),(hx-bb,-hz),(hx,-hz+bb),(hx,hz-bb),(hx-bb,hz),(-hx+bb,hz),(-hx,hz-bb),(-hx,-hz+bb)]]
            faces=[tuple(range(7,-1,-1)),tuple(range(24,32))]
            for row in range(3):
                for i in range(8):
                    j=(i+1)%8
                    faces.append((row*8+i,row*8+j,(row+1)*8+j,(row+1)*8+i))
        self.mesh(vertices,faces,mat,label=label,yaw=yaw,offset=pos)

    def cylinder(self, pos, radius, height, mat, top=None, segments=16, label="column"):
        top = radius if top is None else top
        vertices = [(math.cos(i*math.tau/segments)*r, h, math.sin(i*math.tau/segments)*r)
                    for r,h in [(radius,-height/2),(top,height/2)] for i in range(segments)]
        faces=[tuple(range(segments-1,-1,-1)),tuple(range(segments,2*segments))]
        faces += [(i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments)]
        self.mesh(vertices,faces,mat,False,label,offset=pos)

    def facade(self, side, u, y, w, h, mat, depth=.008, d=.483, label="facade_panel", bevel=0):
        angle=side*math.pi/2
        self.box((u*math.cos(angle)+d*math.sin(angle),y,-u*math.sin(angle)+d*math.cos(angle)),
                 (w,h,depth),mat,bevel,angle,label)

    def arch(self, side, u, spring, radius, band, mat=LIME, d=.489, depth=.009):
        """Closed ornamental facade arch, not an apparently open passage."""
        vertices=[]
        n=16
        for face_depth in [d-depth/2,d+depth/2]:
            for r in [radius,radius+band]:
                for i in range(n+1):
                    t=math.pi*i/n
                    vertices.append((u+math.cos(t)*r,spring+math.sin(t)*r,face_depth))
        k=n+1
        faces=[]
        for i in range(n):
            faces.extend([(i,i+1,k+i+1,k+i),(2*k+i,3*k+i,3*k+i+1,2*k+i+1),
                          (i,2*k+i,2*k+i+1,i+1),(k+i,k+i+1,3*k+i+1,3*k+i)])
        faces += [(0,k,3*k,2*k),(n,2*k+n,3*k+n,k+n)]
        self.mesh(vertices,faces,mat,label="carved_arch",yaw=side*math.pi/2)

    def roof(self, low, high, width, depth, mat, top_ratio=.6, cx=0, cz=0):
        vertices=[]
        for y, ratio in [(low,1),(high,top_ratio)]:
            vertices += [(cx+x*width*ratio/2,y,cz+z*depth*ratio/2) for z in [-1,1] for x in [-1,1]]
        self.mesh(vertices,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)],mat,label="tapered_roof")

    def finish(self):
        mesh=bpy.data.meshes.new(self.name+"_geometry")
        mesh.from_pydata(self.vertices,[],self.faces)
        mesh.update()
        for mat in MATS:
            mesh.materials.append(mat)
        for polygon,mat,smooth in zip(mesh.polygons,self.materials,self.smooth):
            polygon.material_index=mat
            polygon.use_smooth=smooth
        bm=bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        uv=mesh.uv_layers.new(name="Original_stone_projection")
        for face in mesh.polygons:
            axis=max(range(3),key=lambda i:abs(face.normal[i]))
            axes=[i for i in range(3) if i != axis]
            for loop in face.loop_indices:
                point=mesh.vertices[mesh.loops[loop].vertex_index].co
                uv.data[loop].uv=(point[axes[0]]*7,point[axes[1]]*7)
        obj=bpy.data.objects.new(self.name,mesh)
        bpy.context.collection.objects.link(obj)
        obj["preset"]=self.name
        obj["anchor"]="base_center"
        obj["collision"]="none; authority boxes owned by runtime"
        coords=np.array([(v.co.x,v.co.z,-v.co.y) for v in mesh.vertices])
        lo,hi=coords.min(axis=0),coords.max(axis=0)
        assert np.all(lo >= np.array([-.5,0,-.5])-1e-6), (self.name,lo)
        assert np.all(hi <= np.array([.5,1,.5])+1e-6), (self.name,hi)
        mesh.calc_loop_triangles()
        return {"node":self.name,"vertices":len(mesh.vertices),"triangles":len(mesh.loop_triangles),
                "material_indices":sorted(set(self.materials)),"material_slots_used":len(set(self.materials)),
                "bounds_y_up":{"min":lo.tolist(),"max":hi.tolist()},"components":self.components}


def ledge(b,y,width=1,depth=1,mat=LIME,height=.025):
    b.box((0,y,0),(width,height,depth),mat,.0025,label="carved_cornice")


def temple_body():
    b=Builder("temple_sandstone")
    b.box((0,.5,0),(.96,.94,.96),SAND,.008,label="closed_authority_volume")
    ledge(b,.025,1,1,LIME,.05)
    for y in [.09,.33,.66,.93,.985]:
        ledge(b,y,1,1,LIME,.024 if y<.96 else .03)
        if y<.96:
            ledge(b,y+.018,.982,.982,BRASS,.006)
    for side in range(4):
        for u in [-.38,-.19,0,.19,.38]:
            # Dark coloured insets have masonry backing; no actual opening.
            b.facade(side,u,.205,.13,.18,DARK,d=.481)
            b.arch(side,u,.22,.055,.014)
            for offset in [-.069,.069]:
                b.facade(side,u+offset,.18,.018,.15,LIME,d=.49,bevel=.002)
            for bar in [-.03,0,.03]:
                b.facade(side,u+bar,.188,.005,.12,BRASS,d=.491,label="closed_jali_bar")
            b.facade(side,u,.133,.14,.014,LIME,d=.49)
            # Upper jali: diagonals and mid rail inside framed closed panels.
            for y in [.48,.79]:
                b.facade(side,u,y,.115,.185,TEAL,d=.481)
                for du in [-.065,.065]:
                    b.facade(side,u+du,y,.012,.20,LIME,d=.49)
                for dy in [-.102,.102,0]:
                    b.facade(side,u,y+dy,.142,.012,LIME,d=.49)
                for du in [-.038,0,.038]:
                    b.facade(side,u+du,y,.004,.176,BRASS,d=.491,label="jali_grid")
                for dy in [-.057,.057]:
                    b.facade(side,u,y+dy,.115,.004,BRASS,d=.491,label="jali_grid")
        for u in [-.48,-.285,-.095,.095,.285,.48]:
            b.facade(side,u,.495,.017,.80,LIME,d=.488,bevel=.002,label="facade_pilaster")
            for y in [.345,.645,.925]:
                b.facade(side,u,y,.031,.028,BRASS,d=.49,label="pilaster_capital")
        # Serrated roof frieze, original decorative rhythm.
        for i in range(15):
            b.facade(side,-.455+i*.065,.955,.032,.025,TEAL,d=.491,label="frieze_inlay")
    return b


def modern_body():
    b=Builder("modern_terrace")
    b.box((0,.5,0),(.962,.98,.962),PLASTER,.006,label="closed_authority_volume")
    ledge(b,.017,1,1,INDIGO,.034)
    for y in [.20,.395,.59,.785,.985]:
        ledge(b,y,1,1,PLASTER,.03)
        ledge(b,y-.023,.987,.987,INDIGO,.01)
    for side in range(4):
        for row,y in enumerate([.115,.31,.505,.70,.895]):
            for col,u in enumerate([-.36,-.12,.12,.36]):
                b.facade(side,u,y,.193,.129,GLASS,d=.483,label="opaque_recessed_window")
                b.facade(side,u,y,.008,.133,INDIGO,d=.491,label="window_mullion")
                b.facade(side,u,y-.065,.20,.009,BRASS,d=.492,label="window_sill")
                # Solid solar fins articulate each face without fake passages.
                b.facade(side,u-.107,y,.012,.15,PLASTER,depth=.026,d=.485,label="solar_fin")
                if (side+row+col)%4==0:
                    b.facade(side,u+.045,y-.025,.071,.07,LIGHT,d=.489,label="inhabited_window")
        for u in [-.475,.475]:
            b.facade(side,u,.5,.031,.94,INDIGO,d=.484,label="transit_vertical_band")
        b.facade(side,0,.407,.63,.028,TEAL,d=.495,label="transit_frieze")
    return b


def shikhara(name="lanka_shikhara", crown=False):
    b=Builder(name)
    ledge(b,.025,1,1,LIME,.05)
    b.box((0,.16,0),(.89,.25,.89),SAND,.007,label="shrine_plinth")
    for side in range(4):
        for u in [-.28,0,.28]:
            b.facade(side,u,.16,.17,.14,TEAL,d=.45,label="closed_shrine_panel")
            b.arch(side,u,.17,.072,.014,LIME,d=.456)
    for i in range(7):
        width=.94-i*.105
        y=.29+i*.083
        b.roof(y,y+.065,width,width,SAND,.78)
        ledge(b,y+.007,width+.015,width+.015,LIME,.016)
        # Miniature shrines at cardinal corners silhouette every other tier.
        if i in [0,2,4]:
            for x,z in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                r=width*.38
                b.box((x*r,y+.05,z*r),(.055,.062,.055),LIME,.003,label="roof_kudu")
                b.roof(y+.08,y+.115,.075,.075,TEAL,.2,cx=x*r,cz=z*r)
    b.cylinder((0,.897,0),.105,.045,BRASS,top=.078,segments=24,label="crown_disc")
    b.cylinder((0,.94,0),.066,.042,BRASS,top=.045,segments=20,label="finial_neck")
    b.cylinder((0,.979,0),.045,.042,BRASS,top=.004,segments=20,label="finial_tip")
    return b


def watchtower():
    b=Builder("lanka_watchtower")
    for y,w,h in [(.04,1,.08),(.13,.88,.10),(.48,.66,.6),(.80,.84,.05),(.85,.93,.03)]:
        b.box((0,y,0),(w,h,w),SAND if h>.08 else LIME,.006,label="watchtower_stage")
    for side in range(4):
        for y in [.32,.53,.72]:
            b.facade(side,0,y,.20,.13,DARK,d=.333)
            b.arch(side,0,y+.025,.1,.016,LIME,d=.34)
            for u in [-.26,.26]:
                b.facade(side,u,y,.032,.18,LIME,d=.338)
    b.roof(.866,.95,.95,.95,TEAL,.35)
    b.cylinder((0,.975,0),.045,.05,BRASS,top=.001,segments=16,label="finial")
    return b


def transit_tower(name="transit_tower", garden=False):
    b=Builder(name)
    ledge(b,.025,1,1,INDIGO,.05)
    for center,size in [((0,.19,0),(.93,.32,.93)),((.05,.505,-.025),(.72,.31,.76)),((-.055,.79,.04),(.51,.27,.55))]:
        b.box(center,size,PLASTER,.01,label="stepped_skyline_volume")
        ytop=center[1]+size[1]/2
        b.box((center[0],ytop,center[2]),(size[0]+.025,.02,size[2]+.025),INDIGO,.002,label="skyline_canopy")
        if garden:
            for sx in [-1,1]:
                b.box((center[0]+sx*size[0]*.35,ytop+.013,center[2]),(.08,.02,size[2]*.8),LEAF,.002,label="planted_terrace")
        for side in range(4):
            for row in range(3):
                y=center[1]-size[1]*.32+row*size[1]*.3
                for col in range(4):
                    u=-size[0]*.35+col*size[0]*.2333
                    # Rectilinear window ribbons on four closed sides.
                    if side in [0,2]:
                        x=center[0]+u
                        z=center[2]+(1 if side==0 else -1)*(size[2]/2+.001)
                        b.box((x,y,z),(size[0]*.185,.055,.005),GLASS,label="skyline_window")
                    else:
                        z=center[2]+u*size[2]/size[0]
                        x=center[0]+(1 if side==1 else -1)*(size[0]/2+.001)
                        b.box((x,y,z),(.005,.055,size[2]*.185),GLASS,label="skyline_window")
    b.box((-.055,.955,.04),(.21,.07,.23),TEAL,.004,label="crown_service_volume")
    b.cylinder((-.055,.995,.04),.018,.01,BRASS,segments=12,label="beacon_cap")
    return b


def rooftop_garden():
    b=Builder("transit_garden")
    ledge(b,.022,1,1,PLASTER,.044)
    # Raised inset planters make the low broad roof detail meaningful at scale.
    for x,z,sx,sz in [(-.36,0,.16,.85),(.36,0,.16,.85),(0,-.35,.48,.16)]:
        b.box((x,.11,z),(sx,.18,sz),INDIGO,.008,label="roof_planter")
        b.box((x,.214,z),(sx*.9,.045,sz*.95),LEAF,.008,label="planted_bed")
    for x in [-.20,.20]:
        for z in [-.20,.20]:
            b.box((x,.50,z),(.035,.94,.035),BRASS,.004,label="pergola_column")
    for z in [-.27,-.18,-.09,0,.09,.18,.27]:
        b.box((0,.977,z),(.60,.046,.025),INDIGO,.003,label="pergola_roof_louvre")
    b.box((0,.09,.32),(.46,.13,.10),LIME,.006,label="roof_bench")
    return b


builders=[temple_body(),modern_body(),shikhara(),watchtower(),transit_tower(),
          transit_tower("sky_garden",True),shikhara("temple_crown",True),rooftop_garden()]
reports=[builder.finish() for builder in builders]
print("Architecture geometry completed",json.dumps(reports),flush=True)
bpy.ops.export_scene.gltf(filepath=str(OUT),export_format="GLB",export_yup=True,
    export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials="EXPORT",
    export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
data=OUT.read_bytes()
length,kind=struct.unpack_from("<II",data,12)
gltf=json.loads(data[20:20+length])
manifest={
    "schema_version":1,"id":"confluence-original-architecture","status":"art_review_candidate",
    "generator":"games/yuga-native/art/world/build-architecture.py",
    "generator_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "asset":"games/yuga-native/assets/world/architecture.glb",
    "asset_sha256":hashlib.sha256(data).hexdigest(),"asset_bytes":len(data),
    "blender_version":bpy.app.version_string,"elapsed_seconds":round(time.monotonic()-START,3),
    "license":"Original YUGA project-authored geometry and procedural textures; no third-party asset content.",
    "source_inspiration":"Original stylization of coastal sandstone courts, carved Indian temple cornices, jali screens and modern transit terraces; not a surveyed historical reconstruction.",
    "coordinates":{"up":"+Y","anchor":"base_center","bounds":{"min":[-.5,0,-.5],"max":[.5,1,.5]},
                   "scale":"world width,height,depth; each mesh root is one preset"},
    "collision":"No asset collision; native authority boxes alone block traversal. Ground facades are opaque and closed.",
    "presets":reports,"total_triangles":sum(p["triangles"] for p in reports),
    "gltf":{"nodes":len(gltf.get("nodes",[])),"meshes":len(gltf.get("meshes",[])),
            "materials":len(gltf.get("materials",[])),"images":len(gltf.get("images",[])),
            "primitives":sum(len(mesh["primitives"]) for mesh in gltf.get("meshes",[]))},
    "review_rounds":[
        {"round":1,"result":"Read shared map contract; agreed eight preset names and unit-bound base-centre API with layout and native runtime agents."},
        {"round":2,"result":"Authored closed authority-sized facade volumes, shallow backed arches/jali, cornices, modern mullions, stepped skyline and planted roof modules."},
        {"round":3,"result":"Generator verifies finite unit bounds and records geometry/material budgets; GLB exported from actual Blender mesh data."},
        {"round":4,"result":"Inspected actual native R1 temple-avenue and overview captures. Broad stone colour bands masked architectural trim. Reduced albedo variation approximately 90%, softened already subtle normal detail, warmed the mineral palette and increased grain repetition. Geometry unchanged. Matched R2 renderer review remains with parent; no production art approval claimed."}
    ],
    "limitations":["Authored modular environment candidate, not commercial-game visual parity.",
                   "No LOD meshes or hardware performance measurements yet.",
                   "Current collision is the original flat authority model; decorative roof detail is not a playable vertical route."]
}
(HERE/"architecture-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print(json.dumps({"architecture_glb":str(OUT),"sha256":manifest["asset_sha256"],"bytes":len(data),"triangles":manifest["total_triangles"]}),flush=True)
