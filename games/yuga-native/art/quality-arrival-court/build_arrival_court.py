"""Original Lotus Gate kit for the existing YUGA Surya arrival court.

Blender 4.3+, no addons/downloads. Staged art, deliberately not runtime placement.
Author coordinates below are Godot metres (x, up, forward); p() converts to Blender.
Run only after acquiring the shared heavy-export slot:
 blender --background --python games/yuga-native/art/quality-arrival-court/build_arrival_court.py
"""
from __future__ import annotations
import bpy
import math
import json
import hashlib
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parents[1] / 'docs/evidence/rama-quality/environment'
START = time.monotonic()
SEED = 2026101707
RNG = np.random.default_rng(SEED)
GROUPS = defaultdict(list)
MATS = {}
MODULES = {}
TEXTURES = []
LAMPS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def p(x, y, z):
    return (x, -z, y)


def image(name, pixels, data=False):
    n = len(pixels)
    im = bpy.data.images.new(name, width=n, height=n, alpha=False)
    im.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    alpha = np.ones((n, n, 1), dtype=np.float32)
    im.pixels.foreach_set(np.concatenate((pixels, alpha), axis=-1).astype(np.float32).ravel())
    file = HERE / 'textures' / f'{name}.png'
    file.parent.mkdir(exist_ok=True)
    im.filepath_raw = str(file)
    im.file_format = 'PNG'
    im.save()
    im.pack()
    TEXTURES.append({'path': str(file.relative_to(HERE)), 'bytes': file.stat().st_size,
                     'sha256': sha(file), 'size': [n, n], 'colour_space': 'linear_data' if data else 'sRGB'})
    return im


def material(name, colour, roughness, metallic=0, texture=False, emission=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*colour, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*colour, 1)
        bsdf.inputs['Emission Strength'].default_value = emission
    if texture:
        n = 1024
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) / n
        height = np.zeros((n, n), dtype=np.float32)
        for freq, amp in [(2, .15), (7, .08), (19, .04), (67, .018), (173, .006)]:
            phase = RNG.uniform(0, math.tau)
            height += np.cos(math.tau * (freq * xx + (freq + 1) * yy) + phase) * amp
            height += np.sin(math.tau * ((freq + 1) * xx - freq * yy) - phase) * amp * .4
        height += (RNG.random((n, n)).astype(np.float32) - .5) * .018
        if metallic:
            # Sparse cast-metal oxidation, not bright gold noisily covering the frame.
            patina = np.maximum(0, height - .09) * .7
            rgb = np.clip(np.array(colour)[None, None, :] * (1 + height[:, :, None] * .10)
                          + patina[:, :, None] * np.array([-.12, .015, .025]), 0, 1)
            rough = np.clip(roughness + height * .24 + patina, .30, .72)
        else:
            rgb = np.clip(np.array(colour)[None, None, :] * (1 + height[:, :, None] * .09), 0, 1)
            rough = np.clip(roughness + height * .12, .65, .92)
        dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 2.2
        dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 2.2
        norm = np.stack((-dx, -dy, np.ones_like(height)), -1)
        norm /= np.linalg.norm(norm, axis=-1, keepdims=True)
        maps = [(image(name + '-basecolor', rgb), 'Base Color'),
                (image(name + '-roughness', np.repeat(rough[:, :, None], 3, 2), True), 'Roughness')]
        for im, socket in maps:
            node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            node.image = im
            mat.node_tree.links.new(node.outputs['Color'], bsdf.inputs[socket])
        node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image(name + '-normal', norm * .5 + .5, True)
        normal = mat.node_tree.nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = .36 if metallic else .30
        mat.node_tree.links.new(node.outputs['Color'], normal.inputs['Color'])
        mat.node_tree.links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    MATS[name] = mat
    return mat


def register(obj, name, mat, module='LotusGate', smooth=False):
    obj.name = name
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = smooth
    GROUPS[(module, mat.name)].append(obj)
    return obj


