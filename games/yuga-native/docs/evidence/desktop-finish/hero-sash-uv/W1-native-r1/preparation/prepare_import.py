"""Prepare private sash import only. No engine, canonical or shared-store write."""
import hashlib,json,re,shutil,sys
from pathlib import Path
REPO=Path('/workspace/ANDOLAN/games/yuga-native')
ROOT=Path('/tmp/yuga-s4-smooth-review-r1/candidate')
SHARED=Path('/tmp/yuga-desktop-recovery-r1/current-project')
W=Path(__file__).resolve().parent
OUT=W.parent/'candidate-project';BASELINE=W.parent/'baseline-project'
sys.path.insert(0,str(SHARED/'tools/graphics-six'))
import snapshot
SOURCE=REPO/'art/hero-finish/sash-texel-r1/candidate-r2'
ENGINE=Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
ENGINE_PIN='f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(paths,root):return {str(p.relative_to(root)):{'sha256':sha(p),'bytes':p.stat().st_size}for p in paths if p.is_file()}
def main():
 assert not OUT.exists() and not BASELINE.exists() and not(W/'import-preparation.json').exists()
 base=snapshot.verify(ROOT);shared=snapshot.verify(SHARED);assert sha(ENGINE)==ENGINE_PIN
 manifest=json.loads((SOURCE/'manifest.json').read_text());assert manifest['scale_uv']==[.2,.95]
 for row in manifest['lods']:
  assert sha(ROOT/'assets/heroes'/row['file'])==row['input_sha256']
  assert sha(SOURCE/row['file'])==row['output_sha256']
 settings=(ROOT/'project.godot').read_text();line='run/main_scene="res://scenes/boot.tscn"\n';assert settings.count(line)==1;private=settings.replace(line,'')
 sources=[ROOT/'project.godot',ROOT/'.godot/uid_cache.bin']+sorted((ROOT/'assets/heroes').glob('rama-hero*'))+sorted((ROOT/'.godot/imported').glob('*'))
 before=inventory(sources,ROOT)
 for project in [OUT,BASELINE]:
  (project/'assets/heroes').mkdir(parents=True);(project/'project.godot').write_text(private)
 for row in manifest['lods']:
  rel=Path('assets/heroes')/row['file'];shutil.copyfile(SOURCE/row['file'],OUT/rel);shutil.copyfile(ROOT/(str(rel)+'.import'),OUT/(str(rel)+'.import'))
 for p in sorted((ROOT/'assets/heroes').glob('rama-hero*')):
  if p.is_file():shutil.copyfile(p,BASELINE/p.relative_to(ROOT))
 (BASELINE/'.godot/imported').mkdir(parents=True)
 for p in sorted((ROOT/'.godot/imported').glob('*')):
  if p.is_file():shutil.copyfile(p,BASELINE/p.relative_to(ROOT))
 uid=ROOT/'.godot/uid_cache.bin'
 if uid.exists():shutil.copyfile(uid,BASELINE/'.godot/uid_cache.bin')
 command=['env','LP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','OMP_NUM_THREADS=1','MKL_NUM_THREADS=1','XDG_CACHE_HOME='+str(W.parent/'user/cache'),'XDG_CONFIG_HOME='+str(W.parent/'user/config'),'XDG_DATA_HOME='+str(W.parent/'user/data'),'taskset','-c','0,1','timeout','120s',str(ENGINE),'--headless','--path',str(OUT),'--editor','--import','--quit']
 report={'schema':1,'scope':'Source preparation only. Import execution and semantic comparison pending.','candidate_project':str(OUT),'baseline_cached_project':str(BASELINE),'frozen_source':str(ROOT),'shared_base':str(SHARED),'shared_marker_sha256':sha(SHARED/snapshot.MARKER),'frozen_marker_sha256':sha(ROOT/snapshot.MARKER),'shared_files':len(shared['files']),'frozen_files':len(base['files']),'candidate_manifest':str(SOURCE/'manifest.json'),'candidate_manifest_sha256':sha(SOURCE/'manifest.json'),'prepare_sha256':sha(__file__),'probe_sha256':sha(W/'import_semantics.gd'),'engine_sha256':sha(ENGINE),'command':command,'project_settings':{'frozen_sha256':sha(ROOT/'project.godot'),'private_sha256':sha(OUT/'project.godot'),'only_removed_line':line.rstrip(),'all_render_and_import_settings_retained':True},'frozen_before':before,'candidate_before':inventory(sorted(OUT.rglob('*')),OUT),'baseline_before':inventory(sorted(BASELINE.rglob('*')),BASELINE)}
 snapshot.verify(ROOT);snapshot.verify(SHARED)
 (W/'import-preparation.json').write_text(json.dumps(report,indent=2)+'\n');print('Private sash projects prepared; no engine run.')
if __name__=='__main__':main()
