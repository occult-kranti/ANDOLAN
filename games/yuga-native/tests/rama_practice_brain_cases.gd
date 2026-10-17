extends SceneTree
## Isolated AI decisions plus actual geometry/kit admission, no new hero actor.
const Brain = preload("res://scripts/rama_practice_brain.gd")
const Geometry = preload("res://scripts/lane_army.gd")
const Practice = preload("res://scripts/rama_practice_army.gd")
const Target = preload("res://scripts/target.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const DEFAULT_CANDIDATES := [{"id":"enemy-a", "team":"moon", "alive":true, "observed":true, "position":Vector3(0, 0, 12)}]
var checks: Array = []
var brain
var geometry
var tick := 0
var now := 0.0
var changed_input := false
var mutation_input := {}
var callback_reset := false
var callback_reenter := false
var nested := {}

func _initialize() -> void: call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"case":label, "passed":passed, "evidence":details})
	if not passed: push_error("PRACTICE BRAIN FAILED: " + label)

func cooldowns(value := 0.0) -> Dictionary:
	var result := {}
	for id in Brain.ABILITIES: result[id] = value
	return result

func enemy(id := "enemy-a", position := Vector3(0, 0, 12)) -> Dictionary:
	return {"id":id, "team":"moon", "alive":true, "observed":true, "position":position}

func observation(candidates: Array = DEFAULT_CANDIDATES) -> Dictionary:
	return {"actor_id":"practice-rama", "session_id":"test-session", "generation":7, "tick":tick, "time_s":now, "paused":false, "ended":false, "alive":true, "grounded":true, "action_locked":false, "movement_locked":false, "team":"sun", "position":Vector3.ZERO, "yaw":0.0, "max_health":300.0, "health":300.0, "shield":0.0, "ammo":12, "cooldowns":cooldowns(), "candidates":candidates.duplicate(true)}

func fresh(difficulty := "standard") -> void:
	brain = Brain.new(); tick = 0; now = 0.0; geometry.boxes.clear()
	changed_input = false; mutation_input.clear(); callback_reset = false; callback_reenter = false; nested.clear()
	assert(brain.configure("practice-rama", "test-session", 7, difficulty))

func clear_path(from: Vector3, to: Vector3, margin: float):
	if callback_reset: callback_reset = false; brain.reset(8)
	if callback_reenter:
		callback_reenter = false
		nested = brain.decide(.05, now, observation(), clear_path, steer)
	if changed_input:
		changed_input = false
		mutation_input.candidates[0].position = Vector3(99, 0, 99)
	return geometry.line_clear(from, to, margin)

func steer(_origin: Vector3, desired: Vector3, _lookahead: float) -> Vector3:
	return desired

func next(candidates: Array = DEFAULT_CANDIDATES, overrides: Dictionary = {}) -> Dictionary:
	tick += 1; now += .05
	var input := observation(candidates); input.merge(overrides, true)
	return brain.decide(.05, now, input, clear_path, steer)

func ready(candidates: Array = DEFAULT_CANDIDATES, overrides: Dictionary = {}) -> Dictionary:
	var result := {}
	for index in 10:
		result = next(candidates, overrides)
		if not result.ability_id.is_empty() or result.reload: break
	return result

