extends SceneTree
## Check real presentation nodes and audio dispatch accounting with event
## transcripts. Uses synthetic events to exercise malformed order at receiver.

const Effects = preload("res://scripts/hanuman_trial_effects.gd")
var effects: Node3D
var checks: Array[Dictionary] = []
var terrain := Vector3(2.0, 0.0, -3.0)
var aim := Vector3(.6, 0, -.8)


func _initialize() -> void:
	call_deferred("run")


func sample(kind: String, sequence: int, cast := 12, generation := 5) -> Dictionary:
	return {"schema": 1, "hero_id": "hanuman", "ability_id": "lanka_dahan", "kind": kind,
		"generation": generation, "event_seq": sequence, "cast_id": cast,
		"timing": {"windup_s": .45, "travel_s": 0.0, "active_s": 2.0, "recovery_s": .4},
		"geometry": {"origin": terrain, "center": terrain, "forward": aim, "kind": "sector", "range_m": 5.0, "half_angle_cos": .15},
		"receipts": [], "reason": ""}


func record(label: String, accepted: bool, details: Dictionary = {}) -> void:
	checks.append({"case": label, "passed": accepted, "details": details})
	if not accepted: print("FAIL ", label, ": ", details)


func run() -> void:
	effects = Effects.new()
	root.add_child(effects)
	record("five presentation profiles installed", effects.report().profiles == 5)
	record("begin builds one actual warning group", effects.consume_event(sample("begin", 1)) and effects.report().active == 1)
	var cue := effects.get_node_or_null("Cue12") as Node3D
	if cue != null and cue.get_child_count() == 3:
		var ring := cue.get_child(0) as MeshInstance3D
		var vertices: PackedVector3Array = ring.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
		var direction := cue.global_basis * Vector3.BACK
		var outer_min := INF
		var outer_max := -INF
		var angular_min := INF
		for index in range(1, vertices.size(), 2):
			var radial := Vector3(vertices[index].x, 0.0, vertices[index].z)
			outer_min = minf(outer_min, radial.length())
			outer_max = maxf(outer_max, radial.length())
			angular_min = minf(angular_min, aim.dot(cue.global_basis * radial.normalized()))
		record("warning mesh matches locked origin, radius, and angle",
			cue.global_position.is_equal_approx(terrain) and direction.is_equal_approx(aim)
			and is_equal_approx(outer_min, 5.0) and is_equal_approx(outer_max, 5.0) and is_equal_approx(angular_min, .15),
			{"outer_min": outer_min, "outer_max": outer_max, "angular_min": angular_min})
	else:
		record("warning mesh matches locked origin, radius, and angle", false)
	record("duplicate begin and stale release rejected", not effects.consume_event(sample("begin", 1)) and not effects.consume_event(sample("release", 2, 12, 4)))
	record("impact and end require a valid progression", not effects.consume_event(sample("impact", 2)) and not effects.consume_event(sample("end", 2)))
	var audio_before: int = effects.report().audio_cues
	record("release and impact advance correctly", effects.consume_event(sample("release", 2)) and effects.consume_event(sample("impact", 3)))
	var audio_after: int = effects.report().audio_cues
	var before_ticks: int = cue.get_child_count() if is_instance_valid(cue) else -1
	var ticks_ok := true
	for sequence in range(4, 44):
		ticks_ok = effects.consume_event(sample("tick", sequence)) and ticks_ok
	record("forty burn ticks produce no repeated audio or geometry",
		ticks_ok and audio_after == audio_before + 1 and effects.report().audio_cues == audio_after and is_instance_valid(cue) and cue.get_child_count() == before_ticks,
		{"audio_before": audio_before, "after_release": audio_after, "after_ticks": effects.report().audio_cues})
	record("recovery and end retire the cue", effects.consume_event(sample("recovery", 44)) and effects.consume_event(sample("end", 45)) and effects.report().active == 0 and not cue.visible)
	record("new cast can cancel in anticipation", effects.consume_event(sample("begin", 46, 13)) and effects.consume_event(sample("cancel", 47, 13)) and effects.report().active == 0)
	var cancelled := effects.get_node_or_null("Cue13") as Node3D
	record("cancel hides nodes and prevents late release", cancelled != null and not cancelled.visible and not effects.consume_event(sample("release", 48, 13)))
	await process_frame
	await process_frame
	record("deferred cue deletion leaves no stale dynamic children", effects.get_child_count() == 3)
	record("generation reset rejects delayed prior events", effects.consume_event(sample("reset", 1, 0, 6)) and not effects.consume_event(sample("begin", 49, 14, 5)))
	var missing := sample("begin", 2, 1, 6)
	missing["timing"] = {}
	record("missing timing fails before creating partial state", not effects.consume_event(missing) and effects.report().active == 0 and effects.get_child_count() == 3)
	var status: Dictionary = effects.report()
	var report := {"checks": checks, "passed": checks.all(func(item): return item.passed), "report": status,
		"effect_sha256": FileAccess.get_sha256("res://scripts/hanuman_trial_effects.gd"),
		"profile_sha256": FileAccess.get_sha256("res://assets/design/hanuman-presentation.json"),
		"fixture_sha256": FileAccess.get_sha256(get_script().resource_path)}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path := argument.trim_prefix("--report=")
			var file := FileAccess.open(path, FileAccess.WRITE) if not FileAccess.file_exists(path) else null
			if file == null:
				printerr("Review output path must be writable and fresh: ", path)
				quit(2)
				return
			file.store_string(JSON.stringify(report, "  ") + "\n")
			file.close()
	print("Hanuman effects independent checks: %d/%d" % [checks.filter(func(item): return item.passed).size(), checks.size()])
	effects.free()
	# Let the dummy audio driver consume the stop commands before engine teardown.
	await create_timer(.25).timeout
	quit(0 if report.passed else 1)
