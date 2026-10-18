#!/usr/bin/env python3
"""Build an orphan transport using a private index and streaming binary Git blobs."""
import argparse
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = Path('/workspace/ANDOLAN')
SOURCE = Path('/workspace/scratch/yuga-continuation-W6-r1/package-successor-r2/build')
RELEASE_ID = 416542426
QUALIFICATION_RECEIPTS = {'export_package': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-package-r2/qualification-receipt-uid-reviewed.json',
                    'bytes': 94575,
                    'sha256': 'e924d90af27dad48c96fcb99ad9bbbe2cfd84ac01899b2221491199baf00f400'},
 'actual_warm_cold': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W1-actual-r1/package-successor-r2/receipt.json',
                      'bytes': 4229,
                      'sha256': 'b7a3f90433247072d68b34ee7f3b03a73edca69ded4cb561d144591f687533d3'},
 'warm': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W1-actual-r1/package-successor-r2/warm/receipt.json',
          'bytes': 11372,
          'sha256': 'b71b25fbc53baa6b94a5750391d42770c43c079bb769358bbe7fb0ae54ad2226'},
 'cold': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W1-actual-r1/package-successor-r2/cold/receipt.json',
          'bytes': 9054,
          'sha256': 'e424cf6051b88ef611f3a3df56bb2a40a6df2fd4435eb05232b8ddff58f19868'},
 'independent': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1/package-native-independent-r2.json',
                 'bytes': 12491,
                 'sha256': 'bab4255a670a864d8ad76e1ded101139d5b9c1a2379c2d82e3f760c1cf48afb6'},
 'independent_visual': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W2-package-successor-r2/receipt.json',
                        'bytes': 27571,
                        'sha256': '7f07078258afcf4eb4fbde40b383db3f01b7473b79fef428c2377e20a148b3bd'},
 'direct_upload': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/published/release-polish-r1/direct-upload-receipt.json',
                   'bytes': 975,
                   'sha256': '6ede8306471b405a77f3bef3fbc3f7bb6c39a49790d235b17db1300cbe8a204c'},
 'empty_draft': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/published/release-polish-r1/draft-after-direct-upload.json',
                 'bytes': 3308,
                 'sha256': '9ef632de938bcdee8d19753f97618efa2e8049085fcdfd058d2a81cc232c4959'},
 'initial_draft': {'path': '/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/published/release-polish-r1/create-draft-response.json',
                   'bytes': 3308,
                   'sha256': '9ef632de938bcdee8d19753f97618efa2e8049085fcdfd058d2a81cc232c4959'}}
PART_COUNTS = (2, 3, 1, 1, 1)
BRANCH = 'transport/yuga-desktop-polish-2026-10-18-r2'
TARGET = '79e5c15d8a3657e16fda67acb277b2406120dcd1'
# Exact qualified successor bytes; prior public release remains unchanged.
EXPECTED = [('yuga-native-linux-x86_64.zip', 97903966, '781d904d2f6986f423274cf23ecdc16a35df65df755db5171a97a152a3c88aa8'),
 ('yuga-native-windows-x86_64.zip', 146200829, '8051586f45275c0e1956749f428a8ad2643ada69582410056597ed6f5efe01c8'),
 ('native-export-manifest.json', 465170, '104fbfd1c1f83616d5f1d55bcfe33903457b2241a4753117dbd366978f8c0e48'),
 ('native-package-manifest.json', 15546, '8a74ef1abd3b29ddc86a72a162b07fbb41f4528a426f4f652c2a024b3d399527')]
EXPECTED_SUMS_SHA256 = '026555b126ee4d6035f4ad7a920107a4e864f118399d699e6e705059891f75a5'

MATERIALIZE = False

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
    expected = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if MATERIALIZE:
        assert git('hash-object', '-w', '--stdin', data=data).decode().strip() == expected
    return expected


def put_stream(source, length):
    proc = (subprocess.Popen(['git', 'hash-object', '-w', '--stdin'], cwd=REPO,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE) if MATERIALIZE else None)
    digest = hashlib.sha256()
    blob = hashlib.sha1(b'blob ' + str(length).encode() + b'\0')
    remaining = length
    while remaining:
        block = source.read(min(remaining, 1024 * 1024))
        if not block:
            raise ValueError('source became shorter')
        remaining -= len(block)
        digest.update(block)
        blob.update(block)
        if proc:
            proc.stdin.write(block)
    oid = blob.hexdigest()
    if proc:
        proc.stdin.close()
        actual = proc.stdout.read().decode().strip()
        if proc.wait() != 0 or actual != oid:
            raise ValueError('hash-object failed or mismatched')
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


