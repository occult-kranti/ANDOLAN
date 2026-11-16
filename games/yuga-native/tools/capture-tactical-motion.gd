extends SceneTree
## Actual native components, scripted rehearsal. Never ordinary-input/match proof.
## Run with --fixed-fps 15; root owns serialized rendering and video encoding.
signal sample_finished
const FPS := 15
const DT := 1.0 / FPS
const FRAME_COUNT := 180
const ORIGIN := Vector3(-29, 0, -18)
const TARGETS := {5: Vector3(-29, 0, -3), 6: Vector3(-35, 0, -2)}
var output := ""
var probe_only := false
var world: Node3D
var sources: Dictionary = {}
var imports: Dictionary = {}
var frames: Array[Dictionary] = []
var actions: Array[Dictionary] = []
var checks: Array[Dictionary] = []
var pending := false
var sample_index := -1
var failure := ""
var label: Label
var solar_releases: Array[Dictionary] = []
var initial_state: Dictionary = {}
var final_state: Dictionary = {}
var stage_clock := 0.0
var dash_origin := Vector3.ZERO
var reload_return := Vector3.ZERO
var has_reload_return := false
var actual_delta := 0.0

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--probe-only": probe_only = true
		else: push_error("Unknown argument: " + arg); quit(1); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):
		push_error("Choose a new absolute output directory."); quit(1); return
	DirAccess.make_dir_recursive_absolute(output)
	if not probe_only and (DisplayServer.get_name() == "headless" or RenderingServer.get_current_rendering_method() != "forward_plus"):
		failure = "Film capture requires an actual Forward+ display."; _finish(); return
	Engine.physics_ticks_per_second = FPS
	Engine.time_scale = 1.0
	_pin_sources()
	root.size = Vector2i(1280, 720); root.content_scale_size = root.size
	root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA · Sanctum — staged native motion rehearsal"
	if not probe_only: root.show()
	world = load("res://scenes/tactical_world.tscn").instantiate()
	root.add_child(world); current_scene = world
	world.set_physics_process(false); world.set_process(false)
	world.set_process_input(false); world.set_process_unhandled_input(false)
	world.bots.configured = false # Only decisions disabled; actor poses/death still step normally.
	world._release_actions()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	world.settings["reduced_motion"] = false
	world.player.weapon.reduced_motion = false
	world.player.base_fov = 90.0
	world.player.camera.fov = 90.0
	world.rules.actors[0].credits = 9000
	for item in ["carbine", "armor", "q", "c"]: world.request_purchase(item)
	_check("fixture purchases accepted through real own-spawn buy API", world.rules.actors[0].weapon == "carbine" and world.rules.actors[0].armor == 50 and world.rules.actors[0].charges.q == 1 and world.rules.actors[0].charges.c == 1)
	for tick in 80: world.rules.tick(.25)
	world.map.set_buy_barriers(false); world._consume_events(); world._hint_life = 0
	_check("actual preparation clock reached live", world.rules.phase == "live")
	world.player.reset_at(ORIGIN, PI, "carbine")
	for id: int in TARGETS:
		world.actor_nodes[id].reset_at(TARGETS[id])
		world.actor_nodes[id].face(ORIGIN)
	_aim_at(world.actor_position(5) + Vector3.UP * 1.05, 1.0)
	if not probe_only:
		var overlay := CanvasLayer.new(); overlay.layer = 100; root.add_child(overlay)
		label = Label.new(); overlay.add_child(label); label.position = Vector2(354, 102)
		label.add_theme_font_size_override("font_size", 14)
		label.add_theme_color_override("font_color", Color("f1d7a0"))
		label.add_theme_color_override("font_outline_color", Color("101820"))
		label.add_theme_constant_override("outline_size", 5)
	# Physics-space settling occurs before the film. Every film sample follows one
	# real physics callback; CharacterBody3D therefore receives the same 1/15 delta.
	for warmup in 8:
		await _sample(-1)
		if not probe_only: await RenderingServer.frame_post_draw
	_check("grounded start and clear receiver", world.player.is_on_floor() and world.line_of_sight(0, 5))
	stage_clock = world._clock
	initial_state = _state()
	for index in FRAME_COUNT:
		await _sample(index)
		if not probe_only: await RenderingServer.frame_post_draw
		var entry := {"index":index, "sample_time_s":float(index + 1) / FPS, "simulation_delta_s":DT, "actual_physics_delta_s":actual_delta, "physics_tick":Engine.get_physics_frames(), "render_frame":Engine.get_frames_drawn(), "phase_label":_phase(index), "state":_state()}
		if not probe_only:
			var name := "frame-%05d.png" % index
			var path := output.path_join(name)
			var result := root.get_texture().get_image().save_png(path)
			if result != OK: failure = "Could not save original " + name; break
			entry.image = {"file":name, "sha256":FileAccess.get_sha256(path), "width":1280, "height":720}
		frames.append(entry)
		if index % 15 == 0: print("TACTICAL_MOTION frame=", index, " phase=", _phase(index))
		if not failure.is_empty(): break
	world._release_actions()
	final_state = _state()
	_check("180 simulation samples / twelve seconds", frames.size() == FRAME_COUNT and absf(float(world._clock) - stage_clock - 12.0) < .00001)
	_check("real primary damage and receiver death", not world.rules.actors[5].alive)
	_check("reload returned magazine and model origin", has_reload_return and reload_return.length() < .00001 and world.player.weapon.ammo == 24 and world.player.weapon.reserve == 69)
	_check("actual seed flight then cloud", _has_effect_frame("veil_seed") and _has_effect_frame("smoke"))
	_check("actual placed ward remains active", _has_effect_frame("ward") and world.rules.actors[0].charges.c == 0)
	_check("grounded dash moved past ward edge", dash_origin.distance_to(world.player.global_position) > 3.5 and world.player.global_position.x < -32.35 and world.rules.actors[0].charges.e == 0)
	_check("three paced ultimate releases and real second receiver death", solar_releases.size() == 3 and not world.rules.actors[6].alive and world.rules.actors[0].ult < 6)
	_check("normal live one-life authority retained", world.rules.phase == "live" and world.rules.actors[0].alive and world.rules.round_number == 1)
	_finish()

