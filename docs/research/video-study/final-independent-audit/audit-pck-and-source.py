#!/usr/bin/env python3
"""Independent streaming source/PCK reader. Does not invoke the packager."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,mmap,struct
parser=argparse.ArgumentParser();parser.add_argument('--snapshot',type=Path,required=True);parser.add_argument('--build',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
root=args.snapshot;project=root/'games/yuga-native';build=args.build;output=args.output;output.mkdir(parents=True,exist_ok=True)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def record(path):return {'bytes':path.stat().st_size,'sha256':digest(path)}
export_path=build/'native-export-manifest.json';export_bytes=export_path.read_bytes();export=json.loads(export_bytes)
source_paths=[]
for folder in ['scripts','shaders','scenes','assets']:source_paths.extend(p for p in (project/folder).rglob('*') if p.is_file())
source_paths.extend([project/'project.godot',project/'export_presets.cfg'])
actual_source={str(p.relative_to(project)):record(p) for p in sorted(source_paths)}
source_signature=hashlib.sha256(json.dumps(actual_source,sort_keys=True).encode()).hexdigest()
checks=[]
def check(name,passed,details=None):checks.append({'name':name,'passed':bool(passed),'details':details or {}})
check('Frozen source file set and every byte/hash match export source_state',actual_source==export['source']['files'],{'files':len(actual_source),'bytes':sum(v['bytes'] for v in actual_source.values())})
check('Independently recomputed source_state aggregate matches',source_signature==export['source']['sha256'],{'sha256':source_signature})
closure={p:record(root/p) for p in export['native_contracts']['sources']}
check('Every finite native-contract source-proof input matches current snapshot',closure==export['native_contracts']['sources'],{'inputs':len(closure)})
catalog=json.loads((project/'assets/contracts/native-contracts-v1.json').read_text());profile=catalog['profiles'][1]
old=json.loads((project/'tests/fixtures/contracts/native-content9-catalog.json').read_text())['profiles'][1]
check('Effective native content10 has19sources and preserves previous17pins',profile['content_revision']==10 and len(profile['content_sources'])==19 and len(old['content_sources'])==17 and all(profile['content_sources'].get(p)==h for p,h in old['content_sources'].items()))
check('Catalog content-source ledger matches actual frozen bytes',all(digest(root/p)==sha for p,sha in profile['content_sources'].items()))
check('Canonical catalog content digest matches19source ledger',hashlib.sha256(json.dumps(profile['content_sources'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==profile['content_sha256'])
pack_reports={}
critical=['assets/contracts/native-contracts-v1.json','assets/world/sangam-district.json','assets/design/native-field-shop.json','shaders/sangam_masonry.gdshader']
for platform in ['linux','windows']:
 path=build/f'yuga-native-{platform}.pck';before=record(path);entries=[];payloads={};ranges=[]
 with path.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as data:
  assert data[:4]==b'GDPC','PCKmagic'
  version,major,minor,patch,flags=struct.unpack_from('<5I',data,4);assert version in [2,3] and (major,minor,patch)==(4,6,3) and not flags&~2
  file_base=struct.unpack_from('<Q',data,24)[0];pos=struct.unpack_from('<Q',data,32)[0] if version==3 else 96
  count=struct.unpack_from('<I',data,pos)[0];pos+=4;assert 10<=count<=10000
  seen=set()
  for index in range(count):
   length=struct.unpack_from('<I',data,pos)[0];pos+=4;assert 1<=length<=4096 and pos+length+36<=len(data)
   name=data[pos:pos+length].rstrip(b'\0').decode();pos+=length
   offset,size=struct.unpack_from('<QQ',data,pos);expected_md5=bytes(data[pos+16:pos+32]);entry_flags=struct.unpack_from('<I',data,pos+32)[0];pos+=36
   relative=name.removeprefix('res://');canonical=PurePosixPath(relative)
   assert relative==canonical.as_posix() and not canonical.is_absolute() and '..' not in canonical.parts and '\\' not in relative and relative not in seen and entry_flags==0
   seen.add(relative);start=file_base+offset;assert start>=0 and start+size<=len(data)
   md5=hashlib.md5();sha=hashlib.sha256()
   for cursor in range(start,start+size,1024*1024):
    block=data[cursor:min(cursor+1024*1024,start+size)];md5.update(block);sha.update(block)
   assert md5.digest()==expected_md5,relative
   row={'path':name,'bytes':size,'sha256':sha.hexdigest(),'stored_md5_verified':True};entries.append(row);ranges.append((start,start+size,relative))
   if relative in critical or relative in ['scripts/native_contracts.gd.remap','scripts/confluence_world.gd.remap','scripts/sangam_district.gd.remap','scripts/native_field_shop.gd.remap','scripts/combat_match_metrics.gd.remap']:payloads[relative]=bytes(data[start:start+size])
  ranges.sort();assert all(ranges[i][1]<=ranges[i+1][0] for i in range(len(ranges)-1))
 expected=export['packs'][platform];expected_entries={r['path']:{k:r[k] for k in ['bytes','sha256']} for r in expected['entries']};actual_entries={r['path']:{k:r[k] for k in ['bytes','sha256']} for r in entries}
 check(platform+' PCK exact identity matches export manifest',before=={k:expected[k] for k in ['bytes','sha256']} and count==expected['entry_count'])
 check(platform+' every PCK entry MD5 and independent SHA256 match export directory',actual_entries==expected_entries,{'entries':count,'nonoverlapping_payload_ranges':True})
 for relative in critical:
  check(platform+' direct critical source payload matches '+relative,relative in payloads and hashlib.sha256(payloads.get(relative,b'')).hexdigest()==actual_source[relative]['sha256'])
 for relative,payload in payloads.items():
  if relative.endswith('.gd.remap'):
   import re
   target=re.search(rb'path="res://([^"\r\n]+)"',payload)
   check(platform+' compiled script remap resolves '+relative,target is not None and target[1].decode() in {r['path'].removeprefix('res://') for r in entries})
 check(platform+' PCK unchanged during independent audit',record(path)==before)
 pack_reports[platform]={'path':str(path),**before,'entries':entries,'critical_packed_catalog':json.loads(payloads['assets/contracts/native-contracts-v1.json'])['profiles'][1]}
check('Linux and Windows PCKs share exact current payload identity',pack_reports['linux']['sha256']==pack_reports['windows']['sha256'])
check('Export manifest unchanged during independent audit',export_path.read_bytes()==export_bytes)
result={'task_id':'FINAL-INDEPENDENT-AUDIT-01','passed':all(c['passed'] for c in checks),'checks':checks,'snapshot':str(root),'build':str(build),'source_state_sha256':source_signature,'source_files':actual_source,'source_file_count':len(actual_source),'native_contract_inputs':closure,'export_manifest_sha256':hashlib.sha256(export_bytes).hexdigest(),'source_baseline_commit':export['git']['head'],'branch':export['git']['branch'],'git_snapshot_status_bytes':len(export['git'].get('native_worktree_status','').encode()),'packs':pack_reports,'scope':'Independent frozen source/contract closure hashing andPCKdirectory/payload integrity. Compiled GDScript hashes bind actual exported bytes; raw source equivalence is supplied by source-bound exporter metadata and separately tested compiled contract probe, not decompilation. No render/import/export or runtime quality acceptance.'}
(output/'pck-source-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':[c for c in checks if not c['passed']],'source_files':len(actual_source),'contract_inputs':len(closure),'pck_entries':{p:len(d['entries']) for p,d in pack_reports.items()},'source_state_sha256':source_signature},indent=2))
