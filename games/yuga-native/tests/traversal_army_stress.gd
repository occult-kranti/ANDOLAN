extends SceneTree
## Independent integrated native-world checks. Physical movement uses actual
## physics frames; the long army sweep below is explicitly accelerated 20 Hz.
## No OS-input, audible-quality, hardware-performance or multiplayer claim.

var checks: Array[Dictionary] = []
var output := ""
var scene
var player
var source_before: Dictionary = {}
var physical_frames := 0
var simulated_ticks := 0
var traversal_events: Array[String] = []
var driver: PhysicsDriver

class PhysicsDriver extends Node:
	signal stepped
	var pending: Callable
	func _physics_process(_delta: float) -> void:
		if pending.is_valid():
			var call := pending
			pending = Callable()
			call.call()
			stepped.emit()

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name": label, "passed": passed, "details": details})
	print("PASS " if passed else "FAIL ", label)

func frames(count: int) -> void:
	for unused in range(count):
		await physics_frame
		physical_frames += 1
	await process_frame

func process_frames(count: int) -> void:
	for unused in range(count): await process_frame

func act(callback: Callable) -> void:
	driver.pending = callback
	await driver.stepped
	await process_frame

func release() -> void:
	for action in ["move_left", "move_right", "move_forward", "move_back", "jump", "sprint", "dash", "fire", "fly", "grapple", "descend", "pulse"]:
		if InputMap.has_action(action): Input.action_release(action)

func vec(values: Array) -> Vector3:
	return Vector3(values[0], values[1], values[2])

func input_key(code: int) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	root.push_input(event)
	await process_frames(2)
	event = InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = false
	root.push_input(event)
	await process_frames(2)

func teleport(point: Vector3) -> void:
	release()
	scene.set_paused(false)
	scene.teleport_to(point, 180.0)
	await frames(3)

func unit_count(army) -> int:
	var count := 0
	for child in army.get_children():
		if child.get("unit_id") != null: count += 1
	return count

func audio_player_count(node: Node) -> int:
	var count := 1 if node is AudioStreamPlayer or node is AudioStreamPlayer3D else 0
	for child in node.get_children(): count += audio_player_count(child)
	return count

func enemy_of_role(army, role: String):
	for unit in army.units:
		if is_instance_valid(unit) and unit.alive and unit.team == "moon" and unit.role == role: return unit
	return null

