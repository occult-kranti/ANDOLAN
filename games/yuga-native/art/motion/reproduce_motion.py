#!/usr/bin/env python3
"""Reproduce a licensed, isolated TPS-to-Rama motion adaptation with Godot4.6.3."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
SOURCE_SHA = '16b783ec2e19245d034326d401796b9bd2635de75f4e38917854316abeee4f9c'

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference-project', required=True, type=Path)
    p.add_argument('--work-dir', required=True, type=Path)
    p.add_argument('--target', type=Path, default=NATIVE / 'assets/heroes/rama-production.glb')
    p.add_argument('--target-sha256')
    p.add_argument('--output', type=Path, default=HERE)
    p.add_argument('--library', type=Path, default=NATIVE / 'assets/animations/tps_rama_motion_library.tres')
    p.add_argument('--full-body-study', action='store_true')
    p.add_argument('--godot', default='godot')
    a = p.parse_args()
    work, reference, target = a.work_dir.resolve(), a.reference_project.resolve(), a.target.resolve()
    if work == NATIVE or NATIVE in work.parents or work == reference or reference in work.parents:
        raise ValueError('Use a separate work directory outside both source projects.')
    if sha(reference / 'player/model/player.glb') != SOURCE_SHA:
        raise ValueError('Source differs from the pinned licensed model.')
    if a.target_sha256 and sha(target) != a.target_sha256:
        raise ValueError('Target differs from the requested exact hash.')
    if not subprocess.check_output([a.godot, '--version'], text=True).strip().startswith('4.6.3.stable.'):
        raise ValueError('Use pinned Godot4.6.3; review engine changes before regeneration.')
    project = work / 'godot'
    project.mkdir(parents=True, exist_ok=True)
    for folder in ('model', 'textures'):
        shutil.copytree(reference / 'player' / folder, project / 'player' / folder, dirs_exist_ok=True)
    imp = project / 'player/model/player.glb.import'
    settings = imp.read_text().replace('nodes/use_name_suffixes=true', 'nodes/use_name_suffixes=false')
    settings = settings.replace('animation/fps=15', 'animation/fps=24')
    if 'nodes/use_name_suffixes=false' not in settings or 'animation/fps=24' not in settings:
        raise ValueError('Review changed source importer before proceeding.')
    imp.write_text(settings)
    (project / 'target').mkdir(exist_ok=True)
    copied_target = project / 'target/rama.glb'
    if target != copied_target: shutil.copyfile(target, copied_target)
    shutil.copyfile(HERE / 'bake_tps_motion.gd', project / 'bake_tps_motion.gd')
    (project / 'project.godot').write_text('''config_version=5
[application]
config/name="YUGA isolated licensed motion bake"
config/features=PackedStringArray("4.6", "GL Compatibility")
[rendering]
renderer/rendering_method="gl_compatibility"
[threading]
worker_pool/max_threads=2
''')
    env = os.environ.copy()
    for variable, folder in [('XDG_DATA_HOME','data'), ('XDG_CONFIG_HOME','config'), ('XDG_CACHE_HOME','cache')]:
        env[variable] = str(work / 'xdg' / folder)
        Path(env[variable]).mkdir(parents=True, exist_ok=True)
    bake = [a.godot, '--headless', '--path', str(project), '--script', 'res://bake_tps_motion.gd', '--',
            '--output=' + str(a.output.resolve()), '--library=' + str(a.library.resolve())]
    if a.full_body_study: bake.append('--full-body-study')
    commands = [([a.godot, '--headless', '--path', str(project), '--editor', '--import', '--quit'], 'import.log'), (bake, 'bake.log')]
    for command, name in commands:
        log_path = work / name
        with log_path.open('w') as log:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        content = log_path.read_text()
        if result.returncode or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            raise RuntimeError('Import/bake failed; inspect ' + str(log_path))
    manifest = json.loads((a.output / 'motion-retarget-manifest.json').read_text())
    if not manifest['passed'] or sha(a.library) != manifest['library']['sha256']:
        raise RuntimeError('Generated library differs from the passing bake manifest.')
    print(json.dumps({'source_sha256': SOURCE_SHA, 'target_sha256': sha(target), 'library_sha256': sha(a.library),
                      'bake_checks': len(manifest['checks']), 'full_body_study': a.full_body_study,
                      'rendered': False, 'runtime_promoted': False}))

if __name__ == '__main__': main()
