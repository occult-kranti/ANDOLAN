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
var baseline_nodes := 0
var retiring_playbacks: Array[WeakRef] = []
var retiring_details: Array = []

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
	# The focus-loss case below emits a real window signal. Model the return
	# explicitly so later audio fixtures do not inherit an unfocused device.
	root.focus_entered.emit()
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

func capture_playback_retirement(node: Node) -> void:
	if (node is AudioStreamPlayer or node is AudioStreamPlayer3D or node is AudioStreamPlayer2D) and node.playing:
		var playback: AudioStreamPlayback = node.get_stream_playback()
		if playback != null:
			retiring_playbacks.append(weakref(playback))
			retiring_details.append({"node":String(node.get_path()), "stream":node.stream.resource_path if node.stream != null else "", "playback_class":playback.get_class()})
	for child in node.get_children(): capture_playback_retirement(child)

func run() -> void:
	baseline_nodes = int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	for path in ["res://scripts/player.gd", "res://scripts/rama_hero_runtime.gd", "res://scripts/rama_action_buffer.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/rama_vitals.gd", "res://scripts/rama_action_audio.gd", "res://scripts/confluence_world.gd", "res://assets/design/rama-ability-kit.json", "res://assets/audio/rama-quality/manifest.json", get_script().resource_path]: sources[path] = FileAccess.get_sha256(path)
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
	var voices_before: int = runtime.action_audio.report().played
	var accepted_before: int = kit.accepted_casts
	var motion_before: Dictionary = scene.player.rama_motion.diagnostics()
	await tap("ultimate")
	scene.rama_hud._process(FRAME)
	check("Final-recovery input reaches the adapter through normal player polling", buffer.report().pending.get("ability_id") == "dawn_volley" and is_equal_approx(kit.elapsed, .85) and runtime.notice == "Dawn Volley · queued after recovery" and scene.rama_hud.note.text == runtime.notice, {"buffer":buffer.report(), "note":scene.rama_hud.note.text})
	check("Queued UI feedback does not fake begin, sound or animation", kit.accepted_casts == accepted_before and begin_count("dawn_volley") == 0 and runtime.action_audio.report().played == voices_before and scene.player.rama_motion.diagnostics().action == motion_before.action and scene.player.rama_motion.diagnostics().release_count == motion_before.release_count and kit.report().cooldowns.dawn_volley == 0)
	var old_forward: Vector3 = last_begin("piercing_dawn").forward
	scene.player.yaw += .35; scene.player._update_camera()
	advance(.10)
	var volley := last_begin("dawn_volley")
	check("Actual recovery produces one synchronized real X begin", begin_count("dawn_volley") == 1 and buffer.report().pending.is_empty() and kit.report().active_ability == "dawn_volley" and scene.player.rama_committed and scene.player.rama_action_locked and scene.player.rama_motion.diagnostics().action == "dawn_volley" and scene.player.rama_motion.diagnostics().stage == "windup", {"authority_s":kit.elapsed, "notice":runtime.notice})
	check("The real dispatch samples the changed current camera aim", not volley.is_empty() and Vector3(volley.forward).angle_to(old_forward) > .15 and volley.origin.distance_to(scene.player.global_position) < .06)
	check("Only the actual accepted dispatch starts the windup cue", runtime.action_audio.report().played == voices_before + 1 and runtime.action_audio.report().voices.any(func(voice): return voice.cue == "draw_dawn_volley" and voice.playing and voice.spatial) and scene.player.ammo == 12 and kit.report().cooldowns.dawn_volley > 17.9 and runtime.notice == "Dawn Volley · drawing")
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

	await fresh()
	var audio: Node3D = runtime.action_audio
	var before_damage: Dictionary = audio.report()
	check("The actual runtime owns the ready four-voice staged sound set", before_damage.ready and before_damage.players == 4 and before_damage.streams == 15 and before_damage.receiver_generation == runtime.vitals.generation and before_damage.alive and before_damage.focused and not before_damage.suspended)
	var nonlethal: Dictionary = runtime.vitals.receive_damage(25, "combined_nonlethal", runtime.vitals.generation, 0)
	var after_damage: Dictionary = audio.report()
	check("Actual nonlethal vitals receipt reaches the local threat cue once", nonlethal.accepted and nonlethal.sequence == 0 and runtime.vitals.health == 275 and after_damage.played == before_damage.played + 1 and after_damage.damage_sources == before_damage.damage_sources + 1 and after_damage.rejected == before_damage.rejected and after_damage.voices.any(func(voice): return voice.playing and voice.cue == "threat" and not voice.spatial), {"receipt":nonlethal,"audio":after_damage})
	var duplicate: Dictionary = runtime.vitals.receive_damage(25, "combined_nonlethal", runtime.vitals.generation, 0)
	check("Actual duplicate hazard is rejected before another audio onset", not duplicate.accepted and runtime.vitals.health == 275 and audio.report().played == after_damage.played and audio.report().rejected == after_damage.rejected)
	var lethal: Dictionary = runtime.vitals.receive_damage(1000, "combined_lethal", runtime.vitals.generation, 0)
	var after_lethal: Dictionary = audio.report()
	check("Actual lethal receipt reaches the silent defeated audio lifecycle", lethal.accepted and lethal.health_after == 0 and not runtime.vitals.alive and not after_lethal.alive and after_lethal.playing == 0 and after_lethal.played == after_damage.played and after_lethal.damage_sources == after_damage.damage_sources + 1 and after_lethal.rejected == after_damage.rejected, {"receipt":lethal,"audio":after_lethal})

	await fresh()
	var before_external: Dictionary = runtime.vitals.receive_damage(10, "before_external_reset", runtime.vitals.generation, 0)
	var queued_before_external: bool = await primary_then_queue()
	var receiver_before: int = runtime.vitals.generation
	var played_before_external: int = audio.report().played
	runtime.vitals.reset()
	var external: Dictionary = audio.report()
	check("External real vitals.reset synchronizes receiver generation and clears pending sound", queued_before_external and runtime.vitals.generation == receiver_before + 1 and external.receiver_generation == runtime.vitals.generation and external.vitals_generation == runtime.vitals.generation and external.alive and external.playing == 0 and external.played == played_before_external and buffer.report().pending.is_empty(), {"audio":external,"hero_generation":runtime.vitals.generation})
	var stale: Dictionary = audio.consume_damage(before_external)
	check("An old actual receipt cannot replay after external generation reset", not stale.ok and stale.code == "RECEIVER_GENERATION_MISMATCH" and audio.report().played == played_before_external)
	var after_external: Dictionary = runtime.vitals.receive_damage(10, "after_external_reset", runtime.vitals.generation, 0)
	check("A current actual receipt works after external reset", after_external.accepted and audio.report().played == played_before_external + 1 and audio.report().alive)
	advance(.10)
	check("External actor reset never replays the discarded queued X", begin_count("dawn_volley") == 0 and buffer.report().pending.is_empty())

	await fresh()
	var before_suspend: int = audio.report().played
	var suspend_cast: Dictionary = runtime.cast_ability("piercing_dawn")
	check("A real accepted Q begins the new audio owner", suspend_cast.accepted and audio.report().played == before_suspend + 1 and audio.report().voices.any(func(voice): return voice.playing and voice.cue == "draw_piercing_dawn"))
	runtime.set_suspended(true)
	var suspended_audio: Dictionary = audio.report()
	var suspended_damage: Dictionary = runtime.vitals.receive_damage(10, "suspended_hazard", runtime.vitals.generation, 0)
	var suspended_cast: Dictionary = runtime.cast_ability("dawn_volley")
	check("Actual suspension stops voices and blocks cast and damage onsets", suspended_audio.suspended and suspended_audio.playing == 0 and not suspended_damage.accepted and not suspended_cast.accepted and audio.report().played == suspended_audio.played)
	runtime.set_suspended(false)
	advance(.10)
	check("Resume does not replay a stopped draw or arm a delayed cue", not audio.report().suspended and audio.report().playing == 0 and audio.report().played == suspended_audio.played and buffer.report().pending.is_empty())
	advance(.55)
	check("Only the later real authority release creates the next sound", audio.report().played == suspended_audio.played + 1 and audio.report().voices.any(func(voice): return voice.cue == "release_piercing_dawn" and voice.playing))

	await fresh()
	var reset_queued: bool = await primary_then_queue()
	var before_runtime_reset: int = audio.report().played
	# Stop is synchronous at the Node API; the Dummy mixer releases its
	# playback ref on a later real audio block, not after N synthetic frames.
	capture_playback_retirement(scene)
	runtime.reset()
	var reset_audio: Dictionary = audio.report()
	check("Actual runtime reset clears voices and pending casts without a queued onset", reset_queued and reset_audio.playing == 0 and reset_audio.active_casts == 0 and reset_audio.alive and reset_audio.generation == kit.generation and reset_audio.receiver_generation == runtime.vitals.generation and reset_audio.played == before_runtime_reset and buffer.report().pending.is_empty(), {"audio":reset_audio,"kit_generation":kit.generation,"hero_generation":runtime.vitals.generation})
	advance(.20)
	check("Updates after reset cannot replay pre-reset input or sound", audio.report().played == before_runtime_reset and begin_count("dawn_volley") == 0)

	var unchanged := true
	for path in sources: unchanged = unchanged and FileAccess.get_sha256(path) == sources[path]
	check("Input/runtime/authority source bytes remain unchanged during this fixture", unchanged)
	capture_playback_retirement(scene)
	var scene_weak: WeakRef = weakref(scene)
	paused = false; scene.release_actions(); scene.queue_free(); current_scene = null
	for unused in 6: await process_frame
	check("World teardown frees the scene and every owned Node", scene_weak.get_ref() == null and int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)) == baseline_nodes, {"baseline_nodes":baseline_nodes,"remaining_nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))})
	var retire_start: int = Time.get_ticks_msec()
	while retiring_playbacks.any(func(ref_: WeakRef): return ref_.get_ref() != null) and Time.get_ticks_msec() - retire_start < 1000:
		await create_timer(.025).timeout
	check("Stopped Dummy playback refs retire within one real second", not retiring_playbacks.is_empty() and not retiring_playbacks.any(func(ref_: WeakRef): return ref_.get_ref() != null), {"sampled_playbacks":retiring_playbacks.size(),"wait_ms":Time.get_ticks_msec()-retire_start,"playbacks":retiring_details})
	var passed := true
	for item in checks: passed = passed and item.passed
	var report := {"passed":passed,"checks":checks,"sources":sources,"scope":"Actual Confluence scene, CharacterBody grounding, Input.action_press/release, existing player polling and real 20 Hz army/kit/vitals/action-audio receipts. Focus is an explicitly emitted window signal; audio is the actual Dummy-driver owner, not listening evidence. No OS input, rendered continuity, human-feel, online or hardware performance claim."}
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report, "\t") + "\n")
		else: passed = false
	quit(0 if passed else 1)
