extends SceneTree
## Exercise the actual trial's input, combat clock, animation and effect routing.

const TRIAL = preload("res://scenes/hanuman_trial.tscn")
const STEP := 0.05
const INPUTS := {
	"vajra_gada": "fire",
	"vajra_kavacha": "pulse",
	"maruti_udayana": "dash",
	"lanka_dahan": "guardian_circle",
	"mountain_pulse": "ultimate",
}
const INPUT_SOURCES := [
	"res://scenes/hanuman_trial.tscn",
	"res://scripts/hanuman_trial.gd",
	"res://scripts/hanuman_actor.gd",
	"res://scripts/hanuman_combat.gd",
	"res://scripts/hanuman_trial_effects.gd",
	"res://scripts/hanuman_invocation_art.gd",
	"res://scripts/hanuman_ground_field.gd",
	"res://scripts/input_bindings.gd",
	"res://scripts/rama_practice_army.gd",
	"res://shaders/hanuman_invocation_mark.gdshader",
	"res://shaders/hanuman_ground_field.gdshader",
	"res://assets/heroes/hanuman/hanuman.glb",
	"res://assets/heroes/hanuman/hanuman-ability-motion.tres",
	"res://assets/design/hanuman-ability-kit.json",
	"res://assets/design/hanuman-presentation.json",
	"res://assets/vfx/hanuman-invocation-masks.png",
]

var trial: Node3D
var events: Array[Dictionary] = []
var checks: Array[Dictionary] = []
var scenarios: Array[Dictionary] = []


func _initialize() -> void:
	call_deferred("_run")


func _check(label: String, passed: bool) -> void:
	checks.append({"name": label, "passed": passed})
	if not passed:
		printerr("FAIL ", label)


func _capture(event: Dictionary) -> void:
	events.append(event.duplicate(true))


func _input_state(action: String, pressed: bool) -> void:
	var event := InputEventAction.new()
	event.action = action
	event.pressed = pressed
	event.strength = 1.0 if pressed else 0.0
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func _tap(action: String) -> void:
	_input_state(action, true)
	_input_state(action, false)


func _frames(count: int) -> void:
	for _frame in count:
		await physics_frame


func _steps(count: int, split: bool) -> void:
	for _step in count:
		if split:
			for part in [0.012, 0.013, 0.025]:
				trial.army._physics_process(part)
		else:
			trial.army._physics_process(STEP)


func _timed_steps(count: int, split: bool) -> void:
	for _step in count:
		_steps(1, split)
		await _frames(3)


func _ticks(seconds: float) -> int:
	return ceili(seconds / STEP - 1e-7)


func _timeline(start: int) -> Array:
	return events.slice(start).map(func(event): return [event.kind, roundi(event.age_s * 1000.0)])


func _reset() -> void:
	_tap("reset_training")
	await _frames(12)


func _aim_at_trial_target(id: String) -> void:
	match id:
		"vajra_gada":
			_input_state("move_forward", true)
			await _frames(22)
			_input_state("move_forward", false)
			await _frames(12)
		"vajra_kavacha", "lanka_dahan":
			# The headless backend cannot capture a pointer. Use the same
			# camera method that receives mouse motion in the trial.
			trial.hero.turn_camera(Vector2(PI / trial.hero.look_sensitivity, 0))
		"maruti_udayana":
			trial.hero.turn_camera(Vector2(350, 0))
		"mountain_pulse":
			trial.hero.turn_camera(Vector2(0, 130))
			trial.vitals.receive_damage(25)
	await _frames(3)


