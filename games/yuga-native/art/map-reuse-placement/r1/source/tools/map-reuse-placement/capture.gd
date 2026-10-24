extends "res://tools/wind-court-pilot/capture_pilot.gd"
## Uses existing full-world hold/hash/capture machinery; new composition stays isolated.
const Placement=preload("res://tools/map-reuse-placement/placement.gd")
const Unit=preload("res://scripts/lane_minion.gd")
var selection_path:=""
var placement_result:Dictionary={}
var original_body_ids:Array=[]
var ordinary_camera:Transform3D
var route_frames:Array=[]
var context_checks:Array[Dictionary]=[]
var actual_capsule:CapsuleShape3D
func hashes()->Dictionary:
	var result:=super.hashes()
	for path in ["res://tools/map-reuse-placement/placement.gd","res://tools/map-reuse-placement/capture.gd","res://tools/map-reuse-placement/prepare.py","res://tools/map-reuse-intake/map_loader.gd","res://assets/environment/lanka_courtyard.glb","res://assets/environment/lanka_courtyard.metadata.json","res://scripts/player.gd","res://scripts/lane_army.gd","res://scripts/lane_minion.gd"]:
		result[path]=FileAccess.get_sha256(path)
	if not selection_path.is_empty():result[selection_path]=FileAccess.get_sha256(selection_path)
	return result
func views()->Array[Dictionary]:
	return [{"id":"ordinary-day","phase":0.0,"ordinary":true},{"id":"ordinary-night","phase":1.0,"ordinary":true},{"id":"approach-day","phase":0.0,"at":Vector3(-43,3,-79),"target":Vector3(-40,6,-54)},{"id":"rear-day","phase":0.0,"at":Vector3(-38,2.2,-37),"target":Vector3(-40,5,-54)}]
func gather_bodies(node:Node,result:Array)->void:
	if node is StaticBody3D:result.append(node.get_instance_id())
	for child in node.get_children():gather_bodies(child,result)
func capsule_hits(space:PhysicsDirectSpaceState3D,x:float,z:float,radius:float)->Array[Dictionary]:
	var shape:CapsuleShape3D=actual_capsule.duplicate() if actual_capsule!=null and is_equal_approx(radius,actual_capsule.radius) else CapsuleShape3D.new();shape.radius=radius;shape.height=maxf(1.8,radius*2)
	var q:=PhysicsShapeQueryParameters3D.new();q.shape=shape;q.transform=Transform3D(Basis.IDENTITY,Vector3(x,shape.height*.5+.04,z));q.collision_mask=1
	return space.intersect_shape(q,16)
func context_probe()->void:
	var space:PhysicsDirectSpaceState3D=scene.world.get_world_3d().direct_space_state
	for child in scene.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:actual_capsule=child.shape
	check("actual Confluence capsule is0.65radius1.8height",actual_capsule!=null and is_equal_approx(actual_capsule.radius,.65) and is_equal_approx(actual_capsule.height,1.8))
	var blocked:Array=[];var samples:=0
	for radius in [.29,.65]:
		for x in [-44.0,-43.0,-40.0,-37.0,-36.0]:
			for step in 73:
				var z:float=-72+step*.5;samples+=1
				if not capsule_hits(space,x,z,radius).is_empty():blocked.append([radius,x,z])
	check("actual full-world0.65m capsule and base-player0.29m comparison keep eight metre lane clear",blocked.is_empty(),{"samples":samples,"blocked":blocked})
	var army_failed:Array=[];var army_samples:=0
	# Test existing role radii against real static triangle world, not only army's flat boxes.
	for role in Unit.STATS:
		var radius:float=Unit.STATS[role].radius
		for x in [-42.2,-40.0,-37.8]:
			for step in 41:
				var z:float=-64+step*.5;army_samples+=1
				if not capsule_hits(space,x,z,radius).is_empty():army_failed.append([role,radius,x,z])
	check("all real army role radii and offset ranks clear new section",army_failed.is_empty(),{"samples":army_samples,"blocked":army_failed})
	var los:Dictionary=space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(-40,1.6,-70),Vector3(-40,1.6,-38),1))
	check("actual full-world eye LOS keeps opening clear",los.is_empty())
	var ids:Array=[];gather_bodies(scene.world,ids);var expected:=original_body_ids.duplicate();expected.append(placement_result.body.get_instance_id())
	ids.sort();expected.sort();check("only one source collider added, all previous bodies retain identity",ids==expected,{"before":original_body_ids.size(),"after":ids.size()})
	var stale:=StaticBody3D.new();var holder:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(26,11,10);holder.shape=box;stale.position=Vector3(-40,5.5,-54);stale.add_child(holder);scene.world.add_child(stale)
	await physics_frame;await physics_frame
	check("full-world injected duplicate broad box is detected",not capsule_hits(space,-40,-54,.65).is_empty())
	stale.free();await physics_frame;await physics_frame
	check("full-world original route restored after stale blocker removal",capsule_hits(space,-40,-54,.65).is_empty())
