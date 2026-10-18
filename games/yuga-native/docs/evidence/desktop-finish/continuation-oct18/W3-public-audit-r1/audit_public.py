#!/usr/bin/env python3
"""Independent successor public audit; default plan only, no engine or deletion."""
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
TAG = 'yuga-desktop-polish-2026-10-18'
SOURCE = '79e5c15d8a3657e16fda67acb277b2406120dcd1'
REFERENCE_SHA = 'fe11edd1fcea72997537942634dd626da0e8908b870b331a54e511003d2a629c'
RESERVE = 500 * 1024 * 1024
OLD_RELEASE_ID = 416367666


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


def verify_zip(path, platform, exported, packaged, reference, common_pck=None):
    expected = packaged['packages'][platform]
    prefix = 'yuga-native-' + platform + '-x86_64/'
    pinned = reference['archives'][platform]
    rows = []
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        require(len(names) == len(set(names)) == expected['entry_count'] == pinned['members'], 'ZIP unique inventory')
        require(set(names) == set(pinned['member_records']), 'ZIP independently pinned member census')
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
            require(actual == pinned['member_records'][info.filename], 'ZIP independently qualified member: ' + name)
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
        require({k: exported['packs'][platform][k] for k in ['bytes', 'sha256', 'entry_count']} == pinned['pck'], 'Qualified PCK identity')
        if common_pck is None:
            pck = verify_pck(z.read(prefix + 'yuga-native.pck'), exported['packs'][platform])
        else:
            require(exported['packs']['linux'] == exported['packs']['windows'] and common_pck['sha256'] == pinned['pck']['sha256'], 'Both platform PCK bytes and full entry tables identical')
            pck = {'passed': True, 'entry_count': pinned['pck']['entry_count'], 'sha256': common_pck['sha256'], 'common_full_directory_verified_in': 'linux', 'whole_member_sha256_and_crc_independently_verified': True}
    return {'passed': True, 'platform': platform, 'member_count': len(rows), 'members': rows, 'pck': pck, 'engine_executed': False}


def execution_guards(args):
    require(args.execute_public_download and args.root_publication_signal, 'Both execution and root publication signal flags required')
    require(args.expected_tag == TAG and args.expected_source == SOURCE, 'Caller must provide exact successor tag and full source')
    require(isinstance(args.expected_release_id, int) and args.expected_release_id > 0 and args.expected_release_id != OLD_RELEASE_ID, 'Root must supply the new draft/release ID; old release forbidden')
    require(args.output is not None and args.output.is_absolute() and args.output.parent.resolve().is_relative_to(Path('/workspace/scratch')), 'Absolute scratch output only')
    require(not args.output.exists() and not args.output.is_symlink(), 'Output must be fresh')


