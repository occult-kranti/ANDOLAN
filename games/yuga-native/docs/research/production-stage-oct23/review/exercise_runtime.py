from pathlib import Path
import concurrent.futures, datetime, hashlib, http.client, importlib.util, json, os, subprocess, sys, threading
repo=Path('/workspace/ANDOLAN')
source=repo/'games/yuga-native/tools/build-observatory/observatory.py'
base=Path('/workspace/scratch/production-stage-oct23/review')
run=base/('runtime-'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S'))
run.mkdir()
spec=importlib.util.spec_from_file_location('review_observatory',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
state=m.state_directory(repo,run/'state')
m.update_state(state,initialize=('review-fixture','Independent route/identity review'))
web=run/'web';web.mkdir();(web/'index.html').write_text('<!doctype html><title>Review fixture</title>')
(web/'sample.ttf').write_bytes(b'fixture font')
(web/'outside-link.txt').symlink_to(base/'exercise_runtime.py')
observer=m.Observatory(repo,state);observer.web=web
server=m.make_server(observer,0)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
port=server.server_port
checks=[]
def check(name,condition,detail=None):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
def request(path,method='GET',host=None):
    c=http.client.HTTPConnection('127.0.0.1',port,timeout=8)
    c.request(method,path,headers={'Host':host or f'127.0.0.1:{port}'})
    r=c.getresponse();body=r.read();headers=dict(r.getheaders());status=r.status;c.close()
    return status,headers,body
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(45)'])
try:
    record={'kind':'job','id':'live-child','title':'Owned synthetic child','status':'running','device':'CPU','pid':child.pid,'summary':'Only a reviewer liveness fixture'}
    m.update_state(state,record)
    status,headers,body=request('/api/status');data=json.loads(body)
    j=next(x for x in data['jobs'] if x['id']=='live-child')
    check('live_api_owned_process_is_running',status==200 and data['mode']=='live' and j['status']=='running')
    check('api_redacts_process_identity', 'pid' not in json.dumps(j) and 'boot_id' not in json.dumps(j) and '_tracking' not in json.dumps(j))
    check('read_only_health_and_no_cors',request('/api/health')[0]==200 and not any(k.lower()=='access-control-allow-origin' for k in headers))
    check('host_rebinding_rejected',request('/api/status',host='untrusted.example')[0]==400)
    check('post_has_no_execution_route',request('/api/status','POST')[0]==405)
    check('unknown_api_rejected',request('/api/execute')[0]==404)
    for path in ['/../.git/config','/%2e%2e/.git/config','/%252e%252e/.git/config','/outside-link.txt']:
        s,h,b=request(path)
        check('path_boundary_'+path,s in {404,422} and b'/workspace/' not in b,{'status':s})
    s,h,b=request('/sample.ttf')
    check('ttf_served_with_font_mime',s==200 and h.get('Content-Type')=='font/ttf',{'status':s,'mime':h.get('Content-Type')})
    child.terminate();child.wait(timeout=5)
    data=json.loads(request('/api/status')[2]);j=next(x for x in data['jobs'] if x['id']=='live-child')
    check('ended_process_becomes_stale_not_complete',j['status']=='stale')
    # Explicit old receive time is fixture input for expiration; no sleep/clock edit.
    m.update_state(state,{'id':'heartbeat','title':'Expired fixture','status':'running','device':'CPU','heartbeat_ttl_seconds':5})
    with m.locked(state):
        d=m.read_json(state/'state.json')
        next(x for x in d['jobs'] if x['id']=='heartbeat')['_tracking']['received_at']='2000-01-01T00:00:00+00:00'
        m.atomic_json(state/'state.json',d)
    snap=observer.snapshot('snapshot')
    check('expired_heartbeat_stale_in_snapshot',snap['mode']=='snapshot' and next(x for x in snap['jobs'] if x['id']=='heartbeat')['status']=='stale')
    # Actual separate CLI emit processes must preserve each other's events.
    records=[]
    for n in range(8):
        p=run/f'event-{n}.json';p.write_text(json.dumps({'id':f'parallel-{n}','title':'Concurrent review fixture','status':'queued','device':'CPU'}));records.append(p)
    def emit(p):
        return subprocess.run([sys.executable,str(source),'emit','--workspace',str(repo),'--state-dir',str(state),'--record',str(p)],capture_output=True,text=True,timeout=12).returncode
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: codes=list(ex.map(emit,records))
    ids={x['id'] for x in m.read_json(state/'state.json')['jobs']}
    check('eight_real_concurrent_cli_emits_preserved',codes==[0]*8 and all(f'parallel-{n}' in ids for n in range(8)),{'exit_codes':codes})
    out=run/'snapshot.json'
    r=subprocess.run([sys.executable,str(source),'export','--workspace',str(repo),'--state-dir',str(state),'--output',str(out)],capture_output=True,text=True,timeout=12)
    d=json.loads(out.read_text()) if out.exists() else {}
    check('actual_cli_export_is_dated_snapshot',r.returncode==0 and d.get('mode')=='snapshot' and bool(d.get('collected_at')))
    for name,bad in [('completion_without_evidence',{'id':'bad','status':'complete','summary':'Done'}),('running_without_liveness',{'id':'bad','status':'running'}),('javascript_artifact',{'id':'bad','status':'review','outputs':[{'url':'javascript:alert(1)'}]})]:
        try:m.update_state(state,bad)
        except ValueError:check(name,True)
        else:check(name,False)
finally:
    if child.poll() is None:child.terminate();child.wait(timeout=5)
    server.shutdown();server.server_close();thread.join(timeout=3)
result={'schema_version':1,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source.relative_to(repo)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Independent real localhost server/CLI routes, process liveness, concurrent writes and snapshot semantics. Synthetic jobs only; no model or GPU execution.','checks':checks,'passed':all(x['passed'] for x in checks),'fixture_root':str(run),'server_stopped':True,'owned_child_stopped':child.poll() is not None}
(run/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
