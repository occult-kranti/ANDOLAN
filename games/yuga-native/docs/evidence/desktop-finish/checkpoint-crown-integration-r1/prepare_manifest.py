#!/usr/bin/env python3
"""Prepare an exact allowlist from closed owner packets; never stage or commit."""
from pathlib import Path
import json,hashlib,subprocess,datetime
repo=Path(__file__).resolve().parents[6]; project=repo/'games/yuga-native'; prefix='games/yuga-native/'
dest=Path(__file__).resolve().parent
def rec(p):
 b=p.read_bytes(); return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
files={}; proofs=[]
uid_exceptions={'games/yuga-native/scripts/rama_ability_glyph.gd.uid','games/yuga-native/scripts/rama_upper_hair_layers.gd.uid','games/yuga-native/scripts/world_roof_loggia.gd.uid'}
archived_uid_evidence={'games/yuga-native/docs/evidence/desktop-finish/world-overview-composition/W4-integration-r1/promoted-source/scripts/world_roof_loggia.gd.uid':'d887294cf73699c3a4af327a85bec1f47bf50ba37c6cbf31403edf0b11a4d676'}
def add(p,reason):
 p=Path(p); assert not p.is_symlink(),p
 p=p.resolve(); assert p.is_relative_to(repo) and p.is_file(),p
 rel=str(p.relative_to(repo)); assert '__pycache__' not in p.parts and (not rel.endswith('.uid') or rel in uid_exceptions or rel in archived_uid_evidence),rel
 if rel in archived_uid_evidence: assert rec(p)['sha256']==archived_uid_evidence[rel],rel
 row={'path':rel,**rec(p),'reasons':[reason]}
 if rel in files: files[rel]['reasons'].append(reason)
 else:files[rel]=row