func run() -> void:
	root.size = Vector2i(1280, 720)
	root.content_scale_size = Vector2i(1280, 720)
	for path in ["res://scripts/confluence_world.gd", "res://scripts/player.gd", "res://scripts/player_traversal.gd", "res://scripts/traversal_pose.gd", "res://scripts/traversal_landmarks.gd", "res://scripts/lane_army.gd", "res://scripts/lane_minion.gd", "res://scripts/lane_unit_art.gd", "res://scripts/input_bindings.gd", "res://scripts/controls_overlay.gd", "res://scripts/traversal_audio.gd", "res://assets/world/confluence-map.json", "res://tests/traversal_army_stress.gd"]:
		source_before[path] = FileAccess.get_sha256(path)
	var result := change_scene_to_file("res://scenes/confluence_world.tscn")
	if result != OK:
		record("actual world scene loads", false, {"error": result})
		finish()
		return
	await scene_changed
	scene = current_scene
	await frames(5)
	var ready: bool = scene.get("world_ready") == true and scene.get("army") != null and scene.get("audio") != null and scene.get("controls_overlay") != null
	record("world owns configured traversal army audio and controls", ready)
	if not ready:
		finish()
		return
	player = scene.player
	driver = PhysicsDriver.new()
	driver.process_physics_priority = -100
	root.add_child(driver)
	player.traversal_event.connect(func(kind: String, _point: Vector3): traversal_events.append(kind))
	root.focus_entered.emit()
	var army = scene.army
	var initial: Dictionary = army.report()
	record("six lane-team formations are live on actual scene entry", initial.configured and initial.alive == 30 and scene.manifest.lanes.size() == 3, initial)
	record("native bounds and separate collision domains present", scene.native_platform_bodies.size() == 8 and scene.authority_bodies.size() == 8 and player.traversal_report().anchor_count == 10 and scene.manifest.bounds.nominal_size_xz[0] == 140 and scene.manifest.bounds.nominal_size_xz[1] == 260, {"native_platforms": scene.native_platform_bodies.size(), "browser_boxes": scene.authority_bodies.size()})
	# Freeze only the army scheduler during independent movement fixtures.
	army.set_physics_process(false)
	var landings: Array = []
	var landing_ok := true
	for deck in scene.manifest.traversal.native_collision_boxes:
		var top: float = float(deck.position[1]) + float(deck.size[1])
		await teleport(vec(deck.position) + Vector3.UP * (float(deck.size[1]) + 2.5))
		await frames(60)
		var difference: float = absf(player.position.y - top)
		var correct: bool = player.is_on_floor() and difference < .02 and player.global_position.is_finite()
		landings.append({"id": deck.id, "floor_error_m": difference, "grounded": player.is_on_floor()})
		landing_ok = landing_ok and correct
	record("actual capsule lands on all eight native decks", landing_ok, {"landings": landings, "tolerance_m": .02})
	# Stamina must not recover while hovering even with a floor directly below.
	await teleport(Vector3(20, 8.05, -88))
	await frames(5)
	var takeoff: bool = player.toggle_flight()
	Input.action_press("jump")
	await frames(45)
	release()
	var deck_energy: float = player.traversal.energy
	await frames(20)
	record("platform takeoff spends stamina and never grounded-recharges in flight", takeoff and player.position.y > 9 and player.traversal.energy < deck_energy and player.traversal.energy < 80 and not player.is_on_floor(), {"energy": player.traversal.energy, "feet_y": player.position.y})
	# These are actual authored rings, not test-only anchors. The enlarged hero
	# capsule and real platform colliders participate in both spawn approaches.
	for fixture in [
		{"spawn": Vector3(0,.05,-112), "anchor": "sun-lift-west-ring"},
		{"spawn": Vector3(0,.05,112), "anchor": "moon-lift-east-ring"}]:
		await teleport(fixture.spawn)
		var anchor: Dictionary = {}
		for candidate in scene.manifest.traversal.anchors:
			if candidate.id == fixture.anchor: anchor = candidate
		var point := vec(anchor.position)
		player.camera.look_at(point, Vector3.UP)
		var before: float = (player.position+Vector3.UP*1.15).distance_to(point)
		await act(func(): player.try_grapple())
		var attached: bool = player.traversal.mode == "grapple" and player.traversal.rope.visible
		var highest_speed := 0.0
		var closest := before
		for unused in range(120):
			await frames(1)
			highest_speed = maxf(highest_speed,player.velocity.length())
			closest = minf(closest,(player.position+Vector3.UP*1.15).distance_to(point))
		record("visible native ring pulls player from " + String(fixture.anchor), attached and closest < 3.0 and highest_speed <= 18.001 and player.position.is_finite(), {"start_chest_distance_m": before,"closest_chest_distance_m":closest,"max_speed":highest_speed,"final_mode":player.traversal.mode})
		player.cancel_traversal("fixture finished")
	# All four physical edge approaches use actual flight integration.
	var bound_ok := true
	var edge_results: Array = []
	var boundary: Array = scene.manifest.bounds.actor_xz
	var radius: float = scene.manifest.bounds.hero_radius
	for fixture in [
		{"p": Vector3(boundary[1]-radius-.3, 3, 0), "action": "move_right"},
		{"p": Vector3(boundary[0]+radius+.3, 3, 0), "action": "move_left"},
		{"p": Vector3(0, 3, boundary[2]+radius+.3), "action": "move_forward"},
		{"p": Vector3(0, 3, boundary[3]-radius-.3), "action": "move_back"}]:
		await teleport(fixture.p)
		player.toggle_flight()
		Input.action_press(fixture.action)
		await frames(45)
		var p: Vector3 = player.position
		bound_ok = bound_ok and p.is_finite() and p.x >= boundary[0]+radius-.001 and p.x <= boundary[1]-radius+.001 and p.z >= boundary[2]+radius-.001 and p.z <= boundary[3]-radius+.001
		edge_results.append({"input": fixture.action, "position": [p.x,p.y,p.z], "speed": player.velocity.length()})
		release()
	record("all four expanded edges retain the full capsule", bound_ok, {"edges": edge_results})
	await teleport(Vector3(0, 23.8, -60))
	player.toggle_flight()
	Input.action_press("jump")
	Input.action_press("dash")
	await frames(90)
	record("world ceiling and flight dash exclusion hold together", player.position.y <= 24.001 and player.velocity.length() <= 12.001 and player.dash_time == 0 and player.position.is_finite(), {"feet_y": player.position.y, "speed": player.velocity.length()})
	release()
	# Pausing freezes army, movement and existing effects, and suppresses audio.
	army.set_physics_process(true)
	await teleport(Vector3(0, .05, -112))
	player.toggle_flight()
	Input.action_press("move_forward")
	Input.action_press("jump")
	await frames(8)
	scene.set_paused(true)
	var at_pause: Vector3 = player.position
	var elapsed_pause: float = army.elapsed
	await frames(12)
	var sound: Dictionary = scene.audio.get_diagnostics()
	record("pause freezes army and movement while cancelling traversal and audio", player.position == at_pause and army.elapsed == elapsed_pause and player.velocity == Vector3.ZERO and player.traversal.mode == "ground" and not Input.is_action_pressed("jump") and sound.suspended and sound.playing_cues == 0, sound)
	scene.set_paused(false)
	await frames(4)
	record("resume releases held horizontal movement", not Input.is_action_pressed("move_forward") and absf(player.position.z-at_pause.z) < .001 and army.elapsed > elapsed_pause)
	scene.set_overview(true)
	var elapsed_overview: float = army.elapsed
	await frames(12)
	record("atlas freezes army and suppresses traversal input and sound", army.elapsed == elapsed_overview and not player.active and scene.audio.get_diagnostics().suspended and not player.toggle_flight())
	scene.set_overview(false)
	await frames(4)
	record("atlas exit resumes army with neutral movement", army.elapsed > elapsed_overview and player.active and player.velocity.x == 0 and player.velocity.z == 0)
	# Exercise the actual overlay input dispatch; no direct binding save occurs.
	player.toggle_flight()
	Input.action_press("move_right")
	scene._open_controls()
	scene.controls_overlay.begin_capture("fly")
	await input_key(KEY_ESCAPE)
	record("Escape cancels remap capture without unpausing world", scene.controls_overlay.visible and scene.controls_overlay.capture_action.is_empty() and scene.paused and not Input.is_action_pressed("move_right") and player.traversal.mode == "ground")
	scene.controls_overlay.begin_capture("grapple")
	root.focus_exited.emit()
	await process_frames(3)
	record("focus loss cancels pending capture and retains visible paused controls", scene.controls_overlay.visible and scene.controls_overlay.capture_action.is_empty() and scene.paused and not player.active and scene.audio.get_diagnostics().suspended)
	root.focus_entered.emit()
	for size_ in [Vector2i(1280,720), Vector2i(960,600)]:
		root.size = size_
		root.content_scale_size = size_
		await process_frames(5)
		var layout: Dictionary = scene.controls_overlay.diagnostics()
		var card: Rect2 = layout.card_rect
		var viewport: Rect2 = layout.viewport
		record("controls card remains inside viewport %dx%d" % [size_.x,size_.y], viewport.encloses(card) and layout.button_count == 12, {"card": str(card), "viewport": str(viewport)})
	await input_key(KEY_ESCAPE)
	record("closing controls after focus loss returns to pause", not scene.controls_overlay.visible and scene.paused and scene.pause_panel.visible)
	scene.set_paused(false)
	army.set_physics_process(false)
	# Dispatch a real projectile through the world's fired signal into a unit.
	army.reset()
	var target = enemy_of_role(army, "spearman")
	target.position = Vector3(0,0,-40)
	await teleport(Vector3(0,.05,-35))
	scene.audio.set_volume(.6)
	await frames(2)
	var health_before: float = target.health
	var audio_before: Dictionary = scene.audio.get_diagnostics()
	player.fired.emit(Vector3(0,1,-35), Vector3(0,0,-1), false)
	await frames(15)
	var audio_after: Dictionary = scene.audio.get_diagnostics()
	record("world projectile damages opposing unit through actual collision", is_instance_valid(target) and target.health == health_before-25, {"health_before": health_before, "health_after": target.health if is_instance_valid(target) else -1})
	record("projectile impact reaches bounded world audio pool", audio_after.played_events > audio_before.played_events and audio_player_count(scene.audio) == 7, {"before": audio_before, "after": audio_after})
	# Last-hit reward and pulse wiring share the actual world wallet/HUD callback.
	var reward_ok := true
	var expected := 0
	for role in ["spearman", "bow_guard", "commander"]:
		var enemy = enemy_of_role(army, role)
		var value: int = 18 if role == "spearman" else (24 if role == "bow_guard" else 45)
		expected += value
		var accepted: bool = enemy.take_hit(1000)
		var repeated: bool = enemy.take_hit(1000)
		reward_ok = reward_ok and accepted and not repeated and army.gold == expected
	record("all roles award exact last-hit gold once through world wallet", reward_ok and scene.last_gold == expected and expected == 87, {"gold": army.gold, "kills": army.kills})
	army.reset()
	target = enemy_of_role(army, "spearman")
	target.position = Vector3(0,0,-40)
	await frames(2)
	player.pulse.emit(Vector3(0,1,-40))
	record("player pulse signal damages nearby enemy through integrated army", target.health == 30, {"health": target.health})
	# Zero volume is invariant under traversal, impact, coin and pulse activity.
	scene.audio.set_volume(0)
	for index in range(50):
		player.traversal_event.emit("flight_start", player.global_position)
		scene._impact(Vector3(0,1,-40))
		scene._fire(Vector3(0,1,-35), Vector3(0,0,-1), false)
		scene.audio.play_event("coin", player.global_position)
	var silent: Dictionary = scene.audio.get_diagnostics()
	record("muted event burst stays silent with fixed audio allocation", silent.muted and silent.playing_cues == 0 and not silent.active_music and audio_player_count(scene.audio) == 7, silent)
	record("same-frame projectile and impact bursts obey world caps", scene.projectiles.get_child_count() <= 32 and scene.effects.get_child_count() <= 24, {"projectiles": scene.projectiles.get_child_count(), "effects": scene.effects.get_child_count()})
	scene.teleport_to(Vector3(0,.05,-112), 180)
	await frames(2)
	record("world teleport clears queued projectiles and active traversal", scene.projectiles.get_child_count() == 0 and player.traversal.mode == "ground" and not player.traversal.rope.visible)
	await army_stress(army)
	# Reset is a user-visible operation, so ensure repeated resets leave no stale
	# transient projectiles, wallet or suspended state in the actual world.
	scene._restart_army()
	await frames(3)
	record("restart restores world spawn and clean wallet", army.gold == 0 and army.kills == 0 and not scene.paused and player.position.distance_to(Vector3(0,0,-112)) < .2 and scene.last_gold == 0)
	var old_army_id: int = army.get_instance_id()
	var old_audio_id: int = scene.audio.get_instance_id()
	scene.return_to_courtyard()
	await scene_changed
	await frames(4)
	record("return disposes world army and audio ownership", not is_instance_id_valid(old_army_id) and not is_instance_id_valid(old_audio_id) and current_scene.scene_file_path.ends_with("courtyard.tscn") and not paused)
	finish()

