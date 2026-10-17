import datetime,hashlib,json,pathlib,shutil,subprocess,time
root=pathlib.Path('/workspace/ANDOLAN'); project=root/'games/yuga-native'; out=pathlib.Path('/workspace/scratch/visual-round2/role-11'); durable=project/'docs/evidence/visual-rounds/round2/role11'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
fixture=json.loads((project/'docs/evidence/visual-rounds/round2/role04/face-action-fixtures.json').read_text())
paths=[r['path'] for r in fixture['source_pins']]+['tests/rama_effect_adversarial_cases.gd','tests/rama_ability_cases.gd','tests/rama_vfx_quality_cases.gd','tests/rama_ability_visual_cases.gd','shaders/rama_ability_calligraphy.gdshader','shaders/rama_ribbon.gdshader']
before={p:sha(project/p) for p in paths};receipts=[]
for label,script in [('adversarial','rama_effect_adversarial_cases'),('abilities','rama_ability_cases'),('vfx','rama_vfx_quality_cases'),('visual','rama_ability_visual_cases')]:
 report=out/(label+'.json');cmd=['taskset','-c','0,1','godot','--headless','--path',str(project),'--script','res://tests/'+script+'.gd','--','--report='+str(report)]
 start=time.monotonic();result=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=80)
 (out/(label+'.stdout.log')).write_text(result.stdout);(out/(label+'.stderr.log')).write_text(result.stderr)
 data=json.loads(report.read_text()) if report.exists() else {};checks=data.get('checks',[])
 receipt={'label':label,'command':cmd,'exit_code':result.returncode,'seconds':time.monotonic()-start,'passed':data.get('passed'),'checks':len(checks) if isinstance(checks,list) else checks,'report_sha256':sha(report) if report.exists() else None,'stderr_bytes':len(result.stderr.encode())};receipts.append(receipt);print(json.dumps(receipt),flush=True)
 for p in [report,out/(label+'.stdout.log'),out/(label+'.stderr.log')]:
  if p.exists():shutil.copy2(p,durable/p.name)
after={p:sha(project/p) for p in paths}
r={'schema':1,'task_id':'R2-11','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'receipts':receipts,'source_before_sha256':before,'source_after_sha256':after,'source_unchanged':before==after,'all_passed':all(x['exit_code']==0 and x['passed'] for x in receipts),'scope':'Existing event/VFX suites only, no import, render or candidate pixel acceptance.'}
(out/'run.json').write_text(json.dumps(r,indent=2)+'\n');shutil.copy2(out/'run.json',durable/'run.json');shutil.copy2(__file__,durable/'run-review.py')
