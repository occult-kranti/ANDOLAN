extends SceneTree
## Independent real-world glue checks for the single Rama milestone.
## These assertions cannot establish finished anatomy, continuous visual quality,
## audible quality, physical-GPU performance, Windows or online authority.

const IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
const ORIGIN := Vector3(-40, .05, -10)
const STEP := .05
const SOURCE_PATHS := [
	"res://scripts/confluence_world.gd", "res://scripts/player.gd",
	"res://scripts/rama_ability_kit.gd", "res://scripts/rama_motion.gd",
	"res://scripts/rama_ability_effects.gd", "res://scripts/rama_vitals.gd",
	"res://scripts/rama_hero_runtime.gd", "res://scripts/rama_hero_hud.gd",
	"res://scripts/rama_hero_panel.gd", "res://scripts/input_bindings.gd",
	"res://assets/animations/rama_hero_motion.tres", "res://shaders/rama_ribbon.gdshader",
	"res://assets/design/rama-ability-kit.json",
	"res://tests/rama_hero_integration_cases.gd"
]

var scene: Node3D
var kit: Node3D
var motion: SkeletonModifier3D
var effects: Node3D
var checks: Array[Dictionary] = []
var events: Array[Dictionary] = []
var sources: Dictionary = {}
var output := "/tmp/rama-hero-integration.json"
var starting_nodes := 0
var started_usec := 0
var sample_costs: Array[float] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("_run")

func check(label: String, condition: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label, "passed":condition, "details":detail})
	print("PASS " if condition else "FAIL ", label, " ", JSON.stringify(detail))

func frames(count: int = 3) -> void:
	for _frame in range(count): await process_frame

func collect(event: Dictionary) -> void:
	# Bounded by the fixture, not an unbounded production history surrogate.
	if events.size() < 4096: events.append(event.duplicate(true))

func event_count(kind: String, cast_id: int = -1, generation: int = -1) -> int:
	var result := 0
	for event in events:
		if event.get("kind") == kind and (cast_id < 0 or event.get("cast_id") == cast_id) and (generation < 0 or event.get("generation") == generation): result += 1
	return result

func latest(kind: String) -> Dictionary:
	for index in range(events.size()-1, -1, -1):
		if events[index].get("kind") == kind: return events[index]
	return {}

func snapshot_receivers() -> Dictionary:
	var result := {}
	for unit in scene.army.units:
		if is_instance_valid(unit):
			result[str(unit.unit_id)] = {"health":unit.health, "shield":unit.shield, "alive":unit.alive, "position":unit.position}
	return result

func node_count(node: Node) -> int:
	if not is_instance_valid(node): return 0
	var result := 1
	for child in node.get_children(): result += node_count(child)
	return result

func disable_automatic_steps() -> void:
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	if effects: effects.set_process(false)

func advance(seconds: float, presentation_hz: int = 60) -> void:
	var remaining := seconds
	while remaining > .000001:
		var delta := minf(STEP, remaining)
		var started := Time.get_ticks_usec()
		scene.army.step_simulation(delta)
		# CharacterBody uses the real 60 Hz physics delta inside move_and_slide.
		# Advance three physical presentation ticks for each 20 Hz army step.
		var player_left := delta
		while player_left > .000001:
			var player_delta := minf(1.0/60.0, player_left)
			scene.player._physics_process(player_delta)
			player_left -= player_delta
		if effects and effects.has_method("step"):
			var visual_left := delta
			while visual_left > .000001:
				var visual_delta := minf(1.0 / presentation_hz, visual_left)
				effects.step(visual_delta)
				visual_left -= visual_delta
		if sample_costs.size() < 10000: sample_costs.append((Time.get_ticks_usec()-started)/1000.0)
		remaining -= delta

