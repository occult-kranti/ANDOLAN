#!/usr/bin/env python3
"""One reusable render project; retain displaced source bytes, deduplicate imports.

Never runs Godot/imports. Only a named snapshot and content store are mutated.
Refresh is admitted only after the previous snapshot still matches its seal.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

SOURCE_DIRS = ('scripts', 'scenes', 'shaders', 'assets', 'NOTICE',
               'tools/ui-campaign', 'tools/visual-campaign',
               'tools/visual-rounds', 'tools/graphics-six')
ROOT_FILES = ('project.godot', 'export_presets.cfg', 'art/world/confluence-map.json',
              'art/world-finish/lane-frontage-r1/candidate.gd',
              'art/world-finish/lane-frontage-r1/candidate-mesh.json',
              'tests/ui_campaign_flow_cases.gd')  # Existing UI runner pins this helper.
AUX_FILES = ('.godot/global_script_class_cache.cfg', '.godot/uid_cache.bin',
             '.godot/extension_list.cfg')
MARKER = '.graphics-six-snapshot.json'


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def metadata(path):
    return {'sha256': digest(path), 'bytes': path.stat().st_size}


def paths(project):
    result = {name for name in ROOT_FILES + AUX_FILES if (project / name).is_file()}
    for directory in SOURCE_DIRS + ('.godot/imported',):
        for path in (project / directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                if path.is_symlink():
                    raise ValueError('Symlink source is not admitted: ' + str(path))
                result.add(path.relative_to(project).as_posix())
    return sorted(result)


def inventory(project):
    return {name: metadata(project / name) for name in paths(project)}


def imports(project):
    receipts = []
    for raw in (project / 'assets').rglob('*'):
        if raw.is_file() and raw.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.svg', '.glb', '.gltf', '.ttf', '.otf', '.wav', '.ogg') and not Path(str(raw) + '.import').is_file():
            raise ValueError('Raw asset has no import descriptor: ' + str(raw.relative_to(project)))
    for name in paths(project):
        if not name.endswith('.import'):
            continue
        raw = project / name[:-7]
        if not raw.is_file():
            raise ValueError('Import descriptor has no raw source: ' + name)
        text = (project / name).read_text()
        outputs = re.findall(r'^path(?:\.[A-Za-z0-9_]+)?="res://([^"\n]+)"', text, re.M)
        if not outputs:
            raise ValueError('Import descriptor has no output: ' + name)
        md5 = hashlib.md5(raw.read_bytes()).hexdigest()
        for output in outputs:
            if not output.startswith('.godot/imported/') or '..' in Path(output).parts:
                raise ValueError('Unexpected import path: ' + output)
            compiled = project / output
            check = compiled.with_suffix('.md5')
            if not check.is_file() and compiled.suffix == '.ctex' and compiled.stem.endswith(('.s3tc', '.etc2')):
                check = compiled.with_suffix('').with_suffix('.md5')
            if not compiled.is_file() or not check.is_file():
                raise ValueError('Missing compiled import/receipt: ' + output)
            match = re.search(r'^source_md5="([a-f0-9]{32})"', check.read_text(), re.M)
            if not match or match[1] != md5:
                raise ValueError('Stale compiled import: ' + name)
        receipts.append({'source': name[:-7], 'source_md5': md5, 'outputs': outputs})
    if not receipts:
        raise ValueError('No import descriptors validated')
    return receipts


def verify(project):
    record = json.loads((project / MARKER).read_text())
    actual = inventory(project)
    expected = record['files']
    differences = sorted(name for name in actual.keys() | expected.keys()
                         if actual.get(name) != expected.get(name))
    if differences:
        raise ValueError('Previous snapshot changed; retain failure before refresh: ' + ', '.join(differences))
    for name, item in expected.items():
        if name.startswith('.godot/imported/'):
            blob = Path(record['store']) / 'imports' / item['sha256']
            if not blob.is_file() or metadata(blob) != item:
                raise ValueError('Immutable import store changed: ' + name)
    return record


def atomic_copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def retain(source, store, item):
    if store.exists():
        if metadata(store) != item:
            raise ValueError('Content-addressed store collision/corruption: ' + str(store))
    else:
        atomic_copy(source, store)
        if metadata(store) != item:
            raise ValueError('Source changed while preserving bytes: ' + str(source))
        store.chmod(0o444)


def refresh(source, project, store, round_id, receipt, dry_run=False, overlays=None):
    source, project, store, receipt = [Path(x).resolve() for x in (source, project, store, receipt)]
    for a, b in ((source, project), (source, store), (project, store)):
        if a == b or a in b.parents or b in a.parents:
            raise ValueError('Source, snapshot and store must be separate trees')
    if receipt.exists() or project in receipt.parents or source in receipt.parents or store in receipt.parents:
        raise ValueError('Use a fresh receipt outside all three managed trees')
    if not re.fullmatch(r'G[1-6](?:-[a-zA-Z0-9_-]+)?', round_id):
        raise ValueError('Round must be G1–G6 with an optional revision suffix')
    prior = verify(project) if (project / MARKER).exists() else None
    if project.exists() and not prior:
        raise ValueError('Refusing to reuse an unmarked directory')
    if prior and Path(prior['store']) != store:
        raise ValueError('Snapshot content store cannot change')
    if not (source / 'project.godot').is_file():
        raise ValueError('Missing project.godot')
    imported = imports(source)
    canonical = inventory(source)
    desired = dict(canonical)
    overlay_files = {}
    for name, original in (overlays or {}).items():
        if not name.startswith('tools/visual-rounds/') or '..' in Path(name).parts or Path(name).suffix != '.json':
            raise ValueError('Only explicit visual-rounds JSON harness overlays are admitted')
        original = Path(original).resolve()
        if not original.is_file() or project in original.parents or store in original.parents:
            raise ValueError('Overlay input must exist outside snapshot/store')
        overlay_files[name] = original
        desired[name] = metadata(original)
    old = prior['files'] if prior else {}
    changed = sorted(name for name in desired.keys() | old.keys() if desired.get(name) != old.get(name))
    record = {'schema': 1, 'round': round_id, 'source': str(source), 'project': str(project),
              'store': str(store), 'previous_receipt_sha256': digest(project / MARKER) if prior else None,
              'files': desired, 'canonical_files': canonical,
              'harness_overlays': {name: {'path': str(path), **desired[name]} for name, path in overlay_files.items()},
              'validated_imports': imported, 'changed_paths': changed,
              'source_bytes': sum(v['bytes'] for k, v in desired.items() if not k.startswith('.godot/')),
              'compiled_bytes': sum(v['bytes'] for k, v in desired.items() if k.startswith('.godot/imported/')),
              'preserved_old_sources': {}, 'scope': 'Exact source/cache snapshot; MD5 validates raw import inputs, not art quality. Never import into this project or mutate its read-only shared compiled cache.'}
    if dry_run:
        record.update(passed=True, dry_run=True, writes=False)
        return record
    for name in changed:
        if name in old and not name.startswith('.godot/imported/'):
            blob = store / 'sources' / old[name]['sha256']
            retain(project / name, blob, old[name])
            record['preserved_old_sources'][name] = str(blob)
    project.mkdir(parents=True, exist_ok=True)
    for name in changed:
        target = project / name
        if name not in desired:
            target.unlink()
        elif name.startswith('.godot/imported/'):
            blob = store / 'imports' / desired[name]['sha256']
            retain(source / name, blob, desired[name])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.unlink(missing_ok=True)
            os.link(blob, target)  # Store and snapshot must share a filesystem.
        else:
            atomic_copy(overlay_files.get(name, source / name), target)
    if inventory(source) != canonical or inventory(project) != desired or any(metadata(path) != desired[name] for name, path in overlay_files.items()):
        raise ValueError('Source/cache changed during refresh; preserve failed snapshot, do not capture')
    record.update(passed=True, dry_run=False, writes=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(record, indent=2) + '\n')
    atomic_copy(receipt, project / MARKER)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    update = sub.add_parser('refresh')
    for key in ('source', 'project', 'store', 'receipt'):
        update.add_argument('--' + key, type=Path, required=True)
    update.add_argument('--round', required=True)
    update.add_argument('--dry-run', action='store_true')
    update.add_argument('--harness-overlay', action='append', default=[], metavar='DEST=FILE',
                        help='Explicit visual-rounds JSON contract overlay; never a runtime script')
    check = sub.add_parser('verify')
    check.add_argument('--project', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'verify':
        record = verify(args.project.resolve())
    else:
        overlays = dict(item.split('=', 1) for item in args.harness_overlay)
        record = refresh(args.source, args.project, args.store, args.round, args.receipt, args.dry_run, overlays)
    print(json.dumps({'passed': True, 'round': record['round'], 'files': len(record['files']),
                      'validated_imports': len(record['validated_imports']),
                      'changed_paths': record['changed_paths'], 'source_bytes': record['source_bytes'],
                      'compiled_bytes': record['compiled_bytes'], 'dry_run': record.get('dry_run', False)}, indent=2))


if __name__ == '__main__':
    main()
