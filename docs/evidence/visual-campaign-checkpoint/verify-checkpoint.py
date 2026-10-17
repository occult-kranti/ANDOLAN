#!/usr/bin/env python3
"""Read-only SHA-256 verification of final visual evidence against a committed Git tree.

Reads the manifests themselves from COMMIT, then hashes the actual Git blob bytes.
No engine, checkout, index, working source or repository documentation is changed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

PROJECT = 'games/yuga-native/'
VERIFY_MANIFEST = PROJECT + 'docs/evidence/visual-campaign/final-verification-r4/visual/source-before.json'
FILM_SUFFIX = '/runtime-vs-snapshot.json'


def pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError('Duplicate JSON key: ' + key)
        value[key] = item
    return value


def reject_constant(value):
    raise ValueError('Nonfinite JSON number: ' + value)


def strict_json(raw):
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject_constant)


class GitTree:
    def __init__(self, repo: Path, commit: str):
        self.command = ['git', '--no-optional-locks', '-C', str(repo)]
        self.env = os.environ.copy()
        self.env['GIT_NO_REPLACE_OBJECTS'] = '1'
        kind = self.run(['cat-file', '-t', commit]).strip()
        if kind != b'commit':
            raise ValueError('Requested object is not a commit')
        self.entries = {}
        for record in self.run(['ls-tree', '-r', '-z', commit]).split(b'\0'):
            if not record:
                continue
            metadata, raw_path = record.split(b'\t', 1)
            mode, kind, oid = metadata.decode('ascii').split(' ')
            self.entries[raw_path.decode('utf-8')] = {'mode': mode, 'kind': kind, 'oid': oid}
        self.batch = subprocess.Popen(self.command + ['cat-file', '--batch'], env=self.env,
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.cache = {}

    def run(self, arguments):
        return subprocess.run(self.command + arguments, env=self.env, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def blob(self, path, retain=False):
        if not retain and path in self.cache:
            return self.cache[path]
        entry = self.entries.get(path)
        if entry is None:
            raise FileNotFoundError(path)
        if entry['kind'] != 'blob' or entry['mode'] not in ('100644', '100755'):
            raise ValueError('Expected regular Git blob: ' + path)
        self.batch.stdin.write((entry['oid'] + '\n').encode('ascii'))
        self.batch.stdin.flush()
        header = self.batch.stdout.readline().decode('ascii').strip().split(' ')
        if len(header) != 3 or header[1] != 'blob' or header[0] != entry['oid']:
            raise ValueError('Invalid git cat-file response for ' + path)
        size = int(header[2])
        if retain and size > 16 * 1024 * 1024:
            raise ValueError('Manifest exceeds 16 MiB: ' + path)
        digest = hashlib.sha256()
        remaining = size
        payload = bytearray() if retain else None
        while remaining:
            chunk = self.batch.stdout.read(min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError('Truncated Git blob: ' + path)
            digest.update(chunk)
            if retain:
                payload.extend(chunk)
            remaining -= len(chunk)
        if self.batch.stdout.read(1) != b'\n':
            raise ValueError('Invalid Git blob terminator: ' + path)
        result = {'sha256': digest.hexdigest(), 'bytes': size, 'git_blob': entry['oid']}
        self.cache[path] = result
        return (result, bytes(payload)) if retain else result

    def manifest(self, path):
        identity, payload = self.blob(path, retain=True)
        return strict_json(payload), identity

    def close(self):
        self.batch.stdin.close()
        self.batch.stdout.close()
        self.batch.wait(timeout=10)
        self.batch.stderr.close()
        if self.batch.returncode != 0:
            raise ValueError('git cat-file exited nonzero')


def valid_path(path):
    p = PurePosixPath(path)
    return isinstance(path, str) and not p.is_absolute() and '..' not in p.parts and '\n' not in path and '\r' not in path


def check_records(tree, records):
    mismatches = []
    matched = 0
    expected_bytes = 0
    matched_bytes = 0
    for path, expected in sorted(records.items()):
        if not valid_path(path) or not isinstance(expected, dict):
            raise ValueError('Invalid manifest record path: ' + str(path))
        digest, size = expected.get('sha256'), expected.get('bytes')
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest) or type(size) is not int or size < 0:
            raise ValueError('Invalid expected identity: ' + path)
        expected_bytes += size
        try:
            actual = tree.blob(path)
        except (FileNotFoundError, ValueError) as error:
            mismatches.append({'path': path, 'reason': str(error), 'expected': expected, 'actual': None})
            continue
        if actual['sha256'] != digest or actual['bytes'] != size:
            mismatches.append({'path': path, 'reason': 'Git blob identity mismatch', 'expected': expected, 'actual': actual})
        else:
            matched += 1
            matched_bytes += size
    return {'passed': not mismatches, 'expected_files': len(records), 'matched_files': matched,
            'expected_bytes': expected_bytes, 'matched_bytes': matched_bytes, 'mismatches': mismatches}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True, help='Full 40-character commit SHA')
    parser.add_argument('--repo', type=Path, default=Path('/workspace/ANDOLAN'))
    parser.add_argument('--film-manifest', help='Explicit repository-relative final film runtime-vs-snapshot.json path')
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-fA-F]{40}', args.commit):
        parser.error('--commit must be a full 40-character hexadecimal commit SHA')
    tree = None
    output = {'schema': 1, 'commit': args.commit.lower(), 'passed': False,
              'scope': 'Hashes committed Git blob bytes against evidence manifests read from that same commit; no engine rerun or working-file acceptance.'}
    try:
        tree = GitTree(args.repo, args.commit)
        manifest, identity = tree.manifest(VERIFY_MANIFEST)
        if not isinstance(manifest, dict):
            raise ValueError('Verification manifest is not an object')
        relative = {path: row for path, row in manifest.items()
                    if path.startswith(('scripts/', 'shaders/', 'scenes/', 'assets/'))
                    or path in ('project.godot', 'export_presets.cfg')}
        if len(relative) != 506:
            raise ValueError('Expected exactly 506 R4 runtime records; got ' + str(len(relative)))
        verify_paths = {PROJECT + path for path in relative}
        git_runtime_paths = {path for path in tree.entries if path.startswith(tuple(PROJECT + folder for folder in ('scripts/', 'shaders/', 'scenes/', 'assets/'))) or path in (PROJECT + 'project.godot', PROJECT + 'export_presets.cfg')}
        result = check_records(tree, {PROJECT + path: row for path, row in relative.items()})
        result['extra_git_runtime_paths'] = sorted(git_runtime_paths - verify_paths)
        result['missing_git_runtime_paths'] = sorted(verify_paths - git_runtime_paths)
        result['passed'] = result['passed'] and not result['extra_git_runtime_paths'] and not result['missing_git_runtime_paths']
        result.update(manifest_path=VERIFY_MANIFEST, manifest_git_identity=identity)
        output['verification_runtime'] = result
        candidates = sorted(path for path in tree.entries if '/docs/evidence/visual-campaign/capture-action-' in path and path.endswith(FILM_SUFFIX))
        if args.film_manifest:
            if not valid_path(args.film_manifest):
                raise ValueError('Invalid explicit film manifest path')
            film_path = args.film_manifest
        elif len(candidates) == 1:
            film_path = candidates[0]
        elif len(candidates) > 1:
            raise ValueError('Multiple film manifests; pass --film-manifest explicitly: ' + ', '.join(candidates))
        else:
            film_path = None
        if film_path is None:
            local = sorted(str(path.relative_to(args.repo)) for path in (args.repo / PROJECT / 'docs/evidence/visual-campaign').glob('capture-action-*/runtime-vs-snapshot.json'))
            output['film_runtime'] = {'available': False, 'passed': not local,
                'reason': 'Film archive absent from commit' if not local else 'Film archive exists locally but its manifest is missing from the requested Git tree',
                'local_manifests_not_accepted_as_evidence': local}
        else:
            film, film_identity = tree.manifest(film_path)
            if film.get('complete') is not True or film.get('canonical_runtime_unchanged') is not True or film.get('extra_canonical_files'):
                raise ValueError('Film manifest is incomplete or records changed runtime')
            files = film.get('files')
            if not isinstance(files, list) or len(files) != 506:
                raise ValueError('Expected exactly 506 complete film runtime records')
            report_path = str(PurePosixPath(film_path).parent / 'rama-gameplay-review.json')
            film_report, report_identity = tree.manifest(report_path)
            if report_identity['sha256'] != film['report_sha256'] or film_report.get('complete') is not True or film_report.get('source_unchanged') is not True:
                raise ValueError('Committed film report is mismatched or incomplete')
            records = {}
            for row in files:
                path = row['repository_path']
                if path in records or not path.startswith(PROJECT):
                    raise ValueError('Duplicate or out-of-project film path: ' + path)
                if row.get('resource') != 'res://' + path.removeprefix(PROJECT) or film_report['source_sha256'].get(row['resource']) != row['snapshot_sha256']:
                    raise ValueError('Film runtime row differs from actual capture source pin: ' + path)
                records[path] = {'sha256': row['snapshot_sha256'], 'bytes': row['bytes']}
            film_result = check_records(tree, records)
            film_result.update(available=True, manifest_path=film_path, manifest_git_identity=film_identity, capture_report_git_identity=report_identity)
            film_expected_tree = (git_runtime_paths - {PROJECT + 'export_presets.cfg'}) | {PROJECT + 'art/world/confluence-map.json'}
            film_result['extra_git_runtime_paths'] = sorted(film_expected_tree - set(records))
            film_result['missing_git_runtime_paths'] = sorted(set(records) - film_expected_tree)
            helper_records = {}
            for helper in film.get('invoked_helpers', []):
                archived_path = str(PurePosixPath(film_path).parent / helper['archive_path'])
                archived_identity = tree.blob(archived_path)
                if archived_identity['sha256'] != helper['snapshot_sha256']:
                    raise ValueError('Committed film helper archive mismatch: ' + archived_path)
                helper_records[helper['repository_path']] = {'sha256': helper['snapshot_sha256'], 'bytes': archived_identity['bytes']}
            if len(helper_records) != 3:
                raise ValueError('Expected three unique pinned film producers')
            film_result['invoked_helpers'] = check_records(tree, helper_records)
            # Runtime may differ by purpose: tests pin export_presets.cfg while
            # the actual film also pins art/world/confluence-map.json. Compare
            # the exact shared source records, and report nonoverlap explicitly.
            verify_records = {PROJECT + path: row for path, row in relative.items()}
            common = sorted(set(records) & set(verify_records))
            conflicts = [path for path in common if records[path] != verify_records[path]]
            film_result['shared_runtime_records'] = len(common)
            film_result['cross_manifest_conflicts'] = conflicts
            film_result['film_only_paths'] = sorted(set(records) - set(verify_records))
            film_result['verification_only_paths'] = sorted(set(verify_records) - set(records))
            film_result['passed'] = film_result['passed'] and not conflicts and not film_result['extra_git_runtime_paths'] and not film_result['missing_git_runtime_paths'] and film_result['invoked_helpers']['passed']
            output['film_runtime'] = film_result
        output['passed'] = output['verification_runtime']['passed'] and output['film_runtime']['passed']
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        output['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        if tree is not None:
            try:
                tree.close()
            except Exception as error:
                output['passed'] = False
                output['git_close_error'] = str(error)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
