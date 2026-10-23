#!/usr/bin/env python3
"""Independently compare an actual static GLB pair without a glTF library.

This intentionally narrow review helper assumes the audited single embedded
BIN layout. It verifies attributes, winding and images, then resolves only the
specific standard PBR/sampler defaults observed in this campaign.
"""
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def capture(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<III', raw) == (0x46546C67, 2, len(raw))
    size, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(raw[20:20 + size])
    binary_size, binary_kind = struct.unpack_from('<II', raw, 20 + size)
    assert binary_kind == 0x004E4942 and 28 + size + binary_size == len(raw)
    binary = raw[28 + size:]

    def values(index):
        accessor = doc['accessors'][index]
        assert not accessor.get('sparse')
        view = doc['bufferViews'][accessor['bufferView']]
        width = {5121: 1, 5123: 2, 5125: 4, 5126: 4}[accessor['componentType']]
        width *= {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
        offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        stride = view.get('byteStride', width)
        assert offset + (accessor['count'] - 1) * stride + width <= view.get('byteOffset', 0) + view['byteLength']
        return [binary[offset + i * stride:offset + i * stride + width] for i in range(accessor['count'])]

    shapes = []
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            keys = sorted(primitive['attributes'])
            attributes = [values(primitive['attributes'][key]) for key in keys]
            schema = []
            for key in keys:
                accessor = doc['accessors'][primitive['attributes'][key]]
                schema.append([key, accessor['componentType'], accessor['type'], accessor.get('normalized', False)])
            assert all(len(attribute) == len(attributes[0]) for attribute in attributes)
            full_vertices = [b''.join(vertex) for vertex in zip(*attributes)]
            accessor = doc['accessors'][primitive['indices']]
            fmt = '<' + {5121: 'B', 5123: 'H', 5125: 'I'}[accessor['componentType']]
            indices = [struct.unpack(fmt, value)[0] for value in values(primitive['indices'])]
            assert len(indices) % 3 == 0 and all(0 <= index < len(full_vertices) for index in indices)
            faces = []
            for offset in range(0, len(indices), 3):
                a, b, c = [full_vertices[index] for index in indices[offset:offset + 3]]
                faces.append(min(a + b + c, b + c + a, c + a + b))
            shapes.append({'schema': schema, 'triangles': len(faces), 'oriented_full_attribute_triangle_sha256': sha(b''.join(sorted(faces)))})
    images = []
    for image in doc.get('images', []):
        assert 'uri' not in image
        view = doc['bufferViews'][image['bufferView']]
        offset = view.get('byteOffset', 0)
        data = binary[offset:offset + view['byteLength']]
        images.append([image['mimeType'], len(data), sha(data)])
    return raw, doc, shapes, sorted(images)


def resolved_defaults(doc):
    materials = copy.deepcopy(doc.get('materials', []))
    for material in materials:
        material.setdefault('alphaMode', 'OPAQUE')
        material.setdefault('doubleSided', False)
        pbr = material.setdefault('pbrMetallicRoughness', {})
        for key, value in [('baseColorFactor', [1, 1, 1, 1]), ('roughnessFactor', 1), ('metallicFactor', 1)]:
            pbr.setdefault(key, value)
    textures = copy.deepcopy(doc.get('textures', []))
    for texture in textures:
        sampler = copy.deepcopy(doc.get('samplers', [])[texture.pop('sampler')]) if 'sampler' in texture else {}
        sampler.setdefault('wrapS', 10497)
        sampler.setdefault('wrapT', 10497)
        texture['resolved_sampler'] = sampler
    return {'materials': materials, 'textures_with_resolved_sampler': textures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    a, ja, ga, ia = capture(args.source)
    b, jb, gb, ib = capture(args.candidate)
    stable = {key: ja.get(key) == jb.get(key) for key in ['scenes', 'nodes', 'materials', 'textures', 'samplers', 'extensionsUsed', 'extensionsRequired']}
    checks = {
        'oriented_full_attributes_exact': ga == gb,
        'embedded_image_bytes_exact': ia == ib,
        'scenes_nodes_extension_lists_raw_exact': all(stable[key] for key in ['scenes', 'nodes', 'extensionsUsed', 'extensionsRequired']),
        'resolved_standard_material_sampler_defaults_equal': resolved_defaults(ja) == resolved_defaults(jb),
    }
    report = {'scope': 'Independent raw actual-pair identity only. No visual, performance or asset-rights acceptance.', 'source': str(args.source), 'candidate': str(args.candidate), 'source_sha256': sha(a), 'candidate_sha256': sha(b), 'checks': checks, 'raw_field_equality': stable, 'passed': all(checks.values()), 'geometry': ga, 'images': ia}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'checks': checks}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