func install_candidate()->void:
	var selection:Variant=JSON.parse_string(FileAccess.get_file_as_string(selection_path))
	if not selection is Dictionary:check("selection JSON dictionary",false);return
	placement_result=Placement.build("res://assets/environment/lanka_courtyard.glb",selection)
	check("actual pinned modular composition loads",placement_result.get("ok",false),placement_result.get("reason"))
	if not placement_result.ok:return
	candidate=placement_result.root;scene.world.add_child(candidate)
	await physics_frame;await physics_frame
	await context_probe()
func capture(kind:String,view:Dictionary)->void:
	if view.get("ordinary",false):
		var copy:=view.duplicate();copy.erase("ordinary");copy.at=ordinary_camera.origin;copy.target=ordinary_camera.origin-ordinary_camera.basis.z
		await super.capture(kind,copy)
	else:await super.capture(kind,view)
func short_route()->void:
	scene.set_review_phase(0);scene.player.global_position=Vector3(-40,.04,-64);scene.player.yaw=PI;scene.player.pitch=-.10;scene.player._update_camera();scene.player.velocity=Vector3(0,0,8)
	scene.player.visual.rotation.y=0;scene.player.camera.current=true
	await physics_frame;await physics_frame
	var expected_army:String=held.army_transform_sha256;var collisions:Array=[];var poses:Array=[]
	for index in 72:
		if index>0:
			var hit:KinematicCollision3D=scene.player.move_and_collide(Vector3(0,0,8.0/30))
			if hit!=null:collisions.append({"frame":index,"collider":str(hit.get_collider().get_path()),"normal":vector(hit.get_normal())})
		scene.player._update_rama_motion(1.0/30)
		scene.player.rama_motion.evaluate_pose()
		await physics_frame;await draw_frames(1)
		var state:=freeze_state();poses.append(state.hero_pose_sha256)
		var row:={"frame":index,"feet":vector(scene.player.global_position),"camera":transform(scene.player.camera.global_transform),"hero_pose_sha256":state.hero_pose_sha256,"army_unchanged":state.army_transform_sha256==expected_army,"motion_finite":scene.player.rama_motion.diagnostics().finite}
		if not preflight:
			var image:=root.get_texture().get_image();var name:="route-%03d.png"%index
			row.file=name;row.saved=image.save_png(output.path_join(name))==OK;row.sha256=FileAccess.get_sha256(output.path_join(name));row.drawn_frame=Engine.get_frames_drawn()
		route_frames.append(row)
	check("actual CharacterBody collision sweeps traverse the real gate",collisions.is_empty() and scene.player.global_position.z> -45.2,{"collisions":collisions,"final_feet":vector(scene.player.global_position)})
	check("all72 route frames retain finite actual hero motion and held army",route_frames.size()==72 and route_frames.all(func(row):return row.motion_finite and row.army_unchanged))
	check("route actually advances existing skeletal animation",poses.any(func(value):return value!=poses[0]))
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg.begins_with("--selection="):selection_path=arg.trim_prefix("--selection=")
		elif arg=="--preflight":preflight=true
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output) or not FileAccess.file_exists(selection_path):push_error("Fresh output and existing reviewed selection required");quit(1);return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()!="forward_plus"):push_error("Actual Forward+ display required");quit(1);return
	source_hashes=hashes();root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.msaa_3d=Viewport.MSAA_2X
	if not preflight:root.show()
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene
	await draw_frames(8);check("actual canonical world and accepted Rama load",scene.world_ready and scene.player.model_ready)
	if not checks[-1].passed:await finish();return
	scene.set_overview(false);scene.set_paused(false);scene.set_review_phase(0)
	scene.set_process(false);scene.set_physics_process(false);hold_callbacks(scene.world)
	for water in scene.manifest.waters:
		var material:ShaderMaterial=scene.world.get_node(water.id).get_active_material(0);water_clock_controls.append({"id":water.id,"previous_animation_speed":material.get_shader_parameter("animation_speed")});material.set_shader_parameter("animation_speed",0.0)
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	scene.player.global_position=Vector3(-40,.04,-76);scene.player.velocity=Vector3.ZERO;scene.player.yaw=PI;scene.player.pitch=-.10;scene.player._update_camera();scene.player.visual.rotation.y=0
	await physics_frame;await physics_frame;await draw_frames(2)
	ordinary_camera=scene.player.camera.global_transform
	camera=Camera3D.new();camera.fov=65;camera.near=.08;camera.far=scene.player.camera.far;scene.add_child(camera);camera.current=true
	held=freeze_state();gather_bodies(scene.world,original_body_ids)
	for view in views():await capture("baseline",view)
	await install_candidate()
	for view in views():await capture("reused-gate",view)
	check("eight matched context states produced",shots.size()==8)
	for i in 4:check("matched camera and phase "+String(views()[i].id),shots[i].camera==shots[i+4].camera and shots[i].phase==shots[i+4].phase)
	await short_route();await finish()
