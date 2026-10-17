#!/usr/bin/env python3
"""Transfer reviewed bounded form rows onto unchanged, exact-row original LODs.

No simplification, interpolation, skin generation, Blender export or import occurs.
Every original LOD row must identify an original near row using all attributes.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / 'art/hero-rama-lod'))
from glb_lod import GLB

PINS = {
    'near': 'de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5',
    'mid': '40737faf61e660f74dbb97b7a5a507869fdedd1a27cd964bb15e27e445a2d3cd',
    'far': 'd5888a452c2a8b711a7a5d8542652762d73c2608047b0399a2486c9ed650f9aa',
}
ELIGIBLE = {(1, 0): 'Rama warm skin', (2, 11): 'Rama warm skin', (2, 12): 'Natural lips'}
EDITABLE = ('POSITION', 'NORMAL', 'TANGENT')
HELD_RING_SHA256 = '71cc40e8f5eb732382255cbb9ca2eca88f6306429c2c649f8223dbe5b4db0ccd'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def arrays(g, p):
    return {k: g.array(v) for k, v in p['attributes'].items()}


def row_key(values, index):
    return b''.join(values[k][index].tobytes() for k in sorted(values))


def row_mapping(original, candidate, target):
    if set(original) != set(candidate) or set(target) != set(original):
        raise ValueError('Attribute domains differ')
    keys = {}
    for i in range(len(original['POSITION'])):
        key = row_key(original, i)
        if key in keys and any(not np.array_equal(candidate[k][i], candidate[k][keys[key]]) for k in EDITABLE):
            raise ValueError('Ambiguous original row maps to different candidate forms')
        keys[key] = i
    try:
        return np.array([keys[row_key(target, i)] for i in range(len(target['POSITION']))])
    except KeyError as exc:
        raise ValueError('LOD vertex is not an exact original near attribute row') from exc


def patch_array(raw, g, index, values, allowed):
    a = g.doc['accessors'][index]
    if a['componentType'] != 5126 or 'sparse' in a or a['type'] not in ('VEC3', 'VEC4'):
        raise ValueError('Only dense float position/normal/tangent rows may change')
    width = 3 if a['type'] == 'VEC3' else 4
    v = g.doc['bufferViews'][a['bufferView']]
    offset = 28 + struct.unpack_from('<I', raw, 12)[0] + v.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = v.get('byteStride', width * 4)
    view = np.ndarray((a['count'], width), dtype='<f4', buffer=raw, offset=offset, strides=(stride, 4))
    changed = np.flatnonzero(np.any(view != values, axis=1))
    view[changed] = values[changed]
    for i in changed:
        allowed[offset + int(i) * stride:offset + int(i) * stride + width * 4] = True
    return len(changed)


def verify_frame_bounds(g):
    for mi, pi, p in g.primitives():
        for semantic in EDITABLE:
            index = p['attributes'][semantic]
            spec, values = g.doc['accessors'][index], g.array(index)
            for field, actual in [('min', values.min(axis=0)), ('max', values.max(axis=0))]:
                if (semantic == 'POSITION' or field in spec) and not np.array_equal(spec.get(field), actual):
                    raise ValueError(f'{semantic} {field} bound differs from actual rows: {mi}/{pi}')


def verify_metadata_only_repair(before, after):
    """Reconcile old captured bytes with an exact-binary declared-bound repair."""
    if before.binary != after.binary:
        raise ValueError('Metadata repair changed BIN bytes')
    normalized, changes = copy.deepcopy(after.doc), []
    for mi, pi in ELIGIBLE:
        attrs = before.doc['meshes'][mi]['primitives'][pi]['attributes']
        for semantic in EDITABLE:
            index = attrs[semantic]
            for field in ('min', 'max'):
                old = before.doc['accessors'][index]
                new = after.doc['accessors'][index]
                if field in old and field in new and old[field] != new[field]:
                    changes.append({'accessor': index, 'semantic': semantic, 'field': field,
                                    'before': old[field], 'after': new[field]})
                    normalized['accessors'][index][field] = old[field]
    if normalized != before.doc:
        raise ValueError('Metadata repair changed data outside declared eligible frame bounds')
    verify_frame_bounds(after)
    return {'bin_exact': True, 'bin_sha256': hashlib.sha256(before.binary).hexdigest(),
            'bin_bytes': len(before.binary), 'json_exact_except_frame_bounds': True, 'frame_bounds_changes': changes}


def encode(document, binary):
    data = json.dumps(document, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    data += b' ' * (-len(data) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(data) + len(binary))
            + struct.pack('<II', len(data), 0x4e4f534a) + data
            + struct.pack('<II', len(binary), 0x004e4942) + binary)


def load_held_ring(path):
    if sha(path) != HELD_RING_SHA256:
        raise ValueError('Held-ring input differs from exact original 288-vertex source receipt')
    return np.array(json.loads(Path(path).read_text())['positions_gltf_m'], dtype=float)


def verify_held_ring(original, candidate, ring):
    found = np.zeros(len(ring), dtype=bool)
    matched = 0
    for mi, pi in ELIGIBLE:
        p = original.doc['meshes'][mi]['primitives'][pi]
        q = candidate.doc['meshes'][mi]['primitives'][pi]
        before, after = arrays(original, p), arrays(candidate, q)
        for index, position in enumerate(ring):
            rows = np.flatnonzero(np.max(abs(before['POSITION'] - position), axis=1) < 1e-7)
            found[index] |= len(rows) > 0
            matched += len(rows)
            if any(not np.array_equal(before[key][rows], after[key][rows]) for key in EDITABLE):
                raise ValueError('Original held-ring position/normal/tangent changed')
    if not np.all(found) or len(ring) != 288:
        raise ValueError('Complete original 288-vertex held ring is required')
    return {'source_vertices': len(ring), 'exported_rows': matched, 'all_positions_normals_tangents_exact': True}


def verify_near(original, candidate, ring):
    normalized = copy.deepcopy(candidate.doc)
    for mi, pi in ELIGIBLE:
        index = original.doc['meshes'][mi]['primitives'][pi]['attributes']['POSITION']
        for key in ('min', 'max'):
            normalized['accessors'][index][key] = original.doc['accessors'][index][key]
    if original.doc != normalized or len(original.binary) != len(candidate.binary):
        raise ValueError('Bounded form stage must preserve GLB JSON except eligible POSITION bounds and binary length')
    verify_frame_bounds(candidate)
    verify_held_ring(original, candidate, ring)
    rebuilt = bytearray(original.raw)
    allowed = np.zeros(len(rebuilt), dtype=bool)
    changes = []
    for mi, pi, p in original.primitives():
        old = arrays(original, p)
        new = arrays(candidate, candidate.doc['meshes'][mi]['primitives'][pi])
        if (mi, pi) not in ELIGIBLE:
            continue
        if original.doc['materials'][p['material']]['name'] != ELIGIBLE[mi, pi]:
            raise ValueError('Unexpected eligible material')
        distance = np.linalg.norm(new['POSITION'].astype(float) - old['POSITION'], axis=1)
        if not np.all(np.isfinite(distance)) or distance.max() > .002:
            raise ValueError('Candidate exceeds finite 2 mm form budget')
        moved = distance > 0
        for key in EDITABLE:
            if not np.all(np.isfinite(new[key])):
                raise ValueError('Nonfinite candidate frame')
            if np.any(new[key][~moved] != old[key][~moved]):
                raise ValueError('Frame changed outside actual displaced vertices')
            patch_array(rebuilt, original, p['attributes'][key], new[key], allowed)
        if np.any(new['TANGENT'][:, 3] != old['TANGENT'][:, 3]):
            raise ValueError('Tangent handedness changed')
        changes.append({'mesh': mi, 'primitive': pi, 'vertices': int(moved.sum()), 'maximum_displacement_m': float(distance.max())})
    binary_start = 28 + struct.unpack_from('<I', rebuilt, 12)[0]
    if bytes(rebuilt[binary_start:]) != candidate.binary:
        raise ValueError('Candidate changed bytes outside declared form positions/frames')
    if not any(c['vertices'] for c in changes):
        raise ValueError('Candidate contains no form edits')
    return changes


def transfer(original, candidate, lod):
    raw = bytearray(lod.raw)
    allowed = np.zeros(len(raw), dtype=bool)
    records = []
    document, bounds = copy.deepcopy(lod.doc), []
    for (mi, pi), material in ELIGIBLE.items():
        p = original.doc['meshes'][mi]['primitives'][pi]
        q = candidate.doc['meshes'][mi]['primitives'][pi]
        t = lod.doc['meshes'][mi]['primitives'][pi]
        if lod.doc['materials'][t['material']]['name'] != material:
            raise ValueError('Unexpected LOD material')
        before, after, target = arrays(original, p), arrays(candidate, q), arrays(lod, t)
        mapping = row_mapping(before, after, target)
        if len(p.get('targets', [])) != len(t.get('targets', [])):
            raise ValueError('LOD morph count differs')
        for near_morph, lod_morph in zip(p.get('targets', []), t.get('targets', [])):
            if set(near_morph) != set(lod_morph) or any(not np.array_equal(original.array(near_morph[k])[mapping], lod.array(lod_morph[k])) for k in near_morph):
                raise ValueError('LOD morph does not match mapped near row')
        changed = {}
        for key in EDITABLE:
            changed[key] = patch_array(raw, lod, t['attributes'][key], after[key][mapping], allowed)
        for semantic in EDITABLE:
            index = t['attributes'][semantic]
            for key, value in [('min', after[semantic][mapping].min(axis=0).tolist()), ('max', after[semantic][mapping].max(axis=0).tolist())]:
                if key not in document['accessors'][index]:
                    continue
                before_bound = document['accessors'][index][key]
                if before_bound != value:
                    bounds.append({'accessor': index, 'semantic': semantic, 'field': key, 'before': before_bound, 'after': value})
                    document['accessors'][index][key] = value
        records.append({'mesh': mi, 'primitive': pi, 'mapped_vertices': len(mapping), 'changed_rows': changed})
    different = np.frombuffer(lod.raw, dtype=np.uint8) != np.frombuffer(raw, dtype=np.uint8)
    if not np.all(allowed[different]):
        raise ValueError('LOD transfer changed bytes outside bounded form rows')
    binary_start = 28 + struct.unpack_from('<I', raw, 12)[0]
    complete = encode(document, bytes(raw[binary_start:]))
    return complete, {'primitives': records, 'changed_binary_bytes': int(different.sum()),
                      'all_other_binary_bytes_exact': True, 'json_exact_except_frame_bounds': True,
                      'frame_bounds_changes': bounds}


def build(project, candidate_path, held_ring, output):
    project = project.resolve(strict=True)
    output = output.resolve()
    if output.exists() or output.is_relative_to(PROJECT.parents[1]) or output.is_relative_to(project):
        raise ValueError('Fresh external output directory required')
    near_path = project / 'assets/heroes/rama-hero.glb'
    if sha(near_path) != PINS['near']:
        raise ValueError('Original near asset differs from frozen input')
    original, candidate = GLB(near_path), GLB(candidate_path)
    ring = load_held_ring(held_ring)
    changes = verify_near(original, candidate, ring)
    pending = {}
    for level in ('mid', 'far'):
        path = project / f'assets/heroes/rama-hero-{level}.glb'
        if sha(path) != PINS[level]:
            raise ValueError(f'Original {level} differs from frozen input')
        raw, report = transfer(original, candidate, GLB(path))
        pending[level] = (raw, report)
    output.mkdir(parents=True)
    overlay = output / 'overlay/assets/heroes'
    overlay.mkdir(parents=True)
    (overlay / 'rama-hero.glb').write_bytes(candidate.raw)
    levels = {}
    for level, (raw, report) in pending.items():
        path = overlay / f'rama-hero-{level}.glb'
        path.write_bytes(raw)
        verify_frame_bounds(GLB(path))
        levels[level] = {'input_sha256': PINS[level], 'output_sha256': sha(path), 'bytes': len(raw), **report}
    result = {'schema': 1, 'task': 'R2-14', 'stage': 'principal-facial-form-lod-transfer-v1',
              'generator_sha256': sha(__file__), 'near_input_sha256': PINS['near'],
              'near_candidate_sha256': sha(candidate_path), 'near_changes': changes, 'levels': levels,
              'original_held_ring_sha256': sha(held_ring), 'held_ring_check': verify_held_ring(original, candidate, ring),
              'scope': 'Exact near-row form transfer onto existing LOD topology. Every non-form binary byte, including rig, UV, weights, morphs, animations, images and unrelated geometry, remains unchanged from each original LOD; JSON differs only in already-declared bounds of edited POSITION/NORMAL/TANGENT attributes. Numerical identity is not art or continuous-deformation acceptance.'}
    (output / 'lod-transfer-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, default=PROJECT)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--held-ring', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.project, a.candidate, a.held_ring, a.output), indent=2))
