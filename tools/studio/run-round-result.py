#!/usr/bin/env python3
"""Run one source-bound scripted native result capture on an owned X11 display."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--pack', type=Path, required=True)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--display', type=int, default=129, choices=range(90,200))
    parser.add_argument('--shader-cache-seed', type=Path)
    parser.add_argument('--godot-shader-cache-seed', type=Path)
    parser.add_argument('--timeout', type=int, default=420, choices=range(60,601))
    args = parser.parse_args()
    for name in ('engine','pack','script'):
        path = getattr(args,name).resolve()
        if not path.is_file(): parser.error(name+' must exist')
        setattr(args,name,path)
    out = args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    env = os.environ.copy()
    env['DISPLAY'] = ':'+str(args.display)
    env['LP_NUM_THREADS'] = '8'
    for variable,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        location = out/'user'/folder
        location.mkdir(parents=True)
        env[variable] = str(location)
    env['MESA_SHADER_CACHE_DIR'] = str(out/'user/cache/mesa')
    socket = Path('/tmp/.X11-unix/X'+str(args.display))
    if socket.exists(): parser.error('Requested display is already owned')
    cache_proof = {'seeded':False}
    if args.shader_cache_seed or args.godot_shader_cache_seed:
        helper_path = Path(__file__).resolve().parents[2] / 'games/yuga-native/tools/run-traversal-capture.py'
        spec = importlib.util.spec_from_file_location('native_cache_helper',helper_path)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        (out/'user/data/godot/app_userdata/YUGA • Confluence').mkdir(parents=True,exist_ok=True)
        cache_proof = {'mesa':helper.seed_shader_cache(args.shader_cache_seed,out/'user/cache/mesa'),'godot':helper.seed_shader_cache(args.godot_shader_cache_seed,out/'user/data/godot/app_userdata/YUGA • Confluence/shader_cache')}
    inputs = {name:{'path':str(getattr(args,name)),'sha256':sha(getattr(args,name))} for name in ('engine','pack','script')}
    command = [str(args.engine),'--main-pack',str(args.pack),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--resolution','1280x720','--max-fps','15','--script',str(args.script),'--','--output='+str(out/'capture'),'--restart']
    started = time.monotonic()
    result_code = None
    timed_out = False
    with (out/'xvfb.log').open('w') as xlog,(out/'game.log').open('w') as log:
        display = subprocess.Popen([shutil.which('Xvfb') or 'Xvfb',env['DISPLAY'],'-screen','0','1280x720x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xlog,stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic()+5
            while not socket.exists():
                if display.poll() is not None or time.monotonic()>deadline: raise RuntimeError('Owned X11 server did not start')
                time.sleep(.1)
            game = subprocess.Popen(command,env=env,cwd=out,stdout=log,stderr=subprocess.STDOUT)
            try: result_code = game.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                game.terminate()
                try: result_code = game.wait(timeout=8)
                except subprocess.TimeoutExpired: game.kill();result_code=game.wait()
        finally:
            display.terminate()
            try: display.wait(timeout=5)
            except subprocess.TimeoutExpired: display.kill();display.wait()
    capture = out/'capture/capture.json'
    report = json.loads(capture.read_text()) if capture.exists() else {}
    stable = all(sha(getattr(args,name))==record['sha256'] for name,record in inputs.items())
    receipt = {'shader_cache_seed':cache_proof,'inputs':inputs,'command':command,'exit_code':result_code,'timed_out':timed_out,'wall_s':time.monotonic()-started,'input_bytes_stable':stable,'capture_report_sha256':sha(capture) if capture.exists() else None,'passed':result_code==0 and stable and report.get('complete',False),'scope':'Actual software Forward+ native viewport after scripted player relocations and normal army/kit ticks. No ordinary human-match, audio or physicalGPU claim.'}
    (out/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
    return 0 if receipt['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