func _sample(index: int) -> void:
	sample_index = index; pending = true
	await sample_finished

func _physics_process(delta: float) -> bool:
	if not pending or not is_instance_valid(world): return false
	pending = false
	actual_delta = delta
	# The engine can finish its startup 60-Hz accumulator on the first warmup.
	# Film samples, after eight settling ticks, must all be the declared 15 Hz.
	if sample_index >= 0 and absf(delta - DT) > .000001: failure = "Unexpected actual physics delta " + str(delta)
	if sample_index >= 0: _timeline(sample_index)
	var before: Array = world._ultimate.duplicate()
	world._physics_process(DT)
	if before.size() > world._ultimate.size():
		for index in before.size() - world._ultimate.size():
			solar_releases.append({"frame":sample_index, "film_time_s":float(sample_index + 1) / FPS, "scheduled_age_s":before[index], "actual_age_s":world._ultimate_age})
	world._process(DT)
	sample_finished.emit()
	return false

func _timeline(index: int) -> void:
	if is_instance_valid(label): label.text = "STAGED REHEARSAL · " + _phase(index)
	if index in [8, 11, 14]:
		Input.action_press("tac_fire")
		actions.append({"frame":index, "action":"scripted primary press", "ammo_before":world.player.weapon.ammo})
	if index in [9, 12, 15]: Input.action_release("tac_fire")
	if index == 18:
		var accepted: bool = world.player.weapon.reload()
		if accepted: world.play_cue("reload", world.player.global_position, .7)
		actions.append({"frame":index, "action":"reload through actual weapon", "accepted":accepted})
		_check("real reload accepted", accepted)
	if index == 51:
		reload_return = world.player.weapon.model.position; has_reload_return = true
		Input.action_press("tac_ads")
		actions.append({"frame":index, "action":"ADS press", "reload_return_position":_normal(reload_return)})
	if index == 64: Input.action_release("tac_ads")
	if index == 66: _ability("q", index)
	if index == 86: _ability("c", index)
	if index == 104:
		dash_origin = world.player.global_position
		Input.action_press("tac_right"); _ability("e", index)
	if index == 105: Input.action_release("tac_right")
	if index >= 114 and index <= 123:
		_aim_at(world.actor_position(6) + Vector3.UP * 1.05, .4 if index < 123 else 1.0)
	if index == 124:
		actions.append({"frame":index, "action":"staged full ultimate resource", "previous_points":world.rules.actors[0].ult, "fixture_points":6, "scope":"Shows the actual earned-resource ability. These six points were staged, not earned in this film."})
		world.rules.actors[0].ult = 6
		_ability("x", index)

