"""One anonymous, original-image TRELLIS.2 generation; never retries a GPU call."""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import json
import os
import re
import struct
import sys
import time
from concurrent.futures import TimeoutError
from urllib.parse import urlsplit, urlunsplit

URL = 'https://microsoft-trellis-2.hf.space/'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def clean(value):
    def url(match):
        p = urlsplit(match.group())
        return urlunsplit((p.scheme, p.netloc, p.path, '', ''))
    return re.sub(r'https?://[^\s<>\"\']+', url, str(value))[:2000]

parser = argparse.ArgumentParser()
parser.add_argument('--image', required=True)
parser.add_argument('--expected-sha256', required=True)
parser.add_argument('--output', required=True)
parser.add_argument('--execute', action='store_true')
options = parser.parse_args()
image = Path(options.image).resolve(strict=True)
raw = image.read_bytes()
assert hashlib.sha256(raw).hexdigest() == options.expected_sha256
assert 0 < len(raw) <= 5 * 1024 * 1024
assert raw[:8] == b'\x89PNG\r\n\x1a\n' and raw[12:16] == b'IHDR'
width, height, depth, color = struct.unpack('>IIBB', raw[16:26])
assert color == 6 and depth == 8, 'Expected 8-bit RGBA PNG'
out = Path(options.output).resolve()
out.mkdir(exist_ok=False)
receipt = {
    'started_at_utc': now(), 'status': 'PREPARED',
    'client': {'package': 'gradio-client', 'version': '2.0.1', 'anonymous': True,
               'token_argument': False, 'analytics_enabled': False,
               'transport_threads': 2, 'simultaneous_submitted_jobs': 1},
    'input': {'path': str(image), 'sha256': options.expected_sha256,
              'bytes': len(raw), 'width': width, 'height': height,
              'provenance': 'Original diya concept generated in this task; root owns full provenance.'},
    'budget': {'max_gpu_function_submissions': 1, 'generation_declared_max_gpu_seconds': 120,
               'max_paid_cost': 0, 'job_wall_timeout_seconds': 180,
               'export': 'HELD: no qualified remaining-free-quota observation; no second GPU call permitted.'},
    'calls': [], 'gpu_submission_attempts': 0, 'gpu_success_verified': False,
    'glb_produced': False,
}

def save():
    p = out/'receipt.json.tmp'
    p.write_text(json.dumps(receipt, indent=2)+'\n')
    p.replace(out/'receipt.json')

save()
if not options.execute:
    print(json.dumps({'status': 'PREPARED', 'generation_submitted': False}))
    sys.exit(0)

from gradio_client import Client, handle_file
import importlib.metadata
assert importlib.metadata.version('gradio_client') == '2.0.1'
client = None
active_job = None
exit_status = 1

def call(name, parameters, seconds, gpu=False):
    global active_job
    if gpu:
        assert receipt['gpu_submission_attempts'] == 0
        receipt['gpu_submission_attempts'] += 1
    row = {'api_name': name, 'submitted_at_utc': now(), 'gpu_function': gpu,
           'status': 'SUBMITTING', 'states': []}
    # Keep uploaded content and remote file URLs out of receipts.
    row['parameters'] = {k: ('<image-file>' if k in ('image', 'input') else v)
                         for k, v in parameters.items()}
    receipt['calls'].append(row)
    save()
    started = time.monotonic()
    active_job = client.submit(api_name=name, **parameters)
    deadline = started + seconds
    last_state = None
    while time.monotonic() < deadline:
        helper = active_job.communicator
        row['event_id'] = getattr(helper, 'event_id', None)
        state = active_job.status()
        label = str(state.code)
        if label != last_state:
            row['states'].append({'at_utc': now(), 'code': label,
                                  'rank': state.rank, 'queue_size': state.queue_size,
                                  'eta': state.eta, 'success': state.success})
            last_state = label
            save()
        try:
            result = active_job.result(timeout=min(2, max(0.01, deadline-time.monotonic())))
            row.update(status='COMPLETED', completed_at_utc=now(),
                       wall_seconds=time.monotonic()-started)
            save()
            active_job = None
            return result
        except TimeoutError:
            continue
        except Exception as error:
            row.update(status='FAILED', completed_at_utc=now(),
                       wall_seconds=time.monotonic()-started,
                       error_type=type(error).__name__, error=clean(error))
            save()
            active_job = None
            raise
    row.update(status='WALL_TIMEOUT', wall_seconds=time.monotonic()-started,
               remote_outcome='UNKNOWN; no resubmission')
    try:
        row['cancel_requested'] = bool(active_job.cancel())
    except Exception as error:
        row['cancel_error_type'] = type(error).__name__
    save()
    raise TimeoutError('Existing job timed out; cancellation requested, no GPU retry')

