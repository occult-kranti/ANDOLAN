"""Create matched current-runtime R5 children by verified immutable hardlinks only.

No engine, import, canonical write or full-repository copy. Mutable auxiliary
caches are copied separately. Prior R4 children and store remain unchanged.
"""
import argparse,json,os,shutil,sys
from pathlib import Path
REPO=Path('/workspace/ANDOLAN/games/yuga-native');W=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO/'tools/graphics-six'));import snapshot
HELPER='tools/graphics-six/hair_capture.gd'
PREP_PIN='449aca1e90912fd43fd3398990e54814a1a8abc02511b6b7ac1b858df663ff36'
COMPARATOR_PIN='e5402eaa0b27760964d354496177a40fd536d6bb37c683be5b25eaf244282d5b'
HELPER_PIN='9f0aafd5e5f955027b8af0fbd46544a9eee95339058ca41e3ba6e9f0c2a457d8'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();receipt=a.receipt.resolve()
 assert not out.exists()and not receipt.exists();assert snapshot.digest(W/'import-preparation.json')==PREP_PIN
 prep=json.loads((W/'import-preparation.json').read_text());source=prep['current_capture_source'];frozen=Path(prep['frozen_source']);base=snapshot.verify(frozen);assert snapshot.digest(frozen/snapshot.MARKER)==source['frozen_source_sha256']
 proof=json.loads((W/'import-comparison-r1.json').read_text());assert proof['passed']and proof['comparison_script_sha256']==COMPARATOR_PIN and proof['candidate_manifest_sha256']==prep['candidate_manifest_sha256'];assert snapshot.digest(W/'hair_capture_cleanup.gd')==HELPER_PIN
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
  record={'schema':1,'round':'G5-hair-knot-R5-current-'+branch,'source':str(REPO),'project':str(project),'store':str(store),'files':files,'branch':branch,'frozen_ancestor':str(frozen),'frozen_ancestor_sha256':source['frozen_source_sha256'],'current_source_preparation_sha256':PREP_PIN,'validated_imports':snapshot.imports(project),'source_bytes':sum(v['bytes']for n,v in files.items()if not n.startswith('.godot/')),'compiled_bytes':sum(v['bytes']for n,v in files.items()if n.startswith('.godot/imported/')),'scope':'Fresh matched current canonical runtime, only R5 hair trio/cache differ. Immutable files hardlinked from verified retained stage or private overlay; auxiliary caches independently copied. No engine or canonical writes.'}
  (project/snapshot.MARKER).write_text(json.dumps(record,indent=2)+'\n');snapshot.verify(project);records[branch]={'project':str(project),'marker_sha256':snapshot.digest(project/snapshot.MARKER),'files':files,'imports':len(record['validated_imports'])}
 changed=sorted(n for n in records['baseline']['files']if records['baseline']['files'][n]!=records['candidate']['files'][n]);assert changed==sorted(overrides)
 snapshot.verify(frozen)
 result={'schema':1,'passed':True,'branches':records,'exact_pair_difference_paths':changed,'current_source_preparation_sha256':PREP_PIN,'import_proof_sha256':snapshot.digest(W/'import-comparison-r1.json'),'helper_sha256':HELPER_PIN,'helper_runtime_path':HELPER,'private_store':str(store),'current_source_scope':source,'frozen_R4_unchanged':True,'source_and_import_files_hardlinked_not_copied':True,'auxiliary_cache_files_copied':list(source['copied_auxiliary']),'tmp_free_bytes':shutil.disk_usage('/tmp').free,'engine_started':False}
 receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2)+'\n');print('Matched current-runtime R5 pair staged; only9 raw/cache deltas; no engine. Free',result['tmp_free_bytes'])
if __name__=='__main__':main()
