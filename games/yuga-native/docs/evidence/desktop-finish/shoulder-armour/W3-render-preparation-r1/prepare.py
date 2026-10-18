"""Prepare the inactive shoulder pair without a repository copy or engine run.

Run 'import' only after W1 receives its lane, then 'review' only after the
original strict resource comparator passes. Never writes canonical/base files.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
PROJECT = Path('/workspace/ANDOLAN/games/yuga-native')
ART = PROJECT / 'art/hero-finish/s5-shoulder-armour/compact-r6'
BASE = Path('/tmp/yuga-hair-r5-review-r1/baseline')
BASE_MARKER = '20aed49da1db66b48a2dcac9f0ced2afa9eb08753293a8bda943e7c256fab63e'
MANIFEST = '886528206ee33e1b3809e0363840ba9e08666883725985796fefbdb8da93ee0e'
COMPARATOR = 'bbfc6449f00cfcc268186772dcce338d312b276dc3a0306250c88a95e1042e52'
PROBE = 'acd250ce41adccb46bd0f7fabc012f84af32dd80fecc507cfe7c8e41dc39edaf'
HELPER = 'tools/graphics-six/shoulder_capture.gd'
assert hashlib.sha256((HERE / 'runner/snapshot.py').read_bytes()).hexdigest() == 'ab40dc59d9fae265d2b52e583e9b43ac7002d0eb959aaa9c7ddf4674a3ac3556'
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE / 'runner'))
import snapshot


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def link(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    os.link(source, target)


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def inputs():
    pins = json.loads((HERE / 'inputs.json').read_text())
    for row in pins['local_tools']:
        assert snapshot.digest(HERE / row['path']) == row['sha256'], row['path']
    for row in pins['external_tools']:
        assert snapshot.digest(Path(row['path'])) == row['sha256'], row['path']
    for row in pins['engines'].values():
        assert snapshot.digest(Path(row['path'])) == row['sha256']
    assert snapshot.digest(BASE / snapshot.MARKER) == BASE_MARKER
    base = snapshot.verify(BASE)
    assert snapshot.digest(ART / 'replacement-r7/replacement-manifest.json') == MANIFEST
    assert snapshot.digest(ART / 'compare_shoulder_import.py') == COMPARATOR
    assert snapshot.digest(ART / 'shoulder_import_semantics.gd') == PROBE
    manifest = json.loads((ART / 'replacement-r7/replacement-manifest.json').read_text())
    assert manifest['review_only'] and not manifest['default_activation']
    for level, row in manifest['levels'].items():
        name = Path(row['output']).name
        assert snapshot.digest(ART / 'replacement-r7' / name) == row['sha256']
        assert snapshot.digest(BASE / 'assets/heroes' / name) == row['source_sha256']
    assert snapshot.digest(BASE / 'scripts/rama_motion.gd') == pins['motion_sha256']
    assert snapshot.digest(BASE / 'scripts/rama_surface_finish.gd') == pins['finish_sha256']
    return pins, base, manifest


def prepare_import(work, pins, base, manifest):
    assert not work.exists(), 'Require a fresh private work root'
    work.mkdir(parents=True)
    candidate, baseline = work / 'import/candidate', work / 'import/baseline'
    settings = (BASE / 'project.godot').read_text()
    removed = 'run/main_scene="res://scenes/boot.tscn"\n'
    assert settings.count(removed) == 1
    for project in (candidate, baseline):
        project.mkdir(parents=True)
        (project / 'project.godot').write_text(settings.replace(removed, ''))
    for row in manifest['levels'].values():
        name = Path(row['output']).name
        rel = Path('assets/heroes') / name
        copy(ART / 'replacement-r7' / name, candidate / rel)
        copy(BASE / (str(rel) + '.import'), candidate / (str(rel) + '.import'))
        link(BASE / rel, baseline / rel)
        link(BASE / (str(rel) + '.import'), baseline / (str(rel) + '.import'))
    for name in base['files']:
        if name.startswith('.godot/imported/'):
            link(BASE / name, baseline / name)
        elif name in snapshot.AUX_FILES:
            copy(BASE / name, baseline / name)
    assert snapshot.verify(BASE) == base
    write(work / 'import-preparation.json', {
        'schema': 1, 'base': str(BASE), 'base_marker_sha256': BASE_MARKER,
        'base_files': base['files'], 'candidate_project': str(candidate),
        'baseline_project': str(baseline), 'candidate_manifest_sha256': MANIFEST,
        'settings_only_removed_line': removed.rstrip(),
        'candidate_before': {str(p.relative_to(candidate)): snapshot.metadata(p) for p in candidate.rglob('*') if p.is_file()},
        'raw_bytes_copied': sum(row['bytes'] for row in manifest['levels'].values()),
        'full_repository_copies': 0, 'engine_started': False,
        'scope': 'Minimal private importer; original descriptors/settings, three raw candidate copies, cached baseline hardlinks; no import yet.'})


def prepare_review(work, pins, base, manifest):
    prep = json.loads((work / 'import-preparation.json').read_text())
    assert prep['base_marker_sha256'] == BASE_MARKER and prep['base_files'] == base['files']
    proof = json.loads((work / 'import-comparison.json').read_text())
    assert proof['passed'] and proof['comparator_sha256'] == COMPARATOR
    assert proof['probe_sha256'] == PROBE and proof['manifest_sha256'] == MANIFEST
    for branch in ('baseline', 'candidate'):
        assert snapshot.digest(work / ('semantics-' + branch) / 'semantics.json') == proof[branch + '_semantics_sha256']
    imported = work / 'import/candidate'
    overrides = {}
    for row in manifest['levels'].values():
        rel = 'assets/heroes/' + Path(row['output']).name
        assert snapshot.digest(imported / rel) == row['sha256']
        assert (imported / (rel + '.import')).read_bytes() == (BASE / (rel + '.import')).read_bytes()
        overrides[rel] = imported / rel
    admitted = snapshot.imports(imported)
    assert len(admitted) == 3
    for row in admitted:
        assert len(row['outputs']) == 1 and row['outputs'][0].endswith('.scn')
        name = row['outputs'][0]
        for n in (name, str(Path(name).with_suffix('.md5'))):
            assert n in base['files']
            overrides[n] = imported / n
    assert len(overrides) == 9
    common = work / 'common/shoulder_capture.gd'
    assert not common.exists()
    copy(HERE / 'shoulder_capture.gd', common)
    store, records = work / 'private-store', {}
    for branch in ('baseline', 'candidate'):
        project = work / branch
        assert not project.exists()
        sources = {name: BASE / name for name in base['files']}
        sources[HELPER] = common
        if branch == 'candidate':
            sources.update(overrides)
        files = {name: snapshot.metadata(p) for name, p in sources.items()}
        for name, original in sources.items():
            target = project / name
            if name in snapshot.AUX_FILES:
                copy(original, target)
            elif name.startswith('.godot/imported/'):
                blob = store / 'imports' / files[name]['sha256']
                if not blob.exists():
                    link(original, blob)
                assert snapshot.metadata(blob) == files[name]
                link(blob, target)
            else:
                link(original, target)
        record = {'schema': 1, 'round': 'shoulder-r7-current-' + branch, 'project': str(project),
                  'source': str(BASE), 'store': str(store), 'files': files, 'branch': branch,
                  'frozen_ancestor_sha256': BASE_MARKER, 'validated_imports': snapshot.imports(project),
                  'scope': 'Matched accepted-UV-only shoulder component; no R5 hair. Immutable hardlinks, private auxiliary copies.'}
        write(project / snapshot.MARKER, record)
        snapshot.verify(project)
        records[branch] = {'project': str(project), 'marker_sha256': snapshot.digest(project / snapshot.MARKER), 'files': files}
    differences = sorted(n for n in records['baseline']['files'] if records['baseline']['files'][n] != records['candidate']['files'][n])
    assert differences == sorted(overrides)
    assert snapshot.verify(BASE) == base
    write(work / 'review-staging.json', {'schema': 1, 'passed': True, 'branches': records,
          'exact_pair_differences': differences, 'import_comparison_sha256': snapshot.digest(work / 'import-comparison.json'),
          'helper_sha256': snapshot.digest(common), 'base_unchanged': True, 'engine_started': False,
          'full_repository_copies': 0, 'raw_candidate_copied_once': True})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('import', 'review'))
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    assert args.work.is_absolute() and args.work.parent == Path('/tmp')
    pins, base, manifest = inputs()
    (prepare_import if args.phase == 'import' else prepare_review)(args.work, pins, base, manifest)
