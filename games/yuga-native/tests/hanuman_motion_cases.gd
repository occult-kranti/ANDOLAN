extends SceneTree
## Real launcher, actor, motion library, combat clock and keyed ability inputs.

const Actor = preload("res://scripts/hanuman_actor.gd")
const BOOT := "res://scenes/boot.tscn"
const COURT := "res://scenes/courtyard.tscn"
const TRIAL := "res://scenes/hanuman_trial.tscn"
const BONES := [&"spine01", &"head", &"wrist.R", &"wrist.L", &"foot.L", &"foot.R", &"tail_04"]
const CASTS := [
	["vajra_gada", "fire", "fire"],
	["vajra_kavacha", "pulse", "cast2"],
	["maruti_udayana", "dash", "cast1"],
	["lanka_dahan", "guardian_circle", "tail_sweep"],
	["mountain_pulse", "ultimate", "mountain_pulse"],
]

var _result: Array[Dictionary] = []
var _traces := {}
var _trial: Node3D
var _hero: CharacterBody3D
var _output := ""
var _watch_id := ""
var _events := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): _output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _check(label: String, passed: bool, details: Dictionary = {}) -> void:
	_result.append({"name":label,"passed":passed,"details":details})

func _wait_scene(path: String) -> bool:
	var deadline := Time.get_ticks_msec() + 30000
	while Time.get_ticks_msec() < deadline:
		var loader := root.get_node_or_null("YugaSceneTransitionLayer/SceneTransition")
		if current_scene != null and current_scene.scene_file_path == path and (not loader or not loader.visible):
			return true
		await process_frame
	return false

func _ticks(count: int) -> void:
	for unused in count: await physics_frame

func _key(action: StringName) -> void:
	var input := InputEventAction.new()
	input.action = action
	input.pressed = true
	Input.parse_input_event(input)
	var release := input.duplicate() as InputEventAction
	release.pressed = false
	Input.parse_input_event(release)

func _pose() -> Dictionary:
	var bones := {}
	for name_: StringName in BONES:
		var index: int = _hero.skeleton.find_bone(name_)
		var transform_: Transform3D = _hero.skeleton.get_bone_global_pose(index)
		var origin := transform_.origin
		var rotation := transform_.basis.get_rotation_quaternion()
		bones[name_] = {"m":[origin.x,origin.y,origin.z],"q":[rotation.x,rotation.y,rotation.z,rotation.w]}
	return {"motion":_hero.report().motion,"stage":_hero._action.get("stage", ""),
		"clip_time_s":_hero.animator.current_animation_position,"grounded":_hero.is_on_floor(),"vaulting":not _hero._vault.is_empty(),
		"bones":bones}

func _event(event: Dictionary) -> void:
	var kind: String = event.kind
	if event.ability_id == _watch_id and kind in ["begin","release","impact","recovery","cancel","end"]:
		_events[kind] = _pose().merged({"cast_id":event.cast_id,"generation":event.generation,
			"seq":event.event_seq,"authority_age_s":event.age_s,"reason":event.reason})
	if _watch_id == "mountain_pulse" and event.ability_id == "lanka_dahan" and kind == "end":
		_events["earlier_fire_end"] = _pose()

func _pose_change(from: Dictionary, into: Dictionary) -> Dictionary:
	var change := {}
	if from.is_empty() or into.is_empty(): return change
	for b: StringName in BONES:
		var a: Dictionary = from.bones[b]
		var n: Dictionary = into.bones[b]
		var delta := Vector3(a.m[0],a.m[1],a.m[2]).distance_to(Vector3(n.m[0],n.m[1],n.m[2]))
		var ra := Quaternion(a.q[0],a.q[1],a.q[2],a.q[3])
		var rb := Quaternion(n.q[0],n.q[1],n.q[2],n.q[3])
		change[b] = {"m":delta,"deg":rad_to_deg(ra.angle_to(rb))}
	return change

func _moves(change: Dictionary) -> bool:
	return change.values().any(func(delta: Dictionary): return delta.m > .015 or delta.deg > 3.0)