def packet(rel,reason,receipt='receipt.json'):
 root=project/'docs/evidence/desktop-finish'/rel
 assert root.is_dir(),root
 rp=root/receipt
 if rp.exists():
  d=json.loads(rp.read_text()); entries=d.get('artifacts',d.get('files',[]))
  if isinstance(entries,dict): entries=[{'path':k,**(v if isinstance(v,dict) else {'sha256':v})} for k,v in entries.items()]
  verified=0
  for x in entries:
   if not isinstance(x,dict) or 'path' not in x or 'sha256' not in x: continue
   name=x['path']; p=project/name if name.startswith(('docs/','art/','scripts/','tests/','tools/','NOTICE/','assets/')) else root/name
   # W2 executed/ and W1 source/ remain receipt-local; W6 files are project-relative.
   if not p.exists() and (root/name).exists():p=root/name
   actual=rec(p); assert actual['sha256']==x['sha256'],(rp,p,'sha')
   if 'bytes' in x:assert actual['bytes']==x['bytes'],(rp,p,'bytes')
   verified+=1
  proofs.append({'path':str(rp.relative_to(repo)),**rec(rp),'registered_artifacts_rehashed':verified})
 for p in sorted(root.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and 'users' not in p.parts: add(p,reason)

implementation=json.loads((project/'docs/evidence/desktop-finish/S4/W6-crown-package/implementation-sources.json').read_text())['files']
for x in implementation:
 p=repo/x['path']; add(p,'W6 schema6/automation implementation; ordered sash successor supersedes earlier code pins')
for rel in ['assets/heroes/rama-hero.glb','assets/heroes/rama-hero-mid.glb','assets/heroes/rama-hero-far.glb','scripts/courtyard.gd','scripts/world_ground_common.gdshaderinc','scripts/loading_presentation.gd']:
 add(project/rel,'lead-accepted canonical integration')
for rel in ['art/hero-finish/history/schema6-crown-notice.json','art/hero-finish/prove_hair_compatibility.py']:
 add(project/rel,'accepted ordered stage history/offline-only hair compatibility')
for rel in ['S4/W1-smooth-crown-r1','S4/W2-helper-offline-compatibility-r2','S4/W2-helper-compatibility-r1','S4/W2-promotion-r1','S4/lead-crown-promotion-r1','S4/W6-crown-package','D01/W1-title-fill-day-r1','D01/W1-title-fill-night-200-r1','D01/lead-title-fill-promotion-r1','G0/lead-paving-promotion-r1','D02/W1-boot-dedup-native-r1','hero-sash-uv/W1-native-r1','hero-sash-uv/W6-package','hero-sash-uv/lead-promotion-r1']:
 packet(rel,'accepted integration source/evidence: '+rel)
# The copy receipt excludes its fresh XDG caches; exact separately sealed CI packet is included.
root=project/'docs/evidence/desktop-finish/D02/W6-copy-dedup';d=json.loads((root/'receipt.json').read_text())
for x in d['artifacts']:
 p=root/x['path'];assert rec(p)=={'sha256':x['sha256'],'bytes':x['bytes']};add(p,'sealed loading-copy source/64checks/actual audit')
add(root/'receipt.json','sealed loading-copy receipt')
packet('D02/W6-copy-dedup/ci-39107059307','exact3db successful CI, successor scope excluded')
packet('package-rehearsal-3db','historical exact3db plan only')
for rel in ['docs/evidence/desktop-finish/S4/W2-smooth-visual-r1.md','docs/evidence/desktop-finish/S4/W2-smooth-visual-r1.json']:
 add(project/rel,'independent accepted smooth-crown original review')
for p in sorted((project/'art/lookdev/title-portrait-fill-r1').rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts:add(p,'accepted title-fill source comparison')
for p in sorted((project/'art/hero-finish/sash-texel-r1').rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts:add(p,'accepted sashR2 source plus retained failedR1')
for rel in ['tools/graphics-six/run_focus.py','tools/graphics-six/sash_uv_capture.gd','tools/graphics-six/README.md']:
 add(project/rel,'W1 sealed actually exercised sash adapter')
for p in sorted((repo/'docs/evidence/desktop-finish-cloud-setup-r1').rglob('*')):
 if p.is_file():add(p,'lead environment readiness receipt')
add(repo/'docs/evidence/desktop-finish-old-source-cleanup-r1/execution-receipt.json','lead executed remote-blob-bound cleanup')
for rel in ['scripts/rama_motion.gd','tests/desktop_landing_support_boundary_cases.gd','tests/desktop_landing_pause_cases.gd','tools/run-visual-checks.py','tests/visual_catalog_cases.py']:
 add(project/rel,'lead-accepted bounded landing correction and W5 sealed minimal catalog')
for rel in ['S3/W5-landing-successor-r1','S3/W5-landing-successor-actual-r1','S3/W5-landing-catalog-r1']:
 packet(rel,'accepted landing source/actual/targeted catalog, retained failed limits',receipt='artifact-manifest.json')
for rel in ['S3/W1-landing-shape-review-r1','S3/W1-landing-successor-sampled-review-r1','S3/lead-landing-promotion-r1']:
 packet(rel,'independent/lead bounded landing acceptance')
for rel in sorted(uid_exceptions):
 add(repo/rel,'lead-approved individually audited runtime UID exception')

# Final additions were explicitly released by the owners and lead.
for rel in ['scripts/confluence_world.gd','scripts/world_atlas.gd','scripts/world_roof_loggia.gd','NOTICE/world-roof-loggia.md','tests/traversal_security_cases.py','tests/desktop_world_route_parity_cases.gd']:
 add(project/rel,'accepted combined roof/overview and required PCK dependency')
for rel in ['world-overview-composition/W1-native-r1','world-roof-loggia/W1-native-r1','world-roof-loggia/W4-independent-r1','world-overview-composition/W4-integration-r1','D07/W4-overview-brief-r1','D07/lead-heading-repair-r1']:
 packet(rel,'sealed accepted roof/overview original and independent review evidence')
for rel in ['roof-loggia-r1','overview-composition-r1','overview-render-r1','roof-loggia-render-r1','roof-loggia-render-r2','overview-roof-integration-r1']:
 root=project/'art/world-finish'/rel
 rp=root/'receipt.json';d=json.loads(rp.read_text())
 entries=d.get('artifacts',d.get('files',{}))
 if isinstance(entries,list): entries={x['path']:x for x in entries if isinstance(x,dict) and 'path' in x}
 verified=0
 for name,pin in entries.items():
  expected=pin if isinstance(pin,str) else pin['sha256']
  f=root/name
  if not f.exists() and (project/name).exists():f=project/name
  if not f.exists() and (repo/name).exists():f=repo/name
  assert rec(f)['sha256']==expected,(f,'sha')
  if isinstance(pin,dict) and 'bytes' in pin:assert f.stat().st_size==pin['bytes'],(f,'bytes')
  verified+=1
 proofs.append({'path':str(rp.relative_to(repo)),**rec(rp),'registered_artifacts_rehashed':verified})
 for f in sorted(root.rglob('*')):
  if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.uid':add(f,'sealed source preparation for accepted roof/overview; retained baseline diagnostics')
for rel in ['docs/WORKSPACE_AND_CLEANUP.md']:
 add(repo/rel,'lead final cleanup documentation')
for rel in ['docs/ACTIVE_DESKTOP_HANDOFF.md','docs/DESKTOP_FINISH_CAMPAIGN.md','docs/DESKTOP_FINISH_CAMPAIGN.json']:
 add(project/rel,'lead final integration status and bounded packet ledger')
for name in ['README.md','recovery-map.json']:
 add(repo/'docs/evidence/desktop-finish-package-reserve-cleanup-r1'/name,'lead future bounded reserve cleanup map; no deletion before source push')
for rel in ['D07/W5-atlas-route-regression-r1','D07/W5-route-diagnostic-r1','D07/W5-heading-diagnostic-r1','D07/W5-route-repaired-r1','D07/W5-camera-numeric-diagnostic-r1','D07/W5-route-repair-final-r1']:
 packet(rel,'W5 final world/atlas regression and preserved counterexamples',receipt='artifact-manifest.json')


for f in sorted(dest.rglob('*')):
 if f.is_file() and f.name not in ['ready-manifest.json','ready-paths.txt','README.md','link-audit.json'] and '__pycache__' not in f.parts:
  add(f,'W6 source identity, package plan and exact allowlist preparation')
expected_sources={
 'NOTICE/RAMA-HERO-PROVENANCE.json':'54840529ae5ded648f4b9e6e9dd3ae9c85a3175879dcd26f4cbd7c101365549e',
 'NOTICE/world-roof-loggia.md':'7e544da1f34b8b6dea694e40f3ec3e5e40291eb92aa3de9654fa23b2e0f986fb',
 'scripts/world_atlas.gd':'138c54e86adc4f41ee0ee915619efd58ec8fd6ed6c0d53179f9b770d64b7fdc7',
 'tests/desktop_world_route_parity_cases.gd':'75f947176c620506a46a968105e8ceb8318ee477d1644719deb37e904d6094c8',
 'scripts/confluence_world.gd':'42e617a379f815e51a32b9bbd9cca86c6ba3ac6a7c809e2d2d8c6c89619fc0cb',
 'scripts/world_roof_loggia.gd':'e6305e3fd2734901a488d61b4a715e0c6b75f6b95c7ef6810e945a62e7b69c3c',
 'tools/package-native.py':'c7a3506b468f41fb9f2b993d7fd1b247a59f812341fe8cf9a49e1c3dc55e8fb0',
 'tests/traversal_security_cases.py':'eddedfd07afbb5ac913e18617b3d956d66d310afd25eac5bbb22e056b7c72af5',
 'scripts/courtyard.gd':'43f512dc6509aba77c1d7055f0fd8404054df07fc700d6261f05a725c4e80a57',
 'scripts/loading_presentation.gd':'a01b52890a80cd14a0cecb767680e7905c411f926cae7f1ae97ca28c967424ac',
 'scripts/rama_motion.gd':'5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5',
 'scripts/world_ground_common.gdshaderinc':'2e84ddd1afe67c70db6d8bdc700adaa0e34bee644a20825d4ecde0a7a0f88641',
 'tools/run-visual-checks.py':'3021f04905b190f2db92ed4e4e3e9c73e27dca4505a90c74bd442ca4a530de4a',
 'tests/visual_catalog_cases.py':'92c83c16f0bddb67ae6fb1dd0881de0fb5b092f81ded9bb037c3afebaff62be7',
 'scripts/rama_ability_glyph.gd.uid':'be9213e0ca1e42d4f1f9319ad3d6d693bfd0db2e05531b8e57cf40eb687af90b',
 'scripts/rama_upper_hair_layers.gd.uid':'afb15e02266a4cc0ee755c5f213a12180b2e8533ee6a460b0f50c60a85e45cc5',
 'scripts/world_roof_loggia.gd.uid':'d887294cf73699c3a4af327a85bec1f47bf50ba37c6cbf31403edf0b11a4d676',
}
for name,pin in expected_sources.items(): assert rec(project/name)['sha256']==pin,name
tracked=set(subprocess.check_output(['git','ls-files'],cwd=repo,text=True).splitlines())
changed=set(subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=repo,text=True).splitlines())
ready=sorted(name for name in files if name not in tracked or name in changed)
ignored=set(subprocess.run(['git','check-ignore','--stdin'],input='\n'.join(ready)+'\n',cwd=repo,text=True,capture_output=True).stdout.splitlines())
registered={}
for name in ready:
 f=repo/name;assert f.stat().st_size<100_000_000,f
 registered[name]={**rec(f),'mode':oct(f.stat().st_mode&0o777),'owner_scope':files[name]['reasons'],'requires_scoped_force_add':name in ignored}
report={'schema':1,'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
 'scope':'Exact completed integration delta only; no staging, export, packaging or full quality claim. Accepted source/art scopes and retained failed limits remain in owner receipts.',
 'files':registered,'unchanged_selected_files_omitted':sorted(set(files)-set(ready)),
 'count':len(registered),'bytes':sum(v['bytes'] for v in registered.values()),'ignored_paths':sorted(ignored),'receipt_audit':proofs,
 'uid_exceptions':{k:registered[k]['sha256'] for k in sorted(uid_exceptions)},'archived_uid_evidence':archived_uid_evidence,
 'exclusions':['.design','scratch','unlisted canonical test/tool UIDs','__pycache__','old ready-manifest-draft.json','new hair and shoulder candidates','new sustained movement work','unlisted or unsealed packets'],
 'self_metadata':['ready-manifest.json','README.md','ready-paths.txt','link-audit.json']}
(dest/'ready-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
metadata=[str((dest/name).relative_to(repo)) for name in report['self_metadata']]
(dest/'ready-paths.txt').write_text('\n'.join(ready+metadata)+'\n')
print(json.dumps({'files':len(registered),'bytes':report['bytes'],'ignored':len(ignored),'verified_receipt_artifacts':sum(p['registered_artifacts_rehashed'] for p in proofs),'manifest_sha256':rec(dest/'ready-manifest.json')['sha256']}))
