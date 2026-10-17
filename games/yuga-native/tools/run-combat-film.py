#!/usr/bin/env python3
"""Own an actual software-rendered film capture and encode its sequential frames."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--runtime', type=Path, default=Path('/workspace/tooling/native-render/runtime'))
    parser.add_argument('--godot', default=shutil.which('godot'))
    parser.add_argument('--display', type=int, default=113)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--poses', action='store_true', help='Render eight close studio poses before film acceptance')
    parser.add_argument('--width', type=int, default=960)
    parser.add_argument('--height', type=int, default=540)
    args = parser.parse_args()
    if args.poses:
        args.preview = True
        args.width = args.height = 960
    output, runtime, project = args.output.resolve(), args.runtime.resolve(), args.project.resolve()
    if output.exists() or not args.godot:
        raise ValueError('Require an installed Godot and a new output directory')
    if not 90 <= args.display <= 199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():
        raise ValueError('Select an unused display in [90,199]')
    xvfb = runtime / 'usr/bin/Xvfb'
    icd = runtime / 'usr/share/vulkan/icd.d/lvp_icd.json'
    if not xvfb.is_file() or not icd.is_file():
        raise ValueError('Prepare the verified rendering runtime first')
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(DISPLAY=f':{args.display}',
        LD_LIBRARY_PATH=str(runtime / 'usr/lib/x86_64-linux-gnu') + (':' + environment['LD_LIBRARY_PATH'] if environment.get('LD_LIBRARY_PATH') else ''),
        VK_ICD_FILENAMES=str(icd), LP_NUM_THREADS='2')
    user = output.parent / (output.name + '-user')
    for variable, folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        environment[variable] = str(user / folder)
        Path(environment[variable]).mkdir(parents=True, exist_ok=True)
    # Share only rebuildable Mesa shader cache between review passes.
    environment['MESA_SHADER_CACHE_DIR'] = str(project / 'build' / 'film-mesa-cache')
    command = [args.godot, '--path', str(project), '--display-driver','x11',
        '--rendering-method','forward_plus', '--audio-driver','Dummy', '--disable-vsync',
        '--script','res://tools/capture-duel-poses.gd' if args.poses else 'res://tools/capture-combat-film.gd', '--', '--output=' + str(output),
        f'--width={args.width}', f'--height={args.height}']
    if args.preview:
        command.append('--preview')
    with output.with_suffix('.xvfb.log').open('w') as xlog, output.with_suffix('.godot.log').open('w') as log:
        server = subprocess.Popen([str(xvfb),environment['DISPLAY'],'-screen','0',
            f'{args.width}x{args.height}x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],
            env=environment,stdout=xlog,stderr=subprocess.STDOUT)
        try:
            for _ in range(30):
                if server.poll() is not None:
                    raise RuntimeError('Owned Xvfb failed to start; inspect its log')
                if Path(f'/tmp/.X11-unix/X{args.display}').exists():
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError('Owned Xvfb did not create its socket')
            result = subprocess.run(command,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=3660)
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    report = json.loads((output / 'combat-film-render.json').read_text())
    log_text = output.with_suffix('.godot.log').read_text()
    if result.returncode or not report['complete'] or 'SCRIPT ERROR:' in log_text or '\nERROR:' in log_text:
        raise RuntimeError('Film capture failed; inspect its preserved report/log')
    for frame in report['frames']:
        if sha256(output / frame['file']) != frame['sha256']:
            raise ValueError('Rendered frame hash changed')
    if not args.preview:
        script = json.loads((project / 'assets/cinematics/confluence-duel.json').read_text())
        audio = project / script['audio_mix_path'].removeprefix('res://')
        if sha256(audio) != report['source_sha256'][script['audio_mix_path']]:
            raise ValueError('Audio changed after capture')
        if report['frame_count'] != 576 or any(abs(f['t_seconds'] - i/24) > 1e-5 for i,f in enumerate(report['frames'])):
            raise ValueError('Expected exactly 576 consecutive 24-Hz samples')
        video = output / 'yuga-confluence-duel.mp4'
        encode = ['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n',
            '-framerate','24','-i',str(output/'frame-%05d.png'),'-i',str(audio),
            '-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18',
            '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','24','-movflags','+faststart',str(video)]
        subprocess.run(encode,check=True,timeout=240)
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames',
            '-show_streams','-show_format','-of','json',str(video)],text=True))
        v = next(s for s in probe['streams'] if s['codec_type']=='video')
        a = next(s for s in probe['streams'] if s['codec_type']=='audio')
        if int(v['nb_read_frames']) != 576 or v['avg_frame_rate'] != '24/1' or a['sample_rate'] != '48000' or a['channels'] != 2 or abs(float(probe['format']['duration'])-24)>0.05:
            raise ValueError('Encoded duration, sample rate, channels or frame count differs')
        encoded = {'schema':1,'complete':True,'video':{'file':video.name,'bytes':video.stat().st_size,'sha256':sha256(video)},
            'render_report_sha256':sha256(output/'combat-film-render.json'),'audio_sha256':sha256(audio),
            'command':encode,'probe':probe,'scope':'24 seconds of actual sequential engine rendering; soundtrack authored separately and muxed to the same timeline.'}
        (output/'combat-film-video.json').write_text(json.dumps(encoded,indent=2)+'\n')
    print(json.dumps({'complete':True,'frames':report['frame_count'],'preview':args.preview,'output':str(output)}))


if __name__ == '__main__':
    main()
