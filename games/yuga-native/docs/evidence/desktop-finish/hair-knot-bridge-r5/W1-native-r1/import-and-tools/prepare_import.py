"""Stage minimal R5 hero importer and one current-source overlay. Never run Godot."""
import hashlib,json,os,re,shutil,sys
from pathlib import Path
REPO=Path('/workspace/ANDOLAN/games/yuga-native')
FROZEN=Path('/tmp/yuga-hair-review-r1/baseline')
W=Path(__file__).resolve().parent
OUT=W.parent/'candidate-project';BASELINE=W.parent/'baseline-project';OVERLAY=W.parent/'current-source-overlay'
sys.path.insert(0,str(REPO/'tools/graphics-six'));import snapshot
SOURCE=REPO/'art/hero-finish/hair-knot-bridge-r5/candidate-r1'
ENGINE=Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
ENGINE_PIN='f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
MANIFEST_PIN='becd2571f2aaa88c62d80c56a0d3036368205840bd045f3730bb1c6a86d1f402'
BASE_PINS={'near':'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e','mid':'b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005','far':'aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a'}
def sha(p):return snapshot.digest(Path(p))
def inventory(paths,root):return {str(p.relative_to(root)):snapshot.metadata(p)for p in paths if p.is_file()}
def copy(source,target):target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
def link(source,target):target.parent.mkdir(parents=True,exist_ok=True);os.link(source,target)
def main():
 assert not any(p.exists()for p in [OUT,BASELINE,OVERLAY,W/'import-preparation.json'])
 frozen=snapshot.verify(FROZEN);assert sha(ENGINE)==ENGINE_PIN and sha(SOURCE/'manifest.json')==MANIFEST_PIN
 manifest=json.loads((SOURCE/'manifest.json').read_text());assert manifest['inactive']
 canonical={n:snapshot.metadata(REPO/n)for n in snapshot.paths(REPO)if not n.startswith('.godot/')}
 source_map={};added=[];changed=[];retained=[]
 for name,item in canonical.items():
  if frozen['files'].get(name)==item:source_map[name]=str(FROZEN/name);retained.append(name)
  else:
   target=OVERLAY/name;copy(REPO/name,target);assert snapshot.metadata(target)==item;source_map[name]=str(target)
   (changed if name in frozen['files']else added).append(name)
 omitted=sorted(n for n in frozen['files']if not n.startswith('.godot/')and n not in canonical)
 compiled=set();imports=snapshot.imports(REPO)
 for row in imports:
  for name in row['outputs']:
   compiled.add(name);md5=str(Path(name).with_suffix('.md5'))
   if not(REPO/md5).exists()and Path(name).suffix=='.ctex':md5=str(Path(name).with_suffix('').with_suffix('.md5'))
   compiled.add(md5)
 for name in compiled:assert snapshot.metadata(REPO/name)==frozen['files'][name]
 auxiliary={n:snapshot.metadata(REPO/n)for n in snapshot.AUX_FILES if(REPO/n).is_file()}
 for name,item in auxiliary.items():copy(REPO/name,OVERLAY/name);assert snapshot.metadata(OVERLAY/name)==item
 canonical_pin={n:snapshot.metadata(REPO/n)for n in canonical};assert canonical_pin==canonical
 settings=(REPO/'project.godot').read_text();line='run/main_scene="res://scenes/boot.tscn"\n';assert settings.count(line)==1;private=settings.replace(line,'')
 before=inventory([FROZEN/n for n in frozen['files']],FROZEN)
 for project in [OUT,BASELINE]:
  (project/'assets/heroes').mkdir(parents=True);(project/'project.godot').write_text(private)
 for level,row in manifest['levels'].items():
  name=Path(row['output']).name;rel=Path('assets/heroes')/name
  assert sha(SOURCE/name)==row['output_sha256'] and sha(REPO/rel)==sha(FROZEN/rel)==BASE_PINS[level]
  assert sha(REPO/(str(rel)+'.import'))==sha(FROZEN/(str(rel)+'.import'))
  copy(SOURCE/name,OUT/rel);copy(REPO/(str(rel)+'.import'),OUT/(str(rel)+'.import'))
 for f in sorted((FROZEN/'assets/heroes').glob('rama-hero*')):
  if f.is_file():link(f,BASELINE/f.relative_to(FROZEN))
 for name in sorted(compiled):link(FROZEN/name,BASELINE/name)
 for name in auxiliary:copy(OVERLAY/name,BASELINE/name)
 command=['env','LP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','XDG_CACHE_HOME='+str(W.parent/'user/cache'),'XDG_CONFIG_HOME='+str(W.parent/'user/config'),'XDG_DATA_HOME='+str(W.parent/'user/data'),'taskset','-c','0,1','timeout','120s',str(ENGINE),'--headless','--path',str(OUT),'--editor','--import','--quit']
 report={'schema':1,'scope':'File staging only; W1 owns authorized engine execution. Current canonical runtime is separately frozen as a small overlay; prior R4 pair is untouched.','candidate_project':str(OUT),'baseline_cached_project':str(BASELINE),'frozen_source':str(FROZEN),'shared_base':str(FROZEN),'frozen_marker_sha256':sha(FROZEN/snapshot.MARKER),'shared_marker_sha256':sha(FROZEN/snapshot.MARKER),'candidate_manifest':str(SOURCE/'manifest.json'),'candidate_manifest_sha256':MANIFEST_PIN,'canonical_raw_pins':BASE_PINS,'prepare_sha256':sha(__file__),'probe_sha256':sha(W/'import_semantics.gd'),'engine_sha256':sha(ENGINE),'command':command,'project_settings':{'canonical_sha256':sha(REPO/'project.godot'),'private_sha256':sha(OUT/'project.godot'),'only_removed_line':line.rstrip(),'all_render_and_import_settings_retained':True},'frozen_before':before,'candidate_before':inventory(sorted(OUT.rglob('*')),OUT),'baseline_before':inventory(sorted(BASELINE.rglob('*')),BASELINE),'current_capture_source':{'canonical_root':str(REPO),'files':canonical,'source_map':source_map,'retained_frozen_files':retained,'copied_current_changes':changed,'copied_current_additions':added,'omitted_obsolete_helpers':omitted,'copied_auxiliary':auxiliary,'compiled_files':{n:frozen['files'][n]for n in sorted(compiled)},'canonical_imports':imports,'frozen_source_sha256':sha(FROZEN/snapshot.MARKER),'overlay':str(OVERLAY)},'space':{'tmp_free_bytes_after':shutil.disk_usage('/tmp').free,'copied_new_raw_bytes':sum(p.stat().st_size for p in OUT.rglob('*.glb')),'full_repo_copies':0,'capture_branches':'Not created yet; will hardlink verified immutable files, copying only mutable auxiliary caches.'}}
 assert snapshot.verify(FROZEN)==frozen
 (W/'import-preparation.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Minimal R5 import staged; no engine run. Current changes',len(changed),'additions',len(added),'omitted',omitted,'compiled identity',len(compiled),'tmp free',report['space']['tmp_free_bytes_after'])
if __name__=='__main__':main()
