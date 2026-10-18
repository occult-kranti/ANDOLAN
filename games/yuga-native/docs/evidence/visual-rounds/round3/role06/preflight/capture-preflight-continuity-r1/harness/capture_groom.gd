extends "res://tools/visual-rounds/capture.gd"
## R3: source-pinned actual input, imported geometry and full raw framebuffers.
var contract: Dictionary
var geometry: Array[Dictionary] = []
var bounds_records: Array = []
var last_pose_signal := -1
var posed_globals: Array[Transform3D] = []
var pose_signal_count := 0
var preflight := false

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--mode="): mode = arg.trim_prefix("--mode=")
		elif arg.begins_with("--context="): context = arg.trim_prefix("--context=")
		elif arg == "--preflight": preflight = true
		else: finish("Unknown argument "+arg); return
	if not mode in ["groom-stills","groom-continuity","groom-probe"]: finish("Unknown groom mode"); return
	expected = 8 if mode == "groom-stills" else 150 if mode == "groom-continuity" else 1
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus"): finish("X11 Forward+ required"); return
	contract = JSON.parse_string(FileAccess.get_file_as_string("res://tools/visual-rounds/groom_contract.json"))
	seed(741031)
	root.size = SIZE; root.content_scale_size = SIZE; root.msaa_3d = Viewport.MSAA_2X
	if not preflight: root.show()
	sources = source_hashes()
	scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await draw(6)
	player = scene.player
	if not player.model_ready or not scene.environment_ready: finish("Actual hero/world missing"); return
	review_camera = Camera3D.new(); scene.add_child(review_camera)
	review_camera.near = .05; review_camera.far = 180.0
	player.rama_motion.modification_processed.connect(observe_final_pose)
	scene.start_training(); scene.title_light.hide()
	await draw(8)
	paused = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	scene.ui.hide(); freeze_background_time(); set_light(false)
	cache_geometry()
	if mode == "groom-continuity": await groom_continuity()
	else: await groom_stills()
	if not done: finish("")

func observe_final_pose() -> void:
	# SkeletonModifier3D restores public bone poses after processing. Snapshot in
	# the modifier's completed callback while its actual final transforms exist.
	posed_globals.clear()
	var rig: Skeleton3D = player.rama_motion.rig
	for bone in rig.get_bone_count(): posed_globals.append(rig.get_bone_global_pose(bone))
	last_pose_signal = Engine.get_physics_frames()
	pose_signal_count += 1

