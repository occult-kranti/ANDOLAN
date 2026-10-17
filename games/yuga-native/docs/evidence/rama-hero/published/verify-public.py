#!/usr/bin/env python3
"""Verify this release's public bytes against the frozen local upload manifest."""
import argparse, hashlib, importlib.util, json, subprocess, urllib.request, urllib.error, urllib.parse, zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--expected',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
x=json.loads(a.expected.read_text());a.output.mkdir(parents=True,exist_ok=False)
meta=json.loads(subprocess.check_output(['gh','api','repos/occult-kranti/ANDOLAN/releases/tags/'+x['tag']],text=True))
assert meta['draft'] is False and meta['tag_name']==x['tag']
ref=json.loads(subprocess.check_output(['gh','api','repos/occult-kranti/ANDOLAN/git/ref/tags/'+x['tag']],text=True))
assert ref['object']['type']=='commit' and ref['object']['sha']==x['source_commit']
assets={v['name']:v for v in meta['assets']};assert set(assets)==set(x['assets'])
rows={}
for name,e in x['assets'].items():
 assert Path(name).name==name and name not in ['.','..']
 remote=assets[name];assert remote['size']==e['bytes'] and remote['digest']=='sha256:'+e['sha256']
 h=hashlib.sha256();count=0;dest=a.output/name
 try:
  with urllib.request.urlopen(remote['browser_download_url'],timeout=60) as r,dest.open('xb') as f:
   while block:=r.read(1024*1024):h.update(block);f.write(block);count+=len(block)
 except urllib.error.HTTPError as err:
  raise SystemExit(json.dumps({'download_failed':name,'http_status':err.code,'host':urllib.parse.urlsplit(err.url).hostname}))
 assert h.hexdigest()==e['sha256'] and count==e['bytes'],name
 rows[name]={'bytes':count,'sha256':h.hexdigest(),'public_download_verified':True,'asset_id':remote['id']}
 print(json.dumps({'download_verified':name}),flush=True)
archives={}
for name in ('yuga-native-linux-x86_64.zip','yuga-native-windows-x86_64.zip'):
 with zipfile.ZipFile(a.output/name) as z:
  assert z.testzip() is None
  prefix=name[:-4]+'/'
  assert all(v.startswith(prefix) and not Path(v).is_absolute() and '..' not in Path(v).parts for v in z.namelist())
  manifest=json.loads(z.read(prefix+'PACKAGE-MANIFEST.json'));assert manifest['git']['head']==x['source_commit'] and manifest['git']['native_worktree_status']==''
  for member,e in manifest['payloads'].items():
   h=hashlib.sha256();n=0
   with z.open(prefix+member) as f:
    while block:=f.read(1024*1024):h.update(block);n+=len(block)
   assert h.hexdigest()==e['sha256'] and n==e['bytes'],member
  pack=a.output/(name[:-4]+'.pck');pack.write_bytes(z.read(prefix+'yuga-native.pck'))
  spec=importlib.util.spec_from_file_location('package_native',Path('games/yuga-native/tools/package-native.py').resolve());m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);r=m.inspect_pack(pack)
  assert r['sha256']==x['reviewed_pack_sha256']
  engine='godot' if 'linux' in name else 'godot.exe'
  if engine=='godot':assert manifest['payloads'][engine]['sha256']==x['reviewed_linux_engine_sha256']
  archives[name]={'crc_and_all_manifest_payload_hashes_verified':True,'payloads':len(manifest['payloads']),'pck_sha256':r['sha256'],'pck_entries':r['entry_count'],'source_commit':manifest['git']['head'],'runtime_source_sha256':manifest['runtime_source']['sha256']}
for name in ('rama-motion.mp4','rama-five-abilities.mp4'):
 subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-i',str(a.output/name),'-f','null','-'],check=True,stdout=subprocess.DEVNULL)
report={'passed':True,'source_commit':x['source_commit'],'tag':x['tag'],'url':meta['html_url'],'release_id':meta['id'],'assets':rows,'archives':archives,'linux_execution':'Public ZIP game pack and engine match the exact previously OS-reviewed bytes. This verification does not claim an additional OS-input run from this directory.','windows_execution':'UNRUN','media':'Both public MP4s fully decoded without error.','limits':['Offline preview; no commercial-game visual parity.','No physical-GPU or listening acceptance.']}
(a.output/'public-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'assets':len(rows),'url':meta['html_url']}))
