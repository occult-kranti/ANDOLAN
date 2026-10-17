#!/usr/bin/env python3
"""Capture six seconds of actual triad simulation on an owned software display."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time

spec = importlib.util.spec_from_file_location('capture_helpers', Path(__file__).with_name('run-traversal-capture.py'))
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def validate(report, output, project):
    if report.get('complete') is not True or report.get('failure'):
        raise ValueError('Incomplete triad capture: ' + str(report.get('failure')))
    if report.get('renderer') != 'forward_plus' or report.get('display') == 'headless':
        raise ValueError('Actual Forward+ display required')
    if (report.get('fps'), report.get('physics_hz'), report.get('take_physics_ticks'), report.get('width'), report.get('height')) != (30, 60, 360, 1280, 720):
        raise ValueError('Capture timing differs')
    if report.get('time_scale') != 1.0:
        raise ValueError('Capture time scale differs')
    frames = report['frames']
    if len(frames) != 180 or len(list(output.glob('frame-*.png'))) != 180:
        raise ValueError('Expected 180 consecutive actual frames')
    if type(report.get('take_start_tick')) is not int or report['take_start_tick'] < 0:
        raise ValueError('Invalid starting tick')
    previous_draw = -1
    for index, frame in enumerate(frames):
        if frame['index'] != index or frame.get('physics_tick_delta') != 2 or frame['physics_tick'] != report['take_start_tick'] + 2 * (index + 1) or frame['finite'] is not True:
            raise ValueError('Nonconsecutive or nonfinite frame')
        if type(frame.get('render_frame')) is not int or frame['render_frame'] <= previous_draw:
            raise ValueError('Rendered frame counter did not advance')
        previous_draw = frame['render_frame']
        if frame['image']['file'] != f'frame-{index:05d}.png':
            raise ValueError('Frame name/order mismatch')
        helpers.verify_image(output, frame['image'], (1280, 720))
    if not all(report['outcomes'].get(key) is True for key in ('captured', 'supplied', 'finite')):
        raise ValueError('Required relay capture and supply behavior was not observed')
    if report['before']['rules']['sites'][1]['owner'] != 'neutral' or report['after']['rules']['sites'][1]['owner'] != 'sun' or report['before']['arrows_total'] != 0 or report['after']['arrows_total'] < 3:
        raise ValueError('Neutral to owned relay and real ammo supply were not observed')
    names = {'still-lotus-day.png', 'still-lotus-night.png', 'still-reed-day.png', 'still-sky-day.png'}
    if {item['image']['file'] for item in report.get('stills', [])} != names:
        raise ValueError('Four required art views missing')
    for item in report['stills']:
        helpers.verify_image(output, item['image'], (1280, 720))
    expected = {f'res://{p.relative_to(project).as_posix()}' for folder in ('scripts', 'scenes', 'assets') for p in (project / folder).rglob('*') if p.is_file()}
    expected.update('res://' + name for name in ('project.godot', 'art/world/confluence-map.json', 'tools/capture-traversal.gd', 'tools/run-traversal-capture.py', 'tools/capture-triad.gd', 'tools/run-triad-capture.py'))
    if set(report['source_sha256']) != expected:
        raise ValueError('Capture source inventory differs from checkout')
    for name, digest in report['source_sha256'].items():
        if helpers.sha256(project / name.removeprefix('res://')) != digest:
            raise ValueError('Capture source changed: ' + name)
    if set(report.get('imports', {})) != {'res://assets/heroes/rama-production.glb','res://assets/world/architecture.glb','res://assets/world/nature.glb'}:
        raise ValueError('Imported-asset evidence missing')
    for item in report['imports'].values():
        if item['fresh'] is not True or helpers.sha256(project / item['imported'].removeprefix('res://')) != item['sha256']:
            raise ValueError('Imported asset changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--display', type=int, default=119)
    parser.add_argument('--shader-cache-seed', type=Path)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    runtime = Path('/workspace/tooling/native-render/runtime')
    output = args.output
    if not output.is_absolute() or not 90 <= args.display <= 199:
        parser.error('Use a new absolute output and display in [90,199]')
    user = output.with_name(output.name + '-user')
    log_path, xlog_path = Path(str(output)+'.godot.log'), Path(str(output)+'.xvfb.log')
    if any(p.exists() for p in (output, user, log_path, xlog_path, Path(f'/tmp/.X11-unix/X{args.display}'))):
        parser.error('Output, settings, logs and display must be unused')
    engine, ffmpeg, ffprobe = (shutil.which(x) for x in ('godot', 'ffmpeg', 'ffprobe'))
    if not all((engine, ffmpeg, ffprobe)):
        parser.error('Godot, FFmpeg and ffprobe are required')
    environment = os.environ.copy()
    environment.update(DISPLAY=f':{args.display}', LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu') + (':' + environment['LD_LIBRARY_PATH'] if environment.get('LD_LIBRARY_PATH') else ''), VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'), LP_NUM_THREADS='2')
    for name, folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        environment[name] = str(user/folder)
        (user/folder).mkdir(parents=True)
    environment['MESA_SHADER_CACHE_DIR'] = str(user/'cache/mesa')
    seed = helpers.seed_shader_cache(args.shader_cache_seed, user/'cache/mesa')
    command = [engine, '--path', str(project), '--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--fixed-fps','30','--script','res://tools/capture-triad.gd','--','--output='+str(output)]
    with log_path.open('x') as log, xlog_path.open('x') as xlog:
        server = subprocess.Popen([str(runtime/'usr/bin/Xvfb'),environment['DISPLAY'],'-screen','0','1280x720x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=environment,stdout=xlog,stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if server.poll() is not None: raise RuntimeError('Owned Xvfb exited')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists(): break
                time.sleep(.1)
            else: raise RuntimeError('Owned display failed to become ready')
            result = subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    log_text = log_path.read_text()
    if result.returncode or 'SCRIPT ERROR:' in log_text or '\nERROR:' in log_text:
        raise RuntimeError('Preserve failed renderer logs: '+str(log_path))
    report_path = output/'triad-render-review.json'
    report = json.loads(report_path.read_text())
    validate(report,output,project)
    video = output/'yuga-triad-preview.mp4'
    encode = [ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-n','-framerate','30','-i',str(output/'frame-%05d.png'),'-an','-c:v','libx264','-threads','2','-preset','medium','-crf','18','-pix_fmt','yuv420p','-frames:v','180',str(video)]
    subprocess.run(encode,check=True)
    probe = json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)],text=True))
    streams = probe['streams']
    duration = float(probe['format']['duration'])
    if len(streams)!=1 or streams[0]['codec_type']!='video' or streams[0].get('codec_name')!='h264' or (streams[0].get('width'),streams[0].get('height'))!=(1280,720) or streams[0].get('avg_frame_rate')!='30/1' or int(streams[0]['nb_read_frames'])!=180 or not math.isfinite(duration) or abs(duration-6)>.02:
        raise ValueError('Encoded video differs from capture timing')
    helpers.write_new_json(output/'triad-video.json', {'complete':True,'file':video.name,'bytes':video.stat().st_size,'sha256':helpers.sha256(video),'capture_report_sha256':helpers.sha256(report_path),'encode_command':encode,'probe':probe,'scope':'Silent actual triad simulation; 30 fps is simulated playback, not hardware performance.'})
    helpers.write_new_json(output/'capture-run.json',{'complete':True,'command':command,'source_report_sha256':helpers.sha256(report_path),'shader_cache_seed':seed,'frames':180,'physics_ticks':360})
    print(json.dumps({'complete':True,'output':str(output),'video':video.name}))


if __name__ == '__main__':
    main()
