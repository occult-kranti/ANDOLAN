extends SceneTree
## Reuses actual runtime event routing, Kit/Army, rig, effects and audio receivers.
## Numeric sampling is not rendered review or a human/player-input session.
const Army = preload("res://scripts/lane_army.gd")
const Player = preload("res://scripts/player.gd")
const Runtime = preload("res://scripts/rama_hero_runtime.gd")
const ObservedEffects = preload("res://tools/reuse-event-sync/observed_effects.gd")
const ObservedAudio = preload("res://tools/reuse-event-sync/observed_audio.gd")
const MAP := "res://assets/world/confluence-map.json"
const ORIGIN := Vector3(-40, 0, -10)
const SOCKETS := ["bow_grip", "draw_hand", "string_nock", "arrow_muzzle"]
const SOURCES := [MAP, "res://scripts/player.gd", "res://scripts/rama_hero_runtime.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/lane_army.gd", "res://scripts/lane_minion.gd", "res://scripts/rama_motion.gd", "res://scripts/rama_action_audio.gd", "res://scripts/rama_ability_effects.gd", "res://scripts/rama_vitals.gd", "res://scripts/rama_action_buffer.gd", "res://scripts/ultimate_rules.gd", "res://assets/design/rama-ability-kit.json", "res://assets/heroes/rama-hero.glb", "res://assets/animations/rama_hero_motion.tres", "res://assets/audio/rama-quality/manifest.json"]
var output := ""
var checks: Array = []
var timelines: Array = []
var negative_receipts: Array = []
var current := {}
var pending := {}
var army: Node3D
var player: CharacterBody3D
var runtime: Node3D
var capture_clock := 0.0
var routing := true
var last_event := {}
var state := {"velocity":Vector3.ZERO, "local_velocity":Vector3.ZERO, "floor_y":0.0, "grounded":true, "aiming":false, "aim_pitch":0.0, "aim_yaw":0.0}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label, "passed":passed, "details":details})
	print("PASS " if passed else "FAIL ", label)

func pack(value: Variant) -> Variant:
	if value is Vector3: return [value.x, value.y, value.z]
	if value is Transform3D:
		return {"position":pack(value.origin), "basis":[pack(value.basis.x), pack(value.basis.y), pack(value.basis.z)]}
	if value is Dictionary:
		var out := {}
		for key in value: out[str(key)] = pack(value[key])
		return out
	if value is Array:
		var out := []
		for item in value: out.append(pack(item))
		return out
	return value

func identity(event: Dictionary) -> String:
	return "%d:%d" % [int(event.generation), int(event.event_seq)]

func socket_snapshot() -> Dictionary:
	var result := {}
	# A missing rig is missing. Never call socket_global's identity fallback.
	if not is_instance_valid(player) or not is_instance_valid(player.rama_motion) or not player.rama_motion.configured: return result
	for socket in SOCKETS:
		var bone := "bowstring" if socket == "string_nock" else ("wrist.L" if socket == "draw_hand" else "wrist.R")
		if player.rama_motion.rig.find_bone(bone) >= 0:
			result[socket] = pack(player.rama_motion.socket_global(socket))
	return result

func effects_ack(event: Dictionary, accepted: bool, before: Dictionary, after: Dictionary) -> void:
	if not routing: return
	var key := identity(event)
	if not pending.has(key): pending[key] = {}
	pending[key].sockets_before_motion_event = socket_snapshot()
	pending[key].socket_observed_for = [int(event.generation), int(event.event_seq)]
	pending[key].effect = {"event_identity":[int(event.generation),int(event.event_seq)], "acknowledged":accepted, "accepted_counter_before":before.counts.accepted, "accepted_counter_after":after.counts.accepted, "generation":after.generation, "last_event_seq":runtime.effects._sequence, "live_arrows":after.live_arrows, "finite":after.finite}

func audio_ack(event: Dictionary, acknowledgement: Dictionary, before: Dictionary, after: Dictionary) -> void:
	if not routing: return
	var key := identity(event)
	if not pending.has(key): pending[key] = {}
	pending[key].audio = {"event_identity":[int(event.generation),int(event.event_seq)], "return":acknowledgement.duplicate(true), "generation":after.generation, "last_event_seq":after.last_event_seq, "played_delta":after.played-before.played, "suppressed_delta":after.suppressed-before.suppressed, "dropped_delta":after.dropped-before.dropped, "voice_serials":after.voices, "listening":"UNRUN"}

