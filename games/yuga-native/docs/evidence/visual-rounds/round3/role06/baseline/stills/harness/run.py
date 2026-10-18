#!/usr/bin/env python3
"""Capture bounded source-pinned face, groom and motion review controls.

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
ABILITY_IDS = ['kodanda','piercing_dawn','measured_step','guardian_circle','dawn_volley']

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
    parser.add_argument('--mode', choices=['stills','continuity','actions','probe','forms','groom-stills','groom-continuity','groom-probe'], default='stills')
    parser.add_argument('--context', choices=['courtyard','stone','foliage'], default='courtyard')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.mode not in ('stills','probe') and args.context != 'courtyard': parser.error('Sequence requires courtyard')
    output, project, runtime = args.output.resolve(), args.project.resolve(), args.runtime.resolve()
    user = output.with_name(output.name + '-user')
    log_path = output.with_suffix('.godot.log')
    xlog_path = output.with_suffix('.xvfb.log')
    if not args.output.is_absolute() or any(os.path.lexists(path) for path in (output, user, log_path, xlog_path)):
        parser.error('Choose a fresh absolute output')
    if not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        parser.error('Choose unused X display 90–199')
    command = [args.godot, '--path', str(project), '--display-driver', 'x11', '--rendering-method', 'forward_plus', '--audio-driver', 'Dummy', '--disable-vsync', '--fixed-fps', '30', '--max-threads', '2', '--script', 'res://tools/visual-rounds/capture.gd', '--', '--output=' + str(output)]
    command.extend(['--mode='+args.mode, '--context='+args.context])
    expected = 3 if args.mode == 'forms' else 36 if args.mode == 'continuity' else (5 if args.mode == 'actions' else (1 if args.mode == 'probe' else (10 if args.context == 'courtyard' else 2)))
    if args.mode.startswith('groom-'):
        command[command.index('--script')+1] = 'res://tools/visual-rounds/capture_groom.gd'
        expected = {'groom-stills':8,'groom-continuity':150,'groom-probe':1}[args.mode]
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
    if args.mode == 'continuity':
        sequence = report['shots']
        if any(b['render_frame'] != a['render_frame']+1 for a,b in zip(sequence,sequence[1:])):
            raise ValueError('Sequence skipped a rendered frame')
        weights = [s['face']['weights']['rama_blink_left'] for s in sequence]
        if max(weights) < .98 or weights[-1] >= .5: raise ValueError('Blink closure/reopen missing')
        kinds = [e['kind'] for e in report['ability_events']]
        if not all(k in kinds for k in ['release','cancel']): raise ValueError('Actual release/cancel absent')
        casts = {row['ability']:row['result'] for row in report['sequence_controls'] if row['kind']=='cast'}
        release = [e for e in report['ability_events'] if e['kind']=='release' and e['cast_id']==casts['kodanda']['cast_id']]
        cancelled = [e for e in report['ability_events'] if e['kind']=='cancel' and e['cast_id']==casts['piercing_dawn']['cast_id']]
        forbidden = [e for e in report['ability_events'] if e['kind'] in ['release','impact'] and e['cast_id']==casts['piercing_dawn']['cast_id']]
        if not release or not cancelled or forbidden: raise ValueError('Cast-specific release/cancel contract failed')
    if args.mode == 'groom-continuity':
        sequence = report['shots']
        if any(b['render_frame'] != a['render_frame']+1 for a,b in zip(sequence,sequence[1:])):
            raise ValueError('Groom sequence skipped a rendered frame')
        casts = [x for x in report['sequence_controls'] if x['kind']=='cast']
        if {x['ability'] for x in casts} != {'kodanda','measured_step'}: raise ValueError('Required actual casts absent')
        for cast in casts:
            if not cast['result']['accepted'] or not any(e['kind']=='release' and e['cast_id']==cast['result']['cast_id'] for e in report['ability_events']):
                raise ValueError('Actual cast release absent: '+cast['ability'])
        if not any(x['kind']=='actual_reset' for x in report['sequence_controls']): raise ValueError('Actual reset absent')
        positions = [tuple(s['player_transform'][3]) for s in sequence]
        if len(set(positions)) < 20: raise ValueError('Actual movement absent')
        if not all(s['bounds']['passed'] and s['secondary']['finite'] for s in sequence): raise ValueError('Framing or finite-state failure')
        if max(abs(v) for v in sequence[-1]['secondary']['cloth_offset'])>.001: raise ValueError('Reset did not settle cloth')
    for resource, sha in report['source_sha256'].items():
        path = project / resource.removeprefix('res://')
        if digest(path) != sha: raise ValueError('Changed source: ' + resource)
    for shot in report['shots']:
        if digest(output / shot['file']) != shot['sha256']:
            raise ValueError('Changed raw framebuffer')
    warnings = [line for line in log_text.splitlines() if 'WARNING:' in line]
    receipt = {'complete': True, 'godot_exit_code': result.returncode, 'command': command, 'raw_pngs': expected, 'renderer': report['renderer'], 'adapter': report['adapter'], 'source_pins': len(report['source_sha256']), 'report_sha256': digest(report_path), 'runner_sha256': runner_sha, 'godot_log_sha256': digest(log_path), 'xvfb_log_sha256': digest(xlog_path), 'warnings': warnings, 'scope': report['scope']}
    (output / 'run.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if args.mode in ['continuity','groom-continuity']:
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-framerate','30','-i',str(output/'frame-%03d.png'),'-an','-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p',str(output/'continuity.mp4')],check=True)
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__': main()
