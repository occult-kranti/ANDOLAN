"""Verify dated publication evidence without sending network requests."""
from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parent
repo = root.parents[5]
assert (repo / 'AGENTS.md').is_file()
bound = 0
for line in (root / 'SHA256SUMS').read_text().splitlines():
    expected, name = line.split('  ', 1)
    path = (root / name).resolve(strict=True)
    assert path.is_relative_to(root)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    bound += 1

source = '069ab775c66fff838c4aed149912dd483df4d564'
rows = json.loads((root / 'public-byte-bindings.json').read_text())
assert len(rows) == 19
assert all(row['curl_exit'] == 0 and row['http_status'] == '200' for row in rows)
commit_checks = 0
baseline_checks = 0
for row in rows:
    if 'expected_commit' in row:
        assert row['expected_commit'] == source
        path = 'games/yuga-native/tools/build-observatory/web/' + row['path'].removeprefix('production/')
        result = subprocess.run(['git', '--no-optional-locks', '-C', str(repo), 'show', source + ':' + path],
                                capture_output=True, check=True)
        assert hashlib.sha256(result.stdout).hexdigest() == row['sha256']
        assert row['matches_expected_commit']
        commit_checks += 1
    retained = root / 'captured' / row['path']
    if retained.exists():
        assert hashlib.sha256(retained.read_bytes()).hexdigest() == row['sha256']
        assert retained.stat().st_size == row['bytes']
    if not row['path'].startswith('production/'):
        assert row['matches_expected_local']
        assert row['sha256'] == row['expected_local_sha256']
        assert row['bytes'] == row['expected_local_bytes']
        baseline_checks += 1
assert commit_checks == 13 and baseline_checks == 5

publication = json.loads((root / 'captured/production/publication.json').read_text())
snapshot = json.loads((root / 'captured/production/status.json').read_text())
assert publication['dashboard_source'] == source
assert publication['baseline_source'] == '176b6f8e71fcffd3d570d96e66643d8cb9893603'
assert publication['data_mode'] == snapshot['mode'] == 'snapshot'
assert publication['observation_time'] == snapshot['collected_at'] == '2026-10-23T20:59:35+00:00'
census = json.loads((root / 'baseline-census.json').read_text())
assert len(census) == publication['baseline_files'] == 90
assert hashlib.sha256(json.dumps(census, sort_keys=True).encode()).hexdigest() == publication['baseline_census_sha256']
for row in rows:
    if not row['path'].startswith('production/'):
        assert census[row['path']]['sha256'] == row['sha256']
        assert census[row['path']]['bytes'] == row['bytes']
history = json.loads((root / 'monitor-history.json').read_text())
assert history[-1]['status'] == 'completed' and history[-1]['conclusion'] == 'success'
assert history[-1]['head_sha'] == source
native = json.loads((root / 'nativefoundation-initial.json').read_text())
assert native['head_sha'] == source and native['conclusion'] == 'failure'
glb = next(row for row in rows if row['path'] == 'production/media/rama-generated.glb')
assert glb['sha256'] == '0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b'
assert glb['bytes'] == 4480716
print(json.dumps({'status': 'PASS', 'bundle_files': bound, 'public_responses_http200': 19,
                  'exact_commit_byte_checks': commit_checks,
                  'baseline_entries_fetched': baseline_checks, 'data_mode': 'snapshot',
                  'verifier_network_requests': 0}))
