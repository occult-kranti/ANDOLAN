extends SceneTree
## Unaltered framebuffers from the actual courtyard, fixed camera contract v1.
const SIZE := Vector2i(1280, 960)
var output := ""
var scene: Node3D
var player: CharacterBody3D
var review_camera: Camera3D
var sources := {}
var shots: Array = []
var events: Array = []
var time_controls: Array = []
var started := Time.get_ticks_msec()
var done := false

func _initialize() -> void: call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		else: finish("Unknown argument " + arg); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	if DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus": finish("X11 Forward+ required"); return
	seed(741031)
	root.size = SIZE; root.content_scale_size = SIZE; root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA actual visual campaign"; root.show()
	sources = source_hashes()
	scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await draw(6)
	player = scene.player
	if not player.model_ready or not scene.environment_ready: finish("Actual hero or courtyard missing"); return
	review_camera = Camera3D.new(); review_camera.name = "CampaignReviewCamera"; scene.add_child(review_camera)
	review_camera.fov = 43.0; review_camera.far = 180.0
	freeze_background_time()
	paused = true
	scene.set_process(false); scene.set_physics_process(false)
	set_light(false)
	await shot("01-title-day", scene.title_camera, "actual title camera and interface")
	if done: return
	scene.start_training()
	await draw(8)
	paused = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	scene.ui.hide(); scene.title_light.hide()
	place_hero_camera()
	for night in [false, true]:
		set_light(night)
		await shot("03-hero-near-night" if night else "02-hero-near-day", review_camera, "fixed three-quarter hero portrait; real current mesh/materials")
		if done: return
	scene.ui.show()
	for night in [false, true]:
		set_light(night)
		await shot("05-gameplay-night" if night else "04-gameplay-day", player.camera, "actual player camera and gameplay HUD; input idle")
		if done: return
	scene.ui.hide()
	review_camera.fov = 60.0
	review_camera.global_position = Vector3(16, 12, 24)
	review_camera.look_at(Vector3(0, 2, -3))
	for night in [false, true]:
		set_light(night)
		await shot("07-courtyard-overview-night" if night else "06-courtyard-overview-day", review_camera, "staged overview of actual playable courtyard")
		if done: return
	set_light(false)
	scene.ui.show(); player.camera.make_current()
	scene.rama_runtime.combat_event.connect(func(event: Dictionary):
		if event.get("kind") in ["begin", "release"]: events.append(normal(event)))
	paused = false
	var accepted: Dictionary = scene.rama_runtime.cast_ability("piercing_dawn")
	if not accepted.get("accepted", false): finish("Normal runtime ability request refused: " + str(accepted)); return
	var released := false
	for index in range(30):
		await draw(1)
		for event in events:
			if event.kind == "release": released = true
		if released: break
	if not released: finish("No authority ability release within 30 fixed-rate frames"); return
	paused = true
	await shot("08-piercing-dawn-release", player.camera, "actual runtime cast and authority release; frozen immediately after release frame")
	if not done: finish("")

func draw(count: int) -> void:
	for index in range(count):
		await process_frame
		await RenderingServer.frame_post_draw

func set_light(night: bool) -> void:
	scene.night = night
	scene._apply_settings()

func place_hero_camera() -> void:
	# Explicit framing in metres, independent of changed vertex bounds.
	review_camera.global_position = player.global_position + Vector3(-1.45, 1.30, -3.55)
	review_camera.look_at(player.global_position + Vector3(0, 1.08, 0))
	review_camera.reset_physics_interpolation()

func shot(id: String, camera: Camera3D, scope: String) -> void:
	camera.make_current(); camera.reset_physics_interpolation()
	if is_instance_valid(player.rama_lod): player.rama_lod.update(camera, 1.0/15.0)
	await draw(4)
	var image := root.get_texture().get_image()
	var filename := id + ".png"
	if image.is_empty() or image.get_size() != SIZE or image.save_png(output.path_join(filename)) != OK: finish("Framebuffer write failed"); return
	shots.append({"id":id,"file":filename,"sha256":FileAccess.get_sha256(output.path_join(filename)),"viewport":[SIZE.x,SIZE.y],"camera":{"transform":normal(camera.global_transform),"fov":camera.fov,"near":camera.near,"far":camera.far},"night":scene.night,"ui_visible":scene.ui.visible,"player_transform":normal(player.global_transform),"lod":player.rama_lod.report(),"motion":player.rama_motion.diagnostics(),"render_frame":Engine.get_frames_drawn(),"physics_frame":Engine.get_physics_frames(),"tree_paused":paused,"scope":scope})
	print("VISUAL_CAMPAIGN_SHOT ", filename)

func normal(value: Variant) -> Variant:
	if value is Vector2: return [value.x,value.y]
	if value is Vector3: return [value.x,value.y,value.z]
	if value is Vector4 or value is Quaternion: return [value.x,value.y,value.z,value.w]
	if value is Transform3D: return [normal(value.basis.x),normal(value.basis.y),normal(value.basis.z),normal(value.origin)]
	if value is Dictionary:
		var result := {}
		for key in value: result[key] = normal(value[key])
		return result
	if value is Array:
		var result := []
		for item in value: result.append(normal(item))
		return result
	return value

func collect_files(path: String, paths: Array[String]) -> void:
	for name in DirAccess.get_files_at(path):
		if not name.ends_with(".import") and not name.ends_with(".uid"): paths.append(path.path_join(name))
	for name in DirAccess.get_directories_at(path): collect_files(path.path_join(name), paths)

func source_hashes() -> Dictionary:
	var paths: Array[String] = ["res://project.godot","res://tools/visual-campaign/capture.gd","res://tools/visual-campaign/run.py"]
	for directory in ["res://scripts","res://shaders","res://scenes","res://assets"]: collect_files(directory, paths)
	paths.sort()
	var result := {}
	for path in paths: result[path] = FileAccess.get_sha256(path)
	return result

func freeze_background_time() -> void:
	var seen := {}
	for node in scene.find_children("*", "MeshInstance3D", true, false):
		if not node.mesh: continue
		for surface in node.mesh.get_surface_count():
			var material = node.get_active_material(surface)
			if not material is ShaderMaterial or material.shader == null or seen.has(material.get_instance_id()): continue
			seen[material.get_instance_id()] = true
			if material.shader.resource_path in ["res://scripts/world_water.gdshader","res://shaders/production_water.gdshader"]:
				material.set_shader_parameter("animation_speed", 0.0)
				time_controls.append({"shader":material.shader.resource_path,"animation_speed":0.0})

func finish(failure: String) -> void:
	if done: return
	done = true
	var after := source_hashes() if not sources.is_empty() else {}
	var report := {"schema":1,"kind":"actual-courtyard-visual-campaign","camera_contract":"courtyard-eight-v1","complete":failure.is_empty() and sources == after and shots.size() == 8,"failure":failure,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources == after,"shots":shots,"ability_events":events,"time_controls":time_controls,"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"Original native Forward+ framebuffers. Fixed 15 simulation frames/second is a capture clock, not measured hardware FPS. Frozen views and one real ability release do not qualify continuous motion, gameplay feel or commercial graphics parity."}
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("VISUAL_CAMPAIGN_COMPLETE ", report.complete, " ", failure)
	paused = false
	if is_instance_valid(scene):
		for node in scene.find_children("*","AudioStreamPlayer",true,false): node.stop(); node.stream = null
		scene.queue_free()
	for index in range(3): await process_frame
	await create_timer(.1,true,false,true).timeout
	quit(0 if report.complete else 1)
