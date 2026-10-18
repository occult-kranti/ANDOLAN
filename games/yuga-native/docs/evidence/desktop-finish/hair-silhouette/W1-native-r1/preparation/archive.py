from pathlib import Path
import json,hashlib,shutil,tarfile,os
R=Path('/workspace/ANDOLAN/games/yuga-native');E=R/'docs/evidence/desktop-finish';W=Path('/tmp/yuga-hair-import-r1/evidence');B=Path('/tmp/yuga-hair-review-r1');O=E/'hair-silhouette/W1-native-r1';O.mkdir(parents=True,exist_ok=False)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b);assert h(a)==h(b)
proof=json.loads((W/'import-comparison-r1.json').read_text());comparison=json.loads((B/'render-comparison-r2.json').read_text());assert proof['passed']and comparison['passed'];results={};runs={}
for branch in ['baseline','candidate']:
 raw=B/('render-'+branch+'-r1');logs=raw.with_name(raw.name+'-logs');r=json.loads((logs/'run.json').read_text());c=json.loads((raw/'capture.json').read_text());runs[branch]=r;assert r['complete']and r['engine_exit']==0 and c['complete']and c['source_unchanged']and len(c['shots'])==4
 for source,folder in [(raw,'originals'),(logs,'logs'),(B/('preflight-'+branch+'-r1'),'preflight'),(B/('preflight-'+branch+'-r1-logs'),'preflight-logs')]:
  for p in source.iterdir():
   if p.is_file():cp(p,O/branch/folder/p.name)
 cp(B/branch/'.graphics-six-snapshot.json',O/branch/'snapshot.json')
 lines=(logs/'godot.log').read_text().splitlines();warnings=[x for x in lines if x.startswith('WARNING:')];errors=[x for x in lines if x.startswith(('ERROR:','SCRIPT ERROR:'))];assert not errors
 results[branch]={'engine_exit':0,'seconds':r['engine_elapsed_s'],'originals':4,'warnings':len(warnings),'warning_messages':sorted(set(warnings)),'errors':errors,'snapshot_sha256':r['snapshot_sha256'],'engine_sha256':r['engine_sha256'],'helper_sha256':r['helper_sha256'],'runner_sha256':r['runner_sha256'],'source_unchanged':True,'mixer_cleanup':{k:c['audio_cleanup'][k]for k in ['observed_mixer_ticks','wait_usec','budget_usec']}}
a=runs['baseline'];b=runs['candidate'];assert a['shader_cache_seed']==b['shader_cache_seed']and a['godot_shader_cache_seed']==b['godot_shader_cache_seed'];delta=sorted(k for k in a['source_files'] if a['source_files'][k]!=b['source_files'][k]);assert len(delta)==9
for p in W.iterdir():
 if p.is_file():cp(p,O/'preparation'/p.name)
for n in ['render-comparison-r2.json','preflight-comparison-r2.json']:cp(B/n,O/n)
for p in (W/'comparator-rejected-r1').rglob('*'):
 if p.is_file():cp(p,O/'retained-failure'/p.relative_to(W/'comparator-rejected-r1'))
for name in ['run_focus.py','snapshot.py']:cp(Path('/tmp/yuga-hair-review-r1-tools')/name,O/'tools'/name)
cp(W/'hair_capture_cleanup.gd',O/'tools/hair_capture.gd')
for name in ['capture.gd','capture_groom.gd']:cp(B/'baseline/tools/visual-rounds'/name,O/'tools'/name)
inputs=[R/'art/hero-finish/hair-silhouette-r1/candidate-r4-accepted-uv/groom-manifest.json',R/'art/hero-finish/hair-silhouette-r1/capture_review.gd',R/'docs/evidence/desktop-finish/hair-silhouette/W2/import-handoff.json',R/'docs/evidence/desktop-finish/hair-silhouette/W2/receipt.json']
for p in inputs:cp(p,O/'source-inputs'/p.relative_to(R))
refs=[]
for folder in ['sash-texel-r1/candidate-r2','hair-silhouette-r1/candidate-r4-accepted-uv']:
 for p in sorted((R/'art/hero-finish'/folder).glob('*.glb')):refs.append({'path':os.path.relpath(p,O),'sha256':h(p),'bytes':p.stat().st_size})
(O/'raw-source-references.json').write_text(json.dumps({'scope':'Exact retained original source GLBs in this repository; avoids duplicate whole-asset copies.','files':refs},indent=2)+'\n')
with tarfile.open(O/'common-runtime-source.tar.gz','w:gz') as tar:
 for p in sorted((B/'baseline').rglob('*')):
  if p.is_file() and p.suffix in ['.gd','.tscn','.gdshader','.gdshaderinc','.godot'] and '.godot' not in p.relative_to(B/'baseline').parts:tar.add(p,arcname=str(p.relative_to(B/'baseline')))
cp(W/'REVIEW-draft.md',O/'REVIEW.md')
r={'schema':1,'passed':True,'disposition':json.loads((W/'disposition.json').read_text())['disposition'],'visual_accepted':False,'canonical_activated_by_W1':False,'branches':results,'actual_comparison_checks':comparison['checks'],'source_pair_delta':delta,'imported_hair_levels':proof['levels'],'imported_alpha_census':comparison['imported_hair_census'],'source_import_semantic_differences':proof['exact_semantic_difference_paths'],'independent_original_reviews':json.loads((W/'disposition.json').read_text())['independent_original_reviews'],'seed_archive':'../../G0/template-baseline-cold-600-r1/generated-shader-caches.tar.gz','seed_sha256':'c3729cc23281602c32b7665a8f34fa53178ce2fc11f899c8c181ddab1d9f638c','artifacts':[{'path':str(p.relative_to(O)),'sha256':h(p),'bytes':p.stat().st_size}for p in sorted(O.rglob('*'))if p.is_file()]}
(O/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'path':str(O),'receipt':h(O/'receipt.json'),'review':h(O/'REVIEW.md'),'artifacts':len(r['artifacts']),'bytes':sum(x['bytes']for x in r['artifacts'])}))
