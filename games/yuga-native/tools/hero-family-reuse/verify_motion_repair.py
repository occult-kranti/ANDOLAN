"""Compare real baseline/candidate skin and continuous-motion probe receipts."""
import argparse,hashlib,json
from pathlib import Path
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline-contact',type=Path,required=True);p.add_argument('--candidate-contact',type=Path,required=True);p.add_argument('--baseline-motion',type=Path,required=True);p.add_argument('--candidate-motion',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 bc=json.loads(a.baseline_contact.read_text());cc=json.loads(a.candidate_contact.read_text());bm=json.loads(a.baseline_motion.read_text());cm=json.loads(a.candidate_motion.read_text());checks=[]
 def check(name,passed,detail=None):checks.append({'name':name,'passed':bool(passed),'detail':detail})
 check('18 matched contact trials',len(bc['trials'])==len(cc['trials'])==18)
 check('same actual hero/library inputs',bc['hero_sha256']==cc['hero_sha256'] and bc['library_sha256']==cc['library_sha256'])
 check('frozen contact controllers',bc['motion_unchanged'] and cc['motion_unchanged'])
 cases=[]
 for old,new in zip(bc['trials'],cc['trials']):
  key=f"{new['mode']}@{new['hz']}Hz";mode=new['mode'];before=old['first_frame_string_vertex_step_m'];after=new['first_frame_string_vertex_step_m']
  check(key+' identity',(old['mode'],old['hz'])==(new['mode'],new['hz']))
  check(key+' finite/requests',all(new[k] for k in ['configured','setup_ok','requested','invalid_request_rejected','rejected_request_preserves_entry_cache','finite']))
  check(key+' actual mesh samples',new['actual_string_vertices']==old['actual_string_vertices'] and new['actual_string_vertices']>0 and new['actual_distal_draw_vertices']>0 and new['bone_parent']=='wrist.R')
  check(key+' held contact',new['maximum_held_socket_gap_m']<.0001 and new['maximum_held_finger_skin_gap_m']<.006)
  if mode in {'warm_aim','cancel_reaim'}:check(key+' fixes primed warm snap',before>.15 and after<.005 and after<before*.05,{'before_m':before,'after_m':after})
  elif mode=='respawn_reaim':check(key+' improves respawn reaim without zero claim',before>.15 and after<.03 and after<before*.2,{'before_m':before,'after_m':after})
  elif mode in {'cold','reset_cold'}:check(key+' cold trace unchanged',old['rows']==new['rows'])
  elif mode=='retrigger':check(key+' retrigger not worsened',after<=before+1e-5)
  cases.append({'mode':mode,'hz':new['hz'],'before_first_frame_actual_string_vertex_step_m':before,'after_first_frame_actual_string_vertex_step_m':after,'maximum_held_socket_gap_m':new['maximum_held_socket_gap_m'],'maximum_held_finger_skin_gap_m':new['maximum_held_finger_skin_gap_m']})
 check('nine matched continuous trials',len(bm['trials'])==len(cm['trials'])==9)
 for old,new in zip(bm['trials'],cm['trials']):
  key=f"{new['mode']}@{new['hz']}Hz";same=len(old['frames'])==len(new['frames']) and old['mode']==new['mode'] and old['hz']==new['hz']
  for x,y in zip(old['frames'],new['frames']):
   same=same and all(x[k]==y[k] for k in ['frame','stage','action','locomotion','nocked','release_count'])
  check(key+' continuous clocks/authority exact',same)
  check(key+' continuous finite/contact',new['finite'] and new['maximum_held_string_contact_m']<.0001)
 check('continuous sources unchanged',bm['sources_unchanged'] and cm['sources_unchanged'])
 report={'schema_version':1,'scope':'Grounded warm-primary-draw string entry repair on accepted Rama rig. Contact and authority checks only; respawn/reaim residual and other action motion remain distinct.','passed':all(c['passed'] for c in checks),'checks':checks,'contact_cases':cases,'inputs':{name:{'path':str(path),'sha256':sha(path)} for name,path in [('baseline_contact',a.baseline_contact),('candidate_contact',a.candidate_contact),('baseline_motion',a.baseline_motion),('candidate_motion',a.candidate_motion)]},'script_sha256':sha(__file__),'runtime_promoted':False}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('WARM_ENTRY_REPAIR_COMPARISON',len(checks),'PASS' if report['passed'] else 'FAIL');raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
