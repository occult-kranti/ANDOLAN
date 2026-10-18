"""Stricter nonrail byte follow-up; signed zeros must not evade equality."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[5]
W = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'art/hero-rama-lod'))
from glb_lod import GLB


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    positive = np.array([0.0], dtype='<f4')
    negative = np.array([-0.0], dtype='<f4')
    assert np.array_equal(positive, negative) and positive.tobytes() != negative.tobytes()
    manifest = json.loads((ROOT / 'art/hero-finish/s4-diadem-fit/candidate-r1/source-manifest.json').read_text())
    base = Path('/tmp/yuga-s4-diadem-semantics-baseline-r1')
    candidate = Path('/tmp/yuga-s4-diadem-semantics-candidate-r1')
    a = json.loads((base / 'semantics.json').read_text())
    b = json.loads((candidate / 'semantics.json').read_text())
    assert (base / 'semantics.json').read_bytes() == (W / 'baseline-import-semantics-r1.json').read_bytes()
    assert (candidate / 'semantics.json').read_bytes() == (W / 'candidate-import-semantics-r1.json').read_bytes()
    archive = W / 'semantic-payloads-r1.tar.gz'
    assert digest(archive) == 'ecec0964837dfb54ac160b2eda6461d1e2c22491f7ae22e27231ffda90fa9e8f'
    payloads = tarfile.open(archive, 'r:gz')
    levels = []
    for lod, (level, row) in enumerate(manifest['levels'].items()):
        meshes = [n for n in a['lods'][lod]['nodes'] if n['path'].endswith('/RamaHero')]
        newmeshes = [n for n in b['lods'][lod]['nodes'] if n['path'].endswith('/RamaHero')]
        aa = next(s for s in meshes[0]['surfaces'] if s['material']['name'] == 'Worked warm gold')['arrays']
        bb = next(s for s in newmeshes[0]['surfaces'] if s['material']['name'] == 'Worked warm gold')['arrays']
        source = GLB(ROOT / row['source'])
        primitive = source.doc['meshes'][2]['primitives'][2]
        rail = source.array(primitive['attributes']['POSITION'])[row['selected_vertex_ids']]
        vertices = np.fromfile(base / aa[0]['file'], dtype='<f4').reshape(-1, 3)
        distances, _ = cKDTree(rail).query(vertices)
        mask = distances < 2e-6
        assert int(mask.sum()) == len(row['selected_vertex_ids'])
        arrays = []
        for index, width in [(0, 3), (1, 3), (2, 4)]:
            pa, pb = base / aa[index]['file'], candidate / bb[index]['file']
            assert pa.read_bytes() == payloads.extractfile('baseline/' + aa[index]['file']).read()
            assert pb.read_bytes() == payloads.extractfile('candidate/' + bb[index]['file']).read()
            old = np.fromfile(pa, dtype='<f4').reshape(-1, width)[~mask].tobytes()
            new = np.fromfile(pb, dtype='<f4').reshape(-1, width)[~mask].tobytes()
            assert old == new, (level, index)
            arrays.append({'array_index': index, 'nonrail_bytes': len(old), 'sha256': hashlib.sha256(old).hexdigest(), 'exact': True})
        levels.append({'level': level, 'rail_rows_excluded': int(mask.sum()), 'arrays': arrays})
    result = {'schema': 1, 'passed': True, 'scope': 'Strict raw-byte nonrail P/N/T equality, including signed zeros; no new engine or import.',
              'earlier_import_receipt_sha256': digest(W / 'import-receipt-r1.json'),
              'checker_sha256': digest(Path(__file__)), 'signed_zero_counterexample_rejected': True,
              'levels': levels}
    (W / 'import-nonrail-byte-audit-r1.json').write_text(json.dumps(result, indent=2) + '\n')
    print('3 LODs / 9 nonrail raw-byte arrays exact; signed-zero adversary rejected.')


if __name__ == '__main__':
    main()
