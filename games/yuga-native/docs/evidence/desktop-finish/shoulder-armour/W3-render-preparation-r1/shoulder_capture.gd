extends "res://tools/visual-rounds/capture_groom.gd"
## Review-only original shoulder replacement. Source mesh supplies geometry; no runtime writer.
## Both branches use this exact helper; admission differs only in three GLBs.
const SOURCE_PINS := {
  "baseline": [
    "db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e",
    "b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005",
    "aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a"
  ],
  "candidate": [
    "8755b65b1b103b3d3210993240c9e18c196510757e1b031bb684eb45e47b629b",
    "8ae53f22a9536d7dcf3d9506906ac83e15222d0b9eadacd51cff82c7d7b43371",
    "5b382f97b64658784d15fbb6ef816af22c62d8148717b70c797dea8e2172be37"
  ]
}
const RAW_PATHS := ["res://assets/heroes/rama-hero.glb", "res://assets/heroes/rama-hero-mid.glb", "res://assets/heroes/rama-hero-far.glb"]
const REQUIRED_MOTION := "5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5"
const REQUIRED_FINISH := "6eb51ce8f34a3d5a33deb142ca92aaa20505516b0ee8fff3ca445bcab603078a"
const SHOULDER_SELECTION := {
  "baseline": {"bone":50,"materials":{"Worked warm gold":5896,"Recessed antique gold":2498,"Polished sapphire":722}},
  "candidate": {"bone":49,"materials":{"Worked warm gold":3146,"Cobalt handwoven silk":850,"Recessed antique gold":152}}
}
var branch := ""

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg.begins_with("--mode="): mode=arg.trim_prefix("--mode=")
		elif arg=="--preflight": preflight=true
		else: finish("Unknown argument "+arg); return
	expected=4
	if mode!="groom-stills": finish("Use --mode=groom-stills"); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	branch=OS.get_environment("YUGA_SHOULDER_REVIEW")
	if not SOURCE_PINS.has(branch): finish("Explicit YUGA_SHOULDER_REVIEW=baseline/candidate required"); return
	for index in RAW_PATHS.size():
		if FileAccess.get_sha256(RAW_PATHS[index])!=SOURCE_PINS[branch][index]: finish("Unexpected raw hero "+RAW_PATHS[index]); return
	if FileAccess.get_sha256("res://scripts/rama_motion.gd")!=REQUIRED_MOTION or FileAccess.get_sha256("res://scripts/rama_surface_finish.gd")!=REQUIRED_FINISH:
		finish("Motion/finish source differs from reviewed component inputs"); return
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):
		finish("X11 Forward+ required"); return
	seed(741031); root.size=SIZE; root.content_scale_size=SIZE; root.msaa_3d=Viewport.MSAA_2X
	if not preflight: root.show()
	sources=source_hashes()
	contract={"stills":[
		{"id":"rest-front","player_position_m":[19,.4400999976158142,-15],"visual_yaw_degrees":-90,"camera_position_m":[17.2,1.9400999976158142,-15],"look_at_m":[19,1.9400999976158142,-15],"fov_degrees":38,"near_m":.05,"night":false,"required_bounds":"shoulder"},
		{"id":"rest-profile","player_position_m":[19,.4400999976158142,-1],"visual_yaw_degrees":180,"camera_position_m":[17.2,1.9400999976158142,-1],"look_at_m":[19,1.9400999976158142,-1],"fov_degrees":38,"near_m":.05,"night":false,"required_bounds":"shoulder"},
		{"id":"rest-rear","player_position_m":[19,.4400999976158142,-1],"visual_yaw_degrees":90,"camera_position_m":[17.2,1.9400999976158142,-1],"look_at_m":[19,1.9400999976158142,-1],"fov_degrees":38,"near_m":.05,"night":false,"required_bounds":"shoulder"}]}
	scene=load("res://scenes/courtyard.tscn").instantiate(); root.add_child(scene); current_scene=scene
	await draw(6); player=scene.player
	if not player.model_ready or not scene.environment_ready: finish("Actual hero/world missing"); return
	for forbidden in ["FourTaperedTempleWisps","SevenSweptUpperHairLayers","OptionalArrowFletching","ReviewOnlyLeftShoulderArmour"]:
		if player.visual.find_child(forbidden,true,false)!=null: finish("Unreviewed optional helper present: "+forbidden); return
	review_camera=Camera3D.new(); scene.add_child(review_camera); review_camera.near=.05; review_camera.far=180
	player.rama_motion.modification_processed.connect(observe_final_pose)
	scene.start_training(); scene.title_light.hide(); await draw(8)
	paused=true; Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	scene.ui.hide(); freeze_background_time(); set_light(false); cache_geometry()
	sequence_controls.append({"kind":"shoulder_source_comparison","branch":branch,"default_activation":false,"replacement_geometry":true,"optional_helpers":false,"rest_contract":contract})
	await groom_stills()
	if not done: await actual_cast_view()
	if not done: finish("")

