#!/usr/bin/env python3
"""Verify the source packet and lossless large-JSON identities after relocation."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def digest(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    assert not args.report.exists(), 'Fresh verification output required'
    manifest=json.loads((ROOT/'artifact-manifest.json').read_text())
    checks=[]
    for relative,entry in manifest['files'].items():
        path=ROOT/relative
        assert path.resolve().is_relative_to(ROOT.resolve())
        data=path.read_bytes()
        checks.append({'path':relative,'passed':len(data)==entry['bytes'] and digest(data)==entry['sha256']})
    storage=json.loads((ROOT/'large-json-storage.json').read_text())
    for entry in storage['files']:
        compressed=(ROOT/entry['gzip_path']).read_bytes();raw=gzip.decompress(compressed)
        checks.append({'path':entry['original_path'],'passed':len(raw)==entry['uncompressed_bytes'] and digest(raw)==entry['uncompressed_sha256'] and len(compressed)==entry['gzip_bytes'] and digest(compressed)==entry['gzip_sha256'],'scope':'Exact decompressed original receipt identity'})
    result={'passed':bool(checks) and all(row['passed']for row in checks),'count':len(checks),'files':len(manifest['files']),
            'manifest_sha256':digest((ROOT/'artifact-manifest.json').read_bytes()),'checks':checks,
            'scope':'Repository-only evidence identity replay. No engine, raster or new acceptance claim.'}
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in ('passed','count','files')}))
    raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
