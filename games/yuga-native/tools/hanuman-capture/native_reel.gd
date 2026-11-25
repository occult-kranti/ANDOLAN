extends SceneTree
## Sequential real-render samples from a recorded input plan using the Hanuman
## trial's own player, collision, ability clock, effects and tail modifier.

const SPEC := "res://tools/hanuman-capture/native-storyboard.json"
const TRIAL := "res://scenes/hanuman_trial.tscn"
const ACTIONS := ["move_forward", "move_back", "move_left", "move_right", "fire", "pulse", "dash", "guardian_circle", "ultimate"]

var output: String
var trial: Node3D
var events: Array[Dictionary] = []
var receipt: Dictionary = {}
var release_next: Array[String] = []
var simulate_only := false


func _initialize() -> void:
	call_deferred("_render")


func _render() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output = arg.trim_prefix("--output=")
		elif arg == "--simulate-only":
			simulate_only = true
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output) or (not simulate_only and DisplayServer.get_name() == "headless"):
		push_error("Choose a fresh absolute directory and a real display for the reel.")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SPEC))
	var size := Vector2i(int(plan.size[0]), int(plan.size[1]))
	var fps := int(plan.fps)
	var total := int(plan.frame_count)
	var steps: Dictionary = {}
	for item: Dictionary in plan.steps:
		steps.get_or_add(int(item.frame), []).append(item)
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
		"renderer": RenderingServer.get_current_rendering_method(),
	}
	for path in [SPEC, TRIAL, "res://project.godot", "res://assets/heroes/hanuman/hanuman.glb", "res://assets/design/hanuman-ability-kit.json", "res://assets/design/hanuman-presentation.json", "res://assets/design/hanuman-tail-response.json", "res://scripts/hanuman_trial.gd", "res://scripts/hanuman_actor.gd", "res://scripts/hanuman_trial_effects.gd", "res://scripts/hanuman_combat.gd", "res://scripts/hero_chain_response.gd", "res://tools/hanuman-capture/native_reel.gd"]:
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
	for index in 4:
		await process_frame
		if not simulate_only: await RenderingServer.frame_post_draw
	for frame in total:
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
		var actor: Dictionary = trial.hero.report()
		var row := {"frame": frame, "physics_frame": Engine.get_physics_frames(),
			"actor": actor, "phase": trial.combat.report(false).phase, "effects": trial.effects.report()}
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
	var impacted: Dictionary = {}
	for event in events:
		if event.kind == "impact": impacted[event.ability_id] = true
	_finish(impacted.size() == 5, "" if impacted.size() == 5 else "The input plan missed an ability impact.")


func _send(action: String, pressed: bool) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = pressed
	event.strength = 1.0 if pressed else 0.0
	Input.parse_input_event(event)


func _record(event: Dictionary) -> void:
	if event.kind != "tick":
		events.append(event.duplicate(true))


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
