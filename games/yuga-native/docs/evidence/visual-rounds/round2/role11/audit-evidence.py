import datetime,hashlib,json,math,pathlib,shutil
base=pathlib.Path('/workspace/ANDOLAN/games/yuga-native');out=base/'docs/evidence/visual-rounds/round2/role11';scratch=pathlib.Path('/workspace/scratch/visual-round2/role-11')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((base/p).read_text())
f=read('docs/evidence/visual-rounds/round2/role04/face-action-fixtures.json');r=read('docs/evidence/visual-campaign/capture-action-r1/rama-gameplay-review.json');checks=[]
def check(name,passed,details=None):checks.append({'check':name,'passed':bool(passed),'details':details})
for pin in f['source_pins']:check('fixture_source_pin:'+pin['path'],sha(base/pin['path'])==pin['sha256'],{'current_sha256':sha(base/pin['path']),'fixture_sha256':pin['sha256'],'matches_accepted_capture':pin['same_as_accepted_capture']})
check('accepted_report_complete_unchanged',r['complete'] and r['source_unchanged'])
rows=[]
for item in f['fixtures']:
 aid=item['ability_id'];control=item['accepted_control'];take=next(t for t in r['takes'] if t['ability_id']==aid and t['cast']['generation']==control['generation']);events=take['events'];timing=item['timing']
 check(aid+':report_sha256',sha(base/control['report'])==control['report_sha256'])
 for e in control['event_excerpt']:
  match=[x for x in events if all(x.get(k)==e.get(k) for k in ['generation','cast_id','event_seq'])]
  check(aid+':event_excerpt:'+str(e['event_seq']),len(match)==1 and all(match[0].get(k)==v for k,v in e.items()))
 check(aid+':unique_release',len([e for e in events if e['kind']=='release'])==1)
 for kind,field in [('release','authority_release_age_s'),('recovery','authority_recovery_age_s'),('end','authority_end_age_s')]:
  got=[e['age_s'] for e in events if e['kind']==kind];check(aid+':'+field,len(got)==1 and abs(got[0]-timing[field])<1e-8,got)
 damage=[]
 for event in events:
  for receipt in event['receipts']:
   if receipt['kind']=='damage':
    delta=receipt['health_before']-receipt['health_after']+receipt['shield_before']-receipt['shield_after'];damage.append({'event_seq':event['event_seq'],'age_s':event['age_s'],'projectile_index':event.get('projectile_index'),'unit_id':receipt['unit_id'],'damage':receipt['damage_applied']})
    check(aid+':damage_balance:'+str(event['event_seq']),event['kind']=='impact' and event['reason']=='unit' and receipt['damage_applied']>0 and abs(delta-receipt['damage_applied'])<1e-7)
 for still in control['stills']:
  p=base/'docs/evidence/visual-campaign/capture-action-r1'/still['image']['file'];check(aid+':original_hash:'+p.name,sha(p)==still['image']['sha256'])
 rows.append({'ability':aid,'generation':control['generation'],'cast_id':control['cast_id'],'timing':timing,'damage_receipts':damage,'receiver_requirement':item['receiver_requirement']})
sequence=f['compact_continuous_take'];clock=181/60+6/30
check('sequence_full_close_nominal_frame5',3.205<=clock<=3.230,{'computed_face_clock':clock,'scope':'Arithmetic, not execution'})
check('sequence_cancel_before_piercing_release',(24-15)/30<.65,{'cancel_local_age_s':.3,'declared_release_s':.65})
check('sequence_last_frame_beyond_cancel_fade',36/30-24/30>.16,{'time_after_cancel_s':.4,'fade_s':.16})
run=read('docs/evidence/visual-rounds/round2/role11/run.json');check('runtime_pins_unchanged_across_focused_run',run['source_unchanged'])
payload={'schema':1,'task_id':'R2-11','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':f['source_commit'],'all_passed':all(c['passed'] for c in checks),'check_count':len(checks),'checks':checks,'abilities':rows,'fixture_sha256':sha(base/'docs/evidence/visual-rounds/round2/role04/face-action-fixtures.json'),'review_scope':'Independent comparison of fixtures to actual retained event receipts and current sources. Neither retained receipts nor arithmetic accept a new candidate image.'}
(out/'source-and-event-review.json').write_text(json.dumps(payload,indent=2)+'\n')
notes={
'still-kodanda-windup.png':'Rear camera: head and back silhouette clear; face and front neck hidden by view/hair. Bow/cast is subtle; visible drawing HUD supports state, not facial read.',
'still-piercing_dawn-release.png':'Gold curved strokes flank shoulder/head silhouette and remain below/around head; central target remains visible. Front face unavailable.',
'still-measured_step-release.png':'Pale blue trails mostly below torso and behind legs; head silhouette unobscured. Frozen image does not prove displacement timing.',
'still-guardian_circle-release.png':'Large ground boundary and turquoise low arcs visible around avatar; near ally occludes space ahead. Head silhouette clear, front face unavailable.',
'still-dawn_volley-release.png':'Gold loop surrounds top/side of head silhouette, blue ribbon crosses upper back, three targets visible. Candidate frontal occlusion cannot be inferred.'}
images=[]
for name,note in notes.items():
 p=base/'docs/evidence/visual-campaign/capture-action-r1'/name;rec=next(x for x in r['stills'] if x['image']['file']==name)
 images.append({'path':str(p.relative_to(base)),'sha256':sha(p),'receipt_hash_matches':sha(p)==rec['image']['sha256'],'inspected_with':'view_image original PNG','observation':note,'scope':'retained R1 ordinary gameplay control'})
cap=read('docs/evidence/visual-rounds/round2/role06/baseline/courtyard/capture.json')
for phase in ['day','night']:
 p=base/('docs/evidence/visual-rounds/round2/role06/baseline/courtyard/courtyard-three-quarter-left-'+phase+'.png')
 images.append({'path':str(p.relative_to(base)),'sha256':sha(p),'inspected_with':'view_image original PNG','observation':('Eyes, nose, mouth and exposed neck are visible; dark nose/cheek shading, dotted edge artifacts at temple/neck.' if phase=='day' else 'Eyes and face/neck contour remain visible but facial planes are darker and flatter than day; no action or effect present.'),'scope':'R2 baseline neutral facial closeup; no candidate action/cancel acceptance'})
(out/'reviewed-images.json').write_text(json.dumps({'schema':1,'task_id':'R2-11','images':images,'new_candidate_action_images_reviewed':0,'new_continuous_frames_reviewed':0,'new_image_gate':'PENDING_CAPTURE'},indent=2)+'\n')
for name in ['source-and-event-review.json','reviewed-images.json']:shutil.copy2(out/name,scratch/name)
shutil.copy2(__file__,out/'audit-evidence.py');print(json.dumps({'checks':len(checks),'all_passed':payload['all_passed'],'image_count':len(images),'failed':[c for c in checks if not c['passed']]},indent=2))
