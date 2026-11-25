extends SceneTree
## Inspect the actual time atlas, then trigger it through the launcher and trial.

const Field = preload("res://scripts/hanuman_ground_field.gd")
const COURTYARD := "res://scenes/courtyard.tscn"
const TRIAL := "res://scenes/hanuman_trial.tscn"
const SECTOR := {"kind": "sector", "origin": Vector3(1, 0, 2), "forward": Vector3.LEFT,
		"range_m": 5.0, "half_angle_cos": .15}
const DISK := {"kind": "disk", "center": Vector3(1, 0, 1), "forward": Vector3.FORWARD, "radius_m": 7.0}

var _checks: Array[Dictionary] = []
var _buffers: Dictionary = {}
var _events: Array[Dictionary] = []
var _capture_path := ""


func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture="):
			_capture_path = argument.trim_prefix("--capture=")
	call_deferred("_run")


func _assert(label: String, passed: bool) -> void:
	_checks.append({"name": label, "passed": passed})
	if not passed:
		printerr("FAIL ", label)


func _pixel(field: MultiMeshInstance3D, slot: int, local: Vector2) -> Color:
	var cell := ((local * .5 + Vector2(.5, .5)) * float(Field.SIDE)).floor()
	return field._atlas.get_pixel(int(cell.x), slot * Field.SIDE + int(cell.y))




func _transform(field: MultiMeshInstance3D, instance: int) -> Transform3D:
	# Dummy rendering has no MultiMesh buffer readback.
	return field._fields[instance].transform if DisplayServer.get_name() == "headless" else field.multimesh.get_instance_transform(instance)


