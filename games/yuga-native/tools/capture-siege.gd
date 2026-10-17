extends "res://tools/capture-traversal.gd"
## Continuous actual siege simulation; one public drill/camera staging before take.

var siege_before := {}
var saw_windup := false
var saw_impact := false
var vehicles_moved := false
var start_positions := {}
var siege_finite := true

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): output_path = argument.trim_prefix("--output=")
		else:
			push_error("Unknown siege capture argument")
			quit(1)
			return
	if not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path) or FileAccess.file_exists(output_path):
		push_error("Choose a new absolute output directory")
		quit(1)
		return
	if DirAccess.make_dir_recursive_absolute(output_path) != OK:
		quit(1)
		return
	if DisplayServer.get_name() == "headless" or RenderingServer.get_current_rendering_method() != "forward_plus":
		_fail("Actual Forward+ display required")
		return
	if Engine.physics_ticks_per_second != 60 or not is_equal_approx(Engine.time_scale,1.0):
		_fail("Siege take requires 60 Hz physics and time_scale 1")
		return
	sources = _source_hashes()
	for path in REQUIRED_IMPORTS:
		if not _validate_import(path):
			_finish(false)
			return
	capture_size = Vector2i(1280,720)
	root.size = capture_size
	root.content_scale_size = capture_size
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA — Siege Simulation Capture"
	root.show()
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await _draw_frames(4)
	if not scene.world_ready or not scene.army.start_siege_drill():
		_fail("Actual world and siege drill must be ready")
		return
	scene.set_paused(false)
	scene.set_overview(false)
	scene.set_review_phase(0.0)
	scene.player.active = false
	scene.review_camera.global_position = Vector3(8,12,-28)
	scene.review_camera.look_at(Vector3(0,1,0),Vector3.UP)
	scene.review_camera.fov = 58
	var point_query := PhysicsPointQueryParameters3D.new()
	point_query.position = scene.review_camera.global_position
	point_query.collision_mask = 1
	var sight_query := PhysicsRayQueryParameters3D.create(scene.review_camera.global_position,Vector3(0,1,0),1)
	if not scene.get_world_3d().direct_space_state.intersect_point(point_query,8).is_empty() or not scene.get_world_3d().direct_space_state.intersect_ray(sight_query).is_empty():
		_fail("Staged camera is inside map geometry or cannot see the encounter focus")
		return
	scene.review_camera.make_current()
	scene.ui.visible = false
	var layer := CanvasLayer.new()
	root.add_child(layer)
	var label := Label.new()
	label.text = "YUGA · SIEGE PRACTICE · ACTUAL SOFTWARE RENDER · SIMULATED 30 FPS"
	label.position = Vector2(24,18)
	label.add_theme_font_size_override("font_size",18)
	label.add_theme_constant_override("outline_size",6)
	layer.add_child(label)
	scene.army.siege_event.connect(_siege_event)
	siege_before = scene.army.report()
	for unit in scene.army.units:
		if unit.role in ["cannon_cart","royal_chariot"]: start_positions[unit.unit_id] = unit.position
	take_start_tick = Engine.get_physics_frames()
	var prior_tick := take_start_tick
	var prior_draw := Engine.get_frames_drawn()
	for index in FULL_FRAMES:
		await _draw_frames(1)
		var tick := Engine.get_physics_frames()
		var draw := Engine.get_frames_drawn()
		if tick-prior_tick != 2 or draw <= prior_draw:
			_fail("Nonconsecutive actual simulation frame at %d" % index)
			return
		for unit in scene.army.units:
			siege_finite = siege_finite and unit.articulation_finite()
			if start_positions.has(unit.unit_id) and unit.position.distance_to(start_positions[unit.unit_id]) > .05: vehicles_moved = true
		var image := _save_image("frame-%05d.png" % index)
		if image.is_empty():
			_finish(false)
			return
		frames.append({"index":index,"physics_tick":tick,"physics_tick_delta":tick-prior_tick,"render_frame":draw,"finite":siege_finite,"image":image,"army":scene.army.report(),"effects":scene.siege_effects.report()})
		take_ticks = tick-take_start_tick
		prior_tick = tick
		prior_draw = draw
		if index % 30 == 0: print("YUGA_SIEGE_CAPTURE frame=",index)
	if not saw_windup or not saw_impact or not vehicles_moved or not siege_finite:
		_fail("Take omitted siege windup, impact, vehicle motion or finite articulation")
		return
	if sources != _source_hashes():
		_fail("Capture source changed during take")
		return
	_finish(true)

func _source_hashes() -> Dictionary:
	var result := super._source_hashes()
	for path in ["res://tools/capture-siege.gd","res://tools/run-siege-capture.py"]: result[path] = FileAccess.get_sha256(path)
	return result

func _siege_event(event: Dictionary) -> void:
	if event.kind == "windup": saw_windup = true
	if event.kind == "impact" and not event.get("cancelled",false): saw_impact = true
	events.append({"physics_tick":Engine.get_physics_frames(),"event":_normal(event)})

func _finish(success: bool) -> void:
	var report := {"schema":1,"complete":success,"failure":failure,"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"fps":30,"physics_hz":Engine.physics_ticks_per_second,"time_scale":Engine.time_scale,"width":1280,"height":720,"take_start_tick":take_start_tick,"take_physics_ticks":take_ticks,"frames":frames,"events":events,"source_sha256":sources,"imports":imports,"before":siege_before,"outcomes":{"windup":saw_windup,"impact":saw_impact,"vehicles_moved":vehicles_moved,"finite":siege_finite},"scope":"Six seconds of continuous actual offline siege simulation after a single public drill and camera staging. No per-frame state writes. Silent video; software rendering at a simulated playback rate is not GPU performance or final-art acceptance."}
	if is_instance_valid(scene): report["after"] = scene.army.report()
	var file := FileAccess.open(output_path.path_join("siege-render-review.json"),FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(_normal(report),"\t")+"\n")
	if not success: push_error(failure)
	quit(0 if success else 1)