func cache_geometry() -> void:
	geometry.clear()
	var rig: Skeleton3D = player.rama_motion.rig
	for node in player.visual.find_children("*","MeshInstance3D",true,false):
		if not node.mesh: continue
		var binds: Array = []
		if node.skin:
			for bind in node.skin.get_bind_count():
				var bone: int = rig.find_bone(String(node.skin.get_bind_name(bind)))
				if bone < 0: bone = node.skin.get_bind_bone(bind)
				binds.append({"bone":bone,"inverse":node.skin.get_bind_pose(bind)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array = node.mesh.surface_get_arrays(surface)
			if arrays.is_empty(): continue
			var material: Material = node.get_active_material(surface)
			geometry.append({"node":node,"surface":surface,"material":material,"name":material.resource_name if material else "","vertices":arrays[Mesh.ARRAY_VERTEX],"bones":arrays[Mesh.ARRAY_BONES],"weights":arrays[Mesh.ARRAY_WEIGHTS],"colors":arrays[Mesh.ARRAY_COLOR],"binds":binds,"shapes":node.mesh.surface_get_blend_shape_arrays(surface),"shape_mode":node.mesh.blend_shape_mode})

func imported_bounds(camera: Camera3D, required: String) -> Dictionary:
	var low := Vector2(INF,INF); var high := Vector2(-INF,-INF)
	var head_low := low; var head_high := high
	var count := 0; var head_count := 0; var behind := 0
	var rig: Skeleton3D = player.rama_motion.rig
	if posed_globals.size() != rig.get_bone_count(): return {"passed":false,"failure":"No completed SkeletonModifier3D pose snapshot"}
	for part in geometry:
		var node: MeshInstance3D = part.node
		if not is_instance_valid(node) or not node.is_visible_in_tree(): continue
		var vertices: PackedVector3Array = part.vertices
		var slots: int = part.bones.size()/vertices.size() if part.bones != null and not part.binds.is_empty() else 0
		var transforms: Array[Transform3D] = []
		for bind in part.binds: transforms.append(posed_globals[bind.bone] * bind.inverse)
		var secondary := Vector3.ZERO
		if part.material is ShaderMaterial:
			var value: Variant = part.material.get_shader_parameter("secondary_offset")
			if value is Vector3: secondary = value
		for index in vertices.size():
			var rest: Vector3 = vertices[index]
			var is_head: bool = "Swept black hair" in part.name or "RamaFace" in String(node.name) or ("Rama warm skin" in part.name and rest.y>=1.50 and absf(rest.x)<=.18) or "Natural lips" in part.name
			if required == "head" and not is_head: continue
			var point := rest
			for shape in part.shapes.size():
				var delta: Vector3 = part.shapes[shape][Mesh.ARRAY_VERTEX][index]
				if part.shape_mode == Mesh.BLEND_SHAPE_MODE_NORMALIZED: delta -= rest
				point += delta * node.get_blend_shape_value(shape)
			var posed := point
			if slots>0:
				posed = Vector3.ZERO
				for slot in slots: posed += (transforms[part.bones[index*slots+slot]] * point) * part.weights[index*slots+slot]
			var mask: float = clampf(part.colors[index].a,0,1) if part.colors != null else 0.0
			posed += secondary * mask * mask
			var world: Vector3 = (rig.global_transform if slots>0 else node.global_transform) * posed
			var screen: Vector2 = camera.unproject_position(world)
			low = low.min(screen); high = high.max(screen); count += 1
			if is_head: head_low = head_low.min(screen); head_high = head_high.max(screen); head_count += 1
			if camera.is_position_behind(world): behind += 1
	return {"passed":count>10000 and behind==0 and low.x>=24 and low.y>=24 and high.x<=SIZE.x-24 and high.y<=SIZE.y-24,"required":required,"min":normal(low),"max":normal(high),"head_min":normal(head_low),"head_max":normal(head_high),"vertices":count,"head_vertices":head_count,"behind":behind,"margin_pixels":24,"pose_signal_count":pose_signal_count,"pose_signal_physics_frame":last_pose_signal,"scope":"Actual imported visible mesh vertices, final modifier pose snapshot, inverse binds, live morphs and actual alpha-squared shader offsets. Projection does not prove visibility or collision clearance."}

func groom_stills() -> void:
	var fixtures: Array = contract.stills if mode == "groom-stills" else [contract.stills[2]]
	for fixture in fixtures:
		paused = true
		player.velocity = Vector3.ZERO
		player._reset_quality_motion("R3 paused station teleport")
		if fixture.id == "ordinary-gameplay-day":
			player.global_transform = from_transform(fixture.player_transform)
			player.visual.rotation.y = fixture.visual_yaw_radians
			review_camera.global_transform = from_transform(fixture.camera.transform)
			review_camera.fov = fixture.camera.fov; review_camera.near = fixture.camera.near
		else:
			player.global_position = Vector3(fixture.player_position_m[0],fixture.player_position_m[1],fixture.player_position_m[2])
			player.visual.rotation.y = deg_to_rad(fixture.visual_yaw_degrees)
			review_camera.global_position = Vector3(fixture.camera_position_m[0],fixture.camera_position_m[1],fixture.camera_position_m[2])
			review_camera.look_at(Vector3(fixture.look_at_m[0],fixture.look_at_m[1],fixture.look_at_m[2]))
			review_camera.fov = fixture.fov_degrees; review_camera.near = fixture.near_m
		player.reset_physics_interpolation(); player.visual.reset_physics_interpolation()
		scene.ui.visible = fixture.get("ui_visible",false)
		set_light(fixture.night)
		review_camera.make_current(); review_camera.reset_physics_interpolation()
		player.rama_lod.reset("R3 station"); player.rama_lod.update(review_camera,1.0/30.0)
		await draw(4)
		groom_frame(fixture.id,fixture.required_bounds)
		if done: return

func from_transform(value: Array) -> Transform3D:
	return Transform3D(Basis(Vector3(value[0][0],value[0][1],value[0][2]),Vector3(value[1][0],value[1][1],value[1][2]),Vector3(value[2][0],value[2][1],value[2][2])),Vector3(value[3][0],value[3][1],value[3][2]))

func follow_camera() -> void:
	if done or not is_instance_valid(player): return
	review_camera.global_position = player.global_position + Vector3(-3,2.2,-4)
	review_camera.look_at(player.global_position + Vector3(0,1,0))
	review_camera.fov = 50.0
	review_camera.reset_physics_interpolation()

func groom_continuity() -> void:
	for action in ["move_left","move_right","fire"]:
		if not InputMap.has_action(action): finish("Missing actual input "+action); return
		Input.action_release(action)
	scene.reset_training(); scene.start_training(); scene.ui.hide(); scene.title_light.hide()
	player.visual.rotation.y = PI
	player.reset_physics_interpolation(); player.visual.reset_physics_interpolation()
	set_light(false); follow_camera(); review_camera.make_current()
	scene.rama_runtime.combat_event.connect(record_event)
	if not preflight: RenderingServer.frame_pre_draw.connect(follow_camera)
	paused = false
	sequence_controls.append({"frame":0,"kind":"reset_origin","secondary":normal(player.rama_secondary.report())})
	for index in 150:
		if index in [15,66]:
			var action: String = "move_left" if index==15 else "move_right"
			Input.action_press(action); sequence_controls.append({"frame":index,"kind":"press","action":action})
		if index in [30,78]:
			var action: String = "move_left" if index==30 else "move_right"
			Input.action_release(action); sequence_controls.append({"frame":index,"kind":"release_input","action":action})
		if index in [45,90]:
			var ability: String = "kodanda" if index==45 else "measured_step"
			var result: Dictionary = scene.rama_runtime.cast_ability(ability)
			sequence_controls.append({"frame":index,"kind":"cast","ability":ability,"result":normal(result)})
			if not result.get("accepted",false): finish("Actual cast denied "+ability); return
		if index == 120:
			scene.reset_training(); scene.ui.hide(); scene.title_light.hide()
			sequence_controls.append({"frame":index,"kind":"actual_reset","secondary":normal(player.rama_secondary.report())})
		# Physics update supplies movement/secondary; camera translation follows in
		# frame_pre_draw so the rendered camera and stored matrix are identical.
		await draw(1)
		groom_frame("frame-%03d"%index,"fullbody")
		if done: return
	for action in ["move_left","move_right","fire"]: Input.action_release(action)
	paused = true

func groom_frame(id: String, required: String) -> void:
	if preflight and mode == "groom-continuity" and int(id.trim_prefix("frame-")) not in [0,15,30,45,50,66,78,90,94,110,120,149]:
		shots.append({"id":id,"bounds_sampled":false,"motion":normal(player.rama_motion.diagnostics()),"secondary":normal(player.rama_secondary.report())})
		return
	var bounds := imported_bounds(review_camera,required)
	bounds_records.append({"id":id,"bounds":bounds})
	if not bounds.passed: finish("Imported groom/cloth framing failed "+id+": "+str(bounds)); return
	if preflight:
		shots.append({"id":id,"bounds":bounds,"player_transform":normal(player.global_transform),"camera":normal(review_camera.global_transform),"motion":normal(player.rama_motion.diagnostics()),"secondary":normal(player.rama_secondary.report())})
	else:
		super.write_frame(id,review_camera,"R3 actual imported groom/cloth and runtime inputs; final modifier pose observation")
		if done: return
		shots[-1]["bounds"] = bounds
		shots[-1]["secondary"] = normal(player.rama_secondary.report())
		shots[-1]["rendered_pose_globals"] = normal(posed_globals)
		shots[-1]["rendered_pose_pin"] = JSON.stringify(normal(posed_globals),"",true,true).sha256_text()
		shots[-1]["body_velocity"] = normal(player.velocity)
		shots[-1]["woven_materials"] = woven_state()

func woven_state() -> Array:
	var result := []
	for part in geometry:
		if not ("Cobalt handwoven silk" in part.name or "Cobalt lotus brocade" in part.name): continue
		var material: ShaderMaterial = part.material
		var texture: Texture2D = material.get_shader_parameter("rough_texture")
		var data: Image = texture.get_image()
		result.append({"node":String(part.node.name),"surface":part.surface,"visible":part.node.is_visible_in_tree(),"material":part.name,"texture":texture.resource_path,"size":[texture.get_width(),texture.get_height()],"mipmaps":data.get_mipmap_count(),"rough_channel":normal(material.get_shader_parameter("rough_channel")),"roughness_value":material.get_shader_parameter("roughness_value"),"specular_value":material.get_shader_parameter("specular_value")})
	return result

func source_hashes() -> Dictionary:
	var result := super.source_hashes()
	for name in ["capture_groom.gd","groom_contract.json"]: result["res://tools/visual-rounds/"+name] = FileAccess.get_sha256("res://tools/visual-rounds/"+name)
	return result

func draw(count: int) -> void:
	for index in count:
		if preflight:
			for tick in 2: await physics_frame
			if mode == "groom-continuity" and is_instance_valid(player): follow_camera()
		else:
			await process_frame
			await RenderingServer.frame_post_draw

func finish(failure: String) -> void:
	if not preflight:
		super.finish(failure)
		return
	if done: return
	done = true
	var report := {"complete":failure.is_empty() and shots.size()==expected,"failure":failure,"shots":shots,"expected":expected,"events":events,"controls":sequence_controls,"source_sha256":sources,"scope":"Headless real-input and final-modifier-pose projection preflight. No framebuffer or rendered art claim."}
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("preflight.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("GROOM_PREFLIGHT ",report.complete," ",failure)
	paused = false
	if is_instance_valid(scene): scene.queue_free()
	for index in 3: await process_frame
	quit(0 if report.complete else 1)

