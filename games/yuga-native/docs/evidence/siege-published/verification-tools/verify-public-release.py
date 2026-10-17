#!/usr/bin/env python3
"""Read-only public release download and independent package/source verification.
No network is used without --execute. Output must be a fresh absolute directory.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,160}\Z')
TAG = re.compile(r'yuga-traversal-armies-[A-Za-z0-9][A-Za-z0-9._-]{0,100}\Z')
AGENT = 'YUGA-independent-public-release-verification'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def record(path):
    path = Path(path)
    return {'bytes': path.stat().st_size, 'sha256': digest(path)}


def save(path, value):
    with Path(path).open('x') as output:
        json.dump(value, output, indent=2, sort_keys=True, allow_nan=False)
        output.write('\n')


def api(url):
    request = urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def download(url, destination, expected_size):
    require(0 < expected_size <= 1024 * 1024 * 1024, 'Unbounded or empty public asset')
    request = urllib.request.Request(url, headers={'User-Agent': AGENT})
    count = 0
    with urllib.request.urlopen(request, timeout=120) as response, destination.open('xb') as output:
        for block in iter(lambda: response.read(1024 * 1024), b''):
            count += len(block)
            require(count <= expected_size, 'Public payload exceeded its listed size')
            output.write(block)
    require(count == expected_size, 'Public payload was truncated')
    return record(destination)


def load_helper(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_blob(checkout, commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=checkout, stderr=subprocess.PIPE)


def verify_package(archive_path, platform, exported, aggregate, inspector, evidence):
    expected_root = 'yuga-native-' + platform + '-x86_64'
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and len(names) < 1000, 'Duplicate/excess package entries')
        for entry in archive.infolist():
            p = PurePosixPath(entry.filename)
            require(not p.is_absolute() and '..' not in p.parts and '\\' not in entry.filename and p.parts[0] == expected_root,
                    'Unsafe archive entry')
            require(not stat.S_ISLNK(entry.external_attr >> 16), 'Symlink in package')
        require(archive.testzip() is None, 'ZIP CRC failure')
        packaged = json.loads(archive.read(expected_root + '/PACKAGE-MANIFEST.json'))
        require(packaged['git']['head'] == aggregate['git']['head'] == exported['git']['head'], 'Packaged source commit mismatch')
        require(packaged['runtime_source'] == exported['source'], 'Internal runtime source inventory differs')
        required = {expected_root + '/' + name for name in packaged['payloads']} | {expected_root + '/PACKAGE-MANIFEST.json'}
        require(set(names) == required, 'Exact archive payload inventory mismatch')
        for name, expected in packaged['payloads'].items():
            full = expected_root + '/' + name
            require(archive.getinfo(full).file_size == expected['bytes'], 'Payload length mismatch: ' + name)
            h = hashlib.sha256()
            with archive.open(full) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(block)
            require(h.hexdigest() == expected['sha256'], 'Payload hash mismatch: ' + name)
        with tempfile.TemporaryDirectory(prefix='pck-inspection-', dir=evidence) as temporary:
            pack = Path(temporary) / 'game.pck'
            with archive.open(expected_root + '/yuga-native.pck') as source, pack.open('xb') as output:
                for block in iter(lambda: source.read(1024 * 1024), b''):
                    output.write(block)
            actual = inspector.inspect_pack(pack)
        require(actual == packaged['pck'] == exported['packs'][platform], 'PCK entries/header/hash differ from export evidence')
        engine_name = 'godot' if platform == 'linux' else 'godot.exe'
        require(packaged['payloads'][engine_name] == aggregate['packages'][platform]['engine'], 'Engine fingerprint mismatch')
        return {'passed': True, 'zip': record(archive_path), 'entries': len(names), 'pck_entries': actual['entry_count'],
                'pck_sha256': actual['sha256'], 'all_zip_crc_and_payload_sha256_verified': True,
                'all_pck_md5_and_sha256_verified': True, 'executed': False}


def run(args):
    output = args.output
    require(output.is_absolute() and not output.exists(), 'Output must be a new absolute directory')
    require(TAG.fullmatch(args.tag) and args.tag.endswith('-siege'), 'Expected a siege release tag')
    require(re.fullmatch(r'[0-9a-f]{40}', args.commit), 'A full expected source commit is required')
    require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository), 'Invalid repository')
    if not args.execute:
        print(json.dumps({'execute': False, 'tag': args.tag, 'commit': args.commit, 'output': str(output),
                          'expected_assets': args.expected_assets, 'network_requests': 0}, indent=2))
        return
    output.mkdir(parents=True)
    assets = output / 'assets'; assets.mkdir()
    evidence = output / 'evidence'; evidence.mkdir()
    report = {'passed': False, 'tag': args.tag, 'commit': args.commit,
              'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'Public bytes, exact inventories, committed sources and package structure. No game execution, listening, rendering, Windows or hardware-performance claim.'}
    try:
        endpoint = 'https://api.github.com/repos/' + args.repository
        release = api(endpoint + '/releases/tags/' + urllib.parse.quote(args.tag, safe=''))
        require(not release['draft'] and release['tag_name'] == args.tag, 'Release is not published under the expected tag')
        save(evidence / 'remote-release.json', release)
        ref = api(endpoint + '/git/ref/tags/' + urllib.parse.quote(args.tag, safe=''))
        save(evidence / 'remote-tag-ref.json', ref)
        obj = ref['object']
        for _ in range(8):
            if obj['type'] == 'commit':
                break
            require(obj['type'] == 'tag' and re.fullmatch(r'[0-9a-f]{40}', obj['sha']), 'Unexpected tag object')
            obj = api(endpoint + '/git/tags/' + obj['sha'])['object']
        require(obj['type'] == 'commit' and obj['sha'] == args.commit, 'Remote tag source mismatch')
        listing = []
        for page in range(1, 5):
            rows = api(endpoint + f'/releases/{release["id"]}/assets?per_page=100&page={page}')
            listing.extend(rows)
            if len(rows) < 100:
                break
        else:
            raise ValueError('Public asset listing exceeds bounded pagination')
        save(evidence / 'remote-assets.json', listing)
        require(len(listing) == len({row['name'] for row in listing}), 'Duplicate remote asset name')
        if args.expected_assets is not None:
            require(len(listing) == args.expected_assets, 'Remote asset count differs from confirmed CI inventory')
        by_name = {row['name']: row for row in listing}
        prefix = 'https://github.com/' + args.repository + '/releases/download/' + args.tag + '/'
        for name, row in by_name.items():
            require(NAME.fullmatch(name) and row['state'] == 'uploaded', 'Unsafe or incomplete remote asset')
            require(row['browser_download_url'] == prefix + name, 'Unexpected asset download origin/path')
        require('release-manifest.json' in by_name, 'Missing public inventory')
        row = by_name['release-manifest.json']
        download(row['browser_download_url'], assets / row['name'], row['size'])
        manifest = json.loads((assets / row['name']).read_text())
        require(manifest['tag'] == args.tag and manifest['commit'] == args.commit, 'Manifest source identity mismatch')
        require(set(by_name) == set(manifest['files']) | {'release-manifest.json', 'SHA256SUMS'}, 'Remote listing differs from manifest inventory')
        def get(name):
            row = by_name[name]
            actual = download(row['browser_download_url'], assets / name, row['size'])
            if name in manifest['files']:
                require(actual == manifest['files'][name], 'Downloaded asset differs from manifest: ' + name)
            if row.get('digest'):
                require(row['digest'] == 'sha256:' + actual['sha256'], 'GitHub asset digest mismatch: ' + name)
            return name, actual
        with ThreadPoolExecutor(max_workers=3) as pool:
            downloads = dict(pool.map(get, sorted(set(by_name) - {'release-manifest.json'})))
        downloads['release-manifest.json'] = record(assets / 'release-manifest.json')
        save(evidence / 'downloaded-asset-hashes.json', downloads)
        project = args.checkout / 'games/yuga-native'
        for filename in ['release-native.py', 'package-native.py']:
            local = project / 'tools' / filename
            require(local.read_bytes() == git_blob(args.checkout, args.commit, 'games/yuga-native/tools/' + filename),
                    'Verification helper differs from tagged source: ' + filename)
        command = [sys.executable, str(project / 'tools/release-native.py'), 'verify', '--directory', str(assets), '--tag', args.tag, '--commit', args.commit]
        checked = subprocess.run(command, cwd=args.checkout, capture_output=True, text=True)
        (evidence / 'release-verify.stdout.txt').write_text(checked.stdout)
        (evidence / 'release-verify.stderr.txt').write_text(checked.stderr)
        require(checked.returncode == 0, 'Repository release verifier failed')
        exported = json.loads((assets / 'native-export-manifest.json').read_text())
        aggregate = json.loads((assets / 'native-package-manifest.json').read_text())
        source_files = exported['source']['files']
        signature = hashlib.sha256(json.dumps(source_files, sort_keys=True).encode()).hexdigest()
        require(signature == exported['source']['sha256'] == aggregate['runtime_source_sha256'], 'Runtime source inventory signature mismatch')
        for relative, expected in source_files.items():
            require(not PurePosixPath(relative).is_absolute() and '..' not in PurePosixPath(relative).parts, 'Unsafe source inventory path')
            raw = git_blob(args.checkout, args.commit, 'games/yuga-native/' + relative)
            require({'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} == expected,
                    'Runtime source differs from committed bytes: ' + relative)
        inspector = load_helper(project / 'tools/package-native.py', 'independent_native_pack_inspector')
        report['packages'] = {}
        for platform in ['linux', 'windows']:
            report['packages'][platform] = verify_package(assets / aggregate['packages'][platform]['filename'], platform, exported, aggregate, inspector, evidence)
        report.update(passed=True, assets=len(listing), source_files_verified=len(source_files), runtime_source_sha256=signature,
                      release_id=release['id'], release_verify=json.loads(checked.stdout), remote_tag_matches=True,
                      remote_asset_listing_matches=True, command=command)
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        report['finished_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(evidence / 'public-verification.json', report)
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repository', default='occult-kranti/ANDOLAN')
    parser.add_argument('--checkout', type=Path, default=Path('/workspace/ANDOLAN'))
    parser.add_argument('--expected-assets', type=int, help='Set only after CI confirms the final inventory count')
    parser.add_argument('--execute', action='store_true', help='Perform public read-only network requests and downloads; otherwise plan only')
    run(parser.parse_args())


if __name__ == '__main__':
    main()
