#!/usr/bin/env python3
"""Bounded Chromium UI checks with explicit synthetic status fixtures.

Uses installed Python Playwright and Chromium; starts its own loopback file server.
Evidence goes outside the checkout. No fixture is written to published status.json.
"""
import argparse
import copy
import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def run(output):
    web = Path(__file__).resolve().parent
    output.mkdir(parents=True, exist_ok=False)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    fixture = {
        'schema_version': 1, 'mode': 'live', 'collected_at': now,
        'run': {'id': 'ui-verification-fixture', 'title': 'Original art. Measured production.', 'updated_at': now,
                'summary': 'Synthetic UI test data. This browser run tests controls and layout; it is not production activity.'},
        'source': {'branch': 'game/yuga-native-production', 'commit': '7c7259260782c181b29276c4429353f9445f2a22', 'dirty': True},
        'host': {'logical_cpus': 4, 'quota_cpus': 4, 'memory_total_bytes': 32 * 1024**3,
                 'memory_available_bytes': 23 * 1024**3, 'gpu': {'available': False, 'devices': [], 'reason': 'No GPU attached to this fixture. A public service is a separate job.'}},
        'jobs': [
            {'id': 'hero', 'title': 'Rama · material and lighting intake', 'owner': 'Hero artist', 'stage': 'Source inspection',
             'status': 'running', 'device': 'CPU', 'model': 'Blender 4.3.2', 'started_at': now, 'updated_at': now,
             'summary': 'Review the existing original character and source rig before accepting a material change.',
             'outputs': [{'label': 'Original render', 'url': './media/hero-concept.png'}],
             'next_step': 'Inspect matched front, side and rear views, then test motion contact.'},
            {'id': 'diya', 'title': 'Diya · generated source candidate', 'owner': 'Asset intake', 'stage': 'Independent review',
             'status': 'review', 'device': 'Public GPU service', 'model': 'TRELLIS.2 public demo', 'started_at': now, 'updated_at': now,
             'summary': 'An original generated mesh is a source candidate, with topology and collision still open.', 'outputs': [],
             'next_step': 'Reduce source density and author an appropriate flame effect.'},
            {'id': 'authority', 'title': 'Native authority · next dependency gate', 'owner': 'Networking', 'stage': 'Planned',
             'status': 'queued', 'device': 'CPU', 'model': None, 'updated_at': now, 'summary': 'No authority work is running in this UI fixture.',
             'outputs': [], 'next_step': 'Exercise a complete two-client match before expansion.'},
        ],
        'assets': [
            {'id': 'rama', 'title': 'Rama · concept reference', 'status': 'Concept, not a runtime acceptance',
             'image_url': './media/hero-concept.png', 'summary': 'Existing original reference shown to test the dashboard image presentation.'},
            {'id': 'diya', 'title': 'Worked-brass diya', 'status': 'Source candidate', 'image_url': './media/diya-front.png',
             'summary': 'Actual prior Blender render. UI fixture does not change its production status.'},
            {'id': 'diya-side', 'title': 'Diya · side inspection', 'status': 'Review pending', 'image_url': './media/diya-side.png',
             'summary': 'A source inspection view, not a finished environment.'},
        ],
        'milestones': [{'id': 'P1', 'title': 'Accept one hero and arena', 'status': 'review', 'evidence': 'Continuous motion, source provenance and actual gameplay views remain separate gates.'},
                       {'id': 'FG06', 'title': 'Complete native 3v3', 'status': 'queued', 'evidence': 'Requires accepted shared authority and real rendered clients.'}],
        'sources': [{'name': 'Godot Engine', 'url': 'https://github.com/godotengine/godot', 'license': 'MIT', 'status': 'Existing project engine'},
                    {'name': 'Blender', 'url': 'https://github.com/blender/blender', 'license': 'GPL-3.0', 'status': 'Existing source-art tool'}],
    }
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(web)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    checks, screenshots, errors = [], [], []

    def check(name, passed):
        checks.append({'name': name, 'passed': bool(passed)})
        if not passed:
            raise AssertionError(name)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        version = browser.version
        page = browser.new_page(viewport={'width': 1440, 'height': 1080}, reduced_motion='reduce')
        page.on('pageerror', lambda error: errors.append(str(error)))
        mode = {'value': 'live', 'body': fixture}

        def route_api(route):
            if mode['value'] != 'live':
                route.fulfill(status=503, body='offline')
            else:
                route.fulfill(status=200, content_type='application/json', body=json.dumps(mode['body']))

        def route_snapshot(route):
            if mode['value'] == 'error':
                route.fulfill(status=404, body='missing')
            else:
                body = copy.deepcopy(mode['body'])
                body['mode'] = 'snapshot'
                route.fulfill(status=200, content_type='application/json', body=json.dumps(body))

        page.route('**/api/status', route_api)
        page.route('**/status.json', route_snapshot)
        page.goto(base)
        page.get_by_text('Live worker observation', exact=True).wait_for()
        check('live_label_and_no_gpu_observation', 'No attached GPU observed' in page.locator('#gpu-observation').inner_text())
        check('three_job_buttons', page.locator('.job-row').count() == 3)
        page.locator('#status-filter').select_option('review')
        check('status_filter', page.locator('.job-row').count() == 1 and 'Diya' in page.locator('.job-row').inner_text())
        check('filter_selects_visible_job', 'Diya' in page.locator('#inspector-title').inner_text())
        page.locator('#device-filter').select_option('CPU')
        check('empty_filter_state', page.locator('#empty-queue').is_visible())
        check('empty_filter_clears_inspector', page.locator('#inspector-title').inner_text() == 'No job selected')
        page.locator('#empty-clear').click()
        check('clear_filter_state', page.locator('.job-row').count() == 3)
        page.locator('.job-row').nth(1).focus()
        page.keyboard.press('Enter')
        check('keyboard_select_job', 'Diya' in page.locator('#inspector-title').inner_text())
        check('keyboard_focus_preserved_after_selection', page.evaluate('document.activeElement.dataset.jobId') == 'diya')
        page.locator('#pause-button').click()
        check('pause_and_historical_running', page.locator('#pause-button').get_attribute('aria-pressed') == 'true' and 'Recorded running' in page.locator('.job-row').first.inner_text())
        page.locator('#refresh-button').click()
        page.wait_for_timeout(100)
        check('manual_refresh_does_not_resume', page.locator('#pause-button').get_attribute('aria-pressed') == 'true')
        page.locator('#pause-button').click()
        page.wait_for_timeout(100)
        check('resume', page.locator('#pause-button').get_attribute('aria-pressed') == 'false')
        check('reduced_motion', page.evaluate('matchMedia("(prefers-reduced-motion:reduce)").matches'))
        for width, height, name in [(1440, 1080, 'desktop'), (390, 844, 'narrow'), (720, 550, 'zoom-equivalent-720css'), (320, 740, 'minimum-320css')]:
            page.set_viewport_size({'width': width, 'height': height})
            page.screenshot(path=str(output / f'{name}.png'), full_page=True)
            screenshots.append(str(output / f'{name}.png'))
            check(f'no_document_overflow_{width}', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        page.set_viewport_size({'width': 1440, 'height': 1080})
        mode['value'] = 'snapshot'
        page.locator('#refresh-button').click()
        page.get_by_text('Saved snapshot — not live', exact=True).wait_for()
        check('snapshot_labels_running_as_historical', 'Recorded running' in page.locator('.job-row').first.inner_text())
        check('snapshot_age_visible', 'Observed' in page.locator('#connection-age').inner_text())
        page.screenshot(path=str(output / 'saved-snapshot.png'), full_page=True)
        screenshots.append(str(output / 'saved-snapshot.png'))

        long = copy.deepcopy(fixture)
        long['run']['title'] = 'A deliberately long production title to verify wrapping and readable content at a narrow viewport'
        long['jobs'][0]['title'] = 'A' * 190
        long['jobs'][0]['summary'] = '<img src=x onerror="window.__unsafe=true">'
        long['jobs'][0]['outputs'] = [{'label': 'Unsafe URL must be inert', 'url': 'javascript:window.__unsafe=true'}]
        mode['body'] = long
        page.set_viewport_size({'width': 320, 'height': 740})
        page.locator('#refresh-button').click()
        page.wait_for_timeout(150)
        page.locator('.job-row').first.click()
        check('long_content_no_overflow', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check('untrusted_text_is_literal', '<img src=x' in page.locator('#job-detail').inner_text() and page.locator('#job-detail img').count() == 0)
        check('unsafe_link_is_inert', page.locator('#job-detail a').count() == 0 and not page.evaluate('Boolean(window.__unsafe)'))
        empty = copy.deepcopy(fixture)
        for key in ['jobs', 'assets', 'milestones', 'sources']:
            empty[key] = []
        mode['body'] = empty
        page.locator('#refresh-button').click()
        page.wait_for_timeout(150)
        check('empty_assets_and_roadmap', page.locator('#empty-artifacts').is_visible() and page.locator('#empty-roadmap').is_visible())
        check('empty_sources', page.locator('#empty-sources').is_visible())
        page.close()
        mode['value'] = 'error'
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.route('**/api/status', route_api)
        page.route('**/status.json', route_snapshot)
        page.goto(base)
        page.locator('#error-panel').wait_for(state='visible')
        check('full_error_state_and_retry', page.locator('#retry-button').is_visible() and not page.locator('#dashboard').is_visible())
        page.screenshot(path=str(output / 'unavailable.png'), full_page=True)
        screenshots.append(str(output / 'unavailable.png'))
        mode['value'] = 'live'
        mode['body'] = fixture
        mode['body']['collected_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        page.locator('#retry-button').click()
        page.get_by_text('Live worker observation', exact=True).wait_for()
        check('error_recovery', page.locator('#dashboard').is_visible())
        malformed = copy.deepcopy(fixture)
        malformed['jobs'].append(None)
        mode['body'] = malformed
        page.close()
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/api/status', route_api)
        page.route('**/status.json', route_snapshot)
        page.goto(base)
        page.locator('#error-panel').wait_for(state='visible')
        check('null_job_rejected_with_recovery', page.locator('#retry-button').is_visible())
        malformed = copy.deepcopy(fixture)
        malformed['host'] = None
        mode['body'] = malformed
        page.locator('#retry-button').click()
        page.wait_for_timeout(100)
        check('null_context_rejected', page.locator('#error-panel').is_visible())
        browser.close()
    server.shutdown()
    check('no_page_javascript_errors', errors == [])
    receipt = {'status': 'PASS', 'recorded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'scope': 'Synthetic UI fixtures; no game/model/GPU execution. Chromium only. 720 CSS-pixel capture approximates the layout width of a 1440px display at 200% zoom; actual browser zoom and a screen reader were not exercised.',
               'browser': version, 'checks': checks, 'screenshots': screenshots, 'javascript_errors': errors}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'checks': len(checks), 'receipt': str(output / 'receipt.json'), 'screenshots': screenshots}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(args.output)
