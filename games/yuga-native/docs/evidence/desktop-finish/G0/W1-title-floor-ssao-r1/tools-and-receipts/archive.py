from pathlib import Path
import json,hashlib,shutil,sys,datetime
W=Path('/tmp/yuga-floor-ao-r1');N=Path('/workspace/ANDOLAN/games/yuga-native');D=N/'docs/evidence/desktop-finish/G0/W1-title-floor-ssao-r1'
assert not D.exists();D.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
for p in (W/'evidence').rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts and not any(v in p.parts for v in ['data','config','cache']):cp(p,D/'tools-and-receipts'/p.relative_to(W/'evidence'))
for run in ['baseline-preflight-r1','baseline-preflight-r2','candidate-preflight-r2','baseline-render-r2','candidate-render-r2']:
 for p in (W/run).iterdir():
  if p.is_file():cp(p,D/run/p.name)
 for p in (W/(run+'-logs')).iterdir():
  if p.is_file():cp(p,D/(run+'-logs')/p.name)
for name in ['baseline-project','candidate-project','baseline-project-r2','candidate-project-r2']:
 cp(W/name/'.graphics-six-snapshot.json',D/'snapshots'/(name+'.json'))
for p in (W/'frozen-inputs').rglob('*'):
 if p.is_file():cp(p,D/'frozen-inputs'/p.relative_to(W/'frozen-inputs'))
manifest=Path('/tmp/yuga-desktop-integrated-package-r3/build/native-export-manifest.json');cp(manifest,D/'f8-native-export-manifest.json')
refs={}
for name in ['docs/evidence/desktop-finish/G0/template-baseline-cold-600-r1/generated-shader-caches.tar.gz','docs/evidence/desktop-finish/G0/template-baseline-cold-600-r1/receipt.json','art/world-finish/title-floor-ssao-plan-r1/recipe-source-only.json']:
 p=N/name;refs[name]={'sha256':sha(p),'bytes':p.stat().st_size}
(D/'source-references.json').write_text(json.dumps({'references':refs,'raw_source_recovery':'Exact f8dec commit + common helper/one-line profile derivative and frozen-inputs; all source/cache metadata in four snapshots. Existing imported store remains pinned. No editor or import ran.','generated_cache_scope':'Initial112 Godot+101 Mesa seeds are losslessly archived by the referenced previous owner; each run records all seed hashes and postrun source equality. New generated user caches remain in original private/tmp run directories, not duplicated here.'},indent=2)+'\n')
images={}
for branch in ['baseline','candidate']:
 for shot in ['00-title','01-training']:
  p=D/f'{branch}-render-r2'/f'{shot}.png';images[str(p.relative_to(D))]={'sha256':sha(p),'bytes':p.stat().st_size,'directly_opened_by_W1':True}
(D/'visual-review.json').write_text(json.dumps({'disposition':'REJECT AO-off as dotted-floor repair; no promotion','all_four_full_originals_directly_viewed':True,'images':images,'findings':['Dotted joints remain in ordinary title and training views.','All four preselected floor ROIs and all three contact-cost ROIs are RGB byte-identical.','All interior framebuffer columns0–958 are RGB byte-identical; every changed pixel is on final column959. No unsupported edge-effect cause is assigned.','Actual environment AO getter true versus false, all164 bone poses, scene controls, materials, light, camera, clocks, renderer,MSAA and other environment settings match exactly.','No temporal, hardware-performance, universal AO inactivity or permanent AO-off claim.'],'warnings':'Each actual run retained63 RGB8-to-RGBA8 format warnings; no script errors, ERROR lines or ObjectDB leak warning.','failed_preflight':'Initial typed-null serializer produced2288 SCRIPT ERROR entries despite inner helper complete=true; outer runner correctly rejected. Preserved exact original/helper/take. Common successor adds only nullObject→JSONnull handling; unsupported nonnull/RID/depth/nonfinite checks remain.'},indent=2)+'\n')
(D/'REVIEW.md').write_text('''The one-toggle comparison rejects disabling SSAO as a repair for the dotted courtyard floor in these two views. All four full originals were opened. The dotted seams remain, and all four floor regions selected before the candidate and all three contact regions are byte-identical. Every changed pixel is confined to the last framebuffer column; no cause is assigned to that edge difference. There is no canonical change or further AO tuning in this packet.

The source is the exact f8dec5fa package runtime, with a shared read-only observer. The candidate changes only hero_atmosphere.gd’s SSAO-enabled profile entry. Both actual Forward+ takes use unmodified public dce, fresh copies of the same112 Godot and101 Mesa cache files, CPU0,1/LP2, ordinary title camera then explicitly staged start_training API, and bounds600s overall/300s without progress. Baseline completed in36.620s and candidate30.587s; each produced2 originals and passed6 capture checks. Strict comparison confirms164 bone poses, camera, clocks, light, materials, all other environment properties, renderer andMSAA2x exactly match. AO getters are true and false respectively.

The initial helper preflight failed on typed-null stored objects. Its source, log and misleading inner complete flag are retained; the outer runner correctly rejected2288 SCRIPT ERROR entries. A one-line shared successor serializes a typed-null object as JSONnull without weakening nonnull/opaque/nonfinite/depth guards. Both new JSON preflights passed6/6 and strict paired controls. W4 independently reviewed that narrow correction. Each actual take retained63 RGB8-to-RGBA8 warnings, with no script errors or leak warning.

The result bounds this pair only. It does not establish universal renderer AO behaviour, temporal quality or GPU performance. New user caches remain in their private execution directories; exact initial cache inputs are referenced to their existing lossless archive. All originals, raw sidecars, complete logs, source manifests, changed source bytes, helper versions, commands and comparator are retained here.
''')
files={str(p.relative_to(D)):{'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(D.rglob('*'))if p.is_file()}
r={'schema':1,'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'owner':'W1','disposition':'AO-off rejected as repair; no runtime promotion','source_commit':'f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1','controls_passed':True,'initial_failed_helper_preserved':True,'raw_originals':4,'heavy_lane_released':True,'artifacts':files,'artifact_count':len(files),'artifact_bytes':sum(v['bytes']for v in files.values())};(D/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'path':str(D),'receipt_sha256':sha(D/'receipt.json'),'review_sha256':sha(D/'REVIEW.md'),'artifacts':len(files),'bytes':r['artifact_bytes']}))