func run() -> void:
	geometry = Geometry.new()
	var unconfigured = Brain.new()
	check("Unconfigured decision fails closed", not unconfigured.decide(.05, 0.0, {}, clear_path, steer).valid)
	check("Configuration rejects invalid identity, generation and difficulty", not unconfigured.configure("", "session", 0) and not unconfigured.configure("hero", "session", -1) and not unconfigured.configure("hero", "session", 0, "impossible"))
	fresh()
	check("Exactly one binding and bounded difficulty profile", not brain.configure("other", "session", 0) and brain.report().profile.speed_mps <= 6 and brain.report().unsupported.has("second_native_hero_authority"))
	check("Reset rejects reused or regressing actor generations", not brain.reset(7) and not brain.reset(6) and brain.report().generation == 7)
	var first := next()
	check("First sight waits before movement, aim or abilities", first.state == "react" and first.move_direction == Vector3.ZERO and first.ability_id.is_empty() and first.yaw == 0)
	for index in 4: first = next()
	check("Standard reaction does not fire at 200 ms", first.ability_id.is_empty() and first.move_direction == Vector3.ZERO)
	first = next()
	check("A visible grounded opponent permits one deliberate intent after reaction", first.valid and first.ability_id == "piercing_dawn" and first.target_id == "enemy-a", first)
	var after := next()
	check("Intent cadence prevents repeated calls while cooldown snapshot remains ready", after.ability_id.is_empty() and brain.report().emitted_intents == 1)
	var duplicate: Dictionary = brain.decide(.05, now, observation(), clear_path, steer)
	check("Duplicate authority tick neutralizes held controls", not duplicate.valid and duplicate.move_direction == Vector3.ZERO and duplicate.ability_id.is_empty())
	fresh(); ready()
	var prior_yaw: float = brain._yaw
	geometry.boxes = [{"position":Vector3(0, 2, 6), "size":Vector3(20, 4, .001)}]
	var blocked := next([enemy("enemy-a", Vector3(3, 0, 12))], {"yaw":prior_yaw})
	check("Actual thin wall loses target without tracking new hidden position", blocked.valid and blocked.target_id.is_empty() and blocked.move_direction == Vector3.ZERO and blocked.ability_id.is_empty() and blocked.yaw == prior_yaw and brain.report().target_id.is_empty())
	geometry.boxes.clear()
	check("Reappearance requires a new reaction window", next().state == "react")
	fresh()
	var friend := enemy("friend"); friend.team = "sun"
	var unseen := enemy("unseen"); unseen.observed = false
	var dead := enemy("dead"); dead.alive = false
	var absent := next([friend, unseen, dead, enemy("behind", Vector3(0, 0, -10)), enemy("high", Vector3(0, 3, 10)), enemy("distant", Vector3(0, 0, 41))])
	check("No friendly, dead, unobserved, rear, elevated or out-of-range acquisition", absent.target_id.is_empty() and absent.ability_id.is_empty())
	fresh(); var tie := next([enemy("z"), enemy("a")])
	check("Exact distance ties use stable identity, not array order", tie.target_id == "a")
	var retained := next([enemy("z", Vector3(0, 0, 11)), enemy("a")])
	check("Visible near-equal target retention avoids selection oscillation", retained.target_id == "a")
	fresh("hard"); next([enemy("side", Vector3(10, 0, 3))]); next([enemy("side", Vector3(10, 0, 3))]); next([enemy("side", Vector3(10, 0, 3))])
	var turn := next([enemy("side", Vector3(10, 0, 3))])
	check("Aim turns within profile rate instead of snapping to a new target", absf(turn.yaw) > 0 and absf(turn.yaw) <= float(brain.report().profile.turn_radians_s) * .05 + 1e-7 and turn.ability_id.is_empty(), {"yaw":turn.yaw})
	var denied_turn := next([enemy("side", Vector3(10, 0, 3))])
	check("Unapplied turn cannot accumulate fictional local authority aim", absf(denied_turn.yaw) <= float(brain.report().profile.turn_radians_s) * .05 + 1e-7)
	fresh("hard")
	var movement := ready([enemy("far", Vector3(0, 0, 30))], {"cooldowns":cooldowns(60.0)})
	check("Approach is planar, unit bounded and no faster than actual walk speed", movement.state == "approach" and movement.move_direction.is_equal_approx(Vector3(0, 0, 1)) and movement.speed_mps == 6.0 and movement.ability_id.is_empty())
	var bad_steer := func(_a, _b, _c): return Vector3(0, 1, 100)
	tick += 1; now += .05
	var bad_move: Dictionary = brain.decide(.05, now, observation([enemy("far", Vector3(0, 0, 30))]), clear_path, bad_steer)
	check("Nonplanar unbounded steering fails closed", not bad_move.valid and bad_move.move_direction == Vector3.ZERO)
	fresh("hard")
	var weave := ready([enemy()], {"cooldowns":cooldowns(60.0)})
	geometry.boxes = [{"position":Vector3(signf(weave.move_direction.x) * .5, 2, 0), "size":Vector3(.001, 4, .2)}]
	var safe_stop := next([enemy()], {"cooldowns":cooldowns(60.0)})
	check("Movement checks actor-width cover independently of the shot corridor", safe_stop.target_id == "enemy-a" and safe_stop.move_direction == Vector3.ZERO and safe_stop.ability_id.is_empty())
	fresh("hard")
	var low := ready([enemy("near", Vector3(0, 0, 4))], {"health":90.0})
	check("Low-health protection requests the real self-centred Guardian ability", low.ability_id == "guardian_circle" and low.ground_target == Vector3.ZERO and low.move_direction == Vector3.ZERO)
	fresh("hard")
	var escape_cooldowns := cooldowns(); escape_cooldowns.guardian_circle = 10.0
	var escape := ready([enemy("near", Vector3(0, 0, 4))], {"health":90.0, "cooldowns":escape_cooldowns})
	check("Close visible threat requests a bounded retreat step without invulnerability", escape.ability_id == "measured_step" and escape.step_direction.is_equal_approx(Vector3(0, 0, -1)))
	fresh("hard")
	var volley := ready([enemy("center", Vector3(0, 0, 10)), enemy("right", Vector3(1.05, 0, 10))])
	check("Volley waits for multiple visible firing-lane targets", volley.ability_id == "dawn_volley", volley)
	fresh("hard")
	var single_lane := ready([enemy("front", Vector3(0, 0, 10)), enemy("back", Vector3(0, 0, 12))])
	check("Two enemies behind one first-hit lane prefer Piercing Dawn to Volley", single_lane.ability_id == "piercing_dawn", single_lane)
	fresh("hard")
	var reload := ready([enemy()], {"ammo":0})
	check("Empty bow emits reload intent without granting ammunition", reload.reload and reload.ability_id.is_empty() and not next([enemy()], {"ammo":0}).reload)
	fresh("hard")
	var locked := ready([enemy()], {"action_locked":true, "movement_locked":true})
	check("Authority action/movement locks block attacks and movement", locked.ability_id.is_empty() and locked.move_direction == Vector3.ZERO)
	for state in ["paused", "ended", "dead", "airborne"]:
		fresh(); var overrides := {}
		if state == "dead": overrides = {"alive":false, "health":0.0}
		elif state == "airborne": overrides.grounded = false
		else: overrides[state] = true
		var stopped := next([enemy()], overrides)
		check("Lifecycle neutralizes " + state, not stopped.valid and stopped.state == state and stopped.move_direction == Vector3.ZERO and stopped.ability_id.is_empty() and not stopped.reload)
	fresh(); next(); now += .4
	check("Long observation gap restarts reaction instead of catching up", next().state == "react")
	for invalid in ["sample_age", "future_time", "generation", "identity", "session", "nan_position", "missing_cooldown", "oversized_candidates", "duplicate_candidates", "inconsistent_alive"]:
		fresh(); tick = 1; now = 1.0; var input := observation()
		match invalid:
			"sample_age": input.time_s = .8
			"future_time": input.time_s = 1.1
			"generation": input.generation = 8
			"identity": input.actor_id = "other"
			"session": input.session_id = "old-session"
			"nan_position": input.position = Vector3(NAN, 0, 0)
			"missing_cooldown": input.cooldowns.erase("kodanda")
			"oversized_candidates":
				input.candidates = []
				for index in 97: input.candidates.append(enemy(str(index)))
			"duplicate_candidates": input.candidates = [enemy(), enemy()]
			"inconsistent_alive": input.health = 0
		var invalid_result: Dictionary = brain.decide(.05, now, input, clear_path, steer)
		check("Reject malformed authority " + invalid, not invalid_result.valid and invalid_result.ability_id.is_empty() and invalid_result.move_direction == Vector3.ZERO)
	fresh(); next()
	check("Invalid and regressing clocks never advance decisions", not brain.decide(NAN, now, observation(), clear_path, steer).valid and not brain.decide(.2, now, observation(), clear_path, steer).valid and not brain.decide(.05, now - .01, observation(), clear_path, steer).valid)
	fresh(); next(); tick += 1
	check("A new tick at the same clock cannot accelerate aim or reaction", not brain.decide(.05, now, observation(), clear_path, steer).valid)
	fresh(); tick = 1; now = .05
	var extra := observation(); extra.unbounded = {"payload":[]}
	check("Unknown nested payloads reject before observation duplication", not brain.decide(.05, now, extra, clear_path, steer).valid)
	check("Missing authority geometry callbacks cannot admit a decision", not brain.decide(.05, now, observation(), Callable(), steer).valid)
	fresh(); callback_reset = true
	check("A reset inside a geometry callback invalidates the entire old-generation result", not next().valid and brain.report().generation == 8 and brain.report().target_id.is_empty())
	fresh(); callback_reenter = true
	var outer := next()
	check("Reentrant callback cannot create an extra action", outer.valid and not nested.valid and nested.ability_id.is_empty() and brain.report().accepted_observations == 1)
	fresh(); tick = 1; now = .05; mutation_input = observation(); changed_input = true
	var detached: Dictionary = brain.decide(.05, now, mutation_input, clear_path, steer)
	check("Geometry callbacks cannot alias-mutate the detached observation", detached.target_id == "enemy-a" and mutation_input.candidates[0].position.x == 99)
	var report_copy: Dictionary = brain.report(); report_copy.profile.speed_mps = 1000
	check("Reports cannot mutate internal difficulty", brain.report().profile.speed_mps <= 6)
	var sequences: Array = []
	for run_index in 2:
		fresh(); var sequence: Array = []
		for index in 80:
			var decision := next([enemy("fixed", Vector3(4, 0, 15))])
			sequence.append([decision.yaw, decision.move_direction, decision.ability_id, decision.reload])
		sequences.append(sequence)
	check("Same actor, difficulty and observations produce identical decisions", sequences[0] == sequences[1])
	# This is a caller/kit compatibility fixture, not a second native hero actor.
	var target := Target.new(); root.add_child(target); target.position = Vector3(0, 0, 5)
	var army := Practice.new(); root.add_child(army); army.set_physics_process(false)
	var kit := Kit.new(); root.add_child(kit)
	check("Existing real practice army and Rama kit configure", army.configure([target]) and kit.configure(army))
	brain = Brain.new(); tick = 0; now = 0.0; assert(brain.configure("practice-rama", "test-session", kit.generation, "hard"))
	var actual_input := observation([enemy("bullseye", target.global_position)]); actual_input.generation = kit.generation
	var proposed := {}
	for index in 4:
		tick += 1; now += .05; actual_input.tick = tick; actual_input.time_s = now; actual_input.cooldowns = kit.report().cooldowns
		proposed = brain.decide(.05, now, actual_input, army.line_clear, func(_o, _d, _l): return Vector3.ZERO)
	check("Brain alone never applies damage or starts casts", army.units[0].health == 90 and kit.accepted_casts == 0 and proposed.ability_id == "kodanda")
	var admitted: Dictionary = kit.request_ability(proposed.ability_id, Vector3.ZERO, proposed.aim, proposed.ground_target)
	for index in 12: army.step_simulation(.05)
	check("Explicit caller can submit the intent through the real kit for one real hit", admitted.accepted and kit.accepted_casts == 1 and army.units[0].health == 62 and kit.release_count == 1, {"target_health":army.units[0].health, "accepted_casts":kit.accepted_casts, "releases":kit.release_count})
	var report := {"suite":"rama_practice_brain_cases", "passed":checks.all(func(entry): return entry.passed), "checks":checks, "scope":"Headless deterministic grounded decisions, actual lane geometry and explicit real-kit caller compatibility. No integrated second hero, rendered bot, online match, aim-feel or hardware performance claim.", "source_sha256":{}}
	for path in ["res://scripts/rama_practice_brain.gd", "res://scripts/lane_army.gd", "res://scripts/rama_practice_army.gd", "res://scripts/rama_practice_target.gd", "res://scripts/target.gd", "res://scripts/rama_ability_kit.gd", "res://assets/design/rama-ability-kit.json", "res://tests/rama_practice_brain_cases.gd"]: report.source_sha256[path] = FileAccess.get_sha256(path)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var path := arg.trim_prefix("--report="); DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			var file := FileAccess.open(path, FileAccess.WRITE); file.store_string(JSON.stringify(report, "  ")); file.close()
	print("Rama practice brain checks: %d/%d" % [checks.filter(func(entry): return entry.passed).size(), checks.size()])
	kit.free(); army.free(); target.free(); geometry.free()
	quit(0 if report.passed else 1)
