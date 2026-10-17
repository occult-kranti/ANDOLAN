#!/usr/bin/env python3
"""Counterexamples for bounded form admission and exact LOD row mapping."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import numpy as np
import transfer_form_lods as transfer


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--held-ring', type=Path, required=True)
    a = p.parse_args()
    original = transfer.GLB(transfer.PROJECT / 'assets/heroes/rama-hero.glb')
    candidate = transfer.GLB(a.candidate)
    ring = transfer.load_held_ring(a.held_ring)
    checks = []
    def check(name, call, valid=False):
        error = None
        try: call()
        except ValueError as exc: error = str(exc)
        checks.append({'name': name, 'passed': (error is None) == valid, 'rejection': error})
    def yes(condition):
        if not condition: raise ValueError('Expected equality is false')
    with tempfile.TemporaryDirectory(prefix='rama-form-transfer-cases-') as folder:
        folder = Path(folder)
        def validate_altered(mutator):
            return transfer.verify_near(original, altered(mutator), ring)
        def altered(mutator):
            doc, binary = copy.deepcopy(candidate.doc), bytearray(candidate.binary)
            mutator(doc, binary)
            file = folder / 'altered.glb'
            file.write_bytes(transfer.encode(doc, bytes(binary)))
            return transfer.GLB(file)
        def array(doc, binary, index):
            spec = doc['accessors'][index]
            view = doc['bufferViews'][spec['bufferView']]
            width = {'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[spec['type']]
            return np.ndarray((spec['count'], width), dtype='<f4', buffer=binary,
                              offset=view.get('byteOffset', 0) + spec.get('byteOffset', 0),
                              strides=(view.get('byteStride', width * 4), 4))
        face = original.doc['meshes'][1]['primitives'][0]['attributes']
        skin = original.doc['meshes'][2]['primitives'][11]['attributes']
        check('real bounded form accepted', lambda: transfer.verify_near(original, candidate, ring), True)
        check('unchanged no-op refused', lambda: transfer.verify_near(original, original, ring))
        check('stale lip accessor bound refused', lambda: validate_altered(
            lambda d, b: d['accessors'][d['meshes'][2]['primitives'][12]['attributes']['POSITION']]['max'].__setitem__(2, .16893260180950165)))
        check('changed bone identity refused', lambda: validate_altered(lambda d, b: d['nodes'][0].update(name='different')))
        check('UV edit refused', lambda: validate_altered(lambda d, b: array(d, b, face['TEXCOORD_0']).__setitem__((0, 0), .9)))
        check('weight edit refused', lambda: validate_altered(lambda d, b: array(d, b, skin['WEIGHTS_0']).__setitem__((0, 0), .9)))
        check('nonfinite frame refused', lambda: validate_altered(lambda d, b: array(d, b, face['NORMAL']).__setitem__((0, 0), np.nan)))
        check('tangent handedness edit refused', lambda: validate_altered(lambda d, b: array(d, b, face['TANGENT']).__setitem__((0, 3), -array(d, b, face['TANGENT'])[0, 3])))
        def displacement(d, b):
            arr = array(d, b, face['POSITION'])
            arr[0, 2] += .01
            d['accessors'][face['POSITION']].update(min=arr.min(axis=0).tolist(), max=arr.max(axis=0).tolist())
        check('greater than 2mm displacement refused', lambda: validate_altered(displacement))
        held_row = int(np.flatnonzero(np.max(abs(original.array(face['POSITION']) - ring[0]), axis=1) < 1e-7)[0])
        check('microscopic held-ring displacement refused', lambda: validate_altered(lambda d, b: array(d, b, face['POSITION']).__setitem__((held_row, 2), array(d, b, face['POSITION'])[held_row, 2] + .000001)))
        check('held-ring normal-only change refused', lambda: validate_altered(lambda d, b: array(d, b, face['NORMAL']).__setitem__((held_row, 0), .01)))
        check('incomplete original ring refused', lambda: transfer.verify_near(original, candidate, ring[:-1]))
        bad_ring = folder / 'changed-ring.json'
        bad_ring.write_bytes(a.held_ring.read_bytes() + b' ')
        check('unreviewed self-contained ring source refused', lambda: transfer.load_held_ring(bad_ring))
        values = {'POSITION': np.array([[0, 0, 0], [1, 0, 0]], dtype='<f4'),
                  'NORMAL': np.array([[0, 1, 0], [0, 1, 0]], dtype='<f4'),
                  'TANGENT': np.array([[1, 0, 0, 1], [1, 0, 0, 1]], dtype='<f4')}
        changed = {k: v.copy() for k, v in values.items()}
        changed['POSITION'][1, 2] = .001
        check('exact reordered row transfer maps deterministically', lambda: yes(transfer.row_mapping(values, changed, {k: v[::-1] for k, v in values.items()}).tolist() == [1, 0]), True)
        unknown = {k: v.copy() for k, v in values.items()}
        unknown['NORMAL'][0, 0] = .1
        check('position match with different original frame refused', lambda: transfer.row_mapping(values, changed, unknown))
        duplicate = {k: np.tile(v[:1], (2, 1)) for k, v in values.items()}
        check('ambiguous original row producing different forms refused', lambda: transfer.row_mapping(duplicate, changed, values))
        check('missing original attribute refused', lambda: transfer.row_mapping(values, changed, {'POSITION': values['POSITION']}))
        for level in ('mid', 'far'):
            lod = transfer.GLB(transfer.PROJECT / f'assets/heroes/rama-hero-{level}.glb')
            raw, receipt = transfer.transfer(original, candidate, lod)
            path = folder / f'{level}.glb'
            path.write_bytes(raw)
            actual = transfer.GLB(path)
            check(level + ' every declared POSITION NORMAL TANGENT bound exact', lambda: transfer.verify_frame_bounds(actual), True)
            def stale_frame(semantic):
                doc = copy.deepcopy(actual.doc)
                index = doc['meshes'][1]['primitives'][0]['attributes'][semantic]
                doc['accessors'][index]['min'][0] -= .001
                stale = folder / f'{level}-{semantic}-stale.glb'
                stale.write_bytes(transfer.encode(doc, actual.binary))
                return transfer.GLB(stale)
            for semantic in ('POSITION', 'NORMAL', 'TANGENT'):
                stale = stale_frame(semantic)
                check(level + ' stale ' + semantic + ' bound refused', lambda: transfer.verify_frame_bounds(stale))
                check(level + ' ' + semantic + ' bound-only repair reconciles exact BIN', lambda: transfer.verify_metadata_only_repair(stale, actual), True)
            def invalid_repair(binary_change=False):
                doc = copy.deepcopy(actual.doc)
                payload = bytearray(actual.binary)
                if binary_change:
                    payload[0] ^= 1
                else:
                    doc['asset']['generator'] = 'untracked replacement'
                target = folder / f'{level}-unsafe-repair.glb'
                target.write_bytes(transfer.encode(doc, bytes(payload)))
                return transfer.verify_metadata_only_repair(actual, transfer.GLB(target))
            check(level + ' metadata repair cannot change generator', invalid_repair)
            check(level + ' metadata repair cannot change any BIN byte', lambda: invalid_repair(True))
            check(level + ' complete held-ring positions and frames exact', lambda: transfer.verify_held_ring(lod, actual, ring), True)
            check(level + ' deterministic complete bytes', lambda: yes(transfer.transfer(original, candidate, lod)[0] == raw), True)
            check(level + ' rig nodes and animation structures retained', lambda: yes(all(lod.doc[k] == actual.doc[k] for k in ('nodes', 'skins', 'animations'))), True)
            check(level + ' all four decoded morphs unchanged', lambda: yes(all(
                np.array_equal(lod.array(v), actual.array(v)) for target in lod.doc['meshes'][1]['primitives'][0]['targets'] for v in target.values())), True)
        check('repository output refused before writing', lambda: transfer.build(transfer.PROJECT, a.candidate, a.held_ring, transfer.PROJECT / 'UNWRITTEN-form-test'))
        check('existing output refused before writing', lambda: transfer.build(transfer.PROJECT, a.candidate, a.held_ring, folder))
    result = {'schema': 1, 'task': 'R2-14', 'passed': all(c['passed'] for c in checks), 'count': len(checks),
              'checks': checks, 'candidate_sha256': transfer.sha(a.candidate),
              'source_sha256': {str(Path(transfer.__file__).relative_to(transfer.PROJECT)): transfer.sha(transfer.__file__),
                                str(Path(__file__).relative_to(transfer.PROJECT)): transfer.sha(__file__)},
              'scope': 'Exact form admission, source bounds, deterministic LOD correspondence and rejection tests; no imported deformation or visual acceptance.'}
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'count': len(checks), 'failures': [c for c in checks if not c['passed']]}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
