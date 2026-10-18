from pathlib import Path
import json,hashlib,shutil,gzip,tarfile,io
root=Path('/workspace/ANDOLAN/games/yuga-native');out=Path('/tmp/yuga-public463-template-priority-cold-600-r1');logs=out.with_name(out.name+'-logs');dst=root/'docs/evidence/desktop-finish/G0/template-priority-cold-600-r1';dst.mkdir(exist_ok=False)
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
review='''# Cold candidate completed eight actual screens\n\nThe isolated one-line pipeline-priority engine completed the full eight-screen fixture with fresh Godot and Mesa caches: engine/runner exit0, 307.595 seconds, eight original960×540 framebuffers, and12/12 fixture checks. The first scheduled title screenshot records engine wall158.200 seconds; it is not a measurement of the first drawable frame. The title100/150/200%, live world100/150/200%, suspended F1 overview200%, and F3 guide200% originals are retained unchanged with paired JSON.\n\nThis run separately declared600-second overall/no-output bounds because the earlier matched120-second candidate failure had captured active LLVM code generation. That failed experiment and the unmodified baseline remain unchanged in their own packets. The exact a02 fixture, external6cfcc runner, e69af candidate binary, CPU0,1/llvmpipe2, full original shader/assets and import features were retained. No seed, shader reduction, manual camera/light/pose/health/clock manipulation, or image processing was used. Viewport key injection and content scale changes are declared harness inputs.\n\nAt120.110 seconds the single native attachment captured LLVM register allocation/MCJIT; it exited0 and detached after0.377 seconds. Fifteen-second CPU/RSS samples continued until process exit. Maximum sampled resident memory was3,414,695,936 bytes; this is process RSS, not a heap census or exact peak. Fixed30 simulation steps do not establish30FPS or hardware GPU performance. The renderer is Forward+ on llvmpipe LLVM19.1.7.\n\nIndependent visual inspection of title100/200, world100/200, overview200 and guide200 confirms actual full hero/environment/UI pixels. The title200% YUGA heading is clipped at the top while primary-action focus is revealed; this concrete issue was routed to the screen owner. Normal-size world auxiliary text remains small, and ground stippling/seam aliasing, simplified infantry, and hero face/costume finish remain open art limitations. Guide headings and Back are visible; its list/details use explicit scroll regions. No overall aesthetic, night-state, continuous motion, packaged-build or release acceptance follows from these eight screens.\n\nBoth generated cache trees are preserved losslessly in `generated-shader-caches.tar.gz`:112 Godot files (14,456,196 bytes) and101 Mesa files (6,012,132 bytes),213members total. `cache-preservation.json` binds every name/size/hash, archive hash and extraction recheck. No preferences are included. The archive is retained for explicitly declared future warm experiments; it is not an input to either cold control.\n\nThe unmodified source-built engine with the same600-second bound and an independent candidate repeat remain separate controls. This packet establishes one successful cold diagnostic run; it neither promotes a custom engine nor proves universal deadlock prevention. The installed editor and canonical product remain unchanged.\n'''
(dst/'REVIEW.md').write_text(review)
receipt={'schema':1,'passed':True,'scope':'One successful separately bounded fresh-cache diagnostic,12fixture checks/8actualscreens. No universal engine, art, performance or release qualification.','checks':checks,'engine_elapsed_s':r['engine_elapsed_s'],'engine_sha256':r['engine_sha256'],'snapshot_sha256':r['snapshot_sha256'],'first_saved_shot_wall_ms':c['checkpoints'][1]['wall_ms'],'artifacts':{str(f.relative_to(dst)):{'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(dst.rglob('*')) if f.is_file()}}
(dst/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'path':str(dst),'receipt_sha256':sha(dst/'receipt.json'),'review_sha256':sha(dst/'REVIEW.md'),'cache_archive_sha256':sha(archive),'cache_archive_bytes':archive.stat().st_size,'cache_members':len(cache)},indent=2))
