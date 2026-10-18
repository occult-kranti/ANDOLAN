from pathlib import Path
import hashlib,json,os,shutil,importlib.util
W=Path(__file__).parent.parent;H=W/'harness';R=Path('/workspace/ANDOLAN/games/yuga-native');P=W/'world-candidate-project'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('m',H/'snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);old=m.verify(P);canonical=m.inventory(R);runtime={n:v for n,v in canonical.items() if n.startswith(('scripts/','scenes/','shaders/','assets/')) or n in m.ROOT_FILES};runtime['scripts/confluence_world.gd']=m.metadata(P/'scripts/confluence_world.gd')
expected=dict(old['files']);origins={}
for n,item in runtime.items():
 if expected.get(n)!=item:expected[n]=item;origins[n]=R/n
for n,item in expected.items():
 if n.startswith(('assets/','.godot/imported/')):assert (R/n).is_file() and m.metadata(R/n)==item
rows={}
for role in ['baseline','candidate']:
 D=W/('hud-'+role+'-project');assert not D.exists();D.mkdir();files=dict(expected)
 for n,origin in [('tools/graphics-six/capture_scene_anchors.gd',H/'capture_idle_hud.gd')]:origins[n]=origin;files[n]=m.metadata(origin)
 for n,item in files.items():
  target=D/n;target.parent.mkdir(parents=True,exist_ok=True);origin=origins.get(n,P/n)
  if n in origins or n in m.AUX_FILES or n=='tools/visual-rounds/frontage-review.json':shutil.copyfile(origin,target)
  else:os.link(origin,target)
 n='tools/visual-rounds/frontage-review.json';(D/n).write_text(json.dumps({'branch':role})+'\n');files[n]=m.metadata(D/n)
 record=dict(old);record.update(project=str(D),round='continuation-idle-hud-'+role,files=files,common_harness_overlay={'tools/graphics-six/capture_scene_anchors.gd':files['tools/graphics-six/capture_scene_anchors.gd']},scope='Prepared fullworld idle-HUD pair; candidate confluence still baseline until W2 freeze/admission. No render admitted.')
 (D/m.MARKER).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');m.verify(D);rows[role]={'project':str(D),'initial_seal_sha256':sha(D/m.MARKER),'confluence_sha256':sha(D/'scripts/confluence_world.gd')}
(W/'hud-prepared-staging.json').write_text(json.dumps({'actual_admitted':False,'waiting_for':'W2 baseline/current confluence freeze and source gates','roles':rows,'common_source_runtime':runtime,'no_import_or_full_asset_copy':True},indent=2)+'\n');m.verify(P);print(json.dumps(rows))