func record_event(event: Dictionary) -> void:
	if not routing or current.is_empty(): return
	var key := identity(event)
	var record: Dictionary = pending.get(key, {}).duplicate(true)
	pending.erase(key)
	player.rama_motion.evaluate_pose()
	record.sockets_after_motion_event = socket_snapshot()
	record.identity = [int(event.generation), int(event.event_seq)]
	record.event = pack(event.duplicate(true))
	record.capture_clock_s = capture_clock
	record.wall_clock_us = Time.get_ticks_usec()
	record.motion = pack(player.rama_motion.diagnostics())
	current.events.append(record)
	last_event = event.duplicate(true)

func advance(seconds: float, hz: int) -> void:
	var lattice := maxi(60, hz)
	var ticks := int(round(seconds*lattice))
	for tick in range(1,ticks+1):
		capture_clock += 1.0/lattice
		if tick % (lattice/20) == 0:
			if army.step_simulation(.05): current.accepted_simulation_steps += 1
		if tick % (lattice/hz) == 0:
			player.rama_motion.update_motion(1.0/hz, state)
			player.rama_motion.evaluate_pose()
			runtime.effects.step(1.0/hz)
			current.frames.append({"capture_clock_s":capture_clock, "simulation_time_s":runtime.kit.elapsed, "generation":runtime.kit.generation, "sockets":socket_snapshot(), "motion":pack(player.rama_motion.diagnostics()), "effects":runtime.effects.report()})

func start_case(label: String, hz: int) -> void:
	current = {"label":label, "presentation_hz":hz, "simulation_hz":20, "accepted_simulation_steps":0, "events":[], "frames":[]}
	capture_clock = 0.0
	runtime.kit.reset("sidecar case boundary")
	player.rama_motion.evaluate_pose()
	army._attacks.clear()
	army._decision_clock = 100000.0
	army._next_wave = 100000.0

func request(ability: String) -> Dictionary:
	return runtime.kit.request_ability(ability, player.global_position, Vector3.BACK, player.global_position+Vector3.BACK*4)

func count(kind: String, generation := -1) -> int:
	return current.events.filter(func(row): return row.event.kind == kind and (generation < 0 or int(row.event.generation) == generation)).size()

func finish_case() -> void:
	var acknowledgements: bool = current.events.all(func(row): return row.get("effect", {}).get("acknowledged", false) and row.get("audio", {}).get("return", {}).get("ok", false))
	var sockets: bool = current.events.all(func(row): return row.sockets_before_motion_event.size() == 4 and row.sockets_after_motion_event.size() == 4)
	check("%d/%s actual receiver acknowledgements" % [current.presentation_hz,current.label], acknowledgements)
	check("%d/%s four actual socket transforms per event" % [current.presentation_hz,current.label], sockets)
	timelines.append(current.duplicate(true))
	current.clear()

func receiver_negatives(event: Dictionary, label: String) -> void:
	routing = false
	var before_fx: Dictionary = runtime.effects.report()
	var before_audio: Dictionary = runtime.action_audio.report()
	var effect: bool = runtime.effects.consume_event(event)
	var sound: Dictionary = runtime.action_audio.consume_event(event)
	var after_fx: Dictionary = runtime.effects.report()
	var after_audio: Dictionary = runtime.action_audio.report()
	var passed: bool = not effect and not sound.ok and before_fx.counts.accepted == after_fx.counts.accepted and before_audio.played == after_audio.played
	check(label, passed, {"effect_accepted":effect,"audio":sound})
	negative_receipts.append({"label":label,"event":pack(event),"effect_acknowledged":effect,"audio_acknowledgement":sound,"passed":passed})
	routing = true

