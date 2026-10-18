import hashlib, json, os, shutil, sys
from pathlib import Path

NATIVE=Path('/workspace/ANDOLAN/games/yuga-native')
SOURCE=Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN/games/yuga-native')
FROZEN=Path('/tmp/yuga-hair-r5-review-r1/baseline')
WORK=Path('/tmp/yuga-floor-ao-r1'); E=WORK/'evidence'
RECIPE=NATIVE/'art/world-finish/title-floor-ssao-plan-r1'
TOOLS=NATIVE/'docs/evidence/desktop-finish/G0/template-baseline-cold-600-r1/tools'
sys.path.insert(0,str(TOOLS)); import snapshot

def main():
 assert not (E/'staging.json').exists()
 assert shutil.disk_usage('/tmp').free>768*1024**2
 assert snapshot.digest(FROZEN/snapshot.MARKER)=='20aed49da1db66b48a2dcac9f0ced2afa9eb08753293a8bda943e7c256fab63e'
 frozen=snapshot.verify(FROZEN)
 source=snapshot.inventory(SOURCE); imports=snapshot.imports(SOURCE)
 export=json.loads(Path('/tmp/yuga-desktop-integrated-package-r3/build/native-export-manifest.json').read_text())
 assert export['git']['head']=='f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1'
 for name,item in export['source']['files'].items(): assert snapshot.metadata(SOURCE/name)==item,name
 recipe=json.loads((RECIPE/'recipe-source-only.json').read_text())
 for name,digest in recipe['artifacts'].items(): assert snapshot.digest(RECIPE/name)==digest,name
 for f in RECIPE.iterdir():
  if f.is_file():shutil.copy2(f,E/f.name)
 (E/'tools').mkdir()
 for name in ['snapshot.py','run_focus.py']: shutil.copy2(TOOLS/name,E/'tools'/name)
 assert snapshot.digest(E/'tools/run_focus.py')=='6cfcc86a3efb7ed1abb52f3df88a91b39027a88c7759fc70de4657302cfdc34c'
 original=(SOURCE/'scripts/hero_atmosphere.gd').read_bytes()
 assert hashlib.sha256(original).hexdigest()==recipe['baseline_script_sha256']
 old=b'"ssao_enabled": forward_plus, "ssao_radius": 0.28,'
 new=b'"ssao_enabled": false, "ssao_radius": 0.28,'
 assert original.count(old)==1
 candidate=original.replace(old,new)
 assert hashlib.sha256(candidate).hexdigest()==recipe['hypothetical_candidate_sha256']
 (E/'hero_atmosphere-ao-off.gd').write_bytes(candidate)
 helper='tools/graphics-six/capture_scene_anchors.gd'
 desired={**source,helper:snapshot.metadata(E/'capture_floor_ao.UNRUN.gd')}
 store=WORK/'store'; overlay=WORK/'frozen-inputs'; links={}; reused=[];copied=[]
 for name,item in desired.items():
  if name==helper:links[name]=E/'capture_floor_ao.UNRUN.gd';continue
  if name in frozen['files'] and frozen['files'][name]==item and name not in snapshot.AUX_FILES:
   links[name]=FROZEN/name;reused.append(name)
  else:
   target=overlay/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SOURCE/name,target)
   assert snapshot.metadata(target)==item;links[name]=target;copied.append(name)
 records={}
 for branch in ['baseline','candidate']:
  project=WORK/(branch+'-project');assert not project.exists();files=dict(desired);inputs=dict(links)
  if branch=='candidate':files['scripts/hero_atmosphere.gd']=snapshot.metadata(E/'hero_atmosphere-ao-off.gd');inputs['scripts/hero_atmosphere.gd']=E/'hero_atmosphere-ao-off.gd'
  for name,item in files.items():
   target=project/name;target.parent.mkdir(parents=True,exist_ok=True);origin=inputs[name]
   if name in snapshot.AUX_FILES:shutil.copyfile(origin,target)
   elif name.startswith('.godot/imported/'):
    blob=store/'imports'/item['sha256'];blob.parent.mkdir(parents=True,exist_ok=True)
    if not blob.exists():os.link(origin,blob)
    assert snapshot.metadata(blob)==item;os.link(blob,target)
   else:os.link(origin,target)
  record={'schema':1,'round':'G6-floor-ao-'+branch,'source':str(SOURCE),'source_commit':export['git']['head'],'project':str(project),'store':str(store),'files':files,'validated_imports':snapshot.imports(project),'source_bytes':sum(z['bytes']for n,z in files.items()if not n.startswith('.godot/')),'compiled_bytes':sum(z['bytes']for n,z in files.items()if n.startswith('.godot/imported/')),'scope':'Exact f8 runtime/tool/cache inventory with shared AO observer helper; candidate only SSAO enabled false. No import/canonical/clone writes.'}
  (project/snapshot.MARKER).write_text(json.dumps(record,indent=2)+'\n');snapshot.verify(project)
  records[branch]={'project':str(project),'marker_sha256':snapshot.digest(project/snapshot.MARKER),'files':files,'imports':len(record['validated_imports'])}
 changed=[n for n in records['baseline']['files']if records['baseline']['files'][n]!=records['candidate']['files'][n]]
 assert changed==['scripts/hero_atmosphere.gd']
 assert snapshot.inventory(SOURCE)==source;snapshot.verify(FROZEN)
 out={'passed':True,'source_commit':export['git']['head'],'source_before_after_equal':True,'frozen_parent_unchanged':True,'reused_immutable_files':reused,'copied_source_files':copied,'copied_bytes':sum(desired[n]['bytes']for n in copied),'branches':records,'sole_pair_delta':changed,'recipe_sha256':snapshot.digest(RECIPE/'recipe-source-only.json'),'helper_sha256':snapshot.digest(E/'capture_floor_ao.UNRUN.gd'),'runner_sha256':snapshot.digest(E/'tools/run_focus.py'),'no_import':True,'no_engine_yet':True}
 (E/'staging.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'passed':True,'files':len(desired),'imports':len(imports),'copied_bytes':out['copied_bytes'],'markers':{b:r['marker_sha256']for b,r in records.items()},'free':shutil.disk_usage('/tmp').free}))

if __name__=='__main__': main()
