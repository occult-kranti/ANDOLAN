extends "res://tools/visual-campaign/capture.gd"
## Bounded original framebuffers. All changes are diagnostic camera/time controls.
var mode := "stills"
var context := "courtyard"
var sequence_controls: Array = []
var expected := 0

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--mode="): mode = arg.trim_prefix("--mode=")
		elif arg.begins_with("--context="): context = arg.trim_prefix("--context=")
		else: finish("Unknown argument "+arg); return
	if not mode in ["stills","continuity","actions","probe","forms"] or not context in ["courtyard","stone","foliage"]: finish("Unknown mode/context"); return
	expected = 3 if mode == "forms" else 36 if mode == "continuity" else (5 if mode == "actions" else (1 if mode == "probe" else (10 if context == "courtyard" else 2)))
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	if DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus": finish("X11 Forward+ required"); return
	seed(741031)
	root.size = SIZE; root.content_scale_size = SIZE; root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA bounded visual controls"; root.show()
	shadow_world = context != "courtyard"
	sources = source_hashes()
	scene = load("res://scenes/confluence_world.tscn" if shadow_world else "res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await draw(6)
	player = scene.player
	if not player.model_ready or not (scene.world_ready if shadow_world else scene.environment_ready): finish("Actual hero or world missing"); return
	review_camera = Camera3D.new(); review_camera.name = "RoundReviewCamera"; scene.add_child(review_camera)
	review_camera.fov = 32.0; review_camera.far = 180.0
	freeze_background_time()
	paused = true
	scene.set_process(false); scene.set_physics_process(false)
	if shadow_world:
		scene.set_paused(false); scene.set_overview(false)
		scene.teleport_to(Vector3(-20,.05,14) if context == "stone" else Vector3(-54,.05,0),180.0 if context == "stone" else 18.627274488929288)
	else:
		scene.start_training()
		scene.title_light.hide()
	await draw(8)
	paused = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	scene.ui.hide()
	set_light(false)
	if mode in ["stills","probe","forms"]: await capture_stills()
	elif mode == "continuity": await capture_continuity()
	else: await capture_action_poses()
	if not done: finish("")

func face_camera(view: String) -> void:
	var rig: Skeleton3D = player.rama_motion.rig
	var center: Vector3 = rig.global_transform * rig.get_bone_global_pose(rig.find_bone("head")).origin + Vector3(0,.075,0)
	var offset: Vector3 = {"front":Vector3(0,.04,-.89),"three-quarter-left":Vector3(-.64,.04,-.62),"three-quarter-right":Vector3(.64,.04,-.62),"profile":Vector3(.89,.04,0)}[view]
	if context == "foliage": offset.y = -.08
	offset = Basis(Vector3.UP,player.visual.global_rotation.y - PI) * offset
	review_camera.global_position = center+offset
	review_camera.look_at(center)
	review_camera.reset_physics_interpolation()
	player.rama_lod._selector.reset()
	player.rama_lod.update(review_camera,1.0/30.0)

func capture_stills() -> void:
	var views := ["front","three-quarter-left","three-quarter-right","profile","gameplay"] if context == "courtyard" and mode != "probe" else ["three-quarter-left"]
	if mode == "forms": views = ["front","three-quarter-left","profile"]
	for night in ([false] if mode in ["probe","forms"] else [false,true]):
		set_light(night)
		for view in views:
			scene.ui.visible = view == "gameplay"
			if view != "gameplay": face_camera(view)
			var camera: Camera3D = player.camera if view == "gameplay" else review_camera
			await shot(context+"-"+view+("-night" if night else "-day"),camera,"Fixed current-runtime " + context+" view; original light/material/geometry policy; portrait fill off")
			if done: return

func capture_continuity() -> void:
	face_camera("three-quarter-left"); review_camera.make_current()
	player.pitch = -.25
	player.pivot.rotation.y = PI
	player.rama_face.reset("capture sequence origin")
	# Clock setup uses the public single-owner facial update; no direct morph writes.
	for tick in 181: player.rama_face.update_facial(1.0/60.0,{"alive":true,"paused":false,"effort":0.0})
	sequence_controls.append({"kind":"facial_clock_preroll","normal_update_ticks":181,"tick_seconds":1.0/60.0,"state":player.rama_face.report(),"world_advanced":false})
	scene.rama_runtime.combat_event.connect(record_event)
	paused = false
	var cast: Dictionary = scene.rama_runtime.cast_ability("kodanda")
	if not cast.get("accepted",false): finish("Kodanda denied: "+str(cast)); return
	sequence_controls.append({"frame":0,"kind":"cast","ability":"kodanda","result":normal(cast)})
	paused = false
	for index in 36:
		if index == 15:
			cast = scene.rama_runtime.cast_ability("piercing_dawn")
			if not cast.get("accepted",false): finish("Piercing denied"); return
			sequence_controls.append({"frame":index,"kind":"cast","ability":"piercing_dawn","result":normal(cast)})
		if index == 24:
			var cancelled: bool = scene.rama_runtime.kit.cancel_windup("round2_face_probe")
			if not cancelled: finish("Windup cancellation denied"); return
			sequence_controls.append({"frame":index,"kind":"cancel_windup","reason":"round2_face_probe"})
		await draw(1)
		write_frame("frame-%03d"%index,review_camera,"Adjacent normal runtime frames; real Kodanda cast then Piercing cancellation; fixed camera")
		if done: return
	paused = true

func capture_action_poses() -> void:
	scene.rama_runtime.combat_event.connect(record_event)
	for id in ABILITY_IDS:
		paused = true
		scene.reset_training(); scene.start_training(); scene.ui.hide(); scene.title_light.hide(); set_light(false)
		player.pitch = -.25; player.pivot.rotation.y = PI
		face_camera("three-quarter-left"); review_camera.make_current()
		paused = false
		var cast: Dictionary = scene.rama_runtime.cast_ability(id)
		if not cast.get("accepted",false): finish("Action pose denied "+id); return
		paused = false
		var windup_frames: int = {"kodanda":3,"piercing_dawn":18,"measured_step":2,"guardian_circle":15,"dawn_volley":27}[id]
		await draw(windup_frames)
		paused = true
		await shot("action-"+id+"-windup",review_camera,"Real runtime cast, late windup; normal FX on")
		sequence_controls.append({"ability":id,"cast":normal(cast),"phase":"late windup","advanced_render_frames":windup_frames,"events":events.duplicate(true)})
		if done: return

func shot(id: String, camera: Camera3D, scope: String) -> void:
	camera.make_current(); camera.reset_physics_interpolation()
	player.rama_lod.update(camera,1.0/30.0)
	await draw(4)
	write_frame(id,camera,scope)

func write_frame(id: String,camera: Camera3D,scope: String) -> void:
	var frame := root.get_texture().get_image()
	var file := id+".png"
	if frame.is_empty() or frame.get_size()!=SIZE or frame.save_png(output.path_join(file))!=OK: finish("Framebuffer write failed"); return
	var env: Environment = scene.world_environment.environment
	shots.append({"id":id,"file":file,"sha256":FileAccess.get_sha256(output.path_join(file)),"viewport":[SIZE.x,SIZE.y],"camera":{"transform":normal(camera.global_transform),"fov":camera.fov,"near":camera.near,"far":camera.far},"context":context,"night":scene.night,"ui_visible":scene.ui.visible,"player_transform":normal(player.global_transform),"visual_yaw":player.visual.global_rotation.y,"lod":player.rama_lod.report(),"motion":player.rama_motion.diagnostics(),"face":player.rama_face.report(),"pose_pin":rig_pose_pin(),"skin_materials":skin_state(),"render_settings":{"taa":root.use_taa,"msaa_3d":root.msaa_3d,"screen_space_aa":root.screen_space_aa},"light":{"sun_transform":normal(scene.sun.global_transform),"color":normal(scene.sun.light_color),"energy":scene.sun.light_energy,"angular_distance":scene.sun.light_angular_distance,"shadow_enabled":scene.sun.shadow_enabled,"shadow_bias":scene.sun.shadow_bias,"shadow_normal_bias":scene.sun.shadow_normal_bias,"tonemap_exposure":env.tonemap_exposure,"ssao_enabled":env.ssao_enabled,"portrait_fill":false},"render_frame":Engine.get_frames_drawn(),"physics_frame":Engine.get_physics_frames(),"tree_paused":paused,"scope":scope})
	print("VISUAL_ROUNDS_SHOT ",file)

func skin_state() -> Array:
	var result: Array = []
	var seen := {}
	for node in player.visual.find_children("*","MeshInstance3D",true,false):
		if not node.mesh: continue
		for surface in node.mesh.get_surface_count():
			var material = node.get_active_material(surface)
			if not material is StandardMaterial3D or seen.has(material.get_instance_id()) or not "skin" in material.resource_name.to_lower(): continue
			seen[material.get_instance_id()] = true
			var texture: Texture2D = material.roughness_texture
			var image: Image = texture.get_image() if texture else null
			result.append({"name":material.resource_name,"sss_enabled":material.subsurf_scatter_enabled,"sss_strength":material.subsurf_scatter_strength,"roughness":material.roughness,"roughness_texture":texture.resource_path if texture else "","roughness_has_mipmaps":image.has_mipmaps() if image else false,"roughness_mipmap_count":image.get_mipmap_count() if image else 0})
	return result

func collect_import_metadata(path: String, paths: Array[String]) -> void:
	for name in DirAccess.get_files_at(path):
		if name.ends_with(".import"): paths.append(path.path_join(name))
	for name in DirAccess.get_directories_at(path): collect_import_metadata(path.path_join(name),paths)

func source_hashes() -> Dictionary:
	var result := super.source_hashes()
	var metadata: Array[String] = []
	collect_import_metadata("res://assets",metadata)
	for path in metadata: result[path] = FileAccess.get_sha256(path)
	for path in ["res://tools/visual-rounds/capture.gd","res://tools/visual-rounds/run.py"]: result[path] = FileAccess.get_sha256(path)
	return result

func finish(failure: String) -> void:
	if done: return
	done = true
	var after := source_hashes() if not sources.is_empty() else {}
	var report := {"schema":1,"kind":"actual-native-visual-rounds","camera_contract":"face-context-v1","mode":mode,"context":context,"complete":failure.is_empty() and sources==after and shots.size()==expected,"failure":failure,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"shots":shots,"ability_events":events,"sequence_controls":sequence_controls,"expected_raw_pngs":expected,"time_controls":time_controls,"clocks":{"fixed_capture_process_hz":30,"physics_hz":Engine.physics_ticks_per_second,"army_authority_hz":20,"hardware_fps_measured":false},"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"Original Forward+ full framebuffers. Fixed30Hz capture is simulation sampling, not hardware FPS. Static context and 1.2s diagnostic clip do not certify full gameplay or commercial graphics parity."}
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("VISUAL_ROUNDS_COMPLETE ",report.complete," ",failure)
	paused = false
	if is_instance_valid(scene):
		for node in scene.find_children("*","AudioStreamPlayer",true,false): node.stop(); node.stream=null
		scene.queue_free()
	for index in range(3): await process_frame
	await create_timer(.1,true,false,true).timeout
	quit(0 if report.complete else 1)