func actual_cast_view() -> void:
	paused=false
	scene.reset_training(); scene.start_training(); scene.ui.hide(); scene.title_light.hide()
	for action in ["move_left","move_right","move_forward","move_back","fire"]: Input.action_release(action)
	player.global_position=Vector3(-.65,.0001,0); player.velocity=Vector3.ZERO
	player.yaw=0; player.pitch=0; player._update_camera(); player.visual.rotation.y=PI
	player.reset_physics_interpolation(); player.visual.reset_physics_interpolation()
	set_light(false); player.camera.make_current(); await draw(8)
	if not player.is_on_floor(): finish("Actor lacks actual floor contact"); return
	var origin: Vector3=player.camera.project_ray_origin(Vector2(SIZE)*.5)
	var direction: Vector3=player.camera.project_ray_normal(Vector2(SIZE)*.5)
	var hit: Dictionary=scene.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(origin,origin+direction*80,1|4,[player.get_rid()]))
	if hit.is_empty() or String(hit.collider.name)!="Target03": finish("Actual player aim misses Target03"); return
	scene.rama_runtime.combat_event.connect(record_event)
	var cast: Dictionary=scene.rama_runtime.cast_ability("piercing_dawn")
	if not cast.get("accepted",false): finish("Actual Piercing Dawn refused"); return
	var begin_time: float=scene.rama_runtime.kit.elapsed
	var age:=0.0; var frames:=0
	while age+.000001<.30 and frames<30:
		await draw(1); frames+=1; age=scene.rama_runtime.kit.elapsed-begin_time
	paused=true
	if age>.325 or player.rama_motion.action_stage!="windup" or not player.rama_motion.nocked_arrow.visible:
		finish("Required live nocked windup missing"); return
	var rig: Skeleton3D=player.rama_motion.rig
	var shoulder: int=rig.find_bone("shoulder01.L")
	if shoulder!=49 or posed_globals.size()!=164: finish("Final imported shoulder pose missing"); return
	var center: Vector3=rig.global_transform*posed_globals[shoulder].origin
	var offset:=Basis(Vector3.UP,player.visual.global_rotation.y-PI)*Vector3(-1.20,.12,-1.275)
	review_camera.global_position=center+offset; review_camera.look_at(center); review_camera.fov=38
	review_camera.make_current(); review_camera.reset_physics_interpolation()
	player.rama_lod.reset("Original shoulder replacement cast review"); player.rama_lod.update(review_camera,1.0/30)
	await draw(4)
	sequence_controls.append({"kind":"real_public_cast","cast":normal(cast),"authority_age_s":age,"advanced_render_frames":frames,"aim_hit":normal(hit.position),"collider":String(hit.collider.name),"captured_motion_stage":player.rama_motion.action_stage})
	groom_frame("cast-three-quarter","shoulder")

func groom_frame(id: String, required: String) -> void:
	super.groom_frame(id,required)
	if done: return
	shots[-1]["shoulder_branch"]=branch
	shots[-1]["rendered_pose_globals"]=normal(posed_globals)
	shots[-1]["rendered_pose_pin"]=JSON.stringify(normal(posed_globals),"",true,true).sha256_text()
	shots[-1]["scope"]="Original shoulder replacement comparison. Rest is staged; cast uses the actual public ability and final modifier pose. Exact rigid-joint/material selection proves framing only, not visibility, collision, physical attachment or general motion acceptance."

func source_hashes() -> Dictionary:
	var result:=super.source_hashes()
	result.erase("res://tools/visual-rounds/groom_contract.json")
	var helper_path: String=get_script().resource_path
	result[helper_path]=FileAccess.get_sha256(helper_path)
	return result