func fixture() -> Dictionary:
	scene.set_paused(false)
	scene._restart_army()
	disable_automatic_steps()
	scene.teleport_to(ORIGIN, 0.0)
	scene.player.yaw = PI
	scene.player.pitch = -.32
	scene.player._update_camera()
	# Actual CharacterBody grounding; no test assignment to is_on_floor().
	scene.player.set_physics_process(true)
	for _frame in range(8): await physics_frame
	scene.player.set_physics_process(false)
	scene.army._attacks.clear()
	scene.army._decision_clock = 100000.0
	scene.army._next_wave = 100000.0
	var ally: Node3D
	var enemy: Node3D
	for unit in scene.army.units:
		if unit.role == "commander" and unit.team == "sun" and not ally: ally = unit
		if unit.role == "commander" and unit.team == "moon" and not enemy: enemy = unit
	for unit in scene.army.units.duplicate():
		if unit != ally and unit != enemy:
			scene.army.units.erase(unit)
			unit.free()
	for unit in [ally, enemy]:
		unit.target = null
		unit.attack_time = 100000.0
		unit.attack_cooldown = 100000.0
	ally.position = ORIGIN + Vector3(2, -.05, 5)
	enemy.position = ORIGIN + Vector3(0, -.05, 6)
	ally.receive_damage(90.0, "army")
	for unit in [ally, enemy]: unit.previous_position = unit.position
	scene.army._rebuild_buckets()
	events.clear()
	return {"ally":ally, "enemy":enemy}

func align_receivers(targets: Dictionary, begin: Dictionary) -> void:
	if begin.get("ability_id") == "guardian_circle":
		targets.ally.global_position = begin.target + Vector3(.5, 0, 0)
		targets.enemy.global_position = begin.target + Vector3(0, 0, .5)
	else:
		targets.enemy.global_position = begin.origin + begin.forward * 5.0
	for unit in targets.values(): unit.previous_position = unit.position
	scene.army._rebuild_buckets()

func lifecycle_cases() -> void:
	for ability in IDS:
		var targets := await fixture()
		var accepted: Dictionary = scene.cast_rama_ability(ability)
		var begin := latest("begin")
		check(ability+": real world entry accepts exactly one draw", accepted.get("accepted", false) and event_count("begin") == 1 and begin.get("ability_id") == ability and scene.player.is_on_floor() and motion.diagnostics().action == ability and motion.diagnostics().stage == "windup", {"response":accepted})
		if not accepted.get("accepted", false) or begin.is_empty(): continue
		align_receivers(targets, begin)
		var before := snapshot_receivers()
		var motion_release_before: int = motion.diagnostics().release_count
		var rejected: Dictionary = scene.cast_rama_ability("piercing_dawn" if ability == "kodanda" else "kodanda")
		check(ability+": a second input cannot replace a committed action", not rejected.get("accepted", true) and event_count("begin") == 1 and kit.report().action_locked)
		# Deliberately advance the player/cosmetic clock with the army clock stopped.
		for _frame in range(60): scene.player._physics_process(1.0/60.0)
		check(ability+": presentation cannot authorize release", event_count("release") == 0 and snapshot_receivers() == before and kit.report().action_locked and motion.diagnostics().release_count == motion_release_before and motion.diagnostics().stage == "hold", {"motion":motion.diagnostics().get("stage", "")})
		if ability in ["piercing_dawn", "guardian_circle", "dawn_volley"]:
			var locked_position: Vector3 = scene.player.position
			Input.action_press("move_forward")
			Input.action_press("fire")
			for _frame in range(30): scene.player._physics_process(1.0/60.0)
			Input.action_release("move_forward")
			Input.action_release("fire")
			var horizontal_travel := Vector2(scene.player.position.x-locked_position.x, scene.player.position.z-locked_position.z).length()
			check(ability+": authority stall preserves movement and traversal commitment", horizontal_travel < .001 and not scene.player.toggle_flight() and not scene.player.try_grapple() and event_count("begin") == 1, {"travel_m":horizontal_travel})
		var pre_release := maxf(0, ceilf(float(begin.timing.windup_s)/STEP-1e-7)*STEP-STEP)
		advance(pre_release)
		check(ability+": no release or receiver mutation one authority tick early", event_count("release") == 0 and snapshot_receivers() == before)
		advance(STEP)
		check(ability+": first eligible army tick releases once", event_count("release") == 1 and event_count("release", accepted.cast_id, accepted.generation) == 1 and motion.diagnostics().get("stage") == "recovery" and motion.diagnostics().release_count == motion_release_before+1, {"release":latest("release"), "motion_stage":motion.diagnostics().get("stage", "")})
		advance(float(begin.timing.recovery_s)+.10)
		check(ability+": recovery restores action ownership", not kit.report().action_locked and event_count("release") == 1 and event_count("recovery") == 1)
		if ability in ["kodanda", "piercing_dawn", "dawn_volley"]:
			check(ability+": actual enemy health changes with a damage receipt", targets.enemy.health < float(before[str(targets.enemy.unit_id)].health) and event_count("impact") > 0, {"before":before[str(targets.enemy.unit_id)].health, "after":targets.enemy.health})
		elif ability == "guardian_circle":
			check("guardian_circle: real ally shield and healing; enemy unchanged", targets.ally.shield > 0 and targets.ally.health > float(before[str(targets.ally.unit_id)].health) and targets.enemy.health == float(before[str(targets.enemy.unit_id)].health), {"ally_health":targets.ally.health, "ally_shield":targets.ally.shield})
		elif ability == "measured_step":
			check("measured_step: accepted receiver moves actual CharacterBody", scene.player.position.distance_to(ORIGIN) > 1.0 and scene.player.position.distance_to(ORIGIN) < 5.2 and event_count("impact") == 1, {"position":str(scene.player.position)})
		advance(6.0)
		check(ability+": completed cast retires and never releases again", kit.report().casts.is_empty() and event_count("release") == 1 and event_count("end") == 1)

