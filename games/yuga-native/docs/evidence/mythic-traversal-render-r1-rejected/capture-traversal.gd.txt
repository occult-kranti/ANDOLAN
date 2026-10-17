extends SceneTree
## Actual rendered sequential input scenario. No human-input or realtime-FPS claim.

const FPS := 30
const FULL_FRAMES := 180
const PREVIEW_FRAMES := 24
const ACTIONS := ["grapple", "fly", "jump", "move_right"]
const REQUIRED_IMPORTS := ["res://assets/heroes/rama-production.glb", "res://assets/world/architecture.glb", "res://assets/world/nature.glb"]
var output_path := ""
var preview := false
var capture_size := Vector2i(1280, 720)
var scene: Node3D
var sources := {}
var imports := {}
var frames: Array[Dictionary] = []
var stills: Array[Dictionary] = []
var inputs: Array[Dictionary] = []
var events: Array[Dictionary] = []
var failure := ""
var started_ms := Time.get_ticks_msec()
var take_start_tick := 0
var take_start_draw := 0
var pose_digest := ""
var pose_finite := true
var pose_samples := 0
var saw_grapple := false
var saw_flight := false
var saw_rope := false
var saw_overlay := false
var max_speed := 0.0
var min_energy := 100.0
var take_ticks := 0
var army_staging := {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			output_path = argument.trim_prefix("--output=")
		elif argument == "--preview":
			preview = true
		else:
			push_error("Unknown capture argument: " + argument)
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
		_fail("Actual Forward+ display required; headless dummy images are not accepted")
		return
	if Engine.physics_ticks_per_second != 60 or not is_equal_approx(Engine.time_scale, 1.0):
		_fail("The scenario requires 60 Hz physics and time_scale 1")
		return
	sources = _source_hashes()
	for path in REQUIRED_IMPORTS:
		if not _validate_import(path):
			_finish(false)
			return
	capture_size = Vector2i(960, 540) if preview else Vector2i(1280, 720)
	root.size = capture_size
	root.content_scale_size = Vector2i(1280, 720)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA — Staged Native Input Capture"
	root.show()
	var packed = load("res://scenes/confluence_world.tscn")
	if not packed is PackedScene:
		_fail("Confluence scene failed to load")
		return
	scene = packed.instantiate()
	root.add_child(scene)
	current_scene = scene
	await _draw_frames(4)
	if not scene.world_ready or not scene.player.model_ready or not scene.player.traversal_report().enabled:
		_fail("The actual world, imported hero and traversal must be ready")
		return
	_add_label()
	scene.set_overview(false)
	scene.set_paused(false)
	scene.set_review_phase(0.0)
	var start := Vector3(0, 0.05, -112)
	var anchor := Vector3(-20, 12, -88)
	var direction := anchor - start
	scene.teleport_to(start, rad_to_deg(atan2(direction.x, direction.z)))
	await _draw_frames(8)
	# One public camera staging operation before the take; no actor transform writes.
	scene.player.camera.look_at(anchor, Vector3.UP)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	scene.player.traversal_event.connect(_traversal_event)
	if not is_instance_valid(scene.player.traversal_pose):
		_fail("Original traversal modifier is unavailable")
		return
	scene.player.traversal_pose.modification_processed.connect(_sample_pose)
	await _draw_frames(2)
	if scene.player.traversal_report().candidate.is_empty():
		_fail("First Sun ring is not actually eligible after camera staging")
		return
	var count := PREVIEW_FRAMES if preview else FULL_FRAMES
	take_start_tick = Engine.get_physics_frames()
	take_start_draw = Engine.get_frames_drawn()
	var prior_tick := take_start_tick
	var prior_draw := take_start_draw
	for index in count:
		_drive(index)
		await _draw_frames(1)
		var tick := Engine.get_physics_frames()
		var draw := Engine.get_frames_drawn()
		var state: Dictionary = scene.player.traversal_report()
		var position: Vector3 = scene.player.global_position
		var velocity: Vector3 = scene.player.velocity
		if tick - prior_tick != 2 or draw <= prior_draw:
			_fail("Sequential take lost its required two physics ticks per rendered frame at index %d" % index)
			return
		if not position.is_finite() or not velocity.is_finite() or not pose_finite or pose_digest.is_empty() or not is_finite(float(state.energy)):
			_fail("Nonfinite player/pose state during actual take")
			return
		saw_grapple = saw_grapple or state.mode == "grapple"
		saw_flight = saw_flight or state.mode == "flight"
		saw_rope = saw_rope or state.rope_visible
		saw_overlay = saw_overlay or float(state.pose.get("weight", 0)) > 0
		max_speed = maxf(max_speed, velocity.length())
		min_energy = minf(min_energy, float(state.energy))
		var image := _save_image("frame-%05d.png" % index)
		if image.is_empty():
			_finish(false)
			return
		var frame := {"index":index, "presentation_seconds":float(index) / FPS,
			"sample_end_simulation_seconds":float(tick - take_start_tick) / 60.0,
			"physics_tick":tick, "physics_tick_delta":tick - prior_tick, "render_frame":draw,
			"player_position":_normal(position), "player_velocity":_normal(velocity),
			"traversal":_normal(state), "pose_sha256":pose_digest, "pose_samples":pose_samples,
			"held_actions":_held(), "finite":true, "image":image}
		frame["state_sha256"] = JSON.stringify(frame).sha256_text()
		frames.append(frame)
		if index == (12 if preview else 145):
			var hud := _save_image("still-05-actual-take-hud.png")
			stills.append({"id":"actual-take-hud", "image":hud, "take_frame":index, "scope":"Exact same rendered frame as the sequential take; no camera or actor restaging."})
		prior_tick = tick
		prior_draw = draw
		if index % 30 == 0:
			print("YUGA_TRAVERSAL_CAPTURE frame=", index, " physics_ticks=", tick - take_start_tick)
	take_ticks = Engine.get_physics_frames() - take_start_tick
	_release()
	if not saw_grapple or not saw_rope or not saw_overlay or (not preview and not saw_flight):
		_fail("Input take did not demonstrate the required traversal modes/rope/pose")
		return
	# All subsequent stills are explicitly separate staging, after the unmodified take.
	scene.set_paused(true)
	scene.set_overview(true)
	scene.ui.visible = false
	for id in ["city-overview", "sun-landing-courts"]:
		if not await _named_still(id):
			_finish(false)
			return
	if not preview:
		if not await _army_still():
			_finish(false)
			return
		if not await _named_still("moonlit-confluence"):
			_finish(false)
			return
	if sources != _source_hashes():
		_fail("Runtime source contents or source file set changed during capture")
		return
	_finish(true)

func _drive(index: int) -> void:
	match index:
		0: _input("grapple", true, index)
		1: _input("grapple", false, index)
		72:
			if scene.player.traversal_report().mode == "grapple":
				_input("grapple", true, index)
			else:
				inputs.append({"frame":index,"action":"grapple","operation":"release skipped because tether already ended"})
		73: _input("grapple", false, index)
		90:
			_input("fly", true, index)
			_input("jump", true, index)
			_input("move_right", true, index)
		91: _input("fly", false, index)
		150:
			_input("jump", false, index)
			_input("move_right", false, index)
		165:
			if scene.player.traversal_report().mode == "flight":
				_input("fly", true, index)
		166: _input("fly", false, index)

func _input(action: String, pressed: bool, index: int) -> void:
	if pressed:
		Input.action_press(action)
	else:
		Input.action_release(action)
	inputs.append({"frame":index,"action":action,"pressed":pressed})

func _held() -> Array[String]:
	var held: Array[String] = []
	for action in ACTIONS:
		if Input.is_action_pressed(action): held.append(action)
	return held

func _release() -> void:
	for action in ACTIONS:
		if InputMap.has_action(action): Input.action_release(action)

func _sample_pose() -> void:
	var skeleton: Skeleton3D = scene.player.traversal_pose.get_skeleton()
	var values := PackedFloat32Array()
	for index in skeleton.get_bone_count():
		var pose := skeleton.get_bone_global_pose(index)
		pose_finite = pose_finite and pose.is_finite() and absf(pose.basis.determinant()) > 0.000001
		for vector in [pose.origin, pose.basis.x, pose.basis.y, pose.basis.z]:
			values.append_array(PackedFloat32Array([vector.x, vector.y, vector.z]))
	var hashing := HashingContext.new()
	hashing.start(HashingContext.HASH_SHA256)
	hashing.update(values.to_byte_array())
	pose_digest = hashing.finish().hex_encode()
	pose_samples += 1

func _traversal_event(kind: String, position: Vector3) -> void:
	events.append({"kind":kind,"position":_normal(position),"physics_tick":Engine.get_physics_frames()})

func _named_still(id: String) -> bool:
	for view in scene.get_review_camera_views():
		if view.id == id:
			scene.set_review_phase(float(view.phase))
			scene.review_camera.global_position = Vector3(view.position[0],view.position[1],view.position[2])
			scene.review_camera.look_at(Vector3(view.target[0],view.target[1],view.target[2]),Vector3.UP)
			scene.review_camera.fov = float(view.get("fov",65))
			await _draw_frames(3)
			var image := _save_image("still-" + id + ".png")
			stills.append({"id":id,"image":image,"view":view,"scope":"Separate camera staging after the input take; actor and army paused."})
			return not image.is_empty()
	failure = "Required review viewpoint missing: " + id
	return false

func _army_still() -> bool:
	if not is_instance_valid(scene.army) or not scene.army.has_method("step_simulation"):
		failure = "Army simulation is unavailable for its separate review still"
		return false
	var before: Dictionary = scene.army.report()
	var steps := 0
	while steps < 5400 and int(scene.army.report().queued_attacks) == 0:
		if not scene.army.step_simulation(1.0 / 60.0):
			failure = "Army rejected a bounded staging step"
			return false
		steps += 1
	var after: Dictionary = scene.army.report()
	var focal := Vector3.ZERO
	var found := false
	for unit in scene.army.units:
		unit.update_pose(float(scene.army.elapsed), 1.0)
		if not found and unit.alive and is_instance_valid(unit.target):
			focal = (unit.global_position + unit.target.global_position) * 0.5
			found = true
	army_staging = {"before":before,"after":after,"additional_ticks":steps,"additional_simulation_seconds":float(steps) / 60.0,
		"observed_queued_attack":int(after.queued_attacks) > 0,"scope":"Separate post-take public army.step_simulation staging. This time advance is absent from the six-second traversal video."}
	if not found or int(after.queued_attacks) == 0:
		failure = "No actual army engagement found within bounded staging interval"
		return false
	scene.set_review_phase(0.0)
	scene.review_camera.global_position = focal + Vector3(8,5,11)
	scene.review_camera.look_at(focal + Vector3.UP,Vector3.UP)
	scene.review_camera.fov = 55
	await _draw_frames(3)
	var image := _save_image("still-army-engagement.png")
	stills.append({"id":"army-engagement","image":image,"focus":_normal(focal),"staging":army_staging})
	return not image.is_empty()

func _add_label() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 100
	root.add_child(layer)
	var label := Label.new()
	label.text = "STAGED NATIVE INPUT CAPTURE · SIMULATED 30 FPS / 60 HZ PHYSICS"
	label.position = Vector2(320,8)
	label.add_theme_font_size_override("font_size",14)
	label.add_theme_color_override("font_color",Color(1,0.9,0.65))
	label.add_theme_color_override("font_outline_color",Color(0.01,0.02,0.04))
	label.add_theme_constant_override("outline_size",7)
	layer.add_child(label)

func _draw_frames(count: int) -> void:
	for index in count:
		await process_frame
		await RenderingServer.frame_post_draw

func _save_image(filename: String) -> Dictionary:
	var rendered := root.get_texture().get_image()
	if rendered.is_empty() or rendered.get_size() != capture_size:
		failure = "Renderer did not produce the requested %dx%d image" % [capture_size.x, capture_size.y]
		return {}
	var path := output_path.path_join(filename)
	if FileAccess.file_exists(path) or rendered.save_png(path) != OK:
		failure = "Image save refused or failed: " + filename
		return {}
	return {"file":filename,"sha256":FileAccess.get_sha256(path),"width":capture_size.x,"height":capture_size.y,
		"render_frame":Engine.get_frames_drawn(),
		"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		"rendered_objects":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
		"rendered_primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)}

func _source_hashes() -> Dictionary:
	var paths: Array[String] = ["res://project.godot","res://tools/capture-traversal.gd","res://tools/run-traversal-capture.py","res://art/world/confluence-map.json"]
	for directory in ["res://scripts","res://shaders","res://scenes","res://assets"]:
		_collect(directory,paths)
	paths.sort()
	var result := {}
	for path in paths:
		result[path] = FileAccess.get_sha256(path) if FileAccess.file_exists(path) else "MISSING"
	return result

func _collect(path: String, paths: Array[String]) -> void:
	for name in DirAccess.get_files_at(path): paths.append(path.path_join(name))
	for name in DirAccess.get_directories_at(path): _collect(path.path_join(name),paths)

func _validate_import(path: String) -> bool:
	var config := ConfigFile.new()
	if config.load(path + ".import") != OK:
		failure = "Missing import metadata: " + path
		return false
	var imported: String = config.get_value("remap","path","")
	var checksum := imported.get_basename() + ".md5"
	if not FileAccess.file_exists(imported) or not FileAccess.file_exists(checksum):
		failure = "Missing imported resource: " + path
		return false
	var pattern := RegEx.new()
	var stamp := FileAccess.get_file_as_string(checksum)
	for item in [["source_md5",path],["dest_md5",imported]]:
		pattern.compile(String(item[0]) + '="([a-f0-9]+)"')
		var match_ := pattern.search(stamp)
		if not match_ or match_.get_string(1) != FileAccess.get_md5(item[1]):
			failure = "Stale imported resource: " + path
			return false
	imports[path] = {"fresh":true,"imported":imported,"sha256":FileAccess.get_sha256(imported)}
	return true

func _normal(value):
	if value is Vector3: return [value.x,value.y,value.z]
	if value is Vector2: return [value.x,value.y]
	if value is Dictionary:
		var result := {}
		for key in value: result[key] = _normal(value[key])
		return result
	if value is Array:
		var result := []
		for item in value: result.append(_normal(item))
		return result
	return value

func _fail(message: String) -> void:
	failure = message
	_finish(false)

func _finish(success: bool) -> void:
	_release()
	var report := {"schema":1,"kind":"actual-staged-native-traversal-input","complete":success,"failure":failure,
		"preview":preview,"fps":FPS,"expected_frames":PREVIEW_FRAMES if preview else FULL_FRAMES,"width":capture_size.x,"height":capture_size.y,
		"physics_hz":Engine.physics_ticks_per_second,"take_physics_ticks":take_ticks,"take_start_tick":take_start_tick,
		"source_sha256":sources,"imports":imports,"frames":frames,"stills":stills,"input_schedule":inputs,"events":events,
		"outcomes":{"grapple":saw_grapple,"flight":saw_flight,"visible_rope":saw_rope,"pose_overlay":saw_overlay,"pose_finite":pose_finite,"maximum_speed":max_speed,"minimum_energy":min_energy},
		"army_staging":army_staging,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),
		"display":DisplayServer.get_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started_ms,
		"scope":"Actual sequential software-rendered scene frames driven by injected Godot Input actions. Only spawn/camera were staged before the take. This is not human OS input, realtime performance, online play, or final visual acceptance. Video is silent; army still uses a separately documented simulation advance."}
	if is_instance_valid(scene): report["world_build"] = _normal(scene.get_build_report())
	var file := FileAccess.open(output_path.path_join("traversal-render-review.json"),FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(report,"\t") + "\n")
	if not success: push_error(failure)
	quit(0 if success else 1)
