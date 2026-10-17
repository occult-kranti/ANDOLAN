#!/usr/bin/env python3
"""Owned-display actual motion render. Call only when assigned the renderer slot."""
import argparse, json, os, pathlib, shutil, subprocess, time
NATIVE=pathlib.Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(); p.add_argument('--output',type=pathlib.Path,required=True); p.add_argument('--display',type=int,default=145); p.add_argument('--asset',default='res://assets/heroes/rama-hero.glb'); p.add_argument('--full',action='store_true'); p.add_argument('--side',action='store_true'); p.add_argument('--shader-cache',type=pathlib.Path); a=p.parse_args()
 assert a.output.is_absolute() and not a.output.exists() and 90<=a.display<=199
 runtime=pathlib.Path('/workspace/tooling/native-render/runtime'); env=os.environ.copy()
 env.update(DISPLAY=f':{a.display}',LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu'),VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),LP_NUM_THREADS='2',XDG_DATA_HOME=str(a.output)+'-user/data',XDG_CONFIG_HOME=str(a.output)+'-user/config',XDG_CACHE_HOME=str(a.output)+'-user/cache')
 assert not pathlib.Path(f'/tmp/.X11-unix/X{a.display}').exists()
 for key in ['XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME']: pathlib.Path(env[key]).mkdir(parents=True,exist_ok=False)
 if a.shader_cache:
  for name in ['mesa_shader_cache','mesa_shader_cache_db']:
   source=a.shader_cache/name
   if source.is_dir(): shutil.copytree(source,pathlib.Path(env['XDG_CACHE_HOME'])/name)
 with open(str(a.output)+'.xvfb.log','x') as xl,open(str(a.output)+'.godot.log','x') as gl:
  server=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),env['DISPLAY'],'-screen','0','640x640x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT)
  try:
   for _ in range(50):
    if pathlib.Path(f'/tmp/.X11-unix/X{a.display}').exists(): break
    if server.poll() is not None: raise RuntimeError('Display stopped')
    time.sleep(.1)
   cmd=[shutil.which('godot'),'--path',str(NATIVE),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--script','res://art/hero-rama-motion/capture_motion.gd','--','--output='+str(a.output),'--asset='+a.asset]
   if a.full: cmd.append('--full')
   if a.side: cmd.append('--side')
   result=subprocess.run(cmd,env=env,stdout=gl,stderr=subprocess.STDOUT,timeout=660)
  finally:
   server.terminate()
   try: server.wait(timeout=5)
   except subprocess.TimeoutExpired: server.kill(); server.wait()
 assert result.returncode==0, str(a.output)+'.godot.log'
 report=json.loads((a.output/'motion-capture.json').read_text()); assert report['complete'] and report['frames']
 import hashlib
 snapshots=a.output/'sources'; snapshots.mkdir()
 for relative,digest in report['sources'].items():
  source=NATIVE/relative.removeprefix('res://')
  assert hashlib.sha256(source.read_bytes()).hexdigest()==digest, relative
  if source.suffix in ['.gd','.tres']:
   destination=snapshots/relative.removeprefix('res://'); destination.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,destination)
 previous=-1
 for frame in report['frames']:
  assert frame['rendered_frame_counter']>previous; previous=frame['rendered_frame_counter']
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-framerate','24','-i',str(a.output/'frame-%05d.png'),'-an','-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p',str(a.output/'rama-motion.mp4')],check=True)
 print(json.dumps({'complete':True,'frames':len(report['frames']),'output':str(a.output)}))
if __name__=='__main__': main()
