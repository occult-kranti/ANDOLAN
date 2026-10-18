"""Stage minimal R6 hero importer from frozen f8 accepted baseline. Never run Godot."""
import argparse,hashlib,json,os,re,shutil,sys
from pathlib import Path
REPO=Path('/workspace/ANDOLAN/games/yuga-native')
FROZEN=Path('/tmp/yuga-hair-r5-review-r1/baseline')
FROZEN_PIN='20aed49da1db66b48a2dcac9f0ced2afa9eb08753293a8bda943e7c256fab63e'
RECIPE=Path(__file__).resolve().parent
W=RECIPE
OUT=W.parent/'candidate-project';BASELINE=W.parent/'baseline-project';OVERLAY=W.parent/'current-source-overlay'
sys.path.insert(0,str(RECIPE/'runner'));import snapshot
SOURCE=REPO/'art/hero-finish/hair-collected-r6/candidate-r1'
ENGINE=Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
ENGINE_PIN='f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
MANIFEST_PIN='81ceaecd8c8fb550c1b0c9072da186e36d4c7ebfc99959d6ec88263ae5b15eb8'
BASE_PINS={'near':'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e','mid':'b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005','far':'aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a'}
def sha(p):return snapshot.digest(Path(p))
def inventory(paths,root):return {str(p.relative_to(root)):snapshot.metadata(p)for p in paths if p.is_file()}
def copy(source,target):target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
def link(source,target):target.parent.mkdir(parents=True,exist_ok=True);os.link(source,target)
def main():
 global W,OUT,BASELINE,OVERLAY
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work',type=Path,required=True);args=ap.parse_args();work=args.work.resolve();assert not work.exists()and work.parent==Path('/tmp'),'Fresh direct /tmp work path required'
 assert snapshot.digest(FROZEN/snapshot.MARKER)==FROZEN_PIN
 assert sha(REPO/'docs/evidence/desktop-finish/hair-collected-r6/W2/receipt.json')=='4e2c12b95c9e02cc1822a26c6b2f2acde31abf34eec863327472ca0b61777059'
 assert sha(REPO/'docs/evidence/desktop-finish/hair-collected-r6/W3-source-review/receipt.json')=='6b708e26c10b8d3617283e62060b98ecc3dff588ad322db8776acb4a95d81821'
 raw_bytes=sum(f.stat().st_size for f in SOURCE.glob('*.glb'));assert shutil.disk_usage('/tmp').free>raw_bytes+768*1024**2,'Preserve 500 MiB diagnostic/package reserve plus 256 MiB working headroom'
 W=work/'evidence';OUT=work/'candidate-project';BASELINE=work/'baseline-project';OVERLAY=work/'current-source-overlay';W.mkdir(parents=True)
 for original in RECIPE.rglob('*'):
  if original.is_file()and '__pycache__'not in original.parts:copy(original,W/original.relative_to(RECIPE))
 assert not any(p.exists()for p in [OUT,BASELINE,OVERLAY,W/'import-preparation.json'])
 frozen=snapshot.verify(FROZEN);assert sha(ENGINE)==ENGINE_PIN and sha(SOURCE/'manifest.json')==MANIFEST_PIN
 manifest=json.loads((SOURCE/'manifest.json').read_text());assert manifest['inactive']
 canonical={n:item for n,item in frozen['files'].items()if not n.startswith('.godot/')}
 source_map={n:str(FROZEN/n)for n in canonical};retained=list(canonical);changed=[];added=[];omitted=[]
 compiled={n for n in frozen['files']if n.startswith('.godot/imported/')};imports=snapshot.imports(FROZEN)
 auxiliary={n:frozen['files'][n]for n in snapshot.AUX_FILES if n in frozen['files']}
 for name,item in auxiliary.items():copy(FROZEN/name,OVERLAY/name);assert snapshot.metadata(OVERLAY/name)==item
 settings=(FROZEN/'project.godot').read_text();line='run/main_scene="res://scenes/boot.tscn"\n';assert settings.count(line)==1;private=settings.replace(line,'')
 before=inventory([FROZEN/n for n in frozen['files']],FROZEN)
 for project in [OUT,BASELINE]:
  (project/'assets/heroes').mkdir(parents=True);(project/'project.godot').write_text(private)
 for level,row in manifest['levels'].items():
  name=Path(row['output']).name;rel=Path('assets/heroes')/name
  assert sha(SOURCE/name)==row['output_sha256'] and sha(FROZEN/rel)==BASE_PINS[level]
  assert sha(FROZEN/(str(rel)+'.import'))==frozen['files'][str(rel)+'.import']['sha256']
  copy(SOURCE/name,OUT/rel);copy(FROZEN/(str(rel)+'.import'),OUT/(str(rel)+'.import'))
 for f in sorted((FROZEN/'assets/heroes').glob('rama-hero*')):
  if f.is_file():link(f,BASELINE/f.relative_to(FROZEN))
 for name in sorted(compiled):link(FROZEN/name,BASELINE/name)
 for name in auxiliary:copy(OVERLAY/name,BASELINE/name)
 command=['env','LP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','XDG_CACHE_HOME='+str(W.parent/'user/cache'),'XDG_CONFIG_HOME='+str(W.parent/'user/config'),'XDG_DATA_HOME='+str(W.parent/'user/data'),'taskset','-c','0,1','timeout','120s',str(ENGINE),'--headless','--path',str(OUT),'--editor','--import','--quit']
 report={'schema':1,'scope':'File staging only; W1 owns authorized engine execution. Reuses exact retained f8/current-runtime accepted baseline from R5; no mutable canonical input or old R5 image substitution.','candidate_project':str(OUT),'baseline_cached_project':str(BASELINE),'frozen_source':str(FROZEN),'shared_base':str(FROZEN),'frozen_marker_sha256':sha(FROZEN/snapshot.MARKER),'shared_marker_sha256':sha(FROZEN/snapshot.MARKER),'candidate_manifest':str(SOURCE/'manifest.json'),'candidate_manifest_sha256':MANIFEST_PIN,'canonical_raw_pins':BASE_PINS,'independent_source_review_sha256':'6b708e26c10b8d3617283e62060b98ecc3dff588ad322db8776acb4a95d81821','prepare_sha256':sha(__file__),'probe_sha256':sha(W/'import_semantics.gd'),'engine_sha256':sha(ENGINE),'command':command,'project_settings':{'canonical_sha256':sha(FROZEN/'project.godot'),'private_sha256':sha(OUT/'project.godot'),'only_removed_line':line.rstrip(),'all_render_and_import_settings_retained':True},'frozen_before':before,'candidate_before':inventory(sorted(OUT.rglob('*')),OUT),'baseline_before':inventory(sorted(BASELINE.rglob('*')),BASELINE),'current_capture_source':{'canonical_root':str(FROZEN),'files':canonical,'source_map':source_map,'retained_frozen_files':retained,'copied_current_changes':changed,'copied_current_additions':added,'omitted_obsolete_helpers':omitted,'copied_auxiliary':auxiliary,'compiled_files':{n:frozen['files'][n]for n in sorted(compiled)},'canonical_imports':imports,'frozen_source_sha256':sha(FROZEN/snapshot.MARKER),'overlay':str(OVERLAY)},'space':{'tmp_free_bytes_after':shutil.disk_usage('/tmp').free,'copied_new_raw_bytes':sum(p.stat().st_size for p in OUT.rglob('*.glb')),'full_repo_copies':0,'capture_branches':'Not created yet; will hardlink verified immutable files, copying only mutable auxiliary caches.'}}
 assert snapshot.verify(FROZEN)==frozen
 (W/'import-preparation.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Minimal R6 import staged; no engine run. Current changes',len(changed),'additions',len(added),'omitted',omitted,'compiled identity',len(compiled),'tmp free',report['space']['tmp_free_bytes_after'])
if __name__=='__main__':main()
