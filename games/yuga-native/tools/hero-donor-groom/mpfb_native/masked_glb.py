"""Build isolated nape-only suppression by appending a filtered index accessor.

All existing binary payload bytes stay exact, including skin/rig, materials,
images, UVs, positions, tangents and clips. JSON changes are checked explicitly.
"""
import argparse
import copy
import hashlib
import json
import struct
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(source, proof, output):
    source, proof, output = map(Path, (source, proof, output))
    mask = json.loads(proof.read_text())
    assert sha(source) == mask['source_sha256'] and not output.exists()
    raw = source.read_bytes()
    assert struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw))
    size, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(raw[20:20 + size])
    bin_size, bin_kind = struct.unpack_from('<II', raw, 20 + size)
    assert bin_kind == 0x004e4942
    binary = raw[28 + size:28 + size + bin_size]
    original_doc = copy.deepcopy(doc)
    prim = doc['meshes'][mask['mesh_index']]['primitives'][mask['primitive_index']]
    assert prim['indices'] == mask['indices_accessor']
    accessor = doc['accessors'][prim['indices']]
    view = doc['bufferViews'][accessor['bufferView']]
    assert accessor['componentType'] in (5123, 5125) and accessor['type'] == 'SCALAR'
    code = 'H' if accessor['componentType'] == 5123 else 'I'
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    indices = struct.unpack_from('<' + code * accessor['count'], binary, offset)
    assert len(indices) == mask['source_index_count'] and len(indices) % 3 == 0
    selected = set(mask['selected_accessor_vertex_ids'])
    removed = set(mask['removed_triangle_ids'])
    kept = []
    for triangle in range(len(indices) // 3):
        corners = indices[triangle * 3:triangle * 3 + 3]
        flags = [i in selected for i in corners]
        assert all(flags) or not any(flags), 'mixed/protected triangle refused'
        assert (triangle in removed) == all(flags), 'mask identity disagrees'
        if triangle not in removed:
            kept.extend(corners)
    assert len(kept) == mask['kept_triangle_count'] * 3 and kept
    assert len(doc['buffers']) == 1
    extra = struct.pack('<' + code * len(kept), *kept)
    extra += b'\0' * (-len(extra) % 4)
    new_view = len(doc['bufferViews'])
    new_accessor = len(doc['accessors'])
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(kept) * struct.calcsize(code), 'target': 34963})
    doc['accessors'].append({'bufferView': new_view, 'byteOffset': 0, 'componentType': accessor['componentType'], 'count': len(kept), 'type': 'SCALAR', 'min': [min(kept)], 'max': [max(kept)]})
    prim['indices'] = new_accessor
    doc['buffers'][0]['byteLength'] = len(binary) + len(extra)
    comparison = copy.deepcopy(doc)
    comparison['bufferViews'].pop()
    comparison['accessors'].pop()
    comparison['meshes'][mask['mesh_index']]['primitives'][mask['primitive_index']]['indices'] = mask['indices_accessor']
    comparison['buffers'][0]['byteLength'] = original_doc['buffers'][0]['byteLength']
    assert comparison == original_doc
    encoded = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    payload = binary + extra
    result = struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(payload)) + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + struct.pack('<II', len(payload), 0x004e4942) + payload
    output.write_bytes(result)
    assert result[28 + len(encoded):28 + len(encoded) + len(binary)] == binary
    receipt = {'source_sha256': sha(source), 'mask_receipt_sha256': sha(proof), 'script_sha256': sha(__file__), 'output_sha256': sha(output), 'output_bytes': len(result), 'removed_triangles': len(removed), 'retained_hair_triangles': len(kept) // 3, 'existing_binary_bytes_exact': len(binary), 'json_changes': 'one primitive indices reference, appended index accessor/view, total buffer length only', 'canonical_promoted': False}
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True)
    p.add_argument('--mask', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    print(json.dumps(build(a.source, a.mask, a.output), indent=2))
