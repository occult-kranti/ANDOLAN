#!/usr/bin/env python3
"""Make one fixed frontage pair from the already verified96d5 content store."""
import argparse,hashlib,importlib.util,json,os,shutil,difflib
from pathlib import Path
ROOT=Path('/workspace/scratch/yuga-frontage-review-r1')
NATIVE=Path('/workspace/ANDOLAN/games/yuga-native')
STORE=ROOT/'store'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return {'sha256':sha(p),'bytes':Path(p).stat().st_size}
def put(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
p=argparse.ArgumentParser();p.add_argument('--helper',type=Path,required=True);a=p.parse_args()
prep=json.loads((ROOT/'store-preparation.json').read_text());assert prep['passed']
assert shutil.disk_usage(ROOT).free>500*1024*1024+100*1024*1024
assert all(meta(STORE/n)==v for n,v in prep['unique_objects'].items())
h=ROOT/'harness';h.mkdir()
ancestor=NATIVE/'art/world-finish/overview-render-r1'
shutil.copy2(ancestor/'run_focus.py',h/'run_focus.py')
stock=(ancestor/'snapshot.py').read_text()
old="ROOT_FILES = ('project.godot', 'export_presets.cfg', 'art/world/confluence-map.json',"
new=old+"\n              'art/world-finish/lane-frontage-r1/candidate.gd',\n              'art/world-finish/lane-frontage-r1/candidate-mesh.json',"
assert stock.count(old)==1
patched=stock.replace(old,new)
(h/'snapshot.py').write_text(patched)
(h/'snapshot-scope.patch').write_text(''.join(difflib.unified_diff(stock.splitlines(True),patched.splitlines(True),fromfile='original-snapshot.py',tofile='frontage-snapshot.py')))
spec=importlib.util.spec_from_file_location('frontage_snapshot',h/'snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
common={
 'tools/graphics-six/capture_scene_anchors.gd':a.helper.resolve(),
 'art/world-finish/lane-frontage-r1/candidate.gd':NATIVE/'art/world-finish/lane-frontage-r1/candidate.gd',
 'art/world-finish/lane-frontage-r1/candidate-mesh.json':NATIVE/'art/world-finish/lane-frontage-r1/candidate-mesh.json'}
assert sha(common['art/world-finish/lane-frontage-r1/candidate.gd'])=='cc78e2b941c175ad535cb317619f4282a1a6a06d3ce040fbabcfb31af6f1b924'
assert sha(common['art/world-finish/lane-frontage-r1/candidate-mesh.json'])=='117123f32c232dc2c2693bbf0180578feb85396fcddaf1518b7c6d653698f141'
commonpins={n:meta(src)for n,src in common.items()}
for n,src in common.items():
 blob=STORE/'sources'/sha(src)
 if not blob.exists():shutil.copyfile(src,blob);blob.chmod(0o444)
 assert meta(blob)==commonpins[n]
records={};ownership={}
for branch in ['baseline','candidate']:
 project=ROOT/branch;assert not project.exists();project.mkdir()
 expected=dict(prep['source_inventory']);expected.update(commonpins)
 aux=[]
 for n,v in expected.items():
  dest=project/n;dest.parent.mkdir(parents=True,exist_ok=True)
  blob=STORE/('imports'if n.startswith('.godot/imported/')else'sources')/v['sha256']
  if n in m.AUX_FILES:
   shutil.copyfile(blob,dest);dest.chmod(0o644);aux.append(n)
  else:os.link(blob,dest)
 selector=project/'tools/visual-rounds/frontage-review.json';put(selector,{'branch':branch});selector.chmod(0o444)
 expected[str(selector.relative_to(project))]=meta(selector)
 actual=m.inventory(project);assert actual==expected
 record={'schema':1,'round':'G6-frontage-'+branch+'-r1','source_commit':prep['source_commit'],'source':prep['source'],'project':str(project),'store':str(STORE),'files':actual,'validated_imports':prep['validated_imports'],'source_bytes':sum(v['bytes']for n,v in actual.items()if not n.startswith('.godot/')),'compiled_bytes':sum(v['bytes']for n,v in actual.items()if n.startswith('.godot/imported/')),'branch':branch,'source_store_receipt_sha256':sha(ROOT/'store-preparation.json'),'common_harness_overlay':commonpins,'scope':'Exact96d5source with common review helper and inactive candidate inputs; only branch JSON selects replacement. Auxiliary metadata private; all other files immutable store hardlinks. No import or canonical mutation.'}
 put(project/m.MARKER,record);m.verify(project)
 checks=[]
 for n in actual:
  if n=='tools/visual-rounds/frontage-review.json':continue
  dest=project/n;blob=STORE/('imports'if n.startswith('.godot/imported/')else'sources')/actual[n]['sha256']
  checks.append((dest.stat().st_ino!=blob.stat().st_ino) if n in aux else (dest.stat().st_ino==blob.stat().st_ino and not dest.stat().st_mode&0o222))
 assert all(checks)
 ownership[branch]={'checks':len(checks),'passed':True,'private_auxiliary':aux,'metadata_marker_private':True,'source_files':len(actual)}
 records[branch]={'project':str(project),'marker_sha256':sha(project/m.MARKER),'record':record}
aa=records['baseline']['record']['files'];bb=records['candidate']['record']['files'];d=[n for n in aa.keys()|bb.keys()if aa.get(n)!=bb.get(n)]
assert d==['tools/visual-rounds/frontage-review.json']
assert all(meta(STORE/n)==v for n,v in prep['unique_objects'].items())
assert all(meta(src)==commonpins[n]for n,src in common.items())
put(ROOT/'pair-staging.json',{'passed':True,'source_commit':prep['source_commit'],'store_preparation_sha256':sha(ROOT/'store-preparation.json'),'records':records,'declared_only_branch_difference':d,'ownership':ownership,'runner':meta(h/'run_focus.py'),'snapshot_adapter':meta(h/'snapshot.py'),'common_inputs':commonpins,'free_after':shutil.disk_usage(ROOT).free,'no_engine':True,'no_import':True,'scope':'Source staging only. Headless preflight and actual paired originals remain required.'})
print(json.dumps({'passed':True,'markers':{b:v['marker_sha256']for b,v in records.items()},'source_files':len(aa),'branch_delta':d,'free_after':shutil.disk_usage(ROOT).free}))
