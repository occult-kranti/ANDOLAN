from pathlib import Path
import json,hashlib,shutil,gzip,tarfile,io
root=Path('/workspace/ANDOLAN/games/yuga-native');out=Path('/tmp/yuga-public463-template-baseline-cold-600-r1');logs=out.with_name(out.name+'-logs');dst=root/'docs/evidence/desktop-finish/G0/template-baseline-cold-600-r1';dst.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in sorted(out.iterdir()):
 if p.is_file():shutil.copyfile(p,dst/p.name)
(dst/'logs').mkdir()
for name in ['run.json','godot.log','xvfb.log','driver-window-observer.json','native-gdb-120s.log']:shutil.copyfile(logs/name,dst/'logs'/name)
(dst/'tools').mkdir()
frozen=root/'docs/evidence/desktop-finish/G0/workspace-recovery-r1/tools'
for n in ['run_focus.py','snapshot.py']:shutil.copyfile(frozen/n,dst/'tools'/n)
shutil.copyfile('/workspace/tooling/godot-public-4.6.3/priority-candidate-r1/observe_cold_600.py',dst/'tools/observe_cold_600.py')
shutil.copyfile(__file__,dst/'tools/archive_cold_600.py')
project=Path('/tmp/yuga-desktop-recovery-r1/compact-project-r1')
shutil.copyfile(project/'tools/graphics-six/capture_compact_screens.gd',dst/'tools/capture_compact_screens.gd')
shutil.copyfile(project/'.graphics-six-snapshot.json',dst/'snapshot-source.json')
cache_roots={'godot':logs/'user/data/godot/app_userdata/YUGA • Confluence/shader_cache','mesa':logs/'user/cache/mesa'}
cache={}
for label,path in cache_roots.items():
 for f in sorted(path.rglob('*')):
  if f.is_file():
   assert not f.is_symlink();name=label+'/'+f.relative_to(path).as_posix();cache[name]={'sha256':sha(f),'bytes':f.stat().st_size}
archive=dst/'generated-shader-caches.tar.gz'
with archive.open('xb') as raw:
 with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for name,pin in sorted(cache.items()):
    label,rel=name.split('/',1);f=cache_roots[label]/rel;b=f.read_bytes();assert hashlib.sha256(b).hexdigest()==pin['sha256'];ti=tarfile.TarInfo(name);ti.size=len(b);ti.mode=0o644;ti.mtime=0;tar.addfile(ti,io.BytesIO(b))
with tarfile.open(archive,'r:gz') as tar:
 members={}
 for ti in tar:
  assert ti.isfile() and '..' not in Path(ti.name).parts and not ti.name.startswith('/');b=tar.extractfile(ti).read();members[ti.name]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
assert members==cache
for name,pin in cache.items():
 label,rel=name.split('/',1);assert sha(cache_roots[label]/rel)==pin['sha256']