func finish()->void:
	check("bounded short route completes72frames",route_frames.size()==72)
	var after:=hashes();check("all protected product, art and selection sources remain unchanged",source_hashes==after)
	var passed:=checks.all(func(row):return row.passed)
	var report:={"complete":passed,"preflight":preflight,"actual_image_count":0 if preflight else shots.size()+route_frames.size(),"shots":shots,"route_frames":route_frames,"checks":checks,"composition":placement_result.get("report",{}),"held_state":held,"hold_controls":hold_controls,"water_clock_controls":water_clock_controls,"ordinary_camera":transform(ordinary_camera),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"display":DisplayServer.get_name(),"engine":Engine.get_version_info(),"source_sha256":source_hashes,"source_after_sha256":after,"canonical_enabled":false,"scope":"Existing canonical world with isolated reuse-first CC0 gate. Four baseline/candidate matched camera/lighting pairs. Ordinary view is actual 65degree3.5m shoulder-camera pose at feet(-40,.04,-76), default pitch-.10 and northward yawPI. Actual CharacterBody3D collision sweep and existing skeletal motion advanced72frames at8m/s through section, actual spring camera follows; scene/army held. SkeletonModifier3D callback is held for matched pairs, then existing rama_motion.evaluate_pose() is called explicitly after each existing player._update_rama_motion(1/30) in route; no bone pose fabricated. This is scripted staged traversal, not human-input or multiplayer/hardware-FPS qualification."}
	FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	if is_instance_valid(scene):scene.queue_free()
	for unused in 8:await process_frame
	print("LANKA_REUSE_CAPTURE_COMPLETE ",passed);quit(0 if passed else 1)
