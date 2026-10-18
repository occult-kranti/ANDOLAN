#!/usr/bin/env python3
"""Run one bounded private headless probe and preserve its original diagnostics."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--role',choices=['baseline','candidate','legacy'],required=True)
    ap.add_argument('--kind',choices=['landing','scene','guard','boundary','pause'],required=True)
    ap.add_argument('--hz',type=int,default=120)
    ap.add_argument('--suffix',default='r1')
    args=ap.parse_args()
    prefix=args.role+'-'+args.kind+'-'+str(args.hz)+'-'+args.suffix
    out=ROOT/prefix
    assert not out.exists();out.mkdir()
    project=Path('/tmp/yuga-s3-landing-successor-r1')/args.role/'project'
    motion_before=sha(project/'scripts/rama_motion.gd')
    engine=Path(shutil.which('godot')).resolve()
    env=dict(os.environ,LP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
             XDG_DATA_HOME='/tmp/yuga-'+prefix+'-data',XDG_CACHE_HOME='/tmp/yuga-'+prefix+'-cache')
    command=['taskset','-c','4',str(engine),'--headless','--fixed-fps',str(args.hz),'--path',str(project)]
    if args.kind=='landing':
        raw_dir=Path('/tmp/yuga-'+prefix+'-original');assert not raw_dir.exists()
        command+=['--script','res://tools/graphics-six/capture_transition.gd','--','--case=landing120',
                  '--output='+str(raw_dir),'--preflight']
        raw=raw_dir/'preflight.json'
    else:
        raw=Path('/tmp/yuga-'+prefix+'.json');assert not raw.exists()
        script={'boundary':'desktop_landing_support_boundary_cases.gd','pause':'desktop_landing_pause_cases.gd'}.get(args.kind,'desktop_s3_transition_'+('scene' if args.kind=='scene' else 'guard')+'_cases.gd')
        command+=['--script','res://tests/'+script,'--','--report='+str(raw)]
        if args.kind=='scene':command+=['--hz='+str(args.hz),'--summary-report']
    start=time.monotonic();code=None;timeout=False
    with (out/'engine.log').open('wb') as log:
        try:code=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
        except subprocess.TimeoutExpired:timeout=True
    execution={'command':command,'engine_sha256':sha(engine),'exit_code':code,'timeout':timeout,
               'wall_seconds':round(time.monotonic()-start,3),'motion_before':motion_before,
               'motion_after':sha(project/'scripts/rama_motion.gd'),'affinity':[4],
               'library_threads':1,'engine_worker_pool':'not capped','raw_report':str(raw),
               'scope':'Headless actual imported resources; no raster or motion-quality acceptance.'}
    if raw.is_file():
        data=raw.read_bytes();parsed=json.loads(data)
        if args.kind=='landing':
            gz=gzip.compress(data,mtime=0);(out/'report.json.gz').write_bytes(gz)
            execution.update(raw_sha256=hashlib.sha256(data).hexdigest(),raw_bytes=len(data),
                             gzip_sha256=hashlib.sha256(gz).hexdigest(),gzip_bytes=len(gz),
                             complete=parsed.get('complete'),checks=parsed.get('checks'))
        else:
            shutil.copy2(raw,out/'report.json')
            if 'trace' in parsed:
                sidecar=raw.parent/parsed['trace']['path'];shutil.copy2(sidecar,out/sidecar.name)
            execution.update(complete=parsed.get('passed'),checks=parsed.get('checks'))
    (out/'execution.json').write_text(json.dumps(execution,indent=2)+'\n')
    print(json.dumps({k:execution.get(k) for k in ('exit_code','timeout','wall_seconds','complete')}))
    raise SystemExit(code if code is not None else 124)


if __name__=='__main__':main()