func _ability(slot: String, index: int) -> void:
	var before: Dictionary = world.rules.actors[0].duplicate(true)
	world._ability(slot)
	var after: Dictionary = world.rules.actors[0]
	var accepted: bool = after.ult < before.ult if slot == "x" else after.charges[slot] < before.charges[slot]
	actions.append({"frame":index, "action":"actual world ability", "slot":slot, "accepted":accepted, "position":_normal(world.player.global_position)})
	_check("world accepted " + slot, accepted)

func _aim_at(target: Vector3, weight: float) -> void:
	var direction: Vector3 = (target - world.player.camera.global_position).normalized()
	world.player.yaw = lerp_angle(world.player.yaw, atan2(-direction.x, -direction.z), weight)
	world.player.pitch = lerpf(world.player.pitch, asin(direction.y), weight)
	world.player.rotation.y = world.player.yaw
	world.player.camera.rotation.x = world.player.pitch

func _phase(index: int) -> String:
	if index < 18: return "SURYA · FIRE / HIT"
	if index < 51: return "SURYA · RELOAD / RETURN"
	if index < 66: return "SURYA · AIM DOWN SIGHTS"
	if index < 86: return "SOLAR VEIL · SEED / BLOOM"
	if index < 104: return "WARD WALL · PATTERN / COVER"
	if index < 124: return "MEASURED STEP · FLANK"
	if index < 146: return "DAWN VOLLEY · THREE PACED SHOTS"
	return "A APPROACH · LIVE UTILITY / RECOVERY"

func _state() -> Dictionary:
	var fx: Array = []
	for entry: Dictionary in world.effects.effects:
		fx.append({"kind":entry.kind, "remaining_s":entry.life, "position":_normal(entry.node.global_position)})
	var receivers: Array = []
	for id: int in TARGETS:
		receivers.append({"id":id, "health":world.rules.actors[id].health, "alive":world.rules.actors[id].alive, "position":_normal(world.actor_position(id)), "body_rotation":_normal(world.actor_nodes[id].body_visual.rotation)})
	return {"clock_s":world._clock, "phase":world.rules.phase, "time_left_s":world.rules.time_left, "player_position":_normal(world.player.global_position), "grounded":world.player.is_on_floor(), "camera_yaw":world.player.yaw, "camera_pitch":world.player.pitch, "fov":world.player.camera.fov, "ammo":world.player.weapon.ammo, "reserve":world.player.weapon.reserve, "ads":world.player.weapon.ads, "reload_remaining_s":world.player.weapon.reload_remaining, "model_position":_normal(world.player.weapon.model.position), "model_rotation":_normal(world.player.weapon.model.rotation), "charges":world.rules.actors[0].charges.duplicate(true), "ult_points":world.rules.actors[0].ult, "ultimate_pending":world._ultimate.duplicate(), "receivers":receivers, "effects":fx, "authority_event_count":world.event_receipts.size()}

func _has_effect_frame(kind: String) -> bool:
	for frame: Dictionary in frames:
		for entry: Dictionary in frame.state.effects:
			if entry.kind == kind: return true
	return false

