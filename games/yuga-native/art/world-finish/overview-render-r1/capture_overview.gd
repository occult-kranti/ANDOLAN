extends "res://tools/graphics-six/capture_compact_screens.gd"
## Three explicit matched overview views, reusing native boot/key/camera/snapshot helpers.
## Installed only as capture_scene_anchors.gd in declared isolated children.
## The declared runner copy changes only scene-anchors expected count tothree; not a
## title/training observation. No clock/pose/authority override is performed.

func transform_values(value: Transform3D) -> Array:
	return [vector(value.basis.x),vector(value.basis.y),vector(value.basis.z),vector(value.origin)]

func collision_inventory(node: Node, result: Array) -> void:
	if node is CollisionObject3D:
		var row:={"path":String(node.get_path()),"class":node.get_class(),"layer":node.collision_layer,"mask":node.collision_mask,"transform":transform_values(node.global_transform),"shapes":[]}
		for child in node.get_children():
			if child is not CollisionShape3D: continue
			var shape:Shape3D=child.shape
			var item:={"class":shape.get_class(),"disabled":child.disabled,"transform":transform_values(child.transform)}
			if shape is BoxShape3D: item.size=vector(shape.size)
			elif shape is CapsuleShape3D: item.height=shape.height;item.radius=shape.radius
			elif shape is ConcavePolygonShape3D:
				var values:Array=[]
				for point in shape.get_faces(): values.append(vector(point))
				item.faces=values.size()/3;item.faces_sha256=JSON.stringify(values).sha256_text();item.backface_collision=shape.backface_collision
			row.shapes.append(item)
		result.append(row)
	for child in node.get_children(): collision_inventory(child,result)

func snapshot(id:String) -> Dictionary:
	var state:=super.snapshot(id)
	var scene=current_scene
	state.review_scope="Actual native suspended overview at100/150/200%; the candidate intentionally changes overview camera translation and HUD composition only. Original gameplay camera, full sampled hero/army state, colliders and light must match."
	state.product_camera=camera_state(scene.player.camera)
	state.hero_skeleton={"bone_names":[],"bone_global_poses":[]}
	var rig:Skeleton3D=scene.player.rama_motion.rig
	for index in rig.get_bone_count():
		state.hero_skeleton.bone_names.append(String(rig.get_bone_name(index)))
		state.hero_skeleton.bone_global_poses.append(transform_values(rig.get_bone_global_pose(index)))
	state.army_units=[]
	for unit in scene.army.units:
		var joints:={}
		var names:Array=unit.joints.keys();names.sort()
		for name in names:
			if unit.joints[name] is Node3D: joints[name]=transform_values(unit.joints[name].transform)
		state.army_units.append({"id":unit.unit_id,"team":unit.team,"role":unit.role,"health":unit.health,"alive":unit.alive,"state":unit.state,"transform":transform_values(unit.global_transform),"joints":joints})
	var environment:Environment=scene.world_environment.environment
	state.light_state={"diagnostics":scene.lighting.diagnostics(),"exposure":environment.tonemap_exposure,"ambient":environment.ambient_light_energy,"ambient_color":str(environment.ambient_light_color),"sun_transform":transform_values(scene.sun.global_transform),"sun_energy":scene.sun.light_energy,"sun_color":str(scene.sun.light_color)}
	state.collision_objects=[]
	collision_inventory(scene.world,state.collision_objects)
	state.overview_composition={"guide":str(scene.atlas_guide.get_global_rect()),"map":str(scene.map_control.get_global_rect()),"plot":str(scene.map_control._plot_rect()),"return_hint":scene.atlas_guide_return.text,"details":scene.atlas_live_details.text,"visible_cards":[],"combat_hud_visible":scene.rama_hud.visible}
	for name in ["TitleCard","RelayStatus","ControlsCard","TraversalStatus"]:
		if scene.hud.get_node(name).is_visible_in_tree():state.overview_composition.visible_cards.append(name)
	return state

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg=="--preflight": preflight=true
		elif arg=="--case=scene-anchors": pass
		else: finish("Unknown argument: "+arg);return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"): finish("X11 Forward+ required");return
	source_start=hashes()
	if source_start.is_empty(): finish("Immutable source manifest required");return
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
	if not preflight: root.show()
	checkpoint("actual_boot_main_scene")
	if change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))!=OK: finish("Main scene failed");return
	if not await wait_scene("res://scenes/courtyard.tscn"): finish("Boot did not reach title");return
	await frames(SETTLE_FRAMES)
	var court=current_scene
	# Preserve the current ten-shot helper's settled title scale sequence, without PNGs.
	for scale in SCALES: root.content_scale_factor=scale;await frames(SETTLE_FRAMES)
	root.content_scale_factor=1.0;await frames(SETTLE_FRAMES)
	court.main_panel.primary_button.grab_focus();await key(KEY_ENTER)
	if not await wait_scene("res://scenes/confluence_world.tscn"): finish("Primary action did not reach world");return
	await frames(SETTLE_FRAMES)
	var scene=current_scene
	if not scene.world_ready or not scene.player.model_ready: finish("World/hero missing");return
	await key(KEY_F1);await frames(SETTLE_FRAMES)
	var clock:float=scene.army.elapsed
	var kit_clock:float=scene.rama_runtime.kit.elapsed
	for entry in [{"id":"00-overview-100","scale":1.0},{"id":"01-overview-150","scale":1.5},{"id":"02-overview-200","scale":2.0}]:
		root.content_scale_factor=entry.scale
		await frames(SETTLE_FRAMES)
		check("actual suspended overview "+entry.id,scene.overview and not paused and not scene.player.active and scene.rama_runtime.suspended and root.get_camera_3d()==scene.review_camera and scene.atlas_guide.visible)
		if not take(entry.id):return
	check("authority clocks held across allthreeviews",shots.all(func(item):return item.army_elapsed==clock and item.kit_elapsed==kit_clock))
	check("full sampled hero skeleton recorded",shots.all(func(item):return item.hero_skeleton.bone_names.size()==164 and item.hero_skeleton.bone_global_poses.size()==164))

	finish("")

