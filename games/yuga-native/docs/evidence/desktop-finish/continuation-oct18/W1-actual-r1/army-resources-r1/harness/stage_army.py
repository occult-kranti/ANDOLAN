from pathlib import Path
import json,hashlib,shutil,importlib.util
W=Path(__file__).parent.parent;H=W/'harness';R=Path('/workspace/ANDOLAN/games/yuga-native');A=Path('/workspace/scratch/yuga-continuation-W4-army-r1/actual-helper-r1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(A/'capture_army.gd')=='eced4bde40c64e24712718b0e60c1ea46458c4bb3bef1da9789626ad4755ebb1';assert sha(A/'compare_army.py')=='8681988b086de0cb5168733185fac8a511a96c9bfb8923f6f0db9b5b87e23e70'
for n in ['capture_army.gd','compare_army.py']:shutil.copyfile(A/n,H/n)
spec=importlib.util.spec_from_file_location('snapshot',H/'snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for role in ['baseline','candidate']:
 P=W/('army-'+role+'-project');assert not P.exists();P.mkdir();(P/'scripts').mkdir();(P/'tools/graphics-six').mkdir(parents=True)
 for name in ['lane_army.gd','lane_minion.gd','lane_infantry_art.gd','lane_vehicle_art.gd','world_render_resources.gd']:
  source=(W/'world-baseline-project/scripts'/name) if role=='baseline' and name in ['lane_army.gd','lane_minion.gd'] else R/'scripts'/name
  shutil.copyfile(source,P/'scripts'/name)
 shutil.copyfile(H/'capture_army.gd',P/'tools/graphics-six/capture_scene_anchors.gd')
 (P/'project.godot').write_text('config_version=5\n[application]\nconfig/name="YUGA army geometry fixture"\n[display]\nwindow/size/viewport_width=960\nwindow/size/viewport_height=540\n[rendering]\nrenderer/rendering_method="forward_plus"\n')
 record={'schema':1,'round':'continuation-army-'+role,'store':str(W/'unused-army-store'),'files':m.inventory(P),'validated_imports':[],'changed_paths':[],'source_bytes':sum(p.stat().st_size for p in P.rglob('*') if p.is_file()),'compiled_bytes':0,'scope':'Source-only tiny fixedarmy oracle; noimports/assets/audio/Rama'}
 (P/m.MARKER).write_text(json.dumps(record,indent=2)+'\n');m.verify(P)
print('army tiny stages frozen')
