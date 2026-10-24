extends "res://tools/lanka-water-garden/capture.gd"
## Three actual integrated states; existing UI owner refreshes after staging/phase.
func hashes() -> Dictionary:
	var result := super.hashes()
	result["res://tools/lanka-water-garden/capture_integrated.gd"] = FileAccess.get_sha256("res://tools/lanka-water-garden/capture_integrated.gd")
	return result

func capture(kind: String, view: Dictionary) -> void:
	await super.capture(kind, view)
	check("existing live UI owner shows staged district " + String(view.id), scene.location_label.text == scene.district_at(scene.player.position), {"shown": scene.location_label.text, "district": scene.district_at(scene.player.position)})
	check("existing live atlas tracks actual held hero " + String(view.id), scene.map_control.hero_position == scene.player.position)
	var phase_label := "Moonlight" if float(view.phase) > .5 else "Golden hour"
	check("existing status owner shows actual phase " + String(view.id), phase_label in scene.status_label.text, scene.status_label.text)

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--preflight": preflight = true
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): push_error("fresh absolute output required"); quit(1); return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name() == "headless" or RenderingServer.get_current_rendering_method() != "forward_plus"):
		push_error("actual Forward+ renderer required"); quit(1); return
	source_hashes = hashes()
	root.size = Vector2i(960, 540)
	root.content_scale_size = Vector2i(1280, 720)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.msaa_3d = Viewport.MSAA_2X
	if not preflight: root.show()
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await draw_frames(8)
	check("actual default integrated world and accepted Rama ready", scene.world_ready and scene.player.model_ready)
	if not checks[-1].passed: await finish(); return
	check("default reviewed banks and gate mounted", scene.lanka_water_garden_enabled and scene.lanka_water_garden_report.enabled and scene.lanka_lane_gate_report.enabled and scene.world.has_node(Garden.ROOT_NAME))
	check("current bank resource identity and4bodies", scene.lanka_water_garden_report.asset_sha256 == Garden.ASSET_SHA and scene.world.get_node(Garden.ROOT_NAME).find_children("*", "StaticBody3D", true, false).size() == 4)
	check("39army boxes retain8authority8deck10anchors", scene.army.boxes.size() == 39 and scene.authority_bodies.size() == 8 and scene.native_platform_bodies.size() == 8 and scene.manifest.traversal.anchors.size() == 10)
	scene.set_overview(false); scene.set_paused(false); scene.set_review_phase(0)
	scene.set_process(false); scene.set_physics_process(false); hold_callbacks(scene.world)
	for water: Dictionary in scene.manifest.waters:
		var material: ShaderMaterial = scene.world.get_node(water.id).get_active_material(0)
		material.set_shader_parameter("animation_speed", 0.0)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	scene.player.global_position = Vector3(-50, .04, 0)
	scene.player.velocity = Vector3.ZERO
	scene.player.yaw = PI / 2
	scene.player.pitch = -.10
	scene.player._update_camera()
	scene.player.visual.rotation.y = -PI / 2
	scene.player._update_rama_motion(1.0 / 60)
	scene.player.rama_motion.evaluate_pose()
	await physics_frame; await physics_frame; await draw_frames(2)
	ordinary_camera = scene.player.camera.global_transform
	camera = Camera3D.new()
	camera.fov = scene.player.camera.fov; camera.near = scene.player.camera.near; camera.far = scene.player.camera.far
	scene.add_child(camera); camera.current = true
	held = freeze_state()
	placement_result = {"enabled": true, "report": scene.lanka_water_garden_report}
	for view in views(): await capture("integrated", view)
	await finish()

func finish() -> void:
	check("three integrated current-UI views", shots.size() == 3)
	var after := hashes()
	check("protected sources unchanged through capture", after == source_hashes)
	var passed := checks.all(func(row): return row.passed)
	var report := {"schema": 1, "complete": passed, "preflight": preflight, "checks": checks, "shots": shots,
		"actual_image_count": 0 if preflight else shots.size(), "route_frames": [], "composition": placement_result.get("report", {}),
		"held_state": held, "ordinary_camera": transform(ordinary_camera), "source_sha256": source_hashes, "source_after_sha256": after,
		"renderer": RenderingServer.get_current_rendering_method(), "adapter": RenderingServer.get_video_adapter_name(), "display": DisplayServer.get_name(),
		"canonical_enabled": true, "scope": "Three actual current default integrated bank-feature views. Real Rama idle evaluated, then callbacks/army/water held; existing scene._process(.13) refreshes district/atlas/status from current staged hero and phase. No fabricated UI copy. Staged diagnostics, not normal-input journey or hardware performance; previous six matched R1 views retain earlier source and held stale HUD."}
	FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"), FileAccess.WRITE).store_string(JSON.stringify(report, "  ") + "\n")
	if is_instance_valid(scene): scene.queue_free()
	for unused in 8: await process_frame
	print("WATER_GARDEN_INTEGRATED_COMPLETE ", passed, " checks=", checks.size())
	quit(0 if passed else 1)