func army_stress(army) -> void:
	army.set_physics_process(false)
	var reset_ok := true
	var highest_nodes := 0
	for index in range(50):
		army.reset()
		var count := unit_count(army)
		highest_nodes = maxi(highest_nodes,count)
		var state: Dictionary = army.report()
		reset_ok = reset_ok and count == 30 and state.queued_for_deletion == 0 and state.queued_attacks == 0 and army.gold == 0
	record("fifty same-frame resets never retain old army nodes or attacks", reset_ok, {"highest_unit_nodes": highest_nodes})
	var current = army.units.duplicate()
	for unit in current:
		if is_instance_valid(unit): unit.receive_damage(1000,"army")
	var burst: Dictionary = army.report()
	record("same-frame army death burst retains at most24 corpses and96 nodes", burst.pending_cleanup <= 24 and unit_count(army) <= 96 and burst.queued_for_deletion == 0 and army.gold == 0, burst)
	# Separate accelerated scene avoids rendering thousands of recovered units.
	var simulation = load("res://scripts/lane_army.gd").new()
	simulation.visual_enabled = false
	root.add_child(simulation)
	simulation.set_physics_process(false)
	var configured: bool = simulation.configure(scene.manifest, null)
	record("independent accelerated army uses the actual manifest", configured)
	if not configured:
		simulation.free()
		return
	var bounded := true
	var finite := true
	var max_live := 0
	var max_nodes := 0
	var max_corpses := 0
	var max_attacks := 0
	var ticks := 0
	var earliest_end := -1.0
	var started := Time.get_ticks_msec()
	for index in range(24000):
		simulation.step_simulation(.05)
		ticks += 1
		var report: Dictionary = simulation.report()
		max_live = maxi(max_live, report.alive)
		max_nodes = maxi(max_nodes, unit_count(simulation))
		max_corpses = maxi(max_corpses, report.pending_cleanup)
		max_attacks = maxi(max_attacks, report.queued_attacks)
		bounded = bounded and max_live <= 72 and max_nodes <= 96 and max_corpses <= 24 and max_attacks <= 72 and report.queued_for_deletion == 0
		finite = finite and report.finite
		if not String(report.winner).is_empty():
			earliest_end = float(report.elapsed)
			break
		if index % 200 == 0: await process_frame
	simulated_ticks += ticks
	var final_state: Dictionary = simulation.report()
	record("independent20-minute army sweep has bounded finite live state", bounded and finite and ticks == 24000 and final_state.elapsed >= 1199.9, {"ticks": ticks, "elapsed": final_state.elapsed, "earliest_end": earliest_end, "max_alive": max_live, "max_unit_nodes": max_nodes, "max_corpses": max_corpses, "max_attacks": max_attacks, "wall_ms": Time.get_ticks_msec()-started})
	record("independent soak includes combat in every lane without static obstruction", final_state.kills_by_lane[0] > 0 and final_state.kills_by_lane[1] > 0 and final_state.kills_by_lane[2] > 0 and final_state.route_blocked_moves == 0, {"kills_by_lane": final_state.kills_by_lane, "blocked_moves": final_state.route_blocked_moves, "waves": final_state.waves})
	# Construct one surviving arrival for each team on opposite ends of one lane.
	# Both cores at7 ensures simultaneous arrival is draw rather than iteration bias.
	simulation.reset()
	var keep: Array = []
	for team in ["sun","moon"]:
		for unit in simulation.units:
			if unit.team == team and unit.role == "spearman" and unit.lane_id == 0:
				keep.append(unit)
				break
	for unit in simulation.units.duplicate():
		if not keep.has(unit):
			simulation.units.erase(unit)
			unit.free()
	for unit in keep:
		unit.progress = simulation.lanes[0].length - .01
		unit.lateral = 0
		unit.position = simulation.route_sample(0,unit.progress,unit.team,0).position
	simulation.cores = {"sun":7.0,"moon":7.0}
	simulation.step_simulation(.05)
	record("simultaneous opposing core arrivals settle as draw once", simulation.winner == "draw" and simulation.cores.sun == 0 and simulation.cores.moon == 0 and simulation.report().queued_attacks == 0, simulation.report())
	var ended := JSON.stringify(simulation.report())
	simulation.step_simulation(.05)
	record("finished army cannot continue scoring or scheduling", JSON.stringify(simulation.report()) == ended)
	simulation.reset()
	record("post-outcome reset restores two cores and no previous attacks", simulation.winner.is_empty() and simulation.cores.sun == 100 and simulation.cores.moon == 100 and simulation.report().queued_attacks == 0 and simulation.report().alive == 30)
	simulation.free()
	await process_frame

func finish() -> void:
	release()
	paused = false
	if is_instance_valid(driver): driver.queue_free()
	if is_instance_valid(current_scene):
		current_scene.queue_free()
	await process_frames(3)
	var unchanged := true
	for path in source_before: unchanged = unchanged and FileAccess.get_sha256(path) == source_before[path]
	record("integrated sources remain unchanged during test", unchanged, source_before)
	var passed := true
	for item in checks: passed = passed and item.passed
	var report := {"passed": passed, "checks": checks, "sources": source_before, "engine": Engine.get_version_info().string,
		"physics_ticks_per_second": Engine.physics_ticks_per_second, "physics_frames_observed": physical_frames, "accelerated_army_ticks": simulated_ticks,
		"scope": "Actual native scene, Godot physics, injected InputEvents/signals and lifecycle; separate accelerated army simulation at20Hz. No OS-input, renderer, audible-quality, consumer-GPU performance, multiplayer authority or comprehensive security certification."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
	print("YUGA_TRAVERSAL_ARMY_STRESS ",JSON.stringify({"passed":passed,"checks":checks.size(),"physics_frames":physical_frames,"army_ticks":simulated_ticks}))
	quit(0 if passed else 1)
