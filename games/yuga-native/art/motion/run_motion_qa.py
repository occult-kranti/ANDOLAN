#!/usr/bin/env python3
"""Run reconstructed numerical motion QA in a clean, bounded Godot project."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

NATIVE = Path(__file__).resolve().parents[2]

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work-dir',required=True,type=Path)
    p.add_argument('--library',type=Path,default=NATIVE/'assets/animations/tps_rama_motion_library.tres')
    p.add_argument('--manifest',type=Path,default=NATIVE/'art/motion/motion-retarget-manifest.json')
    p.add_argument('--contacts',type=Path,default=NATIVE/'art/motion/support-contact-samples.json')
    p.add_argument('--report',type=Path,default=NATIVE/'tests/evidence/motion-retarget-recovered-support.json')
    p.add_argument('--godot',default='godot')
    a=p.parse_args()
    work=a.work_dir.resolve()
    if work==NATIVE or NATIVE in work.parents: raise ValueError('Use a separate project outside native source.')
    project=work/'godot'
    files={NATIVE/'assets/heroes/rama-production.glb':'assets/heroes/rama-production.glb',NATIVE/'assets/heroes/rama.glb':'assets/heroes/rama.glb',a.library:'assets/animations/tps_rama_motion_library.tres',a.manifest:'art/motion/motion-retarget-manifest.json',a.contacts:'art/motion/support-contact-samples.json',NATIVE/'tests/motion_retarget_cases.gd':'tests/motion_retarget_cases.gd'}
    for source,destination in files.items():
        dest=project/destination
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,dest)
    (project/'project.godot').write_text('''config_version=5
[application]
config/name="Isolated YUGA motion acceptance"
config/features=PackedStringArray("4.6", "GL Compatibility")
[rendering]
renderer/rendering_method="gl_compatibility"
[threading]
worker_pool/max_threads=2
''')
    env=os.environ.copy()
    for variable,folder in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        env[variable]=str(work/'xdg'/folder)
        Path(env[variable]).mkdir(parents=True,exist_ok=True)
    commands=[([a.godot,'--headless','--path',str(project),'--editor','--import','--quit'],'import.log'),([a.godot,'--headless','--path',str(project),'--script','res://tests/motion_retarget_cases.gd','--','--report='+str(a.report.resolve())],'qa.log')]
    for command,filename in commands:
        with (work/filename).open('w') as log:
            result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        content=(work/filename).read_text()
        if result.returncode or 'SCRIPT ERROR:' in content or '\nERROR:' in content:
            print(json.dumps({'passed':False,'log':str(work/filename),'exit_code':result.returncode,'report':str(a.report)}))
            raise SystemExit(result.returncode or 1)
    report=json.loads(a.report.read_text())
    print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'report':str(a.report)}))

if __name__=='__main__': main()
