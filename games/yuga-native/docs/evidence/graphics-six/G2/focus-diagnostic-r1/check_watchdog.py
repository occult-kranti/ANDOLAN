import importlib.util, json, os, sys, time
from pathlib import Path
root=Path('/tmp/yuga-g2-focus-harness-diagnosis-r1')
source=Path('/workspace/ANDOLAN/games/yuga-native/tools/graphics-six/run_focus.py')
spec=importlib.util.spec_from_file_location('focus_runner',source)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cases=[
 ('successful_ready',"print('YUGA_NATIVE_READY ok',flush=True); time.sleep(.4)",2,.6,None),
 ('ready_then_stall',"print('YUGA_NATIVE_READY ok',flush=True); time.sleep(10)",2,.3,'No new engine log'),
 ('never_ready',"time.sleep(10)",.6,.3,'Overall engine deadline'),
 ('split_ready',"print('YUGA_NATIVE_',end='',flush=True); time.sleep(.3); print('READY ok',flush=True); time.sleep(10)",2,.3,'No new engine log'),
 ('progress_extends_liveness',"print('YUGA_NATIVE_READY ok',flush=True)\nfor i in range(4):\n time.sleep(.3)\n print(i,flush=True)",3,.6,None),
]
results=[]
for name,code,deadline,progress,expected in cases:
 folder=root/name; folder.mkdir(); record={}; failure=None
 command=[sys.executable,'-u','-c','import time\n'+code]
 with (folder/'godot.log').open('x') as stream:
  try:
   m.run_engine(command,os.environ.copy(),stream,folder/'godot.log',folder/'images',deadline,progress,record)
  except TimeoutError as e: failure=str(e)
 try: os.kill(record['engine_pid'],0); alive=True
 except ProcessLookupError: alive=False
 passed=not alive and ((expected is None and failure is None and record['engine_exit']==0) or (expected is not None and failure is not None and expected in failure and record['engine_exit']!=0))
 results.append(dict(name=name,command=command,passed=passed,child_alive_after_return=alive,record=record,failure=failure))
report={'passed':all(c['passed'] for c in results),'count':len(results),'checks':results,'runner_sha256':m.sha(source)}
(root/'watchdog.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'count':len(results),'elapsed':[round(c['record']['engine_elapsed_s'],2) for c in results]}))
assert report['passed']
