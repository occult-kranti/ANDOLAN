#!/usr/bin/env python3
"""Run Rama quality component checks sequentially; no import or visual acceptance.

Each Godot suite receives separate temporary XDG directories. Reports and logs
are retained even when a component fails. Run after the normal project import;
this runner does not render images, start online matches or install tools.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
LIMITS = ('Headless component and offline-scene assertions only. No rendered art, OS input, '
          'human feel/listening, integrated native multiplayer/AI, Windows or physical-GPU acceptance.')
SUITES = (
    ('lod-interchange', 'python', 'tests/hero_lod_cases.py', ()),
    ('action-audio-build', 'python', 'art/audio/rama-quality/build_audio.py', ('--check',)),
    ('lod-selector', 'godot', 'tests/hero_lod_cases.gd', ()),
    ('lod-one-rig-binding', 'godot', 'tests/hero_lod_binding_cases.gd', ()),
    ('lighting-properties', 'godot', 'tests/production_lighting_quality_cases.gd', ()),
    ('action-audio-component', 'godot', 'tests/rama_action_audio_cases.gd', ()),
    ('action-buffer-component', 'godot', 'tests/rama_action_buffer_cases.gd', ()),
    ('action-buffer-offline-integration', 'godot', 'tests/rama_action_buffer_integration_cases.gd', ()),
    ('facial-component-and-active-asset', 'godot', 'tests/rama_facial_cases.gd', ('--asset=res://assets/heroes/rama-hero.glb',)),
    ('active-hero-offline-integration', 'godot', 'tests/rama_quality_integration_cases.gd', ()),
    ('material-component', 'godot', 'tests/rama_material_cases.gd', ()),
    ('practice-brain-component', 'godot', 'tests/rama_practice_brain_cases.gd', ()),
    ('remote-replica-component', 'godot', 'tests/rama_remote_replica_cases.gd', ()),
    ('screen-focus-and-layout', 'godot', 'tests/rama_screen_quality_cases.gd', ()),
    ('secondary-motion-component', 'godot', 'tests/rama_secondary_motion_cases.gd', ()),
    ('vfx-component', 'godot', 'tests/rama_vfx_quality_cases.gd', ()),
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def runtime_sources() -> dict:
    files = [p for name in ('scripts', 'shaders', 'scenes', 'assets')
             for p in (PROJECT / name).rglob('*') if p.is_file()]
    files += [PROJECT / 'project.godot', PROJECT / 'export_presets.cfg']
    records = {str(p.relative_to(PROJECT)): {'bytes': p.stat().st_size, 'sha256': sha(p)}
               for p in sorted(files)}
    encoded = json.dumps(records, sort_keys=True, separators=(',', ':')).encode()
    return {'sha256': hashlib.sha256(encoded).hexdigest(), 'files': records}


def executable(value: str) -> str:
    resolved = shutil.which(value)
    if resolved is None:
        raise ValueError(f'Required executable is unavailable: {value}')
    # Keep a venv's executable path: resolving its symlink to the system Python
    # would discard the venv and its pinned NumPy dependency.
    return os.path.abspath(resolved)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', default='godot')
    parser.add_argument('--python', default=sys.executable, dest='python_engine')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--suite', action='append', choices=[s[0] for s in SUITES], help='Run only the named packet(s); default is all suites.')
    parser.add_argument('--list', action='store_true', help='Print the exact suite catalog without executing it.')
    parser.add_argument('--timeout', type=float, default=120.0, help='Maximum wall seconds per suite.')
    parser.add_argument('--max-cpus', type=int, default=2, help='Linux process-affinity cap; not a performance benchmark.')
    args = parser.parse_args()
    selected = [s for s in SUITES if not args.suite or s[0] in args.suite]
    if args.list:
        print(json.dumps({'suites': [{'id': i, 'kind': k, 'source': s, 'arguments': a} for i, k, s, a in selected], 'scope': LIMITS}, indent=2))
        return 0
    if args.output is None:
        parser.error('--output is required unless --list is used')
    if not 0 < args.timeout <= 1800 or not 1 <= args.max_cpus <= 64:
        parser.error('timeout must be in (0,1800] and max-cpus in [1,64]')
    try:
        engine, python_engine = executable(args.engine), executable(args.python_engine)
    except ValueError as error:
        parser.error(str(error))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    for name in ('reports', 'logs', 'users'):
        (output / name).mkdir()
    if hasattr(os, 'sched_getaffinity') and hasattr(os, 'sched_setaffinity'):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:args.max_cpus])
    version = subprocess.check_output([engine, '--version'], text=True).strip()
    if not version.startswith('4.6.3.stable.'):
        raise ValueError(f'Expected Godot4.6.3 standard; received {version}')
    before = runtime_sources()
    write_json(output / 'source-before.json', before)
    checked_paths = {source for _, _, source, _ in selected} | {'tools/run-quality-checks.py'}
    if any(s[0] == 'lod-interchange' for s in selected):
        checked_paths.add('art/hero-rama-lod/glb_lod.py')
    checked_sources = {source: sha(PROJECT / source) for source in sorted(checked_paths)}
    summary = {'schema': 1, 'passed': False, 'scope': LIMITS, 'engine_version': version,
               'python_version': subprocess.check_output([python_engine, '--version'], text=True).strip(),
               'runner_sha256': sha(Path(__file__)), 'selected_suites': [s[0] for s in selected],
               'suite_sources': checked_sources, 'suites': [], 'source_unchanged': False}
    write_json(output / 'summary.json', summary)
    for suite_id, kind, source, arguments in selected:
        report, log = output / 'reports' / (suite_id + '.json'), output / 'logs' / (suite_id + '.log')
        env = os.environ.copy()
        if kind == 'godot':
            user = Path(tempfile.mkdtemp(prefix=suite_id + '-', dir=output / 'users'))
            env.update(XDG_DATA_HOME=str(user / 'data'), XDG_CONFIG_HOME=str(user / 'config'),
                       XDG_CACHE_HOME=str(user / 'cache'), LP_NUM_THREADS='2')
            # AudioServer's Dummy mixer uses real audio time. Do not force a
            # synthetic fixed-fps clock onto that suite's captured PCM checks.
            command = [engine, '--headless', '--single-threaded-scene', '--audio-driver', 'Dummy',
                       '--path', str(PROJECT), '--script', 'res://' + source, '--',
                       *arguments, '--report=' + str(report)]
        else:
            command = [python_engine, str(PROJECT / source), *arguments, '--report=' + str(report)]
        started = time.monotonic()
        result = {'id': suite_id, 'kind': kind, 'source': source, 'command': command,
                  'report': str(report.relative_to(output)), 'log': str(log.relative_to(output)),
                  'passed': False}
        with log.open('w') as stream:
            try:
                process = subprocess.run(command, cwd=REPOSITORY, env=env, stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=args.timeout)
                result['exit_code'] = process.returncode
            except subprocess.TimeoutExpired:
                result.update(exit_code=None, error='suite_timeout')
        result['wall_seconds'] = round(time.monotonic() - started, 3)
        if report.is_file():
            result['report_sha256'] = sha(report)
            try:
                data = json.loads(report.read_text())
                result['passed'] = result['exit_code'] == 0 and isinstance(data, dict) and data.get('passed') is True
                if isinstance(data, dict):
                    result['checks'] = len(data['checks']) if isinstance(data.get('checks'), list) else data.get('count', data.get('checks'))
                    if isinstance(data.get('checks'), list):
                        exercised = bool(data['checks']) and all(
                            isinstance(check, dict) and check.get('passed') is True
                            for check in data['checks'])
                    else:
                        exercised = type(data.get('files')) is int and data['files'] > 0
                    if not exercised:
                        result.update(passed=False, error='empty_or_unrecognized_suite_report')
            except (ValueError, OSError):
                result['error'] = 'invalid_suite_report'
        else:
            result['error'] = result.get('error', 'missing_suite_report')
        result['log_sha256'] = sha(log)
        result['engine_errors'] = [line for line in log.read_text(errors='replace').splitlines()
                                   if line.startswith(('SCRIPT ERROR:', 'ERROR:'))]
        if result['engine_errors']:
            result.update(passed=False, error='engine_error_in_log')
        summary['suites'].append(result)
        write_json(output / 'summary.json', summary)
        print(json.dumps({'suite': suite_id, 'passed': result['passed'], 'exit_code': result['exit_code']}), flush=True)
    after = runtime_sources()
    write_json(output / 'source-after.json', after)
    summary['checked_sources_unchanged'] = checked_sources == {source: sha(PROJECT / source) for source in sorted(checked_paths)}
    summary['source_unchanged'] = before == after and summary['checked_sources_unchanged']
    summary['passed'] = summary['source_unchanged'] and all(s['passed'] for s in summary['suites'])
    write_json(output / 'summary.json', summary)
    print(json.dumps({'passed': summary['passed'], 'suites': len(selected), 'source_unchanged': summary['source_unchanged'], 'output': str(output), 'scope': LIMITS}))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
