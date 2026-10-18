"""Strict full-world controls, admitting only3 pinned shader-code/path substitutions."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json
from PIL import Image
PRIOR=Path('/workspace/scratch/yuga-frontage-production-r1/compare_frontage_r2.py')
assert hashlib.sha256(PRIOR.read_bytes()).hexdigest()=='a2644672e1ef204ff78c3773ab3339a9f9832772974162b7904e8d5aa618ae4d'
spec=importlib.util.spec_from_file_location('reviewed_controls',PRIOR);ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
IDS=['lanka-sea','west-reed-water','east-reed-water'];ORIGINAL='add24973aab0d30ebeae2f2db7d096f74fd304bf22868afc4470e22506f86283';CANDIDATE='3f5a6b89b6bdaaea547c51829da558d829445fb63a690d119e21720b8ce27a7e';CANDIDATE_PATH='/workspace/scratch/yuga-next-W4-r1/thin-film-r1/world_water.gdshader';ORIGINAL_PATH='res://scripts/world_water.gdshader'
def normalized(report,role,errors,legacy=False):
 r,audit=ref.normalize_finish_owner(report,role,errors);expected=CANDIDATE if role=='candidate' else ORIGINAL;path=CANDIDATE_PATH if role=='candidate' else ORIGINAL_PATH
 for s in r['shots']:
  if s.get('reused_original'):
   expected_path=Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W1-actual-r1/water-baseline-r1/raw/00-night-swamp.png')
   expected_sha='f169f43710434b3dc871ce792182e424578ceb90226d106b5e165962754b9bb7'
   assert role=='baseline' and s['id']=='00-night-swamp' and not legacy
   assert s['reused_original']=={'path':str(expected_path),'sha256':expected_sha,'strict_control_comparison_required':True}
   assert hashlib.sha256(expected_path.read_bytes()).hexdigest()==expected_sha and Image.open(expected_path).size==(960,540)
   helper=Path('/workspace/scratch/yuga-next-W1-r1/harness/capture_water_pair.gd');assert hashlib.sha256(helper.read_bytes()).hexdigest()=='53dc475383089529c73a3766268acc28b3a58fe8a5e2cb5045e09ad41d03797c'
   assert s['framebuffer_size']==[720,405] and s['physical_size']==[960,540] and s['base_canvas']==[1280,720] and s['content_scale_factor']==1.0 and s['drawn_frame']==24 and s['process_frame']==24 and s['physics_frame']==49
   for name in ['01-coast-day','02-day-swamp']:
    sibling=Path('/workspace/scratch/yuga-next-W1-r1/water-pair-baseline-actual-r1')/(name+'.png');side=json.loads(sibling.with_suffix('.json').read_text());assert Image.open(sibling).size==(960,540) and hashlib.sha256(sibling.read_bytes()).hexdigest()==side['sha256'] and side['framebuffer_size']==[960,540]
   s['framebuffer_size']=[960,540] # DERIVED comparison only. Raw mislabeled texture descriptor remains720x405.
  proof=s.pop('water_shader_override',None)
  if not legacy:
   assert proof and proof['role']==role and proof['candidate_sha256']==CANDIDATE and proof['candidate_path']==CANDIDATE_PATH
   assert len(proof['rows'])==3 and {x['id'] for x in proof['rows']}==set(IDS)
   for row in proof['rows']:
    assert row['applied']==(role=='candidate') and row['original_code_sha256']==ORIGINAL and row['original_shader_path']==ORIGINAL_PATH
    assert row['active_code_sha256']==expected and row['active_shader_path']==path and row['all_uniforms_copied_exact'] and row['uniforms_before']==row['uniforms_after_install']
  remap={};water_keys=[]
  for ident in IDS:
   meshes=[m for m in s['meshes'] if m['path']=='World/'+ident];assert len(meshes)==1
   mesh=meshes[0];key=mesh['material_override'];water_keys.append(key);material=copy.deepcopy(s['materials'][key]);assert material['class']=='ShaderMaterial'
   shader=material['properties']['shader'];assert set(shader)==({'class','path','code'} if role=='candidate' else {'class','path','code','source_sha256'}) and shader['class']=='Shader'
   if role!='candidate':assert shader.pop('source_sha256')==ORIGINAL
   assert shader['path']==path and hashlib.sha256(shader['code'].encode()).hexdigest()==expected
   if proof:
    row=next(x for x in proof['rows'] if x['id']==ident)
    uniforms=material['shader_uniforms']
    assert uniforms==row['uniforms_at_snapshot']
   shader['path']='exact declared water shader path';shader['code']='exact declared original/thin-film code'
   newkey=hashlib.sha256(json.dumps(material,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
   assert newkey not in s['materials'];remap[key]=newkey;s['materials'][newkey]=material
  assert len(set(water_keys))==3
  for key in water_keys:del s['materials'][key]
  for mesh in s['meshes']:
   for key in ['material_override','material_overlay']:mesh[key]=remap.get(mesh[key],mesh[key])
   mesh['surfaces']=[remap.get(k,k) for k in mesh['surfaces']]
  assert len(s['water_projection'])==3 and {x['id'] for x in s['water_projection']}==set(IDS)
  for row in s['water_projection']:
   assert row['shader_path']==path;row['shader_path']='exact declared water shader path'
  # This is fixture provenance text, not a material/render value.
  assert s['review_fixture']['animation'] in ['only water animation_speed frozen0; shader source unchanged','only water animation_speed frozen0; exact isolated external shader override declared separately']
  s['review_fixture']['animation']='declared water animation frozen0'
  for field in ['file','sha256','reused_original']:s.pop(field,None)
 return r,audit

def compare(a,b,role_b='candidate',legacy_a=False):
 errors=[]
 try:
  x,ax=normalized(a,'baseline',errors,legacy_a);y,ay=normalized(b,role_b,errors)
  diffs=ref.differences(x['shots'],y['shots']);passed=not errors and not diffs
  return {'passed':passed,'differences':diffs,'normalization_errors':errors,'reviewed_owner_normalization_sha256':hashlib.sha256(PRIOR.read_bytes()).hexdigest(),'owner_audit':{'a':ax,'b':ay},'scope':'All snapshot fields strict after validating exactly3 shader code/path substitutions and4 previously reviewed owner-only metadata normalizations. Material uniforms, light/camera/164finalposes/authority/collision/mesh arrays/clocks/globalframecounters remain exact. PNG references and declared fixture provenance handled separately.'}
 except Exception as e:return {'passed':False,'validation_exception':type(e).__name__+': '+str(e),'normalization_errors':errors}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('a',type=Path);p.add_argument('b',type=Path);p.add_argument('--report',type=Path,required=True);p.add_argument('--role-b',default='candidate',choices=['baseline','candidate']);p.add_argument('--legacy-a',action='store_true');a=p.parse_args();assert not a.report.exists();x=json.loads(a.a.read_text());y=json.loads(a.b.read_text());r=compare(x,y,a.role_b,a.legacy_a);a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'differences':len(r.get('differences',[])),'exception':r.get('validation_exception')}));raise SystemExit(0 if r['passed'] else 1)
