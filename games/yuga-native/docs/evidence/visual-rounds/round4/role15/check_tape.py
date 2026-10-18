"""Independent whole-tape evidence checks and descriptive contact measurements."""
from pathlib import Path
import hashlib,json,math
HERE=Path(__file__).parent
SOURCE=HERE.parent/'role06'
ORIGINALS=SOURCE/'originals'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((ORIGINALS/'capture.json').read_text())
a=json.loads((SOURCE/'motion-check.json').read_text())
shots=d['shots'];rows=a['contact_rows'];names=d['bone_names'];checks=[]
seen=[0,15,16,29,30,31,32,34,35,36,44,45,47,48,59,62,64,75,76,79,81,90,102,113,114,115,117,149,150,151,158,159,160,163]
def ck(name,ok):checks.append({'name':name,'passed':bool(ok)})
def dist(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def point(t,p):return [t[3][i]+sum(t[j][i]*p[j] for j in range(3)) for i in range(3)]
ck('210 consecutive original frames with matching content digests',len(shots)==210 and [s['tape_index'] for s in shots]==list(range(210)) and all(sha(ORIGINALS/s['file'])==s['sha256'] for s in shots))
ck('all raw and imported source pins remain exact across take',d['source_unchanged'] and d['source_sha256']==d['source_after_sha256'])
promotion=json.loads((HERE.parent.parent/'round3/integration/promotion.json').read_text())
raw=['assets/heroes/rama-hero.glb','assets/heroes/rama-hero-mid.glb','assets/heroes/rama-hero-far.glb','assets/materials/rama-finish/woven-roughness.png']
ck('current accepted controller and all four R7 asset sources',d['source_sha256']['res://scripts/rama_motion.gd']=='4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1' and all(d['source_sha256']['res://'+name]==promotion['source_files'][name]['sha256'] for name in raw))
ck('all12 accepted R7 imported resource descriptor and MD5 pins',len(promotion['cache_files'])==12 and all(d['source_sha256']['res://'+name]==record['sha256'] for name,record in promotion['cache_files'].items()))
ck('all210 callback body and observed draw physics are coherent',len(rows)==210 and all(r['frame']==i and r['callback_physics_frame']==r['draw_physics_frame']==shots[i]['final_modifier_body']['physics_frame']==shots[i]['physics_frame'] for i,r in enumerate(rows)))
ck('all210 contact summaries match captured sole records',all(r['soles']==s['sole_contacts']['sides'] for r,s in zip(rows,shots)))
ck('two physics ticks per captured frame with one recorded LOD',all(shots[i]['physics_frame']-shots[i-1]['physics_frame']==2 for i in range(1,210)) and set(r['lod'] for r in rows)=={1})
ck('actual imported fullbody projection is contained in every frame',all(s['bounds']['passed'] and s['bounds']['behind']==0 and s['bounds']['vertices']>0 for s in shots))
events=d['ability_events'];cancel=next(c for c in d['sequence_controls'] if c['kind']=='cancel_windup')
ck('one accepted cast and same-identity public cancel without release or impact',len(events)==2 and [e['kind'] for e in events]==['begin','cancel'] and events[0]['cast_id']==events[1]['cast_id']==cancel['cast']['cast_id'] and cancel['cast']['accepted'] and cancel['returned'] and 0<events[1]['age_s']<cancel['cast']['windup_s'])
ck('cancel immediately removes commitment nock and warning then fades to none',not cancel['immediate_after']['rama_committed'] and not cancel['immediate_after']['nocked'] and not cancel['immediate_after']['nocked_node_visible'] and cancel['immediate_after']['warning_nodes']==[] and cancel['immediate_after']['effects']['active']==0 and shots[159]['action']['stage']=='fade' and all(s['action']['stage']=='none' and not s['action']['nocked'] and s['action']['effects']['active']==0 for s in shots[163:]))
ck('one genuine jump and no in-take reset or teleport',shots[-1]['final_modifier_body']['jump_count']==1 and all(c['kind'] not in ['reset','teleport'] for c in d['sequence_controls']) and any(not r['on_floor'] for r in rows) and rows[-1]['on_floor'])
ck('all164 bone transforms exist and are finite for every frame',len(names)==164 and all(len(s['rendered_pose_globals'])==164 and all(math.isfinite(v) for t in s['rendered_pose_globals'] for xyz in t for v in xyz) for s in shots))
grounded=[r for r in rows if r['on_floor']]
minima=[];penetrations=[];locked=[];near_floor=[];drifts=[];endpoint_errors=[];world_steps=[];relative_steps=[]
for i,s in enumerate(shots):
    b=s['final_modifier_body'];t=b['rig_transform'];root=b['player_transform'][3]
    for side,index in [('L',names.index('foot.L')),('R',names.index('foot.R'))]:
        contact=rows[i]['soles'][side];value=contact['minimum_signed_m']
        minima.append({'m':value,'frame':i,'side':side,'locked':contact['locked'],'vertex':contact['minimum_vertex']})
        if rows[i]['on_floor']:
            if value < -.005:penetrations.append(minima[-1])
            if abs(value)<=.005:near_floor.append(minima[-1])
            if contact['locked']:locked.append(minima[-1])
        if contact['locked']:
            target=b['foot_targets_rig'][side] # Stored in WORLD coordinates by rama_motion._apply_contact.
            endpoint_errors.append({'m':dist(point(t,s['rendered_pose_globals'][index][3]),target),'frame':i,'side':side})
            if i and rows[i-1]['soles'][side]['locked']:
                drifts.append({'m':dist(target,shots[i-1]['final_modifier_body']['foot_targets_rig'][side]),'frame':i,'side':side})
    if i:
        previous=shots[i-1];pb=previous['final_modifier_body'];pt=pb['rig_transform'];pr=pb['player_transform'][3]
        for bone,(pose,ppose) in enumerate(zip(s['rendered_pose_globals'],previous['rendered_pose_globals'])):
            now=point(t,pose[3]);old=point(pt,ppose[3]);record={'frame':i,'bone':names[bone]}
            world_steps.append({'m':dist(now,old),**record})
            relative_steps.append({'m':dist([now[j]-root[j] for j in range(3)],[old[j]-pr[j] for j in range(3)]),**record})
both_clear=[r['frame'] for r in grounded if min(v['minimum_signed_m'] for v in r['soles'].values())>.005]
stationary_clear=[r['frame'] for r in grounded if math.sqrt(sum(v*v for v in r['velocity']))<1e-5 and min(v['minimum_signed_m'] for v in r['soles'].values())>.005]
partitions={label:max((v for v in relative_steps if low<=v['frame']<=high),key=lambda v:v['m']) for label,low,high in [('movement_start_stop_reverse',1,89),('jump_land',90,149),('cast_entry',150,150),('windup',151,158),('cancel_fade',159,163)]}
result={'task':'R4-15','evidence_checks_passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,
 'sources':{'capture_sha256':sha(ORIGINALS/'capture.json'),'motion_check_sha256':sha(SOURCE/'motion-check.json'),'freeze_sha256':sha(SOURCE/'motion-freeze.json'),'motion_sha256':d['source_sha256']['res://scripts/rama_motion.gd'],'player_sha256':d['source_sha256']['res://scripts/player.gd'],'world_sha256':d['source_sha256']['res://scripts/confluence_world.gd']},
 'opened_originals':[{'frame':n,'file':shots[n]['file'],'sha256':shots[n]['sha256']} for n in seen],
 'metrics':{'grounded_frames':len(grounded),'grounded_side_samples':len(grounded)*2,'locked_grounded_side_samples':len(locked),'near_floor_5mm_grounded_side_samples':len(near_floor),'minimum':min(minima,key=lambda v:v['m']),'grounded_penetrations_below_minus5mm':penetrations,'both_sole_minima_above5mm_grounded_frames':both_clear,'both_sole_minima_above5mm_stationary_grounded_frames':stationary_clear,'locked_minimum_m':min(v['m'] for v in locked),'locked_maximum_of_minima_m':max(v['m'] for v in locked),'consecutive_locked_sample_pairs':len(drifts),'maximum_sampled_anchor_drift':max(drifts,key=lambda v:v['m']),'maximum_sampled_foot_endpoint_error':max(endpoint_errors,key=lambda v:v['m']),'max_world_joint_origin_step':max(world_steps,key=lambda v:v['m']),'max_body_translation_removed_joint_origin_step':max(relative_steps,key=lambda v:v['m']),'body_translation_removed_partition_maxima':partitions,'cast_entry_visual_yaw_change_degrees':math.degrees(shots[150]['visual_yaw']-shots[149]['visual_yaw'])},
 'scope':'34/210 original PNGs visually opened; every210 event/body/contact/pose record checked. No full MP4 playback. Contact is coherent CPU skinning from captured imported rig, not independent GPU readback. Five-mm bins describe existing fixture data, not acceptance thresholds. Boolean lock is not eligibility or visible contact. Thirty-Hz adjacent samples can miss 60-Hz internal events and do not prove C0/C1 bounds. No baseline/candidate improvement comparison or hardware FPS.'}
(HERE/'tape-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks_passed':result['evidence_checks_passed'],'count':len(checks),'failed':[c['name'] for c in checks if not c['passed']],'metrics':result['metrics']},indent=2))
