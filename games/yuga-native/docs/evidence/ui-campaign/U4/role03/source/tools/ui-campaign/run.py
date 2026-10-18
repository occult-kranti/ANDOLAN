#!/usr/bin/env python3
"""Owned X11 UI input capture. Adapted from visual-rounds/run.py and native-window-review.py.
Only native XTest events drive controls; observer writes readiness/focus and raw PNGs.
"""
import argparse, ctypes as C, ctypes.util, hashlib, json, os, pathlib, shutil, subprocess, time
P=pathlib.Path
PROJECT=P(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(P(p).read_bytes()).hexdigest()
def save(p,v): P(p).write_text(json.dumps(v,indent=2)+'\n')
def read(p):
    try: return json.loads(P(p).read_text())
    except (FileNotFoundError,json.JSONDecodeError): return {}
def wait_for(test, seconds=30):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        result=test()
        if result: return result
        time.sleep(.01)
    raise TimeoutError('Readiness condition not reached')
class NativeInput:
    def __init__(self, display):
        self.x=C.CDLL(ctypes.util.find_library('X11')); self.xt=C.CDLL(ctypes.util.find_library('Xtst'))
        x,xt=self.x,self.xt
        x.XOpenDisplay.argtypes=[C.c_char_p]; x.XOpenDisplay.restype=C.c_void_p
        for name,types,result in [('XDefaultRootWindow',[C.c_void_p],C.c_ulong),('XQueryTree',[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)],C.c_int),('XFetchName',[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)],C.c_int),('XFree',[C.c_void_p],C.c_int),('XSetInputFocus',[C.c_void_p,C.c_ulong,C.c_int,C.c_ulong],C.c_int),('XGetInputFocus',[C.c_void_p,C.POINTER(C.c_ulong),C.POINTER(C.c_int)],C.c_int),('XStringToKeysym',[C.c_char_p],C.c_ulong),('XKeysymToKeycode',[C.c_void_p,C.c_ulong],C.c_uint),('XFlush',[C.c_void_p],C.c_int),('XCloseDisplay',[C.c_void_p],C.c_int)]:
            getattr(x,name).argtypes=types; getattr(x,name).restype=result
        xt.XTestFakeKeyEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
        xt.XTestFakeButtonEvent.argtypes=[C.c_void_p,C.c_uint,C.c_int,C.c_ulong]
        xt.XTestFakeMotionEvent.argtypes=[C.c_void_p,C.c_int,C.c_int,C.c_int,C.c_ulong]
        self.d=wait_for(lambda:x.XOpenDisplay(display.encode()),5)
    def window(self):
        root,parent=C.c_ulong(),C.c_ulong(); children=C.POINTER(C.c_ulong)(); count=C.c_uint()
        self.x.XQueryTree(self.d,self.x.XDefaultRootWindow(self.d),C.byref(root),C.byref(parent),C.byref(children),C.byref(count))
        found=[]
        for i in range(count.value):
            name=C.c_char_p()
            if self.x.XFetchName(self.d,children[i],C.byref(name)) and name.value:
                if name.value.startswith(b'YUGA'): found.append(children[i])
                self.x.XFree(name)
        if children: self.x.XFree(children)
        return found[0] if len(found)==1 else None
    def focus(self):
        target=wait_for(self.window)
        self.x.XSetInputFocus(self.d,target,2,0); self.x.XFlush(self.d)
        actual=C.c_ulong(); revert=C.c_int()
        self.x.XGetInputFocus(self.d,C.byref(actual),C.byref(revert))
        if actual.value!=target: raise RuntimeError('Owned window did not receive X focus')
        return target
    def _inject(self, step, delay=.15, flush=True):
        if 'key' in step:
            code=self.x.XKeysymToKeycode(self.d,self.x.XStringToKeysym(step['key'].encode()))
            if not code: raise ValueError('Unknown keysym')
            for down in [1,0]:
                self.xt.XTestFakeKeyEvent(self.d,code,down,0)
                if flush: self.x.XFlush(self.d)
                if delay: time.sleep(delay)
        else:
            x,y=step['point']; self.xt.XTestFakeMotionEvent(self.d,-1,int(x),int(y),0)
            for down in [1,0]:
                self.xt.XTestFakeButtonEvent(self.d,1,down,0)
                if flush: self.x.XFlush(self.d)
                if delay: time.sleep(delay)
    def event(self, step):
        target=self.focus()
        self._inject(step,0 if step.get('immediate') else .15)
        return target
    def burst(self, events):
        target=self.focus()
        for event in events: self._inject(event,0,False)
        self.x.XFlush(self.d)
        return target

