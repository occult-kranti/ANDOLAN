#!/usr/bin/env python3
"""Prepare one complete, isolated export artifact; default is a read-only plan.

Requires an exact pushed source freeze. It never exports, deletes, imports or
registers another managed project. Keep canonical linked inputs frozen until the
after-audit. All mutable native inputs and the cache are private copies.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import time

SOURCE = Path('/workspace/ANDOLAN')
NATIVE = Path('games/yuga-native')
AREA = Path('/workspace/scratch/yuga-continuation-W6-r1')
APPROVED_EXCLUDE = Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN/.git/info/exclude')
APPROVED_EXCLUDE_SHA256 = 'cbb147e36af3300e84b8a13a3855bf17ff53078d9adc4d3f458b6f673bc18ae8'
RAW_INPUT_SUFFIXES = {'.glb', '.png', '.webp', '.jpg', '.jpeg', '.wav', '.ogg', '.ttf', '.woff', '.woff2'}
ACTIVE_DOCS = {'README.md', 'docs/START_HERE.md', 'docs/WORKSPACE_AND_CLEANUP.md',
              'games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md',
              'games/yuga-native/docs/DESKTOP_FINISH_CAMPAIGN.md',
              'games/yuga-native/docs/DESKTOP_FINISH_CAMPAIGN.json',
              'games/yuga-native/docs/BUILD_HANDBOOK.md'}
# r4 observed upper sizes plus a separate 32MiB growth allowance. Recheck at
# final source freeze; this is capacity reservation, never an acceptance claim.
OUTPUT_BUDGET = 141_200_000 + 401_000_000 + 245_000_000 + 32 * 1024**2
METADATA_BUDGET = 20_000_000


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def regular(path):
    if path.resolve() != path.absolute() or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError('Nonregular or symlink input: ' + str(path))


def hashes(path):
    regular(path)
    size = path.stat().st_size
    blob = hashlib.sha1(('blob %d\0' % size).encode())
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            blob.update(block)
            sha.update(block)
    return size, blob.hexdigest(), sha.hexdigest()


def private(path):
    if path.suffix in {'.uid', '.import'} or path.name in {'.gitignore', '.gitattributes'}:
        return True
    if path.as_posix() in ACTIVE_DOCS:
        return True
    native = path.parts[:2] == NATIVE.parts
    if native and len(path.parts) > 2:
        if path.parts[2] in {'scripts', 'shaders', 'scenes', 'assets', 'NOTICE', 'tools', 'tests'}:
            return path.suffix.lower() not in RAW_INPUT_SUFFIXES
        if len(path.parts) == 3:
            return True
    return False


def tracked(root, commit):
    records = []
    for row in git(root, 'ls-tree', '-r', '-l', '-z', commit).split(b'\0'):
        if not row:
            continue
        metadata, raw_name = row.split(b'\t', 1)
        mode, kind, oid, length = metadata.decode().split()
        name = raw_name.decode('utf-8')
        path = Path(name)
        if mode not in {'100644', '100755'} or kind != 'blob' or path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsupported tracked entry: ' + name)
        source = root / path
        size, actual_oid, sha = hashes(source)
        actual_mode = '100755' if source.stat().st_mode & 0o111 else '100644'
        if (size, actual_oid, actual_mode) != (int(length), oid, mode):
            raise ValueError('Worktree does not match committed blob/mode: ' + name)
        records.append({'path': name, 'blob': oid, 'bytes': size, 'sha256': sha,
                        'mode': mode, 'private': private(path)})
    return records


def cache_records(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Expected a private-copyable cache directory')
    records = []
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('Cache symlink: ' + str(path))
        if path.is_file():
            size, _, sha = hashes(path)
            records.append({'path': path.relative_to(root).as_posix(), 'bytes': size, 'sha256': sha,
                            'mode': stat.S_IMODE(path.stat().st_mode)})
    return records


def round_allocation(size):
    return ((size + 4095) // 4096) * 4096


def free_bytes(path):
    s = os.statvfs(path)
    return s.f_bavail * s.f_frsize


def audit(root, records):
    for row in records:
        path = root / row['path']
        size, oid, sha = hashes(path)
        mode = '100755' if path.stat().st_mode & 0o111 else '100644'
        if (size, oid, sha, mode) != (row['bytes'], row['blob'], row['sha256'], row['mode']):
            raise ValueError('Tracked source changed: ' + str(path))


def audit_index(root, records):
    expected = {row['path']: (row['mode'], row['blob'], '0') for row in records}
    actual = {}
    for row in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if row:
            meta, name = row.split(b'\t', 1)
            name = name.decode('utf-8')
            if name in actual:
                raise ValueError('Duplicate or unmerged index entry: ' + name)
            actual[name] = tuple(meta.decode().split())
    if actual != expected:
        raise ValueError('Complete tracked index differs from declared source')
    flags = git(root, 'ls-files', '-v', '-z').split(b'\0')
    if any(row and row[:1] != b'H' for row in flags):
        raise ValueError('Sparse, skipped or assumed-unchanged index entries are forbidden')


def audit_isolation(source_root, artifact_root, records):
    for row in records:
        source, target = source_root / row['path'], artifact_root / row['path']
        shared = (source.stat().st_dev, source.stat().st_ino) == (target.stat().st_dev, target.stat().st_ino)
        if shared == row['private']:
            raise ValueError('Private-copy/hardlink policy differs: ' + row['path'])


def dump_new(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--artifact-name', default='package-successor-r1')
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--reserve-mib', type=int, default=500)
    parser.add_argument('--materialize', action='store_true')
    args = parser.parse_args()
    if len(args.commit) != 40 or any(c not in '0123456789abcdef' for c in args.commit):
        raise ValueError('An exact full source commit is required')
    if not args.artifact_name.startswith('package-successor-') or '/' in args.artifact_name or '..' in args.artifact_name:
        raise ValueError('Use a fresh artifact-only successor name')
    if args.reserve_mib < 128:
        raise ValueError('Reserve cannot be below the agreed 128MiB floor')
    if args.report.resolve().parent != AREA or args.report.exists():
        raise ValueError('Report must be a fresh direct child of the W6 scratch area')
    if git(SOURCE, 'rev-parse', 'HEAD').decode().strip() != args.commit:
        raise ValueError('Canonical HEAD is not the declared final source freeze')
    branch = git(SOURCE, 'symbolic-ref', '--short', 'HEAD').decode().strip()
    remote = git(SOURCE, 'ls-remote', '--exit-code', 'origin', 'refs/heads/' + branch).decode().split()
    if remote != [args.commit, 'refs/heads/' + branch]:
        raise ValueError('The exact source freeze is not the current remote branch')
    if git(SOURCE, 'diff', '--name-only', args.commit, '--'):
        raise ValueError('Tracked canonical files differ from source freeze')
    output = AREA / args.artifact_name
    if output.exists():
        raise ValueError('Refuse to overwrite any prior artifact or failure')
    entries = tracked(SOURCE, args.commit)
    audit_index(SOURCE, entries)
    runtime_paths = [str(NATIVE / d) for d in ('scripts', 'shaders', 'scenes', 'assets')]
    if git(SOURCE, 'ls-files', '--others', '--exclude-standard', '-z', '--', *runtime_paths):
        raise ValueError('Untracked native runtime inputs must be resolved before source freeze')
    cache_root = SOURCE / NATIVE / '.godot'
    cache = cache_records(cache_root)
    exclude = APPROVED_EXCLUDE.read_bytes()
    if hashlib.sha256(exclude).hexdigest() != APPROVED_EXCLUDE_SHA256:
        raise ValueError('Previously approved exact non-runtime UID exclusions changed')
    for line in exclude.decode().splitlines():
        if line and not line.startswith('#'):
            if (not line.startswith(('/games/yuga-native/tests/', '/games/yuga-native/tools/'))
                    or not line.endswith('.gd.uid') or any(c in line for c in '*?[]!') or '..' in Path(line).parts):
                raise ValueError('Only exact previously approved non-runtime UID exclusions are allowed')
    reserve = args.reserve_mib * 1024**2
    private_bytes = sum(round_allocation(r['bytes']) for r in entries if r['private'])
    cache_bytes = sum(round_allocation(r['bytes']) for r in cache)
    required = private_bytes + cache_bytes + METADATA_BUDGET + OUTPUT_BUDGET + reserve
    observed_free = free_bytes(AREA)
    report = {'schema': 1, 'source_commit': args.commit, 'source_repository': str(SOURCE),
              'classification': 'isolated export artifact; not a managed project',
              'artifact_root': str(output), 'repository': str(output / 'ANDOLAN'),
              'entries': entries, 'cache_seed': {'path': str(cache_root), 'files': cache},
              'exclude_source': str(APPROVED_EXCLUDE), 'exclude_sha256': hashlib.sha256(exclude).hexdigest(),
              'exclude_text': exclude.decode(), 'reserve_bytes': reserve,
              'capacity': {'free_bytes': observed_free, 'required_peak_bytes': required,
                           'private_input_bytes': private_bytes, 'private_cache_bytes': cache_bytes,
                           'output_budget_bytes': OUTPUT_BUDGET, 'metadata_budget_bytes': METADATA_BUDGET,
                           'shortfall_bytes': max(0, required - observed_free)},
              'created_unix': time.time(), 'materialized': False}
    if not args.materialize:
        dump_new(args.report, report)
        print(json.dumps({'plan': str(args.report), 'files': len(entries), 'capacity': report['capacity']}))
        return
    if observed_free < required:
        raise ValueError('Insufficient space: shortfall %d bytes' % (required - observed_free))
    output.mkdir()
    try:
        repo = output / 'ANDOLAN'
        subprocess.run(['git', 'clone', '--shared', '--no-checkout', str(SOURCE), str(repo)], check=True,
                       stdout=(output / 'clone.stdout').open('x'), stderr=(output / 'clone.stderr').open('x'))
        git(repo, 'update-ref', '--no-deref', 'HEAD', args.commit)
        git(repo, 'read-tree', args.commit)
        for row in entries:
            source, target = SOURCE / row['path'], repo / row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            # Recheck immediately before link/copy. Never chmod a linked inode.
            audit(SOURCE, [row])
            if row['private']:
                shutil.copy2(source, target)
            else:
                os.link(source, target, follow_symlinks=False)
        (repo / '.git/info/exclude').write_bytes(exclude)
        shutil.copytree(cache_root, repo / NATIVE / '.godot', copy_function=shutil.copy2)
        if cache_records(cache_root) != cache or cache_records(repo / NATIVE / '.godot') != cache:
            raise ValueError('Private cache seed changed while copying')
        for row in cache:
            a, b = cache_root / row['path'], repo / NATIVE / '.godot' / row['path']
            if (a.stat().st_dev, a.stat().st_ino) == (b.stat().st_dev, b.stat().st_ino):
                raise ValueError('Cache must not share mutable inodes')
        audit(SOURCE, entries)
        audit(repo, entries)
        audit_index(SOURCE, entries)
        audit_index(repo, entries)
        audit_isolation(SOURCE, repo, entries)
        if git(repo, 'status', '--porcelain', '--untracked-files=all'):
            raise ValueError('Artifact checkout is not fully clean')
        if free_bytes(AREA) < OUTPUT_BUDGET + reserve:
            raise ValueError('Insufficient remaining output capacity after materialization')
        report['materialized'] = True
        report['free_bytes_after'] = free_bytes(AREA)
    except Exception as error:
        report['failure'] = repr(error)
        dump_new(args.report, report)
        raise
    dump_new(args.report, report)
    print(json.dumps({'materialized': True, 'report': str(args.report), 'repository': report['repository']}))


if __name__ == '__main__':
    main()
