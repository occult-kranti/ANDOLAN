#!/usr/bin/env python3
"""One read-only status snapshot; caller controls polling interval."""
import concurrent.futures,datetime,json,pathlib,urllib.request,urllib.error
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
root=pathlib.Path('/workspace/scratch/yuga-siege/status-'+stamp);root.mkdir()
base='https://api.github.com/repos/occult-kranti/ANDOLAN'
urls={'jobs':base+'/actions/runs/39011346041/jobs?per_page=100','release':base+'/releases/tags/yuga-traversal-armies-2026-10-17-siege'}
def get(item):
 name,url=item
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','User-Agent':'YUGA-public-verification'}),timeout=30) as r:
   data=json.load(r);status=r.status
 except urllib.error.HTTPError as e:
  status=e.code;data=json.loads(e.read())
 (root/(name+'.json')).write_text(json.dumps({'checked_at':stamp,'http_status':status,'data':data},indent=2))
 if name=='runs': summary=[{k:r.get(k) for k in ['id','name','event','head_sha','status','conclusion','html_url']} for r in data.get('workflow_runs',[])]
 elif name=='jobs': summary=[{'id':r['id'],'name':r['name'],'status':r['status'],'conclusion':r['conclusion'],'steps':[{'name':s['name'],'status':s['status'],'conclusion':s['conclusion']} for s in r.get('steps',[]) if s['status'] not in ['queued','pending']]} for r in data.get('jobs',[])]
 else: summary={k:data.get(k) for k in ['id','tag_name','draft','prerelease','published_at','message']};summary['asset_count']=len(data.get('assets',[]))
 return {'kind':name,'status':status,'summary':summary,'evidence':str(root/(name+'.json'))}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for result in pool.map(get,urls.items()): print(json.dumps(result))
