#!/usr/bin/env python3
"""Run the single R4 tape in a fresh isolated native window and retain raw images."""
import argparse,hashlib,json,os,shutil,subprocess,time
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--display',type=int,default=168);p.add_argument('--shader-cache-seed',type=Path,required=True);p.add_argument('--preflight',action='store_true');a=p.parse_args()
 project=a.project.resolve();out=a.output;runtime=Path('/workspace/tooling/native-render/runtime');user=out.with_name(out.name+'-user');log=out.with_suffix('.godot.log');xlog=out.with_suffix('.xvfb.log')
 assert out.is_absolute() and not any(os.path.lexists(x) for x in [out,user,log,xlog]);assert not Path(f'/tmp/.X11-unix/X{a.display}').exists()
 out.parent.mkdir(parents=True,exist_ok=True);user.mkdir();env=os.environ.copy();env.update(LP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 for key,name in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
  path=user/name;path.mkdir();env[key]=str(path)
 env['MESA_SHADER_CACHE_DIR']=str(user/'cache/mesa');shutil.copytree(a.shader_cache_seed,env['MESA_SHADER_CACHE_DIR'])
 command=['godot','--path',str(project),'--audio-driver','Dummy','--disable-vsync','--fixed-fps','30','--max-threads','2','--script','res://tools/visual-rounds/capture_motion.gd','--','--output='+str(out)]
 server=None
 if a.preflight:command.insert(1,'--headless');command.append('--preflight')
 else:
  command[1:1]=['--display-driver','x11','--rendering-method','forward_plus'];env.update(DISPLAY=f':{a.display}',VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else ''))
 started=time.monotonic()
 with log.open('x') as stdout,xlog.open('x') as xs:
  try:
   if not a.preflight:
    server=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),env['DISPLAY'],'-screen','0','1280x960x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xs,stderr=subprocess.STDOUT)
    for _ in range(50):
     if server.poll() is not None:raise RuntimeError('Owned Xvfb stopped')
     if Path(f'/tmp/.X11-unix/X{a.display}').exists():break
     time.sleep(.1)
    else:raise RuntimeError('Owned Xvfb did not start')
   result=subprocess.run(command,env=env,stdout=stdout,stderr=subprocess.STDOUT,timeout=1800 if not a.preflight else 240)
  finally:
   if server:
    server.terminate()
    try:server.wait(timeout=5)
    except subprocess.TimeoutExpired:server.kill();server.wait()
 text=log.read_text();assert result.returncode==0 and 'SCRIPT ERROR:' not in text and '\nERROR:' not in text,text[-4000:]
 reportpath=out/('preflight.json' if a.preflight else 'capture.json');report=json.loads(reportpath.read_text());assert report['complete'],report['checks']
 for name,pin in report['source_sha256'].items():assert sha(project/name.removeprefix('res://'))==pin,name
 shots=report['shots'];assert len(shots)==210
 assert all(b['physics_frame']-a['physics_frame']==2 for a,b in zip(shots,shots[1:]))
 if not a.preflight:
  assert all(b['render_frame']-a['render_frame']==1 for a,b in zip(shots,shots[1:]))
  for shot in shots:assert sha(out/shot['file'])==shot['sha256']
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-framerate','30','-i',str(out/'frame-%03d.png'),'-an','-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p',str(out/'continuity.mp4')],check=True)
 receipt={'complete':True,'godot_exit_code':result.returncode,'command':command,'raw_pngs':0 if a.preflight else len(shots),'report_sha256':sha(reportpath),'godot_log_sha256':sha(log),'xvfb_log_sha256':sha(xlog),'runner_sha256':sha(__file__),'source_pins':len(report['source_sha256']),'cpu_affinity':sorted(os.sched_getaffinity(0)),'llvmpipe_threads':env['LP_NUM_THREADS'],'warnings':[line for line in text.splitlines() if 'WARNING:' in line],'elapsed_wall_s':time.monotonic()-started,'scope':report['scope']}
 (out/'run.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
