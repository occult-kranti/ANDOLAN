#!/usr/bin/env python3
"""Install the native art baseline Blender 4.3.2 outside the source checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import urllib.request

URL = 'https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz'
SHA256 = '4da1c956673c0485e63054e563ee69198cc8f80d8157dd7592dffc8a6a5592e6'
CHECKSUM_SOURCE = 'https://download.blender.org/release/Blender4.3/blender-4.3.2.sha256'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=Path('/workspaces/tooling/blender'))
    args = parser.parse_args()
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise RuntimeError('This qualified build is for Linux x86_64.')
    root = args.destination.resolve()
    project = Path(__file__).resolve().parents[2]
    if root.is_relative_to(project):
        raise ValueError('Choose a destination outside the source checkout.')
    root.mkdir(parents=True, exist_ok=True)
    archive = root / URL.rsplit('/', 1)[-1]
    if not archive.exists():
        with urllib.request.urlopen(URL, timeout=90) as source, archive.open('xb') as target:
            shutil.copyfileobj(source, target)
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != SHA256:
        raise ValueError('Blender official archive differs from the pinned release checksum.')
    with tarfile.open(archive, 'r:xz') as bundle:
        bundle.extractall(root, filter='data')
    binary = root / 'blender-4.3.2-linux-x64/blender'
    run = subprocess.run([str(binary), '--background', '--factory-startup', '--python-expr',
                          'import bpy; print("STUDIO_BLENDER_READY", bpy.app.version_string)'],
                         capture_output=True, text=True, timeout=60)
    (root / 'blender-startup.log').write_text(run.stdout + run.stderr)
    if run.returncode or 'STUDIO_BLENDER_READY 4.3.2' not in run.stdout:
        raise RuntimeError('Blender factory-startup check failed; inspect blender-startup.log.')
    result = {'passed': True, 'url': URL, 'sha256': actual, 'bytes': archive.stat().st_size,
              'checksumSource': CHECKSUM_SOURCE, 'binary': str(binary),
              'scope': 'Pinned official archive checksum and background factory-startup; game asset export compatibility remains a separate check.'}
    (root / 'blender-download.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
