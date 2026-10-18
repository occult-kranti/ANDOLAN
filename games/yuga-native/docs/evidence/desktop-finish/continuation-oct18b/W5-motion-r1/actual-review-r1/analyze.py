"""Read-only comparison of the actual 270-frame traces; no engine or pose writes."""
import gzip, hashlib, json, math, re, sys
from pathlib import Path
import numpy as np

REPO = next(p for p in Path(__file__).resolve().parents if (p/'games/yuga-native').is_dir())
GAME = REPO/'games/yuga-native'
BASE = GAME/'docs/evidence/desktop-finish/next-motion/W5-locomotion-actual-current-r1'
OWNER = GAME/'docs/evidence/desktop-finish/continuation-oct18b/W1-actual-r1/motion-candidate-r1'
ROOT = OWNER/'inputs'
CAND = OWNER/'originals'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
b = json.loads(gzip.decompress((BASE/'capture.json.gz').read_bytes()))
candidate_raw = gzip.decompress((OWNER/'capture.json.gz').read_bytes())
c = json.loads(candidate_raw)
run = json.loads((OWNER/'raw-logs/run.json').read_text())
owner = json.loads((OWNER/'receipt.json').read_text())
assert sha(OWNER/'receipt.json')=='bc8d344e78b2b048c25f425da155adf158ed7f258efd51ed4b2de1bdb2528fee'
assert hashlib.sha256(candidate_raw).hexdigest()==owner['gzip']['regular_sha256']
assert len(candidate_raw)==owner['gzip']['regular_bytes']
for relative,h in owner['files'].items(): assert sha(OWNER/relative)==h
names = c['bone_names']
library = GAME/'assets/animations/rama_hero_motion.tres'
text = library.read_text()
parents = list(map(int, re.search(r'metadata/rama_rig_parents = PackedInt32Array\(([^)]*)\)', text)[1].split(',')))
assert json.loads(re.search(r'metadata/rama_rig_names = Array\[String\]\(([^\n]*)\)', text)[1]) == names
assert sha(library) == c['source_sha256']['res://assets/animations/rama_hero_motion.tres']
assert len(b['shots']) == len(c['shots']) == 270 and b['bone_names'] == names and len(names) == len(parents) == 164
leg = [i for i,n in enumerate(names) if n.startswith(('upperleg','lowerleg','foot.','toe'))]
nonleg = [i for i in range(len(names)) if i not in leg]
keys = ['camera','light','render_settings','skin_materials','face','secondary','player_transform','physics_frame','render_frame','action','final_modifier_body','draw_observed_body','actual_camera_identity','visual_yaw','tree_paused','viewport']
controls = {k: all(x[k] == y[k] for x,y in zip(b['shots'],c['shots'])) for k in keys}
controls.update({k: b[k] == c[k] for k in ['sequence_controls','sequence_plan','time_controls','camera_contract']})
changed = {names[i]:[j for j,(x,y) in enumerate(zip(b['shots'],c['shots'])) if x['rendered_pose_globals'][i] != y['rendered_pose_globals'][i]] for i in range(164)}
changed = {k:v for k,v in changed.items() if v}
controls['all_nonleg_globals_exact'] = all(not changed.get(names[i]) for i in nonleg)
controls['all_pose_frames_finite_164'] = all(len(s['rendered_pose_globals'])==164 and np.isfinite(np.array(s['rendered_pose_globals'])).all() for data in [b,c] for s in data['shots'])
controls['source_before_after_exact'] = c['source_sha256'] == c['source_after_sha256'] and c['source_unchanged']
assert all(controls.values()), controls
source_delta = {k:{'baseline':b['source_sha256'].get(k),'candidate':c['source_sha256'].get(k)} for k in set(b['source_sha256'])|set(c['source_sha256']) if b['source_sha256'].get(k)!=c['source_sha256'].get(k)}
assert set(source_delta) == {'res://.graphics-six-snapshot.json','res://scripts/rama_motion.gd','res://tools/graphics-six/capture_locomotion.gd'}
assert run['complete'] and run['exit_code']==0 and not run['errors'] and run['report_sha256']==hashlib.sha256(candidate_raw).hexdigest()
assert all(x['passed'] for x in run['checks']) and run['raw_pngs']==32
for filename,key in [('motion-pair.json','pair_sha256'),('motion-render-inputs.json','render_inputs_sha256')]: assert sha(ROOT/filename)==run[key]
assert sha(ROOT/'.graphics-six-snapshot.json')==run['stage_seal_sha256']
for resource in ['scripts/rama_motion.gd','tools/graphics-six/capture_locomotion.gd']:
    assert sha(ROOT/Path(resource).name)==c['source_sha256']['res://'+resource]

