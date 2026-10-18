#!/usr/bin/env python3
"""Bounded support anchors / 60-frame cast-cancel capture. Root owns heavy lane."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def run_engine(command, env, log_handle, log_path, output, timeout, no_progress, record):
    """Observe our child; log bytes/PNG count are liveness, not render acceptance."""
    process = subprocess.Popen(command, env=env, stdout=log_handle, stderr=subprocess.STDOUT)
    began = time.monotonic()
    last_progress = began
    seen_bytes = 0
    seen_pngs = 0
    ready_at = None
    carry = ''
    record['engine_pid'] = process.pid
    try:
        while process.poll() is None:
            now = time.monotonic()
            size = log_path.stat().st_size
            pngs = len(list(output.glob('*.png')))
            if size > seen_bytes:
                with log_path.open('rb') as incoming:
                    incoming.seek(seen_bytes)
                    new_text = incoming.read().decode('utf-8', errors='replace')
                    seen_bytes = incoming.tell()
                combined = carry + new_text
                if ready_at is None and 'YUGA_NATIVE_READY ' in combined:
                    ready_at = now
                    record['native_ready_elapsed_s'] = now - began
                carry = combined[-256:]
                last_progress = now
            if pngs != seen_pngs:
                seen_pngs = pngs
                last_progress = now
            reason = None
            if now - began >= timeout:
                reason = f'Overall engine deadline exceeded ({timeout}s)'
            elif ready_at is not None and now - last_progress >= no_progress:
                reason = f'No new engine log bytes or PNG count after native-ready ({no_progress}s)'
            if reason:
                record['watchdog_failure'] = reason
                raise TimeoutError(reason)
            time.sleep(.25)
        return process.returncode
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        record['engine_exit'] = process.returncode
        record['engine_elapsed_s'] = time.monotonic() - began
        record['observed_png_count'] = len(list(output.glob('*.png')))
        record['final_log_bytes'] = log_path.stat().st_size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=['support', 'entry-cancel', 'gold-pair'], required=True)
    parser.add_argument('--display', type=int, default=192)
    parser.add_argument('--shader-cache-seed', type=Path)
    parser.add_argument('--godot-shader-cache-seed', type=Path,
                        help='Explicit Godot shader_cache copy, separate from Mesa; never copies preferences')
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--render-thread', choices=['safe', 'separate'],
                        help='Supported Godot scheduling override; does not change render quality')
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--no-progress-timeout', type=float, default=120)
    args = parser.parse_args()
    if not 0 < args.timeout <= 900 or not 0 < args.no_progress_timeout <= args.timeout:
        parser.error('Require 0 < no-progress-timeout <= timeout <= 900 seconds')
    project, output = args.project.resolve(), args.output.resolve()
    if not args.output.is_absolute() or output.exists():
        parser.error('Fresh absolute output required')
    if not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        parser.error('Use an unused X display90–199')
    spec = importlib.util.spec_from_file_location('graphics_snapshot', Path(__file__).with_name('snapshot.py'))
    snapshot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(snapshot)
    seal = snapshot.verify(project)
    helper_name = 'capture_gold.gd' if args.case == 'gold-pair' else 'capture_focus.gd'
    helper = project / 'tools/graphics-six' / helper_name
    if not helper.is_file():
        parser.error('Refresh the snapshot with the new capture helper first')
    runtime = Path('/workspace/tooling/native-render/runtime')
    command = [shutil.which('godot'), '--path', str(project), '--audio-driver', 'Dummy',
               '--disable-vsync', '--fixed-fps', '30',
               '--script', 'res://tools/graphics-six/' + helper_name, '--',
               '--output=' + str(output), '--case=' + args.case]
    if args.verbose:
        command.insert(1, '--verbose')
    if args.render_thread:
        command[1:1] = ['--render-thread', args.render_thread]
    if args.preflight:
        command.insert(1, '--headless')
        command.append('--preflight')
    else:
        command[1:1] = ['--display-driver', 'x11', '--rendering-method', 'forward_plus']
    if args.dry_run:
        print(json.dumps({'command': command, 'snapshot_round': seal['round'], 'starts_engine': False,
                          'timeout_s': args.timeout, 'no_progress_timeout_s': args.no_progress_timeout,
                          'render_thread_override': args.render_thread,
                          'godot_shader_cache_seed': str(args.godot_shader_cache_seed) if args.godot_shader_cache_seed else None,
                          'godot_worker_pool_limit': None}, indent=2))
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
    godot_seed = {}
    godot_cache_target = None
    if args.godot_shader_cache_seed:
        godot_seed = {str(p.relative_to(args.godot_shader_cache_seed)): sha(p)
                      for p in args.godot_shader_cache_seed.rglob('*') if p.is_file()}
        if not godot_seed or any(not name.endswith('.cache') for name in godot_seed):
            parser.error('Godot seed must contain only shader-cache files')
        project_config = (project / 'project.godot').read_text()
        names = re.findall(r'^config/name="([^"\n]+)"$', project_config, re.M)
        if len(names) != 1 or '/' in names[0] or re.search(r'^config/use_custom_user_dir=true$', project_config, re.M):
            parser.error('Explicit Godot cache seed requires the standard named user directory')
        godot_cache_target = Path(env['XDG_DATA_HOME']) / 'godot/app_userdata' / names[0] / 'shader_cache'
        shutil.copytree(args.godot_shader_cache_seed, godot_cache_target)
    record = {'complete': False, 'command': command, 'case': args.case,
              'snapshot_sha256': sha(project / snapshot.MARKER), 'source_files': seal['files'],
              'helper_sha256': sha(helper), 'runner_sha256': sha(__file__),
              'engine_sha256': sha(command[0]), 'affinity': sorted(os.sched_getaffinity(0)),
              'thread_limits': {k: env[k] for k in ['LP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']},
              'godot_worker_pool_limit': None,
              'render_thread_override': args.render_thread,
              'thread_limit_scope': 'CPU affinity and llvmpipe/environment limits only; no validated Godot worker-pool limit.',
              'watchdog': {'overall_s': args.timeout, 'after_native_ready_no_progress_s': args.no_progress_timeout,
                           'progress': 'Additional engine log bytes or changed PNG count; not evidence of successful rendering.'},
              'shader_cache_seed': seed, 'preflight': args.preflight,
              'godot_shader_cache_seed': godot_seed,
              'godot_shader_cache_seed_path': str(args.godot_shader_cache_seed) if args.godot_shader_cache_seed else None,
              'godot_shader_cache_target': str(godot_cache_target) if godot_cache_target else None,
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
            engine_exit = run_engine(command, env, gl, logs / 'godot.log', output,
                                     args.timeout, args.no_progress_timeout, record)
        text = (logs / 'godot.log').read_text()
        if engine_exit or 'SCRIPT ERROR:' in text or '\nERROR:' in text:
            raise RuntimeError('Engine failure; preserve logs')
        report_path = output / ('preflight.json' if args.preflight else 'capture.json')
        report = json.loads(report_path.read_text())
        shots = report['shots']
        if report['complete'] is not True or len(shots) != (60 if args.case == 'entry-cancel' else 2):
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
        if args.godot_shader_cache_seed and godot_seed != {str(p.relative_to(args.godot_shader_cache_seed)): sha(p) for p in args.godot_shader_cache_seed.rglob('*') if p.is_file()}:
            raise RuntimeError('Source Godot shader cache changed')
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
