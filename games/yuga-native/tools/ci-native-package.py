#!/usr/bin/env python3
"""Build-candidate identity helpers. These do not publish or qualify gameplay."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile

sys.dont_write_bytecode = True
PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
RUNTIME_URL = ('https://github.com/occult-kranti/ANDOLAN/releases/download/'
               'yuga-desktop-polish-2026-10-18/yuga-native-linux-x86_64.zip')
RUNTIME_ARCHIVE = {'bytes': 97903966, 'sha256': '781d904d2f6986f423274cf23ecdc16a35df65df755db5171a97a152a3c88aa8'}
RUNTIME_BINARY = {'bytes': 85447128, 'sha256': 'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'}
RUNTIME_MEMBER = 'yuga-native-linux-x86_64/godot'


def require(value, message):
    if not value:
        raise ValueError(message)


def record(path):
    path = Path(path)
    require(not path.is_symlink() and stat.S_ISREG(path.lstat().st_mode), 'Regular file required: ' + str(path))
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'sha256': digest}


def write_json(path, data):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write('\n')


def extract_runtime(archive, destination, expected_archive=RUNTIME_ARCHIVE, expected_binary=RUNTIME_BINARY):
    """Validate before extracting one named regular file; fixtures may supply pins."""
    require(record(archive) == expected_archive, 'Reviewed runtime ZIP identity mismatch')
    destination = Path(destination)
    require(not destination.exists() and not destination.is_symlink(), 'Fresh runtime destination required')
    with zipfile.ZipFile(archive) as package:
        seen = set()
        for entry in package.infolist():
            name = entry.filename
            parts = name.split('/')
            require(name not in seen and '\\' not in name and all(part not in ('', '.', '..') for part in parts)
                    and not PurePosixPath(name).is_absolute(), 'Unsafe or duplicate runtime ZIP member')
            require(parts[0] == 'yuga-native-linux-x86_64', 'Unexpected runtime ZIP root')
            require(stat.S_ISREG(entry.external_attr >> 16), 'Runtime ZIP member must be a regular file')
            seen.add(name)
        require(RUNTIME_MEMBER in seen, 'Reviewed runtime member missing')
        entry = package.getinfo(RUNTIME_MEMBER)
        require(entry.file_size == expected_binary['bytes'], 'Reviewed runtime member size mismatch')
        destination.mkdir(parents=True)
        target = destination / 'godot'
        with package.open(entry) as source, target.open('xb') as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
        require(record(target) == expected_binary, 'Extracted runtime identity mismatch')
        require(record(archive) == expected_archive, 'Runtime archive changed during extraction')
        target.chmod(0o755)
    proof = {'archive_url': RUNTIME_URL, 'archive': expected_archive,
             'member': RUNTIME_MEMBER, 'runtime': record(target),
             'scope': 'Exact previously reviewed engine only; new game data is exported separately.'}
    write_json(destination / 'runtime-preparation.json', proof)
    return proof


def package_module():
    spec = importlib.util.spec_from_file_location('native_packaging', PROJECT / 'tools/package-native.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def notice_snapshot():
    """Bind the entire notice tree copied into each portable package."""
    root = PROJECT / 'NOTICE'
    require(not root.is_symlink() and root.is_dir(), 'Regular NOTICE directory required')
    resolved_root = root.resolve()
    require(resolved_root.is_relative_to(PROJECT.resolve()), 'NOTICE directory escapes project')
    files = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'NOTICE symlink is not allowed: ' + str(path))
        require(path.resolve().is_relative_to(resolved_root), 'NOTICE path escapes root: ' + str(path))
        if not path.is_dir():
            files[path.relative_to(PROJECT).as_posix()] = record(path)
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', 'games/yuga-native/NOTICE'],
                                      cwd=REPOSITORY).decode().split('\0')
    tracked = {name.removeprefix('games/yuga-native/') for name in tracked if name}
    require(set(files) == tracked, 'NOTICE file census differs from tracked source')
    return files


def source_snapshot(expected_commit):
    package = package_module()
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPOSITORY, text=True).strip()
    require(actual == expected_commit, 'Checkout is not the requested source commit')
    subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--'], cwd=REPOSITORY, check=True)
    runtime = package.source_state()
    prefixes = ['games/yuga-native/' + part for part in ('scripts', 'shaders', 'scenes', 'assets', 'project.godot', 'export_presets.cfg')]
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', *prefixes], cwd=REPOSITORY).decode().split('\0')
    tracked = {name.removeprefix('games/yuga-native/') for name in tracked if name}
    require(set(runtime['files']) == tracked, 'Runtime file census differs from tracked source')
    return {'source_commit': actual, 'runtime': runtime, 'notices': notice_snapshot(),
            'packaging_tool': record(PROJECT / 'tools/package-native.py'),
            'candidate_tool': record(Path(__file__)),
            'workflow': record(REPOSITORY / '.github/workflows/yuga-native-package.yml')}


def finalize(before, build, expected_commit, run_id):
    before = json.loads(Path(before).read_text())
    require(source_snapshot(expected_commit) == before, 'Source changed during import/export/package')
    build = Path(build)
    exported = json.loads((build / 'native-export-manifest.json').read_text())
    packaged = json.loads((build / 'native-package-manifest.json').read_text())
    require(exported['git']['head'] == packaged['git']['head'] == expected_commit, 'Package commit mismatch')
    require(exported['source'] == before['runtime'] and packaged['runtime_source_sha256'] == before['runtime']['sha256'], 'Package runtime source mismatch')
    files = {}
    for platform in ('linux', 'windows'):
        row = packaged['packages'][platform]
        require(row['filename'] == 'yuga-native-' + platform + '-x86_64.zip', 'Unexpected package name')
        require(row['all_crc_and_payload_sha256_verified'] is True and row['entry_count'] > 0, 'Nonempty verified archive required')
        path = build / row['filename']
        files[path.name] = record(path)
        require(files[path.name] == {key: row[key] for key in ('bytes', 'sha256')}, 'Final archive identity mismatch')
    for name in ('native-export-manifest.json', 'native-package-manifest.json'):
        files[name] = record(build / name)
    sums = ''.join(value['sha256'] + '  ' + name + '\n' for name, value in sorted(files.items()))
    with (build / 'SHA256SUMS.txt').open('x') as stream:
        stream.write(sums)
    files['SHA256SUMS.txt'] = record(build / 'SHA256SUMS.txt')
    proof = {'schema': 1, 'source_commit': expected_commit, 'workflow_run_id': run_id,
             'source': before, 'assets': files, 'source_unchanged': True,
             'status': 'built_candidate_requires_independent_qualification',
             'limits': ['No publication.', 'No native window or Windows execution in this job.',
                        'Foundation CI, export diagnostic review and actual Linux acceptance remain separate.']}
    write_json(build / 'native-candidate-proof.json', proof)
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare-runtime')
    prepare.add_argument('--archive', type=Path)
    prepare.add_argument('--destination', type=Path, required=True)
    snapshot = commands.add_parser('snapshot')
    snapshot.add_argument('--commit', required=True)
    snapshot.add_argument('--output', type=Path, required=True)
    finish = commands.add_parser('finalize')
    finish.add_argument('--commit', required=True)
    finish.add_argument('--run-id', required=True)
    finish.add_argument('--before', type=Path, required=True)
    finish.add_argument('--build', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare-runtime':
        archive = args.archive
        if archive is None:
            archive = args.destination.with_suffix('.download.zip')
            archive.parent.mkdir(parents=True, exist_ok=True)
            total = 0
            with urllib.request.urlopen(RUNTIME_URL, timeout=60) as response, archive.open('xb') as output:
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    require(total <= RUNTIME_ARCHIVE['bytes'], 'Runtime download exceeds pinned size')
                    output.write(chunk)
        result = extract_runtime(archive, args.destination)
        print(json.dumps({'prepared': result['runtime'], 'destination': str(args.destination)}))
    elif args.command == 'snapshot':
        result = source_snapshot(args.commit)
        write_json(args.output, result)
        print(json.dumps({'source_commit': args.commit, 'runtime_files': len(result['runtime']['files'])}))
    else:
        result = finalize(args.before, args.build, args.commit, args.run_id)
        print(json.dumps({'status': result['status'], 'source_commit': args.commit, 'assets': result['assets']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
