#!/usr/bin/env python3
"""Independent frozen Git/real loopback HTTP negative controls for the auditor."""
import argparse
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--auditor', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    tools = args.workspace / 'games/yuga-native/tools/build-observatory'
    sys.path.insert(0, str(tools))
    import publish_site as publisher
    spec = importlib.util.spec_from_file_location('frozen_auditor_review', args.auditor)
    auditor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auditor)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    pins = {'auditor': sha(args.auditor), 'publisher': sha(Path(publisher.__file__)), 'probe': sha(Path(__file__))}
    rows = []
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        tool = root / 'games/yuga-native/tools/build-observatory'
        web = tool / 'web'
        web.mkdir(parents=True)
        shutil.copyfile(publisher.__file__, tool / 'publish_site.py')
        for name in ('index.html', 'styles.css', 'app.js'):
            (web / name).write_text('Independent delivered bytes for ' + name)
        snapshot = {'schema_version': 1, 'mode': 'snapshot', 'collected_at': '2026-10-24T00:00:00+00:00',
                    'source': {'commit': 'a' * 40, 'dirty': False}, 'jobs': [], 'assets': [], 'milestones': [], 'sources': []}
        (web / 'status.json').write_text(json.dumps(snapshot))
        def git(*values):
            return subprocess.check_output(['git', *values], cwd=root, stderr=subprocess.DEVNULL)
        git('init', '-q'); git('add', '.')
        git('-c', 'user.name=Independent audit', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'frozen fixture')
        source = git('rev-parse', 'HEAD').decode().strip()
        site = root / 'site'; site.mkdir()
        for name in publisher.REQUIRED_BASELINE:
            path = site / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('Existing entry: ' + name)
        publisher.publish(site, web, 'b' * 40, source)
        production = site / 'production'
        original = {name: (production / name).read_bytes() for name in ['publication.json', 'status.json', 'app.js']}
        publication = json.loads(original['publication.json'])
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(site)))
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            cases = [
                ('positive', None, None, True),
                ('missing_dashboard_source', 'publication.json', {k: v for k, v in publication.items() if k != 'dashboard_source'}, False),
                ('wrong_baseline_pin', 'publication.json', {**publication, 'baseline_source': 'c' * 40}, False),
                ('missing_inventory_file', 'publication.json', {**publication, 'dashboard_files': {k: v for k, v in publication['dashboard_files'].items() if k != 'app.js'}}, False),
                ('malformed_json_syntax', 'publication.json', b'[', False),
                ('publication_array', 'publication.json', [], False),
                ('publication_null', 'publication.json', None, False),
                ('publication_string', 'publication.json', 'not an object', False),
                ('snapshot_array', 'status.json', [], False),
                ('snapshot_null', 'status.json', None, False),
                ('snapshot_source_scalar', 'status.json', {**snapshot, 'source': 7}, False),
                ('delivered_app_changed', 'app.js', b'changed while committed bytes remain fixed', False),
            ]
            for name, target, value, expected in cases:
                for file, raw in original.items(): (production / file).write_bytes(raw)
                if target: (production / target).write_bytes(value if isinstance(value, bytes) else json.dumps(value).encode())
                row = {'name': name, 'expectedAcceptance': expected}
                try:
                    report = auditor.audit(root, source, 'b' * 40, f'http://127.0.0.1:{server.server_port}/', args.output / name)
                    row.update(acceptance=report['passed'], receiptWritten=(args.output / name / 'receipt.json').is_file(), failedChecks=[c['name'] for c in report['checks'] if not c['passed']])
                    row['passed'] = report['passed'] is expected and row['receiptWritten']
                except Exception as exc:
                    row.update(passed=False, exception=type(exc).__name__ + ': ' + str(exc), receiptWritten=(args.output / name / 'receipt.json').is_file())
                rows.append(row)
        finally:
            server.shutdown(); server.server_close(); thread.join()
    result = {'passed': all(row['passed'] for row in rows), 'sourcePins': pins, 'checks': rows,
              'scope': 'Independent actual Git/HTTP fixture. Tests exact bytes/pins/inventory and failed-receipt behavior for malformed public JSON; not production delivery.'}
    (args.output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
