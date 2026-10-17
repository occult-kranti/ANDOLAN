#!/usr/bin/env python3
"""Run matched Rama lighting/material captures on one owned real display."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PROJECT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--display', type=int, default=139)
    parser.add_argument('--shader-cache-seed', type=Path)
    args = parser.parse_args()
    out = args.output
    user = out.with_name(out.name + '-user')
    assert out.is_absolute() and not out.exists() and not user.exists()
    assert 90 <= args.display <= 199 and not Path(f'/tmp/.X11-unix/X{args.display}').exists()
    runtime = Path('/workspace/tooling/native-render/runtime')
    env = os.environ.copy()
    env.update(DISPLAY=f':{args.display}', LP_NUM_THREADS='2',
               LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu'),
               VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'))
    for key, child in [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]:
        directory = user/child
        directory.mkdir(parents=True, exist_ok=False)
        env[key] = str(directory)
    env['MESA_SHADER_CACHE_DIR'] = str(user/'cache/mesa')
    if args.shader_cache_seed:
        assert args.shader_cache_seed.is_dir()
        shutil.copytree(args.shader_cache_seed, env['MESA_SHADER_CACHE_DIR'])
    cmd = [shutil.which('godot'), '--path', str(PROJECT), '--display-driver', 'x11',
           '--rendering-method', 'forward_plus', '--audio-driver', 'Dummy',
           '--disable-vsync', '--script', 'res://art/lookdev/capture_floor_probe.gd',
           '--', '--output='+str(out)]
    with out.with_suffix('.xvfb.log').open('x') as xl, out.with_suffix('.godot.log').open('x') as gl:
        display = subprocess.Popen([str(runtime/'usr/bin/Xvfb'), env['DISPLAY'], '-screen', '0',
                                    '1280x720x24', '-nolisten', 'tcp', '-extension', 'MIT-SHM', '-ac'],
                                   env=env, stdout=xl, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if display.poll() is not None:
                    raise RuntimeError('Owned display stopped')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists():
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('Owned display did not start')
            result = subprocess.run(cmd, env=env, stdout=gl, stderr=subprocess.STDOUT, timeout=1000)
        finally:
            display.terminate()
            try:
                display.wait(timeout=5)
            except subprocess.TimeoutExpired:
                display.kill()
                display.wait()
    assert result.returncode == 0, 'Inspect preserved Godot log'
    log = out.with_suffix('.godot.log').read_text()
    assert 'SCRIPT ERROR:' not in log and '\nERROR:' not in log
    report = json.loads((out/'floor-probe.json').read_text())
    assert report['complete'] and report['source_unchanged'] and len(report['shots']) == 8
    for source, sha in report['sources'].items():
        assert digest(PROJECT/source.removeprefix('res://')) == sha, source
    assert report['imports'], 'No imported scene receipts'
    for source, receipt in report['imports'].items():
        imported = PROJECT/receipt['imported'].removeprefix('res://')
        assert receipt['fresh'] and digest(imported) == receipt['sha256'], source
        assert digest(imported.with_suffix('.md5')) == receipt['stamp_sha256'], source
    from PIL import Image
    for shot in report['shots']:
        assert digest(out/shot['file']) == shot['sha256']
        with Image.open(out/shot['file']) as image:
            assert image.size == (1280, 720)
            image.verify()
    for group in [report['shots'][:4],report['shots'][4:]]:
        assert [s['settings']['variant'] for s in group] == ['candidate','restored_bias','shadows_off','ground_cast_off']
        for shot in group[1:]:
            for key in ['pose_sha256','camera_transform','camera_fov','exposure','phase']:
                assert shot[key] == group[0][key], (shot['id'],key)
    receipt = {'complete': True, 'command': cmd, 'report_sha256': digest(out/'floor-probe.json'),
               'runner_sha256': digest(Path(__file__)), 'log_sha256': digest(out.with_suffix('.godot.log')),
               'shots': 8, 'scenes': 2, 'variants_per_scene': 4,
               'scope': 'Matched actual scenes with identical frozen skeleton, camera and exposure; not physical-GPU or finished-art acceptance.'}
    (out/'floor-probe-run.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'complete': True, 'output': str(out), 'scenes': 2}))


if __name__ == '__main__':
    main()
