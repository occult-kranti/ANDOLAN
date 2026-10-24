"""Real Git + loopback HTTP delivery and altered-byte rejection."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

import audit_public as auditor
import publish_site as publisher


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class PublicAuditTests(unittest.TestCase):
    def test_exact_publication_and_real_tampered_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / 'games/yuga-native/tools/build-observatory'
            web = tool / 'web'
            web.mkdir(parents=True)
            shutil.copyfile(publisher.__file__, tool / 'publish_site.py')
            for name in ('index.html', 'app.js', 'styles.css'):
                (web / name).write_text('bounded actual HTTP fixture: ' + name)
            (web / 'status.json').write_text(json.dumps({
                'schema_version': 1, 'mode': 'snapshot', 'collected_at': '2026-10-24T00:00:00+00:00',
                'source': {'commit': 'a' * 40, 'dirty': False},
                'jobs': [], 'assets': [], 'milestones': [], 'sources': []}))
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('add', '.')
            git('-c', 'user.name=Audit fixture', '-c', 'user.email=fixture@example.invalid',
                '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Frozen publication fixture')
            source = git('rev-parse', 'HEAD').decode().strip()
            site = root / 'site'
            site.mkdir()
            for name in publisher.REQUIRED_BASELINE:
                path = site / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Preserved browser entry ' + name)
            publisher.publish(site, web, 'b' * 40, source)
            server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(site)))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}/'
                accepted = auditor.audit(root, source, 'b' * 40, base, root / 'accepted')
                self.assertTrue(accepted['passed'], accepted['checks'])
                # Actual delivered file changes while both Git and the publisher receipt remain frozen.
                (site / 'production/app.js').write_text('Stale or tampered deployed JavaScript')
                rejected = auditor.audit(root, source, 'b' * 40, base, root / 'rejected')
                self.assertFalse(rejected['passed'])
                bad = next(row for row in rejected['responses'] if row['route'] == 'production/app.js')
                self.assertEqual(bad['http_status'], 200)
                self.assertFalse(bad['matches_expected'])
                (site / 'production/app.js').write_bytes((web / 'app.js').read_bytes())
                publication = site / 'production/publication.json'
                original = publication.read_bytes()
                for index, value in enumerate(([], None, 'unexpected scalar')):
                    publication.write_text(json.dumps(value))
                    malformed = auditor.audit(root, source, 'b' * 40, base, root / f'envelope-{index}')
                    self.assertFalse(malformed['passed'])
                    self.assertTrue((root / f'envelope-{index}/receipt.json').exists())
                publication.write_bytes(original)
                snapshot = site / 'production/status.json'
                for index, value in enumerate(([], None, {'source': 'invalid source object'})):
                    snapshot.write_text(json.dumps(value))
                    malformed = auditor.audit(root, source, 'b' * 40, base, root / f'snapshot-{index}')
                    self.assertFalse(malformed['passed'])
                    self.assertTrue((root / f'snapshot-{index}/receipt.json').exists())
                with self.assertRaises(FileExistsError):
                    auditor.audit(root, source, 'b' * 40, base, root / 'accepted')
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == '__main__':
    unittest.main()
