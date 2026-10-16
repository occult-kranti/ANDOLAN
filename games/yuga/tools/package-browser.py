#!/usr/bin/env python3
"""Package the freshly built browser beta; invoke with npm run yuga:package."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import zipfile

root = Path(__file__).resolve().parents[3]
build = root / 'dist/yuga'
files = sorted(path for path in build.rglob('*') if path.is_file())
assert (build / 'index.html').is_file()
assert all(not path.is_symlink() for path in files), 'Build must contain real files, not symlinks'
expected = []
for name in ['hero-assets.json', 'unit-assets.json']:
    expected.extend(json.loads((root / 'games/yuga/art' / name).read_text())['models'])
actual_models = sorted(sha256(path.read_bytes()).hexdigest() for path in build.rglob('*.glb'))
assert actual_models == sorted(model['sha256'] for model in expected), 'Built models must match both source manifests'
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
manifest = {'repository_head': revision, 'worktree_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root)), 'protocol': 2, 'packed_at': datetime.now(timezone.utc).isoformat(), 'scope': 'Static browser beta with local bot practice; public multiplayer requires a separate secure arena server.', 'files': []}
for path in files:
    content = path.read_bytes()
    manifest['files'].append({'path': path.relative_to(build).as_posix(), 'bytes': len(content), 'sha256': sha256(content).hexdigest()})
instructions = '''YUGA: Confluence — browser beta

Extract the entire archive. Keep index.html and the assets directory together.
Serve the extracted directory over HTTP; opening index.html directly as a file
does not reliably load the external 3D models.

For example, from the extracted directory:
    python3 -m http.server 8080 --bind 127.0.0.1
Then open http://127.0.0.1:8080/ in a modern browser and choose Play with bots.
On Windows the equivalent command may start with py -m http.server.

Move: WASD / arrows. Aim: mouse or IJKL. Fire: click / F.
Abilities: Q E R. Jump: Space. Target lock: T / right click.
Upgrades near spawn: B. Settings / release cursor: Escape.
Settings includes day/night cycle, fixed daylight/night and reduced motion.
The roster offers optional practice goals and a guide for every hero.

Practice runs locally. Online team match needs a reachable YUGA protocol-2
HTTPS/WSS arena server; this archive does not create or host that server.
All fourteen heroes are available. Graphics are an original browser prototype.
Third-party notices are included in the build.

Source: https://github.com/occult-kranti/ANDOLAN/tree/game/yuga-confluence
Build identity and file hashes: BUILD_INFO.json
'''
destination = root / 'dist/yuga-confluence-browser-beta.zip'
temporary = destination.with_suffix('.zip.tmp')
with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in files:
        archive.write(path, path.relative_to(build).as_posix())
    archive.writestr('START_HERE.txt', instructions)
    archive.writestr('BUILD_INFO.json', json.dumps(manifest, indent=2) + '\n')
with zipfile.ZipFile(temporary) as archive:
    assert archive.testzip() is None
    for entry in manifest['files']:
        assert sha256(archive.read(entry['path'])).hexdigest() == entry['sha256']
temporary.replace(destination)
print(json.dumps({'archive': str(destination), 'bytes': destination.stat().st_size, 'sha256': sha256(destination.read_bytes()).hexdigest(), 'repository_head': revision, 'models': len(expected), 'file_integrity': 'passed'}))
