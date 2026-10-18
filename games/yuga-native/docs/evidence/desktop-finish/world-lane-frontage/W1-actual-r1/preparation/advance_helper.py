#!/usr/bin/env python3
"""Preserve one failed pair; replace only its shared capture helper in fresh children."""
import argparse,hashlib,importlib.util,json,os,shutil
from pathlib import Path
ROOT=Path('/workspace/scratch/yuga-frontage-review-r1')
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
p=argparse.ArgumentParser();p.add_argument('--helper',type=Path,required=True);p.add_argument('--from-suffix',default='');p.add_argument('--to-suffix',required=True);a=p.parse_args()
assert a.to_suffix.startswith('-r') and '/'not in a.to_suffix
spec=importlib.util.spec_from_file_location('snapshot',ROOT/'harness/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert shutil.disk_usage(ROOT).free>500*1024*1024+50*1024*1024
helper='tools/graphics-six/capture_scene_anchors.gd';item=m.metadata(a.helper)
blob=ROOT/'store/sources'/item['sha256']
if not blob.exists():shutil.copyfile(a.helper,blob);blob.chmod(0o444)
assert m.metadata(blob)==item
records={}
for branch in ['baseline','candidate']:
 old=ROOT/(branch+a.from_suffix);new=ROOT/(branch+a.to_suffix);assert not new.exists()
 prior=m.verify(old);new.mkdir();expected=dict(prior['files']);expected[helper]=item
 for n,v in expected.items():
  target=new/n;target.parent.mkdir(parents=True,exist_ok=True)
  origin=blob if n==helper else old/n
  if n in m.AUX_FILES or n=='tools/visual-rounds/frontage-review.json':shutil.copyfile(origin,target)
  else:os.link(origin,target)
 record=dict(prior);record.update(project=str(new),round=prior['round']+a.to_suffix,files=expected,previous_marker_sha256=sha(old/m.MARKER),helper_successor={'path':str(a.helper.resolve()),**item},source_bytes=sum(v['bytes']for n,v in expected.items()if not n.startswith('.godot/')))
 record['common_harness_overlay']=dict(record['common_harness_overlay']);record['common_harness_overlay'][helper]=item
 put(new/m.MARKER,record);m.verify(old);m.verify(new)
 delta=[n for n in expected if expected[n]!=prior['files'].get(n)];assert delta==[helper]
 records[branch]={'parent':str(old),'parent_marker_sha256':sha(old/m.MARKER),'project':str(new),'marker_sha256':sha(new/m.MARKER),'only_file_delta':delta}
put(ROOT/('helper-successor'+a.to_suffix+'.json'),{'passed':True,'helper':item,'records':records,'no_engine':True,'old_children_unchanged':True})
print(json.dumps(records))
