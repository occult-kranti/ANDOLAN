#!/usr/bin/env python3
"""Independently fetch pinned element sources and terms; the offline library build never calls this."""
import argparse
import base64
import concurrent.futures
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from library import ROOT, load_sources

MAX_BYTES = 32 * 1024 * 1024
REVISION = re.compile(r'[0-9a-f]{40}')
SPDX = re.compile(r'SPDX-License-Identifier:\s*([A-Za-z0-9.() +:-]+(?:\s+(?:AND|OR|WITH)\s+[A-Za-z0-9.()-]+)*)')
POINTER = re.compile(rb'version https://git-lfs.github.com/spec/v1\r?\noid sha256:([0-9a-f]{64})\r?\nsize (\d+)\r?\n?')
GITHUB = 'github.com'
FORGES = {'projects.blender.org', 'codeberg.org'}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def endpoints(pin):
    """Derive raw endpoints from a commit permalink; never resolve a moving branch."""
    parts = urlsplit(pin)
    path = parts.path.lstrip('/').split('/')
    if parts.scheme != 'https' or parts.query or parts.fragment or parts.username or parts.password:
        raise ValueError('Expected an HTTPS commit permalink')
    if parts.hostname == GITHUB and len(path) >= 5 and path[2] == 'blob':
        rev, leaf = path[3], '/'.join(path[4:])
    elif parts.hostname in FORGES and len(path) >= 6 and path[2:4] == ['src', 'commit']:
        rev, leaf = path[4], '/'.join(path[5:])
    else:
        raise ValueError('Unsupported commit permalink')
    if not REVISION.fullmatch(rev) or '..' in unquote(leaf).split('/') or not leaf:
        raise ValueError('Invalid revision or relative path')
    repo = '/'.join(path[:2])
    if parts.hostname == GITHUB:
        return [
            ('raw', f'https://raw.githubusercontent.com/{repo}/{rev}/{leaf}'),
            ('github-contents', f'https://api.github.com/repos/{repo}/contents/{leaf}?ref={rev}'),
        ]
    return [
        ('forgejo-api', f'https://{parts.hostname}/api/v1/repos/{repo}/raw/{leaf}?ref={rev}'),
        ('forgejo-raw', f'https://{parts.hostname}/{repo}/raw/commit/{rev}/{leaf}'),
    ]


