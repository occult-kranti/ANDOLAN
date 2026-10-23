import urllib.request,pathlib,json,hashlib,sys
base=pathlib.Path(__file__).parent
manifest=base/'fetched.json'
records=json.loads(manifest.read_text()) if manifest.exists() else []
for line in sys.stdin:
 if not line.strip():continue
 name,url=line.strip().split(' ',1)
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Codex-docs-review'}),timeout=30) as r:data=r.read(180001)
  if len(data)>180000:raise ValueError('180KB response cap exceeded')
  dest=base/'sources'/name;dest.write_bytes(data)
  record={'file':str(dest.relative_to(base)),'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()};records.append(record)
  print(name,len(data))
 except Exception as e:print(name,type(e).__name__,str(e))
 manifest.write_text(json.dumps(records,indent=2)+'\n')
