#!/usr/bin/env python3
"""Run an actual frozen-GLB face capture on an exclusively owned display."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
NATIVE=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--display',type=int,default=134);p.add_argument('--shader-cache',type=Path);p.add_argument('--baseline',action='store_true')
    a=p.parse_args()
    assert a.asset.is_absolute()and a.asset.is_file()and a.output.is_absolute()and not a.output.exists()
    assert 90<=a.display<=199 and not Path(f'/tmp/.X11-unix/X{a.display}').exists()
    runtime=Path('/workspace/tooling/native-render/runtime');env=os.environ.copy()
    env.update(DISPLAY=f':{a.display}',LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu'),VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),LP_NUM_THREADS='2',XDG_DATA_HOME=str(a.output)+'-user/data',XDG_CONFIG_HOME=str(a.output)+'-user/config',XDG_CACHE_HOME=str(a.output)+'-user/cache')
    for key in ('XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME'):Path(env[key]).mkdir(parents=True,exist_ok=False)
    if a.shader_cache:
        for name in ('mesa_shader_cache','mesa_shader_cache_db'):
            source=a.shader_cache/name
            if source.is_dir():shutil.copytree(source,Path(env['XDG_CACHE_HOME'])/name)
    with open(str(a.output)+'.xvfb.log','x')as xl,open(str(a.output)+'.godot.log','x')as gl:
        display=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),env['DISPLAY'],'-screen','0','640x800x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT)
        try:
            for unused in range(50):
                if Path(f'/tmp/.X11-unix/X{a.display}').exists():break
                if display.poll()is not None:raise RuntimeError('Owned display stopped')
                time.sleep(.1)
            command=[shutil.which('godot'),'--path',str(NATIVE),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--script','res://art/hero-rama-face/capture_face.gd','--','--asset='+str(a.asset),'--output='+str(a.output)]
            if a.baseline:command.append('--baseline')
            result=subprocess.run(command,env=env,stdout=gl,stderr=subprocess.STDOUT,timeout=600)
        finally:
            display.terminate()
            try:display.wait(timeout=5)
            except subprocess.TimeoutExpired:display.kill();display.wait()
    assert result.returncode==0,str(a.output)+'.godot.log'
    report=json.loads((a.output/'capture.json').read_text())
    assert report['complete']and len(report['frames'])==(3 if a.baseline else 39)
    for path,digest in report['sources'].items():
        source=NATIVE/path.removeprefix('res://')if path.startswith('res://')else Path(path)
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,path
    last_frame=-1
    for frame in report['frames']:
        assert frame['rendered_frame']>last_frame
        assert hashlib.sha256((a.output/frame['file']).read_bytes()).hexdigest()==frame['sha256']
        last_frame=frame['rendered_frame']
    if not a.baseline:
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-framerate','60','-i',str(a.output/'blink-%03d.png'),'-an','-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p',str(a.output/'rama-blink.mp4')],check=True)
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(a.output/'rama-blink.mp4'),'-f','null','-'],check=True)
    print(json.dumps({'complete':True,'frames':len(report['frames']),'output':str(a.output),'scope':'Actual runtime-imported GLB; encoded fixed60Hz sequence is not real-time GPU measurement.'}))

if __name__=='__main__':main()
