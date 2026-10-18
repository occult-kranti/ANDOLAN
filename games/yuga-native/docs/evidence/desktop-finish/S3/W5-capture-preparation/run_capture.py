#!/usr/bin/env python3
"""Bounded exact-pair preflight/render. Never imports or changes runtime inputs."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pair',type=Path,required=True)
    ap.add_argument('--role',choices=['baseline','candidate'],required=True)
    ap.add_argument('--case',choices=['full','landing120'],required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--cpu',choices=['2','3','2,3','0,1'],default='3')
    ap.add_argument('--preflight',action='store_true')
    ap.add_argument('--render',action='store_true',help='Explicit heavy lane mode; caller must own the root-authorized lane')
    ap.add_argument('--display',type=int,default=187)
    ap.add_argument('--timeout',type=int,default=180)
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    if args.preflight==args.render or not 1<=args.timeout<=900:
        ap.error('Choose exactly one of preflight/render and timeout1–900s')
    pair=json.loads(args.pair.read_text());item=pair['stages'][args.role];project=Path(item['project'])
    spec=importlib.util.spec_from_file_location('snapshot',project/'tools/graphics-six/snapshot.py')
    snapshot=importlib.util.module_from_spec(spec);spec.loader.exec_module(snapshot)
    snapshot.verify(project)
    if sha(project/snapshot.MARKER)!=item['seal_sha256']:
        ap.error('Stage seal changed')
    output=args.output.resolve();logs=output.with_name(output.name+'-logs')
    if output.exists() or logs.exists():ap.error('Fresh output and sibling logs required')
    if shutil.disk_usage(output.parent).free < pair['required_free_floor_bytes']+512*1024**2:
        ap.error('Need3GiB free floor plus512MiB run allowance')
    engine=Path(shutil.which('godot') or '')
    if not engine.is_file():ap.error('Installed godot missing')
    hz=120 if args.case=='landing120' else 30
    cmd=['taskset','-c',args.cpu,str(engine),'--path',str(project),'--audio-driver','Dummy','--disable-vsync','--fixed-fps',str(hz)]
    cmd+=['--headless'] if args.preflight else ['--display-driver','x11','--rendering-method','forward_plus']
    cmd+=['--script','res://tools/graphics-six/capture_transition.gd','--',f'--output={output}',f'--case={args.case}']
    if args.preflight:cmd.append('--preflight')
    if args.dry_run:
        print(json.dumps({'command':cmd,'starts_engine':False,'private_godot_seed':item['godot_seed'],'mesa_seed':None,'timeout':args.timeout},indent=2));return
    logs.mkdir(parents=True)
    env=os.environ.copy();env.update(LP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    for name,suffix in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        folder=logs/'user'/suffix;folder.mkdir(parents=True);env[name]=str(folder)
    env['MESA_SHADER_CACHE_DIR']=str(logs/'user/cache/mesa')
    names=re.findall(r'^config/name="([^"\n]+)"',(project/'project.godot').read_text(),re.M)
    if len(names)!=1 or '/' in names[0]:raise RuntimeError('Unexpected project user directory')
    seed=Path(item['godot_seed']);seed_before={str(p.relative_to(seed)):sha(p) for p in seed.rglob('*') if p.is_file()}
    if seed_before!={k:v['sha256'] for k,v in pair['godot_seed_files'].items()}:raise RuntimeError('Warm seed changed')
    target=Path(env['XDG_DATA_HOME'])/'godot/app_userdata'/names[0]/'shader_cache';shutil.copytree(seed,target)
    record={'complete':False,'command':cmd,'pair_sha256':sha(args.pair),'stage_seal_sha256':item['seal_sha256'],'case':args.case,'role':args.role,
            'runner_sha256':sha(Path(__file__)),
            'engine_sha256':sha(engine),'preflight':args.preflight,'worker_pool_capped':False,'affinity':args.cpu,'library_thread_env':1,
            'private_godot_seed_sha256':seed_before,'mesa_seed':None,'timeout_s':args.timeout,'errors':[]}
    xvfb=None;process=None;start=time.monotonic();last_progress=start;previous=(-1,-1)
    try:
        if args.render:
            if not 90<=args.display<=199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():raise RuntimeError('Display must be unused90–199')
            env['DISPLAY']=':'+str(args.display)
            xvfb_log=(logs/'xvfb.log').open('wb')
            xvfb=subprocess.Popen(['Xvfb',env['DISPLAY'],'-screen','0','1280x960x24','-nolisten','tcp'],stdout=xvfb_log,stderr=subprocess.STDOUT)
            deadline=time.monotonic()+5
            while not Path(f'/tmp/.X11-unix/X{args.display}').exists():
                if xvfb.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Xvfb startup failed')
                time.sleep(.05)
        log_path=logs/'godot.log'
        with log_path.open('wb') as log:
            process=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
            record['pid']=process.pid
            while process.poll() is None:
                now=time.monotonic();progress=(log_path.stat().st_size,len(list(output.glob('*.png'))))
                if progress!=previous:last_progress=now;previous=progress
                if now-start>args.timeout or now-last_progress>120:raise TimeoutError('Overall/no-progress deadline exceeded')
                if shutil.disk_usage(output.parent).free<pair['required_free_floor_bytes']:raise RuntimeError('3GiB free floor reached')
                time.sleep(.2)
        record['exit_code']=process.returncode
        report_path=output/('preflight.json' if args.preflight else 'capture.json')
        report=json.loads(report_path.read_text()) if report_path.is_file() else {}
        record['report_sha256']=sha(report_path) if report_path.exists() else None
        record['checks']=report.get('checks',[])
        diagnostics=[line for line in log_path.read_text(errors='replace').splitlines() if re.search(r'(^|\s)(SCRIPT ERROR|ERROR|WARNING):',line)]
        record['errors']=diagnostics
        snapshot.verify(project)
        record['complete']=process.returncode==0 and bool(report.get('complete')) and not diagnostics and sha(project/snapshot.MARKER)==item['seal_sha256']
        record['raw_pngs']=len(list(output.glob('*.png')))
    except Exception as exc:
        record['failure']=str(exc)
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
        if xvfb and xvfb.poll() is None:
            xvfb.terminate();xvfb.wait(timeout=5)
        record['wall_seconds']=round(time.monotonic()-start,3)
        record['seed_unchanged']=seed_before=={str(p.relative_to(seed)):sha(p) for p in seed.rglob('*') if p.is_file()}
        record['complete']=record['complete'] and record['seed_unchanged']
        (logs/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record.get(k) for k in ('complete','exit_code','failure','wall_seconds','raw_pngs')}))
    raise SystemExit(0 if record['complete'] else 1)


if __name__=='__main__':main()
