#!/usr/bin/env python3
"""Compact differential of the unchanged declared natural tape; no engine."""
from pathlib import Path
import gzip,json,hashlib,sys
base_path=Path(sys.argv[1]);candidate_path=Path(sys.argv[2]);output=Path(sys.argv[3])
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def nums(x):
    if isinstance(x,list):
        for v in x:yield from nums(v)
    else:yield float(x)
def contact(d):
    rows=[]
    for s in d['shots']:
        sides=s['sole_contacts']['sides']
        rows.append({'frame':s['tape_index'],'physics':s['final_modifier_body']['physics_frame'],'grounded':s['final_modifier_body']['on_floor'],'gait':s['final_modifier_body']['motion']['locomotion'],'sole_mm':{side:sides[side]['minimum_signed_m']*1000 for side in ['L','R']},'locks':s['final_modifier_body']['motion']['foot_locks']})
    return rows
b=load(base_path);c=load(candidate_path);checks=[]
def check(name,value,**detail):checks.append({'name':name,'passed':bool(value),**detail})
check('both native headless coverage gates complete',b['complete'] and c['complete'] and len(b['checks'])==10 and len(c['checks'])==10 and all(x['passed'] for x in b['checks']+c['checks']))
check('same270 frame identities and bone order',len(b['shots'])==len(c['shots'])==270 and b['bone_names']==c['bone_names'] and [s['id'] for s in b['shots']]==[s['id'] for s in c['shots']])
changed=[k for k in b['source_sha256'].keys()|c['source_sha256'].keys() if b['source_sha256'].get(k)!=c['source_sha256'].get(k)]
marker_parent=load(Path(__file__).parent/'parent-marker.json');marker_candidate=load(Path(__file__).parent/'candidate-marker.json')
file_delta=sorted(k for k in marker_parent['files'].keys()|marker_candidate['files'].keys() if marker_parent['files'].get(k)!=marker_candidate['files'].get(k))
parent_hash=hashlib.sha256((Path(__file__).parent/'parent-marker.json').read_bytes()).hexdigest()
candidate_hash=hashlib.sha256((Path(__file__).parent/'candidate-marker.json').read_bytes()).hexdigest()
check('motion is sole runtime difference and exact child marker accounts for it',set(changed)=={'res://scripts/rama_motion.gd','res://.graphics-six-snapshot.json'} and file_delta==['scripts/rama_motion.gd'] and marker_candidate['previous_marker_sha256']==parent_hash and b['source_sha256']['res://.graphics-six-snapshot.json']==parent_hash and c['source_sha256']['res://.graphics-six-snapshot.json']==candidate_hash,changed=changed,file_delta=file_delta)
terms=['position_world','velocity','player_transform','rig_transform','capsules','actual_move_input','kit_report','army_elapsed','jump_count','on_floor','traversal_mode','transition_age','transition_duration','action']
diffs=[];nonleg=[];nonleg_max=0.0;all_pose_delta=[];lock_diffs=[]
for a,z in zip(b['shots'],c['shots']):
    frame=a['tape_index'];ab=a['final_modifier_body'];zb=z['final_modifier_body']
    for key in terms:
        if ab[key]!=zb[key]:diffs.append({'frame':frame,'term':key})
    if ab['physics_frame']!=zb['physics_frame']:diffs.append({'frame':frame,'term':'physics_frame'})
    for key in ['phase','action_elapsed','cancel_count','release_count','stage','locomotion']:
        if ab['motion'][key]!=zb['motion'][key]:diffs.append({'frame':frame,'term':'motion.'+key})
    if ab['motion']['foot_locks']!=zb['motion']['foot_locks']:lock_diffs.append(frame)
    for index,name in enumerate(b['bone_names']):
        x=a['rendered_pose_globals'][index];y=z['rendered_pose_globals'][index]
        if x==y:continue
        delta=max(abs(u-v) for u,v in zip(nums(x),nums(y)))
        all_pose_delta.append({'frame':frame,'bone':name,'maximum_scalar_delta':delta})
        if not name.startswith(('upperleg','lowerleg','foot','toe')):
            nonleg.append({'frame':frame,'bone':name,'maximum_scalar_delta':delta});nonleg_max=max(nonleg_max,delta)
check('root capsule input authority and all clocks exact',not diffs,differences=diffs[:30],count=len(diffs))
check('nonleg final matrices exact',not nonleg,differences=nonleg[:30],count=len(nonleg),maximum_scalar_delta=nonleg_max)
check('ordinary fixed-anchor admission schedule exact',not lock_diffs,different_frames=lock_diffs)
br=contact(b);cr=contact(c)
landing=next(r['frame'] for i,r in enumerate(cr) if i>225 and r['grounded'] and not cr[i-1]['grounded'])
bmin=min(v for r in br for v in r['sole_mm'].values());cmin=min(v for r in cr for v in r['sole_mm'].values())
check('all sampled soles retain existing minus5mm floor',cmin>=-5,baseline_min_mm=bmin,candidate_min_mm=cmin)
check('sampled minimum penetration does not increase',cmin>=bmin,baseline_min_mm=bmin,candidate_min_mm=cmin)
check('first grounded sole gaps are within5mm',max(cr[landing]['sole_mm'].values())<=5,frame=landing,baseline=br[landing],candidate=cr[landing])
result={'status':'HEADLESS_COMPARISON_ONLY','passed':all(x['passed'] for x in checks),'count':len(checks),'checks':checks,'baseline':pin(base_path),'candidate':pin(candidate_path),'landing_witness':{'baseline':br[landing-4:landing+9],'candidate':cr[landing-4:landing+9]},'changed_pose_samples':len(all_pose_delta),'changed_pose_bounds':{'first_frame':min([r['frame'] for r in all_pose_delta],default=None),'last_frame':max([r['frame'] for r in all_pose_delta],default=None)},'limits':['Prior strict26/27 comparative limitation remains.','No new raster or human full-speed review.','An invalid pre-contact support retains legacy fallback.']}
output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':[(x['name'],x['passed']) for x in checks],'landing':result['landing_witness'],'changed_pose_bounds':result['changed_pose_bounds']}))
