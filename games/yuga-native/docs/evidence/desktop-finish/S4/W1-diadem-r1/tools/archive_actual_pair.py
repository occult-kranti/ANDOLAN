from pathlib import Path
import collections,hashlib,importlib.util,json,shutil
repo=Path('/workspace/ANDOLAN/games/yuga-native'); work=Path('/tmp/yuga-s4-diadem-review-r1'); dest=repo/'docs/evidence/desktop-finish/S4/W1-diadem-r1'
assert not dest.exists();dest.mkdir(parents=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cp(p,q): q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);assert sha(p)==sha(q)
spec=importlib.util.spec_from_file_location('snapshot',repo/'tools/graphics-six/snapshot.py');snap=importlib.util.module_from_spec(spec);spec.loader.exec_module(snap)
reports={};runs={};warnings={};markers={}
for branch in ['baseline','candidate']:
 project=work/branch;seal=snap.verify(project);markers[branch]=sha(project/snap.MARKER)
 p=Path('/tmp/yuga-s4-diadem-'+branch+'-warm-r1');l=p.with_name(p.name+'-logs')
 reports[branch]=json.loads((p/'capture.json').read_text());runs[branch]=json.loads((l/'run.json').read_text())
 assert reports[branch]['complete'] is True and runs[branch]['complete'] is True
 for f in p.iterdir():
  if f.is_file():cp(f,dest/branch/f.name)
 for name in ['run.json','godot.log','xvfb.log']:cp(l/name,dest/branch/name)
 cp(project/snap.MARKER,dest/branch/'snapshot.json')
 warnings[branch]=dict(collections.Counter(s for s in (l/'godot.log').read_text().splitlines() if s.startswith(('WARNING:','ERROR:','SCRIPT ERROR:'))))
 for s in reports[branch]['shots']:assert sha(p/s['file'])==s['sha256']
