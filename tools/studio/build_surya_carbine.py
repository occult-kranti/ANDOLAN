#!/usr/bin/env python3
"""Original SURYA hero firearm, authored in Godot metres and exported by Blender.

blender4.3 --background --threads 8 --python-exit-code 1 --python tools/studio/build_surya_carbine.py
No commercial meshes/textures, generated geometry service or image projection.
The preserved reference PNG guides human-authored masses and ornament only.
"""
from pathlib import Path
import hashlib
import json
import math
import shutil
import subprocess
import time

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "games/yuga-native"
ART = PROJECT / "art/tactical/surya-carbine"
ASSET = PROJECT / "assets/tactical/surya-carbine.glb"
SPEC = ASSET.with_suffix(".json")
ART.mkdir(parents=True, exist_ok=True)
if ASSET.exists():
    raise RuntimeError("Preserve the existing candidate before exporting a successor")
started = time.monotonic()
source_commit = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def cv(p):
    return Vector((p[0], -p[2], p[1]))


def godot(p):
    return [float(p.x), float(p.z), float(-p.y)]


def empty(name, p=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(ob)
    ob.location = cv(p)
    ob.parent = parent
    return ob


root = empty("SURYA")
fixed = empty("Fixed", parent=root)
magazine = empty("Magazine", (0, -.1, -.14), root)
muzzle_socket = empty("Muzzle", (0, .012, -.65), root)


def material(name, color, metal, rough, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    if emission:
        key = "Emission Color" if "Emission Color" in p.inputs else "Emission"
        p.inputs[key].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = 1.25
    m.diffuse_color = (*color, 1)
    return m


indigo = material("SURYA | indigo fired enamel", (.026, .037, .115), .24, .34)
indigo_dark = material("SURYA | recessed indigo", (.013, .022, .055), .28, .45)
brass = material("SURYA | warm worked brass", (.61, .35, .095), .83, .34)
brass_dark = material("SURYA | brass recess", (.27, .13, .035), .8, .46)
ivory = material("SURYA | ivory ceramic inlay", (.78, .69, .49), .05, .42)
steel = material("SURYA | graphite steel", (.045, .055, .068), .82, .31)
black = material("SURYA | dark bore and rubber", (.008, .012, .017), .15, .77)
leather = material("SURYA | umber grip", (.09, .034, .014), .02, .73)
stitch = material("SURYA | stitched grip edge", (.27, .15, .057), .05, .62)
solar = material("SURYA | amber solar cells", (.95, .25, .014), .12, .21, (.8, .17, .009))
solar_light = material("SURYA | solar facet", (1, .49, .06), .08, .19, (1, .31, .027))


def finish(ob, mat, bevel=0, segments=3, parent=fixed, smooth=False):
    if mat:
        ob.data.materials.append(mat)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    if bevel:
        mod = ob.modifiers.new("Real machined edge", "BEVEL")
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = .35
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for face in ob.data.polygons:
        face.use_smooth = smooth
    if bevel or smooth:
        mod = ob.modifiers.new("Area weighted surface normals", "WEIGHTED_NORMAL")
        mod.keep_sharp = True
        mod.weight = 40
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # All authored geometry uses global source metres; a reload parent changes
    # the transform without moving its rest vertices.
    matrix = ob.matrix_world.copy()
    ob.parent = parent
    ob.matrix_world = matrix
    ob.select_set(False)
    return ob


def mesh(name, points, faces, mat, bevel=0, segments=3, parent=fixed, smooth=False):
    data = bpy.data.meshes.new(name + "Geometry")
    data.from_pydata([cv(p) for p in points], [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    return finish(ob, mat, bevel, segments, parent, smooth)


def profile(name, outline, width, mat, center_x=0, bevel=.002, parent=fixed, segments=3):
    # Profile pairs are (forward Z, up Y), extruded across weapon X.
    count = len(outline)
    pts = [(center_x + side*width/2, y, z) for side in [-1, 1] for z, y in outline]
    faces = [tuple(range(count-1, -1, -1)), tuple(range(count, 2*count))]
    faces += [(i, (i+1)%count, (i+1)%count+count, i+count) for i in range(count)]
    return mesh(name, pts, faces, mat, bevel, segments, parent)


def cube(name, p, size, mat, bevel=.002, parent=fixed):
    bpy.ops.mesh.primitive_cube_add(size=1, location=cv(p))
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = (size[0], size[2], size[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(ob, mat, bevel, 3, parent)


def cylinder(name, a, b, radius, mat, vertices=48, bevel=.001, parent=fixed):
    aa, bb = cv(a), cv(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=(bb-aa).length, location=(aa+bb)/2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (bb-aa).to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(ob, mat, bevel, 3, parent, True)


def tube(name, points, radius, mat, parent=fixed, cyclic=False, resolution=12):
    curve = bpy.data.curves.new(name+"Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    curve.resolution_u = resolution
    curve.use_fill_caps = not cyclic
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for knot, point in zip(spline.bezier_points, points):
        knot.co = cv(point)
        knot.handle_left_type = "AUTO"
        knot.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.object
    return finish(ob, mat, 0, 3, parent, True)


def ring_z(name, z0, z1, outer, inner, mat, yc=.012, count=64):
    pts = []
    for z, radius in [(z0,outer),(z1,outer),(z1,inner),(z0,inner)]:
        for i in range(count):
            angle = math.tau*i/count
            pts.append((radius*math.cos(angle),yc+radius*math.sin(angle),z))
    faces=[]
    for band in range(4):
        nxt=(band+1)%4
        for i in range(count):
            j=(i+1)%count
            faces.append((band*count+i,band*count+j,nxt*count+j,nxt*count+i))
    return mesh(name,pts,faces,mat,.0007,2,smooth=True)


def bezier_path(points, subdivisions=8):
    # Closed Catmull-Rom contour gives a smooth artist-controlled stock loop.
    result=[]
    n=len(points)
    for i in range(n):
        p0,p1,p2,p3=[Vector(points[j%n]) for j in [i-1,i,i+1,i+2]]
        for k in range(subdivisions):
            t=k/subdivisions
            result.append((2*p1+(p2-p0)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)*.5)
    return result


def stock_band(name, contour, width, depth, mat, center_x=0, bevel=.002):
    pts=[]; n=len(contour)
    for xoff, offset in [(-depth/2,-width/2),(depth/2,-width/2),(depth/2,width/2),(-depth/2,width/2)]:
        for i,p in enumerate(contour):
            tangent=(contour[(i+1)%n]-contour[(i-1)%n]).normalized()
            normal=Vector((-tangent.y,tangent.x))
            q=p+normal*offset
            pts.append((center_x+xoff,q.y,q.x))
    faces=[]
    for j in range(4):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,((j+1)%4)*n+(i+1)%n,((j+1)%4)*n+i))
    return mesh(name,pts,faces,mat,bevel,3,smooth=True)


# Structural receiver is deliberately open at the solar chamber, not a solid
# rectangular block covered with an emissive decal.
profile("SculptedForwardReceiver",[(-.326,-.038),(-.31,.042),(-.262,.059),(-.19,.06),(-.165,.045),(-.158,-.039),(-.19,-.066),(-.294,-.058)],.103,indigo,bevel=.005,segments=4)
profile("RearBreech",[(-.061,-.055),(-.065,.055),(-.045,.067),(-.015,.044),(-.01,-.028),(-.029,-.052)],.108,indigo,bevel=.004,segments=4)
profile("UpperReceiverSpine",[(-.22,.049),(-.218,.069),(-.055,.073),(-.036,.056),(-.052,.048)],.068,indigo_dark,bevel=.003)
profile("LowerReceiverSpine",[(-.19,-.061),(-.175,-.044),(-.046,-.044),(-.019,-.057),(-.04,-.068)],.073,steel,bevel=.003)
cylinder("ChamberAxle",(0,.012,-.3),(0,.012,-.028),.016,steel,64)

# Long forward shroud, restrained ribs and a real hollow muzzle.
cylinder("PrecisionBarrel",(0,.012,-.645),(0,.012,-.285),.014,steel,64,.001)
profile("LowerVentShroud",[(-.474,-.026),(-.462,-.05),(-.338,-.054),(-.309,-.024),(-.338,-.027)],.066,indigo_dark,bevel=.003)
profile("UpperBarrelBridge",[(-.482,.036),(-.478,.05),(-.339,.051),(-.319,.038)],.029,steel,bevel=.002)
for i in range(6):
    z=-.473+i*.024
    ring_z("BarrelBrassRib_%02d"%i,z-.004,z+.004,.025,.0165,brass,count=48)
for z in [-.492,-.31]:
    ring_z("ShroudCollar",z-.008,z+.008,.029,.0145,brass,count=64)
ring_z("MuzzleCrown",-.65,-.613,.023,.012,steel,count=64)
ring_z("MuzzleBrassSocket",-.623,-.609,.026,.015,brass,count=64)
ring_z("BoreShadow",-.645,-.626,.0121,.0102,black,count=48)
# Three formed, ivory-tipped lotus petals sit around the muzzle crown.
for index in range(3):
    angle=math.tau*index/3+math.pi/2
    points=[]
    for z,radius,spread in [(-.607,.024,.011),(-.621,.032,.012),(-.643,.034,.0007)]:
        for sign in [-1,1]:
            points.append((math.cos(angle)*radius-math.sin(angle)*sign*spread,.012+math.sin(angle)*radius+math.cos(angle)*sign*spread,z))
    points += [(x*.91,.012+(y-.012)*.91,z+.0015) for x,y,z in points]
    faces=[(0,1,3,5,4,2),(8,10,11,9,7,6),(0,6,7,1),(1,7,9,3),(3,9,11,5),(5,11,10,4),(4,10,8,2),(2,8,6,0)]
    petal=mesh("MuzzleLotusPetal",points,faces,brass,.0006,2)

# Organic open shoulder stock: a broad swept loop, genuine central negative
# space, separate indigo inlay and formed soft butt pad.
contour=bezier_path([(-.029,.023),(.015,.023),(.069,.062),(.096,.059),(.099,-.083),(.079,-.071),(.026,-.031),(-.03,-.027)])
stock_band("OpenStockBrassFrame",contour,.017,.055,brass,bevel=.0022)
for side in [-1,1]:
    stock_band("StockIndigoInlay",contour,.010,.004,indigo,side*.029,bevel=.001)
profile("FormedButtPad",[(.099,.072),(.116,.068),(.119,.04),(.118,-.085),(.105,-.099),(.093,-.09),(.099,-.065)],.062,black,bevel=.0035,segments=4)
profile("ButtPadBrassHeel",[(.091,-.073),(.104,-.075),(.114,-.085),(.107,-.096),(.089,-.085)],.066,brass,bevel=.0015)
ring_z("StockConnectionCollar",-.033,-.018,.042,.029,brass,yc=.005,count=64)

# Pistol grip has a changing, ergonomic curved profile and raised leather seam.
grip_outline=[(-.035,-.05),(-.008,-.048),(.005,-.08),(.039,-.145),(.037,-.185),(.011,-.195),(-.011,-.178),(-.015,-.13),(-.039,-.085)]
profile("FormedLeatherGrip",grip_outline,.046,leather,bevel=.006,segments=5)
profile("GripHeel",[(.009,-.181),(.038,-.171),(.044,-.184),(.018,-.201),(-.013,-.185),(-.015,-.174)],.052,brass,bevel=.002)
for side in [-1,1]:
    tube("LeatherPiping",[(side*.024,-.071,-.029),(side*.026,-.105,-.014),(side*.026,-.143,.015),(side*.024,-.18,.019)],.0013,stitch)
    for k in range(8):
        y=-.088-k*.011
        z=-.022+max(0,-y-.09)*.45
        tube("GripStitch",[(side*.025,y,z-.004),(side*.025,y-.003,z+.002)],.00055,stitch,resolution=3)
    for k in range(4):
        y=-.105-k*.016
        tube("GripFingerInset",[(side*.024,y,-.014+k*.006),(side*.025,y-.004,.011+k*.006)],.0009,brass_dark,resolution=4)

# Smooth trigger guard and curved trigger, with actual open finger space.
tube("CurvedTriggerGuard",[(0,-.059,-.102),(0,-.112,-.101),(0,-.135,-.073),(0,-.136,-.038),(0,-.122,-.016),(0,-.077,-.024)],.0053,brass,resolution=16)
tube("CurvedTrigger",[(0,-.061,-.063),(0,-.086,-.054),(0,-.109,-.067)],.0033,brass,resolution=16)

# Separate magazine authored around the agreed animation pivot.
mag_outline=[(-.178,-.067),(-.118,-.07),(-.128,-.12),(-.149,-.207),(-.169,-.239),(-.225,-.226),(-.209,-.194),(-.188,-.111)]
profile("CurvedMagazineCore",mag_outline,.046,indigo_dark,bevel=.003,parent=magazine,segments=4)
profile("MagazineFoot",[(-.226,-.217),(-.167,-.231),(-.166,-.243),(-.228,-.229)],.053,brass,bevel=.002,parent=magazine)
profile("MagazineFeedCollar",[(-.181,-.076),(-.118,-.076),(-.122,-.094),(-.188,-.091)],.056,brass,bevel=.0018,parent=magazine)
for side in [-1,1]:
    profile("MagazineEnamelPlate",[(-.178,-.095),(-.129,-.095),(-.156,-.218),(-.216,-.207)],.004,indigo,side*.025,.0018,magazine)
    for shift in [0,.016,.032]:
        tube("MagazineLongitudinalFlute",[(side*.028,-.102,-.173+shift),(side*.029,-.16,-.187+shift),(side*.028,-.21,-.206+shift)],.0014,brass,parent=magazine,resolution=9)
    tube("MagazineLotusArc",[(side*.03,-.192,-.211),(side*.03,-.17,-.189),(side*.03,-.148,-.165),(side*.03,-.182,-.169),(side*.03,-.21,-.174)],.0016,brass,parent=magazine,resolution=9)

# Receiver side plates and real open chamber frames are mirrored for reload
# reversals and third-person use, not only the selected hero view.
for side in [-1,1]:
    x=side*.055
    profile("ForwardOverlappingBrassPlate",[(-.339,-.024),(-.314,.036),(-.297,.048),(-.28,.044),(-.304,.012),(-.311,-.02),(-.265,-.037),(-.218,-.045),(-.205,-.061),(-.291,-.053)],.005,brass,x,.0015)
    profile("UpperChamberLip",[(-.203,.048),(-.17,.07),(-.055,.075),(-.038,.053),(-.054,.049),(-.067,.061),(-.166,.058),(-.184,.041)],.006,brass,x,.0015)
    profile("LowerChamberSweptLip",[(-.204,-.051),(-.168,-.034),(-.063,-.033),(-.029,-.047),(-.031,-.061),(-.065,-.046),(-.166,-.045),(-.19,-.066)],.006,brass,x,.0015)
    # Three amber cells sit behind genuine hexagonal metal boundaries.
    for cell,z in enumerate([-.147,-.108,-.069]):
        yc=.014
        perimeter=[]
        for k in range(6):
            angle=math.tau*k/6+math.pi/6
            perimeter.append((x+side*.004,yc+math.sin(angle)*.025,z+math.cos(angle)*.025))
        # Closed faceted gem with a proud center and darker alternating planes.
        gem_points=[(x-side*.002,yc,z)]+[(x,y,z_) for _,y,z_ in perimeter]+[(x+side*.007,yc,z)]
        gem_faces=[]
        for k in range(6):
            gem_faces += [(0,1+(k+1)%6,1+k),(7,1+k,1+(k+1)%6)]
        gem=mesh("ExposedSolarFacet",gem_points,gem_faces,solar)
        gem.data.materials.append(solar_light)
        for k,poly in enumerate(gem.data.polygons):poly.material_index=1 if k%3==0 else 0
        # Straight short segments keep the hexagon precise; beveled rods catch
        # highlights without replacing the hole with opaque plate geometry.
        for k in range(6):
            a,b=perimeter[k],perimeter[(k+1)%6]
            cylinder("HexagonalSolarLattice",a,b,.0022,brass,12,.0005)
    # Lotus silhouette with five substantial ivory inlaid petals.
    for k,angle in enumerate([-.85,-.43,0,.43,.85]):
        cy,cz=-.005,-.239
        length=.039 if k==2 else .032
        dy,dz=math.cos(angle),math.sin(angle)
        normal_y,normal_z=-dz,dy
        outline=[]
        for along,across in [(0,0),(.28,.007),(.66,.0085),(1,0),(.66,-.0085),(.28,-.007)]:
            outline.append((cz+dz*length*along+normal_z*across,cy+dy*length*along+normal_y*across))
        profile("LotusBrassPetal",outline,.003,brass,side*.058,.0008)
        inner=[(cz+(z-cz)*.8,cy+(y-cy)*.8+.0015) for z,y in outline]
        profile("LotusIvoryInlay",inner,.002,ivory,side*.0605,.0005)
    tube("LotusStem",[(side*.06,-.038,-.28),(side*.061,-.027,-.25),(side*.061,-.008,-.239)],.0018,brass,resolution=12)
    tube("FineReceiverScroll",[(side*.059,-.032,-.292),(side*.06,-.016,-.272),(side*.06,-.026,-.249),(side*.06,-.027,-.216),(side*.06,-.016,-.196)],.0011,brass,resolution=10)
    for z,y in [(-.311,-.031),(-.288,.031),(-.19,-.046),(-.173,.061),(-.046,.057),(-.03,-.045),(-.27,-.046)]:
        cylinder("SeatedHexFastener",(side*.058,y,z),(side*.063,y,z),.004,brass_dark,6,.00045)
        cylinder("FastenerCenter",(side*.0631,y,z),(side*.0637,y,z),.00145,black,12,0)
    # A compact selector is visibly supported at the rear of the receiver.
    cylinder("SelectorBoss",(side*.056,-.052,-.041),(side*.064,-.052,-.041),.008,brass,32,.0008)
    profile("SelectorLever",[(-.049,-.048),(-.027,-.047),(-.025,-.053),(-.049,-.056)],.004,brass,side*.067,.001)

# Open front blade and rear notch; sights stay aligned with bore axis.
cube("FrontSightBase",(0,.05,-.48),(.034,.011,.025),brass,.002)
profile("IvoryFrontBlade",[(-.487,.053),(-.479,.053),(-.476,.081),(-.482,.087),(-.487,.076)],.009,ivory,bevel=.0012)
cube("RearSightBase",(0,.079,-.05),(.049,.012,.027),brass,.002)
for side in [-1,1]:
    profile("IvoryRearNotchEar",[(-.059,.08),(-.04,.08),(-.041,.107),(-.052,.11),(-.06,.1)],.008,ivory,side*.019,.0015)
cube("RearNotchBed",(0,.084,-.05),(.03,.008,.014),brass,.001)
# Four raised rail pads leave real gaps, avoiding fake vent decals.
for z in [-.275,-.245,-.215,-.185]:
    cube("DorsalRailPad",(0,.071,z),(.034,.009,.019),brass,.0015)

# Merge by motion root and material for two named runtime meshes, while the
# editable .blend retains all individual authored components in a source copy.
bpy.context.view_layer.update()
original_meshes=[ob for ob in bpy.context.scene.objects if ob.type=="MESH"]
triangles=sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in original_meshes)
points=[ob.matrix_world @ v.co for ob in original_meshes for v in ob.data.vertices]
gpoints=[godot(p) for p in points]
bounds={"min":[min(p[i] for p in gpoints) for i in range(3)],"max":[max(p[i] for p in gpoints) for i in range(3)]}
assert bounds["min"][2]>=-.651 and bounds["max"][2]<=.121, bounds
print("SURYA_GEOMETRY",triangles,len(original_meshes),bounds,flush=True)
assert len(original_meshes)>90
assert 10000<=triangles<=80000, triangles

# Convenient neutral inspection cameras are source-only. The lead owns actual
# Godot render/animation acceptance; no image is substituted for that evidence.
for name,position in [("Review_Left",(-1,.2,-.28)),("Review_Right",(1,.2,-.28)),("Review_Back",(.5,.25,.65))]:
    camera=bpy.data.cameras.new(name)
    ob=bpy.data.objects.new(name,camera)
    bpy.context.collection.objects.link(ob)
    ob.location=cv(position)
    direction=cv((0,-.045,-.25))-ob.location
    ob.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    camera.type="ORTHO";camera.ortho_scale=.92
    if name=="Review_Left":bpy.context.scene.camera=ob
bpy.context.scene.render.engine="CYCLES"
bpy.context.scene.cycles.samples=24
bpy.context.scene.render.resolution_x=1280
bpy.context.scene.render.resolution_y=720
bpy.context.scene.render.resolution_percentage=100
blend=ART/"surya-carbine.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))

groups = [(parent,[ob for ob in original_meshes if ob.parent==parent]) for parent in [fixed,magazine]]
for parent,group in groups:
    bpy.ops.object.select_all(action="DESELECT")
    for ob in group:ob.select_set(True)
    bpy.context.view_layer.objects.active=group[0]
    bpy.ops.object.join()
    joined=bpy.context.object
    joined.name=parent.name+"Geometry"
    # The original object matrix/parent relationship is retained by joining;
    # geometry lives in that child's transform under the dedicated motion root.

bpy.ops.object.select_all(action="DESELECT")
for ob in root.children_recursive:ob.select_set(True)
root.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(ASSET),export_format="GLB",use_selection=True,export_yup=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
spec={
    "schema_version":1,"id":"surya-carbine-original-v1","task_id":"YUGA-TACTICAL-CASUAL-13",
    "source_commit":source_commit,
    "task_baseline_commit":"7162b5d0b666e4422b0bc73100e1fba947d3323f",
    "authoring":"Original scripted Blender geometry guided by original generated art; not automatic image-to-mesh reconstruction.",
    "axis":"Godot Y-up; forward negative Z; metres; no arms/skin/collision/authority.",
    "animation_contract":{"fixed":"SURYA/Fixed","magazine":"SURYA/Magazine","magazine_pivot":[0,-.1,-.14],"muzzle":"SURYA/Muzzle","muzzle_position":[0,.012,-.65]},
    "bounds_godot":bounds,"triangles":triangles,"editable_components":len(original_meshes),"runtime_meshes":2,
    "materials":[m.name for m in bpy.data.materials if m.users],
    "features":["Open curved stock","Exposed faceted amber chamber and hex lattice","Beveled layered receiver","Six short brass barrel ribs","Hollow muzzle with three petals","Ivory lotus inlays","Formed stitched leather grip","Open curved trigger guard","Separate curved detachable magazine"],
    "asset_sha256":sha(ASSET),"editable_blend_sha256":sha(blend),"generator_sha256":sha(Path(__file__)),
    "reference_sha256":sha(PROJECT/"art/tactical/surya-reference.png"),
    "menu_reference_sha256":sha(PROJECT/"assets/tactical/menu-keyart.png"),
    "blender":bpy.app.version_string,"threads":8,"elapsed_seconds":round(time.monotonic()-started,3),
    "command":"blender4.3 --background --threads 8 --python-exit-code 1 --python tools/studio/build_surya_carbine.py",
    "limits":["No native import or actual pixels reviewed by this author yet.","No hardware performance, finished motion or multiplayer claim.","Untextured PBR materials use actual beveled geometry; reference microscopic wear is not reproduced."]
}
SPEC.write_text(json.dumps(spec,indent=2)+"\n")
(ART/"export-receipt.json").write_text(json.dumps(spec,indent=2)+"\n")
print("SURYA_EXPORT",json.dumps({k:spec[k] for k in ["asset_sha256","triangles","bounds_godot","editable_components","elapsed_seconds"]}))
