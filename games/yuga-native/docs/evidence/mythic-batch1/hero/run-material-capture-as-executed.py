import hashlib,importlib.util,json,os,pathlib,shutil,subprocess,time
project=pathlib.Path('/workspace/ANDOLAN/games/yuga-native')
output=pathlib.Path('/workspace/scratch/yuga-hero-reconstruction-r2/render-r1')
user=output.with_name(output.name+'-user'); logpath=output.with_name(output.name+'.godot.log');xlogpath=output.with_name(output.name+'.xvfb.log')
assert not any(p.exists() for p in [output,user,logpath,xlogpath,pathlib.Path('/tmp/.X11-unix/X120')])
spec=importlib.util.spec_from_file_location('capture_helpers',project/'tools/run-traversal-capture.py');helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
runtime=pathlib.Path('/workspace/tooling/native-render/runtime');env=os.environ.copy();env.update(DISPLAY=':120',LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else ''),VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),LP_NUM_THREADS='2')
for key,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:env[key]=str(user/folder);(user/folder).mkdir(parents=True)
env['MESA_SHADER_CACHE_DIR']=str(user/'cache/mesa');seed=helpers.seed_shader_cache(pathlib.Path('/workspace/scratch/yuga-motion-next/render-r3-user/cache/mesa'),user/'cache/mesa')
command=[shutil.which('godot'),'--path',str(project),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--script','res://tools/capture-hero-next.gd','--','--output='+str(output),'--width=960','--height=960','--timeout=240']
with logpath.open('x') as log,xlogpath.open('x') as xlog:
 server=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),':120','-screen','0','960x960x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xlog,stderr=subprocess.STDOUT)
 try:
  for _ in range(50):
   if server.poll() is not None:raise RuntimeError('Owned display exited')
   if pathlib.Path('/tmp/.X11-unix/X120').exists():break
   time.sleep(.1)
  else:raise RuntimeError('Owned display not ready')
  result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=280)
 finally:
  server.terminate()
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:server.kill();server.wait()
text=logpath.read_text();assert result.returncode==0 and 'SCRIPT ERROR:' not in text and '\nERROR:' not in text,text[-1500:]
report=json.loads((output/'hero-render-review.json').read_text());assert report['complete'] and not report['failure'] and report['expected_shot_count']==report['actual_shot_count']==5
assert report['renderer']=='forward_plus' and report['display_server'].lower()=='x11'
assert report['asset_sha256_before']==report['asset_sha256_after']==helpers.sha256(project/'assets/heroes/rama-production.glb')=='3424d72e74bb425c7e6bb2ff2fddc05c792657c437a888c56671fbd7d3ec3bcc'
assert report['capture_script_sha256']==helpers.sha256(project/'tools/capture-hero-next.gd')
for shot in report['shots']:
 helpers.verify_image(output,shot,(960,960));assert shot['bone_transforms_sampled_finite']==164 and shot['rendered_frame_counter_after']>shot['rendered_frame_counter_before']
record={'complete':True,'command':command,'shader_cache_seed':seed,'source_report_sha256':helpers.sha256(output/'hero-render-review.json'),'scope':'Five actual staged material stills; no gameplay, animation continuity, audio or hardware-performance acceptance.'}
(output/'capture-run.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'complete':True,'views':5,'output':str(output),'asset_sha256':report['asset_sha256_after']}))
