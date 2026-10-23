#!/usr/bin/env python3
"""Restore exact retained GLB mutation bytes from the content-addressed TAR.

No extraction of arbitrary member paths, JSON regeneration or GLB rewriting.
Only a fresh output directory is accepted. Requires Python standard library.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', help='Optional exact original relative path')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError('fresh output directory required')
    restored = []
    checked = set()
    with tarfile.open(args.archive, 'r:') as archive:
        members = archive.getmembers()
        if len({member.name for member in members}) != len(members) or any(not member.isfile() for member in members):
            raise ValueError('archive contains duplicate names or non-file members')
        manifest = json.load(archive.extractfile('manifest.json'))
        if manifest.get('schema') != 1 or manifest.get('blockBytes') != 1048576:
            raise ValueError('unsupported archive schema')
        rows = [row for row in manifest['files'] if args.only is None or row['path'] == args.only]
        if not rows:
            raise ValueError('no matching retained paths')
        output.mkdir(parents=True)
        for row in rows:
            relative = PurePosixPath(row['path'])
            if relative.is_absolute() or '..' in relative.parts or '\\' in row['path'] or relative.suffix != '.glb':
                raise ValueError('unsafe retained path')
            target = output.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            whole = hashlib.sha256()
            size = 0
            with target.open('xb') as result:
                def write(data):
                    nonlocal size
                    result.write(data)
                    whole.update(data)
                    size += len(data)
                header = bytes.fromhex(row['containerHeaderHex'])
                if len(header) != 12:
                    raise ValueError('unexpected container header')
                write(header)
                for chunk in row['chunks']:
                    chunk_header = bytes.fromhex(chunk['headerHex'])
                    if len(chunk_header) != 8:
                        raise ValueError('unexpected chunk header')
                    write(chunk_header)
                    payload_hash = hashlib.sha256()
                    payload_size = 0
                    for block in chunk['blocks']:
                        digest = block['sha256']
                        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                            raise ValueError('invalid object key')
                        member = archive.getmember('objects/' + digest)
                        if member.size != block['bytes'] or not 0 < member.size <= manifest['blockBytes']:
                            raise ValueError('invalid block length')
                        data = archive.extractfile(member).read()
                        if digest not in checked:
                            if hashlib.sha256(data).hexdigest() != digest:
                                raise ValueError('object hash mismatch')
                            checked.add(digest)
                        payload_hash.update(data)
                        payload_size += len(data)
                        write(data)
                    if payload_hash.hexdigest() != chunk['payloadSha256'] or payload_size != chunk['actualPayloadBytes']:
                        raise ValueError('chunk reconstruction mismatch')
                write(bytes.fromhex(row.get('trailingHex', '')))
            if size != row['bytes'] or whole.hexdigest() != row['sha256']:
                raise ValueError('whole-file reconstruction mismatch: ' + row['path'])
            target.chmod(row.get('mode', 0o600))
            restored.append({'path': row['path'], 'bytes': size, 'sha256': whole.hexdigest()})
    print(json.dumps({'passed': True, 'output': str(output), 'restored': restored, 'uniqueObjectsVerified': len(checked)}))


if __name__ == '__main__':
    main()
