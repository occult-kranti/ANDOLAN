"""Verify this frozen handoff and canonical art bytes without network or GPU use."""
from pathlib import Path
import hashlib
import json
import re

root = Path(__file__).resolve().parent
repo = root.parents[5]
assert (repo / 'AGENTS.md').is_file(), 'Unexpected repository root'

checks = 0
for line in (root / 'SHA256SUMS').read_text().splitlines():
    expected, name = line.split('  ', 1)
    path = (root / name).resolve(strict=True)
    assert path.is_relative_to(root), 'Bundle path escape'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    checks += 1

manifest = json.loads((root / 'manifest.json').read_text())
for item in manifest['input_and_canonical_output']:
    path = (repo / item['path']).resolve(strict=True)
    assert path.is_relative_to(repo), 'Canonical path escape'
    body = path.read_bytes()
    assert len(body) == item['bytes']
    assert hashlib.sha256(body).hexdigest() == item['sha256']
    checks += 1

for ledger in ['metadata-ledger.json', 'supplemental-ledger.json']:
    for item in json.loads((root / ledger).read_text()):
        assert item['curl_exit'] == 0 and item['http_status'] == '200'
        body = (root / (item['name'] + '.json')).read_bytes()
        assert len(body) == item['bytes']
        assert hashlib.sha256(body).hexdigest() == item['sha256']
        checks += 1

receipt = json.loads((root / 'run1/receipt.json').read_text())
assert receipt['status'] == 'EXPORTED'
assert receipt['gpu_submission_attempts'] == 2
assert receipt['gpu_generation_verified'] and receipt['glb_produced']
assert all(call['status'] == 'COMPLETED' for call in receipt['calls'])
assert sum(call['gpu_function'] for call in receipt['calls']) == 2
assert receipt['script_sha256'] == manifest['script_sha256']
assert receipt['glb']['sha256'] == manifest['input_and_canonical_output'][1]['sha256']
assert receipt['input']['sha256'] == manifest['input_and_canonical_output'][0]['sha256']
assert len(re.findall('src="data:image/jpeg;base64,', (root / 'run1/preview.html').read_text())) == 54
for snapshot in receipt['preview_snapshots']:
    path = root / 'run1' / snapshot['path']
    if path.exists():
        body = path.read_bytes()
        assert len(body) == snapshot['bytes']
        assert hashlib.sha256(body).hexdigest() == snapshot['sha256']
        checks += 1

preflight = json.loads((root / 'preflight-verification-final.json').read_text())
assert preflight['script_sha256'] == manifest['script_sha256']
assert preflight['wrong_input_hash_rejected'] and preflight['exit_code'] == 1
assert preflight['http_calls'] == preflight['gpu_submission_attempts'] == 0
print(json.dumps({'status': 'PASS', 'hash_size_checks': checks, 'gpu_submissions': 2,
                  'canonical_art_files': 2, 'network_requests_by_verifier': 0}))
