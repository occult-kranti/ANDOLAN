"""Independent package preflight binding/early-path probes; no Godot/export."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,tempfile
from types import SimpleNamespace
PROJECT=Path('/workspace/ANDOLAN/games/yuga-native');OUT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('package_independent',PROJECT/'tools/package-native.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[];pins=m._native_contract_inputs(PROJECT)
def ck(name,ok,detail=''):checks.append({'name':name,'passed':bool(ok),'detail':detail})
catalog=json.loads((PROJECT/'assets/contracts/native-contracts-v1.json').read_text())
expected={path for p in catalog['profiles'] for path in p['content_sources']}
expected.update(['games/yuga/shared/map.ts','games/yuga/shared/types.ts','games/yuga-native/assets/world/confluence-map.json','games/yuga-native/docs/GAME_DESIGN_MASTER.md','games/yuga-native/scripts/relay_control.gd'])
expected.update('games/yuga-native/'+p for p in ['tools/package-native.py','tools/check-native-contracts.py','scripts/native_contracts.gd','assets/contracts/native-contracts-v1.json','assets/contracts/native-envelope-v1.schema.json'])
expected.update(f'games/yuga-native/tests/fixtures/contracts/native-content{r}-{kind}.json' for r in (3,4,5) for kind in ['catalog','descriptor'])
ck('source closure includes every current checker input and historical fixture exactly',set(pins)==expected)
with tempfile.TemporaryDirectory(prefix='i3-independent-contract-') as td:
    repo=Path(td)/'repo';project=repo/'games/yuga-native'
    for path in pins:
        target=repo/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(PROJECT.parents[1]/path,target)
    counter=0
    def output():
        global counter
        counter+=1;return Path(td)/f'case-{counter}'/'proof.json'
    first=m.prove_native_contract_sources(output(),project)
    ck('actual current checker executes51 checks and binds exact closure',first['checks']==51 and first['sources']==pins)
    original_run=m.subprocess.run
    def reject(name,call,needle):
        try:call();ck(name,False,'unexpected success')
        except ValueError as e:ck(name,needle in str(e),str(e))
    fixture=project/'tests/fixtures/contracts/native-content5-descriptor.json';fixture_bytes=fixture.read_bytes()
    def mutate_after_checker(*args,**kwargs):
        result=original_run(*args,**kwargs);fixture.write_bytes(fixture_bytes+b'\n');return result
    m.subprocess.run=mutate_after_checker
    try:reject('fixture mutation after successful checker rejects closing binding',lambda:m.prove_native_contract_sources(output(),project),'report/source bindings changed')
    finally:m.subprocess.run=original_run;fixture.write_bytes(fixture_bytes)
    def rewrite_report(mode):
        def operation(*args,**kwargs):
            result=original_run(*args,**kwargs);command=args[0];path=Path(command[command.index('--report')+1]);report=json.loads(path.read_text())
            if mode=='source':report['source_sha256'].pop('games/yuga-native/scripts/native_contracts.gd')
            else:report['checks'].append(report['checks'][0])
            path.write_text(json.dumps(report));return result
        return operation
    for mode,needle in [('source','report/source bindings changed'),('duplicate','omits required source checks')]:
        m.subprocess.run=rewrite_report(mode)
        try:reject('successful report rejects '+mode+' tampering',lambda:m.prove_native_contract_sources(output(),project),needle)
        finally:m.subprocess.run=original_run
    player=project/'scripts/player.gd';player.write_bytes(player.read_bytes()+b'\n# isolated stale pin\n');m.PROJECT=project
    reject('export checks stale source before accessing engine arguments',lambda:m.export_all(SimpleNamespace(),output().parent),'Native contract source check failed')
    reject('package checks stale source before accessing engine arguments',lambda:m.package_all(SimpleNamespace(),output().parent,{}),'Native contract source check failed')
m.PROJECT=PROJECT
result={'passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'package_sha256':hashlib.sha256((PROJECT/'tools/package-native.py').read_bytes()).hexdigest(),'checker_sha256':hashlib.sha256((PROJECT/'tools/check-native-contracts.py').read_bytes()).hexdigest(),'source_count':len(pins),'scope':'Independent actual Python checker and isolated source closure; post-check mutation/report tampering and early entrypoint rejection. No Godot/import/export or actual package qualification.'}
(OUT/'contract-preflight-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
