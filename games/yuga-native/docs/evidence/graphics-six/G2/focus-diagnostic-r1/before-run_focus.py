#!/usr/bin/env python3
"""Bounded support anchors / 60-frame cast-cancel capture. Root owns heavy lane."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=['support', 'entry-cancel'], required=True)
    parser.add_argument('--display', type=int, default=192)
    parser.add_argument('--shader-cache-seed', type=Path)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    project, output = args.project.resolve(), args.output.resolve()
    if not args.output.is_absolute() or output.exists():
        parser.error('Fresh absolute output required')
    if not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        parser.error('Use an unused X display90–199')
    spec = importlib.util.spec_from_file_location('graphics_snapshot', Path(__file__).with_name('snapshot.py'))
    snapshot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(snapshot)
    seal = snapshot.verify(project)
    helper = project / 'tools/graphics-six/capture_focus.gd'
    if not helper.is_file():
        parser.error('Refresh the snapshot with the new capture helper first')
    runtime = Path('/workspace/tooling/native-render/runtime')
    command = [shutil.which('godot'), '--path', str(project), '--audio-driver', 'Dummy',
               '--disable-vsync', '--fixed-fps', '30', '--max-threads', '2',
               '--script', 'res://tools/graphics-six/capture_focus.gd', '--',
               '--output=' + str(output), '--case=' + args.case]
    if args.preflight:
        command.insert(1, '--headless')
        command.append('--preflight')
    else:
        command[1:1] = ['--display-driver', 'x11', '--rendering-method', 'forward_plus']
    if args.dry_run:
        print(json.dumps({'command': command, 'snapshot_round': seal['round'], 'starts_engine': False}, indent=2))
        return
    logs = output.with_name(output.name + '-logs')
    if logs.exists():
        parser.error('Fresh log directory required')
    logs.mkdir(parents=True)
    env = os.environ.copy()
    env.update(LP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
    for key, suffix in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        folder = logs / 'user' / suffix
        folder.mkdir(parents=True)
        env[key] = str(folder)
    env['MESA_SHADER_CACHE_DIR'] = str(logs / 'user/cache/mesa')
    seed = {str(p.relative_to(args.shader_cache_seed)): sha(p) for p in args.shader_cache_seed.rglob('*') if p.is_file()} if args.shader_cache_seed else {}
    if args.shader_cache_seed:
        if not seed:
            parser.error('Seed cache is empty')
        shutil.copytree(args.shader_cache_seed, env['MESA_SHADER_CACHE_DIR'])
    record = {'complete': False, 'command': command, 'case': args.case,
              'snapshot_sha256': sha(project / snapshot.MARKER), 'source_files': seal['files'],
              'helper_sha256': sha(helper), 'runner_sha256': sha(__file__),
              'engine_sha256': sha(command[0]), 'affinity': sorted(os.sched_getaffinity(0)),
              'thread_limits': {k: env[k] for k in ['LP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']},
              'shader_cache_seed': seed, 'preflight': args.preflight,
              'scope': 'Source-bound staged camera/control fixture; no native XTest or hardware FPS claim.'}
    server = None
    try:
        with (logs / 'godot.log').open('x') as gl, (logs / 'xvfb.log').open('x') as xl:
            if not args.preflight:
                env.update(DISPLAY=f':{args.display}', VK_ICD_FILENAMES=str(runtime / 'usr/share/vulkan/icd.d/lvp_icd.json'),
                           LD_LIBRARY_PATH=str(runtime / 'usr/lib/x86_64-linux-gnu') + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else ''))
                server = subprocess.Popen([str(runtime / 'usr/bin/Xvfb'), env['DISPLAY'], '-screen', '0', '1280x960x24', '-nolisten', 'tcp', '-extension', 'MIT-SHM', '-ac'], env=env, stdout=xl, stderr=subprocess.STDOUT)
                deadline = time.monotonic() + 5
                while not Path(f'/tmp/.X11-unix/X{args.display}').exists():
                    if server.poll() is not None or time.monotonic() > deadline:
                        raise RuntimeError('Owned Xvfb failed')
                    time.sleep(.05)
            result = subprocess.run(command, env=env, stdout=gl, stderr=subprocess.STDOUT, timeout=900)
            record['engine_exit'] = result.returncode
        text = (logs / 'godot.log').read_text()
        if result.returncode or 'SCRIPT ERROR:' in text or '\nERROR:' in text:
            raise RuntimeError('Engine failure; preserve logs')
        report_path = output / ('preflight.json' if args.preflight else 'capture.json')
        report = json.loads(report_path.read_text())
        shots = report['shots']
        if report['complete'] is not True or len(shots) != (2 if args.case == 'support' else 60):
            raise RuntimeError('Capture did not satisfy declared checks/count')
        if args.case == 'entry-cancel':
            if not all(b['physics_frame'] - a['physics_frame'] == 2 for a, b in zip(shots, shots[1:])):
                raise RuntimeError('Missing physics sampling interval')
            if not args.preflight and not all(b['render_frame'] - a['render_frame'] == 1 for a, b in zip(shots, shots[1:])):
                raise RuntimeError('Nonconsecutive rendered frames')
        if not args.preflight and not all(sha(output / s['file']) == s['sha256'] for s in shots):
            raise RuntimeError('Original framebuffer hash mismatch')
        snapshot.verify(project)
        if sha(project / snapshot.MARKER) != record['snapshot_sha256']:
            raise RuntimeError('Snapshot receipt changed')
        if args.shader_cache_seed and seed != {str(p.relative_to(args.shader_cache_seed)): sha(p) for p in args.shader_cache_seed.rglob('*') if p.is_file()}:
            raise RuntimeError('Source shader cache changed')
        record.update(complete=True, report_sha256=sha(report_path), raw_pngs=0 if args.preflight else len(shots))
    except Exception as error:
        record['failure'] = repr(error)
        raise
    finally:
        if server:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        record['logs'] = {p.name: sha(p) for p in logs.glob('*.log')}
        (logs / 'run.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'complete': True, 'case': args.case, 'raw_pngs': record['raw_pngs'], 'logs': str(logs)}, indent=2))


if __name__ == '__main__':
    main()
