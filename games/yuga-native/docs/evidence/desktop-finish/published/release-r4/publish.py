#!/usr/bin/env python3
"""Publish the fixed, independently qualified r4 draft after exact-byte guards."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = Path('/workspace/ANDOLAN')
SOURCE = '96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
TAG = 'yuga-desktop-finish-2026-10-18'
API = 'repos/occult-kranti/ANDOLAN/releases/416367666'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def api(path, *args):
    return subprocess.check_output(['gh', 'api', path, *args], cwd=REPO)

def main():
    owner = HERE.parent.parent / 'package-native-review/W1-patched-r1/receipt.json'
    reviewer = HERE.parent.parent / 'package-native-review/W6-r4-independent-r1/receipt.json'
    assert sha(owner) == 'ebcbaed5d8aad06c9bc647134fa91ab375302fad9c6fd26d1423ca276742acf8'
    assert sha(reviewer) == '99a3d6d9746aa36afe733a0b4d92ec92ea810eadeea54245435b8a5f9c6b4e0e'
    qualification = json.loads(owner.read_text())
    assert qualification['source_commit'] == SOURCE
    assert qualification['warm']['passed'] and qualification['cold']['passed']
    manifest = json.loads((HERE.parent / 'transport-r2/manifest.json').read_text())
    assert manifest['target'] == SOURCE and manifest['release_id'] == 416367666
    expected = {a['name']: a for a in manifest['assets']}
    assert len(expected) == 5
    local = Path('/workspace/scratch/yuga-desktop-integrated-package-r4/build')
    for name, asset in expected.items():
        assert (local/name).stat().st_size == asset['size']
        assert sha(local/name) == asset['sha256']
    raw = api(API)
    (HERE/'draft-before-publication.json').write_bytes(raw)
    release = json.loads(raw)
    assert release['draft'] and release['prerelease']
    assert release['tag_name'] == TAG and release['target_commitish'] == SOURCE
    assert {a['name'] for a in release['assets']} == set(expected)
    assert len(release['assets']) == 5
    for asset in release['assets']:
        pin = expected[asset['name']]
        assert asset['state'] == 'uploaded' and asset['size'] == pin['size']
        assert asset['digest'] == 'sha256:' + pin['sha256']
    workflow = json.loads(api('repos/occult-kranti/ANDOLAN/actions/runs/39122371874'))
    assert workflow['status'] == 'completed' and workflow['conclusion'] == 'success'
    assert workflow['head_sha'] == 'fc0827fda3c43c706a27ee0bb618b2477148c462'
    (HERE/'upload-run-final.json').write_text(json.dumps(workflow, indent=2)+'\n')
    # Keep every identity field explicit; an earlier omitted tag was reset by the API.
    payload = {'tag_name': TAG, 'target_commitish': SOURCE,
               'name': 'YUGA desktop finish preview', 'body': (HERE/'release-notes.md').read_text(),
               'draft': False, 'prerelease': True, 'make_latest': 'false'}
    (HERE/'publication-request.json').write_text(json.dumps(payload, indent=2)+'\n')
    result = api(API, '--method', 'PATCH', '--input', str(HERE/'publication-request.json'))
    (HERE/'publication-response.json').write_bytes(result)
    published = json.loads(result)
    assert not published['draft'] and published['prerelease']
    assert published['tag_name'] == TAG and published['target_commitish'] == SOURCE
    assert published['published_at'] and len(published['assets']) == 5
    print(json.dumps({k: published[k] for k in ['id','html_url','tag_name','target_commitish','draft','published_at']}, indent=2))

if __name__ == '__main__':
    main()
