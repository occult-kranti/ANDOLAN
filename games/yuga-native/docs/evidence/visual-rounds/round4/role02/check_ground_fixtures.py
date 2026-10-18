"""Existing collision surfaces, route broadphases and conservative camera envelope."""
from pathlib import Path
import json,hashlib,sys,itertools,math
import numpy as np
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'docs/evidence/visual-rounds/round3/role02'));from scene_geometry import glb,ray_hits
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
world=json.loads((ROOT/'assets/world/confluence-map.json').read_text());court=glb('assets/environment/lanka_courtyard.glb');colliders=[(t,m,n)for n,parts in court.items()if n.startswith('COL_')for t,m in parts]
visual_parts=[(t,m,n)for n,parts in court.items()for t,m in parts]
normal=[0,1,0];floor=.4399999976158142
fixtures=[{'id':'courtyard-start-stop-turn','scene':'res://scenes/courtyard.tscn','start':[0,.0001,12],'support_y':0.,'support':'CourtyardFloor axis-aligned box top','route_xz':[[0,12],[0,6],[3,6],[3,9]],'controls':'Actual move_forward until z6, release until speed<.12, move_right until x3, release, move_back until z9, release. Use measured threshold crossings, not frame-snapped placement. Log expected targets versus actual capsule route.','check_bounds':[-22,22,-25,25]}, {'id':'courtyard-gallery-jump','scene':'res://scenes/courtyard.tscn','start':[19,floor+.0001,-1],'support_y':floor,'support':'existing COL_BEVEL_Indigo_glazed_stone top','route_xz':[[19,-1]],'controls':'Settle on existing deck, press/release jump once through InputMap, allow normal gravity and landing, then hold idle. Do not write root height or floor state during take.','check_bounds':[15.40500259399414,20.994998931884766,-17.44499969482422,17.44499969482422]}, {'id':'confluence-deck-land','scene':'res://scenes/confluence_world.tscn','start':[-20,9.5001,-88],'support_y':8.,'support':'sun-lift-west-deck top: manifest base0 + height8','route_xz':[[-20,-88]],'controls':'One explicit documented initial airborne placement at1.5m above deck; zero input and zero initial velocity, normal unpaused gravity/collision to landing; no traversal flight/grapple active. Report actual first contact normal, collider and time. Then one ordinary jump and settle.','check_bounds':[-24,-16,-92,-84]}]
def sample_route(route):
 if len(route)==1:return [route[0]]
 out=[]
 for a,b in zip(route,route[1:]):
  a=np.array(a);b=np.array(b);n=max(1,int(np.ceil(np.linalg.norm(b-a)/.25)))
  out.extend((a+(b-a)*t).tolist()for t in np.linspace(0,1,n+1))
 return out
def project_envelope():
 # Room for complete body, bow and ballistic jump; actual vertices remain live gate.
 corners=np.array(list(itertools.product([-1.,1.],[0.,3.75],[-1.,1.])));camera=np.array([0.,2.4,7.]);target=np.array([0.,1.7,0.]);f=target-camera;f/=np.linalg.norm(f);r=np.cross(f,[0,1,0]);r/=np.linalg.norm(r);u=np.cross(r,f);d=corners-camera;z=d@f;s=960/(2*math.tan(math.radians(52)/2));pixels=np.c_[640+s*(d@r)/z,480-s*(d@u)/z];return {'min':pixels.min(0).tolist(),'max':pixels.max(0).tolist(),'all_24px':bool(np.all(pixels.min(0)>=24)and np.all(pixels.max(0)<=[1256,936]))}
