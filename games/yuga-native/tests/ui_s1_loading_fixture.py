#!/usr/bin/env python3
"""Run copied boot/loading sources with tiny scenes; no editor, import or 3D scene."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', default='godot')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--case', choices=('s1','legacy','stress','host-replacement'), default='s1')
    parser.add_argument('--source-boot', type=Path, help='Explicit historical source override for a negative-control run')
    parser.add_argument('--source-transition', type=Path, help='Historical transition source for the same negative control')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    engine = shutil.which(args.engine)
    if not engine:
        parser.error('Godot not found: '+args.engine)
    report = args.report.resolve()
    log_path = report.with_suffix('.log')
    if report.exists() or log_path.exists():
        parser.error('Fresh report/log paths required')
    report.parent.mkdir(parents=True,exist_ok=True)
    test = {'s1':'tests/ui_s1_loading_cases.gd', 'legacy':'tests/ui_boot_cases.gd',
            'stress':'tests/ui_transition_stress_cases.gd',
            'host-replacement':'tests/ui_s2_transition_cases.gd'}[args.case]
    names = ['scripts/boot.gd','scripts/scene_transition.gd','scripts/loading_presentation.gd','scripts/hero_ui_theme.gd','scenes/boot.tscn',test]
    names += [str(p.relative_to(project)) for p in (project/'assets/fonts').glob('*') if p.is_file()]
    names += [str(p.relative_to(project)) for p in (project/'.godot/imported').glob('*.ttf-*') if p.is_file()]
    sources = {name:(args.source_boot.resolve() if name=='scripts/boot.gd' and args.source_boot else project/name) for name in names}
    if args.source_transition:
        sources['scripts/scene_transition.gd']=args.source_transition.resolve()
    sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    pins = {name:sha(path) for name,path in sources.items()}
    result = {'passed':False,'count':0,'passed_count':0,'checks':[]}
    log = ''
    command = []
    exit_code = None
    try:
        with tempfile.TemporaryDirectory(prefix='yuga-s1-loading-') as tmp:
            fixture = Path(tmp)
            for name,path in sources.items():
                target=fixture/name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(path,target)
                if sha(target)!=pins[name]:raise RuntimeError('Fixture copy mismatch: '+name)
            (fixture/'project.godot').write_text('config_version=5\n[application]\nconfig/name="YUGA S1 loading fixture"\n[test]\nui_s1_loading_fixture=true\nui_s2_transition_fixture=true\nui_transition_stress_fixture=true\nscene_transition_fixture=true\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
            command=[engine,'--headless','--path',str(fixture),'--script','res://'+test,'--','--report='+str(fixture/'result.json')]
            environment=os.environ.copy()
            environment.update(LP_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
            completed=subprocess.run(command,capture_output=True,text=True,timeout=20,env=environment)
            exit_code=completed.returncode
            log=completed.stdout+completed.stderr
            if (fixture/'result.json').is_file():result=json.loads((fixture/'result.json').read_text())
            unchanged=all(sha(path)==pins[name] and sha(fixture/name)==pins[name] for name,path in sources.items())
            result['source_unchanged']=unchanged
            if not unchanged:raise RuntimeError('Tested source changed')
            if exit_code:raise RuntimeError('Engine exited '+str(exit_code))
            if any(marker in log for marker in ('ERROR:','WARNING:','ObjectDB instances leaked')):
                raise RuntimeError('Unexpected engine diagnostic; inspect retained log')
            if result.get('passed') is not True or not result.get('checks') or not all(c.get('passed') is True for c in result['checks']):
                raise RuntimeError('Fixture assertions did not pass')
    except subprocess.TimeoutExpired as error:
        log=''.join(v.decode(errors='replace') if isinstance(v,bytes) else v or '' for v in (error.stdout,error.stderr))
        result['passed']=False
        result['error']='Fixture exceeded 20 seconds'
    except Exception as error:
        result['passed']=False
        result['error']=str(error)
    log_path.write_text(log)
    result['harness']={'command':command,'exit_code':exit_code,'case':args.case,
        'source_sha256':pins,'source_boot_override':str(args.source_boot) if args.source_boot else None,
        'source_transition_override':str(args.source_transition) if args.source_transition else None,
        'engine_sha256':sha(Path(engine)),'log_sha256':sha(log_path),
        'cpu_affinity':sorted(os.sched_getaffinity(0)),
        'scope':'Copied scripts/fonts and small scene fixtures; no editor import, 3D render or startup performance acceptance.'}
    report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'count':result.get('count'), 'passed_count':result.get('passed_count'),'error':result.get('error'),'report':str(report)}))
    return 0 if result['passed'] is True else 1

if __name__=='__main__':raise SystemExit(main())
