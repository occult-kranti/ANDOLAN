"""Read-only two-ZIP cleanup audit: hash local aliases and verify public identity."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import stat
import subprocess

OUT = Path(__file__).resolve().parent
BUILD = Path('/workspace/scratch/yuga-desktop-integrated-package-r4/build')
REPO = Path('/workspace/ANDOLAN')
AUDIT = REPO / 'games/yuga-native/docs/evidence/desktop-finish/published/W5-public-download-r4/download-verification.json'
EXPECTED = {
    'yuga-native-linux-x86_64.zip': (97835664, '27c36e5523643c647b245614721c0160b3d1548bf6da851d922886cffc180d0e', 653297487),
    'yuga-native-windows-x86_64.zip': (146132535, '34d8c19d30f7cafe6ad56247c2524d09c15f307cc0cde20572a56eb3d29b1fc6', 653297683),
}

def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()

def file_state(path):
    st = path.lstat()
    assert stat.S_ISREG(st.st_mode) and not path.is_symlink() and path.resolve() == path
    return {'bytes': st.st_size, 'mode': oct(stat.S_IMODE(st.st_mode)),
            'device': st.st_dev, 'inode': st.st_ino, 'nlink': st.st_nlink,
            'allocated_bytes': st.st_blocks * 512, 'mtime_ns': st.st_mtime_ns}

def holders(records):
    identities = {(x['filesystem']['device'], x['filesystem']['inode']): x['path'] for x in records}
    paths = {x['path'] for x in records}
    found, inaccessible_owned, inaccessible_other, exited, zombies = [], [], [], [], []
    for proc in sorted(Path('/proc').iterdir(), key=lambda p: p.name):
        if not proc.name.isdigit():
            continue
        try:
            uid = proc.stat().st_uid
            process_state = next(line.split()[1] for line in (proc / 'status').read_text().splitlines()
                                 if line.startswith('State:'))
            if process_state == 'Z':
                zombies.append(int(proc.name))
                continue
            inaccessible = []
            try:
                for fd in (proc / 'fd').iterdir():
                    try:
                        st = fd.stat()
                        identity = (st.st_dev, st.st_ino)
                        if identity in identities:
                            found.append({'pid': int(proc.name), 'uid': uid, 'kind': 'open_fd',
                                          'fd': fd.name, 'path': identities[identity]})
                    except FileNotFoundError:
                        continue
            except PermissionError:
                inaccessible.append('fd')
            try:
                for line in (proc / 'maps').read_text().splitlines():
                    fields = line.split(maxsplit=5)
                    if len(fields) == 6 and fields[5].removesuffix(' (deleted)') in paths:
                        found.append({'pid': int(proc.name), 'uid': uid, 'kind': 'mapped_file',
                                      'path': fields[5]})
            except PermissionError:
                inaccessible.append('maps')
            if inaccessible:
                (inaccessible_owned if uid == os.getuid() else inaccessible_other).append(
                    {'pid': int(proc.name), 'uid': uid, 'unreadable': inaccessible})
        except (FileNotFoundError, ProcessLookupError):
            exited.append(int(proc.name))
    return {'holders': found, 'inaccessible_owned_processes': inaccessible_owned,
            'inaccessible_other_uid_processes': inaccessible_other, 'exited_during_scan': exited,
            'zombies_without_live_file_descriptor_tables': zombies,
            'scope': 'Exact target inode FD and target pathname memory-map checks. No command lines, environments or credentials read. '
                     'Observation is point-in-time, not a future ownership guarantee.'}

def main():
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    command = ['gh', 'api', 'repos/occult-kranti/ANDOLAN/releases/tags/yuga-desktop-finish-2026-10-18',
               '--jq', '{id,tag_name,target_commitish,draft,prerelease,published_at,html_url,'
                       'assets:[.assets[]|{id,name,size,digest,state,browser_download_url,url,created_at,updated_at}]}']
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=30, check=True)
    (OUT / 'publication-api-current.json').write_text(result.stdout)
    release = json.loads(result.stdout)
    assert release['id'] == 416367666 and release['draft'] is False
    assert release['target_commitish'] == '96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
    assert release['tag_name'] == 'yuga-desktop-finish-2026-10-18'
    historical = json.loads(AUDIT.read_text())
    assert historical['passed'] and historical['public_release_id'] == release['id']
    assert historical['source_commit'] == release['target_commitish']
    old = {x['name']: x for x in historical['downloads']}
    assets = {x['name']: x for x in release['assets']}
    rows = []
    for name, (size, sha, asset_id) in EXPECTED.items():
        path = BUILD / name
        before = file_state(path)
        observed = digest(path)
        assert before == file_state(path), name
        assert before['bytes'] == size and observed == sha
        asset = assets[name]
        assert (asset['size'], asset['digest'], asset['id'], asset['state']) == (size, 'sha256:' + sha, asset_id, 'uploaded')
        assert (old[name]['bytes'], old[name]['sha256'], old[name]['asset_id'], old[name]['url']) == (
            size, sha, asset_id, asset['browser_download_url'])
        rows.append({'path': str(path), 'sha256': sha, 'filesystem': before,
                     'recovery': {'operation': 'download_same_public_asset_then_verify_bytes_and_sha256',
                                  'release_id': release['id'], 'asset_id': asset_id,
                                  'url': asset['browser_download_url'], 'api_asset_url': asset['url'],
                                  'bytes': size, 'sha256': sha, 'restore_mode': before['mode'],
                                  'do_not_overwrite_differing_existing_file': True}})
    observation = holders(rows)
    for row in rows:
        assert file_state(Path(row['path'])) == row['filesystem']
    fs = os.statvfs('/workspace')
    report = {'schema': 1, 'status': 'READ_ONLY_PROPOSAL_NOT_EXECUTED', 'started_utc': start,
              'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'exact_paths': 2, 'files': rows, 'logical_bytes': sum(x['filesystem']['bytes'] for x in rows),
              'allocated_bytes': sum(x['filesystem']['allocated_bytes'] for x in rows),
              'reclaimable_if_single_link_and_no_holders': all(x['filesystem']['nlink'] == 1 for x in rows),
              'workspace_available_bytes': fs.f_bavail * fs.f_frsize,
              'historical_public_download_audit': {'path': str(AUDIT), 'sha256': digest(AUDIT)},
              'current_public_api': {'path': 'publication-api-current.json', 'sha256': digest(OUT / 'publication-api-current.json'),
                                     'command': command, 'exit_code': result.returncode},
              'process_observation': observation, 'new_zip_downloads': 0, 'deletions': 0,
              'preserve': ['all Linux actual extraction files', 'raw Linux PCK and other raw PCKs',
                           'all manifests/reports/logs/source/cache/user-state/originals', 'all paths other than the exact two ZIPs'],
              'execution_gate': 'Root must retain/publish this recovery proposal, confirm current owner releases, '
                                'and recheck exact hashes/stat identities/open holders immediately before any deletion. '
                                'This audit has no delete option.'}
    (OUT / 'recovery-map.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({**{k: report[k] for k in ('exact_paths', 'logical_bytes', 'allocated_bytes',
                                                'workspace_available_bytes')},
                      'holders': len(observation['holders']),
                      'inaccessible_owned': len(observation['inaccessible_owned_processes']),
                      'inaccessible_other_uid': len(observation['inaccessible_other_uid_processes']),
                      'zombies': len(observation['zombies_without_live_file_descriptor_tables'])}))

if __name__ == '__main__':
    main()