func cases(hz: int) -> void:
	for ability in ["kodanda","dawn_volley"]:
		start_case(ability,hz)
		check("%d/%s request accepted" % [hz,ability],request(ability).get("accepted",false))
		advance(1.5 if ability=="kodanda" else 2.6,hz)
		check("%d/%s one begin release end" % [hz,ability],count("begin")==1 and count("release")==1 and count("end")==1)
		check("%d/%s actual projectile terminal contacts" % [hz,ability],count("impact")== (1 if ability=="kodanda" else 3))
		var releases: Array = current.events.filter(func(row):return row.event.kind=="release")
		var aligned := not releases.is_empty()
		var error := 0.0
		for row in releases:
			var point: Array = row.sockets_before_motion_event.arrow_muzzle.position
			for projectile in row.event.geometry.projectiles:
				var source: Array = projectile.origin
				error = maxf(error,Vector3(point[0],point[1],point[2]).distance_to(Vector3(source[0],source[1],source[2])))
			aligned = aligned and error < .000001
		check("%d/%s actual release geometry uses sampled muzzle" % [hz,ability],aligned,{"maximum_error_m":error})
		receiver_negatives(last_event,"%d/%s duplicate actual receiver event rejected" % [hz,ability])
		finish_case()
	start_case("cancel_windup",hz)
	check("%d/cancel request accepted" % hz,request("kodanda").get("accepted",false))
	advance(.1,hz)
	check("%d/cancel actual windup cancelled" % hz,runtime.kit.cancel_windup("sidecar interrupt"))
	advance(.5,hz)
	check("%d/cancel no delayed release or contact" % hz,count("cancel")==1 and count("release")==0 and count("impact")==0)
	finish_case()
	start_case("reset_windup_then_recast",hz)
	var first := request("dawn_volley")
	check("%d/reset request accepted" % hz,first.get("accepted",false))
	advance(.1,hz)
	var old := last_event.duplicate(true)
	var previous_generation: int = runtime.kit.generation
	runtime.kit.reset("sidecar interrupted generation")
	receiver_negatives(old,"%d/reset stale actual generation rejected" % hz)
	check("%d/reset recast accepted" % hz,request("kodanda").get("accepted",false))
	advance(1.5,hz)
	check("%d/reset old generation never releases; new cast releases once" % hz,count("release",previous_generation)==0 and count("cancel",previous_generation)==1 and count("release",runtime.kit.generation)==1 and runtime.kit.generation>previous_generation)
	finish_case()
	start_case("cancel_released_volley",hz)
	check("%d/volley-cancel request accepted" % hz,request("dawn_volley").get("accepted",false))
	advance(1.0,hz)
	runtime.kit.cancel_active("sidecar released cancel")
	var accepted_before: int = runtime.kit.receipts_count
	var played_before: int = runtime.action_audio.report().played
	advance(1.5,hz)
	check("%d/volley-cancel no late contact or pulse" % hz,count("release")==1 and count("cancel")==1 and count("impact")==0 and runtime.kit.receipts_count==accepted_before and runtime.action_audio.report().played==played_before)
	finish_case()

func run() -> void:
	if not output.is_absolute_path() or FileAccess.file_exists(output): printerr("Use a fresh absolute --output file");quit(2);return
	var before := {}
	for path in SOURCES: before[path] = FileAccess.get_sha256(path)
	army = Army.new(); army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	check("actual Army configures unchanged canonical map",army.configure(JSON.parse_string(FileAccess.get_file_as_string(MAP)),null))
	# Existing fixture isolation: no unrelated AI/wave/attacks can consume this trace.
	for unit in army.units.duplicate(): army.units.erase(unit);unit.free()
	army._rebuild_buckets()
	player=Player.new();root.add_child(player);player.set_physics_process(false);player.position=ORIGIN
	check("real player model and motion configured",player.model_ready and is_instance_valid(player.rama_motion) and player.rama_motion.configured)
	player.rama_motion.evaluate_pose()
	runtime=Runtime.new();root.add_child(runtime)
	check("unchanged shared HeroRuntime configures",runtime.configure(player,army))
	# Replace only receivers with instrumentation subclasses. Their inherited
	# consume_event executes exactly once, and the unchanged Runtime routes it.
	runtime.effects.free();runtime.effects=ObservedEffects.new();runtime.add_child(runtime.effects);runtime.effects.set_process(false);runtime.effects.observer=effects_ack
	runtime.action_audio.free();runtime.action_audio=ObservedAudio.new();runtime.add_child(runtime.action_audio);runtime.action_audio.set_process(false);runtime.action_audio.observer=audio_ack
	check("actual audio resources available",runtime.action_audio.report().ready)
	runtime.combat_event.connect(record_event)
	for hz in [30,60,120]: cases(hz)
	var after := {}
	for path in SOURCES: after[path]=FileAccess.get_sha256(path)
	check("observed canonical source and assets unchanged",before==after)
	var report := {"schema":1,"scope":"Headless actual Kit/Army and shared Runtime routing with observing receiver subclasses; real rig sockets sampled numerically. No rendered/player-input/listening/online/hardware acceptance.","engine":Engine.get_version_info(),"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"source_pins":before,"source_after":after,"simulation_hz":20,"audio_driver":AudioServer.get_driver_name(),"audio_clock_policy":"event time controls onset eligibility and 70ms confirmation guard; AudioServer voice lifetime runs on its own clock; capture wall time is diagnostic only", "checks":checks,"timelines":timelines,"negative_receipts":negative_receipts}
	var file := FileAccess.open(output,FileAccess.WRITE)
	if file==null: quit(2);return
	file.store_string(JSON.stringify(report,"\t")+"\n");file.close()
	routing=false;runtime.free();player.free();army.free()
	quit(0 if checks.all(func(row):return row.passed) else 1)
