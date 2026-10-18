#!/usr/bin/env python3
"""Reserved-lane import refresh and independent CPU checks in a frozen runtime copy."""
import argparse, hashlib, json, os, pathlib, re, subprocess, time
P=pathlib.Path
p=argparse.ArgumentParser();p.add_argument('--project',type=P,required=True);p.add_argument('--output',type=P,required=True);a=p.parse_args()
project=a.project.resolve();out=a.output.resolve()
if not a.output.is_absolute() or out.exists():p.error('Use a fresh absolute output.')
out.mkdir(parents=True)
def save(name,value):(out/name).write_text(json.dumps(value,indent=2)+'\n')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def sources():return {str(f.relative_to(project)):sha(f) for f in project.rglob('*') if f.is_file() and '.godot' not in f.relative_to(project).parts}
def cache():return {str(f.relative_to(project)):sha(f) for f in (project/'.godot/imported').rglob('*') if f.is_file()}
def freshness():
    checks=[]
    for f in (project/'assets').rglob('*.import'):
        data=f.read_text();source=re.search(r'source_file="res://([^"]+)"',data);dest=re.search(r'^path="res://([^"]+)"',data,re.M)
        if not source or not dest:continue
        raw=project/source[1];md5=(project/dest[1]).with_suffix('.md5')
        stored=re.search(r'source_md5="([a-f0-9]+)"',md5.read_text()) if md5.exists() else None
        actual=hashlib.md5(raw.read_bytes()).hexdigest() if raw.exists() else None
        checks.append({'path':source[1],'raw_md5':actual,'cached_source_md5':stored[1] if stored else None,'matches':bool(stored and stored[1]==actual)})
    return checks
before=sources();before_cache=cache();save('source-before.json',before);save('cache-before.json',before_cache);save('freshness-before.json',freshness())
record={'project':str(project),'engine_sha256':sha(P('/usr/local/bin/godot')),'started_unix':time.time(),'runs':[]}
save('receipt.json',record)
def run(command,name):
    started=time.time()
    with (out/(name+'-output.txt')).open('w') as f:result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=os.environ.copy())
    entry={'name':name,'command':command,'exit_code':result.returncode,'seconds':time.time()-started,'log_sha256':sha(out/(name+'-output.txt'))}
    record['runs'].append(entry);save('receipt.json',record)
    log=(out/(name+'-output.txt')).read_text()
    if result.returncode or 'SCRIPT ERROR:' in log or '\nERROR:' in log:raise RuntimeError('Inspect '+name+' output')
    return entry
run(['taskset','-c','0,1','godot','--headless','--path',str(project),'--editor','--import','--quit','--max-threads','2'],'import')
after=sources();after_cache=cache();save('source-after-import.json',after);save('cache-after-import.json',after_cache)
changed=[f for f,h in before.items() if after.get(f)!=h];added=sorted(set(after)-set(before))
record.update(source_changes=changed,source_additions=added,cache_changes=[f for f,h in before_cache.items() if after_cache.get(f)!=h],cache_additions=sorted(set(after_cache)-set(before_cache)))
if any(not f.endswith(('.import','.uid')) for f in changed):raise RuntimeError('Unexpected authored source change')
checks=freshness();save('freshness-after.json',checks)
if not all(c['matches'] for c in checks):raise RuntimeError('Stale imports remain')
record['fresh_imports_verified']=len(checks);save('receipt.json',record)
for suite,count in [('ui_font_cases',7),('launch_shell_cases',None),('ui_end_to_end_cases',25),('ui_transition_lifecycle_cases',20)]:
    report=out/(suite+'.json')
    entry=run(['taskset','-c','0,1','godot','--headless','--path',str(project),'--script','res://tests/'+suite+'.gd','--','--report='+str(report)],suite)
    result=json.loads(report.read_text());checks_passed=sum(bool(c['passed']) for c in result['checks']);checks_failed=len(result['checks'])-checks_passed
    entry.update(passed=checks_passed,failed=checks_failed,report_sha256=sha(report))
    if (count is not None and checks_passed!=count) or checks_failed:raise RuntimeError('Test assertions failed')
record['source_unchanged_during_tests']=sources()==after
if not record['source_unchanged_during_tests']:raise RuntimeError('Test run changed source')
record['complete']=True;record['finished_unix']=time.time();save('receipt.json',record)
print(json.dumps({'complete':True,'fresh_imports':len(checks),'checks':sum(r.get('passed',0) for r in record['runs']),'output':str(out)}))
