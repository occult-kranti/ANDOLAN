"""Reuse the verified snapshot API; no engine/import/build/render invocation."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PARENT_PIN = '36351a18fabfffe02bfea0a33bc2429a66668274fa61fe02bc9ce1acaf2bada1'
WORLD_PIN = '6e9d88657b5b3a69b67e0bc93e4f45988faa65d5206d9cabdaea45543e2d19bf'
CANDIDATE_PIN = 'd85c5384133858df2f910a99f453dd7883ee13cac1dd13fdf1fbf49574028234'
PAVING_PIN = '2e84ddd1afe67c70db6d8bdc700adaa0e34bee644a20825d4ecde0a7a0f88641'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--store', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    frozen = ROOT / 'docs/evidence/desktop-finish/G0/workspace-recovery-r1/tools/snapshot.py'
    spec = importlib.util.spec_from_file_location('frozen_snapshot', frozen)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parent, store, output = (path.resolve() for path in (args.parent, args.store, args.output))
    assert not output.exists(), 'fresh stage directory required'
    assert module.digest(parent / module.MARKER) == PARENT_PIN
    before = module.verify(parent)
    assert module.digest(parent / 'scripts/confluence_world.gd') == WORLD_PIN
    candidate = HERE.parent / 'overview-composition-r1/confluence_world.candidate.gd'
    assert module.digest(candidate) == CANDIDATE_PIN
    assert module.digest(ROOT / 'scripts/world_ground_common.gdshaderinc') == PAVING_PIN
    shared = {
        'tools/graphics-six/capture_scene_anchors.gd': HERE / 'capture_overview.gd',
        'scripts/world_ground_common.gdshaderinc': ROOT / 'scripts/world_ground_common.gdshaderinc',
    }
    output.mkdir(parents=True)
    records = {}
    for branch in ('baseline', 'candidate'):
        project = output / (branch + '-project')
        record = module.refresh(parent, project, store, 'G4-overview-' + branch + '-r2', output / (branch + '-initial-source.json'))
        for name, source in shared.items(): module.atomic_copy(source, project / name)
        if branch == 'candidate': module.atomic_copy(candidate, project / 'scripts/confluence_world.gd')
        actual = module.inventory(project)
        delta = sorted(name for name in actual.keys() | before['files'].keys() if actual.get(name) != before['files'].get(name))
        expected = sorted(list(shared) + (['scripts/confluence_world.gd'] if branch == 'candidate' else []))
        assert delta == expected, delta
        record.update(files=actual, canonical_files=before['files'], parent_snapshot_sha256=PARENT_PIN,
                      parent_snapshot=str(parent), changed_paths=delta,
                      harness_overlays={name: module.metadata(project / name) for name in shared},
                      declared_runtime_overlay={'scripts/confluence_world.gd': module.metadata(project / 'scripts/confluence_world.gd')} if branch == 'candidate' else {},
                      source_bytes=sum(value['bytes'] for name, value in actual.items() if not name.startswith('.godot/')),
                      scope='Three matched genuine overview views via scene-anchors transport and explicit3-shot-count-only runner copy. Common helper and promoted paving2e84 in both branches; candidate only replaces presentation caller6e9 with d85c. No geometry/collision/import/canonical/source-parent mutation.')
        receipt = output / (branch + '-source.json')
        receipt.write_text(json.dumps(record, indent=2) + '\n')
        module.atomic_copy(receipt, project / module.MARKER)
        module.verify(project)
        records[branch] = record
    runtime_delta = sorted(name for name in records['baseline']['files'].keys() | records['candidate']['files'].keys() if records['baseline']['files'].get(name) != records['candidate']['files'].get(name))
    assert runtime_delta == ['scripts/confluence_world.gd'], runtime_delta
    module.verify(parent)
    assert module.digest(parent / module.MARKER) == PARENT_PIN
    summary = {'passed': True, 'parent': str(parent), 'parent_snapshot_sha256': PARENT_PIN,
               'pair_file_delta': runtime_delta, 'shared_inputs': {name: module.metadata(source) for name, source in shared.items()},
               'snapshot_api': {'path': str(frozen), **module.metadata(frozen)},
               'projects': {branch: {'path': str(output / (branch + '-project')), 'marker_sha256': module.digest(output / (branch + '-project') / module.MARKER), 'files': len(record['files']), 'imports': len(record['validated_imports'])} for branch, record in records.items()},
               'collider_difference': 'NONE: exact inventory must match for every retained object and shape in allthree views.',
               'render': 'UNRUN; W1 owns queue. Only overview camera translation and column/ordinaryHUD presentation differ. Original playercamera, pose, clocks, light and collider state must match across paired branches.'}
    (output / 'staging.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__': main()
