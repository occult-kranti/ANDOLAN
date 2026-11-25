extends SceneTree
## Targeted modifier and state probe through the actual Hanuman trial.

const Chain = preload("res://scripts/hero_chain_response.gd")
const Actor = preload("res://scripts/hanuman_actor.gd")
var checks := {}
var trial: Node3D
var actor: CharacterBody3D
var response: SkeletonModifier3D
var _pose_distinct := {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	trial = (load("res://scenes/hanuman_trial.tscn") as PackedScene).instantiate()
	root.add_child(trial)
	current_scene = trial
	actor = trial.hero
	response = actor.tail_response if is_instance_valid(actor) else null
	_check("runtime actor attaches one four-role modifier", trial.ready_for_play and is_instance_valid(response) and response.get_skeleton() == actor.skeleton)
	if not checks.values()[0].ok:
		_finish()
		return
	trial.effects.set_options({"volume":0.0})
	response.modification_processed.connect(_sample_pose)
	trial._set_paused(false)
	await _frames(38)
	var idle: Dictionary = response.report()
	_check("authored idle settles and shallow spawn does not count as landing", idle.configured and idle.joints.size() == 4 and _maximum(idle.applied_deg) < .03 and idle.landings == 0 and actor.is_on_floor(), idle)
	Input.action_press("move_right")
	await _frames(24)
	var walking: Dictionary = response.report()
	var turn_tip: Vector2 = Vector2(walking.offsets_deg[-1][0], walking.offsets_deg[-1][1])
	_check("real directional run and turn drives the weighted tail", walking.motion_kind == "moving" and walking.modifier_samples > idle.modifier_samples and absf(turn_tip.y) > .3 and _maximum(walking.applied_deg) > 1.0, walking)
	Input.action_press("sprint")
	await _frames(22)
	var sprint: Dictionary = response.report()
	Input.action_release("move_right")
	Input.action_release("sprint")
	_check("sprint extends speed response and distinct outputs are applied", _maximum(sprint.applied_deg) > _maximum(walking.applied_deg) + .6 and _pose_distinct.size() >= 10, {"samples":_pose_distinct.size(),"moving":walking.applied_deg,"sprint":sprint.applied_deg})
	_check("all additive links stay at their profile limits", _inside_limits(sprint), sprint)
	trial._set_paused(true)
	var held: Dictionary = response.report()
	await _frames(24)
	var retained: Dictionary = response.report()
	_check("pause holds spring and elapsed time", held.held and retained.held and held.elapsed_s == retained.elapsed_s and held.offsets_deg == retained.offsets_deg)
	trial._reset_trial()
	var reset: Dictionary = response.report()
	_check("reset clears all chain inertia while held", _maximum(reset.applied_deg) == 0.0 and reset.offsets_deg.all(func(pair: Array): return pair == [0.0,0.0]) and reset.overlay_weight == 0.0 and reset.resets > held.resets)
	trial._set_paused(false)
	await _frames(12)
	var start: Vector3 = actor.global_position
	var cast: Dictionary = trial.combat.request_ability("maruti_udayana",start,Vector3.RIGHT,start+Vector3.RIGHT*4.0)
	var vault_samples := 0
	var landing_samples := 0
	var vault_peak := 0.0
	var saw_ground_after := false
	for i in range(76):
		await _frames(1)
		var row: Dictionary = response.report()
		if row.motion_kind == "vault":
			vault_samples += 1
			vault_peak = maxf(vault_peak, _maximum(row.applied_deg))
		if row.motion_kind == "landing": landing_samples += 1
		if row.grounded and row.landings > reset.landings: saw_ground_after = true
	_check("vault and checked landing drive separate finite responses", cast.accepted and vault_samples > 10 and vault_peak > 1.0 and landing_samples > 0 and saw_ground_after and actor.is_on_floor(),
		{"vault_frames":vault_samples,"vault_peak_deg":vault_peak,"landing_frames":landing_samples,"report":response.report()})
	Input.action_press("move_right")
	Input.action_press("sprint")
	await _frames(32)
	Input.action_release("move_right")
	Input.action_release("sprint")
	var sprint_entry: Dictionary = response.report()
	start = actor.global_position
	var authored: Dictionary = trial.combat.request_ability("lanka_dahan",start,Vector3.RIGHT,start)
	await _frames(1)
	var first_blend: Dictionary = response.report()
	var gate_delta := float(sprint_entry.overlay_weight) - float(first_blend.overlay_weight)
	var angular_delta := _maximum(sprint_entry.applied_deg) - _maximum(first_blend.applied_deg)
	_check("protected animation ramps down the sprint offset instead of snapping", authored.accepted and sprint_entry.overlay_weight > .97 and first_blend.overlay_weight > .70 and gate_delta > 0.0 and gate_delta < .18 and _maximum(first_blend.applied_deg) > 1.0 and absf(angular_delta) < 3.0,
		{"gate_before":sprint_entry.overlay_weight,"gate_after":first_blend.overlay_weight,"tip_step_degrees":angular_delta})
	await _frames(10)
	var masked: Dictionary = response.report()
	_check("authored tail sweep owns the tail without additive motion", authored.accepted and actor._last_motion == "tail_sweep" and masked.overlay_weight == 0.0 and _maximum(masked.applied_deg) == 0.0, masked)
	await _frames(19)
	var sweep_contact: Dictionary = response.report()
	_check("tail sweep has zero additive motion at its gameplay contact", _saw_event("lanka_dahan", "impact") and sweep_contact.overlay_weight == 0.0 and _maximum(sweep_contact.applied_deg) == 0.0)
	trial.combat.cancel_active("test interrupt")
	var cancelled: Dictionary = response.report()
	await _frames(18)
	var settled: Dictionary = response.report()
	_check("cancel enters bounded neutral settling", cancelled.cancel_settle_s > .0 and settled.cancel_settle_s == 0.0 and _maximum(settled.applied_deg) < .55, settled)
	start = actor.global_position
	var pulse: Dictionary = trial.combat.request_ability("mountain_pulse",start,Vector3.RIGHT,start + Vector3.RIGHT * 3.0)
	await _frames(10)
	var pulse_mask: Dictionary = response.report()
	_check("ultimate keeps authored chain posing authoritative", pulse.accepted and actor._last_motion == "mountain_pulse" and pulse_mask.overlay_weight == 0.0 and _maximum(pulse_mask.applied_deg) == 0.0, pulse_mask)
	await _frames(63)
	var contact: Dictionary = response.report()
	_check("protected ultimate reaches its release and delayed impact with zero additive tail", _saw_event("mountain_pulse", "release") and _saw_event("mountain_pulse", "impact") and contact.overlay_weight == 0.0 and _maximum(contact.applied_deg) == 0.0)
	var invalid := Chain.new()
	var missing := Chain.load_profile(Actor.TAIL_PROFILE)
	missing.joints[2].bone = "tail_role_missing"
	var rejected: bool = not invalid.configure(actor.skeleton, missing) and invalid.report().joints.is_empty()
	_check("missing role rejects without partially binding the real rig", rejected and invalid.configure(actor.skeleton, Chain.load_profile(Actor.TAIL_PROFILE)))
	invalid.free()
	_finish()

func _sample_pose() -> void:
	var bone: int = actor.skeleton.find_bone(&"tail_04")
	var pose: Quaternion = actor.skeleton.get_bone_pose_rotation(bone)
	if pose.is_finite(): _pose_distinct[hash(pose)] = true

func _saw_event(id: String, kind: String) -> bool:
	for event: Dictionary in trial.combat.report().history:
		if event.ability_id == id and event.kind == kind: return true
	return false

func _frames(count: int) -> void:
	for frame in range(count):
		await physics_frame
		await process_frame

func _maximum(values: Array) -> float:
	var maximum := 0.0
	for value in values: maximum = maxf(maximum, absf(float(value)))
	return maximum

func _inside_limits(row: Dictionary) -> bool:
	for i in range(row.limits_deg.size()):
		var pair: Array = row.offsets_deg[i]
		if not Vector2(pair[0], pair[1]).is_finite() or Vector2(pair[0], pair[1]).length() > float(row.limits_deg[i]) + .0001 or absf(row.applied_deg[i]) > float(row.limits_deg[i]) + .0001:
			return false
	return true

func _check(label: String, passed: bool, details: Variant = null) -> void:
	checks[label] = {"ok":passed,"details":details}

func _finish() -> void:
	var failed := checks.values().filter(func(row: Dictionary): return not row.ok).size()
	print("HANUMAN_TAIL ", JSON.stringify({"passed":checks.size()-failed,"failed":failed,"model_sha256":FileAccess.get_sha256(Actor.MODEL_PATH),"profile_sha256":FileAccess.get_sha256(Actor.TAIL_PROFILE),"checks":checks}))
	if is_instance_valid(trial): trial.queue_free()
	for frame in range(6): await process_frame
	quit(0 if failed == 0 else 1)
