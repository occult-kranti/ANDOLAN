#!/usr/bin/env python3
"""One immutable current-source content store; no import, scene, or engine."""
import hashlib,importlib.util,json,os,shutil,time
from pathlib import Path
ROOT=Path('/workspace/scratch/yuga-frontage-review-r1')
SRC=Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN/games/yuga-native')
EXPORT=Path('/workspace/scratch/yuga-desktop-integrated-package-r4/build/native-export-manifest.json')
TOOL=Path('/workspace/ANDOLAN/games/yuga-native/tools/graphics-six/snapshot.py')
STORE=ROOT/'store'
FLOOR=500*1024*1024
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def free():return shutil.disk_usage(ROOT).free
def put(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
assert not STORE.exists(),'Use a fresh store, never overwrite immutable objects'
assert sha(EXPORT)=='4cb3316300092dcdb99016f3c0e6f024066df2f94999a3b7b4944247870aa4a7'
spec=importlib.util.spec_from_file_location('snapshot',TOOL);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
before=m.inventory(SRC);imports=m.imports(SRC)
export=json.loads(EXPORT.read_text());assert len(export['source']['files'])==552
assert all(before.get(n)==v for n,v in export['source']['files'].items())
total=sum(v['bytes']for v in before.values())
initial=free();assert initial-total>=FLOOR+147*1024*1024+80*1024*1024,'Insufficient reserve for transport/render after source store'
STORE.mkdir();copied={};paths={};began=time.time()
for n,meta in before.items():
 assert free()>=FLOOR,'Stop before storage floor'
 bucket='imports' if n.startswith('.godot/imported/') else 'sources'
 p=STORE/bucket/meta['sha256'];p.parent.mkdir(exist_ok=True)
 if not p.exists():
  shutil.copyfile(SRC/n,p);assert m.metadata(p)==meta;p.chmod(0o444);copied[str(p.relative_to(STORE))]=meta
 else:assert m.metadata(p)==meta
 assert p.stat().st_ino!=(SRC/n).stat().st_ino or p.stat().st_dev!=(SRC/n).stat().st_dev
 paths[n]=str(p.relative_to(STORE))
assert m.inventory(SRC)==before
assert all(m.metadata(STORE/p)==before[n] for n,p in paths.items())
data={'passed':True,'source_commit':'96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12','source':str(SRC),'export_manifest_sha256':sha(EXPORT),'snapshot_tool_sha256':sha(TOOL),'snapshot_tool_path':str(TOOL),'source_inventory':before,'validated_imports':imports,'source_file_count':len(before),'runtime_file_count':552,'import_count':len(imports),'file_objects':paths,'unique_objects':copied,'unique_copied_bytes':sum(v['bytes']for v in copied.values()),'source_logical_bytes':total,'free_before':initial,'free_after':free(),'minimum_reserve_bytes':FLOOR,'elapsed_seconds':time.time()-began,'no_source_import_mutation':True,'no_engine':True,'scope':'One copied read-only content store on workspace; not a full Git clone. Later siblings hardlink only these new immutable objects. Metadata uses private copies.'}
put(ROOT/'store-preparation.json',data)
print(json.dumps({k:data[k]for k in ['passed','source_file_count','import_count','unique_copied_bytes','free_after','elapsed_seconds']}))
