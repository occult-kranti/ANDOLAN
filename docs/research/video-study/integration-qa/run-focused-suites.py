#!/usr/bin/env python3
"""Read-only focused integration regression runner; no imports or rendering."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib,json,os,subprocess,time
ROOT=Path('/workspaces/ANDOLAN')
BASE=Path(__file__).resolve().parent
SUITES=['rama_ability_cases','rama_hero_integration_cases','siege_army_cases','input_binding_cases','ui_focus_recovery_cases','ui_pause_navigation_cases','siege_ui_cases']
SOURCES=['confluence_world.gd','rama_hero_runtime.gd','rama_vitals.gd','rama_ability_kit.gd','rama_ability_effects.gd','rama_motion.gd','rama_hero_hud.gd','rama_hero_panel.gd','lane_army.gd','lane_minion.gd','siege_effects.gd','input_bindings.gd','controls_overlay.gd','native_field_shop.gd','native_field_shop_panel.gd','combat_match_metrics.gd','world_outcome_summary.gd','confluence_battle_hud.gd','courtyard.gd']
PATHS=[ROOT/'games/yuga-native/scripts'/name for name in SOURCES]+[ROOT/'games/yuga-native/tests'/f'{name}.gd' for name in SUITES]+[ROOT/'games/yuga-native/assets/design/native-field-shop.json']
def hashes(): return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in PATHS}
before=hashes()
(BASE/'sources-before.json').write_text(json.dumps(before,indent=2)+'\n')
def run(name):
    folder=BASE/name;folder.mkdir(exist_ok=False)
    env=os.environ.copy();env['XDG_DATA_HOME']=str(folder/'user-data')
    command=['godot','--headless','--path','games/yuga-native','--script',f'res://tests/{name}.gd','--',f'--report={folder}/report.json']
    started=time.monotonic();timeout=False
    with (folder/'run.log').open('w') as log:
        try: result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240);code=result.returncode
        except subprocess.TimeoutExpired: code=None;timeout=True
    report_path=folder/'report.json';report=json.loads(report_path.read_text()) if report_path.exists() else None
    checks=report.get('checks',[]) if report else []
    result={'suite':name,'command':command,'environment':{'XDG_DATA_HOME':env['XDG_DATA_HOME']},'exit_code':code,'timeout':timeout,'wall_s':round(time.monotonic()-started,3),'report_exists':report is not None,'passed':code==0 and bool(report and report.get('passed')),'checks':len(checks),'failed_checks':[r for r in checks if not r.get('passed',False)],'log_sha256':hashlib.sha256((folder/'run.log').read_bytes()).hexdigest(),'report_sha256':hashlib.sha256(report_path.read_bytes()).hexdigest() if report_path.exists() else None}
    (folder/'execution.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
results=[]
with ThreadPoolExecutor(max_workers=2) as pool:
    pending={pool.submit(run,name):name for name in SUITES}
    for future in as_completed(pending):
        result=future.result();results.append(result)
        print(json.dumps({'suite':result['suite'],'passed':result['passed'],'checks':result['checks'],'exit_code':result['exit_code'],'wall_s':result['wall_s'],'failed_checks':result['failed_checks']}),flush=True)
after=hashes();(BASE/'sources-after.json').write_text(json.dumps(after,indent=2)+'\n')
index={'passed':all(r['passed'] for r in results) and before==after,'source_unchanged':before==after,'source_before':before,'source_after':after,'results':sorted(results,key=lambda r:SUITES.index(r['suite'])),'scope':'Existing focused headless real-simulation/native-Control regressions. Isolated user data per suite; no import, rendering, exports, OS-window input or GPU performance claims.'}
(BASE/'existing-suites-index.json').write_text(json.dumps(index,indent=2)+'\n')
print(json.dumps({'complete':True,'passed':index['passed'],'source_unchanged':index['source_unchanged'],'suites':len(results),'checks':sum(r['checks'] for r in results)}),flush=True)
