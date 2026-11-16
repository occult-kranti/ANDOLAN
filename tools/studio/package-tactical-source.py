#!/usr/bin/env python3
"""Archive a frozen native source closure and separately identified delivery docs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot, workspace, output = args.snapshot.resolve(), args.workspace.resolve(), args.output.resolve()
    if output.exists():
        raise ValueError('Use a fresh archive path; earlier artifacts are preserved.')
    manifest = json.loads((snapshot / 'SNAPSHOT-MANIFEST.json').read_text())
    excluded = set(manifest['closure']['groups']['import_cache'])
    selected = {p: snapshot / p for p in manifest['files'] if p not in excluded}
    for name in ['SOURCE_SNAPSHOT.json', 'SNAPSHOT-MANIFEST.json']:
        selected[name] = snapshot / name
    extras = []
    for folder in ['games/yuga-native/docs/tactical', 'games/yuga-native/art/tactical']:
        for path in (workspace / folder).rglob('*'):
            if not path.is_file() or any(part.endswith('-user') for part in path.parts):
                continue
            if path.suffix not in ['.md', '.json', '.html', '.txt', '.tsx', '.ts', '.org']:
                continue
            relative = path.relative_to(workspace).as_posix()
            if relative not in selected:
                selected[relative] = path
                extras.append(relative)
    media_groups = {
        'games/yuga-native/docs/tactical/finish2/final-visual-r1': '*.png',
        'games/yuga-native/docs/tactical/finish2/final-motion-r1': '*.mp4',
        'games/yuga-native/docs/tactical/evidence/weapon-r4': 'surya-*.png',
        'games/yuga-native/docs/tactical/finish2/raea': 'surya-cpu-orbit-r3.mp4',
    }
    for folder, pattern in media_groups.items():
        for path in (workspace / folder).glob(pattern):
            relative = path.relative_to(workspace).as_posix()
            selected[relative] = path
            extras.append(relative)
    for relative in ['tools/studio/package-tactical-source.py']:
        selected[relative] = workspace / relative
        extras.append(relative)
    records = {}
    output.parent.mkdir(parents=True, exist_ok=True)
    readme = '''# YUGA Sanctum native source and art

Open games/yuga-native/project.godot in Godot 4.6.3, import, and run.
Command: godot --headless --path games/yuga-native --editor --import --quit
Then: godot --path games/yuga-native

Start at games/yuga-native/docs/tactical/finish2/DELIVERY.md and README.md.
The gallery is games/yuga-native/docs/tactical/PREVIEW.html. Local media is included.
Native runtime source is frozen; delivery documentation is a later identified supplement.
SOURCE_SNAPSHOT.json and SNAPSHOT-MANIFEST.json retain the source identity.
The snapshot's imported cache is omitted; Godot regenerates it on import.
Original provenance inputs, notices, tools, tests and editable Blender sources are retained.
Godot/Blender/Raea binaries are not included. Raea is separate internal rendering tooling.
Casual is local 5v5 first-to-13; online and Ranked are not implemented.
'''
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        archive.writestr('SOURCE-AND-ART.md', readme)
        for relative, path in sorted(selected.items()):
            digest = sha(path)
            expected = manifest['files'].get(relative)
            if expected and digest != expected['sha256']:
                raise ValueError('Frozen source mismatch: ' + relative)
            records[relative] = {'bytes': path.stat().st_size, 'sha256': digest}
            archive.write(path, relative)
        archive.writestr('SOURCE-KIT-MANIFEST.json', json.dumps({
            'runtime_source_sha256': manifest['closure']['runtime_source_sha256'],
            'omitted_group': 'regenerable import_cache',
            'delivery_supplements': sorted(extras), 'files': records,
        }, indent=2) + '\n')
    with zipfile.ZipFile(output) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise ValueError('Archive CRC failed: ' + corrupt)
    receipt = {'complete': True, 'file': str(output), 'bytes': output.stat().st_size,
               'sha256': sha(output), 'files': len(records) + 2, 'crc_pass': True,
               'runtime_source_sha256': manifest['closure']['runtime_source_sha256'],
               'scope': 'Frozen source closure, editable art, notices and identified delivery supplement; no engine binaries or import cache.'}
    output.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