func _check_trial_payload(id: String, cast_events: Array, label: String, origin: Vector3) -> Dictionary:
	if id == "maruti_udayana":
		var move: Dictionary = trial.hero.report().last_vault
		_check(label + " real body clears the angled vault and lands at its accepted destination",
			not move.is_empty() and not move.blocked and move.error_m < 0.03 and move.position.distance_to(origin) > 8.0)
		return {"blocked": move.get("blocked"), "reach_m": move.position.distance_to(origin) if move.has("position") else 0,
			"landing_error_m": move.get("error_m")}
	var payloads := cast_events.filter(func(event): return event.kind == "impact")
	var receipts: Array = payloads[0].receipts if payloads.size() == 1 else []
	var target := receipts.filter(func(receipt): return receipt.unit_id == 1)
	match id:
		"vajra_gada":
			_check(label + " contacts the first enemy at the normal advance distance",
				target.size() == 1 and target[0].damage_applied == 34.0)
		"vajra_kavacha":
			var shield_ids := receipts.filter(func(receipt): return receipt.shield_after == 48.0)
			_check(label + " wards the actual ally and caster",
				shield_ids.map(func(receipt): return receipt.unit_id) == [5, 0])
		"lanka_dahan":
			_check(label + " hits and sustains the rear exposure on the first enemy",
				target.size() == 1 and target[0].damage_applied == 28.0 and is_equal_approx(trial.army.units[0].health, 46.0))
		"mountain_pulse":
			var caster := receipts.filter(func(receipt): return receipt.unit_id == 0)
			_check(label + " damages the first enemy and heals the caster at the aimed landing",
				target.size() == 1 and target[0].damage_applied == 65.0 and caster.size() == 1 and caster[0].healing_applied == 25.0)
	return {"first_target_health_after": trial.army.units[0].health, "impact_receipts": receipts.map(func(receipt):
		return {"unit": receipt.unit_id, "damage": receipt.damage_applied, "heal": receipt.healing_applied,
			"shield_after": receipt.shield_after})}


func _exercise(rule: Dictionary, split: bool, reduced: bool) -> Array:
	await _reset()
	var id: String = rule.id
	await _aim_at_trial_target(id)
	var action: String = INPUTS[id]
	var label := "%s / %s" % [id, "split reduced" if split else "whole full"]
	var start := events.size()
	var accepted_before: int = trial.effects.report().accepted
	_tap(action)
	var began: bool = events.size() == start + 1 and events.back().kind == "begin" and events.back().ability_id == id
	_check(label + " actual mapped action reaches the correct imported clip",
		began and trial.hero.report().motion == rule.motion and trial.effects.report().active == 1)
	if not began:
		return []
	var begin_event: Dictionary = events.back()
	_tap(action)
	_tap("fire" if action != "fire" else "pulse")
	_check(label + " blocks same and different actions during windup", events.size() == start + 1)

	var timing: Dictionary = rule.timing
	var release_tick := _ticks(timing.windup_s)
	var impact_tick := release_tick if id == "maruti_udayana" else _ticks(timing.windup_s + timing.travel_s)
	var recovery_tick := _ticks(timing.windup_s + timing.travel_s + timing.recovery_s)
	var end_tick := _ticks(timing.windup_s + timing.travel_s + maxf(timing.recovery_s, timing.active_s))
	await _timed_steps(release_tick - 1, split)
	_check(label + " one tick before release stays in windup",
		events.size() == start + 1 and trial.combat.report(false).phase == "windup")
	_steps(1, split)
	var released_action: Dictionary = trial.hero.report().action
	var expected_stage := "travel" if timing.travel_s > 0.0 else "recovery"
	var release_sample: float = trial.hero.animator.current_animation_position
	_check(label + " release seeks the authored clip marker in the same event",
		released_action.get("stage") == expected_stage
		and is_equal_approx(release_sample, float(released_action.get("contact_s", -1.0))))
	await _frames(3)
	if id == "mountain_pulse":
		await _timed_steps(impact_tick - release_tick - 1, split)
		var travel_action: Dictionary = trial.hero.report().action
		var in_flight: bool = travel_action.get("stage") == "travel" and events.back().kind == "release" \
			and trial.hero.animator.current_animation_position < travel_action.get("impact_s", -1.0)
		_steps(1, split)
		var landing_action: Dictionary = trial.hero.report().action
		_check(label + " landing seeks a distinct marker only on impact",
			in_flight and landing_action.get("stage") == "recovery" and events.back().kind == "impact"
			and is_equal_approx(trial.hero.animator.current_animation_position, float(landing_action.get("impact_s", -1.0))))
		await _frames(3)
		await _timed_steps(end_tick - impact_tick, split)
	else:
		await _timed_steps(end_tick - release_tick, split)
	var timeline := _timeline(start)
	var kinds: Array = timeline.map(func(entry): return entry[0])
	var order := kinds.filter(func(kind): return kind != "tick")
	var exact := order == ["begin", "release", "impact", "recovery", "end"]
	for expected in [["release", release_tick], ["impact", impact_tick], ["recovery", recovery_tick], ["end", end_tick]]:
		var seen: Array = timeline.filter(func(entry): return entry[0] == expected[0])
		exact = exact and seen.size() == 1 and seen[0][1] == expected[1] * 50
	_check(label + " stages match the profile and movement impact marks launch", exact)
	var tick_count := kinds.count("tick")
	_check(label + " sustained tick count and effect receipts agree",
		tick_count == _ticks(timing.active_s) and trial.effects.report().accepted == accepted_before + timeline.size()
		and trial.effects.report().active == 0 and trial.hero.report().action.is_empty()
		and trial.effects.report().ground_field.visible_instances == 0)
	var payload := _check_trial_payload(id, events.slice(start), label, begin_event.origin)
	var signature := timeline.duplicate(true)
	scenarios.append({"id": id, "split_clock": split, "reduced": reduced, "timeline_ms": signature,
		"release_clip_sample_s": release_sample, "release_clip_marker_s": released_action.get("contact_s"), "payload": payload})

	# The actor has already finished. Fast-forward the remaining empty clock and
	# pressure the exact one-tick boundary with the same mapped action.
	var cooldown_tick := _ticks(rule.cooldown_s)
	_steps(cooldown_tick - end_tick - 1, split)
	var before_retrigger := events.size()
	_tap(action)
	_check(label + " refuses retrigger one tick before cooldown", events.size() == before_retrigger)
	_steps(1, split)
	_tap(action)
	_check(label + " retriggers on the exact cooldown tick",
		events.size() == before_retrigger + 1 and events.back().kind == "begin" and events.back().ability_id == id
		and absf(events.back().time_s - begin_event.time_s - cooldown_tick * STEP) < 1e-6)
	trial.combat.cancel_active("QA cooldown boundary")
	return signature


