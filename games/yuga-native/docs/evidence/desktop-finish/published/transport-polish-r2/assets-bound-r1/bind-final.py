#!/usr/bin/env python3
"""Create the once-bound local delivery sources; no Git or network operations."""
from pathlib import Path
import hashlib,json,difflib,os,pprint,time
HERE=Path(__file__).resolve().parent;PARENT=HERE.parent;PROJECT=Path('/workspace/ANDOLAN/games/yuga-native')
SOURCE='79e5c15d8a3657e16fda67acb277b2406120dcd1';RELEASE=416542426
CONT=PROJECT/'docs/evidence/desktop-finish/continuation-oct18';PUB=PROJECT/'docs/evidence/desktop-finish/published/release-polish-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def new(name,data):
 with (HERE/name).open('xb') as f:f.write(data)
refs={
 'export_package':(CONT/'W6-package-r2/qualification-receipt-uid-reviewed.json','e924d90af27dad48c96fcb99ad9bbbe2cfd84ac01899b2221491199baf00f400'),
 'actual_warm_cold':(CONT/'W1-actual-r1/package-successor-r2/receipt.json','b7a3f90433247072d68b34ee7f3b03a73edca69ded4cb561d144591f687533d3'),
 'warm':(CONT/'W1-actual-r1/package-successor-r2/warm/receipt.json','b71b25fbc53baa6b94a5750391d42770c43c079bb769358bbe7fb0ae54ad2226'),
 'cold':(CONT/'W1-actual-r1/package-successor-r2/cold/receipt.json','e424cf6051b88ef611f3a3df56bb2a40a6df2fd4435eb05232b8ddff58f19868'),
 'independent':(CONT/'W6-integration-r1/package-native-independent-r2.json','bab4255a670a864d8ad76e1ded101139d5b9c1a2379c2d82e3f760c1cf48afb6'),
 'independent_visual':(CONT/'W2-package-successor-r2/receipt.json','7f07078258afcf4eb4fbde40b383db3f01b7473b79fef428c2377e20a148b3bd'),
 'direct_upload':(PUB/'direct-upload-receipt.json',None),
 'empty_draft':(PUB/'draft-after-direct-upload.json',None),
 'initial_draft':(PUB/'create-draft-response.json',None),
}
pins={}
for name,(path,expected) in refs.items():
 assert path.is_file() and not path.is_symlink()
 actual=rec(path)
 if expected:assert actual['sha256']==expected,name
 pins[name]=actual
q=json.loads(refs['export_package'][0].read_text());assert q['passed'] and q['source_commit']==SOURCE
for key in ['warm','cold']:
 r=json.loads(refs[key][0].read_text());assert r['source']==SOURCE and r['passed'] is True and r['native_exit']==0 and all(r['validation_checks'].values())
ind=json.loads(refs['independent'][0].read_text());assert ind['passed'] is True and ind['count']==25 and all(x['passed'] for x in ind['checks'])
visual=json.loads(refs['independent_visual'][0].read_text());assert visual['source_commit']==SOURCE and visual['status']=='SCOPED_EXACT_LINUX_PACKAGE_INDEPENDENT_VISUAL_PASS' and visual['direct_full_original_count']==28
attempt=json.loads(refs['direct_upload'][0].read_text());assert attempt['source_commit']==SOURCE and attempt['release_id']==RELEASE and attempt['attempts']==1 and attempt['http_401'] is True and attempt['assets_after']==[] and attempt['draft_remains_held'] is True
for key in ['empty_draft','initial_draft']:
 draft=json.loads(refs[key][0].read_text());assert draft['id']==RELEASE and draft['target_commitish']==SOURCE and draft['tag_name']=='yuga-desktop-polish-2026-10-18' and draft['draft'] is True and draft['prerelease'] is True and draft['assets']==[]
assets=json.loads((HERE/'asset-binding.json').read_text());assert assets['source_commit']==SOURCE and assets['part_counts']==[2,3,1,1,1]
for row in assets['assets']:assert q['five_assets'][row['name']]=={k:row[k] for k in ['bytes','sha256']}
required=1080568648;v=os.statvfs(assets['asset_root']);free=v.f_bavail*v.f_frsize;assert free>=required,(free,required)
new('space-before-prepare.json',(json.dumps({'unix':time.time(),'free_bytes':free,'required_bytes':required,'margin_bytes':free-required,'minimum_preserved_reserve_bytes':500*1024**2,'scope':'Fresh local preparation gate. Repeat before materialization.'},indent=2)+'\n').encode())
new('qualification-binding.json',(json.dumps({'source_commit':SOURCE,'release_id':RELEASE,'tag':'yuga-desktop-polish-2026-10-18','receipts':pins,'transport_status':'LOCAL_PREPARATION_ONLY_ROOT_INSPECTION_BEFORE_MATERIALIZE_PUSH','no_rebuild_repack_publish':True},indent=2)+'\n').encode())
changes=[]
for name in ['generate.py','upload_template.py','push.py','test_guards.py','test_push_guards.py','upload-ui-release-assets.template.yml']:
 before=(PARENT/name).read_text();after=before
 if name=='generate.py':
  after=after.replace('SOURCE = None  # Await exact W6 qualified build directory.','SOURCE = Path('+repr(assets['asset_root'])+')')
  after=after.replace('RELEASE_ID = None  # Root must create a NEW draft; prior public release is immutable.','RELEASE_ID = '+str(RELEASE))
  after=after.replace('QUALIFICATION_RECEIPTS = None  # Exact reviewed export, actual warm/cold and independent receipt pins.','QUALIFICATION_RECEIPTS = '+pprint.pformat(pins,sort_dicts=False,width=120))
  after=after.replace('PART_COUNTS = None  # Exact five-asset chunk census, derived from final sizes.','PART_COUNTS = (2, 3, 1, 1, 1)')
  after=after.replace('# Pending successor qualification. No old asset pins are admitted.','# Exact qualified successor bytes; prior public release remains unchanged.')
  expected=[(a['name'],a['bytes'],a['sha256']) for a in assets['assets'][:4]]
  after=after.replace('EXPECTED = []','EXPECTED = '+pprint.pformat(expected,width=140))
  after=after.replace('EXPECTED_SUMS_SHA256 = None','EXPECTED_SUMS_SHA256 = '+repr(assets['assets'][-1]['sha256']))
  after=after.replace('{"export_package", "actual_warm_cold", "independent"}',repr(set(pins)))
 if name=='upload_template.py':
  after=after.replace('RELEASE_ID = None  # Await the separately created successor draft.','RELEASE_ID = '+str(RELEASE))
  after=after.replace('PART_COUNTS = None  # Await exact qualified five-asset census.','PART_COUNTS = (2, 3, 1, 1, 1)')
 if name=='upload-ui-release-assets.template.yml':after=after.replace('@@RELEASE_ID@@',str(RELEASE))
 new(name,after.encode());changes.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='unbound/'+name,tofile='bound/'+name))
new('final-binding.patch',''.join(changes).encode())
print(json.dumps({'bound_release':RELEASE,'source':SOURCE,'qualification_receipts':len(pins),'fresh_free_bytes':free,'required_bytes':required,'materialized':False}))
