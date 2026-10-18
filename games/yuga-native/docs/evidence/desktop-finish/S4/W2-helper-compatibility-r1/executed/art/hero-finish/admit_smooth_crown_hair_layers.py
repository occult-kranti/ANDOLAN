"""Overlay compatibility metadata; preserve the original R7 guide author and points.

Run after build_g2_hair_layers.py only against its historical R7 source. This
separate step admits the reviewed crown-only derivative, without repinning the
historical generator or activating the optional helper.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / 'art/hero-rama-lod'))
from glb_lod import GLB

ORIGINAL = '8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c'
SMOOTH = 'e98c9110161e49b653e98b6f4ca1dda997ad891cf73b737abd18f319bb3c2b82'
GENERATOR = '8b929a7b6481b8b95d611e90a10b8d8c80d70169ee8ff3fa087726dee4add934'
PROOF = 'docs/evidence/desktop-finish/S4/W1-smooth-crown-r1/import-and-staging/import-comparison-r1.json'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    old = GLB(PROJECT / 'art/visual-rounds/groom/principal-groom-v1/rama-hero.glb')
    new = GLB(PROJECT / 'assets/heroes/rama-hero.glb')
    assert sha(old.path) == ORIGINAL and sha(new.path) == SMOOTH
    assert old.doc == new.doc, 'Crown-only derivative must retain complete GLB JSON'
    primitive = old.doc['meshes'][2]['primitives'][0]
    assert old.doc['materials'][primitive['material']]['name'] == 'Swept black hair'
    accessors = set(primitive['attributes'].values()) | {primitive['indices']}
    for target in primitive.get('targets', []):
        accessors.update(target.values())
    records = []
    for index in sorted(accessors):
        before, after = old.array(index).tobytes(), new.array(index).tobytes()
        assert before == after, ('Hair accessor changed', index)
        records.append({'accessor': index, 'bytes': len(before), 'sha256': hashlib.sha256(before).hexdigest()})
    guide_path = PROJECT / 'assets/hero-finish/upper-hair-layers.json'
    data = json.loads(guide_path.read_text())
    assert data['schema'] in (1, 2) and data['source_sha256'] == ORIGINAL
    assert data['generator_sha256'] == GENERATOR == sha(PROJECT / data['generator'])
    guides_before = json.dumps(data['guides'], sort_keys=True).encode()
    data.update(schema=2, admitted_source_sha256s=[ORIGINAL, SMOOTH], compatibility={
        'revision': 'smooth-crown-r2', 'proof': PROOF, 'proof_sha256': sha(PROJECT / PROOF),
        'scope': 'Original near-LOD hair primitive arrays, morphs, indices, rig and material JSON unchanged. No new helper geometry or activation.'})
    assert guides_before == json.dumps(data['guides'], sort_keys=True).encode()
    expected = json.dumps(data, indent=2, sort_keys=True) + '\n'
    if a.write:
        guide_path.write_text(expected)
    else:
        assert guide_path.read_text() == expected, 'Guide metadata overlay is missing or stale'
    report = {'passed': True, 'original_sha256': ORIGINAL, 'admitted_sha256': SMOOTH,
        'generator_sha256': GENERATOR, 'overlay_sha256': sha(__file__),
        'import_proof': PROOF, 'import_proof_sha256': sha(PROJECT / PROOF),
        'hair_accessors': records, 'guide_points_sha256': hashlib.sha256(guides_before).hexdigest(),
        'guide_sha256': sha(guide_path), 'runtime_scope': 'Metadata admission is not raw-file identity verification; runtime retains its rig/rest/material contract. Optional helper stays inactive.'}
    a.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': True, 'unchanged_hair_accessors': len(records), 'guide_sha256': report['guide_sha256']}))

if __name__ == '__main__':
    main()
