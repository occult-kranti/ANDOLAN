#!/usr/bin/env python3
"""Read-only source-clone audit; writes reports only beside this script.

No removal, restoration, Git update, engine, import, or export operations exist here.
"""
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

ROOT = Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN')
OUT = Path(__file__).resolve().parent
COMMIT = '5542e61610d20e591effbed9dec15fd10398e31d'
PREFIXES = ('games/yuga-native/docs/evidence/', 'games/yuga-native/art/')
MIN_BYTES = 262144
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS='0')


def git(*args, check=True):
    return subprocess.run(['git', '--no-optional-locks', '-C', str(ROOT), *args],
                          env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=check)


def save(name, value):
    p = OUT / name
    assert not p.exists(), f'refusing to overwrite {p}'
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    return hashlib.sha256(p.read_bytes()).hexdigest()


def metadata(p):
    s = p.lstat()
    return dict(size=s.st_size, allocated_bytes=s.st_blocks * 512, mode=oct(stat.S_IMODE(s.st_mode)),
                device=s.st_dev, inode=s.st_ino, hardlinks=s.st_nlink, mtime_ns=s.st_mtime_ns,
                ctime_ns=s.st_ctime_ns, regular=stat.S_ISREG(s.st_mode), symlink=stat.S_ISLNK(s.st_mode))


def ancestors_safe(p):
    return ROOT.resolve() == ROOT and all(not x.is_symlink() for x in [ROOT, *p.parents][:-1])


def hashed(p, before):
    blob = hashlib.sha1(b'blob ' + str(before['size']).encode() + b'\0')
    sha = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            blob.update(block)
            sha.update(block)
    return blob.hexdigest(), sha.hexdigest(), metadata(p) == before


def process_references():
    references, inaccessible = [], []
    for item in Path('/proc').iterdir():
        if not item.name.isdigit():
            continue
        pid = int(item.name)
        try:
            comm = (item / 'comm').read_text().strip()
            candidates = [('cwd', item / 'cwd'), ('exe', item / 'exe')]
            candidates += [('fd', p) for p in (item / 'fd').iterdir()]
            for kind, p in candidates:
                try:
                    target = os.readlink(p)
                    if target == str(ROOT) or target.startswith(str(ROOT) + '/'):
                        references.append(dict(pid=pid, comm=comm, kind=kind, target=target))
                except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
                    pass
            for line in (item / 'maps').read_text().splitlines():
                parts = line.split(maxsplit=5)
                if len(parts) == 6 and parts[5].startswith(str(ROOT) + '/'):
                    references.append(dict(pid=pid, comm=comm, kind='map', target=parts[5]))
        except (PermissionError, FileNotFoundError, ProcessLookupError, OSError) as error:
            inaccessible.append(dict(pid=pid, reason=type(error).__name__))
    # Process snapshots cannot prove the absence of queued or future dependencies.
    return dict(references=references, inaccessible=inaccessible, scope='one observation; ownership release remains mandatory')


