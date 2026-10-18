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
        if 'wheel' in step:
            x,y=step['point']; self.xt.XTestFakeMotionEvent(self.d,-1,int(x),int(y),0)
            button=4 if step['wheel']>0 else 5
            for _ in range(abs(step['wheel'])):
                for down in [1,0]: self.xt.XTestFakeButtonEvent(self.d,button,down,0)
                if flush: self.x.XFlush(self.d)
                if delay: time.sleep(delay)
        elif any(key in step for key in ['key','key_down','key_up']):
            key_name=step.get('key',step.get('key_down',step.get('key_up')))
            code=self.x.XKeysymToKeycode(self.d,self.x.XStringToKeysym(key_name.encode()))
            if not code: raise ValueError('Unknown keysym')
            edges=[1] if 'key_down' in step else ([0] if 'key_up' in step else [1,0])
            for down in edges:
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
        for event in events:
            self._inject(event,0,False)
            if event.get('after_ms'):
                self.x.XFlush(self.d); time.sleep(float(event['after_ms'])/1000)
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
    p.add_argument('--mode',choices=['component','boot_recovery','transition_fixture','integrated','package'],default='component'); p.add_argument('--plan',type=P)
    p.add_argument('--display',type=int,default=176); p.add_argument('--width',type=int,default=1280); p.add_argument('--height',type=int,default=720)
    p.add_argument('--renderer',default='gl_compatibility',choices=['gl_compatibility','forward_plus']); p.add_argument('--dry-run',action='store_true')
    p.add_argument('--runtime',type=P,default=P('/workspace/tooling/native-render/runtime'))
    p.add_argument('--timeout',type=float,default=120,help='Maximum seconds for each observed readiness/capture condition')
    p.add_argument('--render-threads',type=int,choices=[1,2],default=1)
    p.add_argument('--shader-cache-seed',type=P,help='Copy an existing Mesa cache into this run; never mutate the seed')
    p.add_argument('--executable',type=P,help='Exact extracted package executable; required in package mode')
    p.add_argument('--export-manifest',type=P,help='Authoritative exported runtime source file pins')
    p.add_argument('--package-archive',type=P,help='Original ZIP identity retained alongside extracted payload pins')
    p.add_argument('--package',type=P,help='Exact extracted PCK; required in package mode')
    p.add_argument('--user-state',type=P,help='Explicit isolated XDG root reused across package processes')
    p.add_argument('--allow-authority-staging',action='store_true',help='Explicit fixture: allow labeled actual-rule staging in integrated/package mode')
    a=p.parse_args(); out=a.output.resolve(); source=a.project.resolve()
    if not a.output.is_absolute() or out.exists(): p.error('Use fresh absolute output; failures are preserved')
    if not 90<=a.display<=199 or P(f'/tmp/.X11-unix/X{a.display}').exists(): p.error('Choose unused display90–199')
    if a.mode in ['integrated','transition_fixture','package'] and not a.plan: p.error('This mode requires an explicit readiness/action plan')
    if a.mode=='package' and (not a.executable or not a.package or not a.executable.is_file() or not a.package.is_file()): p.error('Package mode requires existing executable and PCK')
    if a.user_state and (a.mode!='package' or not a.user_state.is_absolute()): p.error('Shared isolated user state requires package mode and absolute path')
    if a.shader_cache_seed and not a.shader_cache_seed.is_dir(): p.error('Shader cache seed must be an existing directory')
    plan=read(a.plan) if a.plan else [
        {'capture':'01-launch','expect':{'launch.selected_mode':'world'}},
        {'click_name':'TrainingMode','expect':{'launch.selected_mode':'train'},'capture':'02-training-selected'},
        {'key':'Tab','capture':'03-keyboard-focus'},
        {'click_name':'ExploreConfluence','expect':{'transition.phase':'error'},'capture':'04-real-missing-scene-error'},
        {'key':'Return','expect':{'transition.phase':'error','transition.attempt':2},'capture':'05-retry-error'},
        {'key':'Escape','expect':{'transition.phase':'cancelled'},'capture':'06-back-focus'},
    ]
    if any('stage' in step for step in plan) and (a.mode not in ['integrated','package'] or not a.allow_authority_staging): p.error('Stage steps require integrated mode and explicit --allow-authority-staging')
    if a.allow_authority_staging and a.mode not in ['integrated','package']: p.error('Authority staging is only available in integrated or package mode')
    if a.dry_run: print(json.dumps({'mode':a.mode,'plan':plan,'render_threads':a.render_threads,'shader_cache_seed':str(a.shader_cache_seed) if a.shader_cache_seed else None,'starts_processes':False},indent=2)); return
    out.mkdir(parents=True); project=source
    pins={}
    files=['scripts/launch_shell.gd','scripts/hero_ui_theme.gd','scripts/scene_transition.gd','tools/ui-campaign/board.gd','tools/ui-campaign/observer.gd','tools/ui-campaign/run.py','tests/ui_campaign_flow_cases.gd']
    if a.allow_authority_staging: files += ['tools/ui-campaign/integrated_capture.gd','tools/ui-campaign/authority_stage.gd']
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
            if a.mode!='package': pins[file]=sha(source/file)
    export_record=read(a.export_manifest) if a.export_manifest else {}
    if a.mode=='package':
        if not export_record.get('source',{}).get('files'): raise ValueError('Package execution requires authoritative export manifest')
        pins={name:item['sha256'] for name,item in export_record['source']['files'].items()}
        if not all((source/name).is_file() and sha(source/name)==checksum for name,checksum in pins.items()): raise RuntimeError('Runtime source differs from exported manifest')
    env=os.environ.copy(); runtime=a.runtime
    env.update(DISPLAY=f':{a.display}',LP_NUM_THREADS=str(a.render_threads),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu'))
    for key,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        path=(a.user_state or out/'user')/folder; path.mkdir(parents=True,exist_ok=True); env[key]=str(path)
    env['MESA_SHADER_CACHE_DIR']=str((a.user_state or out/'user')/'cache/mesa')
    prior_cache_pins={str(f.relative_to(P(env['MESA_SHADER_CACHE_DIR']))):sha(f) for f in P(env['MESA_SHADER_CACHE_DIR']).rglob('*') if f.is_file()}
    seed_pins={}
    if a.shader_cache_seed:
        a.shader_cache_seed=a.shader_cache_seed.resolve()
        seed_pins={str(f.relative_to(a.shader_cache_seed)):sha(f) for f in a.shader_cache_seed.rglob('*') if f.is_file()}
        if not seed_pins: raise ValueError('Shader cache seed contains no files')
        shutil.copytree(a.shader_cache_seed,env['MESA_SHADER_CACHE_DIR'])
        if any(sha(P(env['MESA_SHADER_CACHE_DIR'])/f)!=h for f,h in seed_pins.items()): raise RuntimeError('Shader cache copy differs')
    package_pins={}
    instrumentation={}
    if a.mode=='package':
        for file in [a.executable.resolve(),a.package.resolve()]: package_pins[str(file)]=sha(file)
        external=out/'observer.gd'; shutil.copy2(PROJECT/'tools/ui-campaign/observer.gd',external)
        instrumentation={str(external):sha(external),str(P(__file__).resolve()):sha(P(__file__).resolve())}
        if a.allow_authority_staging:
            authority=out/'authority_stage.gd'; shutil.copy2(PROJECT/'tools/ui-campaign/authority_stage.gd',authority)
            bridge_source=PROJECT/'tools/ui-campaign/integrated_capture.gd'
            bridge=out/'integrated_capture.gd'
            bridge.write_text(bridge_source.read_text().replace('res://tools/ui-campaign/observer.gd',str(external)).replace('res://tools/ui-campaign/authority_stage.gd',str(authority)))
            instrumentation.update({str(authority):sha(authority),str(bridge):sha(bridge),str(bridge_source):sha(bridge_source)})
            external=bridge
    driver='res://tools/ui-campaign/integrated_capture.gd' if a.allow_authority_staging else 'res://tools/ui-campaign/observer.gd'
    prefix=[str(a.executable.resolve()),'--main-pack',str(a.package.resolve())] if a.mode=='package' else [shutil.which('godot'),'--path',str(project)]
    if a.mode=='package': driver=str(external)
    command=prefix+['--display-driver','x11','--rendering-method',a.renderer,'--audio-driver','Dummy','--resolution',f'{a.width}x{a.height}','--position','0,0','--max-fps','20','--max-threads',str(a.render_threads),'--script',driver,'--','--mode='+a.mode,'--output='+str(out)]
    record={'complete':False,'scope':('Actual extracted Linux package, external observer, native XTest and raw framebuffer.' if a.mode=='package' else 'Actual XTest input and raw framebuffer; component fixture is not integrated gameplay.'),'mode':a.mode,'command':command,'source_sha256':pins,'plan':plan,'plan_sha256':sha(a.plan) if a.plan else None,'events':[],'shots':[],'started_unix':time.time(),'renderer_requested':a.renderer,'engine_sha256':sha(command[0])}
    def config_receipt():
        return {str(file.relative_to(a.user_state or out/'user')):{'sha256':sha(file),'text':file.read_text()} for file in (a.user_state or out/'user').rglob('courtyard-settings.cfg')}
    record['package_sha256']=package_pins
    record['export_manifest']={'path':str(a.export_manifest),'sha256':sha(a.export_manifest),'source':export_record.get('source'),'git':export_record.get('git')} if a.export_manifest else None
    record['package_archive']={'path':str(a.package_archive),'sha256':sha(a.package_archive)} if a.package_archive else None
    record['instrumentation_sha256']=instrumentation
    record['user_state']={'path':str(a.user_state or out/'user'),'before':config_receipt()}
    record['scheduling']={'cpu_affinity':sorted(os.sched_getaffinity(0)),'render_threads':a.render_threads,'LP_NUM_THREADS':env['LP_NUM_THREADS'],'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    record['authority_staging']={'enabled':a.allow_authority_staging,'stages':[],'scope':'Only explicit stage steps use authority fixtures. Navigation remains native XTest. Staged outcomes are not native-playthrough claims.'}
    record['shader_cache_seed']={'path':str(a.shader_cache_seed) if a.shader_cache_seed else None,'copied_to':env['MESA_SHADER_CACHE_DIR'],'files_sha256':seed_pins,'reused_isolated_cache_sha256':prior_cache_pins,'scope':'Copied warm Mesa cache; no cold-start or hardware-performance claim.' if seed_pins else ('Reused isolated cache from an earlier package process; warm-cache capture.' if prior_cache_pins else 'No Mesa cache seed supplied.')}
    def resolve_event(step,state):
        event=dict(step)
        if 'wheel' in step:
            if not isinstance(step['wheel'],int) or not 1<=abs(step['wheel'])<=12: raise ValueError('Wheel steps must be 1–12 signed ticks')
            if len(step.get('point',[]))!=2 or not 0<=step['point'][0]<a.width or not 0<=step['point'][1]<a.height: raise ValueError('Wheel point must be inside owned window')
        elif not any(key in step for key in ['key','key_down','key_up']):
            field='name' if 'click_name' in step else 'text'; value=step.get('click_name',step.get('click_text'))
            controls=[c for c in state['controls'] if c[field]==value and c.get('interactive',not c['disabled'])]
            if len(controls)!=1: raise RuntimeError(f'Expected unique enabled control {value}: {controls}')
            x,y,w,h=controls[0].get('input_rect',controls[0]['rect']); event['point']=[x+w/2,y+h/2]
            if not 0<=event['point'][0]<a.width or not 0<=event['point'][1]<a.height: raise RuntimeError('Control outside viewport; scroll with actual input first')
        return event
    def settle_pointer(step,initial):
        field='name' if 'click_name' in step else 'text'; target=step.get('click_name',step.get('click_text'))
        last_frame=-1; last_rect=None; stable=0; samples=[]; deadline=time.monotonic()+a.timeout
        while time.monotonic()<deadline:
            current=read(out/'state.json'); frame=current.get('frame',-1)
            if frame!=last_frame:
                controls=[c for c in current.get('controls',[]) if c[field]==target and c.get('interactive',not c['disabled'])]
                if len(controls)==1:
                    rect=controls[0].get('input_rect',controls[0]['rect'])
                    stable=stable+1 if rect==last_rect else 0
                    samples.append({'frame':frame,'rect':rect})
                    if stable>=2 and frame>=initial.get('frame',0)+2: return current,samples
                    last_rect=rect
                else: stable=0; last_rect=None
                last_frame=frame
            time.sleep(.01)
        raise TimeoutError('Native pointer target did not settle: '+target)
    server=game=native=None
    try:
        with (out/'xvfb.log').open('w') as xl,(out/'godot.log').open('w') as gl:
            server=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),env['DISPLAY'],'-screen','0',f'{a.width}x{a.height}x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT)
            wait_for(lambda:P(f'/tmp/.X11-unix/X{a.display}').exists(),5)
            game=subprocess.Popen(command,env=env,stdout=gl,stderr=subprocess.STDOUT,cwd=a.package.parent if a.mode=='package' else None)
            native=NativeInput(env['DISPLAY']); native.focus()
            for index,step in enumerate(plan):
                state=wait_for(lambda:read(out/'state.json'),a.timeout)
                if 'stage' in step:
                    stage_id='stage-'+str(index+1)
                    save(out/'stage-request.json',{'id':stage_id,'action':step['stage']})
                    receipt=wait_for(lambda:r if (r:=read(out/'stage-result.json')).get('id')==stage_id else None,a.timeout)
                    record['authority_staging']['stages'].append(receipt)
                    if receipt.get('passed') is not True: raise RuntimeError('Authority stage failed: '+str(receipt))
                    state=wait_for(lambda:s if (s:=read(out/'state.json')).get('frame',-1)>receipt['frame'] else None,a.timeout)
                if 'burst' in step:
                    events=[resolve_event(event,state) for event in step['burst']]
                    window_id=native.burst(events)
                    record['events'].append({'burst':events,'window_id':window_id,'before':state,'time_unix':time.time()})
                if 'tab_to_text' in step or 'tab_to_name' in step:
                    focus_key='focus_name' if 'tab_to_name' in step else 'focus_text'
                    target=step.get('tab_to_name',step.get('tab_to_text'))
                    for tab_index in range(40):
                        if state.get(focus_key)==target: break
                        before=state
                        window_id=native.event({'key':'Tab'})
                        record['events'].append({'key':'Tab','window_id':window_id,'before':before,'time_unix':time.time(),'purpose':'Reach '+target})
                        state=wait_for(lambda:s if (s:=read(out/'state.json')).get('frame',-1)>before.get('frame',-1) else None,a.timeout)
                    else: raise RuntimeError('Tab chain did not reach '+target)
                if any(key in step for key in ['key','key_down','key_up']) or 'click_name' in step or 'click_text' in step or 'wheel' in step:
                    settlement=[]
                    if a.mode=='package' and ('click_name' in step or 'click_text' in step): state,settlement=settle_pointer(step,state)
                    event=resolve_event(step,state)
                    if settlement: event['pointer_settlement']=settlement
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
                if 'wait_physics' in step:
                    target_tick=state['physics_frame']+int(step['wait_physics'])
                    state=wait_for(lambda:s if (s:=read(out/'state.json')).get('physics_frame',-1)>=target_tick else None,a.timeout)
                    if not matches(state,expected): raise RuntimeError('State changed during requested physics interval')
                if 'capture' in step:
                    name=step['capture']; save(out/'capture-request.json',{'name':name})
                    shot=wait_for(lambda:read(out/(name+'.json')),a.timeout)
                    if sha(out/shot['file'])!=shot['sha256']: raise RuntimeError('PNG hash differs')
                    record['shots'].append(shot)
                    if not matches(shot,expected): raise RuntimeError('Captured framebuffer state differs from requested expectation: '+name)
                save(out/'run.json',record)
            record['automatic_shots']=[read(file) for file in sorted(out.glob('auto-*.json'))]
            record['package_unchanged']=all(sha(f)==h for f,h in package_pins.items())
            record['instrumentation_unchanged']=all(sha(f)==h for f,h in instrumentation.items())
            if not record['package_unchanged'] or not record['instrumentation_unchanged']: raise RuntimeError('Package or instrumentation changed')
            record['archive_unchanged']=not a.package_archive or sha(a.package_archive)==record['package_archive']['sha256']
            record['export_manifest_unchanged']=not a.export_manifest or sha(a.export_manifest)==record['export_manifest']['sha256']
            if not record['archive_unchanged'] or not record['export_manifest_unchanged']: raise RuntimeError('Archive/provenance manifest changed')
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
        record['user_state']['after']=config_receipt()
        record['finished_unix']=time.time(); record['cleanup_exit']=game.returncode if game else None
        record['logs']={f:sha(out/f) for f in ['godot.log','xvfb.log'] if (out/f).exists()}
        save(out/'run.json',record)
    log=(out/'godot.log').read_text()
    if 'SCRIPT ERROR:' in log or '\nERROR:' in log: raise RuntimeError('Engine error; review preserved godot.log')
    print(json.dumps({'complete':record['complete'],'shots':len(record['shots']),'output':str(out)},indent=2))
if __name__=='__main__': main()
