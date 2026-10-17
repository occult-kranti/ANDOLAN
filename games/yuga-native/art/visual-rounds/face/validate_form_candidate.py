"""Independent exact preservation and sampled morph differential checks."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import numpy as np

ART = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ART / 'hero-rama-lod'))
from glb_lod import GLB, DTYPES, WIDTHS


def validate(source, candidate, report_path):
    before, after = GLB(source), GLB(candidate)
    checks = []

    def check(name, passed, **details):
        checks.append(dict(name=name, passed=bool(passed), **details))

    normalized = copy.deepcopy(after.doc)
    for mi, pi in [(1, 0), (2, 11), (2, 12)]:
        index = before.doc['meshes'][mi]['primitives'][pi]['attributes']['POSITION']
        for key in ('min', 'max'):
            normalized['accessors'][index][key] = before.doc['accessors'][index][key]
    check('All JSON structures exact except eligible POSITION bounds', before.doc == normalized)
    check('Binary length exact', len(before.binary) == len(after.binary))
    allowed = np.zeros(len(before.binary), dtype=bool)
    eligible = {(1, 0), (2, 11), (2, 12)}
    changed = []
    groups = {}
    morph_samples = []
    for mi, pi, primitive in before.primitives():
        attrs = primitive['attributes']
        position_index = attrs['POSITION']
        position_spec = after.doc['accessors'][position_index]
        position_array = after.array(position_index)
        check(f'Exact POSITION bounds {mi}/{pi}', np.array_equal(position_array.min(axis=0), position_spec['min']) and np.array_equal(position_array.max(axis=0), position_spec['max']))
        for key, accessor_index in attrs.items():
            a, b = before.array(accessor_index), after.array(accessor_index)
            equal = np.array_equal(a, b)
            if (mi, pi) in eligible and key in ('POSITION', 'NORMAL', 'TANGENT'):
                rows = np.flatnonzero(np.any(a != b, axis=1))
                spec = before.doc['accessors'][accessor_index]
                view = before.doc['bufferViews'][spec['bufferView']]
                width = WIDTHS[spec['type']] * DTYPES[spec['componentType']].itemsize
                offset = view.get('byteOffset', 0) + spec.get('byteOffset', 0)
                stride = view.get('byteStride', width)
                for index in rows:
                    allowed[offset + int(index) * stride:offset + int(index) * stride + width] = True
                if key == 'POSITION':
                    d = np.linalg.norm(a.astype(float) - b.astype(float), axis=1)
                    check(f'Bounded positions {mi}/{pi}', np.max(d) <= .002 and np.isfinite(b).all(), maximum_m=float(np.max(d)), vertices=int(np.count_nonzero(d)))
                    changed.append(int(np.count_nonzero(d)))
                    for old, new in zip(a, b):
                        groups.setdefault(old.tobytes(), set()).add(new.tobytes())
                if key == 'NORMAL':
                    check(f'Unit local normals {mi}/{pi}', np.isfinite(b).all() and np.max(abs(np.linalg.norm(b, axis=1) - 1)) < 2e-4)
                if key == 'TANGENT':
                    n = after.array(attrs['NORMAL'])
                    check(f'Unit orthogonal signed tangents {mi}/{pi}', np.array_equal(a[:, 3], b[:, 3]) and np.isfinite(b).all() and np.max(abs(np.linalg.norm(b[:, :3], axis=1) - 1)) < 2e-4 and np.max(abs(np.sum(n * b[:, :3], axis=1))) < 3e-4)
            else:
                check(f'Exact attribute {mi}/{pi}/{key}', equal)
        check(f'Exact triangle indices {mi}/{pi}', np.array_equal(before.array(primitive['indices']), after.array(primitive['indices'])))
        for ti, target in enumerate(primitive.get('targets', [])):
            for semantic, index in target.items():
                check(f'Exact morph payload {mi}/{pi}/{ti}/{semantic}', np.array_equal(before.array(index), after.array(index)))
        if primitive.get('targets'):
            old = before.array(attrs['POSITION']).astype(float)
            new = after.array(attrs['POSITION']).astype(float)
            ids = before.array(primitive['indices']).reshape(-1, 3)
            deltas = [before.array(t['POSITION']).astype(float) for t in primitive['targets']]
            for progress in np.linspace(0, 1, 17):
                # Same piecewise full/half basis used by the one runtime owner.
                offset = max(0, 2 * progress - 1) * (deltas[0] + deltas[1]) + (1 - abs(2 * progress - 1)) * (deltas[2] + deltas[3])
                x, y = (old + offset)[ids], (new + offset)[ids]
                nx, ny = np.cross(x[:, 1] - x[:, 0], x[:, 2] - x[:, 0]), np.cross(y[:, 1] - y[:, 0], y[:, 2] - y[:, 0])
                ax, ay = np.linalg.norm(nx, axis=1), np.linalg.norm(ny, axis=1)
                valid = ax > 1e-14
                ratio = ay[valid] / ax[valid]
                cosine = np.sum(nx[valid] * ny[valid], axis=1) / (ax[valid] * ay[valid])
                row = dict(progress=float(progress), minimum_area_ratio=float(np.min(ratio)), maximum_area_ratio=float(np.max(ratio)), minimum_normal_cosine=float(np.min(cosine)), baseline_degenerate=int(np.sum(~valid)), candidate_degenerate=int(np.sum(ay <= 1e-14)))
                morph_samples.append(row)
                check(f'Morph differential geometry {progress:.4f}', np.isfinite(y).all() and np.min(ratio) > .70 and np.max(ratio) < 1.35 and np.min(cosine) > .90 and np.sum(ay <= 1e-14) <= np.sum(~valid), **row)
    check('All pre-existing exact position duplicates remain exact', all(len(values) == 1 for values in groups.values()), unique_original_positions=len(groups))
    difference = np.frombuffer(before.binary, dtype=np.uint8) != np.frombuffer(after.binary, dtype=np.uint8)
    check('Every changed binary byte is a local eligible frame/position record', np.any(difference) and np.all(allowed[difference]), changed_bytes=int(np.sum(difference)))
    check('All embedded image bytes exact', all(before.image(i) == after.image(i) for i in before.doc['images']))
    check('One original 164-joint skin and nine embedded clips exact', len(after.doc['skins']) == 1 and len(after.doc['skins'][0]['joints']) == 164 and len(after.doc['animations']) == 9 and after.doc['skins'] == before.doc['skins'] and after.doc['animations'] == before.doc['animations'])
    result = dict(passed=all(c['passed'] for c in checks), count=len(checks), checks=checks, source_sha256=hashlib.sha256(before.raw).hexdigest(), candidate_sha256=hashlib.sha256(after.raw).hexdigest(), validator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), changed_vertices=sum(changed), morph_samples=morph_samples, scope='Exact source preservation plus 17 rest-to-full-blink differential geometry samples. Not continuous animation, world motion or artistic acceptance.')
    report_path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('passed', 'count', 'changed_vertices', 'candidate_sha256')}))
    for row in checks:
        if not row['passed']:
            print('FAIL', row)
    return result['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    sys.exit(0 if validate(a.input, a.candidate, a.report) else 1)
