#!/usr/bin/env python3
from pathlib import Path,PurePosixPath
import hashlib,json,zipfile,stat
ROOT=Path('/workspaces/ANDOLAN');OUT=ROOT/'docs/research/video-study/final-independent-audit/r4';BUILD=Path('/workspaces/scratch/yuga-video-frozen-r1/build-r4')
pck=json.loads((OUT/'pck-source-audit.json').read_text());aggregate=json.loads((BUILD/'native-package-manifest.json').read_text())
expected={'linux':{'bytes':115178949,'sha256':'b49421501197edf225e9edcf2c2d229ced777c52d53aa33646139df428de998a'},'windows':{'bytes':163475846,'sha256':'50b4a974b8762cad3137c44ea109cee0fd646c6bc286b0eb407a0c61c80a16c4'}}
checks=[];archives={}
def check(name,passed,details=None):checks.append({'name':name,'passed':bool(passed),'details':details or {}})
def record(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return {'bytes':path.stat().st_size,'sha256':h.hexdigest()}
for platform in ['linux','windows']:
 path=BUILD/f'yuga-native-{platform}-x86_64.zip';before=record(path);prefix=f'yuga-native-{platform}-x86_64/'
 check(platform+' ZIP identity matches independently supplied build identity',before==expected[platform] and before=={k:aggregate['packages'][platform][k] for k in ['bytes','sha256']})
 with zipfile.ZipFile(path) as z:
  names=z.namelist();check(platform+' ZIP CRC validates every actual member',z.testzip() is None)
  safe=len(set(names))==len(names)
  for item in z.infolist():
   parts=PurePosixPath(item.filename);mode=item.external_attr>>16
   safe=safe and item.filename==parts.as_posix() and item.filename.startswith(prefix) and not parts.is_absolute() and '..' not in parts.parts and '\\' not in item.filename and not stat.S_ISLNK(mode) and not item.flag_bits&1
  check(platform+' ZIP has canonical unique unencrypted nonsymlink paths',safe)
  manifest_bytes=z.read(prefix+'PACKAGE-MANIFEST.json');manifest=json.loads(manifest_bytes)
  check(platform+' ZIP entry closure exactly equals manifest payloads plus manifest',set(names)=={prefix+p for p in manifest['payloads']}|{prefix+'PACKAGE-MANIFEST.json'})
  records={}
  for item in z.infolist():
   h=hashlib.sha256();count=0
   with z.open(item) as stream:
    for b in iter(lambda:stream.read(1024*1024),b''):h.update(b);count+=len(b)
   records[item.filename.removeprefix(prefix)]={'bytes':count,'sha256':h.hexdigest()}
  check(platform+' Every manifest payload byte count/SHA256 matches actual ZIP data',all(records[p]==r for p,r in manifest['payloads'].items()),{'payloads':len(manifest['payloads'])})
  check(platform+' ZIP PCK bytes match independently audited standalone PCK',records['yuga-native.pck']=={k:pck['packs'][platform][k] for k in ['bytes','sha256']})
  check(platform+' ZIP manifest PCK directory exactly matches independently parsed PCK',manifest['pck']['entry_count']==len(pck['packs'][platform]['entries']) and {r['path']:(r['bytes'],r['sha256']) for r in manifest['pck']['entries']}=={r['path']:(r['bytes'],r['sha256']) for r in pck['packs'][platform]['entries']})
  check(platform+' ZIP manifest source_state equals independently hashed frozen622files',manifest['runtime_source']['sha256']==pck['source_state_sha256'] and manifest['runtime_source']['files']==pck['source_files'])
  check(platform+' ZIP native contract proof equals independently hashed46input closure',manifest['native_contracts']['sources']==pck['native_contract_inputs'])
  runtime='godot' if platform=='linux' else 'godot.exe'
  check(platform+' Bundled runtime matches manifest identity',records[runtime]=={k:manifest['runtime'][k] for k in ['bytes','sha256']})
  if platform=='linux':check('Linux launch/runtime executable bits retained',all((z.getinfo(prefix+p).external_attr>>16)&0o111 for p in ['godot','launch.sh']))
  check(platform+' Required notices are actual packaged payloads',all('NOTICE/'+n in records for n in ['GODOT-LICENSE.txt','GODOT-COPYRIGHT.txt','MAKEHUMAN-ASSET-LICENSE.md','ASSET-NOTICE.md','STUDIO_SOURCES.md']))
  check(platform+' Package truthfully declares it was not executed by packager',manifest['execution_status']=='not_executed_by_packager')
  archives[platform]={'path':str(path),**before,'entry_count':len(names),'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),'payloads':records,'engine':manifest['runtime'],'baseline_commit':manifest['git']['head'],'source_state_sha256':manifest['runtime_source']['sha256']}
 check(platform+' ZIP unchanged during independent audit',record(path)==before)
result={'task_id':'FINAL-INDEPENDENT-AUDIT-01','passed':all(c['passed'] for c in checks),'checks':checks,'archives':archives,'scope':'Independent actual ZIP CRC, streamed member hashes, full manifest closure, executable modes, notices, PCK/source/contract proof consistency. Archive validation does not establish runtime input, visuals, hardware performance or Windows execution.'}
(OUT/'zip-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[c for c in checks if not c['passed']],'zip_entries':{k:v['entry_count'] for k,v in archives.items()}},indent=2))
