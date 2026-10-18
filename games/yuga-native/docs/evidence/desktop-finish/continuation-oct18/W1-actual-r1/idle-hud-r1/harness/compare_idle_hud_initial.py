from pathlib import Path
import hashlib,json,importlib.util,math
from PIL import Image
import numpy as np
W=Path(__file__).parent.parent
P=Path('/workspace/scratch/yuga-frontage-production-r1/compare_frontage_r2.py');spec=importlib.util.spec_from_file_location('prior',P);prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((W/'hud-baseline-actual-r1/capture.json').read_text());b=json.loads((W/'hud-candidate-actual-r1/capture.json').read_text());errors=[];a,oa=prior.normalize_finish_owner(a,'baseline',errors);b,ob=prior.normalize_finish_owner(b,'candidate',errors);left=a['shots'][0];right=b['shots'][0]
expected={
 '/traversal_hud/ability':['VAYU LIFT · GROUND · 0m','Energy 100 / 100'],
 '/traversal_hud/ability_rect/0/1':[419.,502.],'/traversal_hud/custom_minimum/1':[116.,88.],'/traversal_hud/energy_percentage':[True,False],'/traversal_hud/energy_rect/0/1':[444.,527.],'/traversal_hud/energy_rect/1/1':[28.,14.],
 '/traversal_hud/goal':['G tether: aim at a gold ring ≤36m\nOptional: reach a raised landing court','F flight · G tether ≤36m'],
 '/traversal_hud/goal_minimum/1':[42.,0.],'/traversal_hud/goal_rect/0/1':[477.,546.],'/traversal_hud/goal_rect/1/1':[89.,20.],'/traversal_hud/rect/0/1':[407.,490.],'/traversal_hud/rect/1/1':[171.,88.],
 '/visible_hud_peers/TraversalStatus':['[P: (1028.0, 407.0), S: (232.0, 171.0)]','[P: (1028.0, 490.0), S: (232.0, 88.0)]']}
allowed={'/drawn_frame','/physics_frame','/process_frame','/pose_signal_counters/drawn_frame','/pose_signal_counters/physics_frame','/pose_signal_counters/process_frame','/frontage/branch','/sha256'}
diffs=prior.differences(left,right);unexpected=[];seen=set()
for row in diffs:
 path=row['path']
 if path in expected:
  if [row.get('a'),row.get('b')]!=expected[path]:unexpected.append(row)
  seen.add(path)
 elif path not in allowed:unexpected.append(row)
if seen!=set(expected):errors.append('Missing expected exact HUD changes')
sa=a['source_sha256'];sb=b['source_sha256'];source_diffs=[n for n in sorted(sa.keys()|sb.keys()) if sa.get(n)!=sb.get(n)];expected_source=['res://.graphics-six-snapshot.json','scripts/confluence_world.gd','tools/visual-rounds/frontage-review.json'];source_ok=source_diffs==expected_source and sa['scripts/confluence_world.gd']=='1301701f7f8b6a711de7a36a6d283d88f1240708a7186053fa51bfc572ca8c76' and sb['scripts/confluence_world.gd']=='5fde1f003fa9f9d08309c4db656a078b2a028412dcad97d84e101bf7ee3ed6a8'
la=json.loads((W/'hud-baseline-actual-r1-logs/run.json').read_text());lb=json.loads((W/'hud-candidate-actual-r1-logs/run.json').read_text());keys=['engine_sha256','runner_sha256','helper_sha256','shader_cache_seed','godot_shader_cache_seed','affinity','thread_limits'];common={k:la[k]==lb[k] for k in keys}
x=np.array(Image.open(W/'hud-baseline-actual-r1'/left['file']).convert('RGBA'));y=np.array(Image.open(W/'hud-candidate-actual-r1'/right['file']).convert('RGBA'));different=np.any(x!=y,axis=2);points=np.argwhere(different);bbox=[int(points[:,1].min()),int(points[:,0].min()),int(points[:,1].max())+1,int(points[:,0].max())+1] if len(points) else None
# The Window canvas is1280x720 mapped to960x540; one physical pixel covers Panel border rasterization outside its logical rect.
rects=[left['traversal_hud']['rect'],right['traversal_hud']['rect']];sx=x.shape[1]/1280;sy=x.shape[0]/720
roi=[max(0,math.floor(min(r[0][0] for r in rects)*sx)-1),max(0,math.floor(min(r[0][1] for r in rects)*sy)-1),min(x.shape[1],math.ceil(max(r[0][0]+r[1][0] for r in rects)*sx)+1),min(x.shape[0],math.ceil(max(r[0][1]+r[1][1] for r in rects)*sy)+1)]
mask=np.zeros(different.shape,dtype=bool);mask[roi[1]:roi[3],roi[0]:roi[2]]=True;outside=int(np.logical_and(different,~mask).sum())
checks={'both_actual_reports_complete':a['complete'] and b['complete'] and not a['preflight'] and not b['preflight'],'all_collector_checks_pass':all(c['passed'] for r in [a,b] for c in r['checks']),'strict_remaining_controls_exact':not unexpected and not errors,'exact_only_admitted_source_changes':source_ok,'same_runtime_helper_seeds_affinity_threads':all(common.values()),'e69_runtime':la['engine_sha256']=='e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e','pixels_outside_declared_panel_hull_exact':outside==0,'actual_panel_changed':len(points)>0,'source_unchanged':a['source_unchanged'] and b['source_unchanged']}
r={'passed':all(checks.values()),'checks':checks,'expected_exact_UI_changes':expected,'allowed_absolute_counters_and_role_fields':sorted(allowed),'all_shot_differences':diffs,'unexpected':unexpected,'errors':errors,'source_diff_paths':source_diffs,'common_runtime_checks':common,'finish_owner_normalization':{'prior_comparator_sha256':sha(P),'baseline':oa,'candidate':ob,'errors':errors},'pixels':{'mode':'RGBA all4channels','changed_pixels':int(different.sum()),'changed_bbox':bbox,'admitted_panel_union_plus_1physical_border_pixel':roi,'outside_changed_pixels':outside,'scope':'Fullframe exact outside the two declared TraversalStatus rects; only their onepixel border rasterization is admitted.'},'actual_panel_height_logical':[171,88],'no_other_HUD_peer_changes':all(row['path']=='/visible_hud_peers/TraversalStatus' for row in diffs if row['path'].startswith('/visible_hud_peers/'))}
(W/'hud-comparison-r1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k in ['passed','checks','unexpected','errors','pixels']}));raise SystemExit(0 if r['passed'] else 1)
