extends SceneTree
## Real Confluence input polling and kit clock; not OS input or human-feel proof.
const STEP := .05
const FRAME := 1.0 / 60.0
const ORIGIN := Vector3(-40, .05, -10)
var scene: Node3D
var runtime: Node3D
var kit: Node3D
var buffer: Node
var events: Array = []
var checks: Array = []
var sources: Dictionary = {}
var output := ""

func _initialize() -> void: call_deferred("run")

func check(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label, "passed":passed, "evidence":evidence})
	if not passed: push_error("BUFFER INTEGRATION FAILED: " + label)

func disable_steps() -> void:
	scene.set_process(false); scene.set_physics_process(false)
	scene.army.set_physics_process(false); scene.player.set_physics_process(false)
	scene.rama_effects.set_process(false)

func advance(seconds: float) -> void:
	var left := seconds
	while left > 1e-8:
		var delta := minf(STEP, left)
		scene.army.step_simulation(delta)
		var frame_left := delta
		while frame_left > 1e-8:
			var frame_delta := minf(FRAME, frame_left)
			scene.player._physics_process(frame_delta)
			frame_left -= frame_delta
		left -= delta

func fresh() -> void:
	if scene.controls_overlay.visible: scene.controls_overlay.close()
	if scene.rama_panel.visible: scene.rama_panel.close()
	if scene.overview: scene.set_overview(false)
	scene.release_actions()
	# Input.action_press is sampled on the next real engine physics boundary.
	# Clear a prior synthetic just-pressed phase before resetting a new fixture.
	scene.player.set_physics_process(false)
	for unused in 2: await physics_frame
	scene.set_paused(false)
	scene._restart_army()
	disable_steps()
	scene.teleport_to(ORIGIN, 0)
	scene.player.yaw = PI; scene.player.pitch = -.32; scene.player._update_camera()
	scene.player.set_physics_process(true)
	for unused in 8: await physics_frame
	scene.player.set_physics_process(false)
	scene.army._attacks.clear()
	scene.army._decision_clock = 100000.0; scene.army._next_wave = 100000.0
	for unit in scene.army.units.duplicate(): scene.army.units.erase(unit); unit.free()
	scene.army._rebuild_buckets()
	events.clear()

func tap(action: String) -> void:
	Input.action_press(action)
	await physics_frame
	scene.player._physics_process(FRAME)
	Input.action_release(action)
	await physics_frame
	scene.player._physics_process(FRAME)

func begin_count(id: String) -> int:
	return events.filter(func(event): return event.kind == "begin" and event.ability_id == id).size()

func last_begin(id: String) -> Dictionary:
	for index in range(events.size() - 1, -1, -1):
		if events[index].kind == "begin" and events[index].ability_id == id: return events[index]
	return {}

