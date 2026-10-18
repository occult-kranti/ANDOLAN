"""C4 coverage-first continuous scalp and swept closed volumes. Never renders/exports.

Run against the pinned framing-r3 parent; all dimensions below are glTF metres.
These are authored control sections, not inherited scalp or ribbon topology.
"""
import argparse
import gzip
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'clay-framing-r3'))
from scene_semantics import snapshot, differences
from projection_contract import census, fits, points

PARENT_SHA = '1d4a2f77b09a721655145c120ec58c72f2752ec72d464c0fd27c1fc1913646b3'
ORIGIN = Vector((0, 1.765, .045))
SOURCE_PREFIX = 'SOURCE_LOFT_'
HAIR = 'EDITABLE_WholeHair_CoarseClay'

# x,y,z, transverse half-width, radial half-depth. Cross-sections are complete
# rounded rectangles normal to the local path. Each has its own thickness.
# Surface sweeps are parameterized on the protected scalp, with thin roots.
# theta from +Y, phi from +Z toward +X; width/depth are metres.
SWEEPS = [
 ('01_Dominant_crest',[(1.21,-.35,.001,.002),(.99,-.43,.017,.006),(.72,-.60,.023,.008),(.43,-.95,.024,.009),(.30,-1.8,.023,.009),(.42,-2.6,.022,.008),(.65,-3.0,.010,.004)]),
 ('02_Upper_counterflow',[(1.20,.28,.001,.002),(.96,.44,.014,.005),(.71,.65,.020,.006),(.49,1.05,.020,.007),(.41,1.90,.018,.007),(.53,2.65,.017,.006),(.68,3.02,.009,.003)]),
 ('03_Left_temple_sweep',[(1.57,-.92,.001,.002),(1.46,-1.20,.014,.0045),(1.26,-1.57,.019,.0055),(1.02,-1.97,.021,.006),(.79,-2.45,.019,.006),(.65,-2.95,.010,.004)]),
 ('04_Right_temple_sweep',[(1.55,.94,.001,.002),(1.43,1.23,.013,.0045),(1.25,1.60,.018,.0055),(1.03,2.04,.020,.006),(.80,2.51,.019,.006),(.65,3.03,.010,.004)]),
 ('05_Left_lower_return',[(1.70,-1.66,.001,.002),(1.65,-1.94,.011,.004),(1.42,-2.25,.016,.005),(1.17,-2.58,.018,.0055),(.90,-2.84,.017,.0055),(.65,-3.05,.010,.004)]),
 ('06_Right_lower_return',[(1.70,1.66,.001,.002),(1.65,1.94,.011,.004),(1.42,2.25,.016,.005),(1.17,2.58,.018,.0055),(.90,2.84,.017,.0055),(.65,3.05,.010,.004)]),
]
DESIGN = [
 dict(name='07_Filled_tucked_fold',normal='front',sections=[
  [-.004,1.844,-.039,.024,.021],[-.003,1.857,-.040,.024,.021],
  [0,1.870,-.040,.022,.020],[.008,1.882,-.045,.023,.019],
  [.020,1.887,-.054,.022,.017],[.030,1.882,-.063,.020,.016],
  [.027,1.870,-.070,.020,.015],[.014,1.856,-.065,.024,.016],
  [0,1.844,-.057,.023,.015]]),
 dict(name='08_Dominant_tapered_S_fall',normal='back',sections=[
  [-.007,1.846,-.056,.021,.016],[-.022,1.819,-.076,.029,.020],
  [-.031,1.782,-.096,.034,.024],[-.023,1.740,-.114,.035,.025],
  [.003,1.698,-.124,.032,.024],[.019,1.659,-.124,.026,.021],
  [.014,1.622,-.119,.019,.017],[0,1.591,-.108,.012,.012],
  [-.018,1.569,-.091,.0065,.007],[-.034,1.558,-.075,.0025,.003],
  [-.043,1.559,-.061,.0004,.0006]]),
 dict(name='09_Subordinate_tapered_S_fall',normal='back',sections=[
  [.012,1.842,-.057,.020,.015],[.032,1.810,-.081,.024,.019],
  [.040,1.771,-.103,.027,.022],[.026,1.732,-.132,.026,.022],
  [0,1.691,-.142,.023,.020],[-.016,1.656,-.138,.018,.017],
  [-.016,1.627,-.128,.012,.013],[-.004,1.606,-.111,.007,.008],
  [.012,1.596,-.094,.003,.004],[.025,1.598,-.079,.0004,.0006]]),
]



