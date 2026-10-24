#!/usr/bin/env python3
"""Adapt gate intake's whole-component selection for a small existing water court."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ROOT = PROJECT.parents[1]
SOURCE = PROJECT / 'assets/environment/lanka_courtyard.glb'
SOURCE_SHA = '1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33'
PROTOTYPES = {
    'column': {'source_center': [18, 0, 20], 'region_min': [17.3, -.001, 19.3], 'region_max': [18.7, 3.4, 20.7]},
    'diya': {'source_center': [12.7, 0, 20], 'region_min': [12.1, -.001, 19.4], 'region_max': [13.3, 2.1, 20.6]},
}
INSTANCES = [
    {'id': 'garden-north-column', 'prototype': 'column', 'position': [-62.5, 0, 5.0]},
    {'id': 'garden-south-column', 'prototype': 'column', 'position': [-62.5, 0, -5.0]},
    {'id': 'garden-north-diya', 'prototype': 'diya', 'position': [-59.8, 0, 5.2]},
    {'id': 'garden-south-diya', 'prototype': 'diya', 'position': [-59.8, 0, -5.2]},
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def select():
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError('source drift')
    raw = SOURCE.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    document, binary = json.loads(raw[20:20 + size]), raw[28 + size:]
    def read(index):
        accessor = document['accessors'][index]
        view = document['bufferViews'][accessor['bufferView']]
        fmt = '<' + {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[accessor['componentType']] * {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
        stride = view.get('byteStride', struct.calcsize(fmt))
        offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        return [struct.unpack_from(fmt, binary, offset + i * stride) for i in range(accessor['count'])]
    prototypes = {key: dict(value, selected=[]) for key, value in PROTOTYPES.items()}
    for node in document['nodes']:
        if 'mesh' not in node or not node['name'].startswith(('COL_', 'DECOR_')):
            continue
        if set(node) != {'mesh', 'name'}:
            raise ValueError('source transform contract changed')
        for surface, primitive in enumerate(document['meshes'][node['mesh']]['primitives']):
            positions = read(primitive['attributes']['POSITION'])
            indices = [row[0] for row in read(primitive['indices'])]
            parent, weld = list(range(len(indices) // 3)), {}
            def find(index):
                while parent[index] != index:
                    parent[index] = parent[parent[index]]
                    index = parent[index]
                return index
            for triangle in range(len(parent)):
                for vertex in indices[triangle * 3:triangle * 3 + 3]:
                    key = tuple(round(value, 5) for value in positions[vertex])
                    other = weld.setdefault(key, triangle)
                    a, b = find(triangle), find(other)
                    if a != b:
                        parent[a] = b
            groups = {}
            for triangle in range(len(parent)):
                groups.setdefault(find(triangle), []).append(triangle)
            for prototype in prototypes.values():
                selected, components = [], []
                for triangle_ids in groups.values():
                    points = [positions[index] for triangle in triangle_ids for index in indices[triangle * 3:triangle * 3 + 3]]
                    low = [min(point[axis] for point in points) for axis in range(3)]
                    high = [max(point[axis] for point in points) for axis in range(3)]
                    if all(low[axis] >= prototype['region_min'][axis] and high[axis] <= prototype['region_max'][axis] for axis in range(3)):
                        selected.extend(triangle_ids)
                        components.append({'first_source_triangle': min(triangle_ids), 'triangle_count': len(triangle_ids), 'min': low, 'max': high})
                if selected:
                    prototype['selected'].append({'node': node['name'], 'surface': surface, 'collision': node['name'].startswith('COL_'), 'source_triangle_ids': sorted(selected), 'components': components})
    for prototype in prototypes.values():
        prototype['triangles'] = sum(len(row['source_triangle_ids']) for row in prototype['selected'])
        prototype['collision_triangles'] = sum(len(row['source_triangle_ids']) for row in prototype['selected'] if row['collision'])
        prototype['surfaces'] = len(prototype['selected'])
    metadata = json.loads(SOURCE.with_suffix('.metadata.json').read_text())
    if not metadata['license'].startswith('CC0-1.0'):
        raise ValueError('asset licence changed')
    return {'schema': 1, 'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': SOURCE_SHA,
            'source_metadata_sha256': sha(SOURCE.with_suffix('.metadata.json')), 'license': metadata['license'],
            'coordinate_contract': 'metres Y-up, rigid translation only; whole existing components; original normals/UV/tangents/materials',
            'prototypes': prototypes, 'instances': INSTANCES, 'canonical_enabled': False,
            'existing_context': {'water': 'west-reed-water at[-60,0.012,0]; cosmetic film over unchanged y0 floor',
                'nature': 'existing map reeds and lotus, unchanged; no duplicated nature payload',
                'route': 'cross-mid x[-66,-44], z[-2,2]; retain camp clearance radius4 at[-54,0,0]'},
            'source_geometry_generated': False, 'source_bytes_copied': 0}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() or out.is_relative_to(ROOT):
        raise ValueError('fresh outside-checkout output required')
    out.parent.mkdir(parents=True, exist_ok=True)
    result = select()
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'selection': str(out), 'sha256': sha(out), 'costs': {key: {k: v[k] for k in ['triangles', 'collision_triangles', 'surfaces']} for key, v in result['prototypes'].items()}}))

if __name__ == '__main__':
    main()