def rotation(s,i):
    matrices = s['rendered_pose_globals']
    child = np.array(matrices[i][:3]).T
    local = np.linalg.solve(np.array(matrices[parents[i]][:3]).T, child) if parents[i]>=0 else child
    # Remove tiny imported scale/shear; nearest proper orthogonal matrix.
    u,_,v = np.linalg.svd(local); r=u@v
    assert np.linalg.det(r)>0
    return r
def angle(a,d,i):
    r=rotation(a,i).T@rotation(d,i)
    return math.degrees(math.acos(max(-1,min(1,(np.trace(r)-1)/2))))
def metrics(data):
    rows=[]
    for j in range(225,270):
        s=data['shots'][j];old=data['shots'][j-1];body=s['final_modifier_body']
        angles={names[i]:angle(old,s,i) for i in leg if names[i].startswith(('upperleg','lowerleg','foot.'))}
        ankles={}
        rig=np.array(body['rig_transform'][:3]).T; prev=old['final_modifier_body'];oldrig=np.array(prev['rig_transform'][:3]).T
        for side in ['L','R']:
            i=names.index('foot.'+side)
            rel=rig@np.array(s['rendered_pose_globals'][i][3]);oldrel=oldrig@np.array(old['rendered_pose_globals'][i][3])
            world=rel+np.array(body['rig_transform'][3]);oldworld=oldrel+np.array(prev['rig_transform'][3])
            ankles[side]={'world_step_mm':float(np.linalg.norm(world-oldworld)*1000),'root_relative_step_mm':float(np.linalg.norm(rel-oldrel)*1000)}
        sides=s['sole_contacts']['sides']
        rows.append({'frame':j,'physics':s['physics_frame'],'render':s['render_frame'],'on_floor':body['on_floor'],'locomotion':body['motion']['locomotion'],'transition_age_s':body['transition_age'],'locks':body['motion']['foot_locks'],'root_y':body['position_world'][1],'velocity_y':body['velocity'][1],'sole_gap_mm':{k:sides[k]['minimum_signed_m']*1000 for k in ['L','R']},'vertices_below_minus5mm':{k:sides[k]['vertices_below_minus5mm'] for k in ['L','R']},'local_steps_degrees':angles,'ankles':ankles})
    return rows
bm,cm=metrics(b),metrics(c)
saved=list(range(225,256))+[269]
assert c['saved_frame_indices']==saved and sorted(p.name for p in CAND.glob('*.png'))==[f'frame-{i:03}.png' for i in saved]
images=[]
for i in saved:
    p=CAND/f'frame-{i:03}.png'; h=sha(p); assert h==c['shots'][i]['sha256'] and c['shots'][i]['framebuffer_saved']
    images.append({'frame':i,'path':str(p),'bytes':p.stat().st_size,'sha256':h})
baseline_viewed=[]
for i in [235,237,240,248,249,250,251,252]:
    p=BASE/'originals'/f'frame-{i:03}.png';h=sha(p);assert h==b['shots'][i]['sha256'];baseline_viewed.append({'frame':i,'path':str(p),'sha256':h})
out={'scope':'All270 recorded final-modifier frames compared;32 candidate originals and8 retained baseline originals directly viewed separately.60Hz physics/30Hz observations. Angular values are shortest unsigned local-bone orientation steps reconstructed using exact library parent map; not instantaneous joint acceleration or the prior30Hz physics component metric.','controls':controls,'source_delta':source_delta,'source_records':len(c['source_sha256']),'changed_global_bones':{k:{'count':len(v),'first':min(v),'last':max(v)} for k,v in changed.items()},'nonleg_bones_exact':len(nonleg),'candidate_pngs':images,'baseline_pngs_directly_viewed':baseline_viewed,'baseline_landing_window':bm,'candidate_landing_window':cm,'input_pins':{str(p):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [BASE/'capture.json.gz',OWNER/'capture.json.gz',OWNER/'receipt.json',OWNER/'raw-logs/run.json',ROOT/'motion-pair.json',ROOT/'motion-render-inputs.json',ROOT/'.graphics-six-snapshot.json',library]},'run_identity':{k:run[k] for k in ['complete','exit_code','report_sha256','runner_sha256','engine_sha256','stage_seal_sha256','pair_sha256','render_inputs_sha256','raw_pngs','seed_unchanged','mesa_seed_unchanged']}}
dest=Path(sys.argv[1]);assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'controls':controls,'changed_bones':len(changed),'first_grounded':cm[24],'peak_contact_adjacent':max(((max(r['local_steps_degrees'].values()),r['frame']) for r in cm if 249<=r['frame']<=255)),'output':str(dest)},indent=2))