func imported_bounds(camera: Camera3D, required: String) -> Dictionary:
	var low := Vector2(INF,INF); var high := Vector2(-INF,-INF)
	var count := 0; var behind := 0; var observed := {}
	var selection: Dictionary = SHOULDER_SELECTION[branch]
	var rig: Skeleton3D = player.rama_motion.rig
	if posed_globals.size()!=164 or rig.get_bone_name(int(selection.bone))!=("upperarm01.L" if branch=="baseline" else "shoulder01.L"):
		return {"passed":false,"failure":"Exact final shoulder bone mapping missing"}
	for part in geometry:
		var node: MeshInstance3D = part.node
		if not is_instance_valid(node) or not node.is_visible_in_tree() or node.name!="RamaHero": continue
		var material_name := ""
		for admitted: String in selection.materials:
			if admitted in part.name: material_name=admitted
		if material_name.is_empty(): continue
		var vertices: PackedVector3Array = part.vertices
		var slots: int = part.bones.size()/vertices.size() if part.bones!=null and not part.binds.is_empty() else 0
		if slots==0: return {"passed":false,"failure":"Selected material is not skinned"}
		var transforms: Array[Transform3D] = []
		for bind in part.binds: transforms.append(posed_globals[bind.bone]*bind.inverse)
		var secondary := Vector3.ZERO
		if part.material is ShaderMaterial:
			var value: Variant = part.material.get_shader_parameter("secondary_offset")
			if value is Vector3: secondary=value
		for index in vertices.size():
			var selected_weight := 0.0
			for slot in slots:
				if part.binds[part.bones[index*slots+slot]].bone==int(selection.bone): selected_weight+=part.weights[index*slots+slot]
			if selected_weight<.9999: continue
			var rest: Vector3 = vertices[index]
			var point := rest
			for shape in part.shapes.size():
				var delta: Vector3 = part.shapes[shape][Mesh.ARRAY_VERTEX][index]
				if part.shape_mode==Mesh.BLEND_SHAPE_MODE_NORMALIZED: delta-=rest
				point+=delta*node.get_blend_shape_value(shape)
			var posed := Vector3.ZERO
			for slot in slots: posed+=(transforms[part.bones[index*slots+slot]]*point)*part.weights[index*slots+slot]
			var mask: float = clampf(part.colors[index].a,0,1) if part.colors!=null else 0.0
			posed+=secondary*mask*mask
			var world: Vector3=rig.global_transform*posed
			var screen: Vector2=camera.unproject_position(world)
			low=low.min(screen); high=high.max(screen); count+=1
			observed[material_name]=int(observed.get(material_name,0))+1
			if camera.is_position_behind(world): behind+=1
	var selection_passed: bool = observed==selection.materials
	return {"passed":selection_passed and behind==0 and low.x>=24 and low.y>=24 and high.x<=SIZE.x-24 and high.y<=SIZE.y-24,"required":required,"min":normal(low) if count>0 else null,"max":normal(high) if count>0 else null,"vertices":count,"selected_material_vertices":observed,"expected_material_vertices":selection.materials,"selection_passed":selection_passed,"behind":behind,"margin_pixels":24,"pose_signal_count":pose_signal_count,"pose_signal_physics_frame":last_pose_signal,"scope":"Exact source-proven rigid-joint/material membership at near LOD, final modifier pose, inverse binds, live morphs and alpha-squared offsets. Projection does not prove visibility or contact. Baseline selects only superseded rigid50 cap; candidate selects only new rigid49 sculpture."}


func finish(failure: String) -> void:
	if done: return
	done = true
	var after := source_hashes() if not sources.is_empty() else {}
	var report: Dictionary
	if preflight:
		report = {"complete":failure.is_empty() and shots.size()==expected and sources==after,"failure":failure,"shots":shots,"expected":expected,"events":events,"controls":sequence_controls,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"scope":"Headless real-input and final-modifier-pose projection preflight. No framebuffer or rendered art claim."}
	else:
		report = {"schema":1,"kind":"actual-native-visual-rounds","camera_contract":"shoulder-front-profile-rear-cast-v1","mode":mode,"context":context,"complete":failure.is_empty() and sources==after and shots.size()==expected,"failure":failure,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"shots":shots,"ability_events":events,"sequence_controls":sequence_controls,"expected_raw_pngs":expected,"time_controls":time_controls,"clocks":{"fixed_capture_process_hz":30,"physics_hz":Engine.physics_ticks_per_second,"army_authority_hz":20,"hardware_fps_measured":false},"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"Original Forward+ matched front/profile/rear and actual public cast framebuffers. Fixed30Hz capture is simulation sampling, not hardware FPS. No full gameplay/continuous motion acceptance."}
	# After the last observation only. Dummy audio releases on its real mixer,
	# so a few fast headless process frames do not establish completed cleanup.
	paused = false
	if is_instance_valid(scene):
		for node in scene.find_children("*", "AudioStreamPlayer", true, false): node.stop(); node.stream = null
		scene.queue_free()
	for unused in 8: await process_frame
	var cleanup_started := Time.get_ticks_usec()
	var previous := AudioServer.get_time_since_last_mix()
	var observed := 0
	var samples: Array[Dictionary] = []
	while observed < 2 and Time.get_ticks_usec()-cleanup_started < 250000:
		OS.delay_msec(1)
		var now := AudioServer.get_time_since_last_mix()
		if now+.0002 < previous: observed += 1
		samples.append({"wall_usec":Time.get_ticks_usec()-cleanup_started,"since_mix_s":now,"ticks":observed})
		previous = now
	var wait_usec := Time.get_ticks_usec()-cleanup_started
	for unused in 8: await process_frame
	report.audio_cleanup = {"scope":"Capture shutdown after all shots and scene free; no runtime audio change.","observed_mixer_ticks":observed,"wait_usec":wait_usec,"budget_usec":250000,"samples":samples,"main_cleanup_frames":8}
	report.complete = report.complete and observed == 2 and wait_usec <= 250000
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("SHOULDER_CAPTURE_COMPLETE ",report.complete," ",failure)
	quit(0 if report.complete else 1)
