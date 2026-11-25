extends SceneTree
## Enter the actual Hanuman trial through its launcher and measure the footprint.

const BOOT := "res://scenes/boot.tscn"
const COURT := "res://scenes/courtyard.tscn"
const TRIAL := "res://scenes/hanuman_trial.tscn"
const Shadow = preload("res://scripts/hanuman_contact_shadow.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var destination := ""
var capture_directory := ""
var captures: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): destination = arg.trim_prefix("--report=")
		if arg.begins_with("--capture="): capture_directory = arg.trim_prefix("--capture=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name": label, "passed": passed, "details": details})

func _scene(path: String) -> bool:
	var deadline := Time.get_ticks_msec() + 120000
	while true:
		var loader := root.get_node_or_null("YugaSceneTransitionLayer/SceneTransition")
		if is_instance_valid(current_scene) and current_scene.scene_file_path == path \
				and (loader == null or not loader.visible):
			return true
		if Time.get_ticks_msec() >= deadline:
			return false
		await process_frame
	return false

func _ticks(count: int) -> void:
	for unused in range(count):
		await physics_frame

func _opacity(shadow: MeshInstance3D) -> float:
	return float(shadow.material_override.get_shader_parameter("opacity"))

func _capture(shadow: MeshInstance3D, visible: bool, filename: String) -> bool:
	shadow.visible = visible
	await RenderingServer.frame_post_draw
	var path := capture_directory.path_join(filename)
	if root.get_texture().get_image().save_png(path) != OK:
		return false
	captures.append({"file": filename, "sha256": FileAccess.get_sha256(path),
		"contact_visible": visible, "camera": str(root.get_camera_3d().global_transform),
		"floorpoint_px": str(root.get_camera_3d().unproject_position(shadow.global_position))})
	return true

