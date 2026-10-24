#!/usr/bin/env python3
"""Reuse the project's qualified UI runner for the isolated hair comparison.

Inherited warm llvmpipe cache, two software-render threads, pinned real inputs,
fresh X server/output, bounded process lifetime. No GPU performance claim.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('existing_ui_runner', PROJECT / 'tools/ui-campaign/run.py')
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--engine', type=Path, required=True)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--hair', type=Path, required=True)
    p.add_argument('--display', type=int, default=187)
    p.add_argument('--timeout', type=int, default=300)
    p.add_argument('--phase', choices=['all', 'stills', 'motion', 'correction'], default='all')
    a = p.parse_args()
    assert not a.output.exists() and not Path(f'/tmp/.X11-unix/X{a.display}').exists()
    a.output.mkdir(parents=True)
    driver = Path(__file__).with_name('capture_native.gd')
    inputs = [a.base, a.hair, a.engine, driver, Path(__file__),
              driver.with_name('native_candidate.gd'), PROJECT / 'scripts/rama_motion.gd',
              PROJECT / 'assets/animations/rama_hero_motion.tres', PROJECT / 'assets/heroes/rama-hero.glb']
    pins = {str(path.resolve()): ui.sha(path) for path in inputs}
    env = os.environ.copy()
    env.update(DISPLAY=f':{a.display}', LD_LIBRARY_PATH=str(a.runtime / 'usr/lib/x86_64-linux-gnu'),
               VK_ICD_FILENAMES=str(a.runtime / 'usr/share/vulkan/icd.d/lvp_icd.json'),
               LP_NUM_THREADS='2', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    command = [str(a.engine), '--path', str(PROJECT), '--display-driver', 'x11',
               '--rendering-method', 'forward_plus', '--rendering-driver', 'vulkan',
               '--audio-driver', 'Dummy', '--fixed-fps', '30', '--disable-vsync',
               '--resolution', '960x540', '--script', str(driver), '--',
               '--base=' + str(a.base.resolve()), '--hair=' + str(a.hair.resolve()),
               '--phase=' + a.phase,
               '--output=' + str(a.output.resolve())]
    record = {'schema_version': 1, 'source_sha256': pins, 'command': command,
              'cache_policy': 'Inherited qualified warm Mesa/Godot cache',
              'render_threads': 2, 'passed': False, 'started_unix': time.time()}
    server = engine = None
    try:
        with (a.output / 'xvfb.log').open('x') as xlog, (a.output / 'godot.log').open('x') as log:
            server = subprocess.Popen([str(a.runtime / 'usr/bin/Xvfb'), env['DISPLAY'], '-screen', '0', '960x540x24', '-nolisten', 'tcp', '-ac'], env=env, stdout=xlog, stderr=subprocess.STDOUT)
            ui.wait_for(lambda: Path(f'/tmp/.X11-unix/X{a.display}').exists(), 10)
            engine = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            record['engine_pid'] = engine.pid
            ui.save(a.output / 'wrapper.json', record)
            print(json.dumps({'engine_pid': engine.pid, 'output': str(a.output)}), flush=True)
            record['exit_code'] = engine.wait(timeout=a.timeout)
        log_text = (a.output / 'godot.log').read_text()
        assert record['exit_code'] == 0 and 'SCRIPT ERROR:' not in log_text and '\nERROR:' not in log_text, 'Native process failed'
        measurement = ui.read(a.output / 'capture.json')
        assert len(measurement['originals']) == (0 if a.phase == 'motion' else 3 if a.phase == 'correction' else 8)
        assert len(measurement['frames']) == (0 if a.phase in ['stills', 'correction'] else 120)
        for frame in measurement['originals'] + measurement['frames']:
            assert frame['width'] == 960 and frame['height'] == 540 and ui.sha(Path(frame['path'])) == frame['sha256']
        record['passed'] = all(ui.sha(Path(path)) == value for path, value in pins.items())
        record['capture_sha256'] = ui.sha(a.output / 'capture.json')
    except Exception as exc:
        record['error'] = repr(exc)
    finally:
        for process in (engine, server):
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        record['elapsed_seconds'] = time.time() - record['started_unix']
        ui.save(a.output / 'wrapper.json', record)
    print(json.dumps(record, indent=2))
    return 0 if record['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
