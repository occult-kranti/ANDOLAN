#!/usr/bin/env python3
"""Verify, or explicitly remove, only the accompanying 182 Git-backed copies."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

REPO = Path('/workspace/ANDOLAN')
HERE = Path(__file__).resolve().parent
ROOTS = tuple(Path('/workspace/scratch') / name for name in (
    'visual-campaign-shadow-confirm-project-r1',
    'visual-campaign-shadow-confirm-project-r2',
    'visual-campaign-shadow-confirm-project-r3',
    'visual-campaign-final-project-r4',
    'visual-campaign-shadow-bias-project-r1',
    'visual-campaign-shadow-bias-project-r2',
    'visual-campaign-candidate-project-r3',
))


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inspect_processes():
    refs, limits = [], []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            status = (process / 'status').read_text()
            state = next(line for line in status.splitlines() if line.startswith('State:'))
            if 'Z (zombie)' in state:
                continue
            name = next(line for line in status.splitlines() if line.startswith('Name:'))
            candidates = [process / 'cwd', process / 'exe']
            try:
                candidates.extend((process / 'fd').iterdir())
            except PermissionError:
                limits.append({'pid': process.name, 'name': name, 'scope': 'fd'})
            for path in candidates:
                try:
                    target = os.readlink(path)
                except OSError:
                    continue
                if any(target == str(root) or target.startswith(str(root) + '/') for root in ROOTS):
                    refs.append({'pid': process.name, 'reference': str(path), 'target': target})
            try:
                for line in (process / 'maps').read_text().splitlines():
                    if any(str(root) in line for root in ROOTS):
                        refs.append({'pid': process.name, 'reference': 'maps', 'target': line})
            except PermissionError:
                limits.append({'pid': process.name, 'name': name, 'scope': 'maps'})
        except (FileNotFoundError, ProcessLookupError):
            pass
    return refs, limits


def file_check(row):
    path = Path(row['path'])
    assert any(path.is_relative_to(root / 'assets') for root in ROOTS), path
    assert not any(parent.is_symlink() for parent in (path, *path.parents)), path
    value = path.lstat()
    assert stat.S_ISREG(value.st_mode), path
    assert value.st_size > 1024 * 1024, path
    actual = dict(bytes=value.st_size, allocated_bytes=value.st_blocks * 512,
                  device=value.st_dev, inode=value.st_ino, links=value.st_nlink,
                  mode=stat.S_IMODE(value.st_mode))
    assert all(actual[key] == row[key] for key in actual), (path, actual)
    assert value.st_nlink == 1, path
    assert sha(path.read_bytes()) == row['sha256'], path
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove', action='store_true', help='Root-authorized exact removal after remote map publication')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    assert not output.exists(), 'Use a fresh output path; preserve earlier receipts.'
    raw = (HERE / 'recovery-map.json').read_bytes()
    data = json.loads(raw)
    rows = data['files']
    assert len(rows) == len({row['path'] for row in rows}) == 182
    assert sum(row['allocated_bytes'] for row in rows) == 1034743808
    assert tuple(Path(root) for root in data['roots']) == ROOTS
    remote = git('ls-remote', 'origin', 'refs/heads/game/yuga-native-production').decode().split()[0]
    subprocess.run(['git', '-C', str(REPO), 'merge-base', '--is-ancestor', data['recovery_commit'], remote], check=True)
    if args.remove:
        for name in ('recovery-map.json', 'owner-releases.json', 'README.md', 'cleanup.py'):
            path = HERE / name
            assert git('show', f'{remote}:{path.relative_to(REPO)}') == path.read_bytes(), f'Unpublished/changed {name}'
    verified_blobs = set()
    for row in rows:
        file_check(row)
        record = git('ls-tree', data['recovery_commit'], '--', row['git_path']).decode().strip()
        assert record.split()[0:3] == [row['git_mode'], 'blob', row['blob']], row['path']
        if row['blob'] not in verified_blobs:
            original = git('cat-file', 'blob', row['blob'])
            assert len(original) == row['bytes'] and sha(original) == row['sha256'], row['path']
            verified_blobs.add(row['blob'])
    refs, limits = inspect_processes()
    assert not refs, refs
    # The container's inaccessible system daemons are disclosed; any other live
    # process that cannot be inspected blocks this bounded cleanup.
    assert all(row['name'].split(':', 1)[1].strip() in ('dockerd', 'containerd') for row in limits), limits
    before = os.statvfs('/workspace')
    result = {'schema': 1, 'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'operation': 'remove' if args.remove else 'verify_only', 'remote_head': remote,
              'recovery_commit': data['recovery_commit'], 'map_sha256': sha(raw),
              'verified_files': len(rows), 'unique_blobs': len(verified_blobs),
              'process_references': refs, 'process_inspection_limits': limits,
              'workspace_free_before': before.f_bavail * before.f_frsize,
              'removed': [], 'removed_allocated_bytes': 0}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    if args.remove:
        for row in rows:
            file_check(row)
            Path(row['path']).unlink()
            result['removed'].append(row)
            result['removed_allocated_bytes'] += row['allocated_bytes']
            output.write_text(json.dumps(result, indent=2) + '\n')
    after = os.statvfs('/workspace')
    result['workspace_free_after'] = after.f_bavail * after.f_frsize
    result['complete'] = True
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('operation', 'verified_files', 'removed_allocated_bytes', 'workspace_free_after', 'complete')}))


if __name__ == '__main__':
    main()
