#!/usr/bin/env python3
"""Own a bounded original-native carry capture; rendered evidence, not GPU FPS."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

NATIVE = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('capture_helpers', NATIVE/'tools/run-traversal-capture.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--display', type=int, default=119)
    parser.add_argument('--shader-cache-seed', type=Path)
    args = parser.parse_args()
    output = args.output
    user = output.with_name(output.name+'-user')
    log_path, xlog_path = Path(str(output)+'.godot.log'), Path(str(output)+'.xvfb.log')
    if not output.is_absolute() or not 90 <= args.display <= 199:
        parser.error('Use an absolute output and display in [90,199]')
    if any(p.exists() for p in (output,user,log_path,xlog_path,Path(f'/tmp/.X11-unix/X{args.display}'))):
        parser.error('Output, user settings, logs and display must be unused')
    runtime = Path('/workspace/tooling/native-render/runtime')
    engine, ffmpeg, ffprobe = (shutil.which(name) for name in ('godot','ffmpeg','ffprobe'))
    if not all((engine,ffmpeg,ffprobe)):
        parser.error('Godot, FFmpeg and ffprobe are required')
    environment = os.environ.copy()
    environment.update(DISPLAY=f':{args.display}',LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu')+(':'+environment['LD_LIBRARY_PATH'] if environment.get('LD_LIBRARY_PATH') else ''),VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),LP_NUM_THREADS='2')
    for name, folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        environment[name]=str(user/folder)
        (user/folder).mkdir(parents=True)
    environment['MESA_SHADER_CACHE_DIR']=str(user/'cache/mesa')
    seed=helpers.seed_shader_cache(args.shader_cache_seed,user/'cache/mesa')
    command=[engine,'--path',str(NATIVE),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--script','res://tools/capture-motion-next.gd','--','--output='+str(output)]
    with log_path.open('x') as log, xlog_path.open('x') as xlog:
        server=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),environment['DISPLAY'],'-screen','0','640x640x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=environment,stdout=xlog,stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                if server.poll() is not None: raise RuntimeError('Owned Xvfb exited')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists(): break
                time.sleep(.1)
            else: raise RuntimeError('Owned display failed to become ready')
            result=subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=660)
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    text=log_path.read_text()
    if result.returncode or 'SCRIPT ERROR:' in text or '\nERROR:' in text:
        raise RuntimeError('Preserve failed renderer log: '+str(log_path))
    report_path=output/'motion-next-render-review.json'
    report=json.loads(report_path.read_text())
    assert report['complete'] and not report['failure'] and report['renderer']=='forward_plus' and report['display']!='headless'
    assert (report['sample_hz'],report['width'],report['height'])==(24,640,640)
    assert len(report['frames'])==169 and len(list(output.glob('frame-*.png')))==169
    previous=-1
    for index, frame in enumerate(report['frames']):
        assert frame['file']==f'frame-{index:05d}.png' and frame['rendered_frame_counter']>previous
        previous=frame['rendered_frame_counter']
        helpers.verify_image(output,dict(frame,width=640,height=640),(640,640))
    run_frames=[frame for frame in report['frames'] if frame['clip']=='run']
    assert any(b['animation_seconds']<a['animation_seconds'] for a,b in zip(run_frames,run_frames[1:])), 'Native run must loop as player.gd does'
    shots=[frame for frame in report['frames'] if frame['triggered']]
    assert len(shots)==3 and all(frame['clip']=='fire' and frame['carry']['weight']==0 for frame in shots), 'First and repeated shots require immediate action ownership'
    assert all(frame['carry']['weight']==0 for frame in report['frames'] if frame['action_active']), 'Carry must not delay action arms/string'
    for name, digest in report['sources'].items():
        assert helpers.sha256(NATIVE/name.removeprefix('res://'))==digest, name
    video=output/'yuga-native-carry-preview.mp4'
    encode=[ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-n','-framerate','24','-i',str(output/'frame-%05d.png'),'-an','-c:v','libx264','-threads','2','-preset','medium','-crf','18','-pix_fmt','yuv420p','-frames:v','169',str(video)]
    subprocess.run(encode,check=True)
    probe=json.loads(subprocess.check_output([ffprobe,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)],text=True))
    assert len(probe['streams'])==1 and int(probe['streams'][0]['nb_read_frames'])==169
    assert abs(float(probe['format']['duration'])-169/24)<.002
    helpers.write_new_json(output/'motion-next-video.json',{'complete':True,'file':video.name,'bytes':video.stat().st_size,'sha256':helpers.sha256(video),'capture_report_sha256':helpers.sha256(report_path),'probe':probe,'scope':'Silent actual sequential software rendering, not hardware performance or human motion acceptance.'})
    helpers.write_new_json(output/'capture-run.json',{'complete':True,'command':command,'frames':169,'runner_sha256':helpers.sha256(Path(__file__)),'source_report_sha256':helpers.sha256(report_path),'shader_cache_seed':seed})
    print(json.dumps({'complete':True,'frames':169,'video':str(video),'sources':report['sources']}))

if __name__=='__main__': main()