def mesh(name, verts, faces, mat, module='LotusGate', smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata([p(*v) for v in verts], [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return register(obj, name, mat, module, smooth)


def bevel(obj, width=.035, segments=3):
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('Authored rounded stone edges', 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def block(name, pos, size, mat, edge=.025, module='LotusGate'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=p(*pos))
    obj = bpy.context.object
    obj.scale = (size[0], size[2], size[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    register(obj, name, mat, module)
    if edge:
        bevel(obj, edge, 3)
    return obj


def lathe(name, x, z, profile, mat, module='LotusGate', sides=48, flutes=0, flute_depth=0):
    verts, faces = [], []
    for radius, y in profile:
        for i in range(sides):
            a = math.tau * i / sides
            r = radius + flute_depth * math.cos(flutes * a) if flutes else radius
            verts.append((x + r * math.cos(a), y, z + r * math.sin(a)))
    for j in range(len(profile) - 1):
        for i in range(sides):
            k = (i + 1) % sides
            faces.append((j*sides+i, j*sides+k, (j+1)*sides+k, (j+1)*sides+i))
    faces.append(tuple(range(sides-1, -1, -1)))
    faces.append(tuple((len(profile)-1)*sides+i for i in range(sides)))
    return mesh(name, verts, faces, mat, module, True)


def tube(name, points, radius, mat, module='LotusGate', sides=8, taper=False):
    verts, faces = [], []
    pts = [Vector(v) for v in points]
    previous = None
    for i, pos in enumerate(pts):
        tangent = (pts[min(i+1, len(pts)-1)] - pts[max(i-1, 0)]).normalized()
        guide = Vector((0, 0, 1)) if abs(tangent.z) < .92 else Vector((1, 0, 0))
        normal = tangent.cross(guide).normalized()
        if previous is not None and normal.dot(previous) < 0:
            normal = -normal
        previous = normal
        binorm = tangent.cross(normal).normalized()
        r = radius * (.50 + .50*math.sin(math.pi*i/(len(pts)-1))) if taper else radius
        for a in range(sides):
            v = pos + r * (math.cos(math.tau*a/sides)*normal + math.sin(math.tau*a/sides)*binorm)
            verts.append(tuple(v))
    for i in range(len(pts)-1):
        for a in range(sides):
            b=(a+1)%sides
            faces.append((i*sides+a, i*sides+b, (i+1)*sides+b, (i+1)*sides+a))
    faces.extend((tuple(range(sides-1, -1, -1)), tuple((len(pts)-1)*sides+a for a in range(sides))))
    return mesh(name, verts, faces, mat, module, True)


def petal(name, centre, length, width, projection, angle, mat, module='LotusGate'):
    # A closed carved petal, full midrib in actual mesh rather than a flat decal.
    steps, cross = 14, 8
    verts, faces = [], []
    cx, cy, cz = centre
    for back in [False, True]:
        for j in range(steps+1):
            t = j/steps
            half = width * max(.012, math.sin(math.pi*t)**.7)
            along = length * t
            for k in range(cross+1):
                s = 2*k/cross-1
                across = half*s
                px = across*math.cos(angle) - along*math.sin(angle)
                py = across*math.sin(angle) + along*math.cos(angle)
                depth = .015 if back else projection * math.sin(math.pi*t)**.65 * (1-s*s)**.6 + .035
                verts.append((cx+px, cy+py, cz-depth))
    layer = (steps+1)*(cross+1)
    for face_layer in [0, 1]:
        off=face_layer*layer
        for j in range(steps):
            for k in range(cross):
                a=off+j*(cross+1)+k
                f=(a,a+1,a+cross+2,a+cross+1)
                faces.append(f[::-1] if face_layer else f)
    # Closed edges permit reliable normal/degenerate validation and GI.
    boundary=[j*(cross+1) for j in range(steps+1)]
    boundary += [steps*(cross+1)+k for k in range(1,cross+1)]
    boundary += [j*(cross+1)+cross for j in range(steps-1,-1,-1)]
    boundary += list(range(cross-1,0,-1))
    for i,a in enumerate(boundary):
        b=boundary[(i+1)%len(boundary)]
        faces.append((a,b,b+layer,a+layer))
    return mesh(name, verts, faces, mat, module, True)


def arch(name, radius, rise, spring, width, depth, front, mat):
    verts, faces = [], []
    n=128
    for i in range(n+1):
        a=math.pi*i/n
        # Inner/outer edges follow intentionally different radii and rise.
        inner=(radius*math.cos(a), spring+rise*math.sin(a))
        outer=((radius+width)*math.cos(a), spring+(rise+width)*math.sin(a))
        verts += [(inner[0],inner[1],front), (outer[0],outer[1],front),
                  (inner[0],inner[1],front+depth), (outer[0],outer[1],front+depth)]
    for i in range(n):
        a=i*4;b=a+4
        faces.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),
                      (a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
    faces.extend([(0,1,3,2),(n*4,n*4+2,n*4+3,n*4+1)])
    return bevel(mesh(name,verts,faces,mat,smooth=False), .025, 2)


def lotus_rosette(x,y,z,r,mat,leaves=8):
    for a in range(leaves):
        petal(f'Lotus relief petal {a}',(x,y,z),r,.19*r,.12*r,math.tau*a/leaves,mat)
    # Bronze centre is quiet and differentiated from gameplay reward gold.
    points=[(x+.10*r*math.cos(a*math.tau/32),y+.10*r*math.sin(a*math.tau/32),z-.13*r) for a in range(33)]
    tube('Lotus relief seed rim',points,.025*r,BRONZE)


def build_gate():
    for side in [-1,1]:
        x=side*10.7
        block('Deep structural pier', (x,4.15,0), (3.05,8.3,3.0), STONE,.08)
        for y,w,d,h in [(.12,3.9,3.8,.24),(.33,3.65,3.55,.18),(.55,3.35,3.25,.26),
                         (7.60,3.35,3.30,.20),(7.85,3.8,3.7,.24),(8.10,4.1,3.90,.24)]:
            block('Pier moulded plinth / cornice', (x,y,0), (w,h,d), STONE,.045)
        # Inset receives separate sculpted relief, not a painted block pattern.
        block('Recessed teal limestone panel',(x,4.2,-1.535),(1.52,4.1,.10),INLAY,.035)
        for xx in [-.88,.88]:
            lathe('Front fluted shaft',x+xx,-1.59,[(.24,.70),(.28,.79),(.22,.88),(.20,1.1),(.18,6.7),(.22,6.9),(.30,7.0)],STONE,
                  sides=48,flutes=12,flute_depth=.018)
            for y in [.92,1.10,6.72,6.91]:
                lathe('Collar / neck ring',x+xx,-1.59,[(.23,y-.035),(.25,y),(.23,y+.035)],BRONZE,sides=32)
        lotus_rosette(x,4.25,-1.62,.68,STONE)
        # Tapered lotus corbels carry the broad arch at human-visible scale.
        for dx in [-.8,-.4,0,.4,.8]:
            petal('Capital carved lotus bracket',(x+dx,6.90,-1.56),.75,.17,.19,0,STONE)
        for dx in [-1.03,1.03]:
            block('Reveal shadow gap',(x+dx,4.20,-1.57),(.055,5.3,.05),DARK,.008)
        # Proper curved chhatri-style roof mass as an invented coastal silhouette.
        lathe('Lotus bell roof',x,0,[(1.95,8.21),(1.98,8.27),(1.82,8.38),(1.66,8.51),(1.34,8.73),(.96,8.97),(.60,9.20),(.26,9.43),(.16,9.63),(.04,9.88)],STONE,sides=64)
        lathe('Bell roof brass rim',x,0,[(1.98,8.25),(2.02,8.28),(1.98,8.32)],BRONZE,sides=64)
        for a in range(16):
            t=a*math.tau/16
            points=[]
            for r,yy in [(1.88,8.34),(1.57,8.59),(1.18,8.84),(.76,9.10),(.33,9.39)]:
                points.append((x+r*math.cos(t),yy,r*math.sin(t)))
            tube('Roof carved rib',points,.023,STONE,sides=6)
        lathe('Roof copper finial',x,0,[(.15,9.45),(.25,9.55),(.19,9.72),(.08,9.96),(.02,10.12)],BRONZE,sides=32)
    arch('Open load-bearing lotus arch',9.05,5.45,4.80,.92,2.8,-1.4,STONE)
    arch('Arch recessed dark soffit',9.04,5.44,4.80,.15,2.45,-1.23,DARK)
    arch('Arch front indigo reveal',9.16,5.54,4.80,.12,.06,-1.48,INLAY)
    arch('Arch sparse bronze outer reveal',9.78,6.18,4.80,.045,.05,-1.47,BRONZE)
    # Radial carved voussoirs make construction and scale legible.
    for i in range(1,31):
        a=math.pi*i/31
        pts=[]
        for j in range(7):
            t=j/6
            rr=9.31+.32*t
            rise=5.68+.32*t
            pts.append((rr*math.cos(a),4.80+rise*math.sin(a),-1.51-.025*math.sin(math.pi*t)))
        tube('Arch carved voussoir groove',pts,.016,DARK,sides=6)
    # A central keystone bud, with carved stone petals instead of a gold spike.
    block('Central keystone',(0,10.53,-.05),(1.0,1.1,3.15),STONE,.10)
    for dx in [-.42,0,.42]:
        petal('Keystone lotus crown',(dx,10.55,-1.66),.70,.22,.18,dx*.7,STONE)
    # Shallow symmetrical returns finish the pier without suggesting false doors.
    for side in [-1,1]:
        x=side*13.1
        block('Solid low return',(x,.57,.25),(1.6,1.14,2.55),STONE,.06)
        block('Return sloped coping',(x,1.20,.25),(1.82,.20,2.73),STONE,.045)


def build_lamps():
    for side in [-1,1]:
        module='DiyaLeft' if side<0 else 'DiyaRight'
        x,z=side*7.45,-3.60
        # Turned stepped foot, fluted column and a modeled shallow oil basin.
        lathe('Lamp cast foot',x,z,[(.57,0),(.61,.07),(.60,.13),(.48,.20),(.41,.25),(.33,.38),(.21,.48),(.16,.61),(.13,1.10),(.21,1.17)],BRONZE,module,sides=48,flutes=8,flute_depth=.012)
        profile=[(.20,1.12),(.43,1.19),(.66,1.30),(.70,1.36),(.68,1.40),(.62,1.40),(.57,1.34),(.36,1.25),(.20,1.23)]
        lathe('Lamp oil bowl inner and outer wall',x,z,profile,BRONZE,module,sides=64)
        for a in range(12):
            t=math.tau*a/12
            points=[]
            for j in range(10):
                f=j/9
                rr=.26+.38*f
                points.append((x+rr*math.cos(t),1.23+.16*f+.045*math.sin(math.pi*f),z+rr*math.sin(t)))
            tube('Basin lotus rib',points,.012,BRONZE,module,sides=6)
        lathe('Lamp dark oil plane',x,z,[(.01,1.279),(.40,1.279),(.41,1.282),(.01,1.282)],DARK,module,sides=40)
        for a in [0,math.pi*.67,math.pi*1.33]:
            xx,zz=x+.36*math.cos(a),z+.36*math.sin(a)
            tube('Cotton wick',[(xx,1.30,zz),(xx+.025,1.34,zz)],DARK,module,sides=6)
            lathe('Quiet oil flame',xx,zz,[(.015,1.335),(.045,1.38),(.041,1.43),(.025,1.48),(.002,1.56)],FLAME,module,sides=16)
            LAMPS.append({'module':module,'position':[round(xx,5),1.43,round(zz,5)],'light_proposal':'emissive only; no new dynamic lights in asset'})


def build_threshold():
    # Flush inlay: the clear passage gets no decorative step or false collision.
    module='Threshold'
    for side in [-1,1]:
        # Lines converge gently into the existing central route; they are matte.
        pts=[(side*(6.2+.025*j),.009,-18+j*.24) for j in range(65)]
        tube('Honed lead-in inlay',pts,.025,INLAY,module,sides=6)
    for z in [-2.65,-2.40]:
        block('Flush threshold strip',(0,.005,z),(16.8,.008,.075),INLAY,0,module)
    # One restrained petal fan at the threshold, far from the spawn reticle.
    for a in range(-3,4):
        t=a*.16
        pts=[(1.15*math.sin(t)*f,.009,-2.2+1.15*math.cos(t)*f) for f in np.linspace(0,1,16)]
        tube('Threshold lotus line',pts,.012,INLAY,module,sides=6)


def join_and_uv():
    records=[]
    for (module,matname),objects in sorted(GROUPS.items()):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects: obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.join()
        obj=bpy.context.object
        obj.name=f'{module}__{matname}'
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        # Recalculate outward normals on closed components before tangent export.
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.uv.smart_project(angle_limit=math.radians(64),island_margin=.008)
        bpy.ops.object.mode_set(mode='OBJECT')
        if module not in MODULES:
            root=bpy.data.objects.new(module,None)
            bpy.context.collection.objects.link(root)
            MODULES[module]=root
        obj.parent=MODULES[module]
        obj.data.calc_loop_triangles()
        records.append({'name':obj.name,'module':module,'material':matname,
                        'vertices':len(obj.data.vertices),'triangles':len(obj.data.loop_triangles)})
    return records


def export():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type in ['MESH','EMPTY']: obj.select_set(True)
    file=HERE/'lotus-arrival-court.glb'
    bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=True,
        export_yup=True,export_normals=True,export_tangents=True,export_texcoords=True,
        export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False,
        export_extras=True)
    return file


def main():
    global STONE,BRONZE,INLAY,DARK,FLAME
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=1
    STONE=material('Honed warm limestone',(.43,.387,.315),.81,texture=True)
    BRONZE=material('Cast aged bronze',(.32,.19,.073),.49,.84,texture=True)
    INLAY=material('Quiet teal ceramic',(.032,.11,.12),.56)
    DARK=material('Recess and oil',(.025,.034,.032),.90)
    FLAME=material('Warm oil flame',(.85,.19,.025),.55,emission=2.4)
    build_gate()
    build_lamps()
    build_threshold()
    meshes=join_and_uv()
    triangles=sum(m['triangles'] for m in meshes)
    assert triangles<=110000,triangles
    bpy.context.scene.render.engine='CYCLES'
    bpy.context.scene.world.color=(.08,.08,.08)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'lotus-arrival-court.blend'))
    glb=export()
    bounds=[]
    for obj in bpy.context.scene.objects:
        if obj.type=='MESH':
            bounds += [obj.matrix_world@Vector(c) for c in obj.bound_box]
    aabb=[[min(v[i] for v in bounds) for i in range(3)],[max(v[i] for v in bounds) for i in range(3)]]
    # AABB in the authoring scene is converted back to Godot axes.
    godot_aabb=[[aabb[0][0],aabb[0][2],-aabb[1][1]],[aabb[1][0],aabb[1][2],-aabb[0][1]]]
    report={'schema_version':1,'id':'surya-arrival-lotus-gate-r1','status':'staged; requires independent actual native same-camera A/B',
      'generator':str(Path(__file__).relative_to(HERE.parents[3])),'generator_sha256':sha(__file__),
      'seed':SEED,'blender_version':bpy.app.version_string,'elapsed_seconds':round(time.monotonic()-START,3),
      'glb':{'path':glb.name,'bytes':glb.stat().st_size,'sha256':sha(glb)},
      'editable':{'path':'lotus-arrival-court.blend','sha256':sha(HERE/'lotus-arrival-court.blend')},
      'triangles':triangles,'vertices':sum(m['vertices'] for m in meshes),'materials':len(MATS),
      'meshes':meshes,'textures':TEXTURES,'godot_aabb':godot_aabb,'emission_centres':LAMPS,
      'proposed_origin_godot':[0,0,-90],
      'collision_proposal':{'status':'not integrated; root must compare authority and all three lane envelopes',
        'boxes':[{'name':'left_pier','position':[-10.7,4.15,0],'size':[3.05,8.3,3.0]},
                 {'name':'right_pier','position':[10.7,4.15,0],'size':[3.05,8.3,3.0]}],
        'clear_aperture':{'half_width_metres':9.05,'spring_height_metres':4.8,'apex_height_metres':10.25},
        'notes':['No collision/light nodes exported','Flush threshold is decoration; do not create a step','Arch overhead needs an appropriate convex or segmented collider before accessible promotion','Diya bowls require review against route envelopes or move as a module']},
      'provenance':{'geometry':'original analytic/artist procedural modeling; no external mesh/image/audio used',
        'textures':'six original seeded analytic maps; no downloaded texture/photo',
        'inspiration':['R1 Griffith Ramayana selected Lanka gate/court passages in retained SOURCE_LIBRARY.md','A1 Fergusson broad mass descriptions, dated secondary source; no reconstructed historical plan'],
        'license':'CC0-1.0 for new generated geometry and texture assets; generator repository license'},
      'limits':['Staged source is not a shipped map improvement','No consumer GPU performance claim','No physical oil/fire simulation','No human art-direction acceptance yet','No final Deadlock-quality claim']}
    (HERE/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE/'build-r1.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'triangles':triangles,'vertices':report['vertices'],'meshes':len(meshes),'glb_sha256':sha(glb),'elapsed_seconds':report['elapsed_seconds']}),flush=True)


if __name__=='__main__':main()
