from pathlib import Path
import json,gzip,hashlib,importlib.util,copy
from PIL import Image
W=Path('/workspace/scratch/yuga-next-W1-r1');PRIOR=Path('/workspace/scratch/yuga-frontage-production-r1/compare_frontage_r2.py');assert hashlib.sha256(PRIOR.read_bytes()).hexdigest()=='a2644672e1ef204ff78c3773ab3339a9f9832772974162b7904e8d5aa618ae4d'
spec=importlib.util.spec_from_file_location('ref',PRIOR);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
BASE='/workspace/scratch/yuga-next-W4-r1/thin-film-r1/world_water.gdshader';WATER='/workspace/scratch/yuga-next-root-r1/ground-relief-r1/render-water.gdshader';GROUND='/workspace/scratch/yuga-next-root-r1/ground-relief-r1/render-ground.gdshader';ORIGGROUND='res://scripts/world_ground.gdshader';THIN='3f5a6b89b6bdaaea547c51829da558d829445fb63a690d119e21720b8ce27a7e';WG='0e61b90721f2f3f7d32edec88976cb68463801830af2e8ae01b7a1fd2d4fa786';GG='45f98473453bb8f98330f93b1f879516c11e6e493329b1a94ff705ab436a272d';OG='7f687dbde3fe62bbcc38317d87229b4857c7340e1c7bfbb895c4c6911d765213';OW='add24973aab0d30ebeae2f2db7d096f74fd304bf22868afc4470e22506f86283';IDS=['lanka-sea','west-reed-water','east-reed-water']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(state,role,errors):
 s=copy.deepcopy(state);r,audit=ref.normalize_finish_owner({'shots':[s]},role,errors);s=r['shots'][0]
 wp=s.pop('water_shader_override');gp=s.pop('ground_shader_override');assert wp['role']==role and wp['candidate_path']==WATER and wp['candidate_sha256']==WG and wp['baseline_shader_path']==BASE and wp['baseline_shader_sha256']==THIN
 assert len(wp['rows'])==3 and {x['id'] for x in wp['rows']}==set(IDS)
 remap={};oldkeys=[]
 for ident in IDS+['FlatCityPaving']:
  water=ident in IDS;proof=next(x for x in wp['rows'] if x['id']==ident) if water else gp
  digest=(THIN if role=='baseline' else WG) if water else (OG if role=='baseline' else GG)
  path=(BASE if role=='baseline' else WATER) if water else (ORIGGROUND if role=='baseline' else GROUND)
  assert proof['id']==ident and proof['all_uniforms_copied_exact'] and proof['uniforms_before']==proof['uniforms_after_install'] and proof['active_code_sha256']==digest and proof['active_shader_path']==path
  assert proof['original_code_sha256']==(OW if water else OG) and proof['original_shader_path']==('res://scripts/world_water.gdshader' if water else ORIGGROUND)
  assert proof['applied']==(True if water else role=='candidate')
  if not water:assert proof['apron_untouched']
  meshes=[m for m in s['meshes'] if m['path']=='World/'+ident];assert len(meshes)==1;k=meshes[0]['material_override'];assert k not in oldkeys;oldkeys.append(k);m=copy.deepcopy(s['materials'][k]);assert m['class']=='ShaderMaterial';shader=m['properties']['shader'];assert shader['class']=='Shader' and shader['path']==path and hashlib.sha256(shader['code'].encode()).hexdigest()==digest
  if not water and role=='baseline':assert shader.pop('source_sha256')==OG
  assert set(shader)=={'class','path','code'};assert m['shader_uniforms']==proof['uniforms_at_snapshot' if water else 'uniforms_after_install'];shader['path']='declared exact '+('water' if water else 'ground')+' source';shader['code']='declared exact '+('water' if water else 'ground')+' source'
  nk=hashlib.sha256(json.dumps(m,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest();assert nk not in s['materials'];s['materials'][nk]=m;remap[k]=nk
 for k in oldkeys:del s['materials'][k]
 for m in s['meshes']:
  for k in ['material_override','material_overlay']:m[k]=remap.get(m[k],m[k])
  m['surfaces']=[remap.get(k,k) for k in m['surfaces']]
 assert len(s['water_projection'])==3
 for q in s['water_projection']:assert q['shader_path']==(BASE if role=='baseline' else WATER);q['shader_path']='declared exact water source'
 return s,audit

def compare_roots(a,b,day=False):
 reports=[json.loads((p/'capture.json').read_text()) for p in [a,b]];traces=[json.loads((p/('day-trace.json' if day else 'compact-trace.json')).read_text()) for p in [a,b]];count=1 if day else 32
 for p,r,t in zip([a,b],reports,traces):
  assert r['complete'] and r['source_unchanged'] and all(c['passed'] for c in r['checks']) and len(r['shots'])==count
  for im in r['shots']:assert sha(p/im['file'])==im['sha256'] and Image.open(p/im['file']).size==(960,540)
  for z in r['full_snapshot_refs']:
   raw=gzip.decompress((p/z['file']).read_bytes());assert sha(p/z['file'])==z['compressed_sha256'] and hashlib.sha256(raw).hexdigest()==z['decoded_sha256'] and len(raw)==z['decoded_bytes']
 diffs=ref.differences(*traces);full=[]
 for za,zb in zip(reports[0]['full_snapshot_refs'],reports[1]['full_snapshot_refs']):
  x=json.loads(gzip.decompress((a/za['file']).read_bytes()));y=json.loads(gzip.decompress((b/zb['file']).read_bytes()));errors=[]
  try:
   nx,ax=normalize(x,'baseline',errors);ny,ay=normalize(y,'candidate',errors);d=ref.differences(nx,ny);full.append({'boundary':za['file'],'passed':not errors and not d,'differences':d,'errors':errors,'owner_audit':[ax,ay]})
  except Exception as e:full.append({'boundary':za['file'],'passed':False,'exception':type(e).__name__+':'+str(e),'errors':errors})
 return {'passed':not diffs and all(x['passed'] for x in full),'compact_trace_differences':diffs,'full_boundaries':full,'all_png_dimensions_hashes_gzip_decoded_hashes_pass':True,'normalization':'Exactly four material shader code/source/path substitutions with every uniform/array and node property retained; reviewed four Rama owner metadata normalization only. Entire compact/startup trace exact without normalization.','sample_count':count}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--day',action='store_true');a=p.parse_args();stem='water-relief-day' if a.day else 'water-relief';r=compare_roots(W/(stem+'-baseline-actual-r1'),W/(stem+'-candidate-actual-r1'),a.day);o=W/(stem+'-controls-r1.json');assert not o.exists();o.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'trace_differences':len(r['compact_trace_differences']),'boundaries':[{k:x.get(k) for k in ['boundary','passed','exception']} for x in r['full_boundaries']]}));raise SystemExit(0 if r['passed'] else 1)
