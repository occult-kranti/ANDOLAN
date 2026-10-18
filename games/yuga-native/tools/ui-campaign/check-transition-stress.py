#!/usr/bin/env python3
"""Run exact-source seeded transition lifecycle stress in a temporary 2D fixture; no imports."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--engine',default='godot')
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--source',type=Path)
parser.add_argument('--seed',type=int,default=741903)
args=parser.parse_args()
test_source=Path(__file__).resolve().parents[2]
source=args.source.resolve() if args.source else test_source
engine=shutil.which(args.engine)
if not engine:parser.error('Godot engine not found: '+args.engine)
report_path=args.report.resolve();report_path.parent.mkdir(parents=True,exist_ok=True)
log_path=report_path.with_suffix('.output.txt')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
files=[source/'scripts/scene_transition.gd',source/'scripts/hero_ui_theme.gd',test_source/'tests/ui_transition_stress_cases.gd']
files+=list((source/'assets/fonts').glob('*'))+list((source/'.godot/imported').glob('*.ttf-*'))
pins={};log='';command=[];exit_code=None
result={'passed':False,'passed_count':0,'count':0,'checks':[]}
try:
    with tempfile.TemporaryDirectory(prefix='yuga-transition-check-') as folder:
        fixture=Path(folder)
        for file in files:
            if not file.is_file():continue
            relative=file.relative_to(test_source) if file==test_source/'tests/ui_transition_stress_cases.gd' else file.relative_to(source);target=fixture/relative
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target);pins[str(relative)]=sha(file)
            if sha(target)!=pins[str(relative)]:raise RuntimeError('Fixture copy mismatch')
        (fixture/'project.godot').write_text('config_version=5\n[application]\nconfig/name="YUGA transition signal fixture"\n[test]\nui_transition_stress_fixture=true\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        command=[engine,'--headless','--path',str(fixture),'--script','res://tests/ui_transition_stress_cases.gd','--','--report='+str(fixture/'report.json'),'--seed='+str(args.seed)]
        completed=subprocess.run(command,capture_output=True,text=True,timeout=60)
        log=completed.stdout+completed.stderr;exit_code=completed.returncode
        if (fixture/'report.json').is_file():result=json.loads((fixture/'report.json').read_text())
        unchanged=all(sha((test_source if relative.startswith('tests/') else source)/relative)==checksum and sha(fixture/relative)==checksum for relative,checksum in pins.items())
        if not unchanged:raise RuntimeError('Tested source changed during fixture run')
        if exit_code:raise RuntimeError('Engine exited '+str(exit_code))
        if any(marker in log for marker in ['ERROR:','WARNING:','ObjectDB instances leaked']):raise RuntimeError('Unexpected engine diagnostic')
        if result.get('passed') is not True or not result.get('checks') or not all(check.get('passed') is True for check in result['checks']):raise RuntimeError('Fixture assertions did not pass')
        result['source_unchanged']=True
except subprocess.TimeoutExpired as error:
    log=(error.stdout or b'').decode(errors='replace') if isinstance(error.stdout,bytes) else (error.stdout or '')
    result['passed']=False;result['error']='Fixture exceeded60-second timeout'
except Exception as error:
    result['passed']=False;result['error']=str(error)
log_path.write_text(log)
result['harness']={'runtime_source':str(source),'test_source':str(test_source),'command':command,'exit_code':exit_code,'source_sha256':pins,'engine_sha256':sha(Path(engine)),'output_sha256':sha(log_path),'scope':'Temporary tiny PackedScene project; copies existing fonts/imports and performs no editor import or 3D rendering.'}
report_path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'passed_count':result.get('passed_count',0),'count':result.get('count',0),'report':str(report_path)}))
raise SystemExit(0 if result['passed'] is True else 1)
