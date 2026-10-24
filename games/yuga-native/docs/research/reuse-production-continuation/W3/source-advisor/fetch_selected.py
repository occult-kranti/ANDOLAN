"""Fetch only five catalog-licensed long01 members, using cached ZIP metadata.

No full archive fallback. HTTP 206, exact range/size, ETag, per-member central
directory CRC and decompressed sizes are mandatory before files are retained.
"""
import argparse
import datetime
import hashlib
import json
import struct
import time
import urllib.request
import zlib
from pathlib import Path

URL = 'https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip'
ETAG = '"10bbb7ea-6160e7c0d7996"'
DIRECTORY_SHA = '34f1ab98fba2d1c3fd9b7ecfae73737a42ad61849d2688ddc3eaa37f4d557d42'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cached-directory', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--primary-mirror', action='store_true')
    a = p.parse_args()
    data = a.cached_directory.read_bytes()
    assert hashlib.sha256(data).hexdigest() == DIRECTORY_SHA
    a.output.mkdir(parents=True, exist_ok=False)
    rows = []
    i = data.find(b'PK\x01\x02')
    while data[i:i + 4] == b'PK\x01\x02':
        fields = struct.unpack_from('<4s6H3I5H2I', data, i)
        name = data[i + 46:i + 46 + fields[10]].decode()
        rows.append({'name': name, 'crc32': fields[7], 'compressed_bytes': fields[8],
                     'bytes': fields[9], 'method': fields[4], 'local_offset': fields[16]})
        i += 46 + fields[10] + fields[11] + fields[12]
    chosen = [r for r in rows if r['name'].startswith('hair/long01/') and not r['name'].endswith('/')]
    assert len(chosen) == 5 and {Path(r['name']).suffix for r in chosen} == {'.obj', '.mhclo', '.mhmat', '.png', '.thumb'}
    start = min(r['local_offset'] for r in chosen)
    last = max(r['local_offset'] for r in chosen)
    end = min(r['local_offset'] for r in rows if r['local_offset'] > last) - 1
    assert 0 < end - start < 3_200_000
    wanted_range = f'bytes={start}-{end}'
    url = URL.replace('files2.', 'files.') if a.primary_mirror else URL
    request_headers = {'Range': wanted_range, 'User-Agent': 'YUGA-source-intake/1.0'}
    if not a.primary_mirror: request_headers['If-Match'] = ETAG
    request = urllib.request.Request(url, headers=request_headers)
    begin = time.monotonic()
    with urllib.request.urlopen(request, timeout=45) as response:
        assert response.status == 206, 'No full archive fallback permitted'
        assert response.headers['Content-Range'] == f'bytes {start}-{end}/280737770'
        if not a.primary_mirror: assert response.headers['ETag'] == ETAG
        payload = response.read(end - start + 2)
        assert len(payload) == end - start + 1
        headers = dict(response.headers.items())
    selected = []
    for row in chosen:
        offset = row['local_offset'] - start
        fields = struct.unpack_from('<4s5H3I2H', payload, offset)
        assert fields[0] == b'PK\x03\x04' and fields[3] == row['method'] == 8
        name = payload[offset + 30:offset + 30 + fields[9]].decode()
        assert name == row['name']
        body = offset + 30 + fields[9] + fields[10]
        compressed = payload[body:body + row['compressed_bytes']]
        raw = zlib.decompress(compressed, -15)
        assert len(raw) == row['bytes'] and zlib.crc32(raw) == row['crc32']
        target = a.output / Path(name).name
        target.write_bytes(raw)
        selected.append({**row, 'sha256': hashlib.sha256(raw).hexdigest(), 'local_name': target.name})
    receipt = {'schema_version': 1, 'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'url': url, 'range': wanted_range, 'range_bytes': len(payload),
               'range_sha256': hashlib.sha256(payload).hexdigest(), 'headers': headers,
               'cached_directory_sha256': DIRECTORY_SHA, 'files': selected,
               'full_pack_downloaded': False, 'license': 'CC0-1.0, exact official long01 catalog row',
               'seconds': time.monotonic() - begin}
    (a.output / 'download.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
