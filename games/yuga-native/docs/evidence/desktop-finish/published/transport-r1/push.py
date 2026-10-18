#!/usr/bin/env python3
"""Explicit fixed-draft transport push, after local identity checks and root approval."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parent

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

g = load('generator', 'generate.py')
u = load('uploader', 'reconstruct_upload.py')

def require(value, message):
    if not value:
        raise ValueError(message)

def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def expected_entries():
    manifest = u.read_manifest(ROOT / 'manifest.json')
    entries = {part['path']:part['git_blob'] for a in manifest['assets'] for part in a['parts']}
    entries.update({
        'transport/manifest.json': blob((ROOT / 'manifest.json').read_bytes()),
        'transport/reconstruct_upload.py': blob((ROOT / 'reconstruct_upload.py').read_bytes()),
        '.github/workflows/upload-ui-release-assets.yml': blob((ROOT / 'upload-ui-release-assets.yml').read_bytes()),
        '.gitattributes': blob(b'* -text -filter\n'),
    })
    require(len(entries) == 12, 'exact reviewed transport entries')
    return entries

def validate_local(receipt, tests, git=g.git, snapshot=g.snapshot):
    """No remote/API/ref operation; reject receipt drift before inspecting Git objects."""
    require(receipt.get('source_commit') == g.TARGET == u.TARGET, 'fixed source')
    require(receipt.get('transport_branch') == g.BRANCH == 'transport/yuga-desktop-finish-2026-10-18-r1', 'fixed transport branch')
    require(receipt.get('orphan') is True, 'orphan declaration')
    files = {'manifest_sha256':'manifest.json', 'uploader_sha256':'reconstruct_upload.py',
             'workflow_sha256':'upload-ui-release-assets.yml', 'generator_sha256':'generate.py'}
    for key, name in files.items():
        require(receipt.get(key) == g.sha(ROOT / name), 'current source identity: ' + name)
    require(tests.get('passed') == 22 and tests.get('failed') == 0, 'uploader guard result')
    require(tests.get('uploader_sha256') == receipt['uploader_sha256']
            and tests.get('manifest_sha256') == receipt['manifest_sha256']
            and tests.get('test_sha256') == g.sha(ROOT / 'test_guards.py'), 'tested uploader identity')
    entries = expected_entries()
    require(receipt.get('entries') == entries, 'exact current transport entries')
    for key in ['transport_commit','transport_tree']:
        require(isinstance(receipt.get(key), str) and re.fullmatch(r'[0-9a-f]{40}', receipt[key]), 'Git object format')
    require(git('cat-file', '-t', receipt['transport_commit']).decode().strip() == 'commit', 'transport commit object')
    commit = git('cat-file', '-p', receipt['transport_commit']).decode()
    headers = commit.split('\n\n', 1)[0].splitlines()
    require(headers[0] == 'tree ' + receipt['transport_tree'] and not any(x.startswith('parent ') for x in headers), 'exact parentless commit')
    actual = git('ls-tree', '-r', receipt['transport_tree']).decode().splitlines()
    expected = [f'100644 blob {oid}\t{name}' for name,oid in sorted(entries.items())]
    require(actual == expected, 'exact reviewed orphan tree')
    current = snapshot()
    require(current == receipt.get('checkout_before') == receipt.get('checkout_after'), 'normal checkout/index unchanged')
    require(current.get('head') == g.TARGET and current.get('branch') == 'refs/heads/game/yuga-native-production', 'normal source branch')
    return 'refs/heads/' + g.BRANCH

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--push-fixed-draft', action='store_true', required=True)
    parser.parse_args()
    receipt = json.loads((ROOT / 'prepush-receipt.json').read_text())
    tests = json.loads((ROOT / 'guard-tests.json').read_text())
    branch_ref = validate_local(receipt, tests)
    push_tests = json.loads((ROOT / 'push-guard-tests.json').read_text())
    require(push_tests.get('passed') == 10 and push_tests.get('failed') == 0
            and push_tests.get('push_sha256') == g.sha(Path(__file__))
            and push_tests.get('test_sha256') == g.sha(ROOT / 'test_push_guards.py'), 'tested local push guard')
    require(not g.git('ls-remote', '--heads', 'origin', branch_ref).strip(), 'new remote branch required')
    require(subprocess.run(['git', 'show-ref', '--verify', '--quiet', branch_ref], cwd=g.REPO).returncode == 1, 'new local branch required')
    release = json.loads(subprocess.check_output(['gh', 'api', 'repos/occult-kranti/ANDOLAN/releases/416367666'], cwd=g.REPO))
    u.check_release(release, u.read_manifest(ROOT / 'manifest.json'))
    require(release.get('assets') == [], 'fixed draft must still be empty before first transport push')
    (ROOT / 'release-before.json').write_text(json.dumps(release, indent=2, sort_keys=True) + '\n')
    g.git('update-ref', branch_ref, receipt['transport_commit'], '0' * 40)
    start = time.time()
    with (ROOT / 'push.log').open('wb') as log:
        proc = subprocess.run(['git', '-c', 'pack.threads=1', '-c', 'pack.window=0', 'push',
                               'origin', receipt['transport_commit'] + ':' + branch_ref],
                              cwd=g.REPO, stdout=log, stderr=subprocess.STDOUT)
    after = g.snapshot()
    result = {'transport_commit':receipt['transport_commit'], 'transport_tree':receipt['transport_tree'],
              'branch':g.BRANCH, 'push_exit_code':proc.returncode,
              'duration_seconds':round(time.time()-start, 3), 'checkout_before':receipt['checkout_before'],
              'checkout_after':after, 'head_and_index_unchanged':after == receipt['checkout_before'],
              'push_log_sha256':g.sha(ROOT / 'push.log')}
    if proc.returncode == 0:
        remote = g.git('ls-remote', '--heads', 'origin', branch_ref).decode().strip()
        require(remote == receipt['transport_commit'] + '\t' + branch_ref, 'remote transport commit')
        result['verified_remote_ref'] = remote
    (ROOT / 'push-receipt.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    print((ROOT / 'push.log').read_text())
    require(proc.returncode == 0 and result['head_and_index_unchanged'], 'push and normal checkout invariants')

if __name__ == '__main__':
    main()
