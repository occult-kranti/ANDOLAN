#!/usr/bin/env python3
"""Small declared helper overlay on the verified96d5 frontage baseline; no engine/import."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / 'AGENTS.md').is_file())
NATIVE = REPO / 'games/yuga-native'
BASE = Path('/workspace/scratch/yuga-frontage-review-r1/baseline-r4')
ROOT = Path('/workspace/scratch/yuga-locomotion-current-r1')
PROJECT = ROOT / 'project'
SOURCE = '96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
PARENT_MARKER = 'f6e2d474cc2392eae91f9eb2048d0231d07331318a94c6b6a4bc58b44ad802bb'
ENGINE = 'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def put(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def main():
    assert not ROOT.exists(), 'Fresh dedicated derivative required'
    spec = importlib.util.spec_from_file_location('snapshot', HERE / 'snapshot.py')
    snapshot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(snapshot)
    parent = snapshot.verify(BASE)
    assert sha(BASE / snapshot.MARKER) == PARENT_MARKER
    assert parent['source_commit'] == SOURCE
    assert parent['files']['scripts/rama_motion.gd']['sha256'] == '5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5'
    floor = 500 * 1024**2
    allowance = 480 * 1024**2
    assert shutil.disk_usage(ROOT.parent).free >= floor + allowance
    overlays = {
        'tools/graphics-six/capture_transition.gd': NATIVE / 'docs/evidence/desktop-finish/S3/W5-capture-preparation/capture_transition.gd',
        'tools/graphics-six/capture_locomotion.gd': HERE / 'capture_locomotion.gd',
        'tools/graphics-six/locomotion-sequence.json': HERE / 'locomotion-sequence.json',
    }
    expected = dict(parent['files'])
    expected.update({n: snapshot.metadata(p) for n, p in overlays.items()})
    PROJECT.mkdir(parents=True)
    copied = []
    linked = []
    for name in sorted(expected):
        target = PROJECT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if name in overlays or name in snapshot.AUX_FILES:
            shutil.copyfile(overlays.get(name, BASE / name), target)
            copied.append(name)
        else:
            os.link(BASE / name, target)
            linked.append(name)
    record = dict(parent)
    record.update(project=str(PROJECT), round='current96-natural-locomotion-r1', files=expected,
                  previous_marker_sha256=PARENT_MARKER, source_commit=SOURCE,
                  source_bytes=sum(v['bytes'] for n, v in expected.items() if not n.startswith('.godot/')),
                  helper_successor={n: {'path': str(p), **expected[n]} for n, p in overlays.items()})
    record['common_harness_overlay'] = dict(parent.get('common_harness_overlay', {}))
    record['common_harness_overlay'].update({n: expected[n] for n in overlays})
    put(PROJECT / snapshot.MARKER, record)
    snapshot.verify(BASE)
    snapshot.verify(PROJECT)
    assert sha(BASE / snapshot.MARKER) == PARENT_MARKER
    assert snapshot.imports(PROJECT) == snapshot.imports(BASE)
    delta = sorted(n for n in expected.keys() | parent['files'].keys() if expected.get(n) != parent['files'].get(n))
    assert delta == sorted(overlays)
    pair = {'schema': 1, 'source_commit': SOURCE, 'stages': {'current': {
        'project': str(PROJECT), 'seal_sha256': sha(PROJECT / snapshot.MARKER)}},
        'required_free_floor_bytes': floor, 'run_allowance_bytes': allowance,
        'preflight_allowance_bytes': 96 * 1024**2,
        'scope': 'One current-source derivative, not a historical or paired-motion equivalence claim.'}
    put(ROOT / 'stage.json', pair)
    current_inputs_path = BASE.parent / 'execution-inputs.json'
    current_inputs = json.loads(current_inputs_path.read_text())
    old_runtime_path = NATIVE / 'docs/evidence/desktop-finish/S3/W5-actual-motion-r1/render-inputs.json'
    old_runtime = json.loads(old_runtime_path.read_text())['render_runtime']
    assert current_inputs['engine']['sha256'] == ENGINE
    assert sha(Path(current_inputs['engine']['path'])) == ENGINE
    for item in old_runtime['files'].values():
        assert sha(Path(item['path'])) == item['sha256']
    inputs = {'schema': 1, 'pair_sha256': sha(ROOT / 'stage.json'),
        'engine': current_inputs['engine'], 'render_runtime': old_runtime,
        'snapshot_validator': {'path': str(HERE / 'snapshot.py'), 'sha256': sha(HERE / 'snapshot.py')},
        'godot_seed': current_inputs['cache_seeds']['godot'], 'mesa_seed': current_inputs['cache_seeds']['mesa'],
        'parent_inputs': {'path': str(current_inputs_path), 'sha256': sha(current_inputs_path)},
        'render_runtime_ancestry': {'path': str(old_runtime_path), 'sha256': sha(old_runtime_path)},
        'scope': 'Explicit e69 pipeline-low-priority diagnostic patch, unchanged96d5 gameplay. No extracted-package or GPU-performance claim.'}
    put(ROOT / 'render-inputs.json', inputs)
    receipt = {'passed': True, 'source_commit': SOURCE, 'parent_project': str(BASE),
        'parent_marker_sha256': PARENT_MARKER, 'project': str(PROJECT),
        'marker_sha256': sha(PROJECT / snapshot.MARKER), 'source_files': len(expected),
        'import_pairs': len(snapshot.imports(PROJECT)), 'only_file_delta': delta,
        'linked_files': len(linked), 'private_copied_files': copied,
        'private_copied_bytes': sum(expected[n]['bytes'] for n in copied),
        'engine_runs': 0, 'imports_run': 0, 'parent_and_store_unchanged': True,
        'free_bytes_after': shutil.disk_usage(ROOT).free,
        'stage_sha256': sha(ROOT / 'stage.json'), 'render_inputs_sha256': sha(ROOT / 'render-inputs.json')}
    put(ROOT / 'staging-receipt.json', receipt)
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
