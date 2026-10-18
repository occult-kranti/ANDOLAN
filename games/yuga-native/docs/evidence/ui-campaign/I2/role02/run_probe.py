#!/usr/bin/env python3
"""Build a tiny exact-source 2D fixture; never imports assets or exports a pack."""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ENGINE_SHA = 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
FONTS = {
    'NotoSans-Regular.ttf': '89c3c497f618fdaa0b2d1e98fef93582f28c71debd2c4a8cdf41f190ced2909d',
    'NotoSerif-Regular.ttf': '9d7583b7dc9e812afd32a14280c5cac3160012efe50c8d08938f4fea266ff67f',
    'DejaVuSans.ttf': '57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e',
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def record(path):
    return {'bytes': path.stat().st_size, 'sha256': sha(path)}


def safe(root, relative):
    path = root / relative
    if (Path(relative).is_absolute() or '..' in Path(relative).parts or '\\' in relative
            or path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file()):
        raise ValueError('Missing or unsafe frozen file: ' + relative)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', required=True, type=Path)
    parser.add_argument('--freeze-manifest-sha256', required=True)
    parser.add_argument('--workspace', required=True, type=Path, help='Fresh tiny fixture, never a full project copy')
    parser.add_argument('--godot', type=Path, default=Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64'))
    parser.add_argument('--run', action='store_true', help='Only after final I1 source and lane authorization')
    args = parser.parse_args()
    frozen = args.freeze.resolve()
    manifest_path = safe(frozen, 'ui-source-freeze.json')
    if sha(manifest_path) != args.freeze_manifest_sha256:
        raise ValueError('Freeze manifest differs from authorized identity')
    manifest = json.loads(manifest_path.read_text())
    pins = {**manifest['source_sha256'], **manifest['existing_import_sha256']}
    files = ['scripts/hero_ui_theme.gd']
    for filename, expected in FONTS.items():
        source = 'assets/fonts/' + filename
        raw = safe(frozen, source)
        if sha(raw) != expected:
            raise ValueError('Authored raw font differs: ' + filename)
        descriptor = safe(frozen, source + '.import')
        config = configparser.ConfigParser(interpolation=None, strict=True, delimiters=('=',))
        config.optionxform = str
        config.read_string(descriptor.read_text())
        if config.defaults() or config['remap']['importer'] != '"font_data_dynamic"' or config['remap']['type'] != '"FontFile"':
            raise ValueError('Unexpected font importer: ' + filename)
        target = json.loads(config['remap']['path']).removeprefix('res://')
        if re.fullmatch(r'\.godot/imported/' + re.escape(filename) + r'-[0-9a-f]{32}\.fontdata', target) is None:
            raise ValueError('Unexpected font cache target: ' + filename)
        if (config['deps']['source_file'] != json.dumps('res://' + source)
                or json.loads(config['deps']['dest_files']) != ['res://' + target]):
            raise ValueError('Font source/destination binding differs: ' + filename)
        files.extend([source, source + '.import', target])
    sources = {}
    for relative in files:
        source = safe(frozen, relative)
        sources[relative] = record(source)
        if sources[relative]['sha256'] != pins.get(relative):
            raise ValueError('Frozen file pin differs: ' + relative)
    work = args.workspace.resolve()
    work.mkdir(parents=True, exist_ok=False)
    project = work / 'project'
    project.mkdir()
    for relative in files:
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(frozen / relative, destination)
    shutil.copyfile(HERE / 'ownership_probe.gd', project / 'ownership_probe.gd')
    (project / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="I2 ownership fixture"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    contract = {
        'task': 'I2-02', 'freeze': str(frozen), 'freeze_manifest': record(manifest_path),
        'sources': sources, 'raw_font_sha256': FONTS,
        'probe': record(HERE / 'ownership_probe.gd'), 'runner': record(Path(__file__)),
        'copy_scope': 'Exact shared theme, three raw fonts/descriptors/imported FontFile payloads; tiny generated 2D fixture. No world or GLB.',
    }
    (project / 'contract.json').write_text(json.dumps(contract, indent=2) + '\n')
    receipt = {'prepared': True, 'executed': False, 'contract': contract,
               'workspace': str(work), 'copied_bytes': sum(item['bytes'] for item in sources.values())}
    if args.run:
        engine = args.godot.resolve()
        if sha(engine) != ENGINE_SHA:
            raise ValueError('Unqualified engine bytes')
        env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
                   I2_OWNERSHIP_OUTPUT=str(work / 'runtime.json'), GODOT_SILENCE_ROOT_WARNING='1')
        for variable in ('XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME'):
            env[variable] = str(work / variable.lower())
            Path(env[variable]).mkdir()
        command = ['taskset', '-c', '3', str(engine), '--headless', '--path', str(project),
                   '--script', 'res://ownership_probe.gd', '--audio-driver', 'Dummy']
        start = time.monotonic()
        with (work / 'engine.log').open('w') as log:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        log_text = (work / 'engine.log').read_text()
        receipt.update(executed=True, command=command, engine=record(engine), exit_code=result.returncode,
                       duration_seconds=time.monotonic()-start, log=record(work / 'engine.log'))
        receipt['source_and_fixture_unchanged'] = all(sha(frozen / relative) == value['sha256']
            and sha(project / relative) == value['sha256'] for relative, value in sources.items())
        if (work / 'runtime.json').is_file():
            runtime = json.loads((work / 'runtime.json').read_text())
            receipt['runtime_report'] = record(work / 'runtime.json')
            receipt['checks'] = len(runtime['checks'])
            receipt['passed'] = (result.returncode == 0 and runtime['passed']
                and receipt['source_and_fixture_unchanged']
                and not any(token in log_text for token in ('SCRIPT ERROR:', 'ERROR:', 'WARNING:')))
        else:
            receipt['passed'] = False
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({key: receipt[key] for key in ('prepared', 'executed', 'workspace', 'copied_bytes', 'passed', 'checks') if key in receipt}))
    return 0 if not args.run or receipt.get('passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