rows=[]
for fixture in fixtures:
 p=np.array(fixture['start']);route=sample_route(fixture['route_xz']);xmin,xmax,zmin,zmax=fixture['check_bounds'];radius=.29;clearance=min(min(x-xmin,xmax-x,z-zmin,zmax-z)-radius for x,z in route);obstacles=[]
 if fixture['scene'].endswith('courtyard.tscn'):
  for x,z in route:
   lo=np.array([x-radius,fixture['support_y']+.001,z-radius]);hi=np.array([x+radius,fixture['support_y']+1.8,z+radius])
   for t,m,n in colliders:
    hit=np.all(t.max(1)>=lo,1)&np.all(t.min(1)<=hi,1)
    if hit.any():obstacles.append({'route_xz':[x,z],'object':n,'candidate_triangles':int(hit.sum())})
 camera_blockers=[]
 if fixture['scene'].endswith('courtyard.tscn'):
  for x,z in route:
   origin=np.array([x,fixture['support_y']+2.4,z+7])
   for ox,y,oz in itertools.product([-.3,.3],[.02,1.8,3.4],[-.2,.2]):
    target=np.array([x+ox,fixture['support_y']+y,z+oz]);hits=ray_hits(visual_parts,origin,target-origin)
    if hits and hits[0]['distance_m']<np.linalg.norm(target-origin)-.05:camera_blockers.append({'route_xz':[x,z],'target':target.tolist(),'hit':hits[0]})
 support_ray=ray_hits(colliders,[p[0],3,p[2]],[0,-1,0])[:1]if fixture['id']=='courtyard-gallery-jump'else[]
 rows.append({**fixture,'normal':normal,'route_samples':len(route),'minimum_edge_clearance_after_capsule_radius_m':clearance,'source_COL_overlap_candidates':obstacles,'camera_foreground_ray_hits':camera_blockers,'support_triangle_ray':support_ray,'projection_envelope':project_envelope(),'passed':clearance>.29 and not obstacles and not camera_blockers and project_envelope()['all_24px']})
boxes=world['authority_collision_boxes']+world['traversal']['native_collision_boxes'];deck=next(b for b in boxes if b['id']=='sun-lift-west-deck');assert deck['position']==[-20,0,-88]and deck['size']==[8,8,8]and deck['anchor']=='base_center'
report={'task':'R4-02','source_commit':'0437ea91edf6989ff78c1eeadb3661f4825b60f2','fixtures':rows,'camera':{'offset_from_horizontal_player_and_support_m':[0,2.4,7],'target_offset_m':[0,1.7,0],'fov_degrees':52,'near_m':.05,'far_m':180,'viewport':[1280,960],'follow':'Track actual horizontal player coordinates only. Hold camera Y relative to source support plane, so jumps and floor contact stay visible. No camera fit to changing candidate bounds.'},'source_jump':{'upward_speed_mps':7.2,'gravity_mps2':18.,'continuous_ballistic_apex_above_support_m':1.44,'ideal_return_seconds':.8,'limit':'Analytic reference, not measured discrete capsule trajectory; runtime collision/physics must report its actual apex/time.'},'required_runtime_samples':['physics tick/time and actual input','capsule global transform/velocity/is_on_floor/get_floor_normal','slide collider identity/contact position/normal','final modifier-processed bone transforms and skin vertices','sole minimum support-plane signed distance','planted anchor original world position, drift and release state','spring arm hit length, camera transform and head/feet/bow projected bounds','authority/action clocks if an action is active'],'source_sha256':{str(p):sha(p)for p in [Path(__file__),ROOT/'assets/environment/lanka_courtyard.glb',ROOT/'assets/world/confluence-map.json',ROOT/'scripts/player.gd',ROOT/'scripts/courtyard.gd',ROOT/'scripts/confluence_world.gd',ROOT/'scripts/rama_motion.gd']},'passed':all(r['passed']for r in rows),'limits':['Source surfaces are existing axis-aligned flat planes with UP normals; no sloped-ground acceptance.','Source route samples/broadphase are not executed collision sweeps or input.','View envelope is conservative geometry design; current imported fullbody and actual world occlusion remain native gates.','Accepted motion baseline remains unchanged; all role05 release candidates remain rejected.']}
(OUT/'ground-fixtures.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'fixtures':[{'id':r['id'],'passed':r['passed'],'obstacles':len(r['source_COL_overlap_candidates']),'edge_clearance_m':r['minimum_edge_clearance_after_capsule_radius_m']}for r in rows],'camera':project_envelope()},indent=2));assert report['passed']
