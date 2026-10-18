from pathlib import Path
import json,hashlib,importlib.util,shutil
W=Path(__file__).parent.parent;H=W/'harness'
s=(H/'capture_frontage_base.gd').read_text()
a=s.index('func take_frontage(');b=s.index('func finish(',a)
s=s[:a]+'''func take_frontage(id: String) -> bool:
	if not take(id): return false
	var item: Dictionary = shots.back()
	check("full164final-modifier poses and finite controls",item.hero_skeleton.get("bone_names",[]).size()==164 and item.hero_skeleton.get("bone_global_poses",[]).size()==164 and item.serialization_errors.is_empty())
	check("final pose belongs to captured frame",item.pose_correlation.process_age==0 and item.pose_correlation.physics_age==0 and (item.pose_correlation.post_draw_age==0 if preflight else item.pose_correlation.post_draw_age==1))
	return true

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg=="--preflight": preflight=true
		elif arg=="--case=scene-anchors": pass
		else: finish("Unknown argument: "+arg);return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"): finish("X11Forward+ required");return
	var selection: Variant=JSON.parse_string(FileAccess.get_file_as_string(SELECTION))
	branch=selection.branch
	source_start=hashes()
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
	if not preflight: root.show()
	if change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))!=OK: finish("Main failed");return
	if not await wait_scene("res://scenes/courtyard.tscn"): finish("Title failed");return
	await frames(SETTLE_FRAMES)
	var court: Node3D=current_scene
	court.main_panel.primary_button.grab_focus();await key(KEY_ENTER)
	if not await wait_scene("res://scenes/confluence_world.tscn"): finish("World failed");return
	await frames(SETTLE_FRAMES)
	var scene: Node3D=current_scene
	check("full live world and hero",scene.world_ready and scene.player.model_ready and scene.player.active and not paused and not scene.overview)
	scene.player.rama_motion.modification_processed.connect(observe_final_pose);final_observer_connected=true
	review_camera=Camera3D.new();review_camera.name="ReviewLandmarkCamera"
	review_camera.fov=50.;review_camera.near=.1;review_camera.far=400.
	scene.world.add_child(review_camera)
	review_camera.global_position=Vector3(37,22,-51);review_camera.look_at(Vector3(37,5.5,-88),Vector3.UP)
	review_camera.make_current();await frames(SETTLE_FRAMES)
	var relics: Node3D=scene.world.find_child("TraversalRelics",true,false)
	check("full traversal relic root",relics!=null)
	var families: Dictionary={};var projected: Array=[];var ids: Dictionary={}
	for node in relics.find_children("*","MeshInstance3D",true,false):
		var cls: String=node.mesh.get_class()
		if not families.has(cls): families[cls]=0
		families[cls]+=1;ids[node.mesh.get_instance_id()]=true
		if String(node.get_parent().name) in ["sun-lift-east","sun-shrine-east"] or (node is MeshInstance3D and node.mesh is TorusMesh and abs(node.global_position.x-37.)<25. and abs(node.global_position.z+88.)<20.):
			var box: AABB=node.mesh.get_aabb();var rect: Rect2;var first: bool=true;var behind: bool=false
			for i in 8:
				var p: Vector3=node.global_transform*(box.position+box.size*Vector3(float(i&1),float((i>>1)&1),float((i>>2)&1)))
				behind=behind or review_camera.is_position_behind(p)
				var v: Vector2=review_camera.unproject_position(p)
				if first: rect=Rect2(v,Vector2.ZERO);first=false
				else:rect=rect.expand(v)
			projected.append({"path":String(relics.get_path_to(node)),"family":cls,"rect":encode_value(rect),"behind":behind,"inside":root.get_visible_rect().encloses(rect) and not behind})
	check("all four primitive families",families.keys().size()==4)
	check("selected two full decks and rings project inside frame",projected.size()>40 and projected.all(func(row):return row.inside))
	production_admission={"mesh_instances":relics.find_children("*","MeshInstance3D",true,false).size(),"unique_mesh_resources":ids.size(),"families":families,"projected":projected,"scope":"Native full world; only mesh alias distribution differs; no reduction of geometry/light/materials/entities."}
	if checks.any(func(row):return not row.passed): finish("Projection/source contract failed");return
	if not take_frontage("00-landmarks-fullworld"):return
	finish("")
''' + s[b:]
s=s.replace('shots.size()==3','shots.size()==1').replace('three declared matched views','one declared matched fullworld view').replace('"case":"lane-frontage-review"','"case":"landmark-resource-parity"')
s=s.replace('Three source-bound product/contact/native-overview views. Only named block2 visible mesh and existing sole local3D collider detail are declared differences; no art/performance/authority acceptance.','One same-camera full-world landmark view; only traversal primitive sharing is the declared difference. No FPS or whole-world quality acceptance.')
(H/'capture_landmarks.gd').write_text(s)
spec=importlib.util.spec_from_file_location('snapshot',H/'snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for role in ['baseline','candidate']:
 p=W/('world-'+role+'-project');r=m.verify(p);n='tools/graphics-six/capture_scene_anchors.gd';target=p/n;target.unlink();shutil.copyfile(H/'capture_landmarks.gd',target);r['files'][n]=m.metadata(target)
 n='tools/visual-rounds/frontage-review.json';target=p/n;target.unlink();target.write_text(json.dumps({'branch':role})+'\n');r['files'][n]=m.metadata(target)
 r['common_harness_overlay']={n:r['files'][n] for n in ['tools/graphics-six/capture_scene_anchors.gd','tools/visual-rounds/frontage-review.json']}
 (p/m.MARKER).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');m.verify(p)
print('world helper staged both branches')