func pause_and_reset_matrix() -> void:
	for ability in IDS:
		for phase in ["windup", "released", "recovery"]:
			var targets := await fixture()
			var accepted: Dictionary = scene.cast_rama_ability(ability)
			var begin := latest("begin")
			if not accepted.get("accepted", false) or begin.is_empty():
				check(ability+"/"+phase+": pause fixture accepted", false, {"response":accepted})
				continue
			align_receivers(targets, begin)
			var release_tick := ceilf(float(begin.timing.windup_s)/STEP-1e-7)*STEP
			if phase == "released":
				advance(maxf(0, release_tick-STEP))
				scene.army.step_simulation(STEP)
			elif phase == "recovery": advance(release_tick+STEP)
			else: advance(maxf(0, release_tick-STEP))
			var entry_motion: Dictionary = motion.diagnostics()
			var entry_dash_time: float = scene.player.dash_time
			var entry_dash_direction: Vector3 = scene.player.dash_direction
			scene.set_paused(true)
			await frames(3)
			var before: Dictionary = kit.report()
			var receivers := snapshot_receivers()
			var event_total := events.size()
			var motion_before: Dictionary = motion.diagnostics()
			var pose_before: Vector3 = motion.socket_global("string_nock").origin
			var effects_before: Dictionary = effects.report()
			var denied: Dictionary = scene.cast_rama_ability(ability)
			# Engine frames and an accidental army emission both must leave the kit frozen.
			await frames(6)
			scene.army.simulation_stepped.emit(STEP)
			if effects and effects.has_method("step"): effects.step(.05)
			var after: Dictionary = kit.report()
			var frozen := {"request_denied":not denied.get("accepted", true), "clock":after.elapsed == before.elapsed, "cooldowns":after.cooldowns == before.cooldowns, "events":events.size() == event_total, "receivers":snapshot_receivers() == receivers, "motion_time":motion.diagnostics().get("action_elapsed") == motion_before.get("action_elapsed"), "socket":motion.socket_global("string_nock").origin.is_equal_approx(pose_before), "action":entry_motion.action == motion_before.action, "stage":entry_motion.stage == motion_before.stage, "dash_time":scene.player.dash_time == entry_dash_time, "dash_direction":scene.player.dash_direction == entry_dash_direction, "effects":effects.report().casts == effects_before.casts, "arrows":effects.report().live_arrows == effects_before.live_arrows}
			check(ability+"/"+phase+": pause freezes cast cooldown receivers and pose", frozen.values().all(func(value):return value), {"invariants":frozen, "entry_dash_time":entry_dash_time, "paused_dash_time":scene.player.dash_time, "entry_motion":entry_motion, "paused_motion":motion_before})
			scene.set_paused(false)
			advance(1.2)
			check(ability+"/"+phase+": resume never replays release", event_count("release", accepted.cast_id, accepted.generation) == 1)
			# A round reset must invalidate projectiles, fields, poses and delayed callbacks.
			var old_generation: int = accepted.generation
			scene._restart_army()
			disable_automatic_steps()
			var reset_state: Dictionary = kit.report()
			var reset_event_count := events.size()
			advance(2.0)
			var stale := false
			for index in range(reset_event_count, events.size()):
				stale = stale or int(events[index].get("generation", -1)) <= old_generation
			check(ability+"/"+phase+": round reset invalidates all prior action state", int(reset_state.generation) > old_generation and reset_state.casts.is_empty() and not reset_state.action_locked and reset_state.cooldowns.values().all(func(value): return is_zero_approx(float(value))) and not stale and not kit.report().action_locked and motion.diagnostics().get("action", "").is_empty(), {"generation":reset_state.generation, "stale_events":stale})