func _run_cast(ability: String, input: String, expected_clip: String) -> void:
	_watch_id = ability
	_events = {}
	if ability == "maruti_udayana": _hero.turn_camera(Vector2(-328,0))
	if ability == "mountain_pulse": _hero.turn_camera(Vector2(0,50))
	_key(input)
	await _ticks(2)
	var action: Dictionary = _hero._action.duplicate()
	_check(ability + " starts intended imported motion through native input",
		not action.is_empty() and _events.has("begin") and _hero.report().motion == expected_clip)
	if action.is_empty() or not _events.has("begin"): return
	var mark_release := float(action.contact_s)
	var mark_impact := float(action.impact_s)
	var middle := {}
	var flight := {}
	var landing := {}
	var settle := {}
	var tested_pause := false
	if ability == "vajra_gada":
		_key("pulse")
		_key("jump")
		Input.action_press("move_forward")
		await _ticks(4)
		Input.action_release("move_forward")
		_check("Busy cast rejects a second input and maintains grounded pose",
			_hero._action.get("id") == action.id and _hero.is_on_floor()
			and absf(_hero.global_position.z - _trial.SPAWN.z) < .01)
	for frame in 160:
		await physics_frame
		var current: Dictionary = _hero._action
		if current.is_empty(): break
		if current.stage == "windup" and middle.is_empty() and float(current.age) >= float(current.windup_s) * .45:
			middle = _pose()
		if current.stage == "travel" and flight.is_empty() and float(current.age) >= float(current.travel_s) * .4:
			flight = _pose()
		if ability == "maruti_udayana" and current.stage == "recovery" and landing.is_empty():
			landing = _pose()
		if current.stage == "recovery" and settle.is_empty() and float(current.age) >= float(current.recovery_s) * .45:
			settle = _pose()
		if ability == "mountain_pulse" and current.stage == "travel" and not tested_pause:
			tested_pause = true
			_key("pause_game")
			await _ticks(2)
			var before: Dictionary = _pose()
			var clock: float = _trial.combat.elapsed
			await _ticks(8)
			var same: bool = _trial.paused and is_equal_approx(_trial.combat.elapsed,clock) \
				and is_equal_approx(_hero.animator.current_animation_position,float(before.clip_time_s))
			var paused_clip: float = _hero.animator.current_animation_position
			_key("pause_game")
			await _ticks(2)
			_check("Pause freezes authority and pose during Pulse travel, then resumes",same and not _trial.paused,
				{"held_clip_time_s":paused_clip,"previous_clip_time_s":before.clip_time_s,"held_clock_s":clock})
	var release: Dictionary = _events.get("release", {})
	var impact: Dictionary = _events.get("impact", {})
	var recovery: Dictionary = _events.get("recovery", {})
	var windup_change := _pose_change(_events.begin,middle)
	var settle_change := _pose_change(landing if not landing.is_empty() else impact,settle)
	_check(ability + " releases on the authored key and returns to locomotion at authority recovery",
		not release.is_empty() and not impact.is_empty() and not recovery.is_empty()
		and absf(float(release.clip_time_s) - mark_release) < .001 \
		and release.seq < impact.seq and impact.seq < recovery.seq and _hero._action.is_empty())
	_check(ability + " moves bones across windup and recovery", _moves(windup_change) and _moves(settle_change))
	if ability == "maruti_udayana":
		_check("Vault keeps an airborne pose after launch acknowledgement and lands on grounded contact",
			impact.get("reason") == "movement_accepted" and absf(float(impact.get("clip_time_s", -1)) - mark_release) < .001
			and not flight.is_empty() and flight.vaulting and float(flight.clip_time_s) < mark_impact
			and not landing.is_empty() and landing.grounded and not landing.vaulting
			and absf(float(landing.clip_time_s) - mark_impact) < .001,
			{"impact_s":mark_impact,"landing":landing})
	if ability == "mountain_pulse":
		_check("Pulse travels before its actual impact key while an older fire cast finishes independently",
			tested_pause and not flight.is_empty() and float(flight.clip_time_s) < mark_impact
			and absf(float(impact.get("clip_time_s",-1)) - mark_impact) < .001 and recovery.get("motion") == "idle"
			and _events.get("earlier_fire_end", {}).get("motion") == "mountain_pulse")
	_traces[ability] = {"events":_events.duplicate(true),"windup":middle,"travel":flight,
		"landing":landing,"mid_recovery":settle,"windup_bone_changes":windup_change,"recovery_bone_changes":settle_change}