func _run() -> void:
	change_scene_to_file(BOOT)
	if not await _scene(COURT):
		_record("Boot loads the real courtyard launcher", false)
		_finish()
		return
	var shell: Control = current_scene.main_panel
	shell.hanuman_mode_button.pressed.emit()
	shell.primary_button.pressed.emit()
	if not await _scene(TRIAL):
		_record("Hanuman launcher option loads the real trial", false)
		_finish()
		return
	var trial := current_scene
	var hero: CharacterBody3D = trial.hero
	var shadow := trial.get_node_or_null("HanumanContactShadow") as MeshInstance3D
	var sun := trial.get_node_or_null("SettingSun") as DirectionalLight3D
	_record("Normal boot and Hanuman selection mount one trial footprint",
			trial.ready_for_play and trial.paused and shadow != null)
	if shadow == null or hero == null or sun == null:
		_finish()
		return

	var preferences := Bindings.read_config(Bindings.SAVE_PATH)
	var setting: Variant = preferences.config.get_value("video", "shadows", true) if preferences.ok else true
	var expected_sun := bool(setting) if setting is bool else true
	_record("Native shadow preference is honored by the Hanuman trial",
			sun.shadow_enabled == expected_sun, {"sun_enabled": sun.shadow_enabled})
	sun.shadow_enabled = true
	var casters := hero.find_children("*", "MeshInstance3D", true, false).filter(
			func(node: MeshInstance3D): return node.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
	await _ticks(6)
	var sun_opacity := _opacity(shadow)
	_record("Single grounded preview preserves real sun and hero casters",
			shadow.visible and casters.size() > 0 and shadow.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			and is_equal_approx(sun_opacity, Shadow.SUN_CONTACT_OPACITY),
			{"actors_casting": casters.size(), "opacity": sun_opacity, "floor_offset_m": shadow.position.y})

	var begin := trial.find_child("BeginPractice", true, false) as Button
	begin.pressed.emit()
	await _ticks(9)
	_record("Begin practice reaches the actual active hero and following camera",
			not trial.paused and hero.active and hero.camera.current and hero.is_on_floor() and shadow.visible)

	if not capture_directory.is_empty():
		if DisplayServer.get_name() == "headless":
			_record("Image capture requires a graphics display", false)
			_finish()
			return
		hero.turn_camera(Vector2(0, 48))
		await _ticks(3)
		hero.set_paused(true)
		shadow.set_physics_process(false)
		var a := await _capture(shadow, true, "grounded-contact.png")
		var b := await _capture(shadow, false, "grounded-control.png")
		_record("Matched native gameplay images save with and without the contact footprint", a and b)
		_finish()
		return

	var before := hero.global_position
	Input.action_press("move_forward")
	await _ticks(12)
	Input.action_release("move_forward")
	await _ticks(5)
	_record("The footprint follows actual movement on the limestone",
			before.distance_to(hero.global_position) > .15 and shadow.visible
			and Vector2(hero.position.x, hero.position.z).distance_to(Vector2(shadow.position.x, shadow.position.z)) < .01)

	Input.action_press("jump")
	await _ticks(2)
	Input.action_release("jump")
	var faded := false
	var hidden_at_height := false
	var max_height := 0.0
	for frame in range(57):
		await physics_frame
		max_height = maxf(max_height, hero.position.y)
		faded = faded or (hero.position.y > .22 and shadow.visible and _opacity(shadow) < sun_opacity * .9)
		hidden_at_height = hidden_at_height or (hero.position.y > Shadow.MAX_LIFT_M and not shadow.visible)
	_record("Actual jump softens and hides the patch, then restores it at landing",
			faded and hidden_at_height and hero.is_on_floor() and shadow.visible, {"peak_y_m": max_height})

	sun.shadow_enabled = false
	await _ticks(3)
	_record("Disabling the sun shadow selects one stronger fallback under the feet",
			shadow.visible and is_equal_approx(_opacity(shadow), Shadow.FALLBACK_CONTACT_OPACITY)
			and shadow.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF,
			{"opacity": _opacity(shadow)})
	sun.shadow_enabled = true
	hero.set_paused(true)
	hero.reset_at(Vector3(21.85, .06, 2))
	await _ticks(4)
	_record("The circular envelope shrinks to stay inside the actual paving edge",
			shadow.visible and shadow.position.x + maxf(shadow.scale.x, shadow.scale.z) < 22.0,
			{"extent_x_m": shadow.position.x + maxf(shadow.scale.x, shadow.scale.z)})
	hero.reset_at(Vector3(22.25, .06, 2))
	await _ticks(3)
	_record("Outside the known receiver the footprint is hidden", not shadow.visible)

	var step := StaticBody3D.new()
	step.position = Vector3(0, .25, 9)
	var top := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(2, .5, 2)
	top.shape = box
	step.add_child(top)
	trial.add_child(step)
	hero.reset_at(Vector3(0, .52, 9))
	await _ticks(4)
	_record("A raised fixture above the limestone never receives the flat shadow", not shadow.visible)
	step.queue_free()
	hero.set_paused(false)
	var reset := InputEventAction.new()
	reset.action = &"reset_training"
	reset.pressed = true
	Input.parse_input_event(reset)
	await _ticks(5)
	_record("The normal reset restores one footprint at the trial spawn",
			shadow.visible and absf(shadow.position.z - 9) < .01
			and trial.find_children("HanumanContactShadow", "MeshInstance3D", true, false).size() == 1)

	var back := trial.find_child("ReturnToTitle", true, false) as Button
	back.pressed.emit()
	var returned := await _scene(COURT)
	_record("Returning to title releases the trial footprint", returned and not is_instance_valid(shadow))
	_finish()

func _finish() -> void:
	var failures := checks.filter(func(row: Dictionary): return not row.passed)
	var sources := {}
	for path in [get_script().resource_path, "res://scripts/hanuman_contact_shadow.gd",
			"res://shaders/hanuman_contact_shadow.gdshader", "res://scripts/hanuman_trial.gd",
			"res://assets/environment/lanka_courtyard.glb", "res://assets/heroes/hanuman/hanuman.glb"]:
		sources[path] = FileAccess.get_sha256(path)
	var result := {"passed": checks.size() - failures.size(), "failed": failures.size(), "checks": checks,
		"captures": captures, "renderer": RenderingServer.get_current_rendering_method(),
		"display": DisplayServer.get_name(), "sources": sources}
	if not destination.is_empty():
		var file := FileAccess.open(destination, FileAccess.WRITE)
		file.store_string(JSON.stringify(result, "\t") + "\n")
	print("YUGA_HANUMAN_CONTACT " + JSON.stringify(result))
	quit(0 if failures.is_empty() else 1)
