#!/usr/bin/env python3
"""Isolate real tiny loading cases without product imports or scene modifications."""
import argparse, hashlib, json, pathlib, shutil, subprocess
P=pathlib.Path
p=argparse.ArgumentParser();p.add_argument('--output',type=P,required=True);a=p.parse_args()
source=P(__file__).resolve().parents[5];out=a.output.resolve()
if not a.output.is_absolute() or out.exists() or source in out.parents:p.error('Use fresh absolute output outside product.')
out.mkdir(parents=True)
files=[source/'scripts/scene_transition.gd',source/'scripts/hero_ui_theme.gd',source/'tests/ui_transition_signal_cases.gd']
files += list((source/'assets/fonts').glob('*'))+list((source/'.godot/imported').glob('*.ttf-*'))
pins={}
for f in files:
    if not f.is_file():continue
    rel=f.relative_to(source);target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);pins[str(rel)]=hashlib.sha256(f.read_bytes()).hexdigest()
(out/'project.godot').write_text('config_version=5\n[application]\nconfig/name="YUGA transition signal fixture"\n[test]\nui_transition_signal_fixture=true\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
command=['taskset','-c','2','godot','--headless','--path',str(out),'--script','res://tests/ui_transition_signal_cases.gd','--','--report='+str(out/'report.json')]
result=subprocess.run(command,capture_output=True,text=True,timeout=60)
log=result.stdout+result.stderr;(out/'output.txt').write_text(log)
receipt={'command':command,'exit_code':result.returncode,'source_sha256':pins,'source_unchanged':all(hashlib.sha256((out/f).read_bytes()).hexdigest()==h for f,h in pins.items())}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(log)
if result.returncode:raise SystemExit(result.returncode)
if 'ERROR:' in log or 'WARNING:' in log:raise SystemExit('Unexpected engine diagnostic.')