func _run() -> void:
	change_scene_to_file(BOOT)
	if not await _wait_scene(COURT):
		_check("Boot reaches the native courtyard launcher",false)
		_finish()
		return
	var shell: Control = current_scene.main_panel
	shell.hanuman_mode_button.pressed.emit()
	shell.primary_button.pressed.emit()
	if not await _wait_scene(TRIAL):
		_check("Actual title selection reaches Hanuman Trial",false)
		_finish()
		return
	_trial = current_scene
	_hero = _trial.hero
	_trial.find_child("BeginPractice",true,false).pressed.emit()
	await _ticks(18)
	var status: Dictionary = _hero.report()
	_check("Normal launcher and practice button activate the rig",_trial.ready_for_play and _hero.active and _hero.is_on_floor())
	_check("Actor plays five qualified revised clips while retaining all eleven original names",
		status.revised_motion_clips.size() == 5 and status.clips.size() == 11 and status.ability_motion_error.is_empty(),status)
	_trial.combat.ability_event.connect(_event)
	for row: Array in CASTS:
		if row[0] != "mountain_pulse":
			_key("reset_training")
			await _ticks(10)
		await _run_cast(row[0],row[1],row[2])
	var signatures := {}
	for trace: Dictionary in _traces.values():
		var release: Dictionary = trace.events.get("release",{})
		if not release.is_empty(): signatures[JSON.stringify(release.bones)] = true
	_check("All five committed releases have distinct full-body pose signatures",signatures.size() == 5)

	_watch_id = "vajra_gada"
	_events = {}
	_key("reset_training")
	await _ticks(12)
	_key("fire")
	await _ticks(3)
	_trial.combat.cancel_active("Interrupted in the motion probe")
	await _ticks(25)
	_check("Cancel before commit restores locomotion without a release",_events.has("cancel") and not _events.has("release")
		and _hero._action.is_empty() and _hero.report().motion == "idle")

	_watch_id = "maruti_udayana"
	_events = {}
	_key("reset_training")
	await _ticks(14)
	_hero.turn_camera(Vector2(-328,0))
	_key("dash")
	await _ticks(20)
	var was_airborne: bool = not _hero._vault.is_empty() and _hero.global_position.y > .2
	_key("reset_training")
	await _ticks(12)
	_check("Reset during committed travel clears vault and old pose",
		was_airborne and _events.has("release") and _hero._vault.is_empty() and _hero._action.is_empty()
		and _hero.report().motion == "idle" and _hero.global_position.distance_to(_trial.SPAWN) < .1)
	_watch_id = "maruti_udayana"
	_events = {}
	_hero.turn_camera(Vector2(-328,0))
	_key("dash")
	await _ticks(20)
	var crossed: bool = not _hero._vault.is_empty()
	_trial.combat.cancel_active("Interrupted after movement commit in the motion probe")
	await _ticks(36)
	_check("Cancel after vault commit stops the sweep and restores grounded locomotion",
		crossed and _events.has("cancel") and _hero._vault.is_empty()
		and _hero._action.is_empty() and _hero.is_on_floor() and _hero.report().motion == "idle")
	_finish()

func _finish() -> void:
	var failures := _result.filter(func(row: Dictionary): return not row.passed)
	var sources := {}
	for path in [Actor.ABILITY_MOTION_PATH,Actor.MODEL_PATH,"res://scripts/hanuman_actor.gd","res://scripts/hanuman_trial.gd",
			"res://assets/design/hanuman-ability-kit.json",get_script().resource_path]:
		if FileAccess.file_exists(path): sources[path] = FileAccess.get_sha256(path)
	var data := {"checks":_result,"failed":failures.size(),"passed":_result.size()-failures.size(),"traces":_traces,"sources":sources}
	if not _output.is_empty():
		var result := FileAccess.open(_output,FileAccess.WRITE)
		result.store_string(JSON.stringify(data,"\t") + "\n")
	print("YUGA_HANUMAN_MOTION " + JSON.stringify({"passed":data.passed,"failed":data.failed,"failures":failures}))
	if is_instance_valid(current_scene): current_scene.queue_free()
	var transition := root.get_node_or_null("YugaSceneTransitionLayer")
	if transition: transition.queue_free()
	for frame in 3: await process_frame
	quit(0 if failures.is_empty() else 1)
