"""Offline GLB projections and first-scene-hit perimeter rays; no import/render."""
import sys,json,hashlib,math
from pathlib import Path
import numpy as np
ROOT=Path('/workspace/ANDOLAN/games/yuga-native');OUT=ROOT/'docs/evidence/visual-rounds/round3/role02'
sys.path.insert(0,str(ROOT/'art/hero-rama-lod'));from glb_lod import GLB
sys.path.insert(0,str(OUT));from scene_geometry import glb,ray_hits,rotate
sys.path.insert(0,str(ROOT/'art/visual-rounds/groom'));from replay_motion import skin
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=Path('/workspace/scratch/visual-round3/role-08/groom-r5/groom-manifest.json')
candidate=Path(json.loads(manifest.read_text())['levels']['near']['output'])
base=Path('/workspace/scratch/visual-round2/role-08/face-form-candidate-r6/candidate.glb')
runtime=Path('/workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json');samples=json.loads(runtime.read_text())['samples'];pose=samples[0]['bone_global_poses']
parts=[(tri,mat,name) for name,items in glb('assets/environment/lanka_courtyard.glb').items() for tri,mat in items]
def points(path):
 g=GLB(path);groups={'head':[],'cloth':[],'fullbody':[]}
 for mi,pi,p in g.primitives():
  v=g.array(p['attributes']['POSITION']).astype(float);mat=g.doc['materials'][p['material']]['name'];posed=skin(g,p,v,pose) if 'JOINTS_0' in p['attributes'] else v
  groups['fullbody'].append(posed)
  if mi==2 and mat in ['Cobalt handwoven silk','Cobalt lotus brocade','Ivory silk']:groups['cloth'].append(posed)
  selection=np.zeros(len(v),bool)
  if mi==2 and mat=='Swept black hair':selection[:]=True
  elif mi==1:selection[:]=True
  elif mi==2:selection=(v[:,1]>1.5)&(abs(v[:,0])<.20)
  if selection.any():groups['head'].append(posed[selection])
 return {k:np.vstack(v) for k,v in groups.items()}
assets={'baseline':points(base),'candidate':points(candidate)}
def frame(camera,target,fov):
 forward=np.array(target)-camera;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right);up=np.cross(right,forward)
 return forward,right,up,960/(2*math.tan(math.radians(fov)/2))
def projection(world,camera,target,fov):
 f,r,u,scale=frame(camera,target,fov);delta=world-camera;z=delta@f
 pix=np.c_[640+scale*(delta@r)/z,480-scale*(delta@u)/z]
 return {'min':pix.min(0).tolist(),'max':pix.max(0).tolist(),'min_depth_m':float(z.min()),'vertices':len(world),'passed_24px':bool(z.min()>.08 and np.all(pix.min(0)>=24) and np.all(pix.max(0)<=[1256,936]))}
shots=[]
for id,z,yaw,kind,night in [('light-front',-15,-90,'head',False),('dark-front',-1,-90,'head',False),('dark-rear',-1,90,'head',False),('dark-profile',-1,0,'head',False),('light-fullbody',-15,-90,'fullbody',False),('dark-fullbody',-1,90,'fullbody',False),('dark-rear-night',-1,90,'head',True)]:
 player=np.array([19,.05,z]);target=player+np.array([0,1.56 if kind=='head' else 1.0,0]);camera=target+np.array([-1.6 if kind=='head' else -4.0,-.50 if kind=='head' else -.50,0]);fov=38 if kind=='head' else 42
 bounds={}
 for name,groups in assets.items():
  bounds[name]={k:projection(rotate(v,yaw)+player,camera,target,fov)for k,v in groups.items()}
 low=np.min([bounds[n]['head']['min'] for n in bounds],0)-12;high=np.max([bounds[n]['head']['max']for n in bounds],0)+12
 perimeter=[]
 for t in np.linspace(0,1,9):
  perimeter.extend([[low[0]+t*(high[0]-low[0]),low[1]],[low[0]+t*(high[0]-low[0]),high[1]],[low[0],low[1]+t*(high[1]-low[1])],[high[0],low[1]+t*(high[1]-low[1])]])
 f,r,u,s=frame(camera,target,fov);hits=[]
 for px,py in perimeter:
  d=f+r*(px-640)/s-u*(py-480)/s;h=ray_hits(parts,camera,d)
  hits.append({'pixel':[px,py],'hit':h[0]if h else None})
 dark=sum(bool(h['hit'] and h['hit']['material']=='Indigo_glazed_stone')for h in hits)
 before=sum(bool(h['hit']and h['hit']['distance_m']<np.linalg.norm(target-camera)-.5)for h in hits)
 shots.append({'id':id,'player_position_m':player.tolist(),'visual_yaw_degrees':yaw,'camera_position_m':camera.tolist(),'look_at_m':target.tolist(),'fov_degrees':fov,'near_m':.05,'far_m':180,'night':night,'required_bounds':kind,'projection':bounds,'head_perimeter_scene_rays':hits,'indigo_first_hit_fraction':dark/len(hits),'foreground_hit_count':before})
 print(id,'head',bounds['candidate']['head']['min'],bounds['candidate']['head']['max'],'required_pass',all(bounds[n][kind]['passed_24px']for n in bounds),'dark',dark,'/',len(hits),'foreground',before)
source_paths=[base,candidate,runtime,manifest,ROOT/'assets/environment/lanka_courtyard.glb',ROOT/'scripts/courtyard.gd',ROOT/'scripts/player.gd',ROOT/'scripts/rama_secondary_motion.gd',ROOT/'shaders/rama_secondary_cloth.gdshader',ROOT/'tools/visual-rounds/capture.gd',ROOT/'tools/visual-rounds/run.py',OUT/'scene_geometry.py',Path(__file__),ROOT/'art/hero-rama-lod/glb_lod.py',ROOT/'art/visual-rounds/groom/replay_motion.py']
report={'schema':1,'task':'R3-02','source_commit':'0437ea91edf6989ff78c1eeadb3661f4825b60f2','source_sha256':{str(p):sha(p)for p in source_paths},'pose_sample_id':samples[0]['id'],'pose_scope':'Actual previously recorded baseline skeleton matrices replayed on current source GLBs with inverse bind matrices; not imported candidate or newly executed runtime','source_posed_bounds':{a:{k:{'min_m':v.min(0).tolist(),'max_m':v.max(0).tolist(),'vertices':len(v)}for k,v in groups.items()}for a,groups in assets.items()},'shots':shots,'limits':['Perimeter rays test first scene triangles outside the projected bounding rectangle, not final pixel color or hair alpha.','Projection uses a recorded baseline pose. Capture owner must repeat on actual posed imported vertices including shader offsets for every captured frame.','Entire head includes full principal hair, topknot, face and central head/neck; cloth group includes both cobalt materials and ivory. Fullbody includes weapon.','Dark context is existing indigo stone, not foliage; original foliage gate remains unclosed.','No new runtime, import, render, collision sweep or physical-GPU timing executed.']}
(OUT/'geometry-verification.json').write_text(json.dumps(report,indent=2)+'\n')