def self_test():
    from types import SimpleNamespace
    checks = []
    good = dict(execute_public_download=True, root_publication_signal=True, expected_tag=TAG, expected_source=SOURCE, expected_release_id=1, output=Path('/workspace/scratch/yuga-public-guard-fixture-not-created'))
    execution_guards(SimpleNamespace(**good)); checks.append('exact caller guard accepted without network or writes')
    for key, bad in [('execute_public_download', False), ('root_publication_signal', False), ('expected_tag', 'old-tag'), ('expected_source', '0'*40), ('expected_release_id', None), ('expected_release_id', OLD_RELEASE_ID), ('output', Path('/tmp/not-allowed'))]:
        try:
            execution_guards(SimpleNamespace(**(good | {key: bad})))
        except ValueError:
            checks.append('rejected ' + key + ':' + str(bad))
        else:
            raise AssertionError('Guard failed: ' + key)
    require(canonical('res/a') and not canonical('../a') and not canonical('/a') and not canonical('a\\b'), 'Canonical path rejection')
    checks.append('canonical paths')
    payload = b'fixture'
    data = bytearray(256 + len(payload)); data[:4] = b'GDPC'
    struct.pack_into('<5I', data, 4, 3, 4, 6, 3, 0)
    struct.pack_into('<Q', data, 24, 256); struct.pack_into('<Q', data, 32, 100)
    struct.pack_into('<I', data, 100, 1); name = b'res://a\0'
    struct.pack_into('<I', data, 104, len(name)); data[108:108+len(name)] = name
    pos = 108 + len(name); struct.pack_into('<QQ', data, pos, 0, len(payload))
    data[pos+16:pos+32] = hashlib.md5(payload).digest(); struct.pack_into('<I', data, pos+32, 0)
    data[256:] = payload
    expected = dict(bytes=len(data), sha256=sha(data), format=3, entry_count=1, entries=[dict(path='res://a', bytes=len(payload), sha256=sha(payload))])
    require(verify_pck(data, expected)['entry_count'] == 1, 'Positive PCK fixture'); checks.append('positive PCK parser')
    changed = expected | {'entries': [expected['entries'][0] | {'sha256': '0'*64}]}
    try:
        verify_pck(data, changed)
    except ValueError:
        checks.append('PCK wrong entry SHA rejected')
    else:
        raise AssertionError('PCK wrong entry accepted')
    broken = bytearray(data); struct.pack_into('<Q', broken, pos, 999999)
    try:
        verify_pck(broken, expected | {'sha256': sha(broken)})
    except ValueError:
        checks.append('PCK offset out of bounds rejected')
    else:
        raise AssertionError('PCK invalid offset accepted')
    print(json.dumps({'passed': True, 'count': len(checks), 'checks': checks, 'network_calls': 0, 'file_writes': 0}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-public-download', action='store_true')
    parser.add_argument('--root-publication-signal', action='store_true', help='Only after root explicitly supplies the published new release ID')
    parser.add_argument('--expected-tag')
    parser.add_argument('--expected-source')
    parser.add_argument('--expected-release-id', type=int, help='Root-confirmed successor draft/release ID; deliberately unset in reference')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    require(file_hash(HERE / 'reference.json') == REFERENCE_SHA, 'Pinned successor reference')
    ref = json.loads((HERE / 'reference.json').read_text())
    require(ref['source_commit'] == SOURCE and ref['tag'] == TAG and ref['release_id'] is None and len(ref['assets']) == 5, 'Exact successor reference; release ID caller-bound')
    if args.self_test:
        require(not args.execute_public_download, 'Self-test cannot execute downloads')
        self_test(); return 0
    total = sum(r['bytes'] for r in ref['assets'].values())
    if not args.execute_public_download:
        print(json.dumps({'status': 'PREPARED_PUBLIC_UNRUN', 'release_id': None, 'tag': TAG, 'source': SOURCE, 'assets': ref['assets'], 'retained_download_bytes': total, 'reserve_bytes': RESERVE, 'minimum_initial_free_bytes': RESERVE + total + 16*1024*1024, 'network_calls': 0, 'engine_runs': 0}, indent=2))
        return 0
    execution_guards(args)
    require(shutil.disk_usage(args.output.parent).free >= RESERVE + total + 16*1024*1024, 'Need all retained downloads plus fresh 500 MiB floor and 16 MiB metadata allowance')
    args.output.mkdir()
    audit = {'passed': False, 'source_commit': SOURCE, 'tag': TAG, 'expected_release_id': args.expected_release_id, 'script_sha256': file_hash(Path(__file__)), 'reference_sha256': REFERENCE_SHA, 'qualification_receipt_sha256': ref['qualification_receipt_sha256'], 'engine_runs': 0, 'downloads': [], 'archives': [], 'commands': [], 'retention': 'Every downloaded file including both ZIPs retained; no extraction or deletion'}
    def run(command):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
        audit['commands'].append({'argv': command, 'exit': result.returncode, 'stderr': result.stderr.decode(errors='replace')})
        require(result.returncode == 0, 'Command failed: ' + command[0])
        return result.stdout
    try:
        release = json.loads(run(['gh', 'api', '--method', 'GET', f'repos/{REPO}/releases/tags/{TAG}']))
        save(args.output / 'publication-api.json', release)
        require(release['id'] == args.expected_release_id and release['tag_name'] == TAG and release['target_commitish'] == SOURCE and release['draft'] is False and bool(release['published_at']), 'Exact newly published release ID/tag/full source')
        tag = run(['git', 'ls-remote', 'https://github.com/' + REPO + '.git', 'refs/tags/' + TAG, 'refs/tags/' + TAG + '^{}']).decode()
        (args.output / 'tag.txt').write_text(tag)
        refs = {line.split()[1]: line.split()[0] for line in tag.splitlines()}
        require(refs.get('refs/tags/' + TAG + '^{}', refs.get('refs/tags/' + TAG)) == SOURCE, 'Independent public tag resolves to exact source')
        assets = {a['name']: a for a in release['assets']}
        require(len(release['assets']) == len(assets) == 5 and set(assets) == set(ref['assets']), 'Exact five public assets')
        for name, identity in ref['assets'].items():
            a = assets[name]
            require(a['size'] == identity['bytes'] and a['digest'] == 'sha256:' + identity['sha256'] and a['state'] == 'uploaded' and a['browser_download_url'] == f'https://github.com/{REPO}/releases/download/{TAG}/{name}', 'Public API asset identity: ' + name)
        order = ['native-export-manifest.json', 'native-package-manifest.json', 'SHA256SUMS.txt', 'yuga-native-linux-x86_64.zip', 'yuga-native-windows-x86_64.zip']
        common_pck = None
        for name in order:
            require(shutil.disk_usage(args.output).free >= RESERVE + ref['assets'][name]['bytes'], 'Fresh per-download 500 MiB floor: ' + name)
            path = args.output / name
            run(['curl', '--fail', '--location', '--silent', '--show-error', '--proto', '=https', '--proto-redir', '=https', '--max-time', '240', '--max-filesize', str(ref['assets'][name]['bytes']), assets[name]['browser_download_url'], '--output', str(path)])
            identity = {'bytes': path.stat().st_size, 'sha256': file_hash(path)}
            require(identity == ref['assets'][name], 'Downloaded exact independently qualified bytes: ' + name)
            require(shutil.disk_usage(args.output).free >= RESERVE, '500 MiB floor after download')
            audit['downloads'].append({'name': name, 'asset_id': assets[name]['id'], 'url': assets[name]['browser_download_url'], **identity})
            if name.endswith('.zip'):
                exported = json.loads((args.output / 'native-export-manifest.json').read_text())
                packaged = json.loads((args.output / 'native-package-manifest.json').read_text())
                require(exported['git']['head'] == packaged['git']['head'] == SOURCE and exported['git']['native_worktree_status'] == packaged['git']['native_worktree_status'] == '', 'Exact clean qualified source manifests')
                require(exported['engine_selection'] == packaged['engine_selection'] == ref['engine_selection'], 'Same qualified exporter/runtime selection')
                platform = 'linux' if 'linux' in name else 'windows'
                result = verify_zip(path, platform, exported, packaged, ref, common_pck)
                audit['archives'].append(result)
                if common_pck is None:
                    common_pck = result['pck']
            save(args.output / 'audit-progress.json', audit)
        parsed = {}
        for line in (args.output / 'SHA256SUMS.txt').read_text().splitlines():
            digest, name = line.split('  ', 1)
            require(name not in parsed, 'No duplicate downloaded checksums')
            parsed[name] = digest
        require(parsed == {n: r['sha256'] for n, r in ref['assets'].items() if n != 'SHA256SUMS.txt'}, 'Exact downloaded checksum coverage')
        require(len(audit['archives']) == 2 and all(a['pck']['sha256'] == ref['pck_sha256'] for a in audit['archives']), 'Identical exact PCK both platforms')
        audit.update(passed=True, public_release_id=release['id'], published_at=release['published_at'], audited_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), downloaded_bytes=sum(r['bytes'] for r in audit['downloads']), free_bytes_after=shutil.disk_usage(args.output).free, scope='Independent public metadata/tag/exact-byte/ZIP/PCK/provenance review only. No downloaded-build execution, Windows execution, hardware or final-art qualification.')
    except Exception as error:
        audit['error'] = repr(error)
    save(args.output / 'download-verification.json', audit)
    print(json.dumps({'passed': audit['passed'], 'assets': len(audit['downloads']), 'archives': len(audit['archives']), 'error': audit.get('error')}))
    return 0 if audit['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
