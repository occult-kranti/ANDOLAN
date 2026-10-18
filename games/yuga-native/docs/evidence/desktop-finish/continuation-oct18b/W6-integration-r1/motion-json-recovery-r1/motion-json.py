#!/usr/bin/env python3
"""One exact released JSON; lossless gzip recovery required before unlink."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

REPO = Path('/workspace/ANDOLAN')
PACKET = Path(__file__).resolve().parent
TARGET = Path('/workspace/scratch/yuga-next-W1-r1/motion-candidate-actual-r1/capture.json')
RECOVERY = REPO / 'games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W1-actual-r1/motion-candidate-r1/capture.json.gz'
OWNER = RECOVERY.with_name('receipt.json')
REF = 'refs/heads/backup/yuga-desktop-motion-json-2026-10-18b'
RAW_SHA = '0488631d617417af6fad269410f49dd007ccf6b1e87a280bd7628c23df546ae2'
GZIP_SHA = '40f1c1ea5dac2374a59b0f7df19f5429752d520938a05121081bb1e2aa1b57f8'
OWNER_SHA = 'bc8d344e78b2b048c25f425da155adf158ed7f258efd51ed4b2de1bdb2528fee'
CHUNK = 1024 * 1024

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            h.update(block)
    return h.hexdigest()

def regular(path):
    require(path.is_absolute() and '..' not in path.parts, 'unsafe path')
    for p in [path, *path.parents]:
        require(not stat.S_ISLNK(p.lstat().st_mode), 'symlink component')
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode), 'not regular')
    require(s.st_nlink == 1, 'hardlink alias')
    return s

def identity(path):
    s = regular(path)
    return {'path': str(path), 'bytes': s.st_size, 'sha256': sha(path),
            'dev': s.st_dev, 'ino': s.st_ino, 'nlink': s.st_nlink,
            'mode': stat.S_IMODE(s.st_mode), 'mtime_ns': s.st_mtime_ns,
            'ctime_ns': s.st_ctime_ns, 'allocated_bytes': s.st_blocks * 512}

def validate_identity(actual, expected):
    require(actual == expected, 'file identity drift')

def roundtrip(raw, packed, size, expected_sha):
    count = 0
    h = hashlib.sha256()
    with raw.open('rb') as source, gzip.open(packed, 'rb') as decoded:
        while True:
            block = decoded.read(CHUNK)
            if not block:
                break
            count += len(block)
            require(count <= size, 'decoded size exceeded')
            require(source.read(len(block)) == block, 'decoded bytes differ')
            h.update(block)
        require(source.read(1) == b'', 'decoded data truncated')
    require(count == size and h.hexdigest() == expected_sha, 'decoded identity mismatch')
    return {'decoded_bytes': count, 'decoded_sha256': h.hexdigest(), 'byte_exact': True}

def process_refs(expected):
    hits, limits = [], 0
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            for fd in (proc / 'fd').iterdir():
                try:
                    s = fd.stat()
                    if (s.st_dev, s.st_ino) == (expected['dev'], expected['ino']):
                        hits.append(str(fd))
                except FileNotFoundError:
                    pass
                except PermissionError:
                    limits += 1
            maps = (proc / 'maps').read_text()
            if str(TARGET) in maps:
                hits.append(str(proc / 'maps'))
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            limits += 1
    require(not hits, 'active process reference')
    return {'matching_refs': hits, 'inaccessible_or_exited_process_entries': limits,
            'limit': 'Accessible process files/maps only; owner releases additionally required.'}

def audit(m):
    require(m['target']['path'] == str(TARGET), 'wrong target')
    require(m['recovery']['path'] == str(RECOVERY), 'wrong recovery')
    require(m['owner_receipt']['path'] == str(OWNER), 'wrong owner receipt')
    require(m['target']['sha256'] == RAW_SHA and m['target']['bytes'] == 16703321, 'wrong raw pin')
    require(m['recovery']['sha256'] == GZIP_SHA, 'wrong gzip pin')
    require(m['owner_receipt']['sha256'] == OWNER_SHA, 'wrong owner pin')
    for name, path in [('target', TARGET), ('recovery', RECOVERY), ('owner_receipt', OWNER)]:
        validate_identity(identity(path), m[name])
    require((m['target']['dev'], m['target']['ino']) != (m['recovery']['dev'], m['recovery']['ino']), 'recovery aliases target')
    release = PACKET / 'owner-release.json'
    regular(release)
    require(sha(release) == m['owner_release_sha256'], 'owner release drift')
    owners = json.loads(release.read_text())
    require(owners['target'] == str(TARGET) and owners['W1_released'] is True and owners['W6_released'] is True and owners['root_proposal_only'] is True, 'owner not released')
    owner = json.loads(OWNER.read_text())['gzip']
    require(owner['regular_raw_retained_path'] == str(TARGET) and owner['regular_sha256'] == RAW_SHA and owner['regular_bytes'] == 16703321 and owner['gzip_sha256'] == GZIP_SHA and owner['decoded_equals_original'] is True, 'owner recovery binding mismatch')
    recovery = roundtrip(TARGET, RECOVERY, m['target']['bytes'], RAW_SHA)
    # Recheck all three after streaming, including gzip trailer/CRC validation.
    for name, path in [('target', TARGET), ('recovery', RECOVERY), ('owner_receipt', OWNER)]:
        validate_identity(identity(path), m[name])
    return {'roundtrip': recovery, 'process': process_refs(m['target'])}

def remote_backup(m, commit, ref):
    require(ref == REF and re.fullmatch('[0-9a-f]{40}', commit), 'wrong backup identity')
    output = subprocess.check_output(['git', '--no-optional-locks', 'ls-remote', 'origin', ref], cwd=REPO, text=True)
    require(output.strip() == commit + '\t' + ref, 'remote backup mismatch')
    for relative in m['backup_required_paths']:
        path = REPO / relative
        regular(path)
        blob = subprocess.check_output(['git', '--no-optional-locks', 'show', commit + ':' + relative], cwd=REPO)
        require(hashlib.sha256(blob).hexdigest() == sha(path), 'backup bytes mismatch: ' + relative)
    return {'commit': commit, 'ref': ref, 'exact_backed_paths': m['backup_required_paths']}

def write_new(path, value):
    require(not path.exists() and not path.is_symlink(), 'receipt already exists')
    temp = path.with_name('.' + path.name + '.tmp-' + str(os.getpid()))
    with temp.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, sort_keys=True) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-sha256', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--remove', action='store_true')
    parser.add_argument('--backup-commit')
    parser.add_argument('--backup-ref')
    args = parser.parse_args()
    require(args.receipt.parent == PACKET and re.fullmatch(r'[a-z0-9-]+\.json', args.receipt.name), 'receipt outside owned packet')
    require(not args.receipt.exists() and not args.receipt.is_symlink(), 'receipt already exists')
    map_path = PACKET / 'recovery-map.json'
    regular(map_path)
    require(sha(map_path) == args.map_sha256, 'map hash mismatch')
    m = json.loads(map_path.read_text())
    before = os.statvfs('/workspace')
    checked = audit(m)
    backup = remote_backup(m, args.backup_commit, args.backup_ref) if args.remove else None
    result = {'utc_unix': time.time(), 'removed': False, 'map_sha256': args.map_sha256,
              'helper_sha256': sha(Path(__file__)), 'audit': checked, 'backup': backup,
              'free_before': before.f_bavail * before.f_frsize}
    if args.remove:
        # Refresh ownership, recovery and process checks after remote verification.
        result['fresh_audit'] = audit(m)
        parent_fd = os.open(TARGET.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            current = os.stat(TARGET.name, dir_fd=parent_fd, follow_symlinks=False)
            require(stat.S_ISREG(current.st_mode) and current.st_nlink == 1 and (current.st_dev, current.st_ino) == (m['target']['dev'], m['target']['ino']), 'final target drift')
            require((current.st_size, stat.S_IMODE(current.st_mode), current.st_mtime_ns, current.st_ctime_ns) == (m['target']['bytes'], m['target']['mode'], m['target']['mtime_ns'], m['target']['ctime_ns']), 'final metadata drift')
            os.unlink(TARGET.name, dir_fd=parent_fd)
        finally:
            os.close(parent_fd)
        result['removed'] = True
        result['removed_logical_bytes'] = m['target']['bytes']
        result['removed_allocated_bytes'] = m['target']['allocated_bytes']
        require(not TARGET.exists() and not TARGET.is_symlink(), 'target still exists')
    result['retained_rechecked'] = {str(p): identity(p) for p in [RECOVERY, OWNER]}
    for name, path in [('recovery', RECOVERY), ('owner_receipt', OWNER)]:
        validate_identity(result['retained_rechecked'][str(path)], m[name])
    after = os.statvfs('/workspace')
    result['free_after'] = after.f_bavail * after.f_frsize
    write_new(args.receipt, result)
    print(json.dumps({'removed': result['removed'], 'receipt': str(args.receipt), 'free_bytes': result['free_after']}))

if __name__ == '__main__':
    main()
