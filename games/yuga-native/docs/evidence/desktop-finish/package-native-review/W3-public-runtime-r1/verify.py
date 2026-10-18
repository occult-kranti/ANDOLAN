#!/usr/bin/env python3
"""Read source/build/license records; never execute or modify an engine."""
from pathlib import Path
import datetime
import difflib
import gzip
import hashlib
import json
import tarfile

PROJECT = Path('/workspace/ANDOLAN/games/yuga-native')
G0 = PROJECT / 'docs/evidence/desktop-finish/G0'
OUT = Path(__file__).resolve().parent
COMMIT = '35e80b3a8822a9df9be390814b62f44c0a9c69e8'
SOURCE = Path('/tmp/yuga-engine-template-baseline-r1') / ('godot-' + COMMIT)
ARCHIVE = Path('/workspace/tooling/godot-public-4.6.3/downloads/godot-35e80b3a.tar.gz')
BINARY = Path('/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-unmodified')


def pin(p):
    with p.open('rb') as f:
        sha = hashlib.file_digest(f, 'sha256').hexdigest()
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha}


def main():
    manifest_path = G0 / 'template-build-preparation-r1/pristine-source-files.json.gz'
    pristine = json.loads(gzip.decompress(manifest_path.read_bytes()))
    archive_mismatches, archived_names, archive_special = [], [], {}
    with tarfile.open(ARCHIVE, 'r:gz') as archive:
        for member in archive:
            if not member.isfile():
                continue
            root, name = member.name.split('/', 1)
            assert root == 'godot-' + COMMIT
            data = archive.extractfile(member).read()
            row = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            if row != pristine.get(name):
                archive_mismatches.append(name)
            archived_names.append(name)
            if name in ('LICENSE.txt', 'COPYRIGHT.txt', 'servers/rendering/renderer_rd/pipeline_hash_map_rd.h'):
                archive_special[name] = data
    assert len(archived_names) == len(set(archived_names)) == len(pristine) == 13847
    assert not archive_mismatches and set(archived_names) == set(pristine)
    current_changes = []
    for name, expected in pristine.items():
        p = SOURCE / name
        actual = pin(p) if p.is_file() else None
        if actual is None or any(actual[k] != expected[k] for k in ('bytes', 'sha256')):
            current_changes.append({'path': name, 'archived': expected, 'current': actual})
    notices = []
    for name, shipped in [('LICENSE.txt', 'GODOT-LICENSE.txt'), ('COPYRIGHT.txt', 'GODOT-COPYRIGHT.txt')]:
        a = archive_special[name]
        p = PROJECT / 'NOTICE' / shipped
        notices.append({'source_file': name, 'package_notice': pin(p),
                        'archive_sha256': hashlib.sha256(a).hexdigest(),
                        'exact_to_archive': a == p.read_bytes(),
                        'current_source_exact_to_archive': a == (SOURCE / name).read_bytes()})
    receipt_artifacts = []
    for folder in ('template-baseline-r1', 'template-build-preparation-r1'):
        receipt = G0 / folder / 'receipt.json'
        document = json.loads(receipt.read_text())
        checked = []
        for name, expected in document['artifacts'].items():
            actual = pin(receipt.parent / name)
            checked.append({'path': name, 'exact': all(actual[k] == expected[k] for k in ('bytes', 'sha256'))})
        receipt_artifacts.append({'receipt': pin(receipt), 'artifacts_checked': len(checked),
                                  'mismatches': [x['path'] for x in checked if not x['exact']]})
    build_path = G0 / 'template-baseline-r1/build-result.json'
    verification_path = G0 / 'template-baseline-r1/finished-build-verification.json'
    build = json.loads(build_path.read_text())
    verification = json.loads(verification_path.read_text())
    runtime = pin(BINARY)
    archive_pin = pin(ARCHIVE)
    report = {'schema': 1, 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Read-only source/archive/build-record/notice verification; no engine execution, rebuild, export or runtime qualification',
              'source_commit': COMMIT, 'source_archive': archive_pin, 'runtime': runtime,
              'pristine_manifest': pin(manifest_path), 'archive_source_files_checked': len(archived_names),
              'archive_manifest_mismatches': archive_mismatches, 'current_source_original_files_checked': len(pristine),
              'current_source_original_file_changes': current_changes,
              'current_source_tree_unmodified': not current_changes,
              'notices': notices, 'receipt_artifact_checks': receipt_artifacts,
              'build_record': pin(build_path), 'finished_verification': pin(verification_path),
              'build_command': build['command'], 'build_completed': build['completed'],
              'build_exit_code': build['exit_code'], 'historical_source_patches': build['source_patches'],
              'recorded_version': verification['version'],
              'binary_matches_finished_build': runtime['sha256'] == verification['binary_sha256'] and runtime['bytes'] == verification['binary_bytes'],
              'baseline_record_binding_exact': verification['build_result_sha256'] == pin(build_path)['sha256']}
    assert archive_pin['sha256'] == 'fe5b661d0e7b062201ebffc8740cb309ff96c4f1edca79cdb0ecda50ff2af8d5'
    assert runtime['sha256'] == 'dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f'
    assert report['binary_matches_finished_build'] and report['baseline_record_binding_exact']
    assert all(x['exact_to_archive'] for x in notices)
    assert all(not x['mismatches'] for x in receipt_artifacts)
    assert build['completed'] and build['exit_code'] == 0 and build['source_patches'] == 0
    for changed in current_changes:
        name = changed['path']
        if name in archive_special:
            diff = ''.join(difflib.unified_diff(archive_special[name].decode().splitlines(True),
                                              (SOURCE / name).read_text().splitlines(True),
                                              fromfile='pristine-archive/' + name, tofile='current-tree/' + name))
            (OUT / 'source-tree-difference.patch').write_text(diff)
    with (OUT / 'checks.json').open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'archive_sources_exact': len(archived_names), 'runtime_sha256': runtime['sha256'],
                      'notices_exact': all(x['exact_to_archive'] for x in notices),
                      'current_source_changes': [x['path'] for x in current_changes],
                      'receipt_artifacts_exact': sum(x['artifacts_checked'] for x in receipt_artifacts)}, indent=2))


if __name__ == '__main__':
    main()
