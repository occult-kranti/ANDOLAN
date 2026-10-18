#!/usr/bin/env python3
"""Retain a completed one-line priority candidate; never launch a renderer."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/workspace/tooling/godot-public-4.6.3')
RECEIPTS = ROOT / 'priority-candidate-r1'
SOURCE = Path('/tmp/yuga-engine-template-baseline-r1/godot-35e80b3a8822a9df9be390814b62f44c0a9c69e8')


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    build = json.loads((RECEIPTS / 'build-result.json').read_text())
    assert build['completed'] is True and build['exit_code'] == 0
    pristine = json.loads((RECEIPTS / 'pristine-source-files.json').read_text())
    changed = [name for name, pin in pristine.items()
               if not (SOURCE / name).is_file() or (SOURCE / name).stat().st_size != pin['bytes']
               or sha(SOURCE / name) != pin['sha256']]
    assert not changed, changed
    original = json.loads((ROOT / 'template-baseline-r1/pristine-source-files.json').read_text())
    original_delta = [name for name, pin in original.items() if sha(SOURCE / name) != pin['sha256']]
    assert original_delta == ['servers/rendering/renderer_rd/pipeline_hash_map_rd.h'], original_delta
    baseline = ROOT / 'binaries/godot-4.6.3-public-template-debug-unmodified'
    assert sha(baseline) == 'dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f'
    binary = SOURCE / 'bin/godot.linuxbsd.template_debug.x86_64'
    assert binary.is_file() and os.access(binary, os.X_OK)
    assert binary.stat().st_size <= 300 * 1024 ** 2
    retained = ROOT / 'binaries/godot-4.6.3-public-template-debug-pipeline-low-priority'
    assert not retained.exists()
    retained.parent.mkdir(exist_ok=True)
    shutil.copy2(binary, retained)
    version = subprocess.run([str(retained), '--version'], capture_output=True, text=True, timeout=20)
    dependencies = subprocess.run(['ldd', str(retained)], capture_output=True, text=True, timeout=20)
    (RECEIPTS / 'candidate-version.txt').write_text(version.stdout + version.stderr)
    (RECEIPTS / 'candidate-ldd.txt').write_text(dependencies.stdout + dependencies.stderr)
    installed = Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
    installed_sha = sha(installed)
    checks = {'build_completed_exit_zero': True, 'all_expected_sources_match': not changed,
              'retained_binary_exact': sha(binary) == sha(retained),
              'exact_one_original_source_delta': len(original_delta) == 1,
              'baseline_binary_unchanged': sha(baseline) == 'dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f',
              'candidate_binary_differs_from_baseline': sha(binary) != sha(baseline),
              'version_exit_zero': version.returncode == 0,
              'ldd_exit_zero': dependencies.returncode == 0,
              'all_dynamic_dependencies_found': 'not found' not in dependencies.stdout,
              'installed_engine_unchanged': installed_sha == 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'}
    report = {'passed': all(checks.values()), 'checks': checks,
              'source_commit': '35e80b3a8822a9df9be390814b62f44c0a9c69e8',
              'source_files_verified': len(pristine), 'source_patches': 1,
              'binary': str(retained), 'binary_sha256': sha(retained),
              'binary_bytes': retained.stat().st_size, 'version': version.stdout.strip(),
              'installed_engine_sha256': installed_sha,
              'build_result_sha256': sha(RECEIPTS / 'build-result.json'),
              'scope': 'One-line pipeline-task priority diagnostic over exact public-tag template baseline. No product promotion; no renderer or cold-launch result yet.'}
    with (RECEIPTS / 'finished-build-verification.json').open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
