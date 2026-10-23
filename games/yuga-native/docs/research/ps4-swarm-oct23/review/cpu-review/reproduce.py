#!/usr/bin/env python3
"""Local mock-only review reproductions; performs no downloads or inference."""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = Path('/workspace/scratch/ps4-swarm-oct23/cpu/reusable/cpu_llama.py')
spec = importlib.util.spec_from_file_location('cpu_llama_review', SOURCE)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
findings = {}

with tempfile.TemporaryDirectory(prefix='symlink-', dir=HERE) as tmp:
    base = Path(tmp)
    root = base / 'cache'
    (root / 'evidence').mkdir(parents=True)
    (root / 'models').mkdir()
    destination = root / 'models' / 'tiny.gguf'
    outside = base / 'outside-cache.gguf'
    destination.with_name(destination.name + '.part').symlink_to(outside)
    payload = b'mock artifact only\n'
    sha = hashlib.sha256(payload).hexdigest()
    def fake_curl(argv, **kwargs):
        Path(argv[argv.index('--output') + 1]).write_bytes(payload)
        return SimpleNamespace(returncode=0, stdout=f'200\n{len(payload)}\n0.001\n', stderr='')
    with patch.object(helper.subprocess, 'run', side_effect=fake_curl):
        result = helper.download(root, 'https://example.invalid/not-requested', destination,
                                 len(payload), sha, 'mock')
    findings['dangling_partial_symlink'] = {
        'status': result['status'],
        'file_written_outside_cache': outside.read_bytes() == payload,
        'promoted_model_is_symlink': destination.is_symlink(),
        'checked_file_accepts_symlink': helper.checked_file(destination, len(payload), sha),
        'transport': 'mocked subprocess; zero network requests',
    }

class FakeProcess:
    def __init__(self, *args, **kwargs):
        self.returncode = None
    def poll(self):
        return self.returncode
    def terminate(self):
        self.returncode = -15
    def kill(self):
        self.returncode = -9
    def wait(self, **kwargs):
        return self.returncode

class FakeSocket:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def bind(self, *args):
        pass

with tempfile.TemporaryDirectory(prefix='wrong-model-', dir=HERE) as tmp:
    root = Path(tmp)
    (root / 'evidence').mkdir()
    (root / 'models').mkdir()
    (root / 'build/bin').mkdir(parents=True)
    weights = root / 'models' / 'mock.gguf'
    weights.write_bytes(b'not real weights')
    binary = root / 'build/bin/llama-server'
    binary.write_bytes(b'not executable; subprocess is mocked')
    manifest = copy.deepcopy(helper.MANIFEST)
    manifest['model'].update(filename=weights.name, bytes=weights.stat().st_size,
                             sha256=helper.digest(weights))
    (root / 'evidence/build-receipt.json').write_text(json.dumps({
        'source_commit': manifest['source']['commit'], 'binary_sha256': helper.digest(binary)
    }))
    def fake_http(base, endpoint, payload=None):
        if endpoint == '/health':
            return {'status': 'ok'}
        if endpoint == '/v1/models':
            return {'data': [{'id': 'unrelated-model'}]}
        if endpoint == '/v1/chat/completions':
            return {'model': 'unrelated-model', 'usage': {'completion_tokens': 1},
                    'choices': [{'message': {'content': 'incorrect non-JSON output'}}]}
        raise AssertionError(endpoint)
    with patch.object(helper, 'MANIFEST', manifest), \
         patch.object(helper.socket, 'socket', FakeSocket), \
         patch.object(helper.subprocess, 'Popen', FakeProcess), \
         patch.object(helper, 'local_json', side_effect=fake_http):
        result = helper.qualify(root, 8093)
    findings['wrong_model_qualification'] = {
        'status': result['status'],
        'real_inference_performed': result['real_inference_performed'],
        'returned_models': result['models'],
        'completion_model': result['completion']['model'],
        'expected_model': manifest['server_alias'],
        'bounded_content_check_passed': result['bounded_content_check_passed'],
        'transport': 'mocked process/socket/HTTP; zero network requests or inference',
    }

with tempfile.TemporaryDirectory(prefix='curl-config-', dir=HERE) as tmp:
    config = Path(tmp) / '.curlrc'
    config.write_text('definitely-not-a-curl-option = 1\n')
    env = {**os.environ, 'CURL_HOME': tmp}
    ordinary = subprocess.run(['curl', '--version'], capture_output=True, text=True, env=env, check=False)
    disabled = subprocess.run(['curl', '--disable', '--version'], capture_output=True, text=True, env=env, check=False)
    findings['ambient_curl_config'] = {
        'normal_invocation_reads_config': 'definitely-not-a-curl-option' in ordinary.stderr,
        'leading_disable_ignores_config': 'definitely-not-a-curl-option' not in disabled.stderr,
        'transport': 'curl --version only; zero network requests',
    }

with tempfile.TemporaryDirectory(prefix='failed-receipt-', dir=HERE) as tmp:
    root = Path(tmp)
    (root / 'evidence').mkdir()
    receipt = root / 'evidence/mock-build.json'
    receipt.write_text(json.dumps({'exit': 0, 'old_success_marker': True}))
    process = FakeProcess()
    process.pid = 999999
    def terminate_mock(*args):
        process.returncode = -15
    with patch.object(helper.subprocess, 'Popen', return_value=process), \
         patch.object(helper.os, 'killpg', side_effect=terminate_mock), \
         patch.object(helper.time, 'monotonic', side_effect=[0, 10]):
        try:
            helper.run_logged(root, ['mock-build-not-executed'], 'mock-build', timeout=1)
        except RuntimeError as error:
            failure = str(error)
    findings['timeout_receipt'] = {
        'error': failure,
        'previous_success_receipt_preserved': json.loads(receipt.read_text()).get('old_success_marker') is True,
        'child_stopped': process.returncode is not None,
        'transport': 'mocked process and clock; no real process launch',
    }

findings['reviewed_source_sha256'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
(HERE / 'reproduction-results.json').write_text(json.dumps(findings, indent=2) + '\n')
print(json.dumps(findings, indent=2))
