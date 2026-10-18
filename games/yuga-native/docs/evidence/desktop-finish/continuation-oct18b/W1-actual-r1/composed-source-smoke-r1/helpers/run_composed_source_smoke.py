from pathlib import Path
import os,json,hashlib,subprocess,time,shutil,gzip,argparse
R=Path('/workspace/ANDOLAN');P=R/'games/yuga-native';W=Path('/workspace/scratch/yuga-next-W1-r1');S=W/'composed-source-smoke-r1';H=W/'harness/capture_composed_source_smoke.gd';ENGINE=Path('/workspace/scratch/yuga-continuation-W1-r1/package-r2-extracted/godot');SOURCE='1236db5036b558be3e90c1e11b816f2a12e384dc';PROFILE=W/'water-baseline-actual-r2-logs/user';FLOOR=500*1024**2;BUDGET=12*1024**2
CRITICAL={'confluence_world.gd':'503093acba1f8b5679e8dfb3bf81beee5a273c9d766ba60d352e3d07035a375d','rama_hero_hud.gd':'572b0b8469c6b9d0b80d39cde5e8389450c9e0d7e8af989c18644f956dd657bc','rama_motion.gd':'d5550b25044ea97c9ce482a130ac73f012c313e96f2029a555abb590e1375b0e','world_water.gdshader':'3f5a6b89b6bdaaea547c51829da558d829445fb63a690d119e21720b8ce27a7e'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024**2),b''):h.update(chunk)
 return h.hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def inventory(root):return {str(p.relative_to(root)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file()}
def prepare():
 assert not S.exists();S.mkdir();files={};tree=subprocess.check_output(['git','ls-tree','-rz',SOURCE,'--',*[str(P.relative_to(R)/d) for d in ['assets','scripts','scenes','shaders','project.godot']]],cwd=R)
 for row in tree.split(b'\0'):
  if not row:continue
  header,path=row.split(b'\t',1);name=path.decode();p=R/name;raw=p.read_bytes();oid=header.split()[2].decode();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,name+' differs from exact commit';files[str(p)]=hashlib.sha256(raw).hexdigest()
 for n,h in CRITICAL.items():assert sha(P/'scripts'/n)==h
 for p in [H,W/'harness/full_world_collector.gd',W/'harness/capture_compact_base.gd',Path('/workspace/scratch/yuga-continuation-W1-r1/package-successor-r2-preparation/tools/ui-campaign/authority_stage.gd'),Path(__file__)]:files[str(p)]=sha(p)
 assert sha(ENGINE)=='e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'
 cache=inventory(P/'.godot');assert cache and (P/'.godot/imported').is_dir();save(S/'canonical-imports-before.json',cache);save(S/'controls.json',{'source_commit':SOURCE,'files':files})
 prefs=[p for p in PROFILE.rglob('*') if p.is_file() and not any(n in p.relative_to(PROFILE).parts for n in ['cache','shader_cache','logs'])];assert not prefs,'Owned profile preferences require explicit reviewed reset'
 save(S/'preparation.json',{'stage':'PREPARATION ONLY; no engine executed','source':SOURCE,'critical':CRITICAL,'runtime_source_files':len(files),'canonical_import_files':len(cache),'canonical_import_bytes':sum(v['bytes'] for v in cache.values()),'profile':str(PROFILE),'profile_bytes':sum(p.stat().st_size for p in PROFILE.rglob('*') if p.is_file()),'output':'Two PNGs +two directgzip full observations +compact jump trace; no regular fullJSON copies','budget_bytes':BUDGET,'minimum_free_bytes':FLOOR,'free_bytes':shutil.disk_usage(W).free,'admission':'Root storage admission required before any engine','context':'Canonical project/imports; no project snapshot,PCK,export,takeover,shader/camera/pose/health override. Input.action_press jump; real shoot/start_reload; callback hold only final200inspection. Warm reused profile, no cache timing claim.'})
 print(json.dumps({'prepared':True,'runtime_files':len(files),'import_files':len(cache),'free':shutil.disk_usage(W).free,'budget':BUDGET}))
def run(preflight):
 ctl=json.loads((S/'controls.json').read_text());assert all(sha(Path(p))==v for p,v in ctl['files'].items());assert inventory(P/'.godot')==json.loads((S/'canonical-imports-before.json').read_text());free=shutil.disk_usage(W).free;admission=S/'storage-admission.json'
 if admission.exists():origin=json.loads(admission.read_text())['free_before_all_engines']
 else:
  assert free-BUDGET>=FLOOR;origin=free;save(admission,{'free_before_all_engines':origin,'total_combined_preflight_actual_budget_bytes':BUDGET,'minimum_free_bytes':FLOOR,'authorization':'Root admission required before this entrypoint is invoked.'})
 assert free>=FLOOR and origin-free<BUDGET
 out=S/('preflight' if preflight else 'actual');logs=S/('preflight-logs' if preflight else 'actual-logs');assert not out.exists() and not logs.exists();logs.mkdir();rt=Path('/workspace/tooling/native-render/runtime');command=[str(ENGINE),'--path',str(P),'--audio-driver','Dummy','--fixed-fps','30','--script',str(H),'--','--output='+str(out)];env=os.environ.copy();env.update(LP_NUM_THREADS='2',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 server=game=None;start=time.monotonic();minimum=free;before_profile=inventory(PROFILE);(logs/'profile-before.json.gz').write_bytes(gzip.compress(json.dumps(before_profile,sort_keys=True).encode(),mtime=0));r={'source':SOURCE,'command':command,'context':'Canonical project and existing imports, no PCK/export or external source overrides','warm_profile':str(PROFILE),'budget_bytes':BUDGET,'minimum_free_bytes':FLOOR,'free_before':free,'free_before_all_engines':origin,'preflight':preflight,'complete':False}
 if preflight:command[1:1]=['--headless'];command.append('--preflight');os.sched_setaffinity(0,{4})
 else:
  os.sched_setaffinity(0,{0,1});command[1:1]=['--display-driver','x11','--rendering-method','forward_plus','--disable-vsync'];env.update(VK_ICD_FILENAMES=str(rt/'usr/share/vulkan/icd.d/lvp_icd.json'),LD_LIBRARY_PATH=str(rt/'usr/lib/x86_64-linux-gnu'),DISPLAY=':178')
 for key,name in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:env[key]=str(PROFILE/name)
 env['MESA_SHADER_CACHE_DIR']=str(PROFILE/'cache/mesa')
 try:
  if not preflight:
   assert not Path('/tmp/.X11-unix/X178').exists();xf=(logs/'xvfb.log').open('w');server=subprocess.Popen([str(rt/'usr/bin/Xvfb'),':178','-screen','0','960x540x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xf,stderr=subprocess.STDOUT)
   until=time.monotonic()+5
   while not Path('/tmp/.X11-unix/X178').exists():assert time.monotonic()<until;time.sleep(.05)
  with (logs/'godot.log').open('w') as log:
   game=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT);r['pid']=game.pid
   while game.poll() is None:
    free_now=shutil.disk_usage(W).free;minimum=min(minimum,free_now)
    if free_now<FLOOR or origin-free_now>BUDGET:raise RuntimeError('12MiB budget or500MiBfloor crossed')
    if time.monotonic()-start>600:raise TimeoutError('600s bounded source smoke')
    time.sleep(.25)
  r['engine_exit']=game.returncode;report=json.loads((out/('preflight.json' if preflight else 'capture.json')).read_text());r['capture_complete']=report['complete'];r['capture_sha256']=sha(out/('preflight.json' if preflight else 'capture.json'));r['sources_unchanged']=all(sha(Path(p))==v for p,v in ctl['files'].items());after=inventory(P/'.godot');r['canonical_imports_unchanged']=after==json.loads((S/'canonical-imports-before.json').read_text());save(logs/'canonical-imports-after.json',after);text=(logs/'godot.log').read_text();r['diagnostics']={n:text.count(n) for n in ['SCRIPT ERROR:','ERROR:','WARNING:']};r['complete']=game.returncode==0 and report['complete'] and r['sources_unchanged'] and r['canonical_imports_unchanged'] and not any(r['diagnostics'].values())
 except BaseException as e:r['failure']=str(e)
 finally:
  if game and game.poll() is None:
   game.terminate()
   try:game.wait(timeout=5)
   except subprocess.TimeoutExpired:game.kill();game.wait()
  if server:server.terminate();server.wait(timeout=5)
  (logs/'profile-after.json.gz').write_bytes(gzip.compress(json.dumps(inventory(PROFILE),sort_keys=True).encode(),mtime=0));r.update(elapsed_seconds=time.monotonic()-start,minimum_observed_free_bytes=minimum,free_after=shutil.disk_usage(W).free);save(logs/'receipt.json',r)
 print(json.dumps(r));raise SystemExit(0 if r['complete'] else 1)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--prepare',action='store_true');a.add_argument('--run',action='store_true');a.add_argument('--preflight',action='store_true');args=a.parse_args()
 if args.prepare:prepare()
 elif args.run:run(args.preflight)
 else:a.error('Explicit preparation or root-admitted run required')