func _fixture() -> void:
	var field := Field.new()
	root.add_child(field)
	var material: Material = field.material_override
	var texture: Texture2D = material.get_shader_parameter("time_field")
	var mesh: Mesh = field.multimesh.mesh
	_assert("one reusable batch and RG32F atlas have exactly three bounded slots",
		field.multimesh.instance_count == Field.CAPACITY and Field.CAPACITY == 3 and
		texture.get_width() == 96 and texture.get_height() == 288 and
		field._atlas.get_format() == Image.FORMAT_RGF and field.report().texture_bytes == 221184 and
		mesh.get_aabb().size.is_equal_approx(Vector3(2, 0, 2)) and not field.visible)
	_assert("sector mold stamps only once and locks its origin, exact radius and rear heading",
		field.stamp(11, SECTOR, .70, Color.RED) and not field.stamp(11, SECTOR, .70, Color.RED) and
		_transform(field, 0).origin.is_equal_approx(SECTOR.origin + Vector3.UP * Field.GROUND_OFFSET) and
		_transform(field, 0).basis.z.is_equal_approx(SECTOR.forward * SECTOR.range_m))
	var inner := _pixel(field, 0, Vector2(0, .15))
	var outer := _pixel(field, 0, Vector2(0, .83))
	_assert("near and far ember locations store separate arrival times and one common expiry",
		inner.r > 0 and outer.r > inner.r + .05 and is_equal_approx(inner.r + inner.g, .70) and
		is_equal_approx(outer.r + outer.g, .70))
	_assert("outside wedge, outer corner and unused slots store no active timestamp",
		_pixel(field, 0, Vector2(0, -.5)).g == 0.0 and _pixel(field, 0, Vector2(.5, .02)).g == 0.0 and
		_pixel(field, 0, Vector2(.9, .9)).g == 0.0 and _pixel(field, 1, Vector2(0, 0)).g == 0.0)
	var before: PackedByteArray = field._atlas.get_data()
	field.advance(.22)
	_assert("clock advances without rebuilding mesh, material, texture or atlas data",
		is_equal_approx(material.get_shader_parameter("clock_s"), .22) and field.report().texture_updates == 1 and
		field._atlas.get_data() == before and material == field.material_override and texture == material.get_shader_parameter("time_field") and
		mesh == field.multimesh.mesh)
	_assert("overlapping disk starts later and retains its own round footprint",
		field.stamp(12, DISK, .92, Color.GOLD) and field.report().active == 2 and
		_pixel(field, 1, Vector2(0, -.55)).r > .22 and _pixel(field, 1, Vector2(.85, .84)).g == 0.0 and
		_pixel(field, 0, Vector2(0, .83)).is_equal_approx(outer))
	_assert("third overlapping disk can reuse renderer while a fourth is bounded",
		field.stamp(13, DISK, .92, Color.WHEAT) and not field.stamp(14, DISK, .92, Color.WHEAT) and
		field.report().visible_instances == 3 and field.report().texture_updates == 3)
	field.retire(12)
	_assert("cancel clears only the named overlapping field and compacts visible instances",
		field.report().active == 2 and _pixel(field, 1, Vector2(0, 0)).g == 0.0 and
		_pixel(field, 2, Vector2(0, 0)).g > 0.0 and field._fields[1].slot == 2 and (DisplayServer.get_name() == "headless" or int(field.multimesh.get_instance_custom_data(1).r) == 2))
	_assert("retrigger rewrites a reclaimed slot with a later time",
		field.stamp(14, DISK, .62, Color.GOLD) and _pixel(field, 1, Vector2(0, 0)).r > inner.r and
		is_equal_approx(_pixel(field, 1, Vector2(0, 0)).r + _pixel(field, 1, Vector2(0, 0)).g, .84))
	field.set_reduced(true)
	_assert("reduced effects hide the batch and reject extra decorative stamps",
		not field.visible and field.report().visible_instances == 0 and not field.stamp(15, DISK, .5, Color.WHITE))
	field.advance(.64)
	field.set_reduced(false)
	_assert("exposure expires while hidden without clearing the still-live overlapping entry",
		field.report().active == 1 and field.report().visible_instances == 1 and
		_pixel(field, 0, Vector2(0, .15)).g == 0.0 and _pixel(field, 1, Vector2(0, 0)).g == 0.0)
	field.advance(.30)
	_assert("last natural expiry clears the atlas and resets the reusable local clock",
		field.report().active == 0 and not field.visible and field.multimesh.visible_instance_count == 0 and
		_pixel(field, 2, Vector2(0, 0)).g == 0.0 and field.report().clock_s == 0.0)
	field.stamp(19, SECTOR, .7, Color.RED)
	field.clear()
	_assert("explicit reset clears slot contents and reuses original material and atlas",
		field.report().active == 0 and _pixel(field, 0, Vector2(0, .3)).g == 0.0 and
		texture == material.get_shader_parameter("time_field"))
	_buffers = field.report()
	field.free()


func _scene(path: String) -> bool:
	var deadline := Time.get_ticks_msec() + 45000
	while not is_instance_valid(current_scene) or current_scene.scene_file_path != path:
		if Time.get_ticks_msec() >= deadline:
			return false
		await process_frame
	return true


func _step(trial: Node, count: int) -> void:
	for i in count:
		trial.army.step_simulation()


func _input_ability(trial: Node, action: StringName) -> void:
	var input := InputEventAction.new()
	input.action = action
	input.pressed = true
	trial._unhandled_input(input)


