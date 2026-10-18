#!/usr/bin/env python3
"""Create private matched children; never run an engine or mutate the base/store."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path('/workspace/ANDOLAN/games/yuga-native')
sys.path.insert(0, '/tmp/yuga-desktop-recovery-r1/current-project/tools/graphics-six')
import snapshot

RAW_NAMES = ('rama-hero.glb', 'rama-hero-mid.glb', 'rama-hero-far.glb')
HELPER = 'tools/graphics-six/hair_capture.gd'
EXPECTED_BASE = 'ec8122b5bb95901354723e49d597ecd2af2515fd1fd2219599f8482aba435682'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    base, out, receipt = [p.resolve() for p in (args.base, args.output, args.receipt)]
    assert not out.exists() and not receipt.exists(), 'Fresh paths required'
    assert snapshot.digest(base / snapshot.MARKER) == EXPECTED_BASE
    original = snapshot.verify(base)
    inputs = ROOT / 'art/hero-finish/hair-silhouette-r1/candidate-r4-accepted-uv'
    manifest = json.loads((inputs / 'groom-manifest.json').read_text())
    imported = Path('/tmp/yuga-hair-import-r1/candidate-project')
    proof = json.loads((Path('/tmp/yuga-hair-import-r1/evidence/import-comparison-r1.json')).read_text())
    assert proof['passed']
    overrides = {}
    for original_row in manifest['levels'].values():
        row = {'file': Path(original_row['output']).name, 'output_sha256':original_row['output_sha256'], 'input_sha256':original_row['source_sha256']}
        row = {**row, 'source': 'assets/heroes/' + row['file'], 'sha256': row['output_sha256'], 'source_sha256': row['input_sha256']}
        name = Path(row['source']).name
        assert name in RAW_NAMES
        source = inputs / name
        assert snapshot.digest(source) == row['sha256']
        assert snapshot.digest(base / row['source']) == row['source_sha256']
        assert (base / (row['source'] + '.import')).read_bytes() == (imported / (row['source'] + '.import')).read_bytes()
        overrides[row['source']] = source
    for rel, item in proof['imported_resources'].items():
        if Path(rel).suffix not in ('.scn', '.md5') or '.glb-' not in rel:
            continue
        source = imported / rel
        assert snapshot.metadata(source) == item
        overrides[rel] = source
    assert len(overrides) == 9
    store = out / 'private-store'
    records = {}
    for branch in ('baseline', 'candidate'):
        project = out / branch
        desired = {**original['files'], HELPER: snapshot.metadata(Path(__file__).with_name('hair_capture_cleanup.gd'))}
        branch_overrides = {HELPER: Path(__file__).with_name('hair_capture_cleanup.gd')}
        if branch == 'candidate':
            branch_overrides.update(overrides)
            desired.update({name: snapshot.metadata(p) for name, p in overrides.items()})
        for name, item in desired.items():
            source = branch_overrides.get(name, base / name)
            target = project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if name.startswith('.godot/imported/'):
                blob = store / 'imports' / item['sha256']
                snapshot.retain(source, blob, item)
                os.link(blob, target)
            else:
                shutil.copyfile(source, target)
        record = {'schema': 1, 'round': 'G4-hair-accepted-UV-' + branch, 'source': str(base), 'project': str(project),
                  'store': str(store), 'files': desired, 'base_marker_sha256': EXPECTED_BASE,
                  'branch': branch, 'validated_imports': snapshot.imports(project),
                  'source_bytes':sum(v['bytes'] for k,v in desired.items() if not k.startswith('.godot/')),
                  'compiled_bytes':sum(v['bytes'] for k,v in desired.items() if k.startswith('.godot/imported/')),
                  'scope': 'Private exact source comparison; no raster/import/default activation.'}
        (project / snapshot.MARKER).write_text(json.dumps(record, indent=2) + '\n')
        snapshot.verify(project)
        records[branch] = {'project': str(project), 'marker_sha256': snapshot.digest(project / snapshot.MARKER),
                           'files': desired, 'imports': len(record['validated_imports'])}
    changed = sorted(name for name in records['baseline']['files'] if records['baseline']['files'][name] != records['candidate']['files'][name])
    assert changed == sorted(overrides)
    snapshot.verify(base)
    assert snapshot.digest(base / snapshot.MARKER) == EXPECTED_BASE
    result = {'schema': 1, 'passed': True, 'base': str(base), 'base_marker_sha256': EXPECTED_BASE,
              'base_and_shared_store_unchanged': True, 'branches': records, 'exact_pair_difference_paths': changed,
              'helper_source': str(Path(__file__).with_name('hair_capture_cleanup.gd')), 'helper_runtime_path': HELPER,
              'helper_sha256': snapshot.digest(Path(__file__).with_name('hair_capture_cleanup.gd')),
              'private_store': str(store), 'engine_started': False}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'differences': changed, 'receipt': str(receipt)}))


if __name__ == '__main__':
    main()
