extends "res://tools/ui-campaign/observer.gd"
## Matched title-light review: real Moonlit setting callback and native Window scale. No pose/camera/light assignment overrides.
var preflight := false
var sources: Dictionary = {}
var shots: Array = []
var checkpoints: Array = []
var done := false

func _initialize() -> void:
	call_deferred("run")

func _process(_delta: float) -> bool:
	return false

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--case=scene-anchors": pass
		elif arg == "--preflight": preflight = true
		else: finish("Unknown scene-anchor argument " + arg); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus"):
		finish("X11 Forward+ required"); return
	seed(741031)
	mode = "scene-anchors"
	root.size = Vector2i(960, 540)
	root.content_scale_size = Vector2i(1280, 720)
	root.title = "YUGA matched title-light night and 200 percent"
	if not preflight: root.show()
	sources = source_hashes()
	var scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	checkpoint("before_initial_draw6")
	await draw_frames(6)
	checkpoint("after_initial_draw6")
	if not scene.environment_ready or not scene.player.model_ready: finish("Actual environment/hero missing"); return
	if not await set_moonlit(scene, true): return
	if not await take_anchor("00-title-night-100", scene.title_camera): return
	if not await set_moonlit(scene, false): return
	root.content_scale_factor = 2.0
	await draw_frames(12)
	if not await take_anchor("01-title-day-200", scene.title_camera): return
	finish("")

func set_moonlit(scene: Node, value: bool) -> bool:
	scene._open_settings(true)
	await draw_frames(3)
	var toggle: CheckButton
	for item in scene.settings_panel.find_children("*", "CheckButton", true, false):
		if item.text == "Moonlit courtyard": toggle = item
	if not is_instance_valid(toggle): finish("Actual Moonlit courtyard control missing"); return false
	toggle.button_pressed = value
	await draw_frames(3)
	if scene.night != value: finish("Moonlit callback did not apply"); return false
	scene._close_settings()
	await draw_frames(12)
	checkpoint("moonlit_" + str(value))
	return true

func draw_frames(count: int) -> void:
	for index in count:
		if preflight:
			for tick in 2: await physics_frame
		else:
			await process_frame
			await RenderingServer.frame_post_draw

func checkpoint(stage: String) -> void:
	var item := {"stage": stage, "wall_ms": Time.get_ticks_msec(), "physics_frame": Engine.get_physics_frames(), "render_frame": Engine.get_frames_drawn(), "paused": paused}
	checkpoints.append(item)
	print("SCENE_ANCHOR_STAGE ", JSON.stringify(item))

func vector(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func take_anchor(id: String, camera: Camera3D) -> bool:
	if root.get_camera_3d() != camera: finish("Product camera is not active: " + id); return false
	var state := snapshot()
	state.id = id
	state.render_frame = Engine.get_frames_drawn()
	state.camera = {"path": str(camera.get_path()), "matches_expected_product_camera": true, "fov": camera.fov, "near": camera.near, "far": camera.far, "transform": [vector(camera.global_basis.x), vector(camera.global_basis.y), vector(camera.global_basis.z), vector(camera.global_position)]}
	state.canvas_size = [root.content_scale_size.x, root.content_scale_size.y]
	state.content_scale_factor = root.content_scale_factor
	state.logical_viewport = str(root.get_visible_rect())
	var scene = current_scene
	state.portrait_light = {"position": vector(scene.title_light.position), "color": [scene.title_light.light_color.r, scene.title_light.light_color.g, scene.title_light.light_color.b, scene.title_light.light_color.a], "energy": scene.title_light.light_energy, "range": scene.title_light.omni_range, "visible": scene.title_light.visible, "shadow_enabled": scene.title_light.shadow_enabled}
	var rig: Skeleton3D = scene.player.rama_motion.rig
	state.final_bones = []
	for index in rig.get_bone_count():
		var pose := rig.get_bone_global_pose(index)
		state.final_bones.append({"name": str(rig.get_bone_name(index)), "transform": [vector(pose.basis.x), vector(pose.basis.y), vector(pose.basis.z), vector(pose.origin)]})
	state.scope = "Actual product title camera/pose. Moonlit CheckButton callbacks and native Window content_scale_factor are declared fixture actions, not OS input. No light assignments beyond the pinned source variant. Settled frames do not certify initial support acquisition."
	if not preflight:
		var original := root.get_texture().get_image()
		state.framebuffer_size = [original.get_width(), original.get_height()]
		state.file = id + ".png"
		if original.save_png(output.path_join(state.file)) != OK: finish("PNG write failed"); return false
		state.sha256 = FileAccess.get_sha256(output.path_join(state.file))
	shots.append(state)
	_write(output.path_join(id + ".json"), state)
	print("SCENE_ANCHOR_SHOT ", id)
	return true

func source_hashes() -> Dictionary:
	var seal: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://.graphics-six-snapshot.json"))
	var result := {}
	for name in seal.files:
		result[name] = FileAccess.get_sha256("res://" + name)
	result[".graphics-six-snapshot.json"] = FileAccess.get_sha256("res://.graphics-six-snapshot.json")
	return result

func finish(failure: String) -> void:
	if done: return
	done = true
	var after := source_hashes() if not sources.is_empty() else {}
	var checks := [{"name": "two matched title observations", "passed": shots.size() == 2}, {"name": "source unchanged", "passed": sources == after}]
	if shots.size() == 2:
		checks.append({"name": "both actual inactive titles", "passed": shots.all(func(s): return not s.state.player_active and not s.state.started)})
		checks.append({"name": "night100 then day200 title menus", "passed": shots[0].panels.main_panel and shots[1].panels.main_panel and shots[0].state.night and not shots[1].state.night and shots[0].content_scale_factor == 1.0 and shots[1].content_scale_factor == 2.0})
		checks.append({"name": "expected product cameras", "passed": shots.all(func(s): return s.camera.matches_expected_product_camera)})
	var passed := failure.is_empty() and checks.all(func(c): return c.passed)
	var report := {"schema": 1, "case": "scene-anchors", "complete": passed, "failure": failure, "shots": shots, "checks": checks, "checkpoints": checkpoints, "source_sha256": sources, "source_after_sha256": after, "source_unchanged": sources == after, "preflight": preflight, "renderer": RenderingServer.get_current_rendering_method(), "adapter": RenderingServer.get_video_adapter_name(), "scope": "Two settled source-bound actual title cameras: night100 and day200. No quality or hardware performance claim from mechanical checks."}
	if not output.is_empty(): _write(output.path_join("preflight.json" if preflight else "capture.json"), report)
	print("SCENE_ANCHOR_COMPLETE ", passed, " ", failure)
	paused = false
	if is_instance_valid(current_scene): current_scene.queue_free()
	for index in 3: await process_frame
	quit(0 if passed else 1)
