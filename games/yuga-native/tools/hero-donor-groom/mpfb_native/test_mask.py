"""Source-identity and mixed-region counterexamples for the exact mask helper."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from masked_glb import build


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--mask', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    original = json.loads(a.mask.read_text())
    checks = []
    positive = build(a.source, a.mask, a.output / 'positive.glb')
    checks.append({'name': 'actual original-byte positive reproduction', 'passed': positive['output_sha256'] == '491567c6bc0fa7e530e7668290961a177f1f681f441a290b980720a80582c8c4'})
    cases = {}
    wrong_source = copy.deepcopy(original)
    wrong_source['source_sha256'] = '0' * 64
    cases['wrong-source-identity'] = wrong_source
    mixed = copy.deepcopy(original)
    mixed['selected_accessor_vertex_ids'] = mixed['selected_accessor_vertex_ids'][1:]
    cases['mixed-region-triangle'] = mixed
    wrong_faces = copy.deepcopy(original)
    wrong_faces['removed_triangle_ids'] = wrong_faces['removed_triangle_ids'][1:]
    cases['inconsistent-triangle-selection'] = wrong_faces
    for name, data in cases.items():
        proof = a.output / (name + '.json')
        proof.write_text(json.dumps(data) + '\n')
        target = a.output / (name + '.glb')
        refused = False
        reason = ''
        try:
            build(a.source, proof, target)
        except AssertionError as error:
            refused = True
            reason = str(error)
        checks.append({'name': name, 'passed': refused and not target.exists(), 'reason': reason})
    result = {'schema_version': 1, 'checks': checks, 'passed': all(c['passed'] for c in checks),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'helper_sha256': hashlib.sha256(Path(__file__).with_name('masked_glb.py').read_bytes()).hexdigest(),
              'scope': 'Exact mask adapter reproduction and independent input-corruption negatives, not visual acceptance'}
    (a.output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
