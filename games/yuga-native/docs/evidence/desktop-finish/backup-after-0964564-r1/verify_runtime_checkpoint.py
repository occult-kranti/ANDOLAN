"""Read-only verification of the exact owner-staged runtime checkpoint."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path('/workspace/ANDOLAN')
OUT = Path(__file__).resolve().parent / 'runtime-checkpoint-verification'
STAGE = Path('/workspace/scratch/yuga-frontage-runtime-stage-r1')
COMMIT = '0964564d1ba283a5ac0aee8eab0a6cccd8f443f3'
PARENT = '0412db42f0a3da8afa1c30b33be6239d04f7afe8'

def git(*args):
    return subprocess.check_output(['git', '--no-optional-locks', *args], cwd=ROOT)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def state():
    return {'head': git('rev-parse', 'HEAD').decode().strip(),
            'index_sha256': sha(ROOT / '.git/index')}

def main():
    before = state()
    assert before['head'] == COMMIT
    manifest = json.loads((STAGE / 'manifest.json').read_text())
    rows = {row['path']: row for row in manifest['files']}
    assert manifest['parent'] == PARENT and len(rows) == len(manifest['files']) == 128
    assert git('rev-parse', COMMIT + '^').decode().strip() == PARENT
    changed = {x.decode() for x in git('diff-tree', '--no-commit-id', '--name-only',
                                      '-r', '-z', COMMIT).split(b'\0') if x}
    assert changed == set(rows)
    tree = {}
    for item in git('ls-tree', '-r', '-l', '-z', COMMIT).split(b'\0'):
        if item:
            metadata, path = item.split(b'\t', 1)
            mode, kind, blob, size = metadata.decode().split()
            if kind == 'blob':
                tree[path.decode()] = (mode, blob, int(size))
    for path, row in rows.items():
        assert tree[path] == (row['git_mode'], row['git_blob'], row['bytes']), path
    total = sum(row['bytes'] for row in rows.values())
    assert total == 8432966
    old_scope = ROOT / 'games/yuga-native/docs/evidence/desktop-finish/runtime-frontage-checkpoint-r1/scope.json'
    required = json.loads(old_scope.read_text())['required_source_pins']
    assert len(required) == 10 and set(required) <= changed
    for path, pin in required.items():
        assert rows[path]['sha256'] == pin['sha256'] and rows[path]['bytes'] == pin['bytes']
    remote = json.loads((STAGE / 'remote-verification.json').read_text())
    assert remote['passed'] and remote['expected'] == COMMIT and remote['remote_ref'].split()[0] == COMMIT
    stage = json.loads((STAGE / 'stage-verification.json').read_text())
    owner_commit = json.loads((STAGE / 'commit-verification.json').read_text())
    assert stage['passed'] and stage['files'] == 128
    assert owner_commit == {'commit': COMMIT, 'verified_files': 128, 'bytes': total, 'passed': True}
    OUT.mkdir(exist_ok=True)
    for name in ('manifest.json', 'stage-verification.json', 'commit-verification.json', 'remote-verification.json'):
        shutil.copyfile(STAGE / name, OUT / name)
    after = state()
    assert before == after
    checks = ['exact parent', 'unique 128 stage paths', 'exact committed changed-path set',
              'all committed blob IDs/modes/sizes match owner stage', 'exact 8432966 byte census',
              'ten required runtime/test/notice paths and hashes retained',
              'owner stage/commit results match', 'retained independent remote response matches',
              'normal HEAD/index unchanged']
    result = {'schema': 1, 'commit': COMMIT, 'parent': PARENT, 'checks_passed': len(checks),
              'checks': checks, 'files': 128, 'bytes': total,
              'scope': 'Independent Git tree/path/blob/mode/size verification of owner manifest. '
                       'Original owner stage provides working-byte SHA256 verification. '
                       'Remote record is retained proof, not a new network query. '
                       'This commit intentionally changes the bounded frontage runtime/support; '
                       'it is not relabeled evidence-only or a new package qualification.',
              'before': before, 'after': after, 'source_mutations': False, 'engine_runs': 0}
    (OUT / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    (OUT / 'README.md').write_text(
        f'Runtime checkpoint `{COMMIT}` independently matches all 128 committed paths, Git blob IDs, '
        f'modes and sizes in the retained owner stage manifest ({total:,} bytes), with exact parent `{PARENT}`. '
        'All ten required production/test/notice paths remain included. The saved stage/commit/remote '
        'records are copied byte-exactly; there was no new network query or repeated source-content hash campaign. '
        'This checkpoint deliberately changes frontage runtime/support. CI, route, actual production pixels and '
        'new package qualification remain separate owner records. No engine, staging or source change was performed.\n')
    artifacts = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                 for p in OUT.iterdir() if p.is_file() and p.name != 'receipt.json'}
    receipt = {'schema': 1, 'status': 'COMMITTED_RUNTIME_CHECKPOINT_TREE_PROOF',
               'source_commit': COMMIT, 'checks_passed': len(checks),
               'artifacts': artifacts, 'source_or_git_mutations': False}
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'checks': len(checks), 'files': 128, 'bytes': total,
                      'receipt_sha256': sha(OUT / 'receipt.json')}))

if __name__ == '__main__':
    main()
