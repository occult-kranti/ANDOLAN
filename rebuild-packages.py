#!/usr/bin/env python3
"""Reassemble and verify the two exact Hanuman native packages."""
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 rebuild-packages.py FRESH_OUTPUT_DIRECTORY")
    destination = Path(sys.argv[1])
    destination.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((HERE / 'manifest.json').read_text())
    for package in manifest['packages']:
        assembled = sha256()
        pending = destination / (package['file'] + '.partial')
        with pending.open('xb') as output:
            for piece in package['parts']:
                part = HERE / piece['file']
                digest = sha256()
                with part.open('rb') as stream:
                    while data := stream.read(1024 * 1024):
                        digest.update(data)
                        assembled.update(data)
                        output.write(data)
                if part.stat().st_size != piece['bytes'] or digest.hexdigest() != piece['sha256']:
                    raise ValueError(f"Part hash or length mismatch: {part.name}")
        if pending.stat().st_size != package['bytes'] or assembled.hexdigest() != package['sha256']:
            raise ValueError(f"Incorrect assembled package: {package['file']}")
        pending.rename(destination / package['file'])
        print(f"{package['sha256']}  {package['file']}")


if __name__ == '__main__':
    main()
