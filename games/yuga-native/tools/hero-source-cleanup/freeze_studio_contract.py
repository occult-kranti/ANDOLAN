"""Read the pinned packed studio into a reproducible render contract; no render."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import bpy


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value(data):
    if isinstance(data, (str, int, float, bool)) or data is None:
        return data
    try:
        return [value(item) for item in data]
    except TypeError:
        return str(data)


def nodes(tree):
    if tree is None:
        return []
    return [{'name': node.name, 'type': node.bl_idname,
             'inputs': {socket.name: value(socket.default_value)
                        for socket in node.inputs if hasattr(socket, 'default_value')}}
            for node in tree.nodes]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--studio', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert sha(args.studio) == '9fe7b4115f2680f06a320965afdabcd9c5a2b428372b9166be5ad1be187ec398'
    bpy.ops.wm.open_mainfile(filepath=str(args.studio.resolve()))
    scene = bpy.context.scene
    source = bpy.data.objects['geometry_0']
    position_bytes = b''.join(struct.pack('<3f', *v.co) for v in source.data.vertices)
    polygon_bytes = b''.join(struct.pack('<3I', *p.vertices) for p in source.data.polygons)
    uv_bytes = b''.join(struct.pack('<2f', *v.uv) for v in source.data.uv_layers[0].data)
    lights = []
    for obj in scene.objects:
        if obj.type == 'LIGHT':
            data = obj.data
            lights.append({'name': obj.name, 'type': data.type, 'energy': data.energy,
                           'color': list(data.color), 'shape': getattr(data, 'shape', None),
                           'size': getattr(data, 'size', None),
                           'size_y': getattr(data, 'size_y', None),
                           'world_matrix': [list(row) for row in obj.matrix_world],
                           'nodes': nodes(data.node_tree)})
    report = {
        'schema_version': 1, 'scope': 'Frozen original intake studio; no new rendering or artistic acceptance.',
        'studio_sha256': sha(args.studio), 'script_sha256': sha(__file__),
        'blender': bpy.app.version_string,
        'source_geometry': {
            'name': source.name, 'vertices': len(source.data.vertices),
            'triangles': len(source.data.polygons), 'position_bytes_sha256': hashlib.sha256(position_bytes).hexdigest(),
            'polygon_bytes_sha256': hashlib.sha256(polygon_bytes).hexdigest(),
            'uv_bytes_sha256': hashlib.sha256(uv_bytes).hexdigest(),
            'world_matrix': [list(row) for row in source.matrix_world]},
        'source_space': {'front': '-Y', 'rear': '+Y', 'up': '+Z',
                         'glb_to_blender_position': '(glTF.x,-glTF.z,glTF.y)',
                         'real_world_scale_qualified': False},
        'camera': {'type': scene.camera.data.type,
                   'center': [.00036856532096862793,-.0015292912721633911,-.0005865693092346191],
                   'span': 1.0021296739578247,
                   'front_offset_in_spans': [1.1,-3,.75], 'rear_offset_in_spans': [-1.1,3,.75],
                   'ortho_scale': 1.0021296739578247*1.25,
                   'clip_start': scene.camera.data.clip_start, 'clip_end': scene.camera.data.clip_end},
        'lights': lights, 'world_color': list(scene.world.color), 'world_nodes': nodes(scene.world.node_tree),
        'render': {'engine': 'CYCLES', 'device': 'CPU', 'samples': 32, 'denoising': False,
                   'seed': 0, 'animated_seed': False, 'threads': 2,
                   'resolution': [scene.render.resolution_x, scene.render.resolution_y],
                   'resolution_percentage': scene.render.resolution_percentage,
                   'film_transparent': scene.render.film_transparent,
                   'view_transform': scene.view_settings.view_transform,
                   'look': scene.view_settings.look, 'exposure': scene.view_settings.exposure,
                   'gamma': scene.view_settings.gamma},
        'floor': [{'name': obj.name, 'world_matrix': [list(row) for row in obj.matrix_world],
                   'material_nodes': [nodes(m.node_tree) for m in obj.data.materials]}
                  for obj in scene.objects if obj.type == 'MESH' and obj != source],
        'positive_completion': True}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('YUGA_CLEANUP_STUDIO_CONTRACT=' + json.dumps(report, separators=(',', ':')))


if __name__ == '__main__':
    main()