def main():
    started = time.monotonic()
    before_head = git('rev-parse', 'HEAD').stdout.decode().strip()
    symbolic = git('symbolic-ref', '-q', 'HEAD', check=False)
    assert before_head == COMMIT and symbolic.returncode == 1
    remote = git('ls-remote', '--exit-code', 'origin', 'refs/heads/game/yuga-native-production').stdout.decode().strip()
    assert remote == COMMIT + '\trefs/heads/game/yuga-native-production', remote
    status_before = git('status', '--porcelain=v1', '-z', '--untracked-files=no').stdout
    tree = git('ls-tree', '-r', '-l', '-z', COMMIT).stdout
    tracked, selected, failures = [], [], []
    categories = collections.defaultdict(lambda: dict(files=0, logical_bytes=0, allocated_bytes=0))
    for record in tree.split(b'\0'):
        if not record:
            continue
        meta, raw_path = record.split(b'\t', 1)
        mode, kind, expected_blob, expected_size = meta.decode().split()
        rel = os.fsdecode(raw_path)
        p = ROOT / rel
        item = dict(path=rel, git_mode=mode, git_blob=expected_blob, commit=COMMIT)
        try:
            before = metadata(p)
            assert kind == 'blob' and before['regular'] and not before['symlink'] and ancestors_safe(p)
            blob, sha, stable = hashed(p, before)
            match = blob == expected_blob and before['size'] == int(expected_size) and stable
            item.update(before, sha256=sha, observed_git_blob=blob, stable_during_read=stable,
                        bytes_match_commit=match,
                        executable_mode_matches=(bool(int(mode, 8) & 0o111) == bool(int(before['mode'], 8) & 0o111)))
            if not match or not item['executable_mode_matches']:
                failures.append(rel)
            category = 'native-evidence' if rel.startswith(PREFIXES[0]) else 'native-art' if rel.startswith(PREFIXES[1]) else 'retained-tracked'
            item['category'] = category
            item['recommended_selected'] = bool(match and item['executable_mode_matches'] and category != 'retained-tracked'
                                                and before['size'] >= MIN_BYTES and before['hardlinks'] == 1)
            if item['recommended_selected']:
                selected.append(dict(item, recovery=dict(repository='occult-kranti/ANDOLAN', commit=COMMIT,
                                                        git_blob=expected_blob, relative_path=rel,
                                                        action='git cat-file blob into this exact path, restore recorded mode, verify SHA256')))
            c = categories[category]
            c['files'] += 1
            c['logical_bytes'] += before['size']
            c['allocated_bytes'] += before['allocated_bytes']
        except (OSError, AssertionError, ValueError) as error:
            item['error'] = type(error).__name__ + ': ' + str(error)
            failures.append(rel)
        tracked.append(item)

    untracked = []
    for raw in git('ls-files', '--others', '-z').stdout.split(b'\0'):
        if raw:
            rel = os.fsdecode(raw)
            untracked.append(dict(path=rel, **metadata(ROOT / rel), disposition='retain; not a deletion candidate'))
    after_head = git('rev-parse', 'HEAD').stdout.decode().strip()
    status_after = git('status', '--porcelain=v1', '-z', '--untracked-files=no').stdout
    assert before_head == after_head == COMMIT
    assert status_before == status_after == b''
    summary = dict(schema=1, observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   mode='READ_ONLY_PLAN_NO_DELETION', clone=str(ROOT), detached_head=after_head,
                   remote_branch_observation=remote, tracked_status_before_after='clean',
                   selection=dict(prefixes=list(PREFIXES), minimum_bytes=MIN_BYTES, regular_files_only=True,
                                  no_symlink_ancestors=True, require_single_hardlink=True),
                   tracked_files=len(tracked), tracked_failures=failures, category_totals=dict(categories),
                   proposed_files=len(selected), proposed_logical_bytes=sum(x['size'] for x in selected),
                   proposed_allocated_file_bytes=sum(x['allocated_bytes'] for x in selected),
                   untracked_including_ignored_files=len(untracked),
                   untracked_including_ignored_logical_bytes=sum(x['size'] for x in untracked),
                   elapsed_seconds=time.monotonic() - started,
                   execution_gates=['exact package disposition/qualification settled',
                                    'W1 warm+cold and source audit complete with explicit release',
                                    'W6 scoped ownership release', 'root approval of exact reviewed map',
                                    'map committed and remote-verified before deletion',
                                    'fresh per-path hash/mode/inode/link/ancestor/open-reference checks'])
    manifest = {}
    manifest['tracked-audit.json'] = save('tracked-audit.json', tracked)
    manifest['recovery-map.json'] = save('recovery-map.json', dict(schema=1, clone=str(ROOT), commit=COMMIT,
                                      status='PROPOSED_NOT_AUTHORIZED_FOR_EXECUTION', files=selected))
    manifest['retained-untracked.json'] = save('retained-untracked.json', untracked)
    manifest['process-observation.json'] = save('process-observation.json', process_references())
    manifest['summary.json'] = save('summary.json', summary)
    manifest['audit.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    save('artifact-hashes.json', manifest)
    print(json.dumps(summary, indent=2))
    assert not failures


if __name__ == '__main__':
    main()
