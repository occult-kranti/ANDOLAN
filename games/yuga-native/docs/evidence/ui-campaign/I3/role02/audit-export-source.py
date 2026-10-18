#!/usr/bin/env python3
"""Read committed Git objects independently of the exporter and local worktree."""
import argparse, hashlib, json, pathlib, subprocess

p = argparse.ArgumentParser()
p.add_argument('--export', required=True, type=pathlib.Path)
p.add_argument('--report', required=True, type=pathlib.Path)
a = p.parse_args()
repo = pathlib.Path('/workspace/ANDOLAN')
manifest = json.loads(a.export.read_text())
commit = manifest['git']['head']
prefix = 'games/yuga-native/'
roots = [prefix + name for name in ['scripts', 'shaders', 'scenes', 'assets', 'project.godot', 'export_presets.cfg']]
records = subprocess.check_output(['git', 'ls-tree', '-rz', '--full-tree', commit, '--', *roots], cwd=repo)
objects = []
for record in records.split(b'\0'):
    if not record:
        continue
    metadata, name = record.split(b'\t', 1)
    mode, kind, object_id = metadata.split()
    assert kind == b'blob' and mode in [b'100644', b'100755']
    objects.append((object_id, name.decode().removeprefix(prefix)))
proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=repo, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
sources = {}
for object_id, name in objects:
    proc.stdin.write(object_id + b'\n')
    proc.stdin.flush()
    header = proc.stdout.readline().split()
    assert header[:2] == [object_id, b'blob']
    size = remaining = int(header[2])
    digest = hashlib.sha256()
    while remaining:
        data = proc.stdout.read(min(remaining, 1024 * 1024))
        assert data
        digest.update(data)
        remaining -= len(data)
    assert proc.stdout.read(1) == b'\n'
    sources[name] = {'bytes': size, 'sha256': digest.hexdigest()}
proc.stdin.close()
assert proc.wait() == 0
signature = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
changed = subprocess.check_output(['git', 'diff', '--name-only', '83f88f840c59934155aec19d95b41d920d15c6c1', commit, '--', *roots], cwd=repo, text=True).splitlines()
checks = {
    'runtime_count_525': len(sources) == 525,
    'every_export_source_matches_committed_blob': sources == manifest['source']['files'],
    'independent_source_signature_matches': signature == manifest['source']['sha256'],
    'only_contract_runtime_overlay_since_rejected_r2': changed == [prefix + 'assets/contracts/native-contracts-v1.json', prefix + 'scripts/native_contracts.gd'],
}
result = {'passed': all(checks.values()), 'checks': checks, 'commit': commit,
          'export_manifest_sha256': hashlib.sha256(a.export.read_bytes()).hexdigest(),
          'runtime_signature': signature, 'runtime_files': len(sources),
          'changed_runtime_from_rejected_r2': changed, 'committed_sources': sources,
          'scope': 'Independent streaming Git-object hashes; no local runtime reads, import, export, renderer or executable launch.'}
a.report.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in ['passed', 'checks', 'commit', 'runtime_signature', 'runtime_files']}))
raise SystemExit(0 if result['passed'] else 1)
