"""Prove the existing nine-component mask against ordered original GLB data.

Reuses artist_r1/carry_exact_glb.py's ordered POSITION plus UV contract. The
output is a small index-selection receipt; runtime reproduction needs only
the canonical GLB and this receipt, not Blender or an edited body export.
"""
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'artist_r1'))
from carry_exact_glb import parse, attribute, sha, SOURCE_SHA

MASTER_SHA = '8cd254da5f789c14a59a1f150ee738fcea556c2c1b9accb3e6193fc45f0b3ace'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--master', type=Path, required=True)
    p.add_argument('--fit-receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert sha(a.source) == SOURCE_SHA and sha(a.master) == MASTER_SHA
    fit = json.loads(a.fit_receipt.read_text())
    assert fit['scene']['sha256'] == MASTER_SHA and not a.output.exists()
    raw = a.source.read_bytes()
    doc, binary = parse(raw)
    hair_mats = {i for i, m in enumerate(doc['materials']) if m.get('name') == 'Swept black hair'}
    primitives = [(mi, pi, prim) for mi, mesh in enumerate(doc['meshes']) for pi, prim in enumerate(mesh['primitives']) if prim.get('material') in hair_mats]
    assert len(primitives) == 1
    mi, pi, prim = primitives[0]
    po, ps, count = attribute(doc, binary, prim['attributes']['POSITION'])
    bpy.ops.wm.open_mainfile(filepath=str(a.master))
    mesh = bpy.data.objects['APPROVED BASELINE Rama'].data
    materials = {i for i, m in enumerate(mesh.materials) if m.name == 'Swept black hair'}
    ids = sorted({v for polygon in mesh.polygons if polygon.material_index in materials for v in polygon.vertices})
    assert len(ids) == count
    selected = set(fit['masked_original_nape_vertex_ids'])
    assert len(selected) == 3996 and selected <= set(ids)
    selected_accessor = [i for i, vertex in enumerate(ids) if vertex in selected]
    selected_accessor_set = set(selected_accessor)
    uv_acc = doc['accessors'][prim['attributes']['TEXCOORD_0']]
    uv_view = doc['bufferViews'][uv_acc['bufferView']]
    uv_offset = binary + uv_view.get('byteOffset', 0) + uv_acc.get('byteOffset', 0)
    uv_stride = uv_view.get('byteStride', 8)
    uv_by_vertex = {}
    id_set = set(ids)
    for loop in mesh.loops:
        if loop.vertex_index in id_set:
            uv_by_vertex.setdefault(loop.vertex_index, tuple(mesh.uv_layers.active.data[loop.index].uv))
    position_residual = 0.0
    uv_residual = 0.0
    for index, vertex in enumerate(ids):
        x, y, z = struct.unpack_from('<3f', raw, po + index * ps)
        position_residual = max(position_residual, math.dist((x, -z, y), mesh.vertices[vertex].co))
        u, v = struct.unpack_from('<2f', raw, uv_offset + index * uv_stride)
        uv_residual = max(uv_residual, math.dist((u, 1 - v), uv_by_vertex[vertex]))
    assert position_residual < 16 * 2 ** -23 * 2 and uv_residual < 1e-7
    acc = doc['accessors'][prim['indices']]
    view = doc['bufferViews'][acc['bufferView']]
    assert acc['type'] == 'SCALAR' and acc['componentType'] in (5123, 5125) and acc['count'] % 3 == 0
    code = 'H' if acc['componentType'] == 5123 else 'I'
    width = struct.calcsize(code)
    offset = binary + view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    indices = struct.unpack_from('<' + code * acc['count'], raw, offset)
    removed, kept = [], []
    for triangle in range(len(indices) // 3):
        corners = indices[triangle * 3:triangle * 3 + 3]
        present = [i in selected_accessor_set for i in corners]
        assert all(present) or not any(present), ('mixed/protected triangle', triangle)
        (removed if all(present) else kept).append(triangle)
    assert removed and kept
    report = {
        'schema_version': 1, 'source_sha256': SOURCE_SHA, 'master_sha256': MASTER_SHA,
        'fit_receipt_sha256': sha(a.fit_receipt), 'script_sha256': sha(__file__),
        'mapping_method': 'Every ordered original hair POSITION and UV crosschecked; no nearest-neighbour mapping',
        'max_position_residual_m': position_residual, 'max_uv_residual': uv_residual,
        'mesh_index': mi, 'primitive_index': pi, 'indices_accessor': prim['indices'],
        'source_index_count': len(indices), 'source_hair_vertex_count': count,
        'selected_accessor_vertex_ids': selected_accessor,
        'removed_triangle_ids': removed, 'kept_triangle_count': len(kept),
        'all_selected_faces_hair_only': True, 'mixed_selected_protected_triangles': 0,
        'source_input_unchanged': sha(a.source) == SOURCE_SHA and sha(a.master) == MASTER_SHA,
        'scope': 'Exact existing nine-nape-component suppression for isolated comparison, no production replacement',
    }
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if not k.endswith('_ids')}, indent=2))


if __name__ == '__main__':
    main()
