#!/usr/bin/env python3
"""One bounded preview, adapted from reuse-vfx-stage/run_capture.py process ownership."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[4]


def stop(child):
    if child is not None and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--display', type=int, default=188)
    args = parser.parse_args()
    project, runtime, output = args.project.resolve(), args.runtime.resolve(), args.output.resolve()
    if project.is_relative_to(ROOT) or output.is_relative_to(ROOT) or output.exists():
        raise ValueError('fresh outside-checkout output and prepared project required')
    if not 90 <= args.display <= 199 or not (project / 'source-manifest.json').is_file():
        raise ValueError('prepared project and owned display required')
    socket = Path('/tmp/.X11-unix') / f'X{args.display}'
    if socket.exists() or Path(f'/tmp/.X{args.display}-lock').exists():
        raise ValueError('display already owned')
    xvfb = runtime / 'usr/bin/Xvfb'
    if not xvfb.is_file():
        raise ValueError('reuse the existing extracted runtime')
    output.mkdir(parents=True)
    env = os.environ.copy()
    env.update({'DISPLAY': f':{args.display}', 'LP_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'GODOT_SILENCE_ROOT_WARNING': '1', 'LIBGL_ALWAYS_SOFTWARE': '1'})
    env['LD_LIBRARY_PATH'] = str(runtime / 'usr/lib/x86_64-linux-gnu') + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    for name in ['XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME']:
        folder = output / name.lower()
        folder.mkdir()
        env[name] = str(folder)
    command = [shutil.which('godot'), '--path', str(project), '--display-driver', 'x11', '--rendering-method', 'gl_compatibility', '--audio-driver', 'Dummy', '--script', 'res://preview.gd', '--', '--output=' + str(output)]
    display = render = None
    started = time.monotonic()
    try:
        with (output / 'display.log').open('w') as display_log, (output / 'render.log').open('w') as render_log:
            display = subprocess.Popen([str(xvfb), f':{args.display}', '-screen', '0', '960x640x24', '-nolisten', 'tcp', '-extension', 'MIT-SHM', '-ac'], env=env, stdout=display_log, stderr=subprocess.STDOUT)
            for _ in range(80):
                if display.poll() is not None:
                    raise RuntimeError('owned Xvfb failed')
                if socket.exists():
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('display socket unavailable')
            render = subprocess.Popen(command, env=env, stdout=render_log, stderr=subprocess.STDOUT)
            code = render.wait(timeout=60)
            if code:
                raise RuntimeError(f'preview exited {code}; inspect render.log')
        log = (output / 'render.log').read_text()
        if 'SCRIPT ERROR:' in log or '\nERROR:' in log:
            raise RuntimeError('preview emitted errors')
        report = json.loads((output / 'preview-report.json').read_text())
        if not report['passed'] or report['renderer'] != 'gl_compatibility':
            raise RuntimeError('preview contract failed')
        image = output / 'existing-courtyard-element.png'
        report.update({'command': command, 'wallSeconds': round(time.monotonic() - started, 3), 'imageSha256': hashlib.sha256(image.read_bytes()).hexdigest(), 'bytes': image.stat().st_size})
        (output / 'runner-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
    finally:
        stop(render)
        stop(display)


if __name__ == '__main__':
    main()