def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def to_blender(p):
    return (p[0], -p[2], p[1])


def to_gltf(p):
    return (float(p[0]), float(p[2]), float(-p[1]))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def write_gzip(path, data):
    with gzip.GzipFile(filename=str(path), mode='wb', mtime=0) as stream:
        stream.write(json.dumps(data, separators=(',', ':')).encode())


def head_tree():
    obj = bpy.data.objects['LOCKED_2_11_Rama warm skin']
    vertices = [Vector(to_gltf(v.co)) for v in obj.data.vertices]
    faces = [list(f.vertices) for f in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, faces, all_triangles=True)


def scalp_point(theta, phi, tree, offset=0):
    direction = Vector((math.sin(theta)*math.sin(phi), math.cos(theta), math.sin(theta)*math.cos(phi)))
    hit, normal, index, distance = tree.ray_cast(ORIGIN, direction, .5)
    assert hit is not None, (theta,phi)
    return ORIGIN + direction*(distance+offset)


def scalp_cap(tree):
    # Coverage is thin and anatomy-seated. Hairline stays above brow, around ears.
    angular, levels = 128, 32
    vertices, faces = [], []
    for offset in [.0035,-.0010]:
        base=len(vertices)
        vertices.append(tuple(scalp_point(0,0,tree,offset)))
        for j in range(1,levels+1):
            for k in range(angular):
                phi=2*math.pi*k/angular
                q=abs((phi+math.pi)%(2*math.pi)-math.pi)
                # Explicit front hairline, recessed opening above each ear,
                # and lower nape boundary. Cubic interpolation is continuous.
                knots=[(0,1.24),(.60,1.34),(1.13,1.61),(1.57,1.66),(1.85,1.84),(2.45,2.10),(math.pi,2.15)]
                for (a,u),(b,v) in zip(knots,knots[1:]):
                    if a<=q<=b:
                        t=(q-a)/(b-a);t=t*t*(3-2*t);end=u+(v-u)*t;break
                theta=end*j/levels
                vertices.append(tuple(scalp_point(theta,phi,tree,offset)))
        for k in range(angular):
            faces.append([base,base+1+k,base+1+(k+1)%angular])
        for j in range(levels-1):
            for k in range(angular):
                a=base+1+j*angular+k;b=base+1+j*angular+(k+1)%angular
                faces.append([a,a+angular,b+angular,b])
    side=1+angular*levels
    for k in range(angular):
        a=1+(levels-1)*angular+k;b=1+(levels-1)*angular+(k+1)%angular
        faces.append([a,b,b+side,a+side])
    return vertices,faces


def surface_design(name, rows, tree):
    return dict(name=name,normal='radial',sections=[list(scalp_point(t,p,tree,.0037))+[w,d] for t,p,w,d in rows])


