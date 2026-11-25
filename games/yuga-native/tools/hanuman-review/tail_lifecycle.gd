extends SceneTree
## Independent measurements from the integrated trial. Pure animation and
## ordinary input capture are tested separately from this headless sequence.

const Chain = preload("res://scripts/hero_chain_response.gd")
const TRIAL = preload("res://scenes/hanuman_trial.tscn")
const PROFILE := "res://assets/design/hanuman-tail-response.json"

var trial: Node3D
var actor: CharacterBody3D
var response: SkeletonModifier3D
var names: Array = []
var bones: PackedInt32Array
var checks: Array[Dictionary] = []
var callback_samples: Array = []
var capture_callback := false


func _initialize() -> void:
	call_deferred("run")


func check(name_: String, ok: bool, data: Variant = null) -> void:
	checks.append({"case": name_, "passed": ok, "data": data})
	if not ok: print("FAIL ", name_, ": ", data)


func ticks(count: int) -> void:
	for i in count:
		await physics_frame


func on_modifier_applied() -> void:
	if not capture_callback: return
	var rotations: Array = []
	for bone in bones:
		rotations.append(actor.skeleton.get_bone_pose_rotation(bone))
	callback_samples.append(rotations)


func active_offsets(snapshot: Dictionary) -> PackedFloat32Array:
	var sizes := PackedFloat32Array()
	for v in snapshot.offsets_deg:
		sizes.append(Vector2(v[0], v[1]).length())
	return sizes


func finite_bounded(snapshot: Dictionary) -> bool:
	var sizes := active_offsets(snapshot)
	if sizes.size() != names.size() or snapshot.applied_deg.size() != names.size(): return false
	for i in sizes.size():
		if not is_finite(sizes[i]) or sizes[i] > float(snapshot.limits_deg[i]) + .0001:
			return false
		if not is_finite(snapshot.applied_deg[i]) or snapshot.applied_deg[i] > float(snapshot.limits_deg[i]) + .0001:
			return false
	return true


