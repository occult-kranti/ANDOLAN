#!/usr/bin/env python3
"""Losslessly organize only this packet's large JSON; retain scratch originals."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent
BACKUP=Path('/tmp/yuga-s3-landing-successor-raw-json-r1')


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    assert not BACKUP.exists()
    BACKUP.mkdir()
    records=[]
    for source in sorted(ROOT.rglob('*.json')):
        if source.stat().st_size<1024**2:continue
        assert '__pycache__' not in source.parts
        relative=source.relative_to(ROOT)
        raw=source.read_bytes();original=BACKUP/relative
        original.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,original)
        compressed=gzip.compress(raw,compresslevel=6,mtime=0)
        target=source.with_suffix(source.suffix+'.gz');assert not target.exists()
        target.write_bytes(compressed)
        assert gzip.decompress(target.read_bytes())==raw==original.read_bytes()
        records.append({'original_path':str(relative),'gzip_path':str(target.relative_to(ROOT)),
                        'uncompressed_sha256':digest(raw),'uncompressed_bytes':len(raw),
                        'gzip_sha256':digest(compressed),'gzip_bytes':len(compressed),
                        'scratch_original':str(original)})
        source.unlink()
    result={'passed':True,'algorithm':'gzip level6 mtime0','files':records,
            'scope':'Only this packet JSON >=1MiB is stored as lossless gzip. Original report/receipt hashes remain uncompressed identities and resolve through this mapping. Scratch copies remain until remote checkpoint verification; no pose, assertion, log or source bytes changed.'}
    (ROOT/'large-json-storage.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'files':len(records),'raw_bytes':sum(x['uncompressed_bytes']for x in records),'gzip_bytes':sum(x['gzip_bytes']for x in records)}))


if __name__=='__main__':main()
