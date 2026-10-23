"""Verify the blocked comparator; never submit or retry network work."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
repo = root.parents[6]
assert (repo / 'AGENTS.md').is_file()
checks = 0
for line in (root / 'SHA256SUMS').read_text().splitlines():
    expected, name = line.split('  ', 1)
    path = (root / name).resolve(strict=True)
    assert path.is_relative_to(root)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    checks += 1

manifest = json.loads((root / 'manifest.json').read_text())
baseline = repo / manifest['baseline_canonical_glb']
assert hashlib.sha256(baseline.read_bytes()).hexdigest() == manifest['baseline_glb_sha256']
assert not (baseline.parent / 'rama-generated-1024.glb').exists()
receipt = json.loads((root / 'run1/receipt.json').read_text())
assert receipt['gpu_submission_attempts'] == 1
assert not receipt['gpu_generation_verified'] and not receipt['glb_produced']
assert [c['api_name'] for c in receipt['calls']] == ['start_session', 'preprocess_image', 'image_to_3d']
denied = receipt['calls'][-1]
assert denied['status'] == 'SERVER_REJECTED_OR_FAILED'
assert denied['server_error']['title'] == 'ZeroGPU quota exceeded'
assert denied['server_error'] == manifest['provider_error']
assert receipt['generation_settings']['resolution'] == '1024'
contract = json.loads((root / 'comparison-contract.json').read_text())
assert receipt['script_sha256'] == contract['candidate_script_sha256']
baseline_source = (root.parent / 'trellis2_pipeline_once.py').read_bytes()
assert hashlib.sha256(baseline_source).hexdigest() == contract['baseline_script_sha256']
expected = baseline_source.decode().replace("'resolution':'512'", "'resolution':'1024'").replace("parameters=[prepared[0],71,'512'", "parameters=[prepared[0],71,'1024'")
assert (root / 'trellis2_pipeline_once.py').read_text() == expected
assert manifest['gpu_retries'] == manifest['gpu_export_submissions'] == 0
assert not manifest['quality_improvement_claimed']
print(json.dumps({'status': 'PASS', 'bundle_hashes': checks,
                  'baseline512_unchanged': True, 'generation_submissions': 1,
                  'export_submissions': 0, 'candidate_generated': False,
                  'verifier_network_requests': 0}))
