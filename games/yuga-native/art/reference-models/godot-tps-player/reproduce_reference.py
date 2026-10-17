#!/usr/bin/env python3
"""Fetch the exact licensed reference selection and inspect it in an isolated project.

Upstream GDScript and player.tscn are retained as study text but never executed.
Only the original GLB/materials/textures plus this folder's own inspector enter
an isolated Godot project. No YUGA runtime files are modified.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--godot', default='godot')
    parser.add_argument('--download-only', action='store_true')
    args = parser.parse_args()
    destination = args.destination.resolve()
    native_project = HERE.parents[2]
    if destination == native_project or native_project in destination.parents:
        raise ValueError('Use a task-local destination outside the YUGA native project.')
    manifest = json.loads((HERE / 'source-manifest.json').read_text())
    prefix = 'https://raw.githubusercontent.com/godotengine/tps-demo/' + manifest['commit'] + '/'
    files = manifest['source_files']
    if sum(entry['bytes'] for entry in files) > manifest['download_limits']['total_bytes']:
        raise ValueError('Selected download exceeds its recorded bound.')
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for entry in files:
        relative = PurePosixPath(entry['path'])
        if relative.is_absolute() or '..' in relative.parts or not entry['url'].startswith(prefix):
            raise ValueError('Unsafe manifest path or URL.')
        path = destination / 'source' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or sha(path) != entry['sha256']:
            request = urllib.request.Request(entry['url'], headers={'User-Agent': 'YUGA-licensed-reference-inspection'})
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read(manifest['download_limits']['per_file_bytes'] + 1)
            if len(payload) != entry['bytes'] or hashlib.sha256(payload).hexdigest() != entry['sha256']:
                raise ValueError('Downloaded size/hash differs from the pinned manifest: ' + entry['path'])
            blob = hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
            if blob != entry['git_blob_sha1']:
                raise ValueError('Downloaded Git blob differs from pinned tree: ' + entry['path'])
            path.write_bytes(payload)
        records.append({'path': entry['path'], 'bytes': path.stat().st_size, 'sha256': sha(path)})
    (destination / 'verified-downloads.json').write_text(json.dumps(records, indent=2) + '\n')
    if args.download_only:
        print(json.dumps({'downloaded_or_cached': len(records), 'bytes': sum(x['bytes'] for x in records)}))
        return
    project = destination / 'godot'
    project.mkdir(exist_ok=True)
    for entry in files:
        if entry['path'].startswith(('player/model/', 'player/textures/')):
            target = project / entry['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(destination / 'source' / entry['path'], target)
    # Preserve both authored Cannon_Charge and Cannon_Charge-cycle names.
    # Godot 4.6 otherwise logs a duplicate-name error while removing -cycle.
    import_path = project / 'player/model/player.glb.import'
    original_import = import_path.read_text()
    adjusted_import = original_import.replace('nodes/use_name_suffixes=true', 'nodes/use_name_suffixes=false')
    if adjusted_import == original_import:
        raise ValueError('Pinned import setting changed; review the isolated suffix adaptation.')
    import_path.write_text(adjusted_import)
    (destination / 'import-adjustments.json').write_text(json.dumps({
        'source_glb_modified': False, 'isolated_project_only': True,
        'setting': 'nodes/use_name_suffixes', 'upstream_value': True, 'isolated_value': False,
        'reason': 'Keep authored names distinct: Cannon_Charge and Cannon_Charge-cycle.',
        'original_import_sha256': hashlib.sha256(original_import.encode()).hexdigest(),
        'adjusted_import_sha256': hashlib.sha256(adjusted_import.encode()).hexdigest()
    }, indent=2) + '\n')
    (project / 'project.godot').write_text('''config_version=5
[application]
config/name="Isolated Official TPS Character Inspection"
config/features=PackedStringArray("4.6", "GL Compatibility")
[rendering]
renderer/rendering_method="gl_compatibility"
[threading]
worker_pool/max_threads=2
''')
    shutil.copyfile(HERE / 'inspect_reference.gd', project / 'inspect_reference.gd')
    env = os.environ.copy()
    for variable, folder in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        env[variable] = str(destination / 'xdg' / folder)
        Path(env[variable]).mkdir(parents=True, exist_ok=True)
    commands = [
        ([args.godot, '--headless', '--path', str(project), '--editor', '--import', '--quit'], 'import-reproduced.log'),
        ([args.godot, '--headless', '--path', str(project), '--script', 'res://inspect_reference.gd', '--', '--output=' + str(destination / 'godot-inspection.json')], 'inspection-reproduced.log')]
    for command, filename in commands:
        with (destination / filename).open('w') as log:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        text = (destination / filename).read_text()
        if result.returncode or 'SCRIPT ERROR:' in text or '\nERROR:' in text:
            raise RuntimeError('Reference inspection failed; inspect ' + str(destination / filename))
    result = json.loads((destination / 'godot-inspection.json').read_text())
    print(json.dumps({'skeletons': len(result['skeletons']), 'bones': sum(x['bone_count'] for x in result['skeletons']),
                      'animation_resources_including_helpers': len(result['animations']), 'meshes': len(result['meshes']),
                      'finite_bone_samples': result['finite_samples'], 'nonfinite_bone_samples': result['nonfinite_samples'],
                      'rendered': False, 'retarget_applied': False}))


if __name__ == '__main__':
    main()