def require_bound():
    """Reject all pending identities before Git, subprocess, network or payload writes."""
    if (not isinstance(RELEASE_ID, int) or isinstance(RELEASE_ID, bool) or RELEASE_ID <= 0
            or RELEASE_ID == 416367666 or not isinstance(SOURCE, Path)
            or len(EXPECTED) != 4 or not isinstance(EXPECTED_SUMS_SHA256, str)
            or len(EXPECTED_SUMS_SHA256) != 64 or not isinstance(PART_COUNTS, tuple)
            or len(PART_COUNTS) != 5 or not all(isinstance(n, int) and n > 0 for n in PART_COUNTS)
            or not isinstance(QUALIFICATION_RECEIPTS, dict)
            or set(QUALIFICATION_RECEIPTS) != {'direct_upload', 'actual_warm_cold', 'independent_visual', 'independent', 'export_package', 'cold', 'initial_draft', 'empty_draft', 'warm'}):
        raise ValueError("UNBOUND: await new draft, qualified asset pins/census and exact export/actual/independent receipts")
    for label, record in QUALIFICATION_RECEIPTS.items():
        path = Path(record["path"])
        if (path.is_symlink() or not path.is_file() or path.stat().st_size != record["bytes"]
                or sha(path) != record["sha256"]):
            raise ValueError("qualification receipt changed: " + label)


def main():
    global MATERIALIZE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--materialize', action='store_true', help='Explicitly create Git objects/private index/orphan commit after root review; never push')
    args = parser.parse_args()
    MATERIALIZE = args.materialize
    require_bound()
    before = snapshot()
    assert before['head'] == TARGET
    assert before['branch'] == 'refs/heads/game/yuga-native-production'
    checksums = SOURCE / 'SHA256SUMS.txt'
    expected_sums = ''.join(f'{h}  {n}\n' for n, _, h in EXPECTED).encode()
    assert checksums.read_bytes() == expected_sums
    assert sha(checksums) == EXPECTED_SUMS_SHA256
    expected = EXPECTED + [('SHA256SUMS.txt', len(expected_sums), sha(checksums))]
    manifest = {'schema': 1, 'repository': 'occult-kranti/ANDOLAN',
                'release_id': RELEASE_ID, 'tag': 'yuga-desktop-polish-2026-10-18',
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
        if len(asset['parts']) != PART_COUNTS[i]:
            raise ValueError('qualified chunk census changed: ' + name)
        manifest['assets'].append(asset)
        print(json.dumps({'stored': name, 'parts': len(asset['parts']), 'bytes': size}), flush=True)
    manifest_raw = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
    (HERE / 'manifest.json').write_bytes(manifest_raw)
    script = (HERE / 'upload_template.py').read_text().replace('@@MANIFEST_SHA256@@', manifest_sha).encode()
    (HERE / 'reconstruct_upload.py').write_bytes(script)
    script_sha = hashlib.sha256(script).hexdigest()
    workflow = '''name: Upload exact reviewed YUGA desktop draft assets

on:
  push:
    branches:
      - transport/yuga-desktop-polish-2026-10-18-r2

permissions: {}

concurrency:
  group: yuga-exact-draft-assets-@@RELEASE_ID@@
  cancel-in-progress: false

jobs:
  upload:
    if: github.repository == 'occult-kranti/ANDOLAN' && github.ref == 'refs/heads/transport/yuga-desktop-polish-2026-10-18-r2' && github.event.created == true && github.event.deleted == false
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
'''.replace('@@SCRIPT_SHA@@', script_sha).replace('@@RELEASE_ID@@', str(RELEASE_ID)).encode()
    (HERE / 'upload-ui-release-assets.yml').write_bytes(workflow)
    entries['transport/manifest.json'] = put(manifest_raw)
    entries['transport/reconstruct_upload.py'] = put(script)
    entries['.github/workflows/upload-ui-release-assets.yml'] = put(workflow)
    entries['.gitattributes'] = put(b'* -text -filter\n')
    spec = importlib.util.spec_from_file_location('upload', HERE / 'reconstruct_upload.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parsed = module.read_manifest(HERE / 'manifest.json')
    if not MATERIALIZE:
        after = snapshot()
        assert before == after, 'normal checkout/index changed'
        receipt = {'schema': 1, 'mode': 'prepare-only', 'source_commit': TARGET,
                   'transport_branch': BRANCH, 'release_id': RELEASE_ID,
                   'manifest_sha256': manifest_sha, 'uploader_sha256': script_sha,
                   'workflow_sha256': hashlib.sha256(workflow).hexdigest(),
                   'generator_sha256': sha(Path(__file__)), 'checkout_before': before,
                   'checkout_after': after, 'entries': entries,
                   'verified_assets': [{k:a[k] for k in ('name','size','sha256')} for a in parsed['assets']],
                   'retained_chunk_files': 0, 'binary_chunk_count': sum(PART_COUNTS[:2]),
                   'git_objects_written': False, 'git_refs_changed': False,
                   'network_calls': 0, 'uploaded': False, 'pushed': False}
        (HERE / 'preparation-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'prepared': len(entries), 'source_assets': 5, 'git_objects_written': False}))
        return
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
    assert actual == expected_tree and len(actual) == sum(PART_COUNTS) + 4
    commit = git('commit-tree', tree, '-m', 'Transport exact reviewed desktop polish assets to draft ' + str(RELEASE_ID)).decode().strip()
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
               'retained_chunk_files': 0, 'binary_chunk_count': sum(PART_COUNTS[:2]),
               'uploaded': False, 'pushed': False}
    (HERE / 'prepush-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'commit': commit, 'tree': tree, 'assets': len(verification),
                      'normal_head_and_index_unchanged': before == after}, indent=2))


if __name__ == '__main__':
    main()
