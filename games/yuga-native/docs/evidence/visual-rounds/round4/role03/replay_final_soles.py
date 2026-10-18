from pathlib import Path
import sys,json,hashlib
import numpy as np
R=Path('/workspace/ANDOLAN/games/yuga-native');O=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'art/hero-rama-lod'));from glb_lod import GLB
sys.path.insert(0,str(R/'art/visual-rounds/groom'));from replay_motion import skin
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cp=R/'docs/evidence/visual-rounds/round3/role06/baseline/continuity/capture.json';orderp=O/'bone-order.json';capture=json.loads(cp.read_text());order=json.loads(orderp.read_text());g=GLB('/workspace/scratch/visual-round2/role-08/face-form-candidate-r6/candidate.glb');names=[x['name']for x in order['bones']];joints=[g.doc['nodes'][i]['name']for i in g.doc['skins'][0]['joints']]
assert len(names)==164 and set(names)==set(joints) and sha(g.path)==order['source_sha256']==capture['source_sha256']['res://assets/heroes/rama-hero.glb']
# Transform3D normal() serialization contains basis columns then origin.
def transform(raw):
 t=np.eye(4);t[:3,:]=np.array(raw).T;return t
selections=[]
for mi,pi,p in g.primitives():
 if 'JOINTS_0'not in p['attributes']:continue
 v=g.array(p['attributes']['POSITION']);ji=g.array(p['attributes']['JOINTS_0']).astype(int);weights=g.array(p['attributes']['WEIGHTS_0']);lower=v[:,1]<.30
 for side in ['L','R']:
  relevant=np.array([name.startswith(('foot','toe'))and name.endswith('.'+side)for name in joints]);mask=lower&((relevant[ji]*weights).sum(1)>.5)
  if mask.any():selections.append((mi,pi,p,v,side,mask))
rows=[]
for s in capture['shots']:
 poses={name:transform(raw).tolist()for name,raw in zip(names,s['rendered_pose_globals'])};world=transform(s['player_transform']);a=s['visual_yaw'];yaw=np.eye(4);yaw[:3,:3]=[[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]];world=world@yaw;by={side:[]for side in ['L','R']}
 for mi,pi,p,v,side,mask in selections:
  posed=skin(g,p,v,poses)[mask]
  points=(np.c_[posed,np.ones(len(posed))]@world.T)[:,:3];by[side].append(points)
 floor=float(s['ground_contact']['point'][1]);soles={}
 for side,groups in by.items():
  points=np.vstack(groups);i=int(points[:,1].argmin());soles[side]={'minimum_height_above_surface_m':float(points[i,1]-floor),'minimum_vertex_world_m':points[i].tolist(),'selected_vertices':len(points),'reported_foot_lock':s['motion']['foot_locks'][side]}
 rows.append({'id':s['id'],'pose_pin':s['rendered_pose_pin'],'floor_y_m':floor,'root_above_floor_m':float(world[1,3]-floor),'soles':soles,'source_replay_only':True})
report={'task':'R4-03','scope':'Offline source vertices skinned using actual rendered final-modifier pose arrays, with independently dumped actual PackedScene bone names. Not a new imported-vertex measurement; no per-frame Skin bind dump or rig transform was archived. Source hierarchy and player code put rig at yaw-only HeroVisual; any future exact native sole claim must record rig.global_transform and actual imported binds/vertices.','source_sha256':{str(p):sha(p)for p in [Path(__file__),g.path,cp,orderp,R/'scripts/player.gd',R/'art/visual-rounds/groom/replay_motion.py']},'bone_order_source_matches_capture':True,'bone_order_matches_gltf_joint_order':names==joints,'samples':rows,'selected_pixel_witnesses':[r for r in rows if r['id']in ['frame-029','frame-030','frame-031','frame-078']],'minimum_signed_sole_height_m':min(v['minimum_height_above_surface_m']for r in rows for v in r['soles'].values()),'maximum_locked_foot_minimum_height_m':max(v['minimum_height_above_surface_m']for r in rows for v in r['soles'].values()if v['reported_foot_lock'])}
(O/'final-sole-source-replay.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['bone_order_matches_gltf_joint_order','selected_pixel_witnesses','minimum_signed_sole_height_m','maximum_locked_foot_minimum_height_m']},indent=2))
