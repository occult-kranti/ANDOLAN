extends SceneTree
## Actual kit/receivers plus adverse presentation receipts. No renderer/listening claim.
const Army = preload("res://scripts/lane_army.gd")
const Unit = preload("res://scripts/lane_minion.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
const Audio = preload("res://scripts/rama_action_audio.gd")
const Response = preload("res://scripts/rama_hit_response.gd")
var army
var kit
var fx
var audio
var events: Array[Dictionary] = []
var checks: Array[Dictionary] = []
var output := ""
var templates: Dictionary = {}
var source_before := {}
var replay_generation := 1000

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ", label)

func real_case(kind: String, health: float, shield: float) -> void:
	army.reset()
	for unit in army.units.duplicate(): army.units.erase(unit); unit.free()
	army._rebuild_buckets()
	events.clear()
	var unit = Unit.new()
	unit.setup(army,army.next_id,"moon","commander",1)
	army.next_id += 1
	unit.render_art = false
	unit.position = Vector3(0,0,5)
	unit.attack_time = 1000; unit.attack_cooldown = 1000; unit.health = health
	unit.defeated.connect(army._on_defeated)
	army.add_child(unit); army.units.append(unit)
	if shield > 0: unit.apply_shield(shield,12)
	var accepted: Dictionary = kit.request_ability("kodanda",Vector3.ZERO,Vector3.BACK,Vector3(0,0,5))
	for unused in 8:
		army.step_simulation(.05)
		fx.step(.05)
	var hits := events.filter(func(event): return event.kind == "impact" and event.get("reason") == "unit")
	check(kind + " uses an actual accepted kit/receiver receipt",accepted.get("accepted",false) and hits.size() == 1 and hits[0].receipts.size() == 1,{"health":unit.health,"shield":unit.shield})
	if hits.is_empty(): return
	var receipt: Dictionary = hits[0].receipts[0]
	check(kind + " classification matches effective receiver math",Response.classify(receipt) == StringName(kind) and is_equal_approx(float(receipt.damage_applied),health+shield-unit.health-unit.shield),receipt)
	check(kind + " selects matching world contact and audio response",fx.report().contact_styles.any(func(item): return item.response == kind) and audio.report().last_contact.get("response") == kind,{"effects":fx.report().contact_styles,"audio":audio.report().last_contact})
	var feedback: Array = audio.report().voices.filter(func(voice): return not voice.spatial)
	var expected_pitch := .88 if kind == "shield" else (1.18 if kind == "defeat" else 1.0)
	check(kind + " local cue has bounded distinguishing pitch",feedback.size() == 1 and absf(float(feedback[0].pitch_scale)-expected_pitch)<.025 and int(feedback[0].priority) == 2,feedback[0] if feedback.size() else {})
	if kind == "defeat": check("Defeat response never grants an extra reward",army.kills == 1 and army.gold == 45,{"gold":army.gold,"kills":army.kills})
	templates[kind] = {"begin":events.filter(func(event):return event.kind=="begin")[0].duplicate(true),"release":events.filter(func(event):return event.kind=="release")[0].duplicate(true),"impact":hits[0].duplicate(true)}

func replay(case_name: String, receipts: Array, reason := "unit", terminal := false):
	fx.reset()
	replay_generation += 1
	var data: Dictionary = templates.health.duplicate(true)
	var index := 1
	for name_ in ["begin","release","impact"]:
		var event: Dictionary = data[name_]
		event.generation = replay_generation; event.epoch = replay_generation; event.event_seq = index; index += 1
	data.impact.receipts = receipts.duplicate(true)
	data.impact.reason = reason
	data.impact.terminal = terminal
	fx.consume_event(data.begin); fx.consume_event(data.release)
	var before: int = fx.report().impacts
	var accepted: bool = fx.consume_event(data.impact)
	check(case_name,accepted and fx.report().impacts == before,{"response_count":fx.report().impacts,"admitted":accepted})
	return data

func run() -> void:
	for path in ["res://scripts/rama_hit_response.gd","res://scripts/rama_ability_effects.gd","res://scripts/rama_action_audio.gd","res://scripts/rama_ability_kit.gd","res://scripts/lane_army.gd","res://scripts/lane_minion.gd",get_script().resource_path]: source_before[path] = FileAccess.get_sha256(path)
	army = Army.new(); army.visual_enabled = false; root.add_child(army); army.set_physics_process(false)
	check("Actual normal army configures",army.configure(JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json")),null))
	kit = Kit.new(); root.add_child(kit)
	fx = Effects.new(); root.add_child(fx); fx.set_process(false)
	audio = Audio.new("res://art/audio/rama-quality/runtime/"); root.add_child(audio)
	check("Actual kit and existing15-cue/four-voice audio configure",kit.configure(army) and audio.report().ready and audio.report().streams == 15 and audio.report().players == 4)
	kit.set_origin_sampler(func():return Vector3.ZERO)
	kit.ability_event.connect(func(event: Dictionary): events.append(event.duplicate(true)); fx.consume_event(event); audio.consume_event(event))
	real_case("health",150,0)
	real_case("shield",150,45)
	real_case("defeat",20,0)
	check("Real receiver events do not produce consumer schema failures",fx.report().counts.invalid == 0 and audio.report().rejected == 0)
	var receipt: Dictionary = templates.health.impact.receipts[0].duplicate(true)
	replay("Empty unit collision cannot show a confirmed-hit bloom",[])
	var zero: Dictionary = receipt.duplicate(true); zero.damage_applied = 0.0
	replay("Zero damage cannot show a confirmed-hit bloom",[zero])
	var false_defeat: Dictionary = receipt.duplicate(true); false_defeat.health_after = 0.0
	replay("Inconsistent health math cannot invent a defeat bloom",[false_defeat])
	var partial: Dictionary = receipt.duplicate(true); partial.erase("shield_after")
	replay("Partial health snapshots cannot invent a typed contact",[partial])
	replay("Maximum range has no physical contact bloom",[],"range",true)
	for invalid in [null,{},[],true,NAN,INF,-1.0]:
		var malformed: Dictionary = receipt.duplicate(true); malformed.damage_applied = invalid
		check("Malformed damage value is never confirmed: " + str(invalid),Response.classify(malformed).is_empty())
	var generic := {"kind":"damage","damage_applied":28.0}
	check("Legacy positive receipt stays generic without inventing defeat",Response.classify(generic) == &"contact")
	var data = replay("Unknown kind cannot create a hit bloom",[{"kind":"guardian","unit_id":1,"position":Vector3.ZERO}],"unit")
	data = replay("A nonterminal empty contact does not create a bloom",[],"unit")
	data.impact.event_seq += 1
	data.impact.receipts = [receipt.duplicate(true)]
	check("A later real piercing-style receipt creates one contact",fx.consume_event(data.impact) and fx.report().impacts == 1)
	data.impact.event_seq += 1
	check("Higher sequence duplicate target/projectile has no second bloom",fx.consume_event(data.impact) and fx.report().impacts == 1)
	data.impact.event_seq += 1; data.impact.receipts[0].unit_id += 1
	check("Different accepted target can create another piercing contact",fx.consume_event(data.impact) and fx.report().impacts == 2)
	data.impact.event_seq += 1; data.impact.reason = "wall"; data.impact.receipts = []; data.impact.terminal = true
	check("Actual surface contact uses a dull wall response",fx.consume_event(data.impact) and fx.report().contact_styles.back().response == "wall")
	data.impact.event_seq += 1
	data.impact.age_s += .1; data.impact.time_s += .1
	var before_terminal_replay: Dictionary = fx._casts.values()[0].duplicate(true)
	var before_sequence: int = fx._sequence
	check("A terminated projectile cannot create a later contact",not fx.consume_event(data.impact) and fx.report().impacts == 3)
	check("Rejected terminal replay preserves real cast clock and event watermark",fx._casts.values()[0] == before_terminal_replay and fx._sequence == before_sequence)
	fx.reset()
	for reduced in [false,true]:
		fx.set_options({"reduced_effects":reduced,"reduced_motion":true})
		for kind in [&"health",&"shield",&"defeat",&"wall"]:
			fx._impact(Vector3(0,1,0),Color.WHITE,kind != &"wall",Vector3.BACK,kind)
			var impact: Dictionary = fx._impacts.back()
			var triangle_count: int = impact.root.get_child(0).mesh.surface_get_array_index_len(0)/3
			check("Distinct finite bounded geometry " + str(kind) + "/" + str(reduced),triangle_count <= 312 and triangle_count > 0 and impact.root.global_transform.is_finite(),{"triangles":triangle_count})
	check("All contact variants use only8 immutable cached meshes",fx._impact_meshes.size() == 8)
	var signatures := []
	for impact in fx._impacts: signatures.append(impact.root.global_transform)
	fx.set_suspended(true); fx.step(.2)
	check("Suspension freezes all contact transforms",signatures == fx._impacts.map(func(impact):return impact.root.global_transform))
	fx.set_suspended(false)
	fx.step(.43)
	check("Contact variants expire into the same bounded pool",fx.report().impacts == 0 and fx.report().allocated_impacts <= 18)
	for index in 200:
		var kind: StringName = [&"health",&"shield",&"defeat",&"wall"][index%4]
		fx._impact(Vector3(index%9,1,0),Color.WHITE,kind != &"wall",Vector3.BACK,kind)
	check("Dense contact mix keeps18nodes/5616triangles andzero lights or particles",fx.report().allocated_impacts == 18 and fx.report().impact_triangles <= 5616 and fx.report().lights == 0 and fx.report().particles == 0,fx.report())
	fx.reset(); check("Reset clears all pooled/live nodes",fx.get_child_count() == 0)
	var stable := true
	for path in source_before: stable = stable and FileAccess.get_sha256(path) == source_before[path]
	check("Selected sources remain stable during the run",stable)
	var playback_refs: Array[WeakRef] = []
	for voice in audio._world + [audio._feedback]:
		if voice.playing: playback_refs.append(weakref(voice.get_stream_playback()))
	audio.set_suspended(true)
	# Kit exit emits cancellation while its subscribers are still alive.
	kit.free();audio.free();fx.free();army.free()
	await process_frame
	var retire_started := Time.get_ticks_msec()
	while playback_refs.any(func(reference): return reference.get_ref() != null) and Time.get_ticks_msec() - retire_started < 1000:
		await create_timer(.025).timeout
	check("Stopped Dummy playback retires before engine teardown",not playback_refs.any(func(reference):return reference.get_ref() != null),{"sampled_playbacks":playback_refs.size(),"wait_ms":Time.get_ticks_msec()-retire_started})
	var passed := checks.all(func(item):return item.passed)
	var report := {"passed":passed,"checks":checks,"source_sha256":source_before,"scope":"Actual normal army/Rama kit damage receivers plus altered receipt counterexamples, CPU effect geometry and Dummy-driver voice selection. No actual rendered appearance, human listening, combat feel or hardware claim."}
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	quit(0 if passed else 1)
