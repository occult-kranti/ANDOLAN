extends SceneTree
## Exercises exact imported presentation geometry and recipient-only cues.
const Effects = preload("res://scripts/hanuman_trial_effects.gd")
var effects: Node3D
var checks: Array[Dictionary] = []
var seq := 0
var cast_id := 0
var current: Dictionary
const ORIGIN := Vector3(2.5, 0, -1)
const LANDING := Vector3(1.5, 0, -6)

func _initialize() -> void:
	call_deferred("_run")

func _record(name_: String, passed: bool) -> void:
	checks.append({"name": name_, "passed": passed})
	if not passed:
		printerr("FAIL ", name_)

func _begin(ability: String, geometry: Dictionary, travel: float = 0.0, active: float = 0.0) -> bool:
	cast_id += 1
	current = {"schema": 1, "hero_id": "hanuman", "ability_id": ability, "generation": 1, "cast_id": cast_id,
		"timing": {"windup_s": .4, "travel_s": travel, "recovery_s": .4, "active_s": active}, "geometry": geometry.duplicate(true)}
	return _event("begin")

func _event(kind: String, receipts: Array = []) -> bool:
	seq += 1
	var event := current.duplicate(true)
	event.kind = kind
	event.event_seq = seq
	event.receipts = receipts
	return effects.consume_event(event)

func _cue() -> Node3D:
	return effects.get_node_or_null("Cue%d" % cast_id) as Node3D

func _end() -> bool:
	return _event("recovery") and _event("end")

func _run() -> void:
	effects = Effects.new()
	root.add_child(effects)
	effects.set_process(false)
	var sector := {"kind": "sector", "origin": ORIGIN, "center": ORIGIN, "forward": Vector3.BACK, "range_m": 5.0, "half_angle_cos": .15}
	_record("rear warning accepts authoritative bounds", _begin("lanka_dahan", sector, 0.0, 2.0) and _cue().get_child_count() == 3)
	_record("rear sweep release and valid hit", _event("release") and _event("impact"))
	var rear := _cue().get_node_or_null("EmberField") as Node3D
	var projected := true
	var height := 0.0
	if rear != null:
		for layer in rear.get_children():
			var node := layer as MeshInstance3D
			var points: PackedVector3Array = node.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
			for point in points:
				var xz := Vector2(point.x, point.z)
				projected = projected and xz.length() <= 5.00001 and xz.normalized().y >= .14999
				height = maxf(height, point.y)
	_record("two rising ribbons stay inside the exact rear sector", rear != null and rear.get_child_count() == 2 and height >= 1.5 and projected)
	effects._process(.3)
	_record("timestamp ground wash is visible without a third per-cast mesh",
		effects.report().ground_field.visible_instances == 1 and rear.get_child_count() == 2)
	effects.set_options({"reduced_effects": true})
	effects._process(.05)
	_record("reduced effects retain three locked ground boundary meshes and hide tall amber field",
		rear != null and not rear.visible and effects.report().ground_field.visible_instances == 0 and _cue().get_child(0).visible and _cue().get_child(1).visible and _cue().get_child(2).visible)
	_record("completed rear cue retires", _end() and not _cue().visible)
	effects.set_options({"reduced_effects": false})

	var disk := {"kind": "disk", "origin": ORIGIN, "center": LANDING, "forward": Vector3.FORWARD, "radius_m": 7.0}
	var initial_cues: int = effects.report().audio_cues
	_record("mountain begins with only disk", _begin("mountain_pulse", disk, .45) and _cue().get_child_count() == 1)
	var mountain := _cue()
	_record("mountain crest appears on release at locked landing", _event("release") and mountain.global_position.is_equal_approx(LANDING))
	var payload := mountain.get_node_or_null("MountainPayload") as Node3D
	var old_y := payload.position.y if payload != null else -1.0
	effects._process(.225)
	var mid_y := payload.position.y if payload != null else -1.0
	_record("3D crest moves downward during accepted travel", old_y > 4.0 and mid_y < old_y - .8 and mid_y > 2.5)
	effects.set_suspended(true)
	effects._process(.35)
	_record("paused crest does not slide", payload != null and is_equal_approx(payload.position.y, mid_y))
	effects.set_suspended(false)
	effects._process(.225)
	_record("presentation never lands before impact event", payload != null and payload.visible and payload.position.y > .18 and mountain.get_node_or_null("MountainImpact") == null)
	_record("impact swaps crest for five vertical shards and one spatial landing cue",
		_event("impact") and not payload.visible and mountain.get_node_or_null("MountainImpact") != null
		and mountain.get_node("MountainImpact").get_child_count() == 5 and effects.report().audio_cues == initial_cues + 2)
	_record("mountain audio uses casting and landing locations", _voice_at(ORIGIN) and _voice_at(LANDING))
	_record("one accepted mount impact", not _event("impact") and _end())

	var before_ward: int = effects.report().audio_cues
	_record("ward release only draws selection fan", _begin("vajra_kavacha", sector) and _event("release") and _cue().get_node_or_null("ShieldReceipt") == null)
	var empty_ward := _cue()
	_record("ward never substitutes a shield for other receipts", _event("impact", [{"position": ORIGIN, "effects": ["heal"], "shield_after": 48.0}])
		and empty_ward.get_node_or_null("ShieldReceipt") == null and effects.report().audio_cues == before_ward + 1 and _end())
	var ally := ORIGIN + Vector3.BACK * 2.0
	var receipts := [{"position": ally, "effects": ["shield"], "shield_after": 48.0}, {"position": ORIGIN, "effects": ["shield"], "shield_after": 48.0}]
	_record("real shield receipts fire bounded cue and distinct marks", _begin("vajra_kavacha", sector) and _event("release") and _event("impact", receipts))
	var ward_count := 0
	var is_shield_at_ally := false
	for child in _cue().get_children():
		if not String(child.name).begins_with("ShieldReceipt"):
			continue
		ward_count += 1
		is_shield_at_ally = is_shield_at_ally or (child as Node3D).global_position.is_equal_approx(ally)
	_record("two real shields get individual lattices with one confirmation voice", ward_count == 2 and is_shield_at_ally and _voice_at(ally)
		and effects.report().audio_cues == before_ward + 3 and _end())

	effects.set_options({"reduced_motion": true})
	_record("reduced mountain keeps locked disk and reactive sound without moving crest or spires",
		_begin("mountain_pulse", disk, .45) and _event("release") and _event("impact") and _cue().get_node_or_null("MountainPayload") == null
		and _cue().get_node_or_null("MountainImpact") == null and _cue().get_child_count() == 3 and _end())
	await process_frame
	await process_frame
	_record("cue cleanup retains three pooled audio voices", effects.report().active == 0 and effects.get_child_count() == 3)
	var passed := checks.filter(func(check): return check.passed).size()
	var result := {"passed": passed, "failed": checks.size() - passed, "checks": checks,
		"effects_sha256": FileAccess.get_sha256("res://scripts/hanuman_trial_effects.gd"),
		"profile_sha256": FileAccess.get_sha256("res://assets/design/hanuman-presentation.json")}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var out := FileAccess.open(argument.trim_prefix("--report="), FileAccess.WRITE)
			if out != null:
				out.store_string(JSON.stringify(result, "  ") + "\n")
	print("YUGA_HANUMAN_PRESENTATION ", JSON.stringify(result))
	effects.free()
	await create_timer(.25).timeout
	quit(0 if passed == checks.size() else 1)

func _voice_at(point: Vector3) -> bool:
	for voice in effects.get_children():
		if voice is AudioStreamPlayer3D and voice.global_position.is_equal_approx(point):
			return true
	return false