func _practice() -> void:
	root.size = Vector2i(960, 600)
	root.content_scale_size = root.size
	change_scene_to_file(COURTYARD)
	var opened := await _scene(COURTYARD)
	if not opened:
		_assert("actual courtyard launcher loaded", false)
		return
	var launcher: Control = current_scene.main_panel
	launcher.hanuman_mode_button.pressed.emit()
	launcher.primary_button.pressed.emit()
	opened = await _scene(TRIAL)
	_assert("actual launcher opens the dedicated, imported Hanuman court", opened and current_scene.ready_for_play)
	if not opened or not current_scene.ready_for_play:
		return
	var trial := current_scene
	var field: MultiMeshInstance3D = trial.effects._ground_field
	trial.effects.set_process(false)
	trial.army.set_physics_process(false)
	trial.combat.ability_event.connect(func(event): _events.append(event))
	trial._resume.pressed.emit()
	for i in 12:
		await physics_frame
	_input_ability(trial, &"guardian_circle")
	_step(trial, 8)
	_assert("real rear ability windup has an exterior warning and no painted ground",
		_events.size() == 1 and _events[0].kind == "begin" and field.report().active == 0)
	_step(trial, 1)
	var ember: Dictionary = _events.back() if not _events.is_empty() else {}
	_assert("real rear impact writes the authoritative anchored sector once",
		ember.get("ability_id") == "lanka_dahan" and ember.get("kind") == "impact" and
		field.report().active == 1 and field.report().texture_updates == 1 and
		_transform(field, 0).basis.z.normalized().is_equal_approx(ember.geometry.forward))
	_assert("duplicate impact and accepted exposure ticks do not repeat the upload",
		not trial.effects.consume_event(ember) and field.report().texture_updates == 1)
	_step(trial, 4)
	_assert("active exposure ticks never restamp", _events.back().kind == "tick" and field.report().texture_updates == 1)
	trial.effects._process(.125)
	trial._set_paused(true)
	trial.effects._process(.250)
	_assert("real practice pause freezes the shared shader clock", is_equal_approx(field.report().clock_s, .125))
	trial._set_paused(false)
	trial._reset_trial()
	_assert("real trial reset clears the old generation and stale impact cannot repaint",
		field.report().active == 0 and not trial.effects.consume_event(ember))
	for i in 12:
		await physics_frame
	_events.clear()
	# An ordinary admitted aim is still resolved by the actor ray/projection.
	trial.hero.turn_camera(Vector2(0, 55))
	_input_ability(trial, &"ultimate")
	_step(trial, 22)
	var release: Dictionary = _events.back() if not _events.is_empty() else {}
	_assert("actual Mountain Pulse position is locked through release and travel with no ground stamp",
		release.get("ability_id") == "mountain_pulse" and release.get("kind") == "release" and field.report().active == 0)
	_step(trial, 1)
	var mountain: Dictionary = _events.back() if not _events.is_empty() else {}
	_assert("actual Mountain Pulse impact paints a new disk on its real ground target",
		mountain.get("kind") == "impact" and mountain.get("ability_id") == "mountain_pulse" and field.report().active == 1 and
		_transform(field, 0).origin.is_equal_approx(mountain.geometry.center + Vector3.UP * Field.GROUND_OFFSET) and
		_pixel(field, 0, Vector2(0, -.5)).g > 0.0)
	if not _capture_path.is_empty() and DisplayServer.get_name() != "headless":
		trial.effects._process(.24)
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		_assert("a rendered Mountain Pulse frame is captured with the active time field",
			root.get_texture().get_image().save_png(_capture_path) == OK and field.report().visible_instances == 1)
	_step(trial, 10)
	_assert("authority end removes the visual even with no display-frame advance", field.report().active == 0 and _events.back().kind == "end")


func _run() -> void:
	_fixture()
	await _practice()
	var passed := _checks.filter(func(check): return check.passed).size()
	var report := {"passed": passed, "failed": _checks.size() - passed, "checks": _checks,
		"fixture_buffers": _buffers, "event_count": _events.size(),
		"display_driver": DisplayServer.get_name(), "multi_mesh_readback": DisplayServer.get_name() != "headless",
		"script_sha256": FileAccess.get_sha256("res://scripts/hanuman_ground_field.gd"),
		"shader_sha256": FileAccess.get_sha256("res://shaders/hanuman_ground_field.gdshader")}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var output := FileAccess.open(argument.trim_prefix("--report="), FileAccess.WRITE)
			if output != null:
				output.store_string(JSON.stringify(report, "  ") + "\n")
	print("YUGA_HANUMAN_GROUND_FIELD ", JSON.stringify(report))
	quit(0 if passed == _checks.size() else 1)
