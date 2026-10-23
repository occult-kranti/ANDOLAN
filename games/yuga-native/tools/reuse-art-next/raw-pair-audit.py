#!/usr/bin/env python3
"""Independent standard-library oracle for the adapter's accepted static GLBs.

Reads raw image bufferViews and raw per-corner attribute bytes without NodeIO.
Does not replace the adapter intake guard, a glTF validator, or render review.
"""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('audit input exceeds 64 MiB')
    data = path.read_bytes()
    if len(data) < 28 or struct.unpack_from('<III', data) != (0x46546C67, 2, len(data)):
        raise ValueError('complete GLB v2 required')
    length, kind = struct.unpack_from('<II', data, 12)
    if kind != 0x4E4F534A or length % 4:
        raise ValueError('aligned JSON chunk required')
    document = json.loads(data[20:20 + length])
    binary_length, binary_kind = struct.unpack_from('<II', data, 20 + length)
    binary = data[28 + length:]
    if binary_kind != 0x004E4942 or binary_length != len(binary):
        raise ValueError('one complete BIN chunk required')
    return data, document, binary


def audit(path):
    data, document, binary = read(path)
    widths = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    sizes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

    def view_bytes(index):
        view = document['bufferViews'][index]
        if view['buffer'] != 0:
            raise ValueError('embedded buffer required')
        start, length = view.get('byteOffset', 0), view['byteLength']
        result = binary[start:start + length]
        if len(result) != length:
            raise ValueError('bufferView overflow')
        return view, result

    def elements(index):
        accessor = document['accessors'][index]
        view, payload = view_bytes(accessor['bufferView'])
        size = widths[accessor['componentType']] * sizes[accessor['type']]
        offset, stride = accessor.get('byteOffset', 0), view.get('byteStride', size)
        result = [payload[offset + i * stride:offset + i * stride + size] for i in range(accessor['count'])]
        if any(len(element) != size for element in result):
            raise ValueError('accessor overflow')
        if accessor['componentType'] == 5126 and any(not math.isfinite(v) for element in result for v in struct.unpack('<' + 'f' * sizes[accessor['type']], element)):
            raise ValueError('nonfinite attribute')
        return accessor, result

    images = []
    for image in document.get('images', []):
        _, payload = view_bytes(image['bufferView'])
        images.append({'mime': image['mimeType'], 'bytes': len(payload), 'sha256': sha(payload)})
    images.sort(key=lambda value: json.dumps(value, sort_keys=True))
    geometry, vertices, triangles = [], 0, 0
    for mesh in document.get('meshes', []):
        for primitive in mesh['primitives']:
            attributes = [(semantic, *elements(index)) for semantic, index in sorted(primitive['attributes'].items())]
            count = next(accessor['count'] for semantic, accessor, _ in attributes if semantic == 'POSITION')
            if any(accessor['count'] != count for _, accessor, _ in attributes):
                raise ValueError('mismatched vertex streams')
            vertex_hashes = [sha(b''.join(values[i] for _, _, values in attributes)) for i in range(count)]
            indices = [int.from_bytes(value, 'little') for value in elements(primitive['indices'])[1]] if 'indices' in primitive else list(range(count))
            if len(indices) % 3 or any(index >= count for index in indices):
                raise ValueError('invalid triangles')
            faces = []
            for i in range(0, len(indices), 3):
                values = [vertex_hashes[index] for index in indices[i:i + 3]]
                oriented = min(''.join(values), ''.join(values[1:] + values[:1]), ''.join(values[2:] + values[:2]))
                faces.append(sha(oriented.encode()))
            geometry.append({
                'mesh': mesh.get('name', ''), 'material': primitive.get('material', -1),
                'schema': [[semantic, accessor['type'], accessor['componentType'], accessor.get('normalized', False)] for semantic, accessor, _ in attributes],
                'triangles': len(faces), 'orientedAttributeTriangles': sha(''.join(sorted(faces)).encode()),
            })
            vertices += count
            triangles += len(faces)
    return {'path': str(path.resolve()), 'sha256': sha(data), 'bytes': len(data), 'images': images,
            'vertices': vertices, 'triangles': triangles, 'geometry': geometry}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    before, after = audit(args.source), audit(args.candidate)
    if before['images'] != after['images'] or before['geometry'] != after['geometry']:
        raise ValueError('raw source/candidate images or oriented attribute triangles differ')
    print(json.dumps({'schema': 1, 'scope': 'independent raw byte and triangle oracle; no renderer or GPU measurement',
                      'imagesExact': True, 'orientedAttributeTrianglesExact': True,
                      'source': before, 'candidate': after}, indent=2))


if __name__ == '__main__':
    main()