func cancel_matrix() -> void:
	for ability in IDS:
		for phase in ["windup", "released", "recovery"]:
			await fixture()
			var accepted: Dictionary = scene.cast_rama_ability(ability)
			var begin := latest("begin")
			if not accepted.get("accepted", false):
				check(ability+"/"+phase+": cancel fixture accepted", false)
				continue
			var release_tick := ceilf(float(begin.timing.windup_s)/STEP-1e-7)*STEP
			if phase == "released":
				advance(maxf(0, release_tick-STEP))
				scene.army.step_simulation(STEP)
			elif phase == "recovery": advance(release_tick+STEP)
			else: advance(maxf(0, release_tick-STEP))
			kit.cancel_active("independent_phase_probe")
			var after_cancel := snapshot_receivers()
			var player_after_cancel: Vector3 = scene.player.position
			var release_total := event_count("release")
			advance(2.0)
			check(ability+"/"+phase+": cancellation retires visuals and prevents delayed payload", kit.report().casts.is_empty() and not kit.report().action_locked and event_count("cancel") == 1 and event_count("release") == release_total and snapshot_receivers() == after_cancel and motion.diagnostics().get("action", "").is_empty() and (ability != "measured_step" or Vector2(scene.player.position.x-player_after_cancel.x, scene.player.position.z-player_after_cancel.z).length() < .001))

