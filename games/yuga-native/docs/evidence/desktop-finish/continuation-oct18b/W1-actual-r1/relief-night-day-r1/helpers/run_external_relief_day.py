#!/usr/bin/env python3
"""Bounded exact-PCK world fixture transport; no project, import or asset copy."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time,signal,gzip
W=Path('/workspace/scratch/yuga-next-W1-r1');OLD=Path('/workspace/scratch/yuga-continuation-W1-r1')
ENGINE=OLD/'package-r2-extracted/godot';PCK=ENGINE.with_name('yuga-native.pck');ARCHIVE=Path('/workspace/scratch/yuga-continuation-W3-public-audit-r1/yuga-native-linux-x86_64.zip');EXTRACTION=OLD/'package-r2-extraction-report.json'
SEED=OLD/'package-r2-warm-r1/user'
FLOOR=500*1024**2
EXPECTED={'runtime':'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e','pck':'f2be4e20a0f3ea3915c5ab94e3896278ab4778991e80c6c8abaadc5209511a59','archive':'781d904d2f6986f423274cf23ecdc16a35df65df755db5171a97a152a3c88aa8','extraction':'40c42d5bc098992b2587938aa1a2aabb89db874814647ef94491afb86aedf77a'}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inventory(p):return {str(x.relative_to(p)):sha(x) for x in p.rglob('*') if x.is_file()}
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--helper',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--display',type=int,default=178);a.add_argument('--dry-run',action='store_true');a.add_argument('--fixture-arg',action='append',default=[]);args=a.parse_args();out=args.output;logs=out.with_name(out.name+'-logs')
 assert out.is_absolute() and not out.exists() and not logs.exists()
 inputs={k:sha(p) for k,p in [('runtime',ENGINE),('pck',PCK),('archive',ARCHIVE),('extraction',EXTRACTION)]};assert inputs==EXPECTED
 extraction=json.loads(EXTRACTION.read_text());members=extraction['members'];assert all(sha(ENGINE.parent/n)==v['sha256'] for n,v in members.items())
 controls=json.loads((args.helper.parent/'controls.json').read_text());assert all(sha(Path(p))==h for p,h in controls['files'].items())
 command=[str(ENGINE),'--main-pack',str(PCK),'--display-driver','x11','--rendering-method','forward_plus','--audio-driver','Dummy','--disable-vsync','--fixed-fps','30','--script',str(args.helper),'--','--output='+str(out)]+args.fixture_arg
 record={'inputs':inputs,'extraction_archive_alias':'Retained independently downloaded byte-identical public Linux ZIP; original extraction receipt unchanged.','command':command,'minimum_free_bytes':FLOOR,'source':'79e5c15d8a3657e16fda67acb277b2406120dcd1','docs_head':'37ed400e53c215585aa6f40bb9534390f1047273','fixture':str(args.helper),'helper_sha256':sha(args.helper),'controls':controls,'affinity':[0,1],'LP_NUM_THREADS':'2','scope':'Exact shipped PCK with external bounded review helper. Each helper explicitly declares its staging/overrides; no ordinary playthrough, cold-cache or temporal acceptance inferred.','transport_sha256':sha(Path(__file__)),'controls_sha256':sha(args.helper.parent/'controls.json')}
 if args.dry_run:print(json.dumps(record,indent=2));return
 assert shutil.disk_usage(W).free>=FLOOR
 os.sched_setaffinity(0,{0,1});logs.mkdir(parents=True)
 runtime=Path('/workspace/tooling/native-render/runtime')
 profile=W/'water-baseline-actual-r2-logs/user'
 assert profile.is_dir()
 preferences=[f for f in profile.rglob('*') if f.is_file() and not any(x in f.relative_to(profile).parts for x in ['cache','shader_cache','logs'])]
 assert not preferences,'Owned static profile requires explicit reviewed preference reset before reuse'
 before=inventory(profile);meta=logs/'owned-profile-before.json.gz';meta.write_bytes(gzip.compress(json.dumps(before,sort_keys=True).encode(),mtime=0))
 record['owned_profile_reuse']={'path':str(profile),'cache_scope':'Warm cache reused serially from this continuation static-water fixture; not a historical qualified profile. No fresh-cache/performance claim.','preferences_reset':'No persistent preferences/bindings files present; defaults retained, no preference copy/removal.','before_inventory_sha256':sha(meta),'before_file_count':len(before)}
 env=os.environ.copy();env.update(VK_ICD_FILENAMES=str(runtime/'usr/share/vulkan/icd.d/lvp_icd.json'),LD_LIBRARY_PATH=str(runtime/'usr/lib/x86_64-linux-gnu'),LP_NUM_THREADS='2',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',DISPLAY=':'+str(args.display))
 for key,name in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
  p=profile/name;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
 env['MESA_SHADER_CACHE_DIR']=str(profile/'cache/mesa')
 record['preferences_copied']=False;record['root_reserved_actual_growth_bytes']=4*1024**2;record['root_reserved_batch_bytes']=12*1024**2
 game=server=None;began=time.monotonic();record['started_unix']=time.time();record['free_before_bytes']=shutil.disk_usage(W).free
 try:
  assert not Path('/tmp/.X11-unix/X'+str(args.display)).exists()
  with (logs/'xvfb.log').open('w') as xf,(logs/'godot.log').open('w') as gf:
   server=subprocess.Popen([str(runtime/'usr/bin/Xvfb'),':'+str(args.display),'-screen','0','960x540x24','-nolisten','tcp','-extension','MIT-SHM','-ac'],env=env,stdout=xf,stderr=subprocess.STDOUT)
   until=time.monotonic()+5
   while not Path('/tmp/.X11-unix/X'+str(args.display)).exists():
    assert time.monotonic()<until;time.sleep(.05)
   game=subprocess.Popen(command,env=env,stdout=gf,stderr=subprocess.STDOUT);record['engine_pid']=game.pid
   floor_min=record['free_before_bytes']
   while game.poll() is None:
    free=shutil.disk_usage(W).free;floor_min=min(floor_min,free)
    if record['free_before_bytes']-free>4*1024**2:raise RuntimeError('Root4MiB peractual includingcachegrowth reservation exceeded')
    if free<FLOOR:raise RuntimeError('500MiB actual floor crossed')
    if time.monotonic()-began>600:raise TimeoutError('Bounded600s capture deadline')
    time.sleep(.25)
   record['engine_exit']=game.returncode;record['minimum_observed_free_bytes']=floor_min
  report=json.loads((out/'capture.json').read_text());record['capture_complete']=report['complete'];record['capture_sha256']=sha(out/'capture.json')
  record['inputs_unchanged']=all(sha(p)==EXPECTED[k] for k,p in [('runtime',ENGINE),('pck',PCK),('archive',ARCHIVE),('extraction',EXTRACTION)])
  record['extracted_members_unchanged']=all(sha(ENGINE.parent/n)==v['sha256'] for n,v in members.items())
  after_meta=logs/'owned-profile-after.json.gz';after_meta.write_bytes(gzip.compress(json.dumps(inventory(profile),sort_keys=True).encode(),mtime=0));record['owned_profile_reuse']['after_inventory_sha256']=sha(after_meta)
  record['controls_unchanged']=sha(args.helper.parent/'controls.json')==record['controls_sha256'] and sha(Path(__file__))==record['transport_sha256'] and all(sha(Path(p))==h for p,h in controls['files'].items())
  text=(logs/'godot.log').read_text();record['diagnostics']={s:text.count(s) for s in ['SCRIPT ERROR:','ERROR:','WARNING:']}
  record['complete']=game.returncode==0 and report['complete'] and record['inputs_unchanged'] and record['extracted_members_unchanged'] and record['controls_unchanged'] and not any(record['diagnostics'].values())
 except BaseException as e:record['complete']=False;record['failure']=str(e)
 finally:
  if game and game.poll() is None:
   game.terminate()
   try:game.wait(timeout=5)
   except subprocess.TimeoutExpired:game.kill();game.wait()
  if server:
   server.terminate();server.wait(timeout=5)
  record['elapsed_seconds']=time.monotonic()-began;record['free_after_bytes']=shutil.disk_usage(W).free;save(logs/'receipt.json',record)
 print(json.dumps({'complete':record['complete'],'elapsed_seconds':record['elapsed_seconds'],'failure':record.get('failure')}));raise SystemExit(0 if record['complete'] else 1)
if __name__=='__main__':main()
