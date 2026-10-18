#!/usr/bin/env python3
"""Archive this completed, immutable roof pair. Does not launch engines or edit sources."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,tarfile
OUT=Path(__file__).resolve().parent
ROOT=next(p for p in OUT.parents if (p/'AGENTS.md').is_file())
BASE=Path('/tmp/yuga-roof-loggia-render-r4')
ART=ROOT/'games/yuga-native/art/world-finish/roof-loggia-render-r2'
RUNNER=ROOT/'games/yuga-native/docs/evidence/desktop-finish/G0/workspace-recovery-r1/tools'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
spec=importlib.util.spec_from_file_location('snapshot',RUNNER/'snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[];summary={};manifests={};runs={}
for b in ('baseline','candidate'):
 project=BASE/(b+'-project');v=m.verify(project);assert v['passed'];manifests[b]=v
 src=BASE/('render-'+b+'-r1');logs=Path(str(src)+'-logs');r=json.loads((logs/'run.json').read_text());d=json.loads((src/'capture.json').read_text());runs[b]=r
 assert r['complete'] and r['engine_exit']==0 and d['complete'] and d['source_unchanged'] and len(d['shots'])==2
 assert len(d['checks'])==8 and all(c['passed'] is True for c in d['checks'])
 log=(logs/'godot.log').read_text();warnings=[l for l in log.splitlines() if 'WARNING:' in l]
 assert len(warnings)==120 and all('Image format RGB8 not supported by hardware, converting to RGBA8.' in l for l in warnings)
 assert 'ERROR:' not in log and 'leaked' not in log.lower()
 for shot in d['shots']:assert sha(src/(shot['id']+'.png'))==shot['sha256']
 assert d['audio_cleanup']['observed_mixer_ticks']==2 and d['audio_cleanup']['wait_usec']<=250000
 for p in src.iterdir():
  if p.is_file():copy(p,OUT/b/p.name)
 for n in ('run.json','godot.log'):copy(logs/n,OUT/b/n)
 copy(project/'.graphics-six-snapshot.json',OUT/b/'source-snapshot.json')
 copy(project/'scripts/confluence_world.gd',OUT/b/'confluence_world.gd')
 checks.append({'branch':b,'passed':True,'snapshot_verified':True,'source_files':len(v['files']),'capture_checks':8,'originals':2,'source_unchanged':True,'exit':0,'warnings':len(warnings),'errors':0,'elapsed_seconds':r['engine_elapsed_s'],'audio_mixer_ticks':2})
 summary[b]={'snapshot_sha256':r['snapshot_sha256'],'capture_sha256':sha(src/'capture.json'),'run_sha256':sha(logs/'run.json'),'source_sha256':d['source_sha256']}
assert runs['baseline']['shader_cache_seed']==runs['candidate']['shader_cache_seed']
assert runs['baseline']['godot_shader_cache_seed']==runs['candidate']['godot_shader_cache_seed']
diff=[p for p in sorted(set(manifests['baseline']['files'])|set(manifests['candidate']['files'])) if manifests['baseline']['files'].get(p)!=manifests['candidate']['files'].get(p)]
assert diff==['scripts/confluence_world.gd'],diff
c=json.loads((BASE/'render-comparison-r1.json').read_text());assert c['passed'] and len(c['shots'])==2 and all(s['passed'] for s in c['shots'])
copy(BASE/'render-comparison-r1.json',OUT/'render-comparison.json')
for n in ('capture_roof.gd','compare_controls.py','render-commands.UNRUN.json','receipt.json','candidate-source.json','baseline-source.json','staging.json','README.md'):copy(ART/n,OUT/'preparation'/n)
for n in ('run_focus.py','snapshot.py'):copy(RUNNER/n,OUT/'tools'/n)
project=BASE/'baseline-project'
paths=[p for p in project.rglob('*') if p.is_file() and (p.relative_to(project).parts[0] in ('scripts','scenes','shaders') or str(p.relative_to(project)) in ('project.godot','assets/environment-finish/masonry.gdshader','tools/graphics-six/capture_compact_screens.gd','tools/graphics-six/capture_scene_anchors.gd'))]
with tarfile.open(OUT/'common-runtime-source.tar.gz','w:gz') as tar:
 for p in sorted(paths):tar.add(p,arcname=str(p.relative_to(project)),recursive=False)
(OUT/'execution-audit.json').write_text(json.dumps({'passed':True,'branches':checks,'inputs':summary,'branch_source_differences':diff,'strict_control_comparison':True,'same_213_copied_seed_inputs':True,'scope':'Four source-bound originals; full sampled164-bone/unit/camera/light/UI/clock controls equal, global load frame counters disclosed in comparison. One declared roof/collider insertion. Engine/source/cache unchanged; no production asset promotion.','runtime_source_tar_files':len(paths),'source_scope':'Frozen parent36351 plus promoted paving2e84; older frozen hero/motion/art context. Final current integrated assets are a separate gate.'},indent=2)+'\n')
print(json.dumps({'passed':True,'branches':checks,'source_delta':diff,'common_runtime_files':len(paths)},indent=2))
