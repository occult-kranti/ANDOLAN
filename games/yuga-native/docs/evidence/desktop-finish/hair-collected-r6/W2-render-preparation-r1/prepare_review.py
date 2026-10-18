"""Create matched current-runtime R6 children by verified immutable hardlinks only.

No engine, import, canonical write or full-repository copy. Mutable auxiliary
caches are copied separately. Prior R4/R5 children and store remain unchanged.
"""
import argparse,json,os,shutil,sys
from pathlib import Path
REPO=Path('/workspace/ANDOLAN/games/yuga-native');W=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'runner'));import snapshot
HELPER='tools/graphics-six/hair_capture.gd'
MANIFEST_PIN='81ceaecd8c8fb550c1b0c9072da186e36d4c7ebfc99959d6ec88263ae5b15eb8'
COMPARATOR_PIN='4adbc056479dddbedddfdaac516653027d7f07080483342634bc488c0eabf3b4'
HELPER_PIN='865d2c92e5f53a754d9c42fe72ce35ae6b2116e46146955fda64a58c542acd6d'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();receipt=a.receipt.resolve()
 assert not out.exists()and not receipt.exists()and out.parent==Path('/tmp')and REPO not in receipt.parents;PREP_PIN=snapshot.digest(W/'import-preparation.json')
 prep=json.loads((W/'import-preparation.json').read_text());assert prep['candidate_manifest_sha256']==MANIFEST_PIN and prep['prepare_sha256']==snapshot.digest(W/'prepare_import.py') and prep['probe_sha256']==snapshot.digest(W/'import_semantics.gd');assert prep['independent_source_review_sha256']=='6b708e26c10b8d3617283e62060b98ecc3dff588ad322db8776acb4a95d81821';source=prep['current_capture_source'];frozen=Path(prep['frozen_source']);base=snapshot.verify(frozen);assert snapshot.digest(frozen/snapshot.MARKER)==source['frozen_source_sha256']=='20aed49da1db66b48a2dcac9f0ced2afa9eb08753293a8bda943e7c256fab63e'
 proof=json.loads((W/'import-comparison-r1.json').read_text());assert proof['passed']and proof['preparation_sha256']==PREP_PIN and proof['comparison_script_sha256']==COMPARATOR_PIN and proof['candidate_manifest_sha256']==prep['candidate_manifest_sha256'];assert snapshot.digest(W/'hair_capture_cleanup.gd')==HELPER_PIN
 imported=Path(prep['candidate_project']);manifest=json.loads(Path(prep['candidate_manifest']).read_text());overrides={}
 for level,row in manifest['levels'].items():
  name=Path(row['output']).name;rel='assets/heroes/'+name;path=imported/rel
  assert snapshot.digest(path)==row['output_sha256'];assert source['files'][rel]['sha256']==prep['canonical_raw_pins'][level]
  assert(imported/(rel+'.import')).read_bytes()==Path(source['source_map'][rel+'.import']).read_bytes();overrides[rel]=path
 for name,item in proof['imported_resources'].items():
  if Path(name).suffix in ['.scn','.md5']and '.glb-'in name:
   assert snapshot.metadata(imported/name)==item;overrides[name]=imported/name
 assert len(overrides)==9
 desired={**source['files'],**source['compiled_files'],**source['copied_auxiliary'],HELPER:snapshot.metadata(W/'hair_capture_cleanup.gd')}
 links={**{n:Path(v)for n,v in source['source_map'].items()},**{n:frozen/n for n in source['compiled_files']},**{n:Path(source['overlay'])/n for n in source['copied_auxiliary']},HELPER:W/'hair_capture_cleanup.gd'}
 for name,item in desired.items():assert snapshot.metadata(links[name])==item
 store=out/'private-store';records={}
 for branch in ['baseline','candidate']:
  project=out/branch;files=dict(desired);inputs=dict(links)
  if branch=='candidate':files.update({n:snapshot.metadata(f)for n,f in overrides.items()});inputs.update(overrides)
  for name,item in files.items():
   original=inputs[name];target=project/name;target.parent.mkdir(parents=True,exist_ok=True)
   if name in source['copied_auxiliary']:shutil.copyfile(original,target)
   elif name.startswith('.godot/imported/'):
    blob=store/'imports'/item['sha256'];blob.parent.mkdir(parents=True,exist_ok=True)
    if blob.exists():assert snapshot.metadata(blob)==item
    else:os.link(original,blob)
    os.link(blob,target)
   else:os.link(original,target)
  record={'schema':1,'round':'G6-hair-collected-R6-f8-'+branch,'source':str(REPO),'project':str(project),'store':str(store),'files':files,'branch':branch,'frozen_ancestor':str(frozen),'frozen_ancestor_sha256':source['frozen_source_sha256'],'current_source_preparation_sha256':PREP_PIN,'validated_imports':snapshot.imports(project),'source_bytes':sum(v['bytes']for n,v in files.items()if not n.startswith('.godot/')),'compiled_bytes':sum(v['bytes']for n,v in files.items()if n.startswith('.godot/imported/')),'scope':'Fresh matched frozen-f8 accepted runtime, only R6 hair trio/cache differ. Immutable files hardlinked from verified retained stage or private overlay; auxiliary caches independently copied. No engine or canonical writes.'}
  (project/snapshot.MARKER).write_text(json.dumps(record,indent=2)+'\n');snapshot.verify(project);records[branch]={'project':str(project),'marker_sha256':snapshot.digest(project/snapshot.MARKER),'files':files,'imports':len(record['validated_imports'])}
 changed=sorted(n for n in records['baseline']['files']if records['baseline']['files'][n]!=records['candidate']['files'][n]);assert changed==sorted(overrides)
 snapshot.verify(frozen)
 result={'schema':1,'passed':True,'branches':records,'exact_pair_difference_paths':changed,'current_source_preparation_sha256':PREP_PIN,'import_proof_sha256':snapshot.digest(W/'import-comparison-r1.json'),'helper_sha256':HELPER_PIN,'helper_runtime_path':HELPER,'private_store':str(store),'current_source_scope':source,'frozen_R4_R5_unchanged':True,'source_and_import_files_hardlinked_not_copied':True,'auxiliary_cache_files_copied':list(source['copied_auxiliary']),'tmp_free_bytes':shutil.disk_usage('/tmp').free,'engine_started':False}
 receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2)+'\n');print('Matched frozen-f8 R6 pair staged; only9 raw/cache deltas; no engine. Free',result['tmp_free_bytes'])
if __name__=='__main__':main()
