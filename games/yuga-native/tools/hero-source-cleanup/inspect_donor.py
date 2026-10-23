"""Read-only inventory of the pre-C1 project-owned hair substrate."""
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bmesh
import bpy


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    before = sha(args.donor)
    assert before == 'ef018941de8f8b53b3bf4808139601e15ae5c398c7fb23f26a221f1e1a0c6adc'
    bpy.ops.wm.open_mainfile(filepath=str(args.donor.resolve()))
    obj = bpy.data.objects['Unified swept hair sculpture']
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    remaining = set(bm.verts)
    components = []
    while remaining:
        stack = [remaining.pop()]
        component = []
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    stack.append(other)
        components.append(len(component))
    report = {
        'schema_version': 1, 'scope': 'Reusable clean-mesh substrate inventory; no source replacement or artistic acceptance.',
        'source_path': str(args.donor), 'source_sha256': before,
        'script_sha256': sha(__file__), 'blender': bpy.app.version_string,
        'object': obj.name, 'vertices': len(mesh.vertices), 'faces': len(mesh.polygons),
        'components': len(components), 'component_vertices_largest': sorted(components, reverse=True)[:20],
        'boundary_edges': sum(e.is_boundary for e in bm.edges),
        'wire_edges': sum(e.is_wire for e in bm.edges),
        'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
        'finite_geometry': all(math.isfinite(c) for v in mesh.vertices for c in v.co),
        'positions_sha256': hashlib.sha256(b''.join(struct.pack('<3f', *v.co) for v in mesh.vertices)).hexdigest(),
        'bounds_min': [min((obj.matrix_world@v.co)[i] for v in mesh.vertices) for i in range(3)],
        'bounds_max': [max((obj.matrix_world@v.co)[i] for v in mesh.vertices) for i in range(3)],
        'world_matrix': [list(row) for row in obj.matrix_world],
        'uv_layers': [layer.name for layer in mesh.uv_layers],
        'materials': [material.name for material in mesh.materials],
        'images': [{'name': image.name, 'packed': bool(image.packed_file),
                    'packed_sha256': hashlib.sha256(bytes(image.packed_file.data)).hexdigest() if image.packed_file else None}
                   for material in mesh.materials if material.node_tree
                   for node in material.node_tree.nodes if node.type == 'TEX_IMAGE' and node.image
                   for image in [node.image]],
        'skin': {'groups': [group.name for group in obj.vertex_groups],
                 'armature_modifiers': [mod.object.name for mod in obj.modifiers if mod.type == 'ARMATURE']},
        'exclusions': ['Anatomical fitted hair foundation', 'Surface seated natural eyebrow',
                       'Surface seated natural eyebrow.001', 'Fine knot gold tie',
                       'All anatomy, clothing, weapons and other donor objects'],
        'shape_qualified': False, 'runtime_promoted': False,
        'input_unchanged': sha(args.donor) == before,
        'positive_completion': True}
    bm.free()
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('YUGA_CLEANUP_DONOR=' + json.dumps(report, separators=(',', ':')))


if __name__ == '__main__':
    main()
