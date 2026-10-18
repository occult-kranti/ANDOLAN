#!/usr/bin/env python3
"""Stage tiny scene fixtures outside the product and retain exact-source results."""
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
if product == output or product in output.parents:
    raise SystemExit('Fixture output must be outside the product project.')
output.mkdir(parents=True, exist_ok=False)
sources = ['scripts/scene_transition.gd', 'scripts/hero_ui_theme.gd', 'tests/scene_transition_cases.gd']
sources += [str(path.relative_to(product)) for path in (product / 'assets/fonts').glob('*') if path.is_file()]
sources += [str(path.relative_to(product)) for path in (product / '.godot/imported').glob('*.ttf-*') if path.is_file()]
hashes = {}
for relative in sources:
    source = product / relative
    target = output / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    hashes[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
(output / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="Scene transition fixtures"\n[test]\nscene_transition_fixture=true\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
command = [args.engine, '--headless', '--path', str(output), '--script', 'res://tests/scene_transition_cases.gd', '--', '--report=' + str(output / 'report.json')]
result = subprocess.run(command, capture_output=True, text=True, timeout=90)
log = result.stdout + result.stderr
(output / 'run.log').write_text(log)
receipt = {'command': command, 'exit_code': result.returncode, 'source_sha256': hashes, 'expected_errors': ['res://scenes/combat_film.tscn:2 - Parse Error: Unexpected end of file.', 'Failed loading resource: res://scenes/combat_film.tscn.'], 'scope': 'Small actual threaded PackedScene fixture project, headless; no heavy product imports/render or world performance claim.'}
(output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(log, end='')
if result.returncode:
    raise SystemExit(result.returncode)
if 'ObjectDB instances leaked' in log or 'SCRIPT ERROR' in log:
    raise SystemExit('Unexpected engine error/leak; inspect run.log.')
errors = [line.removeprefix('ERROR: ') for line in log.splitlines() if line.startswith('ERROR: ')]
if sorted(errors) != sorted(receipt['expected_errors']):
    raise SystemExit('Unexpected engine errors or missing malformed-scene counterexample; inspect run.log.')
report = json.loads((output / 'report.json').read_text())
if report['failed'] or not report['passed']:
    raise SystemExit('The suite did not complete successfully.')