func _check(id: String, passed: bool) -> void:
	checks.append({"id":id, "passed":passed})

func _pin_sources() -> void:
	for path in ["res://scripts", "res://shaders", "res://scenes", "res://assets/tactical", "res://assets/fonts"]:
		_hash_directory(path)
	for path in ["res://project.godot", "res://tools/capture-tactical-motion.gd"]: _hash_file(path)
	var specification: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/tactical/map.json"))
	for path: String in specification.reused_sources: _hash_file("res://" + path)

func _hash_directory(path: String) -> void:
	for child in DirAccess.get_files_at(path):
		if not child.ends_with(".uid") and not child.ends_with(".import"): _hash_file(path.path_join(child))
	for child in DirAccess.get_directories_at(path): _hash_directory(path.path_join(child))

func _hash_file(path: String) -> void:
	if not FileAccess.file_exists(path): return
	sources[path] = FileAccess.get_sha256(path)
	if not FileAccess.file_exists(path + ".import"): return
	imports[path + ".import"] = FileAccess.get_sha256(path + ".import")
	var config := ConfigFile.new()
	if config.load(path + ".import") != OK: return
	for imported: String in config.get_value("deps", "dest_files", []):
		if FileAccess.file_exists(imported): imports[imported] = FileAccess.get_sha256(imported)

func _normal(value: Variant) -> Variant:
	if value is Vector3: return [value.x, value.y, value.z]
	if value is Array:
		var result: Array = []
		for item in value: result.append(_normal(item))
		return result
	if value is Dictionary:
		var result: Dictionary = {}
		for key in value: result[str(key)] = _normal(value[key])
		return result
	return value

func _finish() -> void:
	var changed: Array = []
	for table: Dictionary in [sources, imports]:
		for path: String in table:
			if FileAccess.get_sha256(path) != table[path]: changed.append(path)
	_check("source and imports unchanged", changed.is_empty())
	var passed := failure.is_empty() and not checks.any(func(c): return not c.passed)
	var events: Array = world.event_receipts.duplicate(true) if is_instance_valid(world) else []
	var report := {"kind":"staged-native-tactical-motion-rehearsal", "task":"YUGA-TACTICAL-CASUAL-13", "complete":passed, "probe_only":probe_only, "failure":failure, "scope":"Actual world firearm/utility authority, physics, poses, HUD and rendered originals driven by a deterministic script. Not OS input, natural match, audio sync, hardware FPS, or production art acceptance.", "fixture":{"credits":9000, "purchases":["carbine","armor","q","c"], "buy_advance":"80 authority ticks of .25 seconds before staging", "bot_decisions":"disabled; real actor poses/deaths remain active", "player_start":_normal(ORIGIN), "receivers":_normal(TARGETS), "ultimate":"set to 6 points at frame 124; these points were not naturally earned", "camera":"continuous gameplay camera; scripted aim and input actions, no in-film teleports", "warmup_ticks":8, "physics_hz":FPS}, "fps":FPS, "frame_count":frames.size(), "duration_s":float(frames.size()) / FPS, "source_sha256":sources, "import_sha256":imports, "changed_sources":changed, "renderer":RenderingServer.get_current_rendering_method(), "adapter":RenderingServer.get_video_adapter_name(), "initial":initial_state, "final":final_state, "checks":checks, "actions":actions, "solar_releases":solar_releases, "authority_events":_normal(events), "frames":frames}
	var file := FileAccess.open(output.path_join("motion.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n"); file.close()
	print("TACTICAL_MOTION_RESULT ", JSON.stringify({"complete":passed, "frames":frames.size(), "failure":failure, "checks":checks}))
	if is_instance_valid(world):
		world._release_actions()
		for voice in world.find_children("*", "AudioStreamPlayer3D", true, false): voice.stop()
		world.queue_free(); await process_frame; await process_frame
		# Let the audio mix worker release stopped source streams before shutdown.
		OS.delay_msec(100)
	quit(0 if passed else 1)