try:
    # Two threads are required for one job plus its SSE reader in this client.
    client = Client(URL, token=False, max_workers=2, verbose=False,
                    analytics_enabled=False, ssl_verify=True,
                    download_files=out/'downloads', httpx_kwargs={'timeout': 30.0})
    assert client.token is False
    assert not any('authorization' in key.lower() or 'token' in key.lower()
                   for key in client.headers), 'Anonymous header check failed'
    assert not client.analytics_enabled
    receipt['client']['anonymous_headers_verified'] = True
    receipt['session_hash'] = client.session_hash
    info = client.view_api(print_info=False, return_format='dict')
    (out/'live-api.json').write_text(json.dumps(info, indent=2)+'\n')
    for required in ('/start_session', '/preprocess_image', '/image_to_3d', '/extract_glb'):
        assert required in info['named_endpoints']
    parameters = {'image': None, 'seed': 23, 'resolution': '512',
                  'ss_guidance_strength': 7.5, 'ss_guidance_rescale': 0.7,
                  'ss_sampling_steps': 8, 'ss_rescale_t': 5.0,
                  'shape_slat_guidance_strength': 7.5, 'shape_slat_guidance_rescale': 0.5,
                  'shape_slat_sampling_steps': 8, 'shape_slat_rescale_t': 3.0,
                  'tex_slat_guidance_strength': 1.0, 'tex_slat_guidance_rescale': 0.0,
                  'tex_slat_sampling_steps': 8, 'tex_slat_rescale_t': 3.0}
    actual = {p['parameter_name'] for p in info['named_endpoints']['/image_to_3d']['parameters']}
    assert set(parameters) == actual, 'Live generation contract changed'
    receipt['status'] = 'RUNNING'
    save()
    call('/start_session', {}, 30)
    processed = call('/preprocess_image', {'input': handle_file(str(image))}, 45)
    processed_path = Path(processed)
    receipt['preprocessed_image'] = {'sha256': hashlib.sha256(processed_path.read_bytes()).hexdigest(),
                                     'bytes': processed_path.stat().st_size}
    parameters['image'] = handle_file(str(processed_path))
    preview = call('/image_to_3d', parameters, 180, gpu=True)
    assert isinstance(preview, str)
    (out/'preview.html').write_text(preview)
    snapshots = []
    for index, encoded in enumerate(re.findall(r'src="data:image/jpeg;base64,([^\"]+)"', preview)):
        body = base64.b64decode(encoded, validate=True)
        assert len(body) < 4 * 1024 * 1024
        p = out/f'preview-{index:02d}.jpg'
        p.write_bytes(body)
        snapshots.append({'path': p.name, 'bytes': len(body),
                          'sha256': hashlib.sha256(body).hexdigest()})
    receipt.update(status='GENERATION_COMPLETE_EXPORT_HELD', gpu_success_verified=True,
                   preview_snapshots=snapshots)
    exit_status = 0
except Exception as error:
    receipt.update(status='FAILED_OR_BLOCKED', error_type=type(error).__name__, error=clean(error))
finally:
    receipt['finished_at_utc'] = now()
    save()
    if client is not None:
        client.close()
        client.executor.shutdown(wait=False, cancel_futures=True)
    print(json.dumps({'status':receipt['status'], 'gpu_submission_attempts':receipt['gpu_submission_attempts'],
                      'gpu_success_verified':receipt['gpu_success_verified'], 'glb_produced':False,
                      'receipt':str(out/'receipt.json')}), flush=True)
    # Bound this dedicated experimental client process, including library SSE threads.
    os._exit(exit_status)
