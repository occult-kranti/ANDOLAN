"""Exact accepted-candidate vs default-production controls; no geometry exception."""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
W=Path(__file__).parent
UTIL=W/'compare_frontage_r2.py'
assert hashlib.sha256(UTIL.read_bytes()).hexdigest()=='a2644672e1ef204ff78c3773ab3339a9f9832772974162b7904e8d5aa618ae4d'
spec=importlib.util.spec_from_file_location('prior',UTIL);u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
PIN={'scripts/confluence_world.gd':'1301701f7f8b6a711de7a36a6d283d88f1240708a7186053fa51bfc572ca8c76','scripts/world_lane_frontage.gd':'dcd0c73d8a12fc32e2fc32fa69ccc3466c3835ab0f4c15b8f18b72e8990dda72','scripts/world_lane_frontage.gd.uid':'7506c2840a369ff018ccd966ad054f9eb01ec9b365236548e1a655949bceb8de','assets/world/block2-frontage.json':'67950a68d7b6384b8b114987a27efff1f113d44f8fb1b7df8632f3e9217406a2'}
HELPER='tools/graphics-six/capture_scene_anchors.gd'
OLD_HELPER='a052a33ed086ec713546021b2a9a3b77ee75ee7fa1e560685b465ec1b92cd43d';NEW_HELPER='f35ef9ef674a0f9cce725245898da07ec14fee462361d1459eff7bf5ee7f742f'
GLOBAL={'process_frame','physics_frame','drawn_frame','file','sha256','pose_signal_counters'}
def compare(a,b,allow_preflight=False):
 errors=[];check=lambda ok,s:u.require(ok,s,errors)
 a,oa=u.normalize_finish_owner(a,'accepted candidate',errors);b,ob=u.normalize_finish_owner(b,'production',errors)
 for label,r in [('accepted',a),('production',b)]:
  check(r['complete'] and not r.get('failure') and r['case']=='lane-frontage-review',label+' complete declared case')
  check(r['source_unchanged'] and r['source_sha256']==r['source_after_sha256'],label+' source unchanged')
  check(r['branch']=='candidate' and len(r['shots'])==3,label+' candidate/3shots')
  check(u.finite(r),label+' finite report')
  check(allow_preflight or (not r['preflight'] and r['renderer']=='forward_plus'),label+' actualForward+ unless explicitpreflight')
 check(a['preflight']==b['preflight'],'same declared mode')
 check(a['renderer']==b['renderer'] and a['adapter']==b['adapter'],'same renderer/adapter')
 check(a['selection_sha256']==b['selection_sha256'],'same selection bytes')
 sa,sb=a['source_sha256'],b['source_sha256'];added=set(PIN)-{'scripts/confluence_world.gd'}
 check(set(sb)==set(sa)|added and not(set(sa)&added),'only three production source additions')
 for n,p in PIN.items():check(sb.get(n)==p,'production exact '+n)
 check(sa.get('scripts/confluence_world.gd')=='42e617a379f815e51a32b9bbd9cca86c6ba3ac6a7c809e2d2d8c6c89619fc0cb','accepted caller exact')
 for r,h in [(a,OLD_HELPER),(b,NEW_HELPER)]:check(r['source_sha256'].get(HELPER)==r['source_sha256'].get('res://'+HELPER)==h,'exact helper aliases')
 allowed={'scripts/confluence_world.gd',HELPER,'res://'+HELPER}|u.MARKERS
 source_diffs=[n for n in set(sa)&set(sb) if sa[n]!=sb[n]];check(set(source_diffs)<=allowed,'no undeclared source change')
 p=b.get('production_admission',{})
 expected={'module_path':'res://scripts/world_lane_frontage.gd','module_sha256':PIN['scripts/world_lane_frontage.gd'],'caller_sha256':PIN['scripts/confluence_world.gd'],'data_path':'res://assets/world/block2-frontage.json','data_sha256':PIN['assets/world/block2-frontage.json'],'root_present_before_observer':True,'published_shape_identity':True,'same_frame_as_observer_connection':True}
 check(all(type(p.get(k)) is type(v) and p.get(k)==v for k,v in expected.items()),'actual default production admission pins/presence/shape/sameframe')
 check(type(p.get('admission_process_frame')) is int and p['admission_process_frame']>0,'observed admission counter')
 check(str(p.get('root_path','')).endswith('/World/ReviewBlock2Frontage'),'actual production root path')
 rows=[]
 for x,y,ident in zip(a['shots'],b['shots'],u.IDS):
  check(x['id']==y['id']==ident,'same shot ID '+ident)
  for shot,report in [(x,a),(y,b)]:
   c=shot['pose_correlation'];check(c['preflight_no_draw']==report['preflight'] and c['process_age']==c['physics_age']==0 and c['post_draw_age']==(0 if report['preflight'] else 1),'sameframe finalpose '+ident)
   check(len(shot['hero_skeleton']['bone_global_poses'])==164,'full164 finalposes '+ident)
  cx=copy.deepcopy(x);cy=copy.deepcopy(y)
  for q in (cx,cy):
   for k in GLOBAL:q.pop(k,None)
   for k in ('meshes','lights','collision_objects'):q[k]=u.path_index(q[k],errors,k)
  diffs=u.differences(cx,cy);rows.append({'id':ident,'passed':not diffs,'differences':diffs,'global_counters':{k:[x.get(k),y.get(k)] for k in sorted(u.GLOBAL_COUNTERS)}})
 check(not u.differences(a['route_checks'],b['route_checks']),'exact overview return controls')
 return {'passed':not errors and all(r['passed'] for r in rows),'errors':errors,'shots':rows,'source_differences':source_diffs,'production_admission':p,'finish_owner_metadata_normalization':{'accepted':oa,'production':ob},'scope':'Production startup observation only; no review configure call. No geometry/material/pose/camera/clock/collision exception; only exact source transition, process-local finish owner metadata and absolute counters are declared.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--accepted',type=Path,required=True);ap.add_argument('--production',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--allow-preflight',action='store_true');a=ap.parse_args();assert not a.output.exists()
 r=compare(json.loads(a.accepted.read_text()),json.loads(a.production.read_text()),a.allow_preflight);r['input_sha256']={n:hashlib.sha256(getattr(a,n).read_bytes()).hexdigest() for n in ('accepted','production')};a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'errors':r['errors'],'shots':[{'id':s['id'],'passed':s['passed'],'difference_count':len(s['differences'])} for s in r['shots']]}));raise SystemExit(0 if r['passed'] else 1)
if __name__=='__main__':main()
