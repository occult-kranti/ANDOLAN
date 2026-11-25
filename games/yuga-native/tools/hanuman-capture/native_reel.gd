extends SceneTree
## Sequential real-render samples from a recorded input plan using the Hanuman
## trial's own player, collision, ability clock, effects and tail modifier.

const SPEC := "res://tools/hanuman-capture/native-storyboard.json"
const TRIAL := "res://scenes/hanuman_trial.tscn"
const ACTIONS := ["move_forward", "move_back", "move_left", "move_right", "reset_training", "fire", "pulse", "dash", "guardian_circle", "ultimate"]
const ABILITIES := ["vajra_gada", "vajra_kavacha", "maruti_udayana", "lanka_dahan", "mountain_pulse"]
const REQUIRED_BEATS := ["begin", "release", "impact", "recovery", "end"]
const RUNTIME_SOURCES := [TRIAL, "res://project.godot", "res://assets/heroes/hanuman/hanuman.glb",
	"res://assets/heroes/hanuman/hanuman-ability-motion.tres", "res://assets/vfx/hanuman-invocation-masks.png",
	"res://assets/audio/rama-quality/confirm.wav",
	"res://assets/environment/lanka_courtyard.glb", "res://assets/design/hanuman-ability-kit.json",
	"res://assets/design/hanuman-presentation.json", "res://assets/design/hanuman-tail-response.json",
	"res://scripts/hanuman_trial.gd", "res://scripts/hanuman_actor.gd", "res://scripts/hanuman_trial_effects.gd",
	"res://scripts/hanuman_combat.gd", "res://scripts/hanuman_ground_field.gd", "res://scripts/hero_chain_response.gd",
	"res://scripts/hanuman_invocation_art.gd", "res://scripts/hanuman_contact_shadow.gd",
	"res://shaders/hanuman_ground_field.gdshader", "res://shaders/hanuman_contact_shadow.gdshader",
	"res://tools/hanuman-capture/native_reel.gd", "res://tools/hanuman-capture/encode_reel.py"]

var output: String
var trial: Node3D
var events: Array[Dictionary] = []
var receipt: Dictionary = {}
var release_next: Array[String] = []
var simulate_only := false
var storyboard := SPEC
var sample_frame := -1
var capture_camera: Camera3D
var shot: Dictionary


func _initialize() -> void:
	call_deferred("_render")


func _render() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output = arg.trim_prefix("--output=")
		elif arg.begins_with("--storyboard="):
			storyboard = arg.trim_prefix("--storyboard=")
		elif arg == "--simulate-only":
			simulate_only = true
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output) or (not simulate_only and DisplayServer.get_name() == "headless"):
		push_error("Choose a fresh absolute directory and a real display for the reel.")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(storyboard))
	if not parsed is Dictionary:
		push_error("The capture storyboard is missing or invalid.")
		quit(1)
		return
	var plan: Dictionary = parsed
	var size := Vector2i(int(plan.size[0]), int(plan.size[1]))
	var fps := int(plan.fps)
	var total := int(plan.frame_count)
	var steps: Dictionary = {}
	var shots: Dictionary = {}
	for item: Dictionary in plan.steps:
		steps.get_or_add(int(item.frame), []).append(item)
	for item: Dictionary in plan.get("shots", []):
		shots[int(item.frame)] = item
	if fps < 8 or fps > 30 or Engine.get_write_movie_path() != "" or total < fps or total > fps * 30:
		push_error("Use a bounded recorded input plan and the FPS it declares.")
		quit(1)
		return
	root.size = size
	root.content_scale_size = Vector2i(1280, 720)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.title = "YUGA — Hanuman motion and effects"
	root.show()
	receipt = {
		"complete": false, "frames": [], "fps": fps, "size": [size.x, size.y],
		"scope": "Headless input plan rehearsal" if simulate_only else "Rendered native trial with scripted input playback at fixed simulation cadence",
		"source_sha256": {}, "events": events,
		"renderer": RenderingServer.get_current_rendering_method(), "renderer_device": RenderingServer.get_video_adapter_name(),
		"godot_version": Engine.get_version_info().string,
		"physics_ticks_per_second": Engine.physics_ticks_per_second, "storyboard": storyboard,
		"capture_cameras": plan.get("shots", []), "audio_recorded": false,
	}
	var sources := [storyboard] + RUNTIME_SOURCES
	for id in ABILITIES + ["mountain_impact"]:
		sources.append("res://assets/audio/hanuman-trial/%s.wav" % id)
	for path in sources:
		if FileAccess.file_exists(path):
			receipt.source_sha256[path] = FileAccess.get_sha256(path)
	trial = (load(TRIAL) as PackedScene).instantiate()
	root.add_child(trial)
	current_scene = trial
	if not trial.ready_for_play:
		_finish(false, "The exact Hanuman trial was unavailable.")
		return
	trial.combat.ability_event.connect(_record)
	# The video captures graphics only. This also keeps headless fixed-step
	# rehearsals independent of the asynchronous Dummy audio mixer.
	trial.effects.set_options({"volume": 0.0})
	trial._set_paused(false)
	if not shots.is_empty():
		capture_camera = Camera3D.new()
		capture_camera.name = "ReelCamera"
		capture_camera.near = .08
		capture_camera.far = 125.0
		root.add_child(capture_camera)
	for index in 4:
		await process_frame
		if not simulate_only: await RenderingServer.frame_post_draw
	for frame in total:
		sample_frame = frame
		if shots.has(frame): shot = shots[frame]
		for action in release_next:
			_send(action, false)
		release_next.clear()
		for item: Dictionary in steps.get(frame, []):
			if item.has("look"):
				trial.hero.turn_camera(Vector2(item.look[0], item.look[1]))
			else:
				var action := String(item.action)
				if action not in ACTIONS:
					_finish(false, "Unknown recorded action " + action)
					return
				_send(action, item.get("pressed", true))
				if not item.has("pressed"):
					release_next.append(action)
		Input.flush_buffered_events()
		await process_frame
		if not shot.is_empty(): _stage_camera(shot)
		var actor: Dictionary = trial.hero.report()
		var row := {"frame": frame, "physics_frame": Engine.get_physics_frames(),
			"actor": actor, "phase": trial.combat.report(false).phase, "effects": trial.effects.report()}
		if not shot.is_empty():
			var hero_feet := capture_camera.unproject_position(trial.hero.global_position)
			var hero_head := capture_camera.unproject_position(trial.hero.socket_world(&"head"))
			row["shot"] = shot.ability
			row["hero_feet_px"] = [hero_feet.x, hero_feet.y]
			row["hero_head_px"] = [hero_head.x, hero_head.y]
		if not simulate_only:
			await RenderingServer.frame_post_draw
			var file := "frame-%05d.png" % frame
			var path := output.path_join(file)
			var image := root.get_texture().get_image()
			if image.is_empty() or image.get_size() != size or image.save_png(path) != OK:
				_finish(false, "The renderer did not produce the expected framebuffer.")
				return
			row.file = file
			row.sha256 = FileAccess.get_sha256(path)
		receipt.frames.append(row)
		if frame % 16 == 0:
			_write()
	var missing := _verify_beats(not shots.is_empty(), fps)
	_finish(missing.is_empty(), missing)


