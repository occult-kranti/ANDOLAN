#!/usr/bin/env python3
"""Run a real Forward+ Confluence review on an owned software Vulkan display."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--runtime', type=Path, default=Path('/workspace/tooling/native-render/runtime'))
    parser.add_argument('--godot', default=shutil.which('godot'))
    parser.add_argument('--display', type=int, default=110)
    args = parser.parse_args()
    output, runtime = args.output.resolve(), args.runtime.resolve()
    if output.exists():
        raise ValueError('Choose a new output directory to preserve prior evidence')
    if not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        raise ValueError('Choose an unused display in [90,199]')
    if not args.godot:
        raise ValueError('Godot is missing')
    xvfb = runtime / 'usr/bin/Xvfb'
    icd = runtime / 'usr/share/vulkan/icd.d/lvp_icd.json'
    if not xvfb.is_file() or not icd.is_file():
        raise ValueError('Run tools/setup-render-runtime.py first')
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(DISPLAY=f':{args.display}',
        LD_LIBRARY_PATH=str(runtime / 'usr/lib/x86_64-linux-gnu') + (':' + environment['LD_LIBRARY_PATH'] if environment.get('LD_LIBRARY_PATH') else ''),
        VK_ICD_FILENAMES=str(icd), LP_NUM_THREADS='2')
    user = output.parent / (output.name + '-user')
    for variable, folder in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        environment[variable] = str(user / folder)
        Path(environment[variable]).mkdir(parents=True, exist_ok=True)
    environment['MESA_SHADER_CACHE_DIR'] = str(user / 'cache/mesa')
    command = [args.godot, '--path', str(args.project.resolve()), '--display-driver', 'x11',
        '--rendering-method', 'forward_plus', '--audio-driver', 'Dummy', '--disable-vsync',
        '--script', 'res://tools/capture-world.gd', '--', '--output=' + str(output)]
    with output.with_suffix('.xvfb.log').open('w') as xlog, output.with_suffix('.godot.log').open('w') as log:
        server = subprocess.Popen([str(xvfb), environment['DISPLAY'], '-screen', '0', '1280x720x24',
            '-nolisten', 'tcp', '-extension', 'MIT-SHM', '-ac'], env=environment, stdout=xlog, stderr=subprocess.STDOUT)
        try:
            for _ in range(30):
                if server.poll() is not None:
                    raise RuntimeError('Owned Xvfb failed to start')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists():
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('Owned Xvfb did not create its display socket')
            result = subprocess.run(command, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=900)
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    report_file = output / 'world-render-review.json'
    if not report_file.exists():
        raise RuntimeError('Renderer produced no report; inspect ' + str(output.with_suffix('.godot.log')))
    report = json.loads(report_file.read_text())
    log_text = output.with_suffix('.godot.log').read_text()
    if result.returncode or not report['complete'] or 'SCRIPT ERROR:' in log_text or '\nERROR:' in log_text:
        raise RuntimeError('World capture failed; preserve and inspect its report/log')
    print(json.dumps({'complete': True, 'shots': len(report['shots']), 'output': str(output),
        'scope': 'Actual software-rendered views; visual acceptance and hardware performance remain separate'}))


if __name__ == '__main__':
    main()
