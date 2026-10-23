"""Compare deployed static bytes with a named immutable Git source."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not re.fullmatch('[0-9a-f]{40}', args.source) or args.output.exists():
    parser.error('Use a full source SHA and a fresh output file')
root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
prefix = 'games/yuga-native/tools/build-observatory/web/'
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', args.source, prefix], cwd=root, text=True).splitlines()
publisher_path = 'games/yuga-native/tools/build-observatory/publish_site.py'
if (root / publisher_path).read_bytes() != subprocess.check_output(['git', 'show', args.source + ':' + publisher_path], cwd=root):
    parser.error('Run with the publisher matching the audited source')
spec = importlib.util.spec_from_file_location('yuga_publication_policy', root / publisher_path)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
expected = {'production/' + path.removeprefix(prefix): path for path in paths if policy.approved(path.removeprefix(prefix))}
excluded = [path.removeprefix(prefix) for path in paths if not policy.approved(path.removeprefix(prefix))]
entries = ['index.html', 'yuga/index.html', 'yuga/lab/index.html', 'yuga/control-lab/index.html', 'yuga/lane-lab/index.html']
requests, errors = [], []
for path in sorted(set(expected) | set(entries) | {'production/publication.json'}):
    url = 'https://occult-kranti.github.io/ANDOLAN/' + path + '?audit=' + args.source
    try:
        with urllib.request.urlopen(url, timeout=45) as response:
            body = response.read(64 * 1024 * 1024 + 1)
            if len(body) > 64 * 1024 * 1024:
                raise ValueError('Public file exceeded audit bound')
            row = {'path': path, 'status': response.status, 'content_type': response.headers.get('Content-Type'), 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
        if path in expected:
            committed = subprocess.check_output(['git', 'show', args.source + ':' + expected[path]], cwd=root)
            row['exact_committed_source_match'] = body == committed
            if not row['exact_committed_source_match']:
                errors.append('Source mismatch: ' + path)
        if path == 'production/publication.json':
            publication = json.loads(body)
            row['dashboard_source'] = publication['dashboard_source']
            row['preserved_baseline_files'] = publication['baseline_files']
            if row['dashboard_source'] != args.source:
                errors.append('Deployment source identity mismatch')
            if sorted(publication['dashboard_files']) != sorted(path.removeprefix('production/') for path in expected):
                errors.append('Published census does not match the committed approved file set')
        if path == 'production/status.json':
            snapshot = json.loads(body)
            row.update({'observed_at': snapshot['collected_at'], 'mode': snapshot['mode'], 'jobs': len(snapshot['jobs']), 'stages': len(snapshot['milestones'])})
        requests.append(row)
    except Exception as error:
        errors.append(path + ': ' + type(error).__name__ + ': ' + str(error))
report = {'passed': not errors, 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'deployed_source': args.source, 'requests': requests, 'errors': errors, 'excluded_local_helpers': excluded, 'scope': 'Actual public HTTP and exact committed approved static bytes, using the source-pinned publisher file policy. Excluded local helpers are listed explicitly. Five older browser entry responses are availability checks; publisher metadata retains the separate browser baseline identity. No new native release, game-quality or physical GPU acceptance.'}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'requests': len(requests), 'exact_source_matches': sum(row.get('exact_committed_source_match', False) for row in requests), 'errors': errors}))
raise SystemExit(0 if report['passed'] else 1)
