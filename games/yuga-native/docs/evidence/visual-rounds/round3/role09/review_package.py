from pathlib import Path
import importlib.util,json,tempfile,hashlib,os
root=Path('/workspace/ANDOLAN/games/yuga-native');proposal=Path('/workspace/scratch/visual-round3/role-14/review-r3');out=Path(__file__).parent
spec=importlib.util.spec_from_file_location('review_packaging',root/'tools/package-native.py');pkg=importlib.util.module_from_spec(spec);spec.loader.exec_module(pkg)
checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
validated=pkg.validate_rama_hero_notice(proposal);manifest=json.loads((proposal/'promotion-manifest.json').read_text())
check('actual fixed proposal validates with five ancestors',len(validated['authoringStages'])==5)
check('proposal is explicitly unpromoted',manifest['status']=='review-proposal-not-promoted' and manifest['optional_shader']['included'] is False)
check('preserved runtime script and shader excluded from promotion files',not any(x in manifest['promotion_files'] for x in ['scripts/rama_surface_finish.gd','shaders/rama_secondary_cloth.gdshader','art/hero-rama-lod/glb_lod.py']))
check('all proposed files have exact existing bytes',all((proposal/path).is_file() and pkg.record(proposal/path)==record for path,record in manifest['promotion_files'].items()))
# Independent path counterexamples against the validator entry actually used
# by schema4; a matching hash must not excuse an ancestor symlink escape.
with tempfile.TemporaryDirectory(prefix='r3-independent-paths-') as folder:
 p=Path(folder);base=p/'root';base.mkdir();outside=p/'outside';outside.mkdir();data=b'controlled independent source witness';(outside/'same.bin').write_bytes(data);digest=hashlib.sha256(data).hexdigest();(base/'escape').symlink_to(outside,target_is_directory=True)
 for relative in ['escape/same.bin','../outside/same.bin',str(outside/'same.bin')]:
  try:pkg._rama_source(base,relative,digest);rejected=False
  except ValueError:rejected=True
  check('reject matching bytes through unsafe source path '+relative,rejected)
 (base/'inside.bin').write_bytes(data);check('matching direct internal control remains valid',pkg._rama_source(base,'inside.bin',digest)['sha256']==digest)
result={'task':'R3-09-independent-R3-14-review','passed':all(x['passed'] for x in checks),'count':len(checks),'checks':checks,'package_sha256':pkg.digest(root/'tools/package-native.py'),'helper_sha256':pkg.digest(root/'tools/visual-rounds/integration/prepare_groom_review.py'),'proposal_sha256':pkg.digest(proposal/'promotion-manifest.json'),'source_count':len(validated['sources']),'promotion_file_count':len(manifest['promotion_files']),'scope':'Bounded independent fixed-proposal identity/path/ancestry and promotion-scope review. No observed preservation/path hole. This is not anatomy, action clearance, render or promotion approval.'}
(out/'package-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'count':len(checks),'source_count':result['source_count'],'promotion_files':result['promotion_file_count']}))
