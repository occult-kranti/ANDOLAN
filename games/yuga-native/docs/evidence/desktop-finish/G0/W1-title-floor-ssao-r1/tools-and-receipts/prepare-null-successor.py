import json,os,shutil,sys,difflib
from pathlib import Path
E=Path('/tmp/yuga-floor-ao-r1/evidence');sys.path.insert(0,str(E/'tools'));import snapshot
helper='tools/graphics-six/capture_scene_anchors.gd';old=(E/'capture_floor_ao.UNRUN.gd').read_text();needle='\t\tTYPE_OBJECT:\n';assert old.count(needle)==1
new=old.replace(needle,needle+'\t\t\tif value == null: return null\n');p=E/'capture_floor_ao-null-r2.gd';p.write_text(new);(E/'null-r2.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original86e',tofile='typed-null-r2')))
result={'scope':'Typed null Object serializes JSON null; nonnull unsupported, RID and depth guards retained. Original failed take/children unchanged.','branches':{}}
for branch in ['baseline','candidate']:
 src=Path('/tmp/yuga-floor-ao-r1')/(branch+'-project');record=snapshot.verify(src);dst=Path('/tmp/yuga-floor-ao-r1')/(branch+'-project-r2');assert not dst.exists()
 for name in record['files']:
  target=dst/name;target.parent.mkdir(parents=True,exist_ok=True)
  if name==helper:shutil.copyfile(p,target)
  elif name in snapshot.AUX_FILES:shutil.copyfile(src/name,target)
  else:os.link(src/name,target)
 record.update(project=str(dst),round='G6-floor-ao-null-r2-'+branch,previous_receipt_sha256=snapshot.digest(src/snapshot.MARKER));record['files'][helper]=snapshot.metadata(p);record['source_bytes']=sum(v['bytes']for k,v in record['files'].items()if not k.startswith('.godot/'))
 (dst/snapshot.MARKER).write_text(json.dumps(record,indent=2)+'\n');snapshot.verify(dst);snapshot.verify(src)
 result['branches'][branch]={'path':str(dst),'marker_sha256':snapshot.digest(dst/snapshot.MARKER)}
result['helper_sha256']=snapshot.digest(p);result['patch_sha256']=snapshot.digest(E/'null-r2.patch');(E/'null-r2-staging.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
