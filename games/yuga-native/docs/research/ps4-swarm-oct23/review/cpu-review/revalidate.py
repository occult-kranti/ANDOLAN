#!/usr/bin/env python3
"""Independent regression reproductions: mocked transfer/server, no network."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = Path('/workspace/scratch/ps4-swarm-oct23/cpu/reusable/cpu_llama.py')
spec = importlib.util.spec_from_file_location('cpu_review_revalidated', SOURCE)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
checks = {}


class FakeProcess:
    pid = 999999
    def __init__(self, *args, **kwargs):
        self.returncode = None
        self.environment = kwargs.get('env', {})
    def poll(self):
        return self.returncode
    def terminate(self):
        self.returncode = -15
    def kill(self):
        self.returncode = -9
    def wait(self, **kwargs):
        return self.returncode


with tempfile.TemporaryDirectory(prefix='cpu-fixed-download-') as temporary:
    base = Path(temporary)
    root = base / 'cache'
    (root / 'evidence').mkdir(parents=True)
    (root / 'models').mkdir()
    artifact = root / 'models/tiny.gguf'
    partial = artifact.with_name(artifact.name + '.part')
    outside = base / 'outside.gguf'
    payload = b'mocked artifact, no weights\n'
    sha = hashlib.sha256(payload).hexdigest()
    partial.symlink_to(outside)
    with patch.object(helper.subprocess, 'run') as curl:
        try:
            helper.download(root, 'https://example.invalid/unrequested', artifact, len(payload), sha, 'mock')
            rejected = False
        except RuntimeError:
            rejected = True
        checks['dangling_partial_rejected'] = rejected and not curl.called and not outside.exists()
    partial.unlink()
    (root / 'models').rmdir()
    (base / 'outside-models').mkdir()
    (root / 'models').symlink_to(base / 'outside-models', target_is_directory=True)
    with patch.object(helper.subprocess, 'run') as curl:
        try:
            helper.download(root, 'https://example.invalid/unrequested', artifact, len(payload), sha, 'mock')
            rejected = False
        except RuntimeError:
            rejected = True
        checks['artifact_parent_symlink_rejected'] = rejected and not curl.called
    (root / 'models').unlink()
    (root / 'models').mkdir()
    invocation = []
    def transfer(argv, **kwargs):
        invocation.append(argv)
        os.write(kwargs['stdout'].fileno(), payload)
        return SimpleNamespace(returncode=0, stderr='mocked transfer')
    with patch.object(helper.subprocess, 'run', side_effect=transfer):
        result = helper.download(root, 'https://example.invalid/unrequested', artifact, len(payload), sha, 'mock')
    checks['exclusive_regular_artifact_verified'] = result['status'] == 'VERIFIED' and artifact.read_bytes() == payload and not artifact.is_symlink() and not partial.exists()
    checks['curl_config_disabled'] = invocation[0][:2] == ['curl', '--disable'] and invocation[0][invocation[0].index('--output') + 1] == '-'


def model_check(listed_alias, completed_alias, budget_failure=False):
    with tempfile.TemporaryDirectory(prefix='cpu-fixed-model-') as temporary:
        root = Path(temporary)
        (root / 'evidence').mkdir()
        (root / 'models').mkdir()
        (root / 'build/bin').mkdir(parents=True)
        model = root / 'models/mock.gguf'
        model.write_bytes(b'not model weights')
        binary = root / 'build/bin/llama-server'
        binary.write_bytes(b'not executable; launch mocked')
        manifest = copy.deepcopy(helper.MANIFEST)
        manifest['model'].update(filename=model.name, bytes=model.stat().st_size,
                                  sha256=helper.digest(model))
        (root / 'evidence/build-receipt.json').write_text(json.dumps({
            'source_commit': manifest['source']['commit'], 'binary_sha256': helper.digest(binary)}))
        calls = []
        process = FakeProcess()
        def launch(*args, **kwargs):
            process.environment = kwargs['env']
            return process
        def http(base, endpoint, payload=None, api_key=None):
            calls.append((endpoint, api_key))
            if endpoint == '/health':
                return {'status': 'ok'}
            if endpoint == '/v1/models':
                return {'data': [{'id': listed_alias}]}
            return {'model': completed_alias, 'usage': {'completion_tokens': 1},
                    'choices': [{'message': {'content': 'not valid JSON'}}]}
        with patch.object(helper, 'MANIFEST', manifest), patch.object(helper.socket, 'socket'), \
                patch.object(helper.subprocess, 'Popen', side_effect=launch), \
                patch.object(helper, 'local_json', side_effect=http), \
                patch.object(helper, 'check_budget', side_effect=RuntimeError('final budget') if budget_failure else None,
                             return_value=0):
            result = helper.qualify(root, 8093)
        saved = json.loads((root / 'evidence/qualification.json').read_text())
        key = process.environment['LLAMA_API_KEY']
        bound = bool(key) and all(k == key for _, k in calls) and key not in json.dumps(saved)
        return result, saved, calls, bound


alias = helper.MANIFEST['server_alias']
result, saved, calls, bound = model_check('unrelated-model', 'unrelated-model')
checks['wrong_inventory_blocks_completion'] = result['status'] == 'QUALIFICATION_FAILED' and not result['real_inference_performed'] and len(calls) == 2
checks['per_launch_key_bound_and_omitted'] = bound
result, saved, calls, bound = model_check(alias, 'unrelated-model')
checks['wrong_completion_blocks_success'] = result['status'] == 'QUALIFICATION_FAILED' and not result['real_inference_performed']
result, saved, calls, bound = model_check(alias, alias, budget_failure=True)
checks['final_budget_failure_saved'] = saved['status'] == 'QUALIFICATION_FAILED' and 'final budget' in saved['budget_error'] and saved['server_stopped']

with tempfile.TemporaryDirectory(prefix='cpu-fixed-receipt-') as temporary:
    root = Path(temporary)
    (root / 'evidence').mkdir()
    receipt = root / 'evidence/mock-build.json'
    receipt.write_text(json.dumps({'status': 'PASSED', 'exit': 0, 'old_marker': True}))
    process = FakeProcess()
    def terminate_group(*args):
        process.terminate()
    with patch.object(helper.subprocess, 'Popen', return_value=process), \
            patch.object(helper.os, 'killpg', side_effect=terminate_group):
        try:
            helper.run_logged(root, ['not-executed'], 'mock-build', timeout=-1)
        except RuntimeError:
            pass
    saved = json.loads(receipt.read_text())
    checks['timeout_replaces_stale_success'] = saved['status'] == 'FAILED' and 'old_marker' not in saved and saved['exit'] == -15 and 'time budget' in saved['error']

with tempfile.TemporaryDirectory(prefix='cpu-fixed-preflight-') as temporary:
    root = Path(temporary)
    (root / 'evidence').mkdir()
    (root / 'models').mkdir()
    (root / 'build/bin').mkdir(parents=True)
    weights = root / 'models/mock.gguf'
    weights.write_bytes(b'not weights')
    binary = root / 'build/bin/llama-server'
    binary.write_bytes(b'altered binary, never executable')
    manifest = copy.deepcopy(helper.MANIFEST)
    manifest['model'].update(filename=weights.name, bytes=weights.stat().st_size,
                              sha256=helper.digest(weights))
    (root / 'evidence/build-receipt.json').write_text(json.dumps({
        'source_commit': manifest['source']['commit'], 'binary_sha256': '0' * 64}))
    receipt = root / 'evidence/qualification.json'
    receipt.write_text(json.dumps({'status': 'REAL_INFERENCE_VERIFIED', 'old_marker': True}))
    with patch.object(helper, 'MANIFEST', manifest), \
            patch.object(sys, 'argv', [str(SOURCE), 'qualify', '--cache-dir', str(root)]), \
            patch.object(sys, 'stdout', io.StringIO()), patch.object(helper.subprocess, 'Popen') as launch:
        exit_code = helper.main()
    saved = json.loads(receipt.read_text())
    checks['binary_preflight_replaces_stale_success'] = exit_code == 1 and not launch.called and saved['status'] == 'QUALIFICATION_FAILED' and not saved['real_inference_performed'] and 'old_marker' not in saved and 'does not match' in saved['error']

report = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
          'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'source_path': str(SOURCE), 'network_requests': 0, 'real_inference_runs': 0,
          'real_model_downloads': 0, 'real_builds': 0}
(HERE / 'revalidation-results.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