func screen_cases() -> void:
	for dimensions in [Vector2i(960,600), Vector2i(1280,720)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		scene.set_paused(true)
		await frames(6)
		var focus := root.gui_get_focus_owner()
		var viewport := Rect2(Vector2.ZERO, Vector2(dimensions))
		check("pause first action remains visible "+str(dimensions), focus == scene.pause_actions[0] and focus.is_visible_in_tree() and viewport.encloses(focus.get_global_rect()) and scene.pause_scroll.get_global_rect().grow(1).encloses(focus.get_global_rect()), {"focus":str(focus)})
		var open_event := InputEventAction.new()
		open_event.action = "open_invocations"
		open_event.pressed = true
		scene._unhandled_input(open_event)
		await frames(5)
		var panel: Control = scene.rama_panel
		focus = root.gui_get_focus_owner()
		check("F3 opens real Rama panel with visible keyboard focus "+str(dimensions), panel.visible and paused and not scene.pause_panel.visible and focus != null and panel.is_ancestor_of(focus) and focus.is_visible_in_tree() and viewport.encloses(focus.get_global_rect()))
		if panel.visible:
			check("Rama panel frame fits "+str(dimensions), viewport.encloses(panel.card.get_global_rect()), {"card":str(panel.card.get_global_rect())})
			panel.close()
			await frames(5)
			focus = root.gui_get_focus_owner()
			check("Rama panel close restores visible pause owner "+str(dimensions), not panel.visible and scene.pause_panel.visible and paused and focus == scene.rama_button and focus.is_visible_in_tree() and viewport.encloses(focus.get_global_rect()) and scene.pause_scroll.get_global_rect().grow(1).encloses(focus.get_global_rect()))
		scene.set_paused(false)
		Input.action_press("fire")
		scene.set_paused(true)
		scene.set_paused(false)
		check("closing modal neutralizes held fire "+str(dimensions), not Input.is_action_pressed("fire"))

func lifetime_cases() -> void:
	await fixture()
	var uninterrupted_ok := true
	# Contact blooms intentionally pool their nodes. Warm the actual released
	# projectile/contact path before measuring retained allocations; resets clear it.
	for _warm in range(3):
		uninterrupted_ok = uninterrupted_ok and scene.cast_rama_ability("kodanda").get("accepted", false)
		advance(1.30)
		await frames(1)
	var uninterrupted_baseline := node_count(kit)+node_count(effects)+node_count(motion)
	var uninterrupted_peak := uninterrupted_baseline
	for _index in range(32):
		if scene.player.ammo == 0:
			uninterrupted_ok = uninterrupted_ok and scene.player.start_reload()
			advance(1.70)
		var cast: Dictionary = scene.cast_rama_ability("kodanda")
		uninterrupted_ok = uninterrupted_ok and cast.get("accepted", false)
		advance(1.30)
		await frames(1)
		uninterrupted_peak = maxi(uninterrupted_peak, node_count(kit)+node_count(effects)+node_count(motion))
	var uninterrupted_state: Dictionary = kit.report()
	check("uninterrupted primary fire and real reload retain bounded completed-cast state", uninterrupted_ok and uninterrupted_peak == uninterrupted_baseline and uninterrupted_state.casts.is_empty() and uninterrupted_state.history_size <= uninterrupted_state.history_capacity, {"casts":32, "owned_nodes":uninterrupted_baseline, "peak_after_completion":uninterrupted_peak, "history_size":uninterrupted_state.history_size, "history_capacity":uninterrupted_state.history_capacity})
	await fixture()
	for _warm in range(3):
		scene.cast_rama_ability("kodanda")
		advance(.45)
		kit.reset("warmup")
		await frames(2)
	var base_owned := node_count(kit)+node_count(effects)+node_count(motion)
	var peak_owned := base_owned
	var all_accepted := true
	for index in range(100):
		var ability: String = IDS[index % IDS.size()]
		var accepted: Dictionary = scene.cast_rama_ability(ability)
		all_accepted = all_accepted and accepted.get("accepted", false)
		if accepted.get("accepted", false): advance(float(accepted.windup_s)+.15)
		kit.reset("bounded_cycle")
		scene.player.reset()
		scene.player.position = ORIGIN
		await frames(2)
		peak_owned = maxi(peak_owned, node_count(kit)+node_count(effects)+node_count(motion))
	await frames(4)
	var final_owned := node_count(kit)+node_count(effects)+node_count(motion)
	check("100 real-world cast/reset cycles keep owned nodes bounded", all_accepted and final_owned == base_owned and peak_owned <= base_owned and kit.report().casts.is_empty() and not kit.report().action_locked, {"cycles":100, "baseline_owned_nodes":base_owned, "peak_after_cleanup":peak_owned, "final_owned_nodes":final_owned, "all_requests_accepted":all_accepted})

func effect_transforms(node: Node, result: Dictionary = {}, path := ".") -> Dictionary:
	# Auto-generated Godot names contain process-wide instance counters. Match
	# the same deterministic child hierarchy, including class, across fresh casts.
	if node is Node3D: result[path+":"+node.get_class()] = node.global_transform
	for index in node.get_child_count(): effect_transforms(node.get_child(index), result, path+"/"+str(index))
	return result

func effect_surfaces(node: Node, result: Dictionary = {}, path := ".") -> Dictionary:
	if node is MeshInstance3D:
		var vertices := PackedVector3Array()
		if node.mesh:
			for surface in node.mesh.get_surface_count():
				var arrays: Array = node.mesh.surface_get_arrays(surface)
				vertices.append_array(arrays[Mesh.ARRAY_VERTEX])
		result[path] = {"visible":node.is_visible_in_tree(), "vertices":vertices}
	for index in node.get_child_count(): effect_surfaces(node.get_child(index), result, path+"/"+str(index))
	return result

func presentation_rate_cases() -> void:
	for ability in ["dawn_volley", "guardian_circle"]:
		var reference: Dictionary = {}
		for hz in [30, 60, 120]:
			var targets := await fixture()
			var accepted: Dictionary = scene.cast_rama_ability(ability)
			if not accepted.get("accepted", false):
				check(ability+": presentation fixture "+str(hz), false, {"response":accepted})
				continue
			align_receivers(targets, latest("begin"))
			advance(1.20, hz)
			var current := {"receivers":snapshot_receivers(), "release_count":event_count("release"), "transforms":effect_transforms(effects, {}), "surfaces":effect_surfaces(effects, {}), "casts":effects.report().casts}
			if reference.is_empty(): reference = current
			var transform_error := 0.0
			var same_nodes: bool = reference.transforms.keys() == current.transforms.keys()
			if same_nodes:
				for path in current.transforms:
					var a: Transform3D = reference.transforms[path]
					var b: Transform3D = current.transforms[path]
					transform_error = maxf(transform_error, a.origin.distance_to(b.origin))
					for axis in 3: transform_error = maxf(transform_error, a.basis[axis].distance_to(b.basis[axis]))
			var vertex_error := 0.0
			var vertices_sampled := 0
			var same_surfaces: bool = reference.surfaces.keys() == current.surfaces.keys()
			if same_surfaces:
				for path in current.surfaces:
					var a: Dictionary = reference.surfaces[path]
					var b: Dictionary = current.surfaces[path]
					same_surfaces = same_surfaces and a.visible == b.visible and a.vertices.size() == b.vertices.size()
					if a.vertices.size() == b.vertices.size():
						for index in a.vertices.size():
							vertex_error = maxf(vertex_error, a.vertices[index].distance_to(b.vertices[index]))
							vertices_sampled += 1
			var ages_match: bool = reference.casts.size() == current.casts.size()
			if ages_match:
				for index in current.casts.size(): ages_match = ages_match and absf(float(reference.casts[index].age_s)-float(current.casts[index].age_s)) < .00001
			check(ability+": equal elapsed time preserves gameplay and rendered effect geometry at "+str(hz)+" Hz", current.receivers == reference.receivers and current.release_count == 1 and same_nodes and transform_error < .0001 and same_surfaces and vertex_error < .0001 and ages_match, {"presentation_hz":hz, "maximum_transform_component_error":transform_error, "maximum_mesh_vertex_error_m":vertex_error, "mesh_vertices_sampled":vertices_sampled, "same_surfaces":same_surfaces, "effect_nodes":current.transforms.size(), "cast_ages_match":ages_match, "same_nodes":same_nodes, "same_receivers":current.receivers == reference.receivers, "release_count":current.release_count})

func siege_and_respawn_cases() -> void:
	await fixture()
	# Queue a real army cannon attack, then let its ordinary impact event reach
	# the hero receiver. The test does not call RamaVitals.receive_damage().
	var cannon = load("res://scripts/lane_minion.gd").new()
	cannon.setup(scene.army, scene.army.next_id, "moon", "cannon_cart", 1)
	scene.army.next_id += 1
	cannon.render_art = false
	cannon.position = ORIGIN + Vector3(0, -.05, 8)
	cannon.attack_time = 100000.0
	cannon.attack_cooldown = 100000.0
	scene.army.add_child(cannon)
	scene.army.units.append(cannon)
	scene.army._rebuild_buckets()
	var accepted: Dictionary = scene.cast_rama_ability("dawn_volley")
	var before: Dictionary = scene.player.vitals.report()
	scene.army._queue_siege_attack(cannon, scene.player.position, .05)
	advance(.05)
	check("real enemy cannon impact interrupts an unreleased draw", accepted.get("accepted", false) and scene.player.vitals.health == before.health-24.0 and event_count("cancel") == 1 and event_count("release") == 0 and motion.diagnostics().get("action") == "hit", {"health_before":before.health, "health_after":scene.player.vitals.health})
	for _hit in range(12):
		scene.army._queue_siege_attack(cannon, scene.player.position, .05)
		advance(.05)
	check("actual enemy impacts enter death and disable new actions", not scene.player.vitals.alive and not scene.player.active and kit.report().casts.is_empty() and not scene.cast_rama_ability("kodanda").get("accepted", true) and motion.diagnostics().get("action") == "death")
	scene.set_paused(true)
	var remaining: float = scene.player.vitals.report().respawn_remaining
	await frames(8)
	scene.army.simulation_stepped.emit(.05)
	check("pause cannot finish the death timer or revive the player", not scene.player.vitals.alive and scene.player.vitals.report().respawn_remaining == remaining and not scene.player.active)
	scene.set_paused(false)
	check("resuming a dead player does not bypass respawn", not scene.player.active)
	advance(3.10)
	check("army time respawns cleanly after actual defeat", scene.player.vitals.alive and scene.player.vitals.health == 300 and scene.player.active and kit.report().casts.is_empty() and not kit.report().action_locked and scene.player.ammo == 12 and scene.player.position.distance_to(scene.rama_runtime.spawn) < .15, {"position":str(scene.player.position), "spawn":str(scene.rama_runtime.spawn), "vitals":scene.player.vitals.report()})

func reentrant_round_reset_cases() -> void:
	for spec in [{"id":"kodanda", "phase":"begin"}, {"id":"guardian_circle", "phase":"release"}]:
		await fixture()
		var previous_generation: int = kit.generation
		var observer_state := {"resets":0}
		var observer := func(event: Dictionary):
			if event.get("kind") == spec.phase and observer_state.resets == 0:
				observer_state.resets += 1
				scene._restart_army()
				disable_automatic_steps()
		kit.ability_event.connect(observer)
		var accepted: Dictionary = scene.cast_rama_ability(spec.id)
		advance(1.0)
		kit.ability_event.disconnect(observer)
		var fresh_receivers := true
		for unit in scene.army.units:
			fresh_receivers = fresh_receivers and unit.alive and unit.health == unit.max_health and unit.shield == 0
		var reset_seen := false
		var stale_payload := false
		for event in events:
			if event.get("kind") == "reset" and int(event.generation) > previous_generation: reset_seen = true
			elif reset_seen and int(event.generation) <= previous_generation: stale_payload = true
		var response_safe: bool = not accepted.get("accepted", true) if spec.phase == "begin" else accepted.get("accepted", false)
		check(spec.id+": round reset inside "+spec.phase+" observer cannot commit stale ammo or payload", observer_state.resets == 1 and response_safe and kit.generation > previous_generation and scene.player.ammo == 12 and scene.player.shots_fired == 0 and fresh_receivers and scene.army.units.size() == 30 and not stale_payload and kit.report().casts.is_empty() and not kit.report().action_locked and not scene.player.rama_action_locked and effects.report().active == 0 and motion.diagnostics().action.is_empty(), {"response":accepted, "observer_resets":observer_state.resets, "generation":kit.generation, "ammo":scene.player.ammo, "fresh_receivers":fresh_receivers, "stale_payload":stale_payload})

func hud_phase_case() -> void:
	await fixture()
	var accepted: Dictionary = scene.cast_rama_ability("piercing_dawn")
	scene.rama_hud._refresh()
	var windup_note: String = scene.rama_hud.note.text
	advance(.65)
	scene.rama_hud._refresh()
	var released_note: String = scene.rama_hud.note.text
	check("visible HUD stops describing a draw after authoritative release", accepted.get("accepted", false) and event_count("release") == 1 and not released_note.is_empty() and released_note != windup_note and not released_note.to_lower().contains("drawing"), {"windup_note":windup_note, "released_note":released_note})
	advance(6.0)
	scene.rama_hud._refresh()
	check("visible HUD does not retain a completed action phase", kit.report().casts.is_empty() and not kit.report().action_locked and not scene.rama_hud.note.text.is_empty() and scene.rama_hud.note.text != windup_note and not scene.rama_hud.note.text.to_lower().contains("drawing"), {"completed_note":scene.rama_hud.note.text})

func _run() -> void:
	started_usec = Time.get_ticks_usec()
	starting_nodes = int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	for path in SOURCE_PATHS:
		if FileAccess.file_exists(path): sources[path] = FileAccess.get_sha256(path)
	root.size = Vector2i(1280,720)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	await frames(5)
	kit = scene.get("rama_kit")
	effects = scene.get("rama_effects")
	motion = scene.player.get("rama_motion")
	check("actual world owns new Rama kit motion effects and panel", scene.world_ready and kit != null and motion != null and effects != null and scene.get("rama_panel") != null and scene.has_method("cast_rama_ability"))
	if kit == null or motion == null or effects == null or not scene.has_method("cast_rama_ability"):
		await finish()
		return
	for node in [kit, motion, effects, scene.rama_panel]:
		var path: String = node.get_script().resource_path
		sources[path] = FileAccess.get_sha256(path)
	var hero_path: String = scene.player.get_script().get_script_constant_map().get("HERO_PATH", "")
	if FileAccess.file_exists(hero_path): sources[hero_path] = FileAccess.get_sha256(hero_path)
	var import_config := ConfigFile.new()
	var import_fresh := false
	if import_config.load(hero_path+".import") == OK:
		var imported_path: String = import_config.get_value("remap", "path", "")
		var md5_path := imported_path.get_basename()+".md5"
		if FileAccess.file_exists(imported_path) and FileAccess.file_exists(md5_path):
			var digest_match := RegEx.new()
			digest_match.compile("source_md5=\"([a-f0-9]+)\"")
			var found := digest_match.search(FileAccess.get_file_as_string(md5_path))
			import_fresh = found != null and found.get_string(1) == FileAccess.get_md5(hero_path)
			sources[imported_path] = FileAccess.get_sha256(imported_path)
	check("actual hero import matches current source asset bytes", import_fresh, {"source":hero_path})
	disable_automatic_steps()
	kit.ability_event.connect(collect)
	check("new full-body owner replaces old competing pose modifiers", scene.player.get("hero_pose") == null and scene.player.get("traversal_pose") == null and motion.diagnostics().get("configured", false))
	await lifecycle_cases()
	await pause_and_reset_matrix()
	await cancel_matrix()
	await screen_cases()
	await presentation_rate_cases()
	await siege_and_respawn_cases()
	await reentrant_round_reset_cases()
	await hud_phase_case()
	await lifetime_cases()
	await finish()

func finish() -> void:
	paused = false
	if is_instance_valid(scene):
		var owner_id := scene.get_instance_id()
		scene.queue_free()
		await frames(5)
		check("world teardown releases owned scene", not is_instance_id_valid(owner_id) and int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)) == starting_nodes, {"baseline_nodes":starting_nodes, "remaining_nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))})
	var stable := true
	for path in sources: stable = stable and FileAccess.get_sha256(path) == sources[path]
	check("tested source bytes remain unchanged during run", stable)
	var passed := not checks.is_empty()
	for item in checks: passed = passed and item.passed
	sample_costs.sort()
	var cpu := {"samples":sample_costs.size(), "scope":"Headless synchronous army plus player plus effects step wall time in this shared software container; excludes rendered GPU work and is not FPS."}
	if not sample_costs.is_empty():
		cpu["median_ms"] = sample_costs[sample_costs.size()/2]
		cpu["p95_ms"] = sample_costs[mini(sample_costs.size()-1, int(sample_costs.size()*.95))]
		cpu["maximum_ms"] = sample_costs[-1]
	var report := {"passed":passed, "checks":checks, "source_sha256":sources, "engine":Engine.get_version_info().string, "wall_seconds":(Time.get_ticks_usec()-started_usec)/1000000.0, "cpu_step_observations":cpu, "scope":"Actual native world kit, body/controller, real troop receivers, pause/reset/cancel integration and headless UI focus/layout. Art, continuous visual contact, audio listening, OS input, physical-GPU FPS, Windows and online authority require separate evidence."}
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(report, "\t")+"\n")
	else: passed = false
	print("RAMA_HERO_INTEGRATION ", JSON.stringify({"passed":passed, "checks":checks.size(), "report":output}))
	quit(0 if passed else 1)