def diffs(a,b,p=''):
 if isinstance(a,dict) and isinstance(b,dict):return sum((diffs(a.get(k),b.get(k),p+'/'+str(k)) for k in sorted(a.keys()|b.keys())),[])
 if isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b): return [(p,[len(a),len(b)])]
  return sum((diffs(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [(p,[a,b])]
d=diffs(reports['baseline'],reports['candidate']);allowed={'/wall_elapsed_ms','/sequence_controls/0/branch'}
for i in range(4):allowed.update({f'/shots/{i}/sha256',f'/shots/{i}/diadem_branch'})
for key in ['source_sha256','source_after_sha256']:
 for lod in ['', '-mid','-far']:allowed.add(f'/{key}/res://assets/heroes/rama-hero{lod}.glb')
assert {p for p,_ in d}==allowed and len(d)==16
checks={
 'both_runs_completed_four_views':all(r['complete'] is True and r['raw_pngs']==4 and r['engine_exit']==0 for r in runs.values()),
 'same_unmodified_engine':all(r['engine_sha256']=='dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f' for r in runs.values()),
 'same_runner_and_helper':runs['baseline']['runner_sha256']==runs['candidate']['runner_sha256'] and runs['baseline']['helper_sha256']==runs['candidate']['helper_sha256'],
 'same_copied_starting_caches':all(runs['baseline'][k]==runs['candidate'][k] for k in ['shader_cache_seed','godot_shader_cache_seed']),
 'both_sources_and_cache_seeds_unchanged':all(r['complete'] is True and reports[b]['source_unchanged'] is True for b,r in runs.items()),
 'exact_expected_metadata_differences':len(d)==16,
 'all_164_final_bones_equal':all(a['rendered_pose_globals']==b['rendered_pose_globals'] and len(a['rendered_pose_globals'])==164 for a,b in zip(reports['baseline']['shots'],reports['candidate']['shots'])),
 'camera_lighting_secondary_morph_time_lod_equal':all(all(a[k]==b[k] for k in ['camera','light','secondary','face','motion','lod','physics_frame','render_frame','tree_paused']) for a,b in zip(reports['baseline']['shots'],reports['candidate']['shots'])),
 'all_original_pngs_verified':True,
 'both_project_and_private_store_inventories_verified':True,
 'no_engine_errors':all(not any(k.startswith(('ERROR:','SCRIPT ERROR:')) for k in v) for v in warnings.values())}
assert all(checks.values())
comparison={'passed':True,'checks':checks,'passed_count':len(checks),'differences':d,'warnings':warnings,'scope':'Source-pinned staged rest and public ability windup originals; no continuous motion, all-LOD visual, cold launch, hardware FPS or release acceptance.'}
(dest/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
for name in ['run_focus.py','snapshot.py']:cp(repo/'tools/graphics-six'/name,dest/'tools'/name)
for rel in ['tools/graphics-six/s4_diadem_capture.gd','tools/visual-rounds/capture_groom.gd','tools/visual-rounds/capture.gd']:cp(work/'baseline'/rel,dest/'tools'/Path(rel).name)
cp(Path(__file__),dest/'tools/archive_actual_pair.py')
for name in ['run.json','godot.log','xvfb.log']:cp(Path('/tmp/yuga-s4-diadem-wrapper-preflight-r1-logs')/name,dest/'wrapper-preflight'/name)
cp(Path('/tmp/yuga-s4-diadem-wrapper-preflight-r1/preflight.json'),dest/'wrapper-preflight/preflight.json')
review='''# S4 crown comparison: bounded visual improvement

Both frozen branches completed four original 1280×960 Forward+ llvmpipe views with the unmodified public 4.6.3 template engine: baseline 71.921 seconds, candidate 68.705 seconds. Three rest stations are explicitly staged; the fourth uses the real public Piercing Dawn cast at 0.30 seconds of windup. These elapsed times are not hardware FPS measurements.

I inspected all eight original images. The candidate removes the conspicuous floating side loop in profile, follows the rear head contour more closely, and preserves the separate front crest. The rail remains visible in the cast view without a newly visible crown/hand intersection. The front side bends are still angular; broad solid hair, costume/material naturalism and general facial quality remain open. This is acceptance of the bounded lower-rail fit improvement in these near views, not finished hero art or canonical activation. Mid/far posed visuals and continuous motion remain unreviewed.

`comparison.json` passes eleven provenance/comparability checks. All 164 final bone transforms, camera, lighting, secondary state, morph/face state, simulation counters and LOD metadata are exactly equal. The sixteen report differences are only six raw source identities, five branch labels, four PNG hashes and wall elapsed time. Project inventories differ only in three raw GLBs and six compiled SCN/MD5 files; imported descriptors, material inputs and capture helpers are unchanged. Both project/private-store inventories and both source cache trees were verified after execution.

Both runs copied the same 112 Godot and 101 Mesa cache files from the successful unmodified cold control into fresh XDG directories. The seed archive and every member are bound by `../../G0/template-baseline-cold-600-r1/cache-preservation.json` and its `cache-scope-clarification.json`. The installed editor and the inactive priority-patched diagnostic binary were not used. The two logs each retain 63 RGB8-to-RGBA8 conversion warnings and no engine errors; these are not warning-free runs.

Commands and environments are retained in each `run.json`; all eight PNGs, full capture reports/logs, source inventories and exact wrapper/helper bytes are archived here. The actual source/candidate import reconstruction is recorded by `../W3/review-preparation-r1.json`, `../W3/review-receipt-r1.json` and the original asset folder's `CAPTURE_HANDOFF.md`. No canonical runtime or asset file was changed by this capture.
'''
(dest/'REVIEW.md').write_text(review)
artifacts={p.relative_to(dest).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(dest.rglob('*')) if p.is_file()}
receipt={'schema':1,'passed':True,'checks':len(checks),'original_pngs':8,'source_snapshots':markers,'artifacts':artifacts,'scope':'Bounded source-pinned crown fit comparison; source promotion remains coordinator-owned.'}
(dest/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'path':str(dest),'receipt_sha256':sha(dest/'receipt.json'),'review_sha256':sha(dest/'REVIEW.md'),'artifacts':len(artifacts),'checks':len(checks)},indent=2))