func _stage_camera(config: Dictionary) -> void:
	var forward: Vector3 = trial.hero.aim_forward()
	if config.has("heading_degrees"):
		forward = Basis(Vector3.UP, deg_to_rad(float(config.heading_degrees))) * Vector3.FORWARD
	var right := forward.cross(Vector3.UP)
	var anchor: Vector3 = trial.hero.global_position
	# Keep elevation fixed during most shots. A partial follow leaves room to see the vault's rise.
	anchor.y *= float(config.get("vertical_follow", .1))
	var offset: Array = config.offset
	var aim: Array = config.aim
	var offset_point := Vector3(offset[0], offset[1], offset[2])
	var aim_point := Vector3(aim[0], aim[1], aim[2])
	var fov := float(config.fov)
	if config.has("dolly"):
		var dolly: Dictionary = config.dolly
		var t := smoothstep(float(dolly.frame), float(dolly.frame) + float(dolly.duration_frames), float(sample_frame))
		offset_point = offset_point.lerp(Vector3(dolly.offset[0], dolly.offset[1], dolly.offset[2]), t)
		aim_point = aim_point.lerp(Vector3(dolly.aim[0], dolly.aim[1], dolly.aim[2]), t)
		fov = lerpf(fov, float(dolly.fov), t)
	capture_camera.global_position = anchor + right * offset_point.x + Vector3.UP * offset_point.y + forward * offset_point.z
	capture_camera.fov = fov
	capture_camera.look_at(anchor + right * aim_point.x + Vector3.UP * aim_point.y + forward * aim_point.z)
	capture_camera.current = true


func _verify_beats(extended: bool, fps: int) -> String:
	var beats := {}
	for event in events:
		if event.ability_id in ABILITIES and event.kind in REQUIRED_BEATS:
			beats.get_or_add(event.ability_id, {})[event.kind] = {
				"frame": event.sample_frame, "time_s": float(event.sample_frame) / fps,
				"physics_frame": event.physics_frame, "cast_id": event.cast_id,
				"generation": event.generation,
			}
	receipt["ability_beats"] = beats
	for id in ABILITIES:
		for beat in (REQUIRED_BEATS if extended else ["impact"]):
			if not beats.get(id, {}).has(beat):
				return "The input plan missed %s %s." % [id, beat]
	return ""


func _send(action: String, pressed: bool) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = pressed
	event.strength = 1.0 if pressed else 0.0
	Input.parse_input_event(event)


func _record(event: Dictionary) -> void:
	if event.kind != "tick":
		var copy := event.duplicate(true)
		copy["sample_frame"] = sample_frame
		copy["physics_frame"] = Engine.get_physics_frames()
		events.append(copy)


func _write() -> void:
	var file := FileAccess.open(output.path_join("render.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(receipt, "\t"))


func _finish(success: bool, reason: String) -> void:
	receipt.complete = success
	receipt.reason = reason
	_write()
	var code := 0 if success else 1
	if is_instance_valid(trial):
		trial._set_paused(true)
		trial.queue_free()
		await process_frame
		await create_timer(0.18).timeout
	quit(code)
