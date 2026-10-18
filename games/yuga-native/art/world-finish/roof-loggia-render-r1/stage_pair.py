"""Reuse the verified snapshot API; no engine/import/build/render invocation."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PARENT_PIN = '36351a18fabfffe02bfea0a33bc2429a66668274fa61fe02bc9ce1acaf2bada1'
WORLD_PIN = '6e9d88657b5b3a69b67e0bc93e4f45988faa65d5206d9cabdaea45543e2d19bf'
CANDIDATE_PIN = 'e64c72770b3d65fcce681999b265236821a6532420b6e9c7e75c02eed00eefff'
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
    candidate = HERE.parent / 'roof-loggia-r1/candidate.gd'
    assert module.digest(candidate) == CANDIDATE_PIN
    assert module.digest(ROOT / 'scripts/world_ground_common.gdshaderinc') == PAVING_PIN
    shared = {
        'tools/graphics-six/capture_scene_anchors.gd': HERE / 'capture_roof.gd',
        'scripts/review_roof_loggia.gd': candidate,
        'NOTICE/roof-loggia-review.md': HERE.parent / 'roof-loggia-r1/NOTICE.md',
        'scripts/world_ground_common.gdshaderinc': ROOT / 'scripts/world_ground_common.gdshaderinc',
    }
    output.mkdir(parents=True)
    records = {}
    for branch in ('baseline', 'candidate'):
        project = output / (branch + '-project')
        record = module.refresh(parent, project, store, 'G4-roof-loggia-' + branch + '-r3', output / (branch + '-initial-source.json'))
        for name, source in shared.items(): module.atomic_copy(source, project / name)
        if branch == 'candidate':
            path = project / 'scripts/confluence_world.gd'
            text = path.read_text()
            anchor = '\t_build_lighting()\n\t_build_player()'
            assert text.count(anchor) == 1
            text = text.replace(anchor, '\t_build_lighting()\n\t# Isolated review-only roof replacement; no canonical activation.\n\tload("res://scripts/review_roof_loggia.gd").configure(world)\n\t_build_player()')
            path.write_text(text)
        actual = module.inventory(project)
        delta = sorted(name for name in actual.keys() | before['files'].keys() if actual.get(name) != before['files'].get(name))
        expected = sorted(list(shared) + (['scripts/confluence_world.gd'] if branch == 'candidate' else []))
        assert delta == expected, delta
        record.update(files=actual, canonical_files=before['files'], parent_snapshot_sha256=PARENT_PIN,
                      parent_snapshot=str(parent), changed_paths=delta,
                      harness_overlays={name: module.metadata(project / name) for name in shared},
                      declared_runtime_overlay={'scripts/confluence_world.gd': module.metadata(project / 'scripts/confluence_world.gd')} if branch == 'candidate' else {},
                      source_bytes=sum(value['bytes'] for name, value in actual.items() if not name.startswith('.godot/')),
                      scope='Two matched roof review views via unchanged external runner scene-anchors transport alias. Common helper/payload/NOTICE and promoted paving2e84 in both branches; candidate only inserts one configure call after lighting. New visible roof and exact matching local3D collider are declared. No import or canonical/source-parent mutation.')
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
               'collider_difference': 'Candidate adds exactly one layer1 StaticBody3D with828 visible triangle faces, no invisible plinth. Baseline old roof has no collider. Existing collision objects and shapes must compare identically in both shots after removing this named added body.',
               'render': 'UNRUN; W1 owns queue. No camera/pose/clock/lighting difference is allowed between paired branches; one supplemental close camera is identical in both.'}
    (output / 'staging.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__': main()