func _cancel_travel() -> void:
	await _reset()
	_tap("ultimate")
	await _timed_steps(14, true)
	var release: Dictionary = events.back().duplicate(true)
	_check("Mountain Pulse has a real travel stage", release.kind == "release" and trial.combat.report(false).phase == "travel")
	_tap("pause_game")
	var before := events.size()
	var age: float = trial.combat.report(false).elapsed
	_steps(60, true)
	_tap("fire")
	_check("Pausing through the landing time keeps the travel clock and input frozen",
		trial.paused and events.size() == before and is_equal_approx(trial.combat.report(false).elapsed, age))
	_tap("pause_game")
	trial.combat.cancel_active("QA interrupt in flight")
	_steps(60, true)
	_check("Cancel after release retires the pending landing and active presentation",
			events.size() == before + 1 and events.back().kind == "cancel" and trial.effects.report().active == 0
			and trial.hero.report().action.is_empty())
	await _reset()
	release.kind = "impact"
	release.event_seq += 1
	_check("Reset rejects a stale landing from the previous generation",
		events.back().kind == "reset" and events.back().generation > release.generation
		and not trial.effects.consume_event(release) and trial.effects.report().ground_field.visible_instances == 0)


func _reset_vault() -> void:
	await _reset()
	await _aim_at_trial_target("maruti_udayana")
	var start: Vector3 = trial.hero.global_position
	_tap("dash")
	await _timed_steps(7, false)
	var airborne: bool = not trial.hero.report().vault.is_empty() and trial.hero.global_position.y > 0.4
	await _reset()
	await _timed_steps(12, false)
	_check("The mapped reset cancels an airborne vault and restores grounded movement and cues",
		airborne and events.back().kind == "reset" and trial.hero.global_position.distance_to(start) < 0.06
		and trial.hero.is_on_floor() and trial.hero.report().vault.is_empty() and trial.hero.report().action.is_empty()
		and trial.effects.report().active == 0 and not trial.combat.report(false).action_locked)


func _overlap_fields() -> void:
	await _reset()
	await _aim_at_trial_target("lanka_dahan")
	_tap("guardian_circle")
	await _timed_steps(17, true)
	var tail_recovered: bool = not trial.combat.report(false).action_locked and trial.effects.report().ground_field.active == 1
	trial.hero.turn_camera(Vector2(PI / trial.hero.look_sensitivity, 130))
	await _frames(3)
	_tap("ultimate")
	await _timed_steps(23, true)
	var exact_overlap: bool = events.back().ability_id == "mountain_pulse" and events.back().kind == "impact" \
		and trial.effects.report().active == 2 and trial.effects.report().ground_field.visible_instances == 2
	var accepted: int = trial.effects.report().accepted
	trial.effects.set_options({"reduced_effects": true})
	var hidden: bool = trial.effects.report().ground_field.active == 2 and trial.effects.report().ground_field.visible_instances == 0
	trial.effects.set_options({"reduced_effects": false})
	_check("Recovered tail overlaps the landed mountain and reduced FX only hides the live fields",
		tail_recovered and exact_overlap and hidden and trial.effects.report().ground_field.visible_instances == 2
		and trial.effects.report().accepted == accepted)
	await _timed_steps(12, true)
	_check("Overlapping ground fields both retire at their original lifecycle boundaries",
		trial.effects.report().ground_field.active == 0 and trial.effects.report().active == 0)


