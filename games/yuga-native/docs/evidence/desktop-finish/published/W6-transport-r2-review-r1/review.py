#!/usr/bin/env python3
"""Independent bounded transport review; never materializes or invokes Git/API."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'transport-r2'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receipt = json.loads((SOURCE / 'receipt.json').read_text())
before = {n: sha(SOURCE / n) for n in receipt['artifacts']}
for name, expected in receipt['artifacts'].items():
    p = SOURCE / name
    assert p.stat().st_size == expected['bytes'] and sha(p) == expected['sha256'], name
manifest = json.loads((SOURCE / 'manifest.json').read_text())
qualification = json.loads((SOURCE / 'w6-qualification-receipt.json').read_text())
assert sha(SOURCE / 'w6-qualification-receipt.json') == 'a82fa9d2e96034831f49d4fe036c0040d0aff9952e5dbf30077bc3adfadc5b52'
expected = [qualification['packages'][x] for x in ['linux', 'windows']]
expected += [qualification[x] for x in ['export_manifest', 'package_manifest', 'checksums']]
names = ['yuga-native-linux-x86_64.zip', 'yuga-native-windows-x86_64.zip',
         'native-export-manifest.json', 'native-package-manifest.json', 'SHA256SUMS.txt']
assert len(manifest['assets']) == 5
for asset, name, pin in zip(manifest['assets'], names, expected):
    assert asset['name'] == name and asset['size'] == pin['bytes'] and asset['sha256'] == pin['sha256']
assert manifest['target'] == qualification['commit'] == '96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
assert manifest['release_id'] == 416367666
assert manifest['transport_branch'] == 'transport/yuga-desktop-finish-2026-10-18-r2'

def forbidden(*args, **kwargs):
    raise AssertionError('External subprocess/network operation forbidden in independent review')

results = {}
with tempfile.TemporaryDirectory(prefix='w6-transport-r2-', dir='/workspace/scratch') as tmp:
    copy = Path(tmp) / 'copy'
    shutil.copytree(SOURCE, copy, ignore=shutil.ignore_patterns('__pycache__'))
    with patch.object(subprocess, 'run', forbidden), patch.object(subprocess, 'Popen', forbidden), \
         patch.object(subprocess, 'check_output', forbidden), patch.object(socket, 'socket', forbidden), \
         patch.object(socket, 'create_connection', forbidden), patch.object(tempfile, 'tempdir', tmp):
        for name, output in [('test_guards.py', 'guard-tests.json'), ('test_push_guards.py', 'push-guard-tests.json')]:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                runpy.run_path(str(copy / name), run_name='__main__')
            (HERE / (name + '.stdout')).write_text(stdout.getvalue())
            result = json.loads((copy / output).read_text())
            assert result['failed'] == 0
            results[name] = result
        g = runpy.run_path(str(copy / 'generate.py'), run_name='independent_generator_import')
        assert g['MATERIALIZE'] is False
        raw = b'bounded no-object control'
        assert g['put'](raw) == hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert g['put_stream'](io.BytesIO(raw), len(raw))[1] == hashlib.sha256(raw).hexdigest()

assert before == {n: sha(SOURCE / n) for n in receipt['artifacts']}
report = {
    'passed': True, 'owner_artifacts_verified': len(before),
    'owner_receipt_sha256': sha(SOURCE / 'receipt.json'),
    'asset_pins_match_sealed_W6_qualification': True,
    'source_commit': manifest['target'], 'release_id': manifest['release_id'],
    'replayed_checks': {n: x['passed'] for n, x in results.items()},
    'default_put_and_put_stream_create_no_objects': True,
    'source_unchanged': True, 'subprocess_operations': 0, 'network_operations': 0,
    'git_objects_refs_index_mutated': False, 'engine_runs': 0,
    'scope': 'Source and mocked guards only. No materialization, upload, package execution or publication. HOLD persists.'
}
(HERE / 'checks.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, sort_keys=True))
