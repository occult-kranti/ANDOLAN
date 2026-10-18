#!/usr/bin/env python3
"""Explicit export/package phase for the audited artifact snapshot only.

No publication, cleanup, checkout creation, import command or runtime substitution.
Existing package-native.py owns all source/UID/PCK/font/engine qualification.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('snapshot', HERE / 'prepare-package-snapshot.py')
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)
EDITOR = '/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64'
RUNTIME = '/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority'
WINDOWS = '/workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['export', 'package'])
    p.add_argument('--preparation', required=True, type=Path)
    p.add_argument('--preparation-sha256', required=True)
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    raw = a.preparation.read_bytes()
    if hashlib.sha256(raw).hexdigest() != a.preparation_sha256:
        raise ValueError('Preparation receipt identity mismatch')
    r = json.loads(raw)
    if not r.get('materialized') or r.get('failure'):
        raise ValueError('A successful materialized preparation receipt is required')
    out, repo = Path(r['artifact_root']), Path(r['repository'])
    if out.parent != snapshot.AREA or repo != out / 'ANDOLAN' or out.resolve() != out:
        raise ValueError('Unexpected artifact repository/output location')
    if snapshot.git(repo, 'rev-parse', 'HEAD').decode().strip() != r['source_commit']:
        raise ValueError('Artifact HEAD changed')
    if snapshot.git(repo, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Artifact source is dirty')
    exclude = repo / '.git/info/exclude'
    if hashlib.sha256(exclude.read_bytes()).hexdigest() != r['exclude_sha256']:
        raise ValueError('Exact approved non-runtime exclusions changed')
    snapshot.audit(snapshot.SOURCE, r['entries'])
    snapshot.audit(repo, r['entries'])
    snapshot.audit_index(snapshot.SOURCE, r['entries'])
    snapshot.audit_index(repo, r['entries'])
    snapshot.audit_isolation(snapshot.SOURCE, repo, r['entries'])
    if snapshot.cache_records(Path(r['cache_seed']['path'])) != r['cache_seed']['files']:
        raise ValueError('Canonical cache seed changed since preparation')
    if a.phase == 'package':
        previous = json.loads((out / 'export-execution.json').read_text())
        if previous.get('exit_code') != 0 or not previous.get('after_source_passed'):
            raise ValueError('Export did not qualify on unchanged source')
        remaining = 401_000_000 + 245_000_000 + 32 * 1024**2
    else:
        remaining = snapshot.OUTPUT_BUDGET
        if (out / 'build').exists():
            raise ValueError('Fresh export output is required; retain earlier failures')
    if snapshot.free_bytes(snapshot.AREA) < remaining + r['reserve_bytes']:
        raise ValueError('Insufficient remaining phase capacity with declared reserve')
    command = ['taskset', '-c', '0,1', 'python3', 'games/yuga-native/tools/package-native.py',
               '--linux-engine', EDITOR, '--linux-runtime', RUNTIME,
               '--linux-runtime-variant', 'pipeline-low-priority',
               '--linux-runtime-provenance', str(repo / snapshot.NATIVE / 'docs/evidence/desktop-finish/G0/template-priority-build-r1/finished-build-verification.json'),
               '--windows-engine', WINDOWS, '--build-dir', str(out / 'build'), '--' + a.phase + '-only']
    if not a.execute:
        print(json.dumps({'execution': False, 'command': command, 'cwd': str(repo), 'hard_bound_s': 300,
                          'reserve_bytes': r['reserve_bytes']}))
        return
    receipt = out / (a.phase + '-execution.json')
    if receipt.exists():
        raise ValueError('Refuse to overwrite any earlier phase receipt')
    logs = out / 'logs'
    logs.mkdir(exist_ok=True)
    environment = {k: str(out / 'user' / v) for k, v in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]}
    environment.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    for name in ['data', 'config', 'cache']:
        (out / 'user' / name).mkdir(parents=True, exist_ok=True)
    record = {'source_commit': r['source_commit'], 'preparation_sha256': a.preparation_sha256,
              'command': command, 'cwd': str(repo), 'environment': environment,
              'started_unix': time.time(), 'after_source_passed': False}
    try:
        with (logs / (a.phase + '.stdout')).open('x') as stdout, (logs / (a.phase + '.stderr')).open('x') as stderr:
            child = subprocess.Popen(command, cwd=repo, env={**os.environ, **environment},
                                     stdout=stdout, stderr=stderr, start_new_session=True)
            record['pid'] = child.pid
            deadline = time.monotonic() + 300
            while child.poll() is None:
                reason = ('hard300s bound' if time.monotonic() >= deadline else
                          'declared free-space reserve crossed' if snapshot.free_bytes(snapshot.AREA) < r['reserve_bytes'] else None)
                if reason:
                    record['terminated_reason'] = reason
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=5)
                    break
                time.sleep(1)
            record['exit_code'] = child.returncode
        snapshot.audit(snapshot.SOURCE, r['entries'])
        snapshot.audit(repo, r['entries'])
        snapshot.audit_index(snapshot.SOURCE, r['entries'])
        snapshot.audit_index(repo, r['entries'])
        snapshot.audit_isolation(snapshot.SOURCE, repo, r['entries'])
        if snapshot.cache_records(Path(r['cache_seed']['path'])) != r['cache_seed']['files']:
            raise ValueError('Canonical cache seed changed during phase')
        if snapshot.git(repo, 'status', '--porcelain', '--untracked-files=all'):
            raise ValueError('Artifact source status changed during phase')
        if hashlib.sha256(exclude.read_bytes()).hexdigest() != r['exclude_sha256']:
            raise ValueError('Non-runtime exclusions changed during phase')
        record['after_source_passed'] = True
        record['generated_ignored_uid_files'] = {
            line[1:]: {'bytes': (repo / line[1:]).stat().st_size,
                       'sha256': snapshot.hashes(repo / line[1:])[2]}
            for line in r['exclude_text'].splitlines()
            if line.startswith('/') and (repo / line[1:]).is_file()}
        tracked_paths = {row['path'] for row in r['entries']}
        record['generated_import_metadata'] = {
            path.relative_to(repo).as_posix(): {'bytes': path.stat().st_size,
                                             'sha256': snapshot.hashes(path)[2]}
            for path in (repo / snapshot.NATIVE).rglob('*')
            if path.suffix in {'.uid', '.import'} and '.godot' not in path.parts
            and path.relative_to(repo).as_posix() not in tracked_paths}
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        record['finished_unix'] = time.time()
        record['free_bytes_after'] = snapshot.free_bytes(snapshot.AREA)
        snapshot.dump_new(receipt, record)
    print(json.dumps({'receipt': str(receipt), 'exit_code': record['exit_code'], 'after_source_passed': True}))
    raise SystemExit(record['exit_code'])


if __name__ == '__main__':
    main()