def atomic(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(dir=path.parent, delete=False)
    temp = Path(handle.name)
    try:
        with handle:
            handle.write(body)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_endpoint(method, url, timeout):
    headers = {'User-Agent': 'Game-Resource-Library-Pin-Audit/1'}
    if method == 'github-contents':
        headers['Accept'] = 'application/vnd.github.raw+json'
    with urlopen(Request(url, headers=headers), timeout=timeout) as response:
        if response.status != 200:
            raise ValueError('Incomplete HTTP response ' + str(response.status))
        body = response.read(MAX_BYTES + 1)
        mime = response.headers.get_content_type()
    if len(body) > MAX_BYTES:
        raise ValueError('File exceeds 32 MiB per-pin audit limit')
    if not body:
        raise ValueError('Empty file')
    if method == 'github-contents' and mime in ('application/json', 'application/vnd.github+json'):
        try:
            entry = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            entry = None
        if isinstance(entry, dict) and entry.get('type') == 'file' and entry.get('encoding') == 'base64':
            body = base64.b64decode(''.join(entry['content'].split()), validate=True)
            git_oid = hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()
            if entry.get('sha') != git_oid:
                raise ValueError('GitHub Contents object digest differs')
        elif isinstance(entry, dict) and 'download_url' in entry and 'sha' in entry:
            raise ValueError('GitHub response contains metadata only')
    if mime == 'text/html' and re.search(rb'<title>[^<]*(?:error|forbidden|captcha|sign in|access denied)', body[:8192], re.I):
        raise ValueError('Received an HTML access or error page')
    return body


def inspect(body):
    result = {'bytes': len(body), 'sha256': sha256(body)}
    if len(body) < 4096:
        match = POINTER.fullmatch(body)
        if match:
            result['lfs_pointer'] = {'object_sha256': match[1].decode(), 'object_bytes': int(match[2])}
    if b'\0' not in body[:8192]:
        text = body[:16384].decode('utf-8', 'replace')
        spdx = sorted({s.strip().split('  ')[0].strip() for s in SPDX.findall(text)})
        if spdx:
            result['header_spdx'] = spdx
    return result


def retrieve(pin, cache, offline, refresh, timeout):
    target = cache / sha256(pin.encode())
    blob, provenance = target.with_suffix('.bin'), target.with_suffix('.json')
    options = endpoints(pin)
    if not refresh:
        try:
            meta = json.loads(provenance.read_text())
            data = blob.read_bytes()
            date.fromisoformat(meta['observed_utc_date'])
            if (meta['pin'] != pin or (meta['method'], meta['url']) not in options or
                    meta['sha256'] != sha256(data)):
                raise ValueError('Cached provenance or byte checksum differs')
            return {'status': 'retrieved', 'via': 'cache', 'method': meta['method'],
                    'observed_utc_date': meta['observed_utc_date'], **inspect(data)}
        except FileNotFoundError:
            pass
        except (OSError, ValueError, KeyError) as error:
            if offline:
                return {'status': 'cache-invalid', 'error': str(error)}
    if offline:
        return {'status': 'cache-miss'}
    errors = []
    for method, url in options:
        try:
            data = read_endpoint(method, url, timeout)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            errors.append(f'{method}: {error}')
            continue
        details = inspect(data)
        observed = datetime.now(timezone.utc).date().isoformat()
        atomic(blob, data)
        atomic(provenance, json.dumps({'pin': pin, 'url': url, 'method': method,
                                      'observed_utc_date': observed, 'sha256': details['sha256']}).encode())
        return {'status': 'retrieved', 'via': 'network', 'method': method,
                'observed_utc_date': observed, **details}
    return {'status': 'unavailable', 'errors': errors}


def audit(rows, results):
    pins = sorted(results)
    pin_ids = {url: i for i, url in enumerate(pins)}
    claims, sources, digests = {}, {}, {}
    for row in rows:
        sources.setdefault(row['source_url'], []).append(row['id'])
        digests.setdefault(row['sha256'], []).append(row['id'])
        if row.get('license_url'):
            claims.setdefault(row['license_url'], set()).add(row['license'])
    records, counts = [], {}
    for row in sorted(rows, key=lambda r: r['id']):
        pin, terms = row['source_url'], row.get('license_url')
        fetched = results[pin]
        state = fetched['status']
        if state == 'retrieved':
            state = 'matched' if fetched['sha256'] == row['sha256'] else 'mismatch'
        terms_state = 'not-supplied'
        if terms:
            terms_state = results[terms]['status']
        item = {'id': row['id'], 'source': pin_ids[pin], 'source_result': state,
                'expected_sha256': row['sha256'], 'terms': pin_ids.get(terms), 'terms_result': terms_state,
                'declared_license': row['license'], 'use': row['use']}
        flags = []
        if re.search(r'\s+(?:AND|OR|WITH)\s+|\badditional terms\b', row['license'], re.I):
            flags.append('compound-or-additional-terms')
        if fetched.get('header_spdx') and fetched['header_spdx'] != [row['license']]:
            flags.append('review-file-header-against-catalog-license')
        if terms and len(claims[terms]) > 1:
            flags.append('shared-terms-pin-with-different-declared-labels')
        if row.get('license_project') and row['license_project'] != row['project']:
            flags.append('terms-in-another-project')
        if row.get('license_revision') and row['license_revision'] != row['revision']:
            flags.append('terms-at-another-revision')
        if terms == pin:
            flags.append('terms-and-source-same-file')
        if fetched.get('lfs_pointer'):
            flags.append('pointer-bytes-checked-separate-media-object')
        if flags:
            item['scope_flags'] = flags
        counts[state] = counts.get(state, 0) + 1
        records.append(item)
    return {
        'version': 1,
        'scope': 'Curated elements only. Each source is compared to its catalog SHA-256. A terms result records availability and exact bytes of the linked file. Read the file header, rights_note and the named terms before reuse; terms retrieval alone does not establish rights in assets, derivatives or bundled content.',
        'provenance': 'network means a fresh GET of the upstream commit permalink via its raw or API endpoint; cache means locally rehashed bytes and matching endpoint provenance recorded by a previous network run. No local checkout or unpinned branch is accepted.',
        'lfs_scope': 'An LFS pointer match covers the pointer text. The referenced media would require separate retrieval and checksum verification.',
        'summary': {'elements': len(rows), 'unique_source_urls': len(sources), 'unique_source_digests': len(digests),
                    'unique_terms_urls': len(claims), 'all_unique_urls': len(pins),
                    'source_results': dict(sorted(counts.items())),
                    'terms_retrieved_rows': sum(r['terms_result']=='retrieved' for r in records),
                    'terms_unavailable_rows': sum(r['terms'] is not None and r['terms_result']!='retrieved' for r in records),
                    'terms_not_supplied_rows': sum(r['terms'] is None for r in records),
                    'network_observation_utc_dates': sorted({r['observed_utc_date'] for r in results.values() if 'observed_utc_date' in r}),
                    'source_with_spdx_header_rows': sum('header_spdx' in results[r['source_url']] for r in rows),
                    'file_header_label_review_rows': sum('review-file-header-against-catalog-license' in r.get('scope_flags',[]) for r in records),
                    'lfs_source_rows': sum('lfs_pointer' in results[r['source_url']] for r in rows)},
        'duplicate_source_pins': [sorted(ids) for ids in sources.values() if len(ids)>1],
        'duplicate_source_digests': [sorted(ids) for ids in digests.values() if len(ids)>1],
        'pins': [{'url': url, **results[url]} for url in pins],
        'elements': records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path(os.getenv('XDG_CACHE_HOME', Path.home()/'.cache'))/'game-resource-library'/'source-pins-v1')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--offline', action='store_true', help='Use only previously verified cache entries')
    mode.add_argument('--refresh', action='store_true', help='Require fresh network requests for every pin')
    parser.add_argument('--jobs', type=int, default=8, choices=range(1,17), metavar='1..16')
    parser.add_argument('--timeout', type=float, default=12)
    parser.add_argument('--output', type=Path, default=ROOT/'evidence/source-pin-audit.json')
    args = parser.parse_args()
    if args.timeout<=0:
        parser.error('--timeout must be positive')
    rows = load_sources()
    urls = sorted({row[key] for row in rows for key in ('source_url','license_url') if row.get(key)})
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(retrieve, url, args.cache, args.offline, args.refresh, args.timeout): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            results[url] = future.result()
            if results[url]['status'] != 'retrieved':
                print(f"{url}: {results[url]['status']}", file=sys.stderr, flush=True)
            for r in rows:
                if r['source_url']==url and results[url].get('sha256') not in (None, r['sha256']):
                    print('MISMATCH '+r['id']+' '+url, file=sys.stderr, flush=True)
    report = audit(rows,results)
    atomic(args.output,(json.dumps(report,ensure_ascii=False,indent=1)+'\n').encode())
    summary = report['summary']
    print(json.dumps(summary,sort_keys=True))
    return int(summary['source_results'].get('matched',0)!=len(rows) or summary['terms_unavailable_rows']>0)


if __name__ == '__main__':
    raise SystemExit(main())