func finish(failure:String) -> void:
	if done:return
	done=true
	var after:=hashes() if not source_start.is_empty() else {}
	check("three declared overview views",shots.size()==3)
	check("source unchanged",not source_start.is_empty() and source_start==after)
	var passed:=failure.is_empty() and checks.all(func(item):return item.passed)
	var report:={"schema":1,"case":"overview-composition-review","outer_transport_alias":"scene-anchors","complete":passed,"failure":failure,"preflight":preflight,"shots":shots,"checks":checks,"checkpoints":checkpoints,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Three source-bound genuine overview views at100/150/200%. The declared candidate changes overview-only camera translation and information-column composition. All gameplay state, original player camera, full sampled164bones and units, retained colliders, light and clocks must match. No gameplay, art or hardware acceptance from this helper."}
	paused=false
	if is_instance_valid(current_scene):current_scene.queue_free()
	for unused in 8:await process_frame
	# Dummy audio fades/releases on its real mixer thread, not fixed-fps scene time.
	# Observe two clock resets without assuming simulated frames span mixer ticks.
	var started:=Time.get_ticks_usec()
	var previous:=AudioServer.get_time_since_last_mix()
	var observed:=0
	var samples:Array[Dictionary]=[]
	while observed<2 and Time.get_ticks_usec()-started<250000:
		OS.delay_msec(1)
		var now:=AudioServer.get_time_since_last_mix()
		if now+.0002<previous: observed+=1
		samples.append({"wall_usec":Time.get_ticks_usec()-started,"since_mix_s":now,"ticks":observed})
		previous=now
	var wait_usec:=Time.get_ticks_usec()-started
	# AudioServer's main-thread list cleanup follows the mix-thread deletion.
	for unused in 8:await process_frame
	check("two real mixer ticks observed within250ms cleanup budget",observed==2 and wait_usec<=250000)
	report.audio_cleanup={"scope":"Capture shutdown only, after allthree shots and scene free; no runtime audio change.","observed_mixer_ticks":observed,"wait_usec":wait_usec,"budget_usec":250000,"samples":samples,"main_cleanup_frames":8}
	report.complete=failure.is_empty() and checks.all(func(item):return item.passed)
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):write_json(output.path_join("preflight.json" if preflight else "capture.json"),report)
	print("OVERVIEW_COMPOSITION_COMPLETE ",report.complete," ",failure)
	quit(0 if report.complete else 1)
