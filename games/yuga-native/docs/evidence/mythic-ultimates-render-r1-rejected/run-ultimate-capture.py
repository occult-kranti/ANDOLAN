#!/usr/bin/env python3
"""Capture 14 original invocation studies + modes and one actual 4-second VFX take.

Scripted presentation; no gameplay authority/damage, audible review or realtime
performance claim. Requires explicit shared renderer ownership before running.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time

PROJECT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('traversal_capture_helpers', PROJECT / 'tools/run-traversal-capture.py')
_helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helpers)
sha256 = _helpers.sha256
verify_image = _helpers.verify_image
seed_shader_cache = _helpers.seed_shader_cache
write_new_json = _helpers.write_new_json
HEROES = ['rama','ravana','arjuna','duryodhana','hanuman','karna','bhima','meghnad','sita','draupadi','subhadra','hidimbi','chitrangada','ulupi']


def validate_capture(report: dict, output: Path, project: Path) -> None:
    if report.get('kind') != 'actual-staged-native-ultimate-vfx' or report.get('gameplay_applied') is not False:
        raise ValueError('Wrong capture scope')
    if report.get('complete') is not True or report.get('failure'):
        raise ValueError('Capture did not complete')
    if report.get('renderer') != 'forward_plus' or str(report.get('display','')).lower() != 'x11':
        raise ValueError('Actual Forward+ X11 display required')
    for key, expected in [('fps',30),('physics_hz',60),('time_scale',1),('take_physics_ticks',240),('width',1280),('height',720)]:
        value = report.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or value != expected:
            raise ValueError('Invalid clock/resolution: '+key)
    frames = report['frames']
    if len(frames) != 120 or report.get('expected_frames') != 120:
        raise ValueError('Expected120 sequential frames')
    last_tick, last_draw = report['take_start_tick'], -1
    phases = set()
    def verify_fx(fx: dict) -> None:
        if fx.get('finite') is not True:
            raise ValueError('Nonfinite VFX state')
        for key,maximum in [('active',4),('nodes',196),('triangles',72000),('lights',0),('particles',0),('voices',0)]:
            if type(fx.get(key)) is not int or not 0 <= fx[key] <= maximum:
                raise ValueError('VFX budget exceeded: '+key)
        if any(type(fx.get(k)) is not bool for k in ['reduced_effects','reduced_motion']):
            raise ValueError('Missing quality modes')
    for index,frame in enumerate(frames):
        if frame.get('index') != index or frame.get('finite') is not True or frame.get('physics_tick_delta') != 2 or frame['physics_tick'] != last_tick+2 or frame['render_frame'] <= last_draw:
            raise ValueError('Sequential frame/tick invariant failed')
        if frame['image']['file'] != f'frame-{index:05d}.png':
            raise ValueError('Wrong frame filename')
        verify_image(output,frame['image'],(1280,720))
        verify_fx(frame['fx'])
        phases.update(frame['effect_phases'])
        last_tick,last_draw = frame['physics_tick'],frame['render_frame']
    if not {'begin','release','impact'} <= phases or frames[-1]['fx']['active'] != 0:
        raise ValueError('Required representative phases/cleanup absent')
    if any(report['outcomes'].get(key) is not True for key in ['begin','release','contact','expired','persistent_zone_cancelled_for_take_end']):
        raise ValueError('Scripted representative choreography incomplete')
    stills = report['stills']
    if len(stills) != 14 or {s['hero_id'] for s in stills} != set(HEROES):
        raise ValueError('Need exactly14 hero motif stills')
    codex = {h['id']:h['abilities'][2]['native_demo']['shape'] for h in json.loads((project/'assets/design/hero-codex.json').read_text())['heroes']}
    for still in stills:
        hero = still['hero_id']
        if still['effect_id'] != hero+'.r.v1' or still['codex_shape'] != codex[hero] or still['image']['file'] != f'still-{hero}.png' or not math.isfinite(still['sample_age_s']) or still['sample_age_s'] <= 0:
            raise ValueError('Wrong motif identity/age')
        verify_image(output,still['image'],(1280,720))
        verify_fx(still['fx'])
    variants = report['variants']
    if len(variants) != 3 or {s['id'] for s in variants} != {'low-effects','reduced-motion','four-overlap'}:
        raise ValueError('Missing quality/overlap views')
    for still in variants:
        if still['image']['file'] != 'still-'+still['id']+'.png':
            raise ValueError('Wrong variant filename')
        verify_image(output,still['image'],(1280,720))
        verify_fx(still['fx'])
        expected = {'low-effects':('reduced_effects',True),'reduced-motion':('reduced_motion',True),'four-overlap':('active',4)}[still['id']]
        if still['fx'][expected[0]] != expected[1]:
            raise ValueError('Variant does not demonstrate its mode')
    paths = [project/'project.godot',project/'tools/capture-ultimates.gd',project/'tools/run-ultimate-capture.py',project/'art/world/confluence-map.json']
    for directory in ['scripts','scenes','assets','shaders']:
        paths.extend(p for p in (project/directory).rglob('*') if p.is_file())
    expected_sources = {'res://'+str(p.relative_to(project)):sha256(p) for p in paths}
    if expected_sources != report['source_sha256']:
        raise ValueError('Runtime source bytes or file set changed')
    if set(report['imports']) != {'res://assets/heroes/rama-production.glb'}:
        raise ValueError('Missing exact imported hero proof')
    for imported in report['imports'].values():
        if imported.get('fresh') is not True or sha256(project/imported['imported'].removeprefix('res://')) != imported['sha256']:
            raise ValueError('Stale imported asset')


def encode_video(output: Path, report_path: Path, ffmpeg: str, ffprobe: str) -> dict:
    video = output/'yuga-ultimate-studies.mp4'
    command = [ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-n','-framerate','30','-i',str(output/'frame-%05d.png'),'-an','-c:v','libx264','-threads','2','-preset','medium','-crf','18','-pix_fmt','yuv420p','-frames:v','120','-movflags','+faststart',str(video)]
    subprocess.run(command,check=True,timeout=300)
    probe_command = [ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)]
    probe = json.loads(subprocess.check_output(probe_command,timeout=30))
    if len(probe['streams']) != 1:
        raise ValueError('Expected one silent video stream')
    stream = probe['streams'][0]
    if stream['codec_type'] != 'video' or stream['codec_name'] != 'h264' or stream['pix_fmt'] != 'yuv420p' or (stream['width'],stream['height']) != (1280,720) or int(stream['nb_read_frames']) != 120 or Fraction(stream['avg_frame_rate']) != 30 or abs(float(probe['format']['duration'])-4) > .02:
        raise ValueError('Encoded frame count/dimensions/duration mismatch')
    subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-xerror','-nostdin','-i',str(video),'-f','null','-'],check=True,timeout=60)
    result = {'schema':1,'complete':True,'file':video.name,'bytes':video.stat().st_size,'sha256':sha256(video),'capture_report_sha256':sha256(report_path),'encode_command':command,'probe_command':probe_command,'probe':probe,'scope':'Silent120-frame actual staged VFX take. Rama full presentation lifecycle and Sita onset/sustain, explicitly cancelled before normal zone expiry. No gameplay damage, audio audition or realtime-performance claim.'}
    write_new_json(output/'ultimate-video.json',result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--project',type=Path,default=PROJECT)
    parser.add_argument('--runtime',type=Path,default=Path('/workspace/tooling/native-render/runtime'))
    parser.add_argument('--godot',default=shutil.which('godot'))
    parser.add_argument('--display',type=int,default=120)
    parser.add_argument('--shader-cache-seed',type=Path)
    parser.add_argument('--dry-run',action='store_true')
    args = parser.parse_args()
    output,project,runtime = args.output.resolve(),args.project.resolve(),args.runtime.resolve()
    user = output.with_name(output.name+'-user')
    log_path = output.with_name(output.name+'.godot.log')
    xlog_path = output.with_name(output.name+'.xvfb.log')
    if any(p.exists() for p in [output,user,log_path,xlog_path]) or not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        parser.error('Choose a new output and unused owned display90..199')
    command = [args.godot,'--path',str(project),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--fixed-fps','30','--script','res://tools/capture-ultimates.gd','--','--output='+str(output)]
    if args.dry_run:
        print(json.dumps({'command':command,'output':str(output),'starts_renderer':False},indent=2));return
    ffmpeg,ffprobe = shutil.which('ffmpeg'),shutil.which('ffprobe')
    if not args.godot or not ffmpeg or not ffprobe:
        parser.error('Godot,FFmpeg andffprobe are required')
    xvfb,icd = runtime/'usr/bin/Xvfb',runtime/'usr/share/vulkan/icd.d/lvp_icd.json'
    if not xvfb.is_file() or not icd.is_file():
        parser.error('Restore native renderer runtime first')
    output.parent.mkdir(parents=True,exist_ok=True)
    user.mkdir()
    environment = os.environ.copy()
    environment.update(DISPLAY=f':{args.display}',LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu')+(':'+environment['LD_LIBRARY_PATH'] if environment.get('LD_LIBRARY_PATH') else ''),VK_ICD_FILENAMES=str(icd),LP_NUM_THREADS='2')
    for variable,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        environment[variable] = str(user/folder);(user/folder).mkdir()
    environment['MESA_SHADER_CACHE_DIR'] = str(user/'cache/mesa')
    cache_seed = seed_shader_cache(args.shader_cache_seed,user/'cache/mesa')
    with xlog_path.open('x') as xlog,log_path.open('x') as log:
        server = subprocess.Popen([str(xvfb),environment['DISPLAY'],'-screen','0','1280x720x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=environment,stdout=xlog,stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if server.poll() is not None:raise RuntimeError('Owned Xvfb failed')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists():break
                time.sleep(.1)
            else:raise RuntimeError('Owned display socket missing')
            result = subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        finally:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait()
    report_path = output/'ultimate-render-review.json'
    if not report_path.is_file():raise RuntimeError('Missing report; retain logs at '+str(log_path))
    log_text = log_path.read_text()
    if result.returncode or 'SCRIPT ERROR:' in log_text or '\nERROR:' in log_text:raise RuntimeError('Renderer failed; inspect '+str(log_path))
    report = json.loads(report_path.read_text())
    validate_capture(report,output,project)
    video = encode_video(output,report_path,ffmpeg,ffprobe)
    write_new_json(output/'capture-run.json',{'complete':True,'command':command,'capture_report_sha256':sha256(report_path),'runner_sha256':sha256(Path(__file__)),'godot_log_sha256':sha256(log_path),'frames':120,'physics_ticks':240,'video_sha256':video['sha256'],'dimensions':[1280,720],'shader_cache_seed':cache_seed,'settings_scope':'Fresh isolatedXDG settings/cache; shader compilation cache only may be seeded.'})
    print(json.dumps({'complete':True,'frames':120,'stills':14,'variants':3,'output':str(output),'video':video['file']}))

if __name__ == '__main__':main()
