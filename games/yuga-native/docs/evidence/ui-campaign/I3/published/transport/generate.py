#!/usr/bin/env python3
"""Build an orphan transport using a private index and streaming binary Git blobs."""
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = Path('/workspace/ANDOLAN')
SOURCE = Path('/workspace/scratch/ui-campaign/I3/package-r3')
BRANCH = 'release/yuga-native-ui-2026-10-18-assets'
TARGET = '9e81a7c849837dea477ddb5a8c93f43665774573'
EXPECTED = [
    ('yuga-native-linux-x86_64.zip', 137812335, '56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5'),
    ('yuga-native-windows-x86_64.zip', 145813678, '16f6e210fef90f26c1c725e503805fb5e9c4ee76d64e86cb2ff7b0788ea186c5'),
    ('native-export-manifest.json', 397267, '9b181f1c67e32de6481cd9256c61b38eb54de6ce2afe54e05f2a68ae2931d75b'),
    ('native-package-manifest.json', 12765, '12010a4eae0b6645d946e5aaa8b52daba5f8f233425356aa942891ab0b87c1b2'),
]
LIMIT = 48 * 1024 * 1024


def git(*args, data=None, env=None):
    return subprocess.run(['git', *args], cwd=REPO, input=data, env=env,
                          check=True, stdout=subprocess.PIPE).stdout


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def snapshot():
    index = Path(git('rev-parse', '--git-path', 'index').decode().strip())
    if not index.is_absolute():
        index = REPO / index
    return {'head': git('rev-parse', 'HEAD').decode().strip(),
            'branch': git('symbolic-ref', 'HEAD').decode().strip(),
            'index_sha256': sha(index)}


def put(data):
    return git('hash-object', '-w', '--stdin', data=data).decode().strip()


