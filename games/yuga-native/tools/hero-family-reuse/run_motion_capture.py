"""Owned display runner reusing native traversal image-verification helpers."""
import argparse,importlib.util,json,os,shutil,subprocess,time
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('existing_native_capture',PROJECT/'tools/run-traversal-capture.py');helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--display',type=int,default=165);p.add_argument('--preview',action='store_true');p.add_argument('--verify-existing',action='store_true',help='Validate retained actual frames/video without launching a renderer or rewriting images');p.add_argument('--shader-cache-seed',type=Path);p.add_argument('--runtime',type=Path,default=Path('/workspace/scratch/ten-rounds-oct23/runtime/runtime'));p.add_argument('--godot',type=Path,default=Path('/workspace/scratch/ten-rounds-oct23/runtime-release/restored/godot'));a=p.parse_args();out=a.output.resolve();user=out.with_name(out.name+'-user')
 if not a.verify_existing and (out.exists() or user.exists() or not 90<=a.display<=199 or Path(f'/tmp/.X11-unix/X{a.display}').exists()):raise ValueError('Use fresh output/user paths and unowned display')
 if a.verify_existing and (not (out/'capture.json').is_file() or (out/'capture-run.json').exists()):raise ValueError('Use retained capture with no existing final receipt')
 out.parent.mkdir(parents=True,exist_ok=True);runtime=a.runtime.resolve()
 if not (runtime/'usr/bin/Xvfb').is_file() or not (runtime/'usr/share/vulkan/icd.d/lvp_icd.json').is_file() or not a.godot.is_file():raise FileNotFoundError('Supply verified native runtime/Xvfb/ICD/Godot paths')
 env=os.environ.copy();env.update(DISPLAY=f':{a.display}',LP_NUM_THREADS='2',LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu'),VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'))
 for key,child in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
  directory=user/child
  if not a.verify_existing:directory.mkdir(parents=True,exist_ok=False)
  env[key]=str(directory)
 env['MESA_SHADER_CACHE_DIR']=str(user/'cache/mesa')
 if a.shader_cache_seed and not a.verify_existing:shutil.copytree(a.shader_cache_seed,env['MESA_SHADER_CACHE_DIR'])
 command=[str(a.godot.resolve()),'--path',str(PROJECT),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--fixed-fps','30','--script','res://tools/hero-family-reuse/capture_warm_entry.gd','--','--output='+str(out),'--frames='+('8' if a.preview else '36')]
 if not a.verify_existing:
  with out.with_suffix('.xvfb.log').open('x') as xl,out.with_suffix('.godot.log').open('x') as gl:
   display=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),env['DISPLAY'],'-screen','0','1024x640x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT)
   try:
    for _ in range(50):
     if display.poll() is not None:raise RuntimeError('Owned display stopped')
     if Path(f'/tmp/.X11-unix/X{a.display}').exists():break
     time.sleep(.1)
    else:raise RuntimeError('Owned display did not start')
    result=subprocess.run(command,env=env,stdout=gl,stderr=subprocess.STDOUT,timeout=360)
   finally:
    display.terminate()
    try:display.wait(timeout=5)
    except subprocess.TimeoutExpired:display.kill();display.wait()
  if result.returncode!=0:raise RuntimeError('Capture failed; preserve Godot log')
 log=out.with_suffix('.godot.log').read_text()
 if 'SCRIPT ERROR:' in log or '\nERROR:' in log:raise RuntimeError('Capture errors; preserve log')
 report=json.loads((out/'capture.json').read_text());expected=8 if a.preview else 36
 if len(report['frames'])!=expected or not report['sources_unchanged'] or not report['automatic_modifiers_disabled'] or report['renderer']!='forward_plus' or report['display']=='headless':raise ValueError('Actual renderer/source contract failed')
 previous_draw=None
 for index,frame in enumerate(report['frames']):
  if frame['index']!=index or frame['manual_pose_updates']!=2 or not all(actor['finite'] for actor in frame['actors']):raise ValueError('Advancing pose contract failed')
  if previous_draw is not None and frame['render_frame']<=previous_draw:raise ValueError('Render frame did not advance')
  helpers.verify_image(out,frame['image'],(1024,640));previous_draw=frame['render_frame']
 for path,digest in report['sources'].items():
  if helpers.sha256(PROJECT/path.removeprefix('res://'))!=digest:raise ValueError('Source changed: '+path)
 video=None
 if not a.preview:
  video=out/'warm-entry-comparison.mp4'
  if not a.verify_existing:subprocess.run([shutil.which('ffmpeg'),'-hide_banner','-loglevel','error','-nostdin','-n','-framerate','30','-i',str(out/'frame-%05d.png'),'-an','-c:v','libx264','-threads','2','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True,timeout=90)
  probe=json.loads(subprocess.check_output([shutil.which('ffprobe'),'-v','error','-count_frames','-show_streams','-of','json',str(video)]));assert int(probe['streams'][0]['nb_read_frames'])==36
 receipt={'schema_version':1,'passed':True,'command':command,'frames':expected,'preview':a.preview,'verified_existing_capture':a.verify_existing,'renderer_launched_by_this_verification':not a.verify_existing,'report_sha256':helpers.sha256(out/'capture.json'),'runner_sha256':helpers.sha256(Path(__file__)),'reused_helpers_sha256':helpers.sha256(PROJECT/'tools/run-traversal-capture.py'),'godot_sha256':helpers.sha256(a.godot),'runtime':str(runtime),'icd_sha256':helpers.sha256(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),'video':str(video) if video else None,'video_sha256':helpers.sha256(video) if video else None,'scope':'Actual isolated native contact comparison; software Vulkan, no physicalGPU/human-feel or newhero acceptance.'};(out/'capture-run.json').write_text(json.dumps(receipt,indent=2)+'\n');print('WARM_ENTRY_CAPTURE_VERIFIED',json.dumps(receipt))
if __name__=='__main__':main()
