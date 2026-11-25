"""Inspect the unpromoted Rock 07 GLB in headless Blender."""
import argparse
import json
import sys
from pathlib import Path

import bmesh
import bpy

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--input', type=Path, default=HERE / 'art/rock07-compact.glb')
parser.add_argument('--output', type=Path, default=Path('/tmp/yuga-rock07-geometry.json'))
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(args.input.resolve()))
objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
bpy.context.view_layer.update()
if len(objects) != 1:
    raise ValueError(f'Expected one mesh object, got {len(objects)}')
obj = objects[0]
mesh = bmesh.new()
mesh.from_mesh(obj.data)
bmesh.ops.remove_doubles(mesh, verts=mesh.verts[:], dist=1e-7)
mesh.normal_update()
coords = [obj.matrix_world @ vertex.co for vertex in mesh.verts]
result = {
    'mesh_objects': len(objects),
    'vertices_welded': len(mesh.verts),
    'faces': len(mesh.faces),
    'boundary_edges': sum(edge.is_boundary for edge in mesh.edges),
    'nonmanifold_edges': sum(not edge.is_manifold for edge in mesh.edges),
    'world_bbox_min': [min(v[i] for v in coords) for i in range(3)],
    'world_bbox_max': [max(v[i] for v in coords) for i in range(3)],
    'note': 'Coordinate-welded Blender mesh; open boundaries can include source scan/UV seam behavior. No gameplay visual test.',
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print('GEOMETRY', json.dumps(result))
mesh.free()
