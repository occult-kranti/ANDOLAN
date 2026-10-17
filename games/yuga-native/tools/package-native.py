#!/usr/bin/env python3
"""Build auditable, portable native packages without editor export templates.

The official MIT-licensed Godot engine runs the exported project with --main-pack.
No downloaded tools or credentials are embedded. Windows packages are not treated
as executed merely because export and archive validation succeed on Linux.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
DEFAULT_LINUX = Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
DEFAULT_WINDOWS = Path('/workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe')
EXPECTED_VERSION = '4.6.3'
PLATFORMS = {'linux': 'Linux x86_64', 'windows': 'Windows x86_64'}
# Match file names, not broad substrings such as the word "shader".
SECRET_NAME = re.compile(r'(^|[._-])(token|credential|credentials|secret|secrets|password|id_rsa|id_ed25519)([._-]|$)', re.I)
SECRET_CONTENT = re.compile(rb'(?:github_pat_[A-Za-z0-9_]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(part)
    return value.hexdigest()


def record(path: Path) -> dict:
    return {'bytes': path.stat().st_size, 'sha256': digest(path)}


def json_write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def source_state() -> dict:
    files = []
    for directory in ('scripts', 'shaders', 'scenes', 'assets'):
        files.extend(p for p in (PROJECT / directory).rglob('*') if p.is_file())
    files.extend([PROJECT / 'project.godot', PROJECT / 'export_presets.cfg'])
    records = {str(p.relative_to(PROJECT)): record(p) for p in sorted(files)}
    signature = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    return {'sha256': signature, 'files': records}


def git_context() -> dict:
    def git(*args: str) -> str:
        return subprocess.check_output(['git', *args], cwd=REPOSITORY, text=True).strip()
    return {'head': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
            'native_worktree_status': git('status', '--short', '--', 'games/yuga-native')}


def inspect_pack(path: Path) -> dict:
    """Read Godot v2/v3 PCK directory and verify every member's stored MD5.

    Layout reference: godotengine/godot 4.6-stable,
    core/io/file_access_pack.cpp PackedSourcePCK::try_open_pack.
    MD5 here verifies the engine's existing pack integrity field; SHA-256 also
    records every actual payload. It is not used as a security signature.
    """
    data = path.read_bytes()
    if len(data) < 100 or data[:4] != b'GDPC':
        raise ValueError('Missing Godot PCK magic/header')
    version, major, minor, patch, flags = struct.unpack_from('<5I', data, 4)
    file_base = struct.unpack_from('<Q', data, 24)[0]
    if version not in (2, 3) or (major, minor, patch) != (4, 6, 3):
        raise ValueError(f'Unexpected pack version/engine: {version}, {major}.{minor}.{patch}')
    if flags & ~2:  # 2 is relative file-base; encrypted or sparse not accepted.
        raise ValueError(f'Unsupported/encrypted pack flags: {flags}')
    position = struct.unpack_from('<Q', data, 32)[0] if version == 3 else 96
    if position + 4 > len(data):
        raise ValueError('Pack directory is outside file')
    count = struct.unpack_from('<I', data, position)[0]
    position += 4
    if count < 10 or count > 10000:
        raise ValueError(f'Unexpected packed resource count: {count}')
    entries = []
    seen = set()
    for _ in range(count):
        length = struct.unpack_from('<I', data, position)[0]
        position += 4
        if length > 4096 or position + length + 36 > len(data):
            raise ValueError('Invalid packed resource entry bounds')
        name = data[position:position + length].rstrip(b'\x00').decode('utf-8')
        position += length
        offset, size = struct.unpack_from('<QQ', data, position)
        expected_md5 = data[position + 16:position + 32]
        entry_flags = struct.unpack_from('<I', data, position + 32)[0]
        position += 36
        if entry_flags:
            raise ValueError(f'Encrypted/removal/delta entry is not allowed: {name}')
        relative = name.removeprefix('res://')
        parts = PurePosixPath(relative).parts
        if not parts or '..' in parts or relative.startswith('/') or '\\' in relative or name in seen:
            raise ValueError(f'Unsafe or duplicate pack path: {name}')
        seen.add(name)
        if parts[0] not in {'.godot', 'assets', 'scripts', 'shaders', 'scenes', 'project.binary'}:
            raise ValueError(f'Unexpected runtime resource directory: {name}')
        if parts[0] == '.godot' and len(parts) > 1 and parts[1] not in {
            'imported', 'exported', 'global_script_class_cache.cfg', 'uid_cache.bin'}:
            raise ValueError(f'Unexpected Godot cache resource: {name}')
        if any(SECRET_NAME.search(part) or part == '.env' for part in parts):
            raise ValueError(f'Potential credential filename in pack: {name}')
        start = file_base + offset
        if start < 0 or start + size > len(data):
            raise ValueError(f'Packed payload exceeds file bounds: {name}')
        payload = data[start:start + size]
        if hashlib.md5(payload).digest() != expected_md5:
            raise ValueError(f'Packed payload MD5 mismatch: {name}')
        if SECRET_CONTENT.search(payload):
            raise ValueError(f'Potential credential marker in payload: {name}')
        entries.append({'path': name, 'bytes': size, 'sha256': hashlib.sha256(payload).hexdigest(),
                        'stored_md5_verified': True})
    required = ('rama.glb-', 'rama-production.glb-', 'lanka_courtyard.glb-',
                'production_water.gdshader', 'project.binary', 'courtyard.tscn')
    for item in required:
        if not any(item in entry['path'] for entry in entries):
            raise ValueError(f'Required runtime resource missing: {item}')
    return {'format': version, 'engine': f'{major}.{minor}.{patch}', 'entries': entries,
            'entry_count': count, 'all_entry_md5_verified': True,
            'no_tools_tests_documents_or_credential_markers': True, **record(path)}


def run_export(godot: Path, platform: str, pack: Path, log: Path) -> None:
    env = os.environ.copy()
    for name, suffix in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        env.setdefault(name, str(PROJECT / 'build' / 'xdg' / suffix))
        Path(env[name]).mkdir(parents=True, exist_ok=True)
    command = [str(godot), '--headless', '--path', str(PROJECT), '--export-pack', PLATFORMS[platform], str(pack)]
    with log.open('w') as stream:
        result = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=240)
    if result.returncode:
        raise RuntimeError(f'{platform} PCK export failed; inspect {log}')
    text = log.read_text(errors='replace')
    if 'SCRIPT ERROR:' in text or '\nERROR:' in text:
        raise RuntimeError(f'{platform} export logged an error; inspect {log}')


def export_all(args: argparse.Namespace, build: Path) -> dict:
    version = subprocess.check_output([str(args.linux_engine), '--version'], text=True).strip()
    if not version.startswith(EXPECTED_VERSION + '.'):
        raise ValueError(f'Expected Godot {EXPECTED_VERSION}; found {version}')
    rama = PROJECT / 'assets/heroes/rama.glb'
    original_rama = REPOSITORY / 'games/yuga/client/assets/heroes/rama.glb'
    if digest(rama) != digest(original_rama):
        raise ValueError('Staged Rama asset differs from the existing YUGA source model')
    production = json.loads((PROJECT / 'NOTICE/RAMA-PRODUCTION-PROVENANCE.json').read_text())
    if digest(PROJECT / 'assets/heroes/rama-production.glb') != production['sha256']:
        raise ValueError('Production Rama notice differs from the active model')
    before = source_state()
    packs = {}
    for platform in PLATFORMS:
        pack = build / f'yuga-native-{platform}.pck'
        run_export(args.linux_engine, platform, pack, build / f'export-{platform}.log')
        packs[platform] = inspect_pack(pack)
    after = source_state()
    if before['sha256'] != after['sha256']:
        raise ValueError('Runtime source changed during export; rerun on a frozen/imported tree')
    manifest = {'schema': 1, 'kind': 'native-pck-export', 'godot_version': version,
                'git': git_context(), 'source': after, 'packs': packs,
                'rama_matches_existing_yuga_source': True,
                'limits': ['No Windows execution performed by this tool.',
                           'PCK and archive checks do not establish visual quality or gameplay acceptance.']}
    json_write(build / 'native-export-manifest.json', manifest)
    return manifest


def start_readme(platform: str) -> str:
    start = './launch.sh' if platform == 'linux' else 'launch.bat'
    return f'''YUGA — LANKA COURTYARD\nOriginal native training foundation / {platform} x86_64\n\nExtract the ENTIRE ZIP to one folder, then run {start}.\nNo Godot editor installation is required. The bundled official Godot 4.6.3\nengine opens yuga-native.pck directly using --main-pack. This portable package\ncontains the full engine binary and is larger than a release-template export.\n\nControls\nWASD / arrows: move; mouse: aim; left mouse: solar bow; Space: jump;\nShift: sprint; R: reload; Q: sunburst; E: dash; Esc: pause/release cursor;\nF5: reset. Settings include aim sensitivity, sound, fullscreen, shadows and night.\n\nCompatibility fallback\nRun {start} --rendering-method gl_compatibility\nThe default Forward+ renderer needs Vulkan-capable graphics. The compatibility\nrenderer omits Forward+ glow and SSAO. A recent graphics driver is recommended.\n\nScope\nThis is an original single-player training courtyard with Rama and five targets.\nIt is not a full match, multiplayer server, commercial-engine reconstruction,\nor evidence of Deadlock/Overwatch visual parity. Windows is packaged and archive-\nvalidated from Linux; native Windows execution has not been verified here.\n\nLicenses and provenance\nSee NOTICE/ and PACKAGE-MANIFEST.json. Original project sources and evidence:\nhttps://github.com/occult-kranti/ANDOLAN/tree/game/yuga-native-production/games/yuga-native\n\nLinux desktop runtime dependencies\nA desktop X11/Wayland session, graphics/audio drivers and standard system\nlibraries are required. The ZIP does not bundle an operating system. On Linux,\nif your unzip tool drops executable bits, run: chmod +x launch.sh godot\n'''


def safe_notice_copy(destination: Path) -> None:
    notices = PROJECT / 'NOTICE'
    required = ['GODOT-LICENSE.txt', 'GODOT-COPYRIGHT.txt', 'MAKEHUMAN-ASSET-LICENSE.md',
                'HERO-PROVENANCE.json', 'RAMA-PRODUCTION-PROVENANCE.json']
    for name in required:
        if not (notices / name).is_file():
            raise ValueError(f'Required package notice is missing: NOTICE/{name}')
    for item in notices.rglob('*'):
        if item.is_symlink():
            raise ValueError('Symlinks are not allowed in package notices')
        if item.is_file():
            payload = item.read_bytes()
            if SECRET_NAME.search(item.name) or SECRET_CONTENT.search(payload):
                raise ValueError('Potential credential marker in package notices')
            target = destination / 'NOTICE' / item.relative_to(notices)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)


def zip_directory(staging: Path, output: Path) -> dict:
    files = sorted(p for p in staging.rglob('*') if p.is_file())
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            name = str(path.relative_to(staging.parent))
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            executable = path.name in {'godot', 'launch.sh'}
            info.external_attr = ((0o100755 if executable else 0o100644) << 16)
            with path.open('rb') as source, archive.open(info, 'w') as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
    expected = {str(p.relative_to(staging.parent)): p for p in files}
    with zipfile.ZipFile(output) as archive:
        if set(archive.namelist()) != set(expected) or len(archive.namelist()) != len(expected):
            raise ValueError('ZIP entry set differs from staging set')
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f'ZIP CRC failure: {bad}')
        for name, source in expected.items():
            with archive.open(name) as stream:
                value = hashlib.sha256()
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    value.update(block)
            if value.hexdigest() != digest(source):
                raise ValueError(f'ZIP payload mismatch: {name}')
    return {**record(output), 'entry_count': len(files), 'all_crc_and_payload_sha256_verified': True}


def package_all(args: argparse.Namespace, build: Path, exported: dict) -> dict:
    if source_state()['sha256'] != exported['source']['sha256']:
        raise ValueError('Runtime sources changed since PCK export; export again before packaging')
    results = {}
    windows_provenance = args.windows_engine.parent / 'godot-windows-provenance.json'
    verified_windows = json.loads(windows_provenance.read_text())
    windows_entry = next(entry for entry in verified_windows['files'] if entry['name'] == args.windows_engine.name)
    if digest(args.windows_engine) != windows_entry['sha256']:
        raise ValueError('Windows engine differs from its independently downloaded provenance')
    for platform in PLATFORMS:
        staging = build / f'yuga-native-{platform}-x86_64'
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        engine = args.linux_engine if platform == 'linux' else args.windows_engine
        shutil.copyfile(engine, staging / ('godot' if platform == 'linux' else 'godot.exe'))
        pack = build / f'yuga-native-{platform}.pck'
        actual_pack = inspect_pack(pack)
        if actual_pack['sha256'] != exported['packs'][platform]['sha256']:
            raise ValueError('PCK changed after export manifest validation')
        shutil.copyfile(pack, staging / 'yuga-native.pck')
        if platform == 'linux':
            launcher = '#!/bin/sh\nset -eu\nPACKAGE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec "$PACKAGE_DIR/godot" --main-pack "$PACKAGE_DIR/yuga-native.pck" "$@"\n'
            (staging / 'launch.sh').write_text(launcher)
            (staging / 'launch.sh').chmod(0o755)
            (staging / 'godot').chmod(0o755)
        else:
            launcher = '@echo off\r\n"%~dp0godot.exe" --main-pack "%~dp0yuga-native.pck" %*\r\n'
            (staging / 'launch.bat').write_bytes(launcher.encode())
        (staging / 'START-HERE.txt').write_text(start_readme(platform), encoding='utf-8')
        safe_notice_copy(staging)
        payloads = {str(p.relative_to(staging)): record(p) for p in sorted(staging.rglob('*')) if p.is_file()}
        manifest = {'schema': 1, 'platform': f'{platform}-x86_64', 'godot_version': exported['godot_version'],
                    'packaging': 'official-full-engine-with-exported-pck', 'git': exported['git'],
                    'runtime_source': exported['source'], 'payloads': payloads,
                    'pck': actual_pack, 'execution_status': 'not_executed_by_packager',
                    'windows_engine_provenance': verified_windows if platform == 'windows' else None}
        json_write(staging / 'PACKAGE-MANIFEST.json', manifest)
        archive = build / f'yuga-native-{platform}-x86_64.zip'
        results[platform] = {'filename': archive.name, **zip_directory(staging, archive),
                             'engine': record(engine), 'pck': {k: actual_pack[k] for k in ['bytes', 'sha256', 'entry_count']},
                             'execution_status': 'not_executed_by_packager'}
    aggregate = {'schema': 1, 'kind': 'native-portable-packages', 'git': exported['git'],
                 'runtime_source_sha256': exported['source']['sha256'], 'packages': results,
                 'packaging_script': record(Path(__file__)),
                 'limits': ['Archive/PCK validation is not runtime acceptance.', 'Windows has not been executed here.']}
    json_write(build / 'native-package-manifest.json', aggregate)
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--linux-engine', type=Path, default=DEFAULT_LINUX)
    parser.add_argument('--windows-engine', type=Path, default=DEFAULT_WINDOWS)
    parser.add_argument('--build-dir', type=Path, default=PROJECT / 'build')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--export-only', action='store_true')
    modes.add_argument('--package-only', action='store_true')
    args = parser.parse_args()
    build = args.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=True)
    if args.package_only:
        exported = json.loads((build / 'native-export-manifest.json').read_text())
    else:
        exported = export_all(args, build)
    if args.export_only:
        print(json.dumps({'exported': {k: {f: v[f] for f in ['sha256', 'bytes', 'entry_count']} for k, v in exported['packs'].items()}}))
    else:
        result = package_all(args, build, exported)
        print(json.dumps({'packages': result['packages']}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'Native packaging failed: {type(error).__name__}: {error}', file=sys.stderr)
        raise SystemExit(1)
