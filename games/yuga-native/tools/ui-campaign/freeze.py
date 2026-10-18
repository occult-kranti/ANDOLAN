#!/usr/bin/env python3
"""Copy a lean, source-pinned UI runtime snapshot with existing imports; no engine run."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[2])
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source, output = args.source.resolve(), args.output.resolve()
if not args.output.is_absolute() or output.exists() or source == output or source in output.parents:
    parser.error('Use a fresh absolute snapshot directory outside the source project.')
output.mkdir(parents=True)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

files = [source / 'project.godot', source / 'export_presets.cfg']
for directory in ['scripts', 'scenes', 'shaders', 'assets', 'NOTICE', 'tools/ui-campaign']:
    files += sorted(path for path in (source / directory).rglob('*') if path.is_file() and '__pycache__' not in path.parts)
files += sorted(path for path in (source / 'tests').iterdir() if path.is_file())
for tool in ['tools/run-visual-checks.py', 'tools/run-authoring-checks.py']:
    if (source / tool).is_file():
        files.append(source / tool)
if (source / 'art/world/confluence-map.json').is_file():
    files.append(source / 'art/world/confluence-map.json')
pins = {}
for file in files:
    relative = file.relative_to(source)
    target = output / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    pins[str(relative)] = digest(file)
    shutil.copy2(file, target)
    if digest(target) != pins[str(relative)]:
        raise SystemExit('Copy verification failed: ' + str(relative))
# Copy, rather than link, retained engine caches to keep the snapshot independent.
imports = source / '.godot/imported'
if not imports.is_dir():
    raise SystemExit('Existing import cache missing; ask the capture owner to prepare it.')
shutil.copytree(imports, output / '.godot/imported')
for name in ['global_script_class_cache.cfg', 'uid_cache.bin', 'extension_list.cfg']:
    file = source / '.godot' / name
    if file.is_file(): shutil.copy2(file, output / '.godot' / name)
if any(digest(source / relative) != checksum for relative, checksum in pins.items()):
    raise SystemExit('Source changed during snapshot; preserve this rejected snapshot and retry after freeze.')
cache_pins = {str(path.relative_to(output)):digest(path) for path in (output / '.godot/imported').rglob('*') if path.is_file()}
receipt = {'source':str(source), 'source_sha256':pins, 'existing_import_sha256':cache_pins,
           'scope':'Exact source copy plus existing imported cache. This does not assert cache freshness against changed raw assets and does not run import/render.'}
(output / 'ui-source-freeze.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'snapshot':str(output),'source_files':len(pins),'import_cache_files':len(cache_pins)}))
