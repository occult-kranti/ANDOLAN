#!/usr/bin/env python3
"""Exact public r4 byte audit. Default is plan-only; never runs the game."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
REPO = 'occult-kranti/ANDOLAN'
TAG = 'yuga-desktop-finish-2026-10-18'
RELEASE_ID = 416367666
SOURCE = '96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
REFERENCE_SHA = 'c2631d4cf8106268bd2ff3cb4208b0bb901431fcd1d047f9456dcc409b32db33'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    value = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def canonical(name):
    p = PurePosixPath(name)
    return bool(p.parts) and not p.is_absolute() and '..' not in p.parts and '\\' not in name and name == p.as_posix()


def verify_pck(data, expected):
    require(len(data) == expected['bytes'] and sha(data) == expected['sha256'], 'PCK whole-file identity')
    require(len(data) >= 100 and data[:4] == b'GDPC', 'PCK header')
    version, major, minor, patch, flags = struct.unpack_from('<5I', data, 4)
    require(version == expected['format'] and (major, minor, patch) == (4, 6, 3) and not flags & ~2, 'PCK engine/flags')
    base = struct.unpack_from('<Q', data, 24)[0]
    pos = struct.unpack_from('<Q', data, 32)[0] if version == 3 else 96
    require(pos + 4 <= len(data), 'PCK directory bounds')
    count = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    declared = {e['path'].removeprefix('res://'): e for e in expected['entries']}
    require(count == len(declared) == expected['entry_count'], 'PCK exact entry count')
    seen, rows = set(), []
    for _ in range(count):
        require(pos + 4 <= len(data), 'PCK name length bounds')
        length = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        require(0 < length <= 4096 and pos + length + 36 <= len(data), 'PCK entry bounds')
        name = data[pos:pos+length].rstrip(b'\0').decode('utf8').removeprefix('res://')
        pos += length
        offset, size = struct.unpack_from('<QQ', data, pos)
        md5 = data[pos+16:pos+32]
        entry_flags = struct.unpack_from('<I', data, pos+32)[0]
        pos += 36
        require(canonical(name) and name not in seen and name in declared and entry_flags == 0, 'PCK canonical unique declared entry')
        seen.add(name)
        start = base + offset
        require(start + size <= len(data), 'PCK payload bounds')
        payload = memoryview(data)[start:start+size]
        digest = hashlib.sha256(payload).hexdigest()
        require(hashlib.md5(payload).digest() == md5, 'PCK stored MD5: ' + name)
        require(size == declared[name]['bytes'] and digest == declared[name]['sha256'], 'PCK declared payload: ' + name)
        rows.append({'path': name, 'bytes': size, 'sha256': digest, 'stored_md5_verified': True})
    require(seen == set(declared), 'PCK complete directory')
    return {'passed': True, 'format': version, 'entry_count': count, 'sha256': sha(data), 'entries': rows}


def verify_zip(path, platform, exported, packaged):
    expected = packaged['packages'][platform]
    prefix = 'yuga-native-' + platform + '-x86_64/'
    rows = []
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        require(len(names) == len(set(names)) == expected['entry_count'], 'ZIP unique inventory')
        require(all(canonical(n) and n.startswith(prefix) and not i.is_dir() and stat.S_ISREG(i.external_attr >> 16) and not i.flag_bits & 1 for n, i in zip(names, infos)), 'ZIP regular canonical members')
        inner = json.loads(z.read(prefix + 'PACKAGE-MANIFEST.json'))
        require(set(names) == {prefix + n for n in inner['payloads']} | {prefix + 'PACKAGE-MANIFEST.json'}, 'ZIP exact declared members')
        require(inner['platform'] == platform + '-x86_64' and inner['git'] == exported['git'] and inner['runtime_source'] == exported['source'], 'ZIP source/platform identity')
        require(inner['exporter'] == exported['engine_selection']['exporter'], 'ZIP exporter identity')
        for info in infos:
            digest, size = hashlib.sha256(), 0
            with z.open(info) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
                    size += len(block)
            name = info.filename[len(prefix):]
            actual = {'bytes': size, 'sha256': digest.hexdigest()}
            require(size == info.file_size, 'ZIP size: ' + name)
            if name != 'PACKAGE-MANIFEST.json':
                require(actual == inner['payloads'][name], 'ZIP payload identity: ' + name)
            rows.append({'path': name, **actual, 'mode': oct(stat.S_IMODE(info.external_attr >> 16)), 'crc32': f'{info.CRC:08x}', 'crc_verified_by_eof_read': True})
        engine = 'godot' if platform == 'linux' else 'godot.exe'
        require(inner['payloads'][engine] == expected['engine'], 'ZIP exact platform engine')
        require(inner['payloads']['yuga-native.pck'] == {k: expected['pck'][k] for k in ['bytes', 'sha256']}, 'ZIP PCK declared identity')
        if platform == 'linux':
            selection = exported['engine_selection']
            require(inner['runtime'] == selection['linux_runtime'], 'ZIP declared patched runtime')
            require(json.loads(z.read(prefix + 'NOTICE/GODOT-RUNTIME-PROVENANCE.json')) == selection, 'ZIP bundled runtime selection')
            proof = selection['linux_runtime']['provenance']
            require(proof['source_patches'] == 1 and proof['variant'] == 'pipeline-low-priority-v1' and len(proof['evidence']) == 11 and set(proof['evidence']) == set(proof['bundled_evidence']), 'ZIP exact eleven source/build proofs')
            for source, identity in proof['evidence'].items():
                raw = z.read(prefix + proof['bundled_evidence'][source])
                require(len(raw) == identity['bytes'] and sha(raw) == identity['sha256'], 'ZIP source/build proof: ' + source)
            require(stat.S_IMODE(z.getinfo(prefix + 'godot').external_attr >> 16) == 0o755 and stat.S_IMODE(z.getinfo(prefix + 'launch.sh').external_attr >> 16) == 0o755, 'ZIP executable modes')
        else:
            require(inner['runtime']['sha256'] == expected['engine']['sha256'], 'ZIP Windows engine remains explicit')
        pck = verify_pck(z.read(prefix + 'yuga-native.pck'), exported['packs'][platform])
    return {'passed': True, 'platform': platform, 'member_count': len(rows), 'members': rows, 'pck': pck, 'engine_executed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-public-download', action='store_true', help='Use only after root publication trigger')
    parser.add_argument('--output', type=Path, default=Path('/workspace/scratch/yuga-desktop-r4-public-audit-r1'))
    args = parser.parse_args()
    require(file_hash(HERE / 'reference.json') == REFERENCE_SHA, 'Pinned audit reference')
    ref = json.loads((HERE / 'reference.json').read_text())
    if not args.execute_public_download:
        print(json.dumps({'status': 'READY_UNRUN', 'release': RELEASE_ID, 'tag': TAG, 'source': SOURCE, 'assets': ref['assets'], 'peak_download_disk_bytes': max(r['bytes'] for r in ref['assets'].values()) + 1024*1024, 'network_calls': 0}, indent=2))
        return 0
    require(not args.output.exists() and args.output.is_absolute() and args.output.is_relative_to(Path('/workspace/scratch')), 'Fresh scratch output only')
    require(shutil.disk_usage(args.output.parent).free >= 512*1024*1024, '512 MiB scratch reserve required')
    args.output.mkdir()
    audit = {'passed': False, 'source_commit': SOURCE, 'script_sha256': file_hash(Path(__file__)), 'reference_sha256': REFERENCE_SHA, 'engine_runs': 0, 'downloads': [], 'archives': [], 'commands': []}
    def run(command):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        audit['commands'].append({'argv': command, 'exit': result.returncode, 'stderr': result.stderr.decode(errors='replace')})
        require(result.returncode == 0, 'Command failed: ' + command[0])
        return result.stdout
    try:
        release = json.loads(run(['gh', 'api', f'repos/{REPO}/releases/tags/{TAG}']))
        save(args.output / 'publication-api.json', release)
        require(release['id'] == RELEASE_ID and release['tag_name'] == TAG and release['target_commitish'] == SOURCE and release['draft'] is False and bool(release['published_at']), 'Exact published release')
        tag = run(['git', 'ls-remote', 'https://github.com/' + REPO + '.git', 'refs/tags/' + TAG, 'refs/tags/' + TAG + '^{}']).decode()
        (args.output / 'tag.txt').write_text(tag)
        refs = {line.split()[1]: line.split()[0] for line in tag.splitlines()}
        require(refs.get('refs/tags/' + TAG + '^{}', refs.get('refs/tags/' + TAG)) == SOURCE, 'Public tag commit')
        assets = {a['name']: a for a in release['assets']}
        require(len(release['assets']) == len(assets) == 5 and set(assets) == set(ref['assets']), 'Exact five public assets')
        for name, identity in ref['assets'].items():
            a = assets[name]
            require(a['size'] == identity['bytes'] and a['digest'] == 'sha256:' + identity['sha256'] and a['state'] == 'uploaded' and a['browser_download_url'] == f'https://github.com/{REPO}/releases/download/{TAG}/{name}', 'Public API asset identity: ' + name)
        # Small manifests first; then one ZIP at a time. No expanded archive copies.
        order = ['native-export-manifest.json', 'native-package-manifest.json', 'SHA256SUMS.txt', 'yuga-native-linux-x86_64.zip', 'yuga-native-windows-x86_64.zip']
        for name in order:
            path = args.output / name
            run(['curl', '--fail', '--location', '--silent', '--show-error', '--proto', '=https', '--proto-redir', '=https', '--max-time', '240', assets[name]['browser_download_url'], '--output', str(path)])
            identity = {'bytes': path.stat().st_size, 'sha256': file_hash(path)}
            require(identity == ref['assets'][name], 'Downloaded exact bytes: ' + name)
            audit['downloads'].append({'name': name, 'asset_id': assets[name]['id'], 'url': assets[name]['browser_download_url'], **identity})
            if name.endswith('.zip'):
                exported = json.loads((args.output / 'native-export-manifest.json').read_text())
                packaged = json.loads((args.output / 'native-package-manifest.json').read_text())
                require(exported['git']['head'] == packaged['git']['head'] == SOURCE and exported['git']['native_worktree_status'] == packaged['git']['native_worktree_status'] == '', 'Exact clean source manifests')
                require(exported['engine_selection'] == packaged['engine_selection'], 'Same declared exporter/runtime selection')
                platform = 'linux' if 'linux' in name else 'windows'
                audit['archives'].append(verify_zip(path, platform, exported, packaged))
                save(args.output / 'audit-progress.json', audit)
                # Only this fresh downloaded ZIP is removed after complete validation.
                path.unlink()
        sums = (args.output / 'SHA256SUMS.txt').read_text().splitlines()
        parsed = {}
        for line in sums:
            digest, name = line.split('  ', 1)
            require(name not in parsed, 'No duplicate checksums')
            parsed[name] = digest
        require(parsed == {n: r['sha256'] for n, r in ref['assets'].items() if n != 'SHA256SUMS.txt'}, 'Exact downloaded checksum coverage')
        require(len(audit['archives']) == 2 and all(a['pck']['sha256'] == ref['pck_sha256'] for a in audit['archives']), 'Same exact PCK both platforms')
        audit.update(passed=True, public_release_id=RELEASE_ID, published_at=release['published_at'], audited_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), downloaded_bytes=sum(r['bytes'] for r in audit['downloads']), scope='Public exact-byte and archive integrity only; no gameplay execution, no Windows execution, no hardware or final-art acceptance.')
    except Exception as error:
        audit['error'] = repr(error)
    save(args.output / 'download-verification.json', audit)
    print(json.dumps({'passed': audit['passed'], 'assets': len(audit['downloads']), 'archives': len(audit['archives']), 'error': audit.get('error')}))
    return 0 if audit['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
