"""Qualify the one isolated import; retain the earlier source-only receipt."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[5]
W = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'tools/graphics-six'))
import snapshot
sys.path.insert(0, str(ROOT / 'art/hero-rama-lod'))
from glb_lod import GLB


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def differences(a, b, path=''):
    if type(a) != type(b): return [path]
    if isinstance(a, dict):
        return [d for k in sorted(set(a) | set(b)) for d in
                (differences(a[k], b[k], path + '/' + k) if k in a and k in b else [path + '/' + k])]
    if isinstance(a, list):
        return [path] if len(a) != len(b) else [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, path + '/' + str(i))]
    return [] if a == b else [path]


def main():
    prep = json.loads((W / 'import-preparation.json').read_text())
    imported = Path(prep['candidate_project']); baseline = Path(prep['baseline_cached_project'])
    bpath = Path('/tmp/yuga-s4-diadem-semantics-baseline-r1')
    cpath = Path('/tmp/yuga-s4-diadem-semantics-candidate-r1')
    b = json.loads((bpath / 'semantics.json').read_text()); c = json.loads((cpath / 'semantics.json').read_text())
    assert b['complete'] and c['complete']
    manifest = json.loads((ROOT / 'art/hero-finish/s4-diadem-fit/candidate-r1/source-manifest.json').read_text())
    expected = []; checks = []; levels = []
    native = json.loads(gzip.decompress((ROOT / 'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()))
    for lod, (level, row) in enumerate(manifest['levels'].items()):
        before, after = b['lods'][lod], c['lods'][lod]
        assert before['raw_sha256'] == row['source_sha256'] and after['raw_sha256'] == row['sha256']
        for key in ['path', 'descriptor_sha256', 'imported_path']: assert before[key] == after[key]
        if level == 'near':
            for key, path in [('raw_sha256', before['path']), ('descriptor_sha256', before['path'] + '.import'), ('imported_sha256', before['imported_path'])]:
                assert before[key] == native['source_before'][path]
        expected += [f'/lods/{lod}/raw_sha256', f'/lods/{lod}/imported_sha256']
        meshes = [(i, n) for i, n in enumerate(before['nodes']) if n['path'].endswith('/RamaHero')]
        assert len(meshes) == 1; ni, mesh = meshes[0]
        surfaces = [(i, s) for i, s in enumerate(mesh['surfaces']) if s['material']['name'] == 'Worked warm gold']
        assert len(surfaces) == 1; si, surface = surfaces[0]
        arrays = surface['arrays']; newarrays = after['nodes'][ni]['surfaces'][si]['arrays']
        oldg = GLB(ROOT / row['source']); newg = GLB(Path(row['output']))
        ids = np.array(row['selected_vertex_ids']); p = oldg.doc['meshes'][2]['primitives'][2]
        oldv = oldg.array(p['attributes']['POSITION'])[ids]; newv = newg.array(p['attributes']['POSITION'])[ids]
        iv = np.fromfile(bpath / arrays[0]['file'], dtype='<f4').reshape(-1, 3)
        nv = np.fromfile(cpath / newarrays[0]['file'], dtype='<f4').reshape(-1, 3)
        distance, _ = cKDTree(oldv).query(iv); newdistance, _ = cKDTree(newv).query(nv)
        mask = distance < 2e-6; newmask = newdistance < 2e-6
        assert np.array_equal(mask, newmask) and int(mask.sum()) == len(ids)
        for ai, width in [(0, 3), (1, 3), (2, 4)]:
            expected.append(f'/lods/{lod}/nodes/{ni}/surfaces/{si}/arrays/{ai}/digest')
            aa = np.fromfile(bpath / arrays[ai]['file'], dtype='<f4').reshape(-1, width)
            bb = np.fromfile(cpath / newarrays[ai]['file'], dtype='<f4').reshape(-1, width)
            assert np.array_equal(aa[~mask], bb[~mask]), 'imported nonrail record changed'
        rigs = [n for n in after['nodes'] if n['class'] == 'Skeleton3D']
        assert len(rigs) == 1 and len(rigs[0]['bone_order']) == 164
        names = [oldg.doc['nodes'][i]['name'] for i in oldg.doc['skins'][0]['joints']]
        assert names == [n['name'] for n in rigs[0]['bone_order']]
        assert rigs[0]['bone_order'][104]['name'] == 'head'
        levels.append({'level': level, 'selected_imported_vertices': int(mask.sum()),
            'rail_to_stored_source_maximum_error_m': float(newdistance[mask].max()),
            'all_imported_nonrail_records_exact': True, 'all164_imported_bone_names_match_source': True,
            'actual_imported_bone_order': rigs[0]['bone_order']})
    actual = differences(b, c)
    assert sorted(actual) == sorted(expected)
    for rel, metadata in prep['canonical_before'].items():
        p = ROOT / rel
        assert p.stat().st_size == metadata['bytes'] and sha(p) == metadata['sha256']
    shared = snapshot.verify(Path(prep['shared_base']))
    assert sha(Path(prep['shared_base']) / snapshot.MARKER) == prep['shared_marker_sha256']
    for rel, metadata in prep['baseline_before'].items():
        p = baseline / rel
        assert p.stat().st_size == metadata['bytes'] and sha(p) == metadata['sha256']
    imported_files = {}
    texture_matches = []; scene_changes = []
    for p in sorted(imported.rglob('*')):
        if not p.is_file(): continue
        rel = str(p.relative_to(imported))
        if p.suffix not in ['.scn', '.ctex', '.md5', '.import', '.png', '.glb']: continue
        imported_files[rel] = {'sha256': sha(p), 'bytes': p.stat().st_size}
        old = ROOT / rel
        if p.suffix in ['.ctex', '.png', '.import']:
            assert old.is_file() and sha(old) == sha(p)
            texture_matches.append(rel)
        if p.suffix == '.scn': scene_changes.append(rel)
    assert len(scene_changes) == 3
    imports = snapshot.imports(imported)
    # All exported binary arrays and semantic payloads are retained together;
    # generated scene bytes/MD5s support reconstruction after /tmp loss.
    with tarfile.open(W / 'semantic-payloads-r1.tar.gz', 'w:gz') as tar:
        for label, directory in [('baseline', bpath), ('candidate', cpath)]:
            for p in sorted(directory.iterdir()): tar.add(p, arcname=label + '/' + p.name)
    with tarfile.open(W / 'candidate-import-cache-r1.tar.gz', 'w:gz') as tar:
        for rel in scene_changes:
            for p in [imported / rel, (imported / rel).with_suffix('.md5')]: tar.add(p, arcname=str(p.relative_to(imported)))
        for p in sorted((imported / 'assets/heroes').glob('*.glb.import')): tar.add(p, arcname=str(p.relative_to(imported)))
    shutil.copyfile(bpath / 'semantics.json', W / 'baseline-import-semantics-r1.json')
    shutil.copyfile(cpath / 'semantics.json', W / 'candidate-import-semantics-r1.json')
    report = {'schema': 1, 'passed': True, 'scope': 'Actual imported candidate/baseline semantics, source bytes and immutable-store integrity. No candidate runtime controller execution or rendering.',
        'source_only_receipt_preserved_sha256': sha(W / 'receipt.json'),
        'comparison_script_sha256': sha(Path(__file__)), 'probe_sha256': sha(W / 'import_semantics.gd'),
        'exact_semantic_difference_paths': actual, 'levels': levels,
        'unchanged': ['all materials and actual texture pixel/format/mipmap payloads', 'all UV/color/bone/weight/index arrays',
                      'all nonrail mesh records', 'all node transforms and full-mesh AABBs', 'all skin bind names/matrices',
                      'all164 skeleton names/parents/rests/poses', 'all animations and morph payloads'],
        'canonical_relevant_files_unchanged': len(prep['canonical_before']),
        'shared_base_and_all_referenced_store_blobs_unchanged': len(shared['files']),
        'cached_baseline_files_unchanged': len(prep['baseline_before']),
        'baseline_near_raw_descriptor_and_scene_exact_to348_tape': True,
        'imported_resources': imported_files, 'verified_import_pairs': len(imports),
        'exact_generated_texture_or_descriptor_files': texture_matches,
        'archives': {name: {'sha256': sha(W / name), 'bytes': (W / name).stat().st_size}
                     for name in ['semantic-payloads-r1.tar.gz', 'candidate-import-cache-r1.tar.gz']},
        'remaining': ['Matched front/profile/rear rest plus cast original images', 'No default activation or canonical promotion',
                      'No mid/far posed or whole-body continuous contact claim']}
    (W / 'import-comparison-r1.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Actual imported comparison passed;15 intended semantic differences,3LODs,164bone order exact.')


if __name__ == '__main__': main()