func _source_hashes() -> Dictionary:
	var inputs := INPUT_SOURCES.duplicate()
	inputs.append(get_script().resource_path)
	var hashes := {}
	for path: String in inputs:
		hashes[path] = FileAccess.get_sha256(path)
	return hashes


func _stress_primary() -> void:
	await _reset()
	var start := events.size()
	var accepted_before: int = trial.effects.report().accepted
	var stable := true
	for cycle in 32:
		var first := events.size()
		_tap("fire")
		_tap("fire")
		_tap("pulse")
		_steps(12, cycle % 2 == 1)
		stable = stable and _timeline(first) == [["begin", 0], ["release", 250], ["impact", 250], ["recovery", 550], ["end", 550]]
		await process_frame
	_check("32 accepted primary cycles with 64 busy inputs produce one lifecycle each", stable and events.size() == start + 160)
	_check("Repeated inputs leave bounded history and no active visual or action",
		trial.combat.report().history.size() == 64 and trial.effects.report().accepted == accepted_before + 160
		and trial.effects.report().active == 0 and trial.hero.report().action.is_empty())


func _run() -> void:
	var sources := _source_hashes()
	trial = TRIAL.instantiate()
	root.add_child(trial)
	_check("The actual courtyard, Hanuman model and five ability cards initialize", trial.ready_for_play and trial.hero.report().bones == 167)
	if trial.ready_for_play:
		var installed: Array = trial.hero.report().revised_motion_clips
		_check("The real actor loads the complete five-action animation library",
			installed.size() == 5 and [&"fire", &"cast2", &"cast1", &"tail_sweep", &"mountain_pulse"].all(
				func(clip): return clip in installed) and trial.hero.report().ability_motion_error.is_empty())
		trial.army.set_physics_process(false)
		trial.combat.ability_event.connect(_capture)
		_tap("fire")
		_check("Paused entry ignores the mapped primary", events.is_empty())
		trial._resume.pressed.emit()
		# Render-time playback is covered by its own suite. This fixture
		# deliberately fast-forwards the simulation and keeps audio muted.
		trial.effects.set_options({"volume": 0.0})
		await _frames(12)
		_check("Begin Practice grounds the actual CharacterBody", not trial.paused and trial.hero.is_on_floor())
		for rule: Dictionary in trial.combat.report(false).abilities:
			trial.effects.set_options({"reduced_effects": false})
			var baseline := await _exercise(rule, false, false)
			trial.effects.set_options({"reduced_effects": true})
			var comparison := await _exercise(rule, true, true)
			_check(String(rule.id) + " equivalent fixed-step partitions and reduced FX preserve the timeline",
				not baseline.is_empty() and baseline == comparison)
		trial.effects.set_options({"reduced_effects": false})
		await _cancel_travel()
		await _reset_vault()
		await _overlap_fields()
		await _stress_primary()
	_check("All pinned input files are present and unchanged during the run",
		"" not in sources.values() and _source_hashes() == sources)
	var passed := checks.filter(func(check): return check.passed).size()
	var result := {"passed": passed, "failed": checks.size() - passed, "checks": checks,
		"scenarios": scenarios, "physics_hz": Engine.physics_ticks_per_second,
		"godot": Engine.get_version_info().string, "sources": sources}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var output := FileAccess.open(argument.trim_prefix("--report="), FileAccess.WRITE)
			if output != null:
				output.store_string(JSON.stringify(result, "  ") + "\n")
	print("YUGA_HANUMAN_ABILITY_INTEGRATION ", JSON.stringify(result))
	if trial.ready_for_play:
		trial.combat.ability_event.disconnect(_capture)
	trial.queue_free()
	await create_timer(.25).timeout
	quit(0 if passed == checks.size() else 1)
