from pathlib import Path
import sys,json,hashlib,ast,copy
import numpy as np
from scipy.spatial import cKDTree
R=Path('/workspace/ANDOLAN/games/yuga-native');O=R/'docs/evidence/visual-rounds/round4/role04'
sys.path.insert(0,str(R/'art/hero-rama-lod'));from glb_lod import GLB
sys.path.insert(0,str(R/'art/visual-rounds/groom'));from replay_motion import skin
# Reuse only pure conservative geometry functions; do not rerun role04 module main.
p=R/'docs/evidence/visual-rounds/round3/role04/check_action_clearance.py';tree=ast.parse(p.read_text());body=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in ['aabb_gap','separation']];exec(compile(ast.Module(body=body,type_ignores=[]),str(p),'exec'))
g=GLB('/workspace/scratch/visual-round3/role-08/groom-r6/rama-hero.glb');runtime=json.load(open('/workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json'));samples=[s for s in runtime['samples']if s['id'].startswith(('measured_step_','guardian_circle_'))]
node=next(i for i,n in enumerate(g.doc['nodes'])if n.get('name')=='wrist.R');desc=[]
def visit(i):
 desc.append(g.doc['nodes'][i]['name'])
 for child in g.doc['nodes'][i].get('children',[]):visit(child)
visit(node);grip=np.array([0,.105,.025,1]);muzzle=np.array([0,.160,.025,1]);rows=[]
for sample in samples:
 poses=copy.deepcopy(sample['bone_global_poses']);w=np.array(poses['wrist.R']);axis=w[:3,1].copy();axis/=np.linalg.norm(axis);a=np.deg2rad(15);cross=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]]);rot=np.eye(3)*np.cos(a)+(1-np.cos(a))*np.outer(axis,axis)+np.sin(a)*cross;anchor=(w@grip)[:3];transform=np.eye(4);transform[:3,:3]=rot;transform[:3,3]=anchor-rot@anchor
 for name in desc:poses[name]=(transform@np.array(poses[name])).tolist()
 groups={k:[]for k in ['cloth','bow','hair']}
 for mi,pi,prim in g.primitives():
  mat=g.doc['materials'][prim['material']]['name'];kind='bow'if mi==0 else'hair'if(mi,pi)==(2,0)else'cloth'if mi==2 and mat in ['Ivory silk','Cobalt handwoven silk','Cobalt lotus brocade']else''
  if not kind:continue
  v=g.array(prim['attributes']['POSITION']);t=g.array(prim['indices']).reshape(-1,3);groups[kind].append(skin(g,prim,v,poses)[t])
 groups={k:np.concatenate(v)for k,v in groups.items()};gaps={k:separation(groups[k],groups['bow'])for k in ['cloth','hair']};row={'id':sample['id'],'angle_degrees':15,'wrist_subtree':desc,'grip_drift_m':float(np.linalg.norm(np.array(poses['wrist.R'])@grip-w@grip)),'muzzle_drift_m':float(np.linalg.norm(np.array(poses['wrist.R'])@muzzle-w@muzzle)),'gaps':gaps};rows.append(row);print(sample['id'],{k:v['lower_bound_m']for k,v in gaps.items()},flush=True)
report={'task':'R4-04','scope':'One +15degree wrist/grip-axis geometric feasibility experiment on6archived actual source poses. Does not execute controller envelopes, mixed poses or native contacts.','source_sha256':{str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in [Path(__file__),g.path,R/'scripts/rama_motion.gd']},'samples':rows,'all_neutral_source_crossings_removed':all(r['gaps']['cloth']['lower_bound_m']>.001 for r in rows),'grip_and_muzzle_invariant':all(r['grip_drift_m']<1e-12 and r['muzzle_drift_m']<1e-12 for r in rows)}
(O/'wrist-arc-feasibility.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'crossings_removed':report['all_neutral_source_crossings_removed'],'socket_invariant':report['grip_and_muzzle_invariant']}))