cache_rec={'passed':True,'scope':'Generated output caches from successful diagnostic candidate. Exact lossless persistent archive; no preferences or source files. Never used in either fresh-cache baseline control.','archive':archive.name,'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'members':cache,'categories':{label:{'files':sum(n.startswith(label+'/') for n in cache),'bytes':sum(v['bytes'] for n,v in cache.items() if n.startswith(label+'/'))} for label in cache_roots}}
(dst/'cache-preservation.json').write_text(json.dumps(cache_rec,indent=2)+'\n')
r=json.loads((dst/'logs/run.json').read_text());c=json.loads((dst/'capture.json').read_text());o=json.loads((dst/'logs/driver-window-observer.json').read_text());assert r['complete'] and r['engine_exit']==0 and len(c['shots'])==8 and all(x['passed'] is True for x in c['checks']);assert all(sha(dst/x['file'])==x['sha256'] for x in c['shots'])
checks={'complete_engine_exit_zero':True,'fixture_12_checks_pass':len(c['checks'])==12,'eight_original_hashes_match':True,'source_unchanged':c['source_unchanged'] is True,'fresh_both_caches':not r['shader_cache_seed'] and not r['godot_shader_cache_seed'],'both_generated_caches_losslessly_preserved':True}
review='# Unmodified cold control also completed\n\nThe unchanged public Godot35e80 template-debug binary completed the same eight-screen fixture using fresh Godot and Mesa directories and600-second overall/no-output limits: engine/runner exit0,301.121 seconds, eight original960×540 framebuffers,12/12 fixture checks. This is a counterexample to a claim that the one-line priority patch was necessary for the successful cold capture. It does not erase the earlier directly observed mutex/group-wait failure.\n\nThe same a02 project fixture, external6cfcc runner, full shaders/assets/imports, CPU0,1, llvmpipe2, viewport inputs, simulation settings and600-second watchdog were used. The only intentional executable difference from the successful candidate is unmodified binarydce0422d rather than patched e69af4f6. Neither cold run used the generated caches from another run. Product and installed-editor files are unchanged. Public-template source/target still differ from the installed editor, so these runs do not qualify that installed build.\n\nA single native attachment near observer120 seconds found active LLVM register-allocation/JIT work (`MachineInstr::addRegisterKilled`, `LiveIntervals::addKillFlags`, `MCJIT::finalizeObject`). The main thread was in the software Vulkan driver wait path, rather than the previously mapped shader-version/group wait. Fifteen-second samples show active CPU use; maximum sampled process RSS was3,263,131,648 bytes. CPU/RSS are diagnostics, not FPS, heap measurements or hardware GPU results. No timeout was extended during execution.\n\nThe independent cold candidate completed in307.595 seconds. Six corresponding PNGs are byte-identical; each of the other two differs at exactly one of518,400 pixels, by at most one8-bit channel level. All per-shot camera/hero/HUD/game-state metadata match after excluding image hashes and global process/physics/drawn counters. Those counters differ because asynchronous boot readiness occurred at different global frames; no pose or clock was manually aligned. `comparison.json` contains exact results, limits and paired source hashes. This is a pixel/state comparison, not a performance benchmark.\n\nBoth generated cache trees are retained losslessly for explicitly declared warm component captures:112 Godot files (14,456,196 bytes),101 Mesa files (6,012,133 bytes),213members total. The tar archive and each extracted name/size/hash were verified against the stopped run. No preferences are included. They were outputs of this fresh control, not inputs.\n\nThe title200% cropped heading and the earlier stated scene/material/character quality limits are still visible. No asset, shader, engine or release promotion follows. The priority candidate remains an inactive diagnostic; repeated randomized/interleaved cold trials would be needed to assess failure incidence or patch effectiveness. Current evidence supports a scheduling-sensitive observed wait failure and a separately measured slow software-compilation path, with at least one successful unmodified cold run.\n'
(dst/'REVIEW.md').write_text(review)
candidate=root/'docs/evidence/desktop-finish/G0/template-priority-cold-600-r1'
cr=json.loads((candidate/'logs/run.json').read_text());rows=[]
import numpy as np
from PIL import Image
for f in sorted(dst.glob('*.png')):
 other=candidate/f.name;x=np.asarray(Image.open(f).convert('RGBA')).astype(np.int16);y=np.asarray(Image.open(other).convert('RGBA')).astype(np.int16);mask=np.any(x!=y,axis=2);diff=np.abs(x-y);bj=json.loads(f.with_suffix('.json').read_text());cj=json.loads(other.with_suffix('.json').read_text());keys=[k for k in sorted(bj.keys()|cj.keys()) if bj.get(k)!=cj.get(k)];metadata_match=all(k in ['sha256','drawn_frame','physics_frame','process_frame'] for k in keys);rows.append({'id':f.name,'baseline_sha256':sha(f),'candidate_sha256':sha(other),'png_byte_identical':f.read_bytes()==other.read_bytes(),'differing_pixels':int(mask.sum()),'total_pixels':int(mask.size),'max_channel_difference':int(diff.max()),'json_differing_top_keys':keys,'other_metadata_equal':metadata_match})
keys=['snapshot_sha256','source_files','helper_sha256','runner_sha256','affinity','thread_limits','godot_worker_pool_limit','render_thread_override','watchdog','shader_cache_seed','godot_shader_cache_seed','preflight'];same={k:r[k]==cr[k] for k in keys};assert all(same.values());assert all(x['other_metadata_equal'] for x in rows)
comparison={'matched_condition_checks':same,'baseline_run_sha256':sha(dst/'logs/run.json'),'candidate_run_sha256':sha(candidate/'logs/run.json'),'baseline_elapsed_s':r['engine_elapsed_s'],'candidate_elapsed_s':cr['engine_elapsed_s'],'paired_originals':rows,'patch_efficacy_established':False,'interpretation':'Both600s cold executions succeeded. Earlier120s baseline nativewait remains observed; scheduling-related failure incidence and patch effectiveness are unresolved.'};(dst/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
receipt={'schema':1,'passed':True,'scope':'Successful unmodified cold control,12fixture checks/8actualscreens. Disconfirms patch necessity in this execution; no general engine/art/performance/release qualification.','checks':checks,'engine_elapsed_s':r['engine_elapsed_s'],'engine_sha256':r['engine_sha256'],'snapshot_sha256':r['snapshot_sha256'],'first_saved_shot_wall_ms':c['checkpoints'][1]['wall_ms'],'artifacts':{str(f.relative_to(dst)):{'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(dst.rglob('*')) if f.is_file()}}
(dst/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'path':str(dst),'receipt_sha256':sha(dst/'receipt.json'),'review_sha256':sha(dst/'REVIEW.md'),'cache_archive_sha256':sha(archive),'cache_archive_bytes':archive.stat().st_size,'cache_members':len(cache)},indent=2))
