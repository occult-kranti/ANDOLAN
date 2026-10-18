#!/usr/bin/env python3
"""Copy a completed owned take and losslessly retain its isolated user files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    assert not args.destination.exists()
    record = json.loads((args.run/'run.json').read_text())
    assert record.get('complete') is True and record.get('verified_exit_code') == 0
    shutil.copytree(args.run, args.destination, ignore=shutil.ignore_patterns('user'))
    watch = args.run.with_name(args.run.name+'-watchdog')
    shutil.copytree(watch, args.destination.with_name(args.destination.name+'-watchdog'))
    user = args.run/'user'
    inventory = {str(p.relative_to(user)): {'sha256':sha(p),'bytes':p.stat().st_size}
                 for p in sorted(user.rglob('*')) if p.is_file()}
    archive = args.destination/'isolated-user-files.tar.gz'
    with tarfile.open(archive, 'w:gz') as output:
        for name in inventory:
            output.add(user/name, arcname=name, recursive=False)
    with tarfile.open(archive, 'r:gz') as source:
        names = source.getnames()
        assert set(names) == set(inventory) and len(names) == len(inventory)
        for item in source:
            payload = source.extractfile(item).read()
            assert len(payload) == inventory[item.name]['bytes']
            assert hashlib.sha256(payload).hexdigest() == inventory[item.name]['sha256']
    copied = {str(p.relative_to(args.run)): {'sha256':sha(p),'bytes':p.stat().st_size}
              for p in sorted(args.run.rglob('*')) if p.is_file() and 'user' not in p.relative_to(args.run).parts}
    assert all(sha(args.destination/name) == row['sha256'] for name,row in copied.items())
    receipt = {'passed':True,'source_run':str(args.run),'copied_raw_files':copied,
               'user_files':inventory,'user_archive':{'sha256':sha(archive),'bytes':archive.stat().st_size},
               'scope':'Exact raw inputs/originals/logs copied; user archive independently decompressed and rehashed. No frame edits.'}
    (args.destination/'archive-copy-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'passed':True,'raw_files':len(copied),'user_files':len(inventory),'archive_bytes':archive.stat().st_size}))


if __name__ == '__main__':
    main()
