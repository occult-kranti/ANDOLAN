import json,pathlib,hashlib,sys,subprocess,shutil,datetime
root=pathlib.Path(__file__).parent
branch=sys.argv[1];assert branch in ('baseline','candidate')
inputs=json.loads((root/'execution-inputs.json').read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert shutil.disk_usage('/workspace').free >= inputs['limits']['minimum_workspace_free_bytes']
engine=pathlib.Path(inputs['engine']['path']);assert digest(engine)==inputs['engine']['sha256']
for seed in inputs['cache_seeds'].values():
 p=pathlib.Path(seed['path']);actual={str(f.relative_to(p)):{'bytes':f.stat().st_size,'sha256':digest(f)} for f in p.rglob('*') if f.is_file()};assert actual==seed['files']
commands=json.loads((root/'commands.UNRUN.json').read_text())['commands'];cmd=commands[branch+'-render'];cmd[cmd.index('--project')+1]=str(root/(branch+'-r4'))
out=pathlib.Path(cmd[cmd.index('--output')+1]);assert not out.exists()
record={'argv':cmd,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'engine':inputs['engine'],'common_helper_sha256':digest(root/(branch+'-r4/tools/graphics-six/capture_scene_anchors.gd')),'marker_sha256':digest(root/(branch+'-r4/.graphics-six-snapshot.json')),'runner_sha256':digest(root/'harness/run_focus.py'),'execution_inputs_sha256':digest(root/'execution-inputs.json'),'workspace_free_before':shutil.disk_usage('/workspace').free}
recordpath=root/(branch+'-render-execution-r1.json');assert not recordpath.exists();recordpath.write_text(json.dumps(record,indent=2)+'\n')
with (root/(branch+'-render-wrapper-r1.log')).open('wb') as log:
 p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);record['runner_pid']=p.pid;recordpath.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'pid':p.pid,'output':str(out),'record':str(recordpath)}),flush=True);code=p.wait()
record.update(exit_code=code,end_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workspace_free_after=shutil.disk_usage('/workspace').free);recordpath.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'exit':code,'output':str(out)}),flush=True);raise SystemExit(code)
