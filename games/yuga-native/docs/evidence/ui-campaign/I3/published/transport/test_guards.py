#!/usr/bin/env python3
"""Local-only adversaries. Network is replaced by an in-memory API."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('uploader', ROOT / 'reconstruct_upload.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
checks = []


def record(name, fn, reject=False):
    try:
        fn()
    except (ValueError, FileExistsError):
        if not reject:
            raise
    else:
        if reject:
            raise AssertionError('accepted invalid fixture: ' + name)
    checks.append({'name': name, 'passed': True})


real = u.read_manifest(ROOT / 'manifest.json')
record('exact pinned manifest', lambda: u.read_manifest(ROOT / 'manifest.json'))
with tempfile.TemporaryDirectory(prefix='transport-guards-') as tmp:
    folder = Path(tmp)
    altered = folder / 'manifest.json'
    altered.write_bytes((ROOT / 'manifest.json').read_bytes() + b' ')
    record('altered manifest bytes rejected', lambda: u.read_manifest(altered), reject=True)
    files = folder / 'files'
    files.mkdir()
    manifest = {'assets': []}
    for n in u.NAMES:
        data = ('fixture-' + n).encode()
        (files / n).write_bytes(data)
        manifest['assets'].append({'name': n, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    release = {'id': u.RELEASE_ID, 'draft': True, 'prerelease': True,
               'tag_name': u.TAG, 'target_commitish': u.TARGET, 'assets': []}
    for key, bad in [('id', 1), ('draft', False), ('prerelease', False),
                     ('target_commitish', 'main'), ('tag_name', 'other-tag')]:
        changed = copy.deepcopy(release)
        changed[key] = bad
        calls = []
        def api(args):
            calls.append(args)
            assert args[0] != '--method', 'mutation attempted before fixed release guard'
            return changed
        record('reject bad ' + key + ' before upload', lambda: u.upload(manifest, files, api), reject=True)
        assert len(calls) == 1
    def asset(expected, ident=1):
        return {'id': ident, 'name': expected['name'], 'size': expected['size'],
                'digest': 'sha256:' + expected['sha256'], 'state': 'uploaded'}
    for label, mutation in [
        ('existing mismatched digest', lambda a: a.update(digest='sha256:' + '0'*64)),
        ('existing missing digest', lambda a: a.pop('digest')),
        ('existing wrong size', lambda a: a.update(size=a['size'] + 1)),
        ('existing incomplete state', lambda a: a.update(state='starter')),
        ('unexpected asset', lambda a: a.update(name='unapproved.zip')),
    ]:
        changed = copy.deepcopy(release)
        existing = asset(manifest['assets'][0])
        mutation(existing)
        changed['assets'] = [existing]
        calls = []
        def api(args):
            calls.append(args)
            assert args[0] != '--method'
            return changed
        record(label + ' prevents clobber', lambda: u.upload(manifest, files, api), reject=True)
    state = copy.deepcopy(release)
    posts = []
    def valid_api(args):
        if args[0] != '--method':
            assert args == [f'repos/{u.REPO}/releases/{u.RELEASE_ID}']
            return copy.deepcopy(state)
        assert args[0:2] == ['--method', 'POST']
        assert args[2].startswith(f'https://uploads.github.com/repos/{u.REPO}/releases/{u.RELEASE_ID}/assets?name=')
        name = Path(args[4]).name
        assert name not in posts
        expected = next(a for a in manifest['assets'] if a['name'] == name)
        out = asset(expected, len(posts) + 1)
        posts.append(name)
        state['assets'].append(out)
        return out
    with contextlib.redirect_stdout(io.StringIO()):
        record('valid control uploads exactly five to fixed ID', lambda: u.upload(manifest, files, valid_api))
        assert tuple(posts) == u.NAMES
        record('exact existing five are skipped without mutation', lambda: u.upload(manifest, files, valid_api))
        assert len(posts) == 5
    first = files / u.NAMES[0]
    first.write_bytes(b'wrong')
    def forbidden_api(args):
        raise AssertionError('API invoked before output identity check')
    record('changed reconstructed bytes rejected before API', lambda: u.upload(manifest, files, forbidden_api), reject=True)
    data = b'exact chunk'
    part = {'path': 'transport/chunks/test.bin', 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    stream_manifest = {'assets': [{'name': 'test.zip', 'size': len(data),
                                  'sha256': part['sha256'], 'parts': [part]}]}
    record('correct stream identity', lambda: u.verify_streams(stream_manifest, lambda p: io.BytesIO(data)))
    record('changed chunk bytes rejected', lambda: u.verify_streams(stream_manifest, lambda p: io.BytesIO(b'X' + data[1:])), reject=True)
    record('oversized chunk rejected', lambda: u.verify_streams(stream_manifest, lambda p: io.BytesIO(data + b'x')), reject=True)
    record('truncated chunk rejected', lambda: u.verify_streams(stream_manifest, lambda p: io.BytesIO(data[:-1])), reject=True)
    wrong_assembled = copy.deepcopy(stream_manifest)
    wrong_assembled['assets'][0]['sha256'] = '0'*64
    record('assembled digest checked independently', lambda: u.verify_streams(wrong_assembled, lambda p: io.BytesIO(data)), reject=True)
receipt = {'checks': checks, 'passed': len(checks), 'failed': 0,
           'uploader_sha256': hashlib.sha256((ROOT / 'reconstruct_upload.py').read_bytes()).hexdigest(),
           'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'manifest_sha256': u.MANIFEST_SHA256,
           'network_mutations': 0, 'fixture_only': True}
(ROOT / 'guard-tests.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({'passed': len(checks), 'failed': 0, 'network_mutations': 0}))
