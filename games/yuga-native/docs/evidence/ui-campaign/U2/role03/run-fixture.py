#!/usr/bin/env python3
"""Run initial boot/recovery fixtures without importing the product world."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--engine', default='godot')
args = parser.parse_args()
product = Path(__file__).resolve().parents[5]
output = args.output.resolve()
if output == product or product in output.parents:
    raise SystemExit('Fixture output must be outside the product.')
output.mkdir(parents=True, exist_ok=False)
sources = ['scripts/boot.gd', 'scenes/boot.tscn', 'scripts/scene_transition.gd', 'scripts/hero_ui_theme.gd', 'tests/ui_boot_cases.gd']
sources += [str(path.relative_to(product)) for path in (product / 'assets/fonts').glob('*') if path.is_file()]
sources += [str(path.relative_to(product)) for path in (product / '.godot/imported').glob('*.ttf-*') if path.is_file()]
hashes = {path: hashlib.sha256((product / path).read_bytes()).hexdigest() for path in sources + ['project.godot']}
commands = []
for mode in ['lifecycle', 'quit']:
    stage = output / mode
    stage.mkdir()
    for relative in sources:
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(product / relative, target)
    (stage / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="Boot fixtures"\nrun/main_scene="res://scenes/boot.tscn"\n[test]\nscene_transition_fixture=true\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    command = [args.engine, '--headless', '--path', str(stage), '--script', 'res://tests/ui_boot_cases.gd', '--', '--autostart', '--smoke', '--report=' + str(stage / 'report.json')]
    if mode == 'quit':
        command += ['--quit-path']
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    log = result.stdout + result.stderr
    (stage / 'run.log').write_text(log)
    commands.append({'mode':mode, 'command':command, 'exit_code':result.returncode})
    print(log, end='')
    if result.returncode or any(marker in log for marker in ['ERROR:', 'WARNING:', 'FAIL ']):
        raise SystemExit('Boot fixture failed: ' + mode)
    if mode == 'lifecycle':
        report = json.loads((stage / 'report.json').read_text())
        if report['failed'] or report['passed'] < 29:
            raise SystemExit('Boot lifecycle did not execute the required checks.')
    elif 'YUGA_BOOT_QUIT_ACTION_EXECUTED' not in log:
        raise SystemExit('The Quit action did not execute.')
(output / 'receipt.json').write_text(json.dumps({'source_sha256':hashes, 'runs':commands, 'scope':'Small native Control/PackedScene fixtures; no product-world import, render or performance acceptance.'}, indent=2) + '\n')