func run() -> void:
	trial = TRIAL.instantiate()
	root.add_child(trial)
	current_scene = trial
	actor = trial.hero
	if is_instance_valid(actor): response = actor.tail_response
	if not trial.ready_for_play or not is_instance_valid(response):
		check("integrated rig with a tail modifier", false, trial.report())
		await finish()
		return
	trial.effects.set_options({"volume": 0.0})
	var start: Dictionary = response.report()
	names = start.joints
	check("four consecutive local modifier roles", start.configured and names == ["tail_01", "tail_02", "tail_03", "tail_04"], names)
	for name_ in names:
		bones.append(actor.skeleton.find_bone(name_))
	response.modification_processed.connect(on_modifier_applied)
	var malformed: Dictionary = Chain.load_profile(PROFILE)
	malformed.joints[2].bone = "wrist.R"
	var rejected := Chain.new()
	check("non-chain bone is rejected before any role mutation", not rejected.configure(actor.skeleton, malformed) and not rejected.report().configured and rejected.report().joints.is_empty())
	rejected.free()

	trial._set_paused(false)
	await ticks(15)
	var ground: Vector3 = actor.global_position
	callback_samples.clear()
	capture_callback = true
	Input.action_press("move_left")
	Input.action_press("move_forward")
	await ticks(28)
	var moving: Dictionary = response.report()
	var moved: Vector3 = actor.global_position
	var deltas := PackedFloat32Array([0.0, 0.0, 0.0, 0.0])
	if not callback_samples.is_empty():
		for row in callback_samples:
			for i in names.size():
				if row[i].is_finite():
					deltas[i] = maxf(deltas[i], rad_to_deg(callback_samples[0][i].angle_to(row[i])))
	var offsets := active_offsets(moving)
	check("all four joints respond while real actor runs and turns", ground.distance_to(moved) > .8 and moving.motion_kind == "moving"
		and offsets[0] > .1 and offsets[1] > .1 and offsets[2] > .1 and offsets[3] > .1
		and offsets[3] > offsets[0] + .15 and finite_bounded(moving), {"offsets": Array(offsets), "distance_m": ground.distance_to(moved)})
	check("modifier callback sees four changing finite final bone rotations", callback_samples.size() > 3 and deltas[0] > .05
		and deltas[1] > .05 and deltas[2] > .05 and deltas[3] > .05, {"callbacks": callback_samples.size(), "turn_deg": Array(deltas)})
	capture_callback = false
	trial._set_paused(true)
	var paused: Dictionary = response.report()
	await ticks(15)
	var held: Dictionary = response.report()
	check("pause keeps simulated time, landing count and bend stable", held.held and held.elapsed_s == paused.elapsed_s
		and held.landings == paused.landings and held.offsets_deg == paused.offsets_deg and actor.global_position == moved)
	trial._reset_trial()
	var reset: Dictionary = response.report()
	check("reset while paused clears every joint without time catch-up", reset.resets > held.resets and reset.elapsed_s == 0.0 and reset.overlay_weight == 0.0
		and active_offsets(reset) == PackedFloat32Array([0, 0, 0, 0]) and reset.held)
	trial._set_paused(false)
	await ticks(12)

	var origin: Vector3 = actor.global_position
	var launch: Dictionary = trial.combat.request_ability("maruti_udayana", origin, Vector3.RIGHT, origin + Vector3.RIGHT * 5.0)
	var launch_max := PackedFloat32Array([0.0, 0.0, 0.0, 0.0])
	var landing_max := PackedFloat32Array([0.0, 0.0, 0.0, 0.0])
	var max_y := 0.0
	var stages := {}
	var all_bounded := true
	for i in 65:
		await physics_frame
		var row: Dictionary = response.report()
		var sizes := active_offsets(row)
		all_bounded = all_bounded and finite_bounded(row)
		stages[row.motion_kind] = true
		max_y = maxf(max_y, actor.global_position.y)
		for j in sizes.size():
			if row.motion_kind == "vault": launch_max[j] = maxf(launch_max[j], sizes[j])
			if row.motion_kind == "landing": landing_max[j] = maxf(landing_max[j], sizes[j])
	var landed: Dictionary = response.report()
	check("actual vault changes every joint and landing settles into the ground", launch.accepted and max_y > .5 and actor.is_on_floor()
		and landed.landings > reset.landings and stages.has("vault") and stages.has("landing") and all_bounded
		and Array(launch_max).all(func(value): return value > .1) and Array(landing_max).all(func(value): return value > .1),
		{"launch": launch, "launch_max_deg": Array(launch_max), "landing_max_deg": Array(landing_max), "max_y_m": max_y, "stages": stages.keys()})

	trial._reset_trial()
	await ticks(12)
	Input.action_press("move_back")
	await ticks(14)
	Input.action_release("move_back")
	var before_cast: Dictionary = response.report()
	var p: Vector3 = actor.global_position
	var tail_cast: Dictionary = trial.combat.request_ability("lanka_dahan", p, Vector3.FORWARD, p)
	var beginning: Dictionary = response.report()
	var fade := [float(beginning.overlay_weight)]
	for i in 8:
		await physics_frame
		fade.append(float(response.report().overlay_weight))
	var smooth := true
	var distinct := {}
	for i in fade.size():
		distinct[fade[i]] = true
		if i > 0:
			var step := float(fade[i - 1]) - float(fade[i])
			smooth = smooth and step >= -.00001 and step <= .21
	check("protected cast blends out from full run rather than snapping", tail_cast.accepted and before_cast.overlay_weight > .9
		and is_equal_approx(float(fade[0]), float(before_cast.overlay_weight)) and fade[-1] == 0.0
		and smooth and distinct.size() >= 5, {"gate_by_tick": fade})
	await ticks(23)
	var protected: Dictionary = response.report()
	check("actual rear cast protects authored tail against procedural overrides", tail_cast.accepted and protected.overlay_weight == 0.0
		and protected.applied_deg.all(func(value): return absf(value) < .0001), {"before_gate": before_cast.overlay_weight, "protected": protected.applied_deg})
	trial.combat.cancel_active("independent_tail_cancel")
	var cancellation: Dictionary = response.report()
	await ticks(16)
	var settled: Dictionary = response.report()
	check("cancel ends pose lock and expires bounded settling window", cancellation.cancel_settle_s > 0.0 and settled.cancel_settle_s == 0.0
		and actor.report().action.is_empty() and finite_bounded(settled))

	trial._reset_trial()
	await ticks(12)
	p = actor.global_position
	var ultimate: Dictionary = trial.combat.request_ability("mountain_pulse", p, Vector3.FORWARD, p + Vector3.FORWARD * 4.0)
	await ticks(50)
	var pulse: Dictionary = response.report()
	check("Mountain Pulse retains its authored tail pose through release", ultimate.accepted and pulse.overlay_weight == 0.0 and pulse.applied_deg.all(func(value): return absf(value) < .0001))
	trial._reset_trial()
	await ticks(31)
	var normal: Dictionary = response.report()
	var modifier_count: int = actor.skeleton.get_children().filter(func(child): return child is SkeletonModifier3D).size()
	check("repeated resets clear action state and keep one modifier attached", normal.resets >= reset.resets + 4
		and actor.report().action.is_empty() and modifier_count == 1
		and finite_bounded(normal) and normal.overlay_weight > .1,
		{"modifier_count": modifier_count, "normal": normal, "earlier_resets": reset.resets, "action": actor.report().action})
	await finish()


func finish() -> void:
	var success := checks.all(func(row): return row.passed)
	var report := {"checks": checks, "passed": success, "source_sha256": {}}
	for source in [get_script().resource_path, PROFILE, "res://scripts/hero_chain_response.gd", "res://scripts/hanuman_actor.gd",
		"res://scripts/hanuman_trial.gd", "res://assets/heroes/hanuman/hanuman.glb"]:
		report.source_sha256[source] = FileAccess.get_sha256(source)
	for argument in OS.get_cmdline_user_args():
		if not argument.begins_with("--report="): continue
		var path := argument.trim_prefix("--report=")
		var file := FileAccess.open(path, FileAccess.WRITE) if not FileAccess.file_exists(path) else null
		if file == null:
			printerr("Review output must be writable and fresh: ", path)
			quit(2)
			return
		file.store_string(JSON.stringify(report, "  ") + "\n")
		file.close()
	print("Hanuman per-joint lifecycle: %d/%d" % [checks.filter(func(item): return item.passed).size(), checks.size()])
	trial.queue_free()
	for i in 8: await process_frame
	quit(0 if success else 1)
