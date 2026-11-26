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
import observatory
from test_publish_site import write_studio_fixture
from urllib.error import HTTPError
from urllib.request import Request, urlopen


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
                'jobs': [], 'assets': [{'url': route} for route in (
                    publisher.AUDIO_ROUTE, publisher.AUDIO_ROUTE.rstrip('/'), publisher.AUDIO_ROUTE + 'quench.flac')],
                'milestones': [], 'sources': []}))
            for route, repo_path in publisher.ATLAS_FILES.items():
                path = root / repo_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Bounded fixture for ' + route)
            studio = root / publisher.STUDIO
            write_studio_fixture(studio)
            (studio / 'work-in-progress.html').write_text('studio working file')
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL)
            def commit(message):
                git('-c', 'user.name=Audit fixture', '-c', 'user.email=fixture@example.invalid',
                    '-c', 'commit.gpgsign=false', 'commit', '-qm', message)
                return git('rev-parse', 'HEAD').decode().strip()
            git('init', '-q')
            git('add', '.')
            source = commit('Frozen publication fixture')
            site = root / 'site'
            site.mkdir()
            for name in publisher.REQUIRED_BASELINE:
                path = site / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Preserved browser entry ' + name)
            publisher.publish(site, web, 'b' * 40, source, workspace=root)
            self.assertFalse((site / 'production/mandala-art/work-in-progress.html').exists())
            worker = observatory.make_server(observatory.Observatory(root, root), 0)
            worker_thread = threading.Thread(target=worker.serve_forever, daemon=True)
            worker_thread.start()
            try:
                url = f'http://127.0.0.1:{worker.server_port}/mandala-art/'
                with urlopen(url) as r:
                    self.assertEqual(r.read(), b'index.html')
                with urlopen(Request(url + 'tour.mp4', headers={'Range': 'bytes=1-4'})) as r:
                    self.assertEqual((r.status, r.headers['Content-Range'], r.read()), (206, 'bytes 1-4/8', b'our.'))
                    tag = r.headers['ETag']
                for headers, expected_status in [({'Range':'bytes=99-'},416), ({'If-None-Match':tag},304)]:
                    with self.assertRaises(HTTPError) as error:
                        urlopen(Request(url + 'tour.mp4', headers=headers))
                    self.assertEqual(error.exception.code, expected_status)
                with self.assertRaises(HTTPError) as refused:
                    urlopen(url + 'work-in-progress.html')
                self.assertEqual(refused.exception.code, 404)
                with urlopen(Request(url + 'mandala-rift.blend', method='HEAD')) as r:
                    self.assertEqual(r.headers['Content-Type'], 'application/octet-stream')
                    self.assertEqual(r.read(), b'')
            finally:
                worker.shutdown()
                worker.server_close()
                worker_thread.join()
            server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(site)))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}/'
                accepted = auditor.audit(root, source, 'b' * 40, base, root / 'accepted')
                self.assertTrue(accepted['passed'], accepted['checks'])
                files = accepted['expected_files']
                self.assertTrue(publisher.ATLAS_FILES.keys() <= files.keys())
                vessel = 'concepts/items/rite-ember-vessel.webp'
                self.assertEqual(files['ember-rite/mandala-map-studio/' + vessel], files[publisher.STUDIO_ROUTE + vessel])
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
                index = studio / 'concepts/index.json'
                concepts = json.loads(index.read_text())
                del concepts['hero']
                index.write_text(json.dumps(concepts))
                git('add', str(index))
                atlas_only, _ = auditor.expected_files(root, commit('Remove the studio route for the shared vessel'))
                self.assertIn('ember-rite/mandala-map-studio/' + vessel, atlas_only)
                self.assertNotIn(publisher.STUDIO_ROUTE + vessel, atlas_only)
                git('rm', '--', publisher.ATLAS_FILES[publisher.AUDIO_ROUTE + 'quench.flac'])
                incomplete = commit('Remove one required audio asset')
                with self.assertRaisesRegex(ValueError, 'Incomplete committed atlas publication'):
                    auditor.expected_files(root, incomplete)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == '__main__':
    unittest.main()
