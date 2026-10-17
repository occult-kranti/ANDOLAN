#!/usr/bin/env python3
"""Capture the current Rama kit against real native receivers on an owned display."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

PROJECT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rama_capture_helpers', PROJECT / 'tools/run-traversal-capture.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
IDS = ['kodanda','piercing_dawn','measured_step','guardian_circle','dawn_volley']


def validate(report, output, project, preview, guardian_probe=False):
    if not report.get('complete') or report.get('failure') or report.get('kind') != 'actual-rama-native-gameplay':
        raise ValueError('Capture failed: ' + str(report.get('failure')))
    if report.get('renderer') != 'forward_plus' or str(report.get('display', '')).lower() != 'x11' or not report.get('gameplay_applied'):
        raise ValueError('Real Forward+ X11 gameplay required')
    if not report.get('source_unchanged') or report['source_sha256'] != report['source_after_sha256']:
        raise ValueError('Sources changed during capture')
    for path, digest in report['source_sha256'].items():
        if helpers.sha256(project / path.removeprefix('res://')) != digest:
            raise ValueError('Stale capture source: ' + path)
    for entry in report['imports'].values():
        if not entry['fresh'] or helpers.sha256(project / entry['imported'].removeprefix('res://')) != entry['sha256']:
            raise ValueError('Imported resource changed')
    if bool(report.get('guardian_probe', False)) != guardian_probe or [take['ability_id'] for take in report['takes']] != (['guardian_circle'] if guardian_probe else IDS):
        raise ValueError('Exact requested ability takes required')
    for take in report['takes']:
        if take['release_count'] != 1 or take['physics_ticks'] != take['frame_count'] * 2:
            raise ValueError('Wrong release or real physics chronology')
        if not preview and not take['normal_expiry']:
            raise ValueError('Full take must show natural expiry')
    for index, frame in enumerate(report['frames']):
        if frame['index'] != index or frame['physics_tick_delta'] != 2 or not frame['fx']['finite']:
            raise ValueError('Invalid sequential frame')
        truth=frame.get('truth',{})
        if not truth or truth['displayed_notice'] != truth['runtime_notice']:
            raise ValueError('Rendered HUD notice differs from current authority at frame '+str(index))
        shield=truth['vitals']['shield']
        if (shield>0 and ('+%.0f'%shield) not in truth['displayed_life']) or (shield<=0 and '+' in truth['displayed_life']):
            raise ValueError('Rendered shield label is stale at frame '+str(index))
        for field in truth['fields']:
            authority=next(c for c in truth['casts'] if c['ability_id']=='guardian_circle')
            guardian=next(t for t in report['takes'] if t['ability_id']=='guardian_circle')
            active=guardian['events'][0]['timing']['active_s']
            live=not authority['released'] or field['authority_age_s']-field['release_age_s']+1e-6<active
            if field['warning_visible'] != live or (not live and (field['main_opacity']>1e-6 or field['recipient_surfaces']!=0)):
                raise ValueError('Guardian boundary/recipient expiry disagrees with authority at frame '+str(index))
        if not preview:
            helpers.verify_image(output, frame['image'], (1280,720))
    for still in report['stills']:
        helpers.verify_image(output, still['image'], (1280,720))
    if len(report['stills']) != (3 if guardian_probe else 25):
        raise ValueError('Unexpected gameplay/review still count')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--runtime', type=Path, default=Path('/workspace/tooling/native-render/runtime'))
    parser.add_argument('--godot', default=shutil.which('godot'))
    parser.add_argument('--display', type=int, default=128)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--guardian-probe', action='store_true', help='One complete actual Guardian take, with per-frame authority/HUD evidence')
    parser.add_argument('--shader-cache-seed', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.preview and args.guardian_probe:parser.error('Guardian probe requires a complete natural lifetime')
    if not args.output.is_absolute():parser.error('Output must be absolute')
    output, project, runtime = args.output.resolve(), args.project.resolve(), args.runtime.resolve()
    user = output.with_name(output.name + '-user')
    log_path = output.with_name(output.name + '.godot.log')
    xlog_path = output.with_name(output.name + '.xvfb.log')
    if any(path.exists() for path in [output,user,log_path,xlog_path]) or not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        parser.error('Choose fresh output and unused display 90–199')
    command = [args.godot,'--path',str(project),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--fixed-fps','30','--script','res://tools/capture-rama-gameplay.gd','--','--output='+str(output)]
    if args.preview:command.append('--preview')
    if args.guardian_probe:command.append('--guardian-probe')
    if args.dry_run:
        print(json.dumps({'command':command,'output':str(output),'starts_renderer':False},indent=2));return
    xvfb, icd = runtime/'usr/bin/Xvfb', runtime/'usr/share/vulkan/icd.d/lvp_icd.json'
    if not args.godot or not xvfb.is_file() or not icd.is_file():parser.error('Prepared Godot/render runtime required')
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not args.preview and (not ffmpeg or not ffprobe):parser.error('FFmpeg and ffprobe required')
    output.parent.mkdir(parents=True,exist_ok=True);user.mkdir()
    env = os.environ.copy()
    env.update(DISPLAY=f':{args.display}', LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else ''), VK_ICD_FILENAMES=str(icd), LP_NUM_THREADS='2')
    for key,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        env[key]=str(user/folder);(user/folder).mkdir()
    env['MESA_SHADER_CACHE_DIR']=str(user/'cache/mesa')
    seed=helpers.seed_shader_cache(args.shader_cache_seed,user/'cache/mesa')
    with xlog_path.open('x') as xlog, log_path.open('x') as log:
        server=subprocess.Popen([str(xvfb),env['DISPLAY'],'-screen','0','1280x720x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xlog,stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if server.poll() is not None:raise RuntimeError('Owned Xvfb failed')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists():break
                time.sleep(.1)
            else:raise RuntimeError('Owned X display missing')
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=2400)
        finally:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait()
    report_path=output/'rama-gameplay-review.json'
    if not report_path.is_file():raise RuntimeError('Missing report; inspect '+str(log_path))
    log=log_path.read_text()
    if result.returncode or 'SCRIPT ERROR:' in log or '\nERROR:' in log:raise RuntimeError('Renderer failed; preserve '+str(log_path))
    report=json.loads(report_path.read_text())
    validate(report,output,project,args.preview,args.guardian_probe)
    video=None
    if not args.preview:
        video=output/('rama-guardian-expiry.mp4' if args.guardian_probe else 'rama-five-abilities.mp4')
        subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-n','-framerate','30','-i',str(output/'frame-%05d.png'),'-an','-c:v','libx264','-threads','2','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True,timeout=300)
        probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)],timeout=30))
        if len(probe['streams'])!=1 or int(probe['streams'][0]['nb_read_frames'])!=len(report['frames']):raise ValueError('Video frame mismatch')
        subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-xerror','-nostdin','-i',str(video),'-f','null','-'],check=True,timeout=60)
        scope='One complete actual Guardian take with natural expiry.' if args.guardian_probe else 'Five separate actual ability takes concatenated in kit order; scene resets are deliberate cuts.'
        helpers.write_new_json(output/'rama-video.json',{'complete':True,'file':video.name,'sha256':helpers.sha256(video),'probe':probe,'scope':scope+' Silent, simulated30fps, not real-time performance.'})
    helpers.write_new_json(output/'capture-run.json',{'complete':True,'command':command,'preview':args.preview,'guardian_probe':args.guardian_probe,'report_sha256':helpers.sha256(report_path),'runner_sha256':helpers.sha256(Path(__file__)),'log_sha256':helpers.sha256(log_path),'frames':len(report['frames']),'stills':len(report['stills']),'video_sha256':helpers.sha256(video) if video else None,'shader_cache_seed':seed})
    print(json.dumps({'complete':True,'output':str(output),'frames':len(report['frames']),'stills':len(report['stills']),'video':str(video) if video else None}))

if __name__=='__main__':main()
