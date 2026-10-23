#!/usr/bin/env python3
"""Preserve this one inactive mutation-fixture directory; never deletes sources."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import tarfile

SOURCE = Path('/workspace/scratch/hero-family-independent-oct23')
BLOCK = 1048576


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--manifest-copy', type=Path, required=True)
    args = parser.parse_args()
    archive_path = args.archive.resolve()
    if archive_path.exists() or archive_path.is_relative_to(SOURCE):
        raise ValueError('fresh archive outside fixture directory required')
    objects = {}
    rows = []
    for path in sorted(SOURCE.rglob('*.glb')):
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
            raise ValueError('only regular singly linked fixture GLBs accepted')
        stat = path.stat()
        data = path.read_bytes()
        if len(data) < 12:
            raise ValueError('unexpected short fixture')
        chunks = []
        offset = 12
        while offset + 8 <= len(data):
            header = data[offset:offset + 8]
            length, kind = struct.unpack('<II', header)
            payload = data[offset + 8:min(offset + 8 + length, len(data))]
            blocks = []
            for start in range(0, len(payload), BLOCK):
                block = payload[start:start + BLOCK]
                digest = hashlib.sha256(block).hexdigest()
                if digest in objects and objects[digest] != block:
                    raise ValueError('object collision')
                objects.setdefault(digest, block)
                blocks.append({'sha256': digest, 'bytes': len(block)})
            chunks.append({'headerHex': header.hex(), 'type': hex(kind), 'declaredPayloadBytes': length,
                           'actualPayloadBytes': len(payload), 'payloadSha256': hashlib.sha256(payload).hexdigest(), 'blocks': blocks})
            offset += 8 + len(payload)
        rows.append({'path': str(path.relative_to(SOURCE)), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                     'mode': stat.st_mode & 0o777, 'inodeAtCapture': stat.st_ino, 'mtimeNsAtCapture': stat.st_mtime_ns,
                     'containerHeaderHex': data[:12].hex(), 'chunks': chunks, 'trailingHex': data[offset:].hex()})
    if len(rows) != 16:
        raise ValueError('expected exactly the 16 reviewed mutation fixtures')
    manifest = {'schema': 1, 'sourceRoot': str(SOURCE), 'sourceCommit': 'db1e3291abd78ec3fb8bf8496e3d098dd597150c',
                'preservation': 'Exact raw container header, chunk headers/padding/payload blocks and whole-file SHA-256; no regeneration',
                'blockBytes': BLOCK, 'files': rows, 'uniqueObjects': len(objects), 'uniqueObjectBytes': sum(len(v) for v in objects.values())}
    encoded = (json.dumps(manifest, indent=2) + '\n').encode()
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with archive_path.open('xb') as raw, tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        def add(name, payload):
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            info.mode = 0o600
            info.mtime = 0
            archive.addfile(info, io.BytesIO(payload))
        add('manifest.json', encoded)
        add('restore.py', Path(__file__).with_name('restore.py').read_bytes())
        add('README.txt', b'Exact inactive YUGA mutation fixtures. Run: python3 restore.py --archive ARCHIVE.tar --output FRESH_DIRECTORY\nNo GLB normalization or recipe regeneration is required. manifest.json binds every original path and byte hash.\n')
        for digest, payload in sorted(objects.items()):
            add('objects/' + digest, payload)
    args.manifest_copy.write_bytes(encoded)
    print(json.dumps({'archive': str(archive_path), 'files': len(rows), 'sourceBytes': sum(r['bytes'] for r in rows),
                      'objects': len(objects), 'objectBytes': manifest['uniqueObjectBytes'], 'archiveBytes': archive_path.stat().st_size,
                      'archiveSha256': hashlib.sha256(archive_path.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