def matches(state, expected):
    for path,value in expected.items():
        current=state
        for key in path.split('.'):
            current=current.get(key) if isinstance(current,dict) else None
        if current!=value: return False
    return bool(state)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=P,required=True); p.add_argument('--project',type=P,default=PROJECT)
    p.add_argument('--mode',choices=['component','boot_recovery','transition_fixture','integrated'],default='component'); p.add_argument('--plan',type=P)
    p.add_argument('--display',type=int,default=176); p.add_argument('--width',type=int,default=1280); p.add_argument('--height',type=int,default=720)
    p.add_argument('--renderer',default='gl_compatibility',choices=['gl_compatibility','forward_plus']); p.add_argument('--dry-run',action='store_true')
    p.add_argument('--runtime',type=P,default=P('/workspace/tooling/native-render/runtime'))
    p.add_argument('--timeout',type=float,default=120,help='Maximum seconds for each observed readiness/capture condition')
    p.add_argument('--render-threads',type=int,choices=[1,2],default=1)
    p.add_argument('--shader-cache-seed',type=P,help='Copy an existing Mesa cache into this run; never mutate the seed')
    a=p.parse_args(); out=a.output.resolve(); source=a.project.resolve()
    if not a.output.is_absolute() or out.exists(): p.error('Use fresh absolute output; failures are preserved')
    if not 90<=a.display<=199 or P(f'/tmp/.X11-unix/X{a.display}').exists(): p.error('Choose unused display90–199')
    if a.mode in ['integrated','transition_fixture'] and not a.plan: p.error('This mode requires an explicit readiness/action plan')
    if a.shader_cache_seed and not a.shader_cache_seed.is_dir(): p.error('Shader cache seed must be an existing directory')
    plan=read(a.plan) if a.plan else [
        {'capture':'01-launch','expect':{'launch.selected_mode':'world'}},
        {'click_name':'TrainingMode','expect':{'launch.selected_mode':'train'},'capture':'02-training-selected'},
        {'key':'Tab','capture':'03-keyboard-focus'},
        {'click_name':'ExploreConfluence','expect':{'transition.phase':'error'},'capture':'04-real-missing-scene-error'},
        {'key':'Return','expect':{'transition.phase':'error','transition.attempt':2},'capture':'05-retry-error'},
        {'key':'Escape','expect':{'transition.phase':'cancelled'},'capture':'06-back-focus'},
    ]
    if a.dry_run: print(json.dumps({'mode':a.mode,'plan':plan,'render_threads':a.render_threads,'shader_cache_seed':str(a.shader_cache_seed) if a.shader_cache_seed else None,'starts_processes':False},indent=2)); return
    out.mkdir(parents=True); project=source
    pins={}
    files=['scripts/launch_shell.gd','scripts/hero_ui_theme.gd','scripts/scene_transition.gd','tools/ui-campaign/board.gd','tools/ui-campaign/observer.gd','tools/ui-campaign/run.py','tests/ui_campaign_flow_cases.gd']
    if a.mode in ['component','boot_recovery','transition_fixture']:
        project=out/'fixture'; project.mkdir()
        if a.mode=='boot_recovery': files += ['scripts/boot.gd','scenes/boot.tscn']
        if a.mode=='transition_fixture': files += ['tools/ui-campaign/transition_board.gd']
        files += [str(path.relative_to(source)) for path in (source/'assets/fonts').glob('*') if path.is_file()]
        files += [str(path.relative_to(source)) for path in (source/'.godot/imported').glob('*.ttf-*') if path.is_file()]
        for file in files:
            dst=project/file; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source/file,dst); pins[file]=sha(dst)
        main='res://scenes/boot.tscn' if a.mode=='boot_recovery' else ('res://scenes/courtyard.tscn' if a.mode=='transition_fixture' else '')
        (project/'project.godot').write_text('[application]\nconfig/name="YUGA UI component fixture"\n'+('run/main_scene="'+main+'"\n' if main else '')+'[display]\nwindow/size/viewport_width='+str(a.width)+'\nwindow/size/viewport_height='+str(a.height)+'\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        pins['project.godot']=sha(project/'project.godot')
        if a.mode=='transition_fixture':
            (project/'scenes').mkdir(exist_ok=True)
            for scene,label in [('courtyard','Sample A'),('confluence_world','Sample B')]:
                file='scenes/'+scene+'.tscn'
                (project/file).write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://tools/ui-campaign/transition_board.gd" id="1"]\n[node name="TransitionSample" type="Control"]\nscript = ExtResource("1")\npage_title = "'+label+'"\n')
                pins[file]=sha(project/file)
    else:
        for directory in ['scripts','scenes','shaders','assets','NOTICE']:
            for file in (source/directory).rglob('*'):
                if file.is_file(): pins[str(file.relative_to(source))]=sha(file)
        pins['project.godot']=sha(source/'project.godot')
        pins['export_presets.cfg']=sha(source/'export_presets.cfg')
        if (source/'art/world/confluence-map.json').is_file():
            pins['art/world/confluence-map.json']=sha(source/'art/world/confluence-map.json')
        for file in files:
            pins[file]=sha(source/file)
    env=os.environ.copy(); runtime=a.runtime
    env.update(DISPLAY=f':{a.display}',LP_NUM_THREADS=str(a.render_threads),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu'))
    for key,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        path=out/'user'/folder; path.mkdir(parents=True); env[key]=str(path)
    env['MESA_SHADER_CACHE_DIR']=str(out/'user/cache/mesa')
    seed_pins={}
    if a.shader_cache_seed:
        a.shader_cache_seed=a.shader_cache_seed.resolve()
        seed_pins={str(f.relative_to(a.shader_cache_seed)):sha(f) for f in a.shader_cache_seed.rglob('*') if f.is_file()}
        if not seed_pins: raise ValueError('Shader cache seed contains no files')
        shutil.copytree(a.shader_cache_seed,env['MESA_SHADER_CACHE_DIR'])
        if any(sha(P(env['MESA_SHADER_CACHE_DIR'])/f)!=h for f,h in seed_pins.items()): raise RuntimeError('Shader cache copy differs')
    command=[shutil.which('godot'),'--path',str(project),'--display-driver','x11','--rendering-method',a.renderer,'--audio-driver','Dummy','--resolution',f'{a.width}x{a.height}','--position','0,0','--max-fps','20','--max-threads',str(a.render_threads),'--script','res://tools/ui-campaign/observer.gd','--','--mode='+a.mode,'--output='+str(out)]
    record={'complete':False,'scope':'Actual XTest input and raw framebuffer; component fixture is not integrated gameplay.','mode':a.mode,'command':command,'source_sha256':pins,'plan':plan,'plan_sha256':sha(a.plan) if a.plan else None,'events':[],'shots':[],'started_unix':time.time(),'renderer_requested':a.renderer,'engine_sha256':sha(command[0])}
    record['scheduling']={'cpu_affinity':sorted(os.sched_getaffinity(0)),'render_threads':a.render_threads,'LP_NUM_THREADS':env['LP_NUM_THREADS'],'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    record['shader_cache_seed']={'path':str(a.shader_cache_seed) if a.shader_cache_seed else None,'copied_to':env['MESA_SHADER_CACHE_DIR'],'files_sha256':seed_pins,'scope':'Copied warm Mesa cache; no cold-start or hardware-performance claim.' if seed_pins else 'No Mesa cache seed supplied.'}
    def resolve_event(step,state):
        event=dict(step)
        if 'key' not in step:
            field='name' if 'click_name' in step else 'text'; value=step.get('click_name',step.get('click_text'))
            controls=[c for c in state['controls'] if c[field]==value and c.get('interactive',not c['disabled'])]
            if len(controls)!=1: raise RuntimeError(f'Expected unique enabled control {value}: {controls}')
            x,y,w,h=controls[0].get('input_rect',controls[0]['rect']); event['point']=[x+w/2,y+h/2]
            if not 0<=event['point'][0]<a.width or not 0<=event['point'][1]<a.height: raise RuntimeError('Control outside viewport; scroll with actual input first')
        return event
    server=game=native=None
    try:
        with (out/'xvfb.log').open('w') as xl,(out/'godot.log').open('w') as gl:
            server=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),env['DISPLAY'],'-screen','0',f'{a.width}x{a.height}x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT)
            wait_for(lambda:P(f'/tmp/.X11-unix/X{a.display}').exists(),5)
            game=subprocess.Popen(command,env=env,stdout=gl,stderr=subprocess.STDOUT)
            native=NativeInput(env['DISPLAY']); native.focus()
            for index,step in enumerate(plan):
                state=wait_for(lambda:read(out/'state.json'),a.timeout)
                if 'burst' in step:
                    events=[resolve_event(event,state) for event in step['burst']]
                    window_id=native.burst(events)
                    record['events'].append({'burst':events,'window_id':window_id,'before':state,'time_unix':time.time()})
                if 'tab_to_text' in step:
                    for tab_index in range(40):
                        if state.get('focus_text')==step['tab_to_text']: break
                        before=state
                        window_id=native.event({'key':'Tab'})
                        record['events'].append({'key':'Tab','window_id':window_id,'before':before,'time_unix':time.time(),'purpose':'Reach '+step['tab_to_text']})
                        state=wait_for(lambda:s if (s:=read(out/'state.json')).get('frame',-1)>before.get('frame',-1) else None,a.timeout)
                    else: raise RuntimeError('Tab chain did not reach '+step['tab_to_text'])
                if 'key' in step or 'click_name' in step or 'click_text' in step:
                    event=resolve_event(step,state)
                    repeat=int(step.get('repeat',1))
                    if not 1<=repeat<=40: raise ValueError('Input repetition must be 1–40')
                    for _ in range(repeat): event['window_id']=native.event(event)
                    event['before']=state; event['time_unix']=time.time(); record['events'].append(event)
                if 'expect_exit' in step:
                    wait_for(lambda:game.poll() is not None,a.timeout)
                    if game.returncode!=step['expect_exit']: raise RuntimeError('Unexpected native exit code '+str(game.returncode))
                    record['verified_exit_code']=game.returncode
                    save(out/'run.json',record)
                    continue
                expected=step.get('expect',{})
                state=wait_for(lambda:s if matches(s:=read(out/'state.json'),expected) else None,a.timeout)
                if 'capture' in step:
                    name=step['capture']; save(out/'capture-request.json',{'name':name})
                    shot=wait_for(lambda:read(out/(name+'.json')),a.timeout)
                    if sha(out/shot['file'])!=shot['sha256']: raise RuntimeError('PNG hash differs')
                    record['shots'].append(shot)
                save(out/'run.json',record)
            record['automatic_shots']=[read(file) for file in sorted(out.glob('auto-*.json'))]
            record['source_unchanged']=all(sha(project/f)==h for f,h in pins.items())
            if not record['source_unchanged']: raise RuntimeError('Source changed during capture')
            record['shader_cache_seed_unchanged']=not seed_pins or seed_pins=={str(f.relative_to(a.shader_cache_seed)):sha(f) for f in a.shader_cache_seed.rglob('*') if f.is_file()}
            if not record['shader_cache_seed_unchanged']: raise RuntimeError('Source shader cache changed during capture')
            record['complete']=True
    except Exception as error:
        record['failure']=repr(error)
        raise
    finally:
        if game and game.poll() is None:
            game.terminate()
            try: game.wait(timeout=5)
            except subprocess.TimeoutExpired: game.kill(); game.wait()
        if native: native.x.XCloseDisplay(native.d)
        if server:
            server.terminate(); server.wait(timeout=5)
        record['finished_unix']=time.time(); record['cleanup_exit']=game.returncode if game else None
        record['logs']={f:sha(out/f) for f in ['godot.log','xvfb.log'] if (out/f).exists()}
        save(out/'run.json',record)
    log=(out/'godot.log').read_text()
    if 'SCRIPT ERROR:' in log or '\nERROR:' in log: raise RuntimeError('Engine error; review preserved godot.log')
    print(json.dumps({'complete':record['complete'],'shots':len(record['shots']),'output':str(out)},indent=2))
if __name__=='__main__': main()