def closed_loft(design, tree):
    sections = design['sections']
    centers = [Vector(row[:3]) for row in sections]
    vertices, faces = [], []
    count = 16
    for i, row in enumerate(sections):
        center = centers[i]
        tangent = centers[min(i + 1, len(centers)-1)] - centers[max(i-1, 0)]
        tangent.normalize()
        preferred = (center - ORIGIN).normalized() if design['normal'] == 'radial' else Vector((0,0,1 if design['normal']=='front' else -1))
        depth_axis = preferred - tangent * preferred.dot(tangent)
        depth_axis.normalize()
        width_axis = tangent.cross(depth_axis).normalized()
        for k in range(count):
            angle = 2 * math.pi * k / count
            # A soft rectangular section gives broad planes without hard corners.
            u = math.copysign(abs(math.cos(angle))**.82, math.cos(angle))
            v = math.copysign(abs(math.sin(angle))**.82, math.sin(angle))
            p = center + width_axis * (row[3]*u) + depth_axis * (row[4]*v)
            # Tie aperture is a protected horizontal ring, never moved. Local
            # aperture seating does not determine the fold's path/outer turn.
            if design['name'] == '07_Filled_tucked_fold' and 1.861 < p.y < 1.875:
                dx, dz = p.x, p.z + .040
                radius = math.hypot(dx, dz)
                if radius > .0275:
                    p.x = dx * .0275 / radius
                    p.z = -.040 + dz * .0275 / radius
            vertices.append(tuple(p))
        if i:
            previous = (i-1)*count
            current = i*count
            for k in range(count):
                nxt = (k+1)%count
                faces.append([previous+k, previous+nxt, current+nxt, current+k])
    # Close both ends explicitly. There is no shell/solidify modifier anywhere.
    faces.append(list(reversed(range(count))))
    faces.append(list(range((len(sections)-1)*count, len(sections)*count)))
    return vertices, faces


