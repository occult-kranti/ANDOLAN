"""Six editable closed lofts -> derived coarse hair volume. Never renders/exports.

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

PARENT_SHA = '71763ab25ed84719a8479bcce771732d50db980780b47c7c4b68114bf2bb9c2f'
ORIGIN = Vector((0, 1.765, .045))
SOURCE_PREFIX = 'SOURCE_LOFT_'
HAIR = 'EDITABLE_WholeHair_CoarseClay'

# x,y,z, transverse half-width, radial half-depth. Cross-sections are complete
# rounded rectangles normal to the local path. Each has its own thickness.
DESIGN = [
    dict(name='01_Dominant_forehead_sweep', normal='radial', sections=[
        [-.052,1.790,.124,.020,.006],
        [-.038,1.813,.130,.046,.013],
        [-.016,1.842,.099,.060,.018],
        [.004,1.860,.050,.061,.021],
        [.007,1.860,.003,.049,.020],
        [-.003,1.851,-.031,.036,.018],
        [-.006,1.845,-.051,.019,.010],
    ]),
    dict(name='02_Opposing_temple_sweep', normal='radial', sections=[
        [.069,1.762,.104,.012,.006],
        [.081,1.784,.089,.023,.011],
        [.080,1.809,.054,.030,.014],
        [.067,1.831,.011,.033,.017],
        [.042,1.845,-.025,.030,.017],
        [.011,1.847,-.049,.022,.012],
    ]),
    dict(name='03_Lower_temple_return', normal='radial', sections=[
        [-.071,1.752,.098,.011,.005],
        [-.085,1.773,.074,.023,.010],
        [-.088,1.795,.033,.027,.014],
        [-.073,1.818,-.012,.030,.016],
        [-.044,1.838,-.046,.031,.017],
        [-.009,1.846,-.058,.021,.012],
    ]),
    dict(name='04_Sideways_fold', normal='front', sections=[
        [-.004,1.846,-.038,.026,.023],
        [-.003,1.858,-.040,.025,.023],
        [.003,1.871,-.041,.023,.022],
        [.024,1.881,-.044,.012,.020],
        [.048,1.881,-.046,.010,.018],
        [.062,1.873,-.052,.011,.017],
        [.050,1.858,-.063,.013,.016],
        [.027,1.850,-.064,.015,.015],
        [.004,1.846,-.058,.016,.012],
    ]),
    dict(name='05_Dominant_collected_S_fall', normal='back', sections=[
        [-.007,1.846,-.055,.023,.017],
        [-.026,1.816,-.075,.037,.023],
        [-.031,1.772,-.095,.045,.029],
        [-.009,1.720,-.109,.044,.031],
        [.020,1.670,-.117,.040,.030],
        [.012,1.618,-.121,.034,.027],
        [-.012,1.578,-.111,.023,.021],
        [-.033,1.553,-.089,.008,.009],
        [-.036,1.552,-.079,.0015,.002],
    ]),
    dict(name='06_Returning_S_fall', normal='back', sections=[
        [.012,1.840,-.057,.022,.016],
        [.039,1.808,-.077,.030,.022],
        [.047,1.762,-.096,.032,.025],
        [.028,1.712,-.132,.029,.027],
        [-.004,1.664,-.145,.027,.025],
        [-.016,1.621,-.136,.022,.022],
        [-.003,1.593,-.116,.016,.017],
        [.021,1.587,-.098,.007,.008],
        [.033,1.596,-.087,.0015,.002],
    ]),
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


def seat_inner_point(p, tree):
    """Seat only obstructed inner scalp/upper-fall points; preserve outer forms."""
    p = Vector(p)
    if p.y < 1.700:
        return p
    radial = p - ORIGIN
    distance = radial.length
    radial.normalize()
    hit, _normal, _index, ray_distance = tree.ray_cast(ORIGIN, radial, .5)
    if hit is not None and distance < ray_distance + .006:
        p = ORIGIN + radial * (ray_distance + .006)
    return p


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
            if design['name'] != '04_Sideways_fold':
                p = seat_inner_point(p, tree)
            # Tie aperture is a protected horizontal ring, never moved. Local
            # aperture seating does not determine the fold's path/outer turn.
            if design['name'] == '04_Sideways_fold' and 1.861 < p.y < 1.875:
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
    source_collection = bpy.data.collections.new('EDITABLE_ClosedLoft_Sources')
    bpy.context.scene.collection.children.link(source_collection)
    sources = []
    for design in DESIGN:
        vertices, faces = closed_loft(design, tree)
        obj = create_mesh(SOURCE_PREFIX+design['name'], vertices, faces, source_collection, material)
        obj['role'] = 'Editable closed authoring volume; overlapping sources are intentional'
        obj['design_sections_gltf'] = json.dumps(design)
        sub = obj.modifiers.new('Editable broad planes', 'SUBSURF')
        sub.levels = 1
        sub.render_levels = 1
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
    hair['role'] = 'Derived union from six closed editable lofts; coarse authoring only'
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

    write_json(args.output/'loft-design.json', dict(coordinates='glTF metres +Y up +Z front', parts=DESIGN))
    write_gzip(args.output/'source-lofts.json.gz', dict(parts=[mesh_payload(o) for o in sources]))
    write_gzip(args.output/'evaluated-clay.json.gz', mesh_payload(hair))
    hair_points, context_points = points(bpy.context.scene)
    projections = census(bpy.context.scene, hair_points, context_points)
    write_json(args.output/'projection.json', dict(views=projections, passed=all(fits(b) for row in projections.values() for b in row.values())))
    after = snapshot()
    delta = differences(before, after)
    allowed = ['.objects.'+HAIR, '.meshes.'+old_mesh_name, '.meshes.'+hair.data.name]
    allowed += ['.objects.'+obj.name for obj in sources] + ['.meshes.'+obj.data.name for obj in sources]
    unexpected = [row[0] for row in delta if not any(row[0]==prefix or row[0].startswith(prefix+'.') for prefix in allowed)]
    # Blender material users counts reflect the intentionally added hair parts.
    unexpected = [path for path in unexpected if not path.endswith('.properties.users')]
    assert not unexpected, unexpected
    write_gzip(args.output/'semantic-before.json.gz', before)
    write_gzip(args.output/'semantic-after.json.gz', after)
    write_json(args.output/'construction-receipt.json', dict(
        scope='Closed editable source volumes and derived coarse authoring union; unrendered, inactive',
        parent_sha256=PARENT_SHA, builder_sha256=sha(__file__),
        source_parts=len(sources), derived_vertices=len(hair.data.vertices), derived_faces=len(hair.data.polygons),
        allowed_difference_prefixes=allowed, difference_paths=[row[0] for row in delta],
        protected_reference_changes=unexpected, reference_geometry_preserved=not unexpected,
        voxel_size_m=.0015, no_solidify=True, no_render=True, no_export=True,
        view_fit_passed=all(fits(b) for row in projections.values() for b in row.values()),
        contact_validation='Independent check pending', aesthetic_acceptance='Four actual views pending'))
    assert shutil.disk_usage('/workspace').free >= 500*1024**2, 'Storage reserve before save'
    destination = args.output/'whole-hair-volume-r3.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
    write_json(args.output/'manifest.json', {p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(args.output.iterdir()) if p.is_file()})
    print('VOLUME_SAVED', destination, sha(destination), len(hair.data.vertices), 'NO_RENDER_NO_EXPORT', flush=True)


if __name__ == '__main__':
    main()
