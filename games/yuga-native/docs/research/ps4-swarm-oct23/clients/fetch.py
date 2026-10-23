import urllib.request,pathlib,json,hashlib,sys
p=pathlib.Path(__file__).parent;f=p/'source-ledger.json';d=json.loads(f.read_text())
for l in sys.stdin:
 if not l.strip():continue
 name,url=l.strip().split(' ',1)
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Codex-docs-review'}),timeout=25) as r:b=r.read(120001)
  if len(b)>120000:raise ValueError('response cap exceeded')
  (p/'sources'/name).write_bytes(b);row={'file':'sources/'+name,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'status':'retrieved'}
  print(name,len(b))
 except Exception as e:row={'url':url,'status':'failed','error':str(e)};print(name,type(e).__name__,str(e))
 d['sources'].append(row);f.write_text(json.dumps(d,indent=2)+'\n')
