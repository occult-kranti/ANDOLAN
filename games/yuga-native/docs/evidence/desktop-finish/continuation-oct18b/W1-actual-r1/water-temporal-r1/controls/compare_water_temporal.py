from pathlib import Path
import json,gzip,hashlib,importlib.util,copy
from PIL import Image
W=Path('/workspace/scratch/yuga-next-W1-r1');H=W/'harness';A=W/'water-temporal-baseline-actual-r1';B=W/'water-temporal-candidate-actual-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=(H/'compare_water_controls.py').read_text();old="assert s['review_fixture']['animation'] in ['only water animation_speed frozen0; shader source unchanged','only water animation_speed frozen0; exact isolated external shader override declared separately']";assert source.count(old)==1
source=source.replace(old,"assert s['review_fixture']['animation']=='original material animation restored before frame24; real TIME, no explicit shader clock override'")
ns={'__name__':'strict_temporal_full_controls'};exec(compile(source,str(H/'compare_water_controls.py'),'exec'),ns)
ra=json.loads((A/'capture.json').read_text());rb=json.loads((B/'capture.json').read_text());ta=json.loads((A/'compact-trace.json').read_text());tb=json.loads((B/'compact-trace.json').read_text());assert ra['complete'] and rb['complete']
for root,r,t in [(A,ra,ta),(B,rb,tb)]:
 assert len(t['frames'])==32 and len(r['shots'])==32 and len(r['full_snapshot_refs'])==2
 assert sha(root/'compact-trace.json')==r['trace_ref']['sha256']
 assert t['time_origin_clock']['draw']==0 and t['before_first_clock']['draw']==24
 for i,s in enumerate(r['shots']):
  assert s['index']==i and s['global_draw']==24+i and sha(root/s['file'])==s['sha256'] and Image.open(root/s['file']).size==(960,540)
  c=t['frames'][i]['clock'];assert c['draw']==24+i and c['process']==24+i and c['physics']==49+2*i and c['time_scale']==1 and abs(c['scaled_node_process_step']-1/30)<7.5e-9 and c['window_can_draw'] and c['render_loop_enabled'] and not c['low_processor_usage_mode']
 assert len(t['draw_history'])==56
 for ref in r['full_snapshot_refs']:
  p=root/ref['file'];raw=gzip.decompress(p.read_bytes());assert sha(p)==ref['compressed_sha256'] and len(p.read_bytes())==ref['compressed_bytes'] and hashlib.sha256(raw).hexdigest()==ref['decoded_sha256'] and len(raw)==ref['decoded_bytes']
full=[]
for name in ['full-first.json.gz','full-last.json.gz']:
 x=json.loads(gzip.decompress((A/name).read_bytes()));y=json.loads(gzip.decompress((B/name).read_bytes()));full.append({'boundary':name,**ns['compare']({'shots':[x]},{'shots':[y]})})
diffs=ns['ref'].differences(ta,tb)
r={'passed':not diffs and all(x['passed'] for x in full),'full_boundaries':full,'compact_trace_differences':diffs,'all_startup_and_sample_history_exact':not diffs,'draw_history_entries':len(ta['draw_history']),'samples':32,'global_draws':[24,55],'all_original_hashes_dimensions_and_gzip_decoded_hashes_pass':True,'normalization':'Full controls exact reviewed four Rama owner fields +3 pinned shader-code/source/path substitutions; compact traces including164 final poses and entire56 startup/sample draw histories have NO normalization.','shader_TIME_scope':'Equal fresh draw0 and exact entire accumulated draw histories,step/time_scale/gating/engine/PCK/args/renderthreadmode required; not walltime or counter/30 inference.','source_static_comparator_sha256':sha(H/'compare_water_controls.py'),'helper_sha256':sha(H/'capture_water_temporal.gd')}
p=W/'water-temporal-controls-r1.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'compact_differences':len(diffs),'full':[{k:x.get(k) for k in ['boundary','passed','validation_exception']} for x in full]}));raise SystemExit(0 if r['passed'] else 1)
