#!/usr/bin/env python3
"""Current96d5/e69 locomotion derivative. Explicit lane, fresh output and measured reserve required."""
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

ENGINE_SHA256 = 'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pair',type=Path,required=True)
    ap.add_argument('--render-inputs',type=Path,required=True)
    ap.add_argument('--progress-timeout',type=int,required=True)
    ap.add_argument('--role',choices=['current'],required=True)
    ap.add_argument('--case',choices=['locomotion'],required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--cpu',choices=['4','0,1'],default='4')
    ap.add_argument('--preflight',action='store_true')
    ap.add_argument('--render',action='store_true',help='Explicit heavy lane mode; caller must own the root-authorized lane')
    ap.add_argument('--display',type=int,default=187)
    ap.add_argument('--timeout',type=int,default=180)
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    if args.preflight==args.render or not 1<=args.timeout<=900:
        ap.error('Choose exactly one of preflight/render and timeout1–900s')
    if not 1<=args.progress_timeout<=args.timeout:ap.error('Progress bound must be within overall bound')
    inputs=json.loads(args.render_inputs.read_text())
    if sha(args.pair)!=inputs['pair_sha256']:ap.error('Frozen pair identity differs')
    pair=json.loads(args.pair.read_text());item=pair['stages'][args.role];project=Path(item['project'])
    if pair.get('source_commit')!='96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12':ap.error('Only the declared96d5 derivative is admitted')
    validator=Path(inputs['snapshot_validator']['path'])
    if sha(validator)!=inputs['snapshot_validator']['sha256']:ap.error('Snapshot validator identity differs')
    spec=importlib.util.spec_from_file_location('snapshot',validator)
    snapshot=importlib.util.module_from_spec(spec);spec.loader.exec_module(snapshot)
    snapshot.verify(project)
    if sha(project/snapshot.MARKER)!=item['seal_sha256']:
        ap.error('Stage seal changed')
    output=args.output.resolve();logs=output.with_name(output.name+'-logs')
    if output.exists() or logs.exists():ap.error('Fresh output and sibling logs required')
    if pair['required_free_floor_bytes']!=500*1024**2 or pair['run_allowance_bytes']!=128*1024**2:
        ap.error('Declared current reserve/allowance differs')
    allowance=pair['preflight_allowance_bytes'] if args.preflight else pair['run_allowance_bytes']
    free_before=shutil.disk_usage(output.parent).free
    if free_before < pair['required_free_floor_bytes']+allowance:
        ap.error('Need500MiB reserve plus measured current run allowance')
    engine=Path(inputs['engine']['path'])
    if inputs['engine']['sha256']!=ENGINE_SHA256 or not engine.is_file() or sha(engine)!=ENGINE_SHA256:ap.error('Explicit e69 patched engine identity differs')
    for runtime_file in inputs['render_runtime']['files'].values():
        if sha(runtime_file['path'])!=runtime_file['sha256']:ap.error('Render runtime identity differs')
    hz=30
    cmd=['taskset','-c',args.cpu,str(engine),'--path',str(project),'--audio-driver','Dummy','--disable-vsync','--fixed-fps',str(hz)]
    cmd+=['--headless'] if args.preflight else ['--display-driver','x11','--rendering-method','forward_plus']
    cmd+=['--script','res://tools/graphics-six/capture_locomotion.gd','--',f'--output={output}',f'--case={args.case}']
    if args.preflight:cmd.append('--preflight')
    if args.dry_run:
        print(json.dumps({'command':cmd,'starts_engine':False,'render_inputs_sha256':sha(args.render_inputs),'private_godot_seed':inputs['godot_seed']['path'],'mesa_seed':inputs['mesa_seed']['path'],'timeout':args.timeout,'progress_timeout':args.progress_timeout,'free_before':free_before,'reserve_bytes':pair['required_free_floor_bytes'],'run_allowance_bytes':allowance,'engine_scope':inputs['scope']},indent=2));return
    logs.mkdir(parents=True)
    lp_threads=1 if args.preflight else 2
    env=os.environ.copy();env.update(LP_NUM_THREADS=str(lp_threads),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    for name,suffix in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        folder=logs/'user'/suffix;folder.mkdir(parents=True);env[name]=str(folder)
    env['MESA_SHADER_CACHE_DIR']=str(logs/'user/cache/mesa')
    names=re.findall(r'^config/name="([^"\n]+)"',(project/'project.godot').read_text(),re.M)
    if len(names)!=1 or '/' in names[0]:raise RuntimeError('Unexpected project user directory')
    seed=Path(inputs['godot_seed']['path']);seed_before={str(p.relative_to(seed)):sha(p) for p in seed.rglob('*') if p.is_file()}
    mesa_seed=Path(inputs['mesa_seed']['path']);mesa_before={str(p.relative_to(mesa_seed)):sha(p) for p in mesa_seed.rglob('*') if p.is_file()}
    if seed_before!={k:v['sha256'] for k,v in inputs['godot_seed']['files'].items()}:raise RuntimeError('Godot seed changed')
    if mesa_before!={k:v['sha256'] for k,v in inputs['mesa_seed']['files'].items()}:raise RuntimeError('Mesa seed changed')
    target=Path(env['XDG_DATA_HOME'])/'godot/app_userdata'/names[0]/'shader_cache';shutil.copytree(seed,target)
    shutil.copytree(mesa_seed,Path(env['MESA_SHADER_CACHE_DIR']))
    if {str(p.relative_to(target)):sha(p) for p in target.rglob('*') if p.is_file()}!=seed_before:raise RuntimeError('Copied Godot seed differs')
    mesa_target=Path(env['MESA_SHADER_CACHE_DIR'])
    if {str(p.relative_to(mesa_target)):sha(p) for p in mesa_target.rglob('*') if p.is_file()}!=mesa_before:raise RuntimeError('Copied Mesa seed differs')
    record={'complete':False,'command':cmd,'pair_sha256':sha(args.pair),'stage_seal_sha256':item['seal_sha256'],'case':args.case,'role':args.role,
            'runner_sha256':sha(Path(__file__)),
            'engine_sha256':sha(engine),'engine_scope':inputs['scope'],'preflight':args.preflight,'worker_pool_capped':False,'affinity':args.cpu,'runner_affinity':sorted(os.sched_getaffinity(0)),'library_thread_env':{'LP_NUM_THREADS':lp_threads,'OPENBLAS_NUM_THREADS':1,'OMP_NUM_THREADS':1,'MKL_NUM_THREADS':1},
            'storage':{'free_before':free_before,'reserve_bytes':pair['required_free_floor_bytes'],'run_allowance_bytes':allowance},
            'render_inputs_sha256':sha(args.render_inputs),'private_godot_seed_sha256':seed_before,'private_mesa_seed_sha256':mesa_before,'timeout_s':args.timeout,'progress_timeout_s':args.progress_timeout,'errors':[]}
    xvfb=None;process=None;start=time.monotonic();last_progress=start;previous=(-1,-1)
    try:
        if args.render:
            if not 90<=args.display<=199 or Path(f'/tmp/.X11-unix/X{args.display}').exists():raise RuntimeError('Display must be unused90–199')
            env['DISPLAY']=':'+str(args.display)
            env['VK_ICD_FILENAMES']=inputs['render_runtime']['files']['vulkan_icd']['path']
            env['LD_LIBRARY_PATH']=inputs['render_runtime']['library_directory']+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
            record['render_environment']={key:env[key] for key in ['DISPLAY','VK_ICD_FILENAMES','LD_LIBRARY_PATH']}
            xvfb_log=(logs/'xvfb.log').open('wb')
            xvfb_command=[inputs['render_runtime']['files']['xvfb']['path'],env['DISPLAY'],'-screen','0','1280x960x24','-nolisten','tcp','-extension','MIT-SHM','-ac']
            record['xvfb_command']=xvfb_command
            xvfb=subprocess.Popen(xvfb_command,env=env,stdout=xvfb_log,stderr=subprocess.STDOUT)
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
                if now-start>args.timeout or now-last_progress>args.progress_timeout:raise TimeoutError('Overall/no-progress deadline exceeded')
                free_now=shutil.disk_usage(output.parent).free
                if free_now<pair['required_free_floor_bytes']:raise RuntimeError('500MiB reserve reached; preserve partial run')
                if free_before-free_now>allowance:raise RuntimeError('Declared run allocation exceeded; preserve partial run')
                time.sleep(.2)
        record['exit_code']=process.returncode
        report_path=output/('preflight.json' if args.preflight else 'capture.json')
        report=json.loads(report_path.read_text()) if report_path.is_file() else {}
        record['report_sha256']=sha(report_path) if report_path.exists() else None
        record['checks']=report.get('checks',[])
        diagnostics=[line for line in log_path.read_text(errors='replace').splitlines() if re.search(r'(^|\s)(SCRIPT ERROR|ERROR|WARNING):',line)]
        record['errors']=diagnostics
        if report.get('complete') and (len(report.get('shots',[]))!=270 or len(report.get('checks',[]))<10 or not all(c.get('passed') is True for c in report['checks'])):
            raise RuntimeError('Declared locomotion coverage/count not satisfied')
        if not args.preflight:
            selected=set(range(225,256))|{269}
            expected_pngs={f'frame-{index:03d}.png' for index in selected}
            saved=[shot for shot in report.get('shots',[]) if shot.get('framebuffer_saved') is True]
            if (report.get('expected_raw_pngs')!=32 or report.get('saved_frame_indices')!=sorted(selected)
                    or {path.name for path in output.glob('*.png')}!=expected_pngs or len(saved)!=32
                    or {shot['file'] for shot in saved}!=expected_pngs
                    or any(shot.get('framebuffer_saved') is not (shot.get('tape_index') in selected) for shot in report.get('shots',[]))
                    or any(shot.get('sha256') is not None for shot in report.get('shots',[]) if shot.get('framebuffer_saved') is False)
                    or not all(sha(output/shot['file'])==shot['sha256'] for shot in saved)):
                raise RuntimeError('Selected32PNG count/indices/hash or omitted-frame metadata mismatch')
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
        record['storage']['free_after']=shutil.disk_usage(output.parent).free
        record['seed_unchanged']=seed_before=={str(p.relative_to(seed)):sha(p) for p in seed.rglob('*') if p.is_file()}
        record['mesa_seed_unchanged']=mesa_before=={str(p.relative_to(mesa_seed)):sha(p) for p in mesa_seed.rglob('*') if p.is_file()}
        record['complete']=record['complete'] and record['seed_unchanged'] and record['mesa_seed_unchanged']
        (logs/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record.get(k) for k in ('complete','exit_code','failure','wall_seconds','raw_pngs')}))
    raise SystemExit(0 if record['complete'] else 1)


if __name__=='__main__':main()
