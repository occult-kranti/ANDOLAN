#!/usr/bin/env python3
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('generator', ROOT / 'generate.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
receipt = json.loads((ROOT / 'prepush-receipt.json').read_text())
tests = json.loads((ROOT / 'guard-tests.json').read_text())
assert tests['passed'] == 22 and tests['failed'] == 0
assert tests['uploader_sha256'] == receipt['uploader_sha256']
assert g.snapshot() == receipt['checkout_before']
branch_ref = 'refs/heads/' + receipt['transport_branch']
assert not g.git('ls-remote', '--heads', 'origin', branch_ref).strip()
assert subprocess.run(['git', 'show-ref', '--verify', '--quiet', branch_ref], cwd=g.REPO).returncode == 1
release = json.loads(subprocess.check_output(['gh', 'api', 'repos/occult-kranti/ANDOLAN/releases/416367666'], cwd=g.REPO))
assert release['id'] == 416367666 and release['draft'] is True and release['prerelease'] is True
assert release['target_commitish'] == g.TARGET and release['tag_name'] == 'yuga-desktop-finish-2026-10-18'
assert release['assets'] == []
(ROOT / 'release-before.json').write_text(json.dumps(release, indent=2, sort_keys=True) + '\n')
g.git('update-ref', branch_ref, receipt['transport_commit'], '0' * 40)
start = time.time()
with (ROOT / 'push.log').open('wb') as log:
    proc = subprocess.run(['git', '-c', 'pack.threads=1', '-c', 'pack.window=0', 'push',
                           'origin', receipt['transport_commit'] + ':' + branch_ref],
                          cwd=g.REPO, stdout=log, stderr=subprocess.STDOUT)
after = g.snapshot()
result = {'transport_commit': receipt['transport_commit'], 'transport_tree': receipt['transport_tree'],
          'branch': receipt['transport_branch'], 'push_exit_code': proc.returncode,
          'duration_seconds': round(time.time() - start, 3), 'checkout_before': receipt['checkout_before'],
          'checkout_after': after, 'head_and_index_unchanged': after == receipt['checkout_before'],
          'push_log_sha256': hashlib.sha256((ROOT / 'push.log').read_bytes()).hexdigest()}
if proc.returncode == 0:
    remote = g.git('ls-remote', '--heads', 'origin', branch_ref).decode().strip()
    assert remote == receipt['transport_commit'] + '\t' + branch_ref
    result['verified_remote_ref'] = remote
(ROOT / 'push-receipt.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2, sort_keys=True))
print((ROOT / 'push.log').read_text())
assert proc.returncode == 0 and result['head_and_index_unchanged']
