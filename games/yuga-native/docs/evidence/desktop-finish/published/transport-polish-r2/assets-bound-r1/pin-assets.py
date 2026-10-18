#!/usr/bin/env python3
"""Read/hash the five exact assets and known receipts; never transport or execute."""
from pathlib import Path
import hashlib,json,os,stat,time
HERE=Path(__file__).resolve().parent
PROJECT=Path('/workspace/ANDOLAN/games/yuga-native')
BUILD=Path('/workspace/scratch/yuga-continuation-W6-r1/package-successor-r2/build')
SOURCE='79e5c15d8a3657e16fda67acb277b2406120dcd1'
QUAL=PROJECT/'docs/evidence/desktop-finish/continuation-oct18/W6-package-r2/qualification-receipt-uid-reviewed.json'
WARM=PROJECT/'docs/evidence/desktop-finish/continuation-oct18/W1-actual-r1/package-successor-r2/warm/receipt.json'
DRAFT=PROJECT/'docs/evidence/desktop-finish/published/release-polish-r1/create-draft-response.json'
PARENT=HERE.parent/'template-receipt.json'
INDEX=Path('/workspace/ANDOLAN/.git/index')
LIMIT=48*1024**2
NAMES=['yuga-native-linux-x86_64.zip','yuga-native-windows-x86_64.zip','native-export-manifest.json','native-package-manifest.json','SHA256SUMS.txt']
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024**2),b''):h.update(block)
 return h.hexdigest()
def rec(path):return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)}
def dump(name,value):
 with (HERE/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
index_before=sha(INDEX)
assert sha(PARENT)=='66ec0cf799c0448f59f23ac41b865cb0fb82abd1b0298b468579107453e8f316'
parent=json.loads(PARENT.read_text())
for name,pin in parent['artifacts'].items():
 path=PARENT.parent/name;assert path.stat().st_size==pin['bytes'] and sha(path)==pin['sha256'],name
assert sha(QUAL)=='e924d90af27dad48c96fcb99ad9bbbe2cfd84ac01899b2221491199baf00f400'
assert sha(WARM)=='b71b25fbc53baa6b94a5750391d42770c43c079bb769358bbe7fb0ae54ad2226'
q=json.loads(QUAL.read_text());warm=json.loads(WARM.read_text());draft=json.loads(DRAFT.read_text())
assert q['passed'] is True and q['source_commit']==SOURCE and len(q['checks'])==40 and all(x['passed'] is True for x in q['checks'])
assert warm['passed'] is True and warm['source']==SOURCE and warm['native_exit']==0 and all(warm['validation_checks'].values())
assert draft['id']==416542426 and draft['tag_name']=='yuga-desktop-polish-2026-10-18' and draft['target_commitish']==SOURCE and draft['draft'] is True and draft['prerelease'] is True and draft['assets']==[]
assert set(q['five_assets'])==set(NAMES)
rows=[]
for name in NAMES:
 path=BUILD/name;before=path.stat();assert stat.S_ISREG(before.st_mode) and not path.is_symlink()
 actual={'bytes':before.st_size,'sha256':sha(path)};after=path.stat()
 assert actual==q['five_assets'][name],name
 assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),name
 sizes=[];remaining=before.st_size
 while remaining:amount=min(remaining,LIMIT);sizes.append(amount);remaining-=amount
 rows.append({'name':name,'path':str(path),**actual,'parts':len(sizes),'part_sizes':sizes})
assert warm['linux_zip_sha256']==rows[0]['sha256']
assert (BUILD/NAMES[-1]).read_text()==''.join(x['sha256']+'  '+x['name']+'\n' for x in rows[:4])
total=sum(x['bytes'] for x in rows);required=2*total+64*1024**2+500*1024**2
free=os.statvfs(BUILD).f_bavail*os.statvfs(BUILD).f_frsize
bindings={'schema':1,'source_commit':SOURCE,'status':'ASSETS_VERIFIED_EXECUTION_STILL_UNBOUND','parent_template':rec(PARENT),'asset_root':str(BUILD),'assets':rows,'total_asset_bytes':total,'chunk_limit':LIMIT,'part_counts':[x['parts'] for x in rows],'known_qualification':{'export_package':rec(QUAL),'warm_only':rec(WARM),'root_held_draft':rec(DRAFT)},'missing_authorization':{'cold_receipt':None,'final_independent_review':None,'direct_upload_outcome':None,'materialize_push_go':None},'held_draft':{'id':draft['id'],'tag':draft['tag_name'],'target':draft['target_commitish'],'draft':True,'prerelease':True,'asset_count':0},'capacity_observation':{'unix':time.time(),'path':str(BUILD),'free_bytes':free,'asset_bytes':total,'two_payloads_plus_64mib_work_and_500mib_reserve':required,'observed_margin_bytes':free-required,'final_fresh_audit_still_required':True},'scope':'Exact local package asset hashes/census, warm-only receipt and root-supplied held draft metadata. Does not qualify cold, independent acceptance, current API state, direct upload or fallback. Existing executable template remains unchanged/unbound.'}
dump('asset-binding.json',bindings)
assert sha(INDEX)==index_before
receipt={'schema':1,'status':'HOLD_PENDING_COLD_INDEPENDENT_DIRECT_OUTCOME','source_commit':SOURCE,'checks':{'five_asset_hashes_match_export_qualification':True,'checksums_exact':True,'package40_passed':True,'warm_owner_receipt_bound':True,'new_held_draft_metadata_bound':True,'sealed_template_all_artifacts_unchanged':True,'index_before_after_equal':True},'index_sha256':index_before,'artifacts':{n:{'bytes':(HERE/n).stat().st_size,'sha256':sha(HERE/n)} for n in ['pin-assets.py','asset-binding.json']},'executed_scope':'Read-only hashing and receipt parsing; local evidence JSON written only.','external_actions':{'engine':False,'network':False,'git_subprocess':False,'git_objects_refs_index_mutation':False,'materialization':False,'upload':False,'publication':False},'final22plus10_guards':'NOT_RUN_BEFORE_FINAL_BINDING'}
dump('receipt.json',receipt)
print(json.dumps({'receipt_sha256':sha(HERE/'receipt.json'),'asset_binding_sha256':sha(HERE/'asset-binding.json'),'assets':len(rows),'total_bytes':total,'part_counts':bindings['part_counts'],'required_free_bytes':required,'observed_free_bytes':free,'margin_bytes':free-required}))
