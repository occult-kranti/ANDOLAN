#!/usr/bin/env python3
"""Capture eight actual courtyard views with the existing software Vulkan setup.

Use a frozen project copy while agents edit the product. No framebuffer processing.
"""
from __future__ import annotations
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
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--runtime', type=Path, default=Path('/workspace/tooling/native-render/runtime'))
    parser.add_argument('--shader-cache-seed', type=Path)
    parser.add_argument('--godot', default=shutil.which('godot'))
    parser.add_argument('--display', type=int, default=158)
    parser.add_argument('--ability-reel', action='store_true', help='Add all five real ability lifecycle milestones')
    parser.add_argument('--abilities-only', action='store_true', help='Only the twenty ability milestone framebuffers')
    parser.add_argument('--title-night', action='store_true', help='Add an actual title night view')
    parser.add_argument('--character-detail', action='store_true', help='Append two review-only matched temple-wisp close-up pairs')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    output, project, runtime = args.output.resolve(), args.project.resolve(), args.runtime.resolve()
    user = output.with_name(output.name + '-user')
    log_path = output.with_suffix('.godot.log')
    xlog_path = output.with_suffix('.xvfb.log')
    if not args.output.is_absolute() or any(os.path.lexists(path) for path in (output, user, log_path, xlog_path)):
        parser.error('Choose a fresh absolute output')
    if not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        parser.error('Choose unused X display 90–199')
    command = [args.godot, '--path', str(project), '--display-driver', 'x11', '--rendering-method', 'forward_plus', '--audio-driver', 'Dummy', '--disable-vsync', '--fixed-fps', '15', '--max-threads', '2', '--script', 'res://tools/visual-campaign/capture.gd', '--', '--output=' + str(output)]
    for option in ('ability_reel', 'abilities_only', 'title_night', 'character_detail'):
        if getattr(args, option): command.append('--' + option.replace('_', '-'))
    expected = (0 if args.abilities_only else 8) + (20 if args.ability_reel or args.abilities_only else 0) + (1 if args.title_night and not args.abilities_only else 0) + (4 if args.character_detail else 0)
    if args.dry_run:
        print(json.dumps({'command': command, 'starts_processes': False, 'raw_pngs': expected}, indent=2)); return
    runner_sha = digest(__file__)
    xvfb = runtime / 'usr/bin/Xvfb'
    icd = runtime / 'usr/share/vulkan/icd.d/lvp_icd.json'
    if not args.godot or not xvfb.is_file() or not icd.is_file():
        parser.error('Prepared Godot and Vulkan runtime required')
    output.parent.mkdir(parents=True, exist_ok=True)
    user.mkdir()
    env = os.environ.copy()
    env.update(DISPLAY=f':{args.display}', LP_NUM_THREADS='2', VK_ICD_FILENAMES=str(icd), LD_LIBRARY_PATH=str(runtime / 'usr/lib/x86_64-linux-gnu') + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else ''))
    for key, folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        path = user / folder; path.mkdir(); env[key] = str(path)
    env['MESA_SHADER_CACHE_DIR'] = str(user / 'cache/mesa')
    if args.shader_cache_seed:
        shutil.copytree(args.shader_cache_seed, env['MESA_SHADER_CACHE_DIR'])
    with log_path.open('x') as log, xlog_path.open('x') as xlog:
        server = subprocess.Popen([str(xvfb), env['DISPLAY'], '-screen','0','1280x960x24','-nolisten','tcp','-extension','MIT-SHM','-ac'], env=env, stdout=xlog, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if server.poll() is not None: raise RuntimeError('Owned Xvfb stopped')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists(): break
                time.sleep(.1)
            else: raise RuntimeError('Owned Xvfb failed to start')
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill(); server.wait()
    log_text = log_path.read_text()
    if result.returncode or 'SCRIPT ERROR:' in log_text or '\nERROR:' in log_text:
        raise RuntimeError('Native capture failed: ' + str(log_path))
    report_path = output / 'capture.json'
    report = json.loads(report_path.read_text())
    if not report.get('complete') or not report.get('source_unchanged') or len(report.get('shots', [])) != expected:
        raise ValueError('Incomplete requested-view report')
    if args.ability_reel or args.abilities_only:
        phases = report.get('ability_phases', [])
        if len(phases) != 5 or any(not row['normal_runtime_request'] or not row['normal_army_clock'] or row['phases'] != ['windup','release','impact','expiry'] for row in phases):
            raise ValueError('Incomplete actual ability lifecycle review')
    if args.character_detail:
        pairs = report.get('character_pairs', [])
        if len(pairs) != 2 or any(not row['same_pose'] or not row['same_camera'] or not row['review_only'] or row['runtime_promoted'] or row['released']['configured'] for row in pairs):
            raise ValueError('Incomplete optional character comparison or release')
    for resource, sha in report['source_sha256'].items():
        path = project / resource.removeprefix('res://')
        if digest(path) != sha: raise ValueError('Changed source: ' + resource)
    for shot in report['shots']:
        if digest(output / shot['file']) != shot['sha256']:
            raise ValueError('Changed raw framebuffer')
    warnings = [line for line in log_text.splitlines() if 'WARNING:' in line]
    receipt = {'complete': True, 'godot_exit_code': result.returncode, 'command': command, 'raw_pngs': expected, 'renderer': report['renderer'], 'adapter': report['adapter'], 'source_pins': len(report['source_sha256']), 'report_sha256': digest(report_path), 'runner_sha256': runner_sha, 'godot_log_sha256': digest(log_path), 'xvfb_log_sha256': digest(xlog_path), 'warnings': warnings, 'scope': report['scope']}
    (output / 'run.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__': main()