def put_stream(source, length):
    proc = subprocess.Popen(['git', 'hash-object', '-w', '--stdin'], cwd=REPO,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    digest = hashlib.sha256()
    remaining = length
    while remaining:
        block = source.read(min(remaining, 1024 * 1024))
        if not block:
            raise ValueError('source became shorter')
        remaining -= len(block)
        digest.update(block)
        proc.stdin.write(block)
    proc.stdin.close()
    oid = proc.stdout.read().decode().strip()
    if proc.wait() != 0:
        raise ValueError('hash-object failed')
    return oid, digest.hexdigest()


@contextlib.contextmanager
def blob_reader(part):
    p = subprocess.Popen(['git', 'cat-file', 'blob', part['git_blob']], cwd=REPO,
                         stdout=subprocess.PIPE)
    try:
        yield p.stdout
    finally:
        p.stdout.close()
        if p.wait() != 0:
            raise ValueError('cat-file failed')


def main():
    before = snapshot()
    assert before['head'] == TARGET
    assert before['branch'] == 'refs/heads/game/yuga-native-production'
    checksums = HERE.parent / 'SHA256SUMS.txt'
    expected_sums = ''.join(f'{h}  {n}\n' for n, _, h in EXPECTED).encode()
    assert checksums.read_bytes() == expected_sums
    expected = EXPECTED + [('SHA256SUMS.txt', len(expected_sums), sha(checksums))]
    manifest = {'schema': 1, 'repository': 'occult-kranti/ANDOLAN',
                'release_id': 416177473, 'tag': 'yuga-native-ui-2026-10-18',
                'target': TARGET, 'transport_branch': BRANCH,
                'chunk_limit': LIMIT, 'assets': []}
    entries = {}
    for i, (name, size, digest) in enumerate(expected):
        source = SOURCE / name if i < 4 else checksums
        assert source.is_file() and not source.is_symlink()
        assert source.stat().st_size == size and sha(source) == digest, name
        asset = {'name': name, 'size': size, 'sha256': digest, 'parts': []}
        with source.open('rb') as f:
            remaining = size
            j = 0
            while remaining:
                amount = min(LIMIT, remaining)
                path = (f'transport/chunks/{"linux" if i == 0 else "windows"}.{j:03d}.bin'
                        if i < 2 else f'transport/files/{name}')
                oid, part_sha = put_stream(f, amount)
                entries[path] = oid
                asset['parts'].append({'path': path, 'size': amount, 'sha256': part_sha,
                                       'git_blob': oid})
                remaining -= amount
                j += 1
            assert f.read(1) == b''
        assert sha(source) == digest, 'source changed while reading'
        manifest['assets'].append(asset)
        print(json.dumps({'stored': name, 'parts': len(asset['parts']), 'bytes': size}), flush=True)
    manifest_raw = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    (HERE / 'manifest.json').write_bytes(manifest_raw)
    script = (HERE / 'upload_template.py').read_text().replace('@@MANIFEST_SHA256@@', manifest_sha).encode()
    (HERE / 'reconstruct_upload.py').write_bytes(script)
    script_sha = hashlib.sha256(script).hexdigest()
    workflow = '''name: Upload exact reviewed YUGA UI draft assets

on:
  push:
    branches:
      - release/yuga-native-ui-2026-10-18-assets

permissions: {}

concurrency:
  group: yuga-exact-draft-assets-416177473
  cancel-in-progress: false

jobs:
  upload:
    if: github.repository == 'occult-kranti/ANDOLAN' && github.ref == 'refs/heads/release/yuga-native-ui-2026-10-18-assets' && github.event.created == true && github.event.deleted == false
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2, existing repo pin
        with:
          fetch-depth: 1
          persist-credentials: false
          lfs: false
          submodules: false
      - name: Verify transport and reconstruct exact reviewed files
        shell: bash
        run: |
          set -euo pipefail
          echo "@@SCRIPT_SHA@@  transport/reconstruct_upload.py" | sha256sum --check --strict
          python3 transport/reconstruct_upload.py verify --manifest transport/manifest.json --output "$RUNNER_TEMP/exact-assets"
      - name: Upload only to the fixed existing draft; never publish or clobber
        shell: bash
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          python3 transport/reconstruct_upload.py upload --manifest transport/manifest.json --output "$RUNNER_TEMP/exact-assets" | tee "$RUNNER_TEMP/exact-upload-receipt.json"
'''.replace('@@SCRIPT_SHA@@', script_sha).encode()
    (HERE / 'upload-ui-release-assets.yml').write_bytes(workflow)
    entries['transport/manifest.json'] = put(manifest_raw)
    entries['transport/reconstruct_upload.py'] = put(script)
    entries['.github/workflows/upload-ui-release-assets.yml'] = put(workflow)
    entries['.gitattributes'] = put(b'* -text -filter\n')
    spec = importlib.util.spec_from_file_location('upload', HERE / 'reconstruct_upload.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parsed = module.read_manifest(HERE / 'manifest.json')
    verification = module.verify_streams(parsed, blob_reader)
    private_index = HERE / 'private.index'
    assert not private_index.exists(), 'use a fresh private index'
    env = dict(os.environ, GIT_INDEX_FILE=str(private_index))
    git('read-tree', '--empty', env=env)
    for name, oid in sorted(entries.items()):
        git('update-index', '--add', '--cacheinfo', f'100644,{oid},{name}', env=env)
    tree = git('write-tree', env=env).decode().strip()
    actual = git('ls-tree', '-r', tree).decode().splitlines()
    expected_tree = [f'100644 blob {oid}\t{name}' for name, oid in sorted(entries.items())]
    assert actual == expected_tree and len(actual) == 13
    commit = git('commit-tree', tree, '-m', 'Transport exact reviewed UI release assets to draft 416177473').decode().strip()
    raw_commit = git('cat-file', '-p', commit).decode()
    assert not any(x.startswith('parent ') for x in raw_commit.splitlines())
    after = snapshot()
    assert before == after, 'normal checkout/index changed'
    receipt = {'schema': 1, 'source_commit': TARGET, 'transport_branch': BRANCH,
               'transport_commit': commit, 'transport_tree': tree, 'orphan': True,
               'manifest_sha256': manifest_sha, 'uploader_sha256': script_sha,
               'workflow_sha256': hashlib.sha256(workflow).hexdigest(),
               'generator_sha256': sha(Path(__file__)), 'checkout_before': before,
               'checkout_after': after, 'entries': entries, 'verified_assets': verification,
               'retained_chunk_files': 0, 'binary_chunk_count': 6,
               'uploaded': False, 'pushed': False}
    (HERE / 'prepush-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'commit': commit, 'tree': tree, 'assets': len(verification),
                      'normal_head_and_index_unchanged': before == after}, indent=2))


if __name__ == '__main__':
    main()