def create_mesh(name, vertices, faces, collection, material):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([to_blender(v) for v in vertices], [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(material)
    for face in mesh.polygons:
        face.use_smooth = True
    return obj


def mesh_payload(obj):
    return dict(name=obj.name, vertices=[to_gltf(v.co) for v in obj.data.vertices],
                faces=[list(f.vertices) for f in obj.data.polygons])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert not args.output.exists(), 'Fresh output required'
    assert shutil.disk_usage('/workspace').free >= 500*1024**2, 'Storage reserve'
    assert sha(bpy.data.filepath) == PARENT_SHA
    args.output.mkdir(parents=True)
    before = snapshot()
    tree = head_tree()
    old = bpy.data.objects[HAIR]
    material = old.data.materials[0]
    old_mesh_name = old.data.name
    removed=[]
    for obj in list(bpy.data.objects):
        if obj.name.startswith(SOURCE_PREFIX):
            removed += ['.objects.'+obj.name,'.meshes.'+obj.data.name]
            mesh=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.meshes.remove(mesh)
    source_collection = bpy.data.collections.new('EDITABLE_C4_CoverageAndSweeps')
    bpy.context.scene.collection.children.link(source_collection)
    sources = []
    vertices, faces = scalp_cap(tree)
    cap=create_mesh(SOURCE_PREFIX+'00_Continuous_seated_scalp',vertices,faces,source_collection,material)
    cap['role']='Thin continuous anatomy-seated coverage with front hairline and ear cutouts'
    sources.append(cap)
    designs=[surface_design(name,rows,tree) for name,rows in SWEEPS]+DESIGN
    for design in designs:
        vertices, faces = closed_loft(design, tree)
        obj = create_mesh(SOURCE_PREFIX+design['name'], vertices, faces, source_collection, material)
        obj['role'] = 'Editable closed authoring volume; buried roots are intentional'
        obj['design_sections_gltf'] = json.dumps(design)
        sub = obj.modifiers.new('Editable broad planes', 'SUBSURF')
        sub.levels = 2
        sub.render_levels = 2
        sources.append(obj)

    # Evaluate each source once, preserving its live cage in the master.
    combined_vertices, combined_faces = [], []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in sources:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        offset = len(combined_vertices)
        combined_vertices.extend(to_gltf(v.co) for v in mesh.vertices)
        combined_faces.extend([[offset+i for i in f.vertices] for f in mesh.polygons])
        evaluated.to_mesh_clear()
    old_mesh = old.data
    bpy.data.objects.remove(old, do_unlink=True)
    bpy.data.meshes.remove(old_mesh)
    hair = create_mesh(HAIR, combined_vertices, combined_faces, bpy.context.scene.collection, material)
    hair['role'] = 'Derived continuous coverage union with shallow sweeps, filled fold and tapered falls; coarse authoring only'
    hair['source_objects'] = json.dumps([obj.name for obj in sources])
    hair['not_runtime'] = True
    bpy.ops.object.select_all(action='DESELECT')
    hair.select_set(True)
    bpy.context.view_layer.objects.active = hair
    # A fixed authoring resolution fuses intersecting roots; it is not used to
    # manufacture the silhouette. Broad authored valleys exceed this scale.
    hair.data.remesh_voxel_size = .0015
    hair.data.remesh_voxel_adaptivity = 0
    bpy.ops.object.voxel_remesh()
    for face in hair.data.polygons:
        face.use_smooth = True
    # One light surface fairing removes voxel stair-steps, not major masses.
    smooth = hair.modifiers.new('Coarse voxel surface fairing', 'SMOOTH')
    smooth.factor = .55
    smooth.iterations = 2
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for obj in sources:
        obj.hide_render = True
        obj.hide_set(True)
    bpy.context.view_layer.update()

    write_json(args.output/'loft-design.json', dict(coordinates='glTF metres +Y up +Z front', parts=designs, scalp=dict(thickness_m=.0045,outer_offset_m=.0035,inner_offset_m=-.001,angular=128,levels=32)))
    write_gzip(args.output/'source-lofts.json.gz', dict(parts=[mesh_payload(o) for o in sources]))
    write_gzip(args.output/'evaluated-clay.json.gz', mesh_payload(hair))
    hair_points, context_points = points(bpy.context.scene)
    projections = census(bpy.context.scene, hair_points, context_points)
    write_json(args.output/'projection.json', dict(views=projections, passed=all(fits(b) for row in projections.values() for b in row.values())))
    after = snapshot()
    delta = differences(before, after)
    allowed = removed + ['.objects.'+HAIR, '.meshes.'+old_mesh_name, '.meshes.'+hair.data.name]
    allowed += ['.objects.'+obj.name for obj in sources] + ['.meshes.'+obj.data.name for obj in sources]
    unexpected = [row[0] for row in delta if not any(row[0]==prefix or row[0].startswith(prefix+'.') for prefix in allowed)]
    # Blender material users counts reflect the intentionally added hair parts.
    unexpected = [path for path in unexpected if not path.endswith('.properties.users')]
    assert not unexpected, unexpected
    write_gzip(args.output/'semantic-before.json.gz', before)
    write_gzip(args.output/'semantic-after.json.gz', after)
    write_json(args.output/'construction-receipt.json', dict(
        scope='C4 continuous seated scalp, shallow sweeps, filled fold and tapered falls; unrendered, inactive',
        parent_sha256=PARENT_SHA, builder_sha256=sha(__file__),
        source_parts=len(sources), derived_vertices=len(hair.data.vertices), derived_faces=len(hair.data.polygons),
        allowed_difference_prefixes=allowed, difference_paths=[row[0] for row in delta],
        protected_reference_changes=unexpected, reference_geometry_preserved=not unexpected,
        voxel_size_m=.0015, no_solidify=True, no_render=True, no_export=True,
        view_fit_passed=all(fits(b) for row in projections.values() for b in row.values()),
        contact_validation='Independent check pending', aesthetic_acceptance='Four actual views pending'))
    assert shutil.disk_usage('/workspace').free >= 500*1024**2, 'Storage reserve before save'
    destination = args.output/'whole-hair-volume-r4.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
    write_json(args.output/'manifest.json', {p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(args.output.iterdir()) if p.is_file()})
    print('VOLUME_SAVED', destination, sha(destination), len(hair.data.vertices), 'NO_RENDER_NO_EXPORT', flush=True)


if __name__ == '__main__':
    main()