func primary_then_queue() -> bool:
	var result: Dictionary = runtime.cast_ability("kodanda")
	advance(.30)
	await tap("ultimate")
	return result.get("accepted", false) and not buffer.report().pending.is_empty()

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	for path in ["res://scripts/player.gd", "res://scripts/rama_hero_runtime.gd", "res://scripts/rama_action_buffer.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/rama_vitals.gd", "res://scripts/confluence_world.gd", "res://assets/design/rama-ability-kit.json", get_script().resource_path]: sources[path] = FileAccess.get_sha256(path)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	for unused in 6: await process_frame
	runtime = scene.rama_runtime; kit = runtime.kit; buffer = runtime.action_buffer
	check("Actual world owns a configured separate Q/X input adapter", scene.world_ready and runtime.configured and buffer.report().configured and scene.player.ability_input_request.is_valid() and scene.player.ability_request.is_valid())
	disable_steps()
	kit.ability_event.connect(func(event): events.append(event.duplicate(true)))

	await fresh()
	check("Actual CharacterBody is grounded in the existing world", scene.player.is_on_floor() and runtime._input_eligibility().eligible)
	await tap("pulse")
	check("A fresh Q input starts the existing kit without spending primary ammo", begin_count("piercing_dawn") == 1 and kit.report().active_ability == "piercing_dawn" and scene.player.ammo == 12 and scene.player.rama_committed)
	await tap("ultimate")
	check("X pressed during real Q windup rejects with truthful feedback", begin_count("dawn_volley") == 0 and buffer.report().pending.is_empty() and runtime.notice == "Finish the current draw" and scene.player.rama_committed, {"notice":runtime.notice})
	advance(.70)
	await tap("ultimate")
	check("X during early recovery never becomes pending", begin_count("dawn_volley") == 0 and buffer.report().pending.is_empty() and runtime.notice == "Finish the current recovery")
	advance(.15)
	var voices_before: int = runtime._voice_index
	var accepted_before: int = kit.accepted_casts
	var motion_before: Dictionary = scene.player.rama_motion.diagnostics()
	await tap("ultimate")
	scene.rama_hud._process(FRAME)
	check("Final-recovery input reaches the adapter through normal player polling", buffer.report().pending.get("ability_id") == "dawn_volley" and is_equal_approx(kit.elapsed, .85) and runtime.notice == "Dawn Volley · queued after recovery" and scene.rama_hud.note.text == runtime.notice, {"buffer":buffer.report(), "note":scene.rama_hud.note.text})
	check("Queued UI feedback does not fake begin, sound or animation", kit.accepted_casts == accepted_before and begin_count("dawn_volley") == 0 and runtime._voice_index == voices_before and scene.player.rama_motion.diagnostics().action == motion_before.action and scene.player.rama_motion.diagnostics().release_count == motion_before.release_count and kit.report().cooldowns.dawn_volley == 0)
	var old_forward: Vector3 = last_begin("piercing_dawn").forward
	scene.player.yaw += .35; scene.player._update_camera()
	advance(.10)
	var volley := last_begin("dawn_volley")
	check("Actual recovery produces one synchronized real X begin", begin_count("dawn_volley") == 1 and buffer.report().pending.is_empty() and kit.report().active_ability == "dawn_volley" and scene.player.rama_committed and scene.player.rama_action_locked and scene.player.rama_motion.diagnostics().action == "dawn_volley" and scene.player.rama_motion.diagnostics().stage == "windup", {"authority_s":kit.elapsed, "notice":runtime.notice})
	check("The real dispatch samples the changed current camera aim", not volley.is_empty() and Vector3(volley.forward).angle_to(old_forward) > .15 and volley.origin.distance_to(scene.player.global_position) < .06)
	check("Only the actual accepted dispatch starts the windup cue", runtime._voice_index == voices_before + 1 and scene.player.ammo == 12 and kit.report().cooldowns.dawn_volley > 17.9 and runtime.notice == "Dawn Volley · drawing")
	advance(.10)
	check("Later updates never repeat a released queued edge", begin_count("dawn_volley") == 1)

	await fresh()
	var held_before := {"down":scene.player._ability_input_down.duplicate(),"ticks":scene.player._ability_input_tick.duplicate(),"frame":Engine.get_physics_frames(),"active":scene.player.active,"grounded":scene.player.is_on_floor(),"just_pressed":Input.is_action_just_pressed("pulse"),"pressed":Input.is_action_pressed("pulse")}
	Input.action_press("pulse")
	held_before["after_press"] = {"just_pressed":Input.is_action_just_pressed("pulse"),"pressed":Input.is_action_pressed("pulse")}
	await physics_frame
	for unused in 6: scene.player._physics_process(FRAME)
	var held_edge: int = scene.player._ability_input_edge
	Input.action_release("pulse")
	for unused in 6: scene.player._physics_process(FRAME)
	await physics_frame
	check("A held or same-tick repeated poll creates one deliberate input edge", begin_count("piercing_dawn") == 1 and scene.player._ability_input_edge == held_edge and buffer.report().pending.is_empty(), {"begins":begin_count("piercing_dawn"),"edge":scene.player._ability_input_edge,"held_edge":held_edge,"buffer":buffer.report(),"notice":runtime.notice,"before":held_before})

	await fresh()
	runtime.cast_ability("piercing_dawn"); advance(.85)
	var before_edge: int = scene.player._ability_input_edge
	Input.action_press("dash"); Input.action_press("guardian_circle"); Input.action_press("fire"); Input.action_press("move_forward")
	await physics_frame
	var before_position: Vector3 = scene.player.global_position
	for unused in 6: scene.player._physics_process(FRAME)
	scene.release_actions(false)
	await physics_frame
	check("Buffer integration preserves committed E/C/LMB and movement locks", begin_count("measured_step") == 0 and begin_count("guardian_circle") == 0 and begin_count("kodanda") == 0 and scene.player._ability_input_edge == before_edge and buffer.report().pending.is_empty() and Vector2(scene.player.global_position.x-before_position.x,scene.player.global_position.z-before_position.z).length() < .001)
	var direct: Dictionary = runtime.cast_ability("dawn_volley")
	check("Direct runtime and kit APIs retain immediate busy rejection", not direct.accepted and not kit.request_ability("dawn_volley",scene.player.global_position,Vector3.FORWARD,scene.player.global_position+Vector3.FORWARD*4).accepted and buffer.report().pending.is_empty())

	await fresh()
	await tap("pulse"); advance(.95)
	runtime.cast_ability("kodanda"); advance(.30)
	await tap("pulse")
	check("Cooldown-blocked Q input gives feedback without arming a retry", buffer.report().pending.is_empty() and runtime.notice == "Ability is cooling down" and begin_count("piercing_dawn") == 1, {"begins":begin_count("piercing_dawn"),"notice":runtime.notice,"buffer":buffer.report(),"kit":kit.report()})
	advance(.10)
	check("Recovery never retries the cooldown-blocked input", begin_count("piercing_dawn") == 1)

	for lifecycle in ["pause", "controls modal", "hero guide", "overview", "window focus", "teleport", "hit", "defeat", "actor generation", "army reset", "round outcome"]:
		await fresh()
		var did_queue: bool = await primary_then_queue()
		match lifecycle:
			"pause": scene.set_paused(true); scene.set_paused(false)
			"controls modal": scene._open_controls(); scene.controls_overlay.close()
			"hero guide": scene._open_rama_panel(); scene.rama_panel.close()
			"overview": scene.set_overview(true); scene.set_overview(false)
			"window focus": root.focus_exited.emit(); scene.set_paused(false)
			"teleport": scene.teleport_to(ORIGIN, 0)
			"hit": runtime.vitals.receive_damage(1, "buffer_hit", runtime.vitals.generation, 0)
			"defeat": runtime.vitals.receive_damage(1000, "buffer_defeat", runtime.vitals.generation, 0)
			"actor generation": runtime.vitals.reset()
			"army reset": scene.army.reset()
			"round outcome": scene.army.cores.moon = 0
		advance(.10)
		check("Actual lifecycle prevents queued execution after " + lifecycle, did_queue and buffer.report().pending.is_empty() and begin_count("dawn_volley") == 0, {"notice":runtime.notice,"kit_generation":kit.generation,"hero_generation":runtime.vitals.generation})

	await fresh()
	var edge_at_reset: int = scene.player._ability_input_edge
	await primary_then_queue()
	scene.teleport_to(ORIGIN, 0)
	var after_reset: int = scene.player._ability_input_edge
	check("Player reset preserves monotonic edge identity", after_reset > edge_at_reset and after_reset == buffer.report().last_edge)

	await fresh()
	runtime.cast_ability("kodanda"); advance(.40)
	var started_reload: bool = scene.player.start_reload()
	await tap("pulse")
	check("Real reload blocks Q before it can become pending", started_reload and buffer.report().pending.is_empty() and begin_count("piercing_dawn") == 0 and runtime.notice == "Finish the current action")

	await fresh()
	scene.player.velocity.y = 7
	scene.player._physics_process(FRAME)
	await tap("pulse")
	check("Actual airborne state blocks discrete kit input", not scene.player.is_on_floor() and buffer.report().pending.is_empty() and begin_count("piercing_dawn") == 0 and runtime.notice == "Land before using Rama's kit")

	var unchanged := true
	for path in sources: unchanged = unchanged and FileAccess.get_sha256(path) == sources[path]
	check("Input/runtime/authority source bytes remain unchanged during this fixture", unchanged)
	var passed := true
	for item in checks: passed = passed and item.passed
	var report := {"passed":passed,"checks":checks,"sources":sources,"scope":"Actual Confluence scene, CharacterBody grounding, Input.action_press/release and existing player physics polling with real 20 Hz army/kit. Focus is an explicitly emitted window signal. No OS input, rendered continuity, listening, human-feel, online or hardware performance claim."}
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report, "\t") + "\n")
		else: passed = false
	paused = false; scene.release_actions(); scene.queue_free(); current_scene = null
	for unused in 6: await process_frame
	quit(0 if passed else 1)
