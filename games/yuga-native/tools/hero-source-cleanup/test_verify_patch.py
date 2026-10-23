#!/usr/bin/env python3
"""Exercise eligibility rejection against corruptions of the real candidate.

All corruptions remain in memory. Neither the source nor the derivative is written.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from verify_patch import accessor, parse, verify_bytes


def run(source, candidate):
    original = source.read_bytes()
    trial = candidate.read_bytes()
    doc, binary = parse(original)
    primitive = doc['meshes'][0]['primitives'][0]
    po, ps, count = accessor(doc, binary, primitive['attributes']['POSITION'])
    no, ns, _ = accessor(doc, binary, primitive['attributes']['NORMAL'])
    changed = next(i for i in range(count)
                   if original[po+i*ps:po+i*ps+12] != trial[po+i*ps:po+i*ps+12])
    protected = next(i for i in range(count)
                     if struct.unpack_from('<3f', original, po+i*ps)[1] < .2)
    cases = []

    def accept(name, data):
        result = verify_bytes(original, data)
        assert result['passed']
        cases.append({'case': name, 'expected': 'accept', 'passed': True})

    def reject(name, data, message):
        try:
            verify_bytes(original, data)
        except ValueError as error:
            assert message in str(error), (name, str(error))
            cases.append({'case': name, 'expected': 'reject', 'passed': True,
                          'reason': str(error)})
        else:
            raise AssertionError(name + ' was accepted')

    accept('actual bounded candidate', trial)
    reject('unchanged source is not a cleanup', original, 'no position change')
    reject('truncated container', trial[:-4], 'Container size changed')

    changed_image = bytearray(trial)
    image_view = doc['bufferViews'][doc['images'][0]['bufferView']]
    changed_image[binary + image_view.get('byteOffset', 0) + 10] ^= 1
    reject('embedded image mutation', changed_image, 'nonpermitted bytes changed')

    changed_uv = bytearray(trial)
    uv = doc['accessors'][primitive['attributes']['TEXCOORD_0']]
    uv_view = doc['bufferViews'][uv['bufferView']]
    changed_uv[binary + uv_view.get('byteOffset', 0) + uv.get('byteOffset', 0)] ^= 1
    reject('UV mutation', changed_uv, 'nonpermitted bytes changed')

    changed_face = bytearray(trial)
    x, y, z = struct.unpack_from('<3f', original, po+protected*ps)
    struct.pack_into('<3f', changed_face, po+protected*ps, x+.00001, y, z)
    reject('protected nonhair position mutation', changed_face, 'protected rear-hair envelope')

    over_budget = bytearray(trial)
    x, y, z = struct.unpack_from('<3f', original, po+changed*ps)
    struct.pack_into('<3f', over_budget, po+changed*ps, x+.01, y, z)
    reject('hair displacement beyond cap', over_budget, 'Displacement exceeds cap')

    zero_normal = bytearray(trial)
    struct.pack_into('<3f', zero_normal, no+changed*ns, 0, 0, 0)
    reject('nonunit hair normal', zero_normal, 'normal is not unit length')

    nan_position = bytearray(trial)
    struct.pack_into('<f', nan_position, po+changed*ps, float('nan'))
    reject('nonfinite hair position', nan_position, 'Nonfinite candidate attribute')
    return {'schema_version': 1, 'scope': 'Mechanical eligibility counterexamples only.',
            'source_sha256': hashlib.sha256(original).hexdigest(),
            'candidate_sha256': hashlib.sha256(trial).hexdigest(),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'cases': cases, 'passed': all(c['passed'] for c in cases),
            'test_count': len(cases), 'files_mutated': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.source, args.candidate)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
