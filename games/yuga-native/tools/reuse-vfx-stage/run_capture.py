#!/usr/bin/env python3
"""Own one short Xvfb/Godot software capture and clean up only its child processes.

Uses the runtime and ownership pattern of tools/run-traversal-capture.py.
No system package installs, credential inspection, canonical imports or remote GPU.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, time

def stop(child):
 if child is not None and child.poll() is None:
  child.terminate()
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--display',type=int,default=153);p.add_argument('--timeout',type=int,default=300);p.add_argument('--godot',type=Path,default=Path(shutil.which('godot') or '/usr/local/bin/godot'));p.add_argument('--controls-only',action='store_true');a=p.parse_args()
 project=a.project.resolve();runtime=a.runtime.resolve();output=a.output.resolve()
 repository=Path(__file__).resolve().parents[4]
 if project.is_relative_to(repository) or output.is_relative_to(repository):raise ValueError('Keep prepared project and capture output outside canonical checkout')
 if not 90<=a.display<=199:raise ValueError('Owned display must be in90..199')
 if output.exists():raise ValueError('Use fresh output directory')
 if not (project/'source-manifest.json').is_file():raise ValueError('Use isolated prepared source project')
 socket=Path('/tmp/.X11-unix')/f'X{a.display}'
 if socket.exists() or Path(f'/tmp/.X{a.display}-lock').exists():raise ValueError('Display already owned; choose another')
 xvfb=runtime/'usr/bin/Xvfb';icd=runtime/'usr/share/vulkan/icd.d/lvp_icd.json'
 if not xvfb.is_file() or not icd.is_file():raise ValueError('Verified extracted shared runtime required')
 env=os.environ.copy();env['DISPLAY']=f':{a.display}';env['VK_ICD_FILENAMES']=str(icd);env['LP_NUM_THREADS']='2'
 env['LD_LIBRARY_PATH']=str(runtime/'usr/lib/x86_64-linux-gnu')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 output.mkdir(parents=True);display_child=None;render_child=None
 for name,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
  path=output/'session-user'/folder;path.mkdir(parents=True);env[name]=str(path)
 env['MESA_SHADER_CACHE_DIR']=str(output/'session-user/cache/mesa')
 command=[str(a.godot.resolve()),'--path',str(project),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--script','res://preview.gd','--','--output='+str(output)]
 if a.controls_only:command.append('--controls-only')
 started=time.monotonic()
 try:
  with (output/'display.log').open('w') as display_log,(output/'render.log').open('w') as render_log:
   display_child=subprocess.Popen([str(xvfb),f':{a.display}','-screen','0','960x640x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=display_log,stderr=subprocess.STDOUT)
   for _ in range(80):
    if display_child.poll() is not None:raise RuntimeError('Owned Xvfb failed')
    if socket.exists():break
    time.sleep(.1)
   else:raise RuntimeError('Owned Xvfb never created socket')
   render_child=subprocess.Popen(command,env=env,stdout=render_log,stderr=subprocess.STDOUT)
   exit_code=render_child.wait(timeout=a.timeout)
   if exit_code:raise RuntimeError(f'Godot capture failed with exit{exit_code}; read render.log')
  log=(output/'render.log').read_text()
  if 'SCRIPT ERROR:' in log or '\nERROR:' in log:raise RuntimeError('Godot emitted errors; read render.log')
  capture=json.loads((output/'capture.json').read_text())
  expected_frames=0 if a.controls_only else 72
  if not capture.get('passed') or capture.get('renderer')!='forward_plus' or capture.get('frames')!=expected_frames:raise RuntimeError('Capture contract failed')
  files=[]
  for image in sorted(output.glob('*.png')):
   files.append({'file':image.name,'bytes':image.stat().st_size,'sha256':hashlib.sha256(image.read_bytes()).hexdigest()})
  if len(files)!=expected_frames+3:raise RuntimeError('Expected advancing frame count plus3 matched control frames')
  result={'passed':True,'command':command,'engine_sha256':hashlib.sha256(a.godot.resolve().read_bytes()).hexdigest(),'runtime':str(runtime),'renderer':capture['renderer'],'adapter':capture['adapter'],'wall_seconds':round(time.monotonic()-started,3),'wall_seconds_are_not_render_fps':True,'frame_files':files,'source_manifest':json.loads((project/'source-manifest.json').read_text()),'scope':'Owned Xvfb + Mesa lavapipe software-rendered frames. No physical GPU or gameplay authority.'}
  (output/'runner-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'output':str(output),'frames':len(files),'renderer':capture['renderer'],'adapter':capture['adapter']}))
 finally:stop(render_child);stop(display_child)
if __name__=='__main__':main()
