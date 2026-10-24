extends SceneTree
## Read-only observer of the existing original-game Kit/Army contract.
## No renderer, timers, audio playback, asset export or gameplay replacement.
const Army = preload("res://scripts/lane_army.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const MAP := "res://assets/world/confluence-map.json"
var output := ""
var checks: Array = []
var observed: Array = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	call_deferred("run")

func check(label: String, passed: bool) -> void:
	checks.append({"name":label, "passed":passed})
	print("PASS " if passed else "FAIL ", label)

func receive(event: Dictionary) -> void:
	var row := {}
	for key in ["kind", "generation", "event_seq", "cast_id", "ability_id", "time_s", "age_s", "release_age_s"]:
		if event.has(key): row[key] = event[key]
	observed.append(row)

func run() -> void:
	if output.is_empty() or not output.is_absolute_path() or FileAccess.file_exists(output):
		push_error("Need a fresh absolute --output file"); quit(2); return
	var pins := {}
	for path in [MAP, "res://assets/design/rama-ability-kit.json", "res://scripts/lane_army.gd", "res://scripts/lane_minion.gd", "res://scripts/world_render_resources.gd", "res://scripts/ultimate_rules.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/rama_motion.gd", "res://scripts/rama_action_audio.gd", "res://scripts/rama_ability_effects.gd", "res://assets/animations/rama_hero_motion.tres"]:
		pins[path] = FileAccess.get_sha256(path)
	var manifest_text := FileAccess.get_file_as_string(MAP)
	var manifest: Dictionary = JSON.parse_string(manifest_text)
	var army := Army.new()
	army.visual_enabled = false
	root.add_child(army)
	army.set_physics_process(false)
	check("existing army configures against unchanged canonical manifest", army.configure(manifest, null))
	var kit := Kit.new()
	root.add_child(kit)
	check("existing original Rama kit configures", kit.configure(army))
	kit.set_movement_receiver(func(_origin, destination, _duration): return {"accepted":true, "destination":destination})
	kit.ability_event.connect(receive)
	var timelines := []
	for ability in Kit.IDS:
		army.reset()
		observed.clear()
		var request: Dictionary = kit.request_ability(ability, Vector3.ZERO, Vector3.BACK, Vector3(0,0,4))
		check(ability + " actual request accepted", request.accepted)
		var accepted_steps := 0
		for _tick in 170:
			if army.step_simulation(.05): accepted_steps += 1
		check(ability + " all 170 fixed 20 Hz steps accepted", accepted_steps == 170)
		var trace := observed.duplicate(true)
		var selected := trace.filter(func(row): return row.kind != "tick")
		check(ability + " one actual begin release end", selected.filter(func(row): return row.kind == "begin").size() == 1 and selected.filter(func(row): return row.kind == "release").size() == 1 and selected.filter(func(row): return row.kind == "end").size() == 1)
		var finite := true
		var previous := -1.0
		for row in trace:
			finite = finite and is_finite(row.time_s) and row.time_s >= previous
			previous = row.time_s
		check(ability + " actual chronology finite and monotonic", finite)
		timelines.append({"ability":ability, "simulation_hz":20, "simulation_steps":accepted_steps, "all_event_count":trace.size(), "tick_count":trace.size()-selected.size(), "events":selected})
	check("canonical manifest bytes and loaded dictionary unchanged", FileAccess.get_file_as_string(MAP) == manifest_text and manifest == JSON.parse_string(manifest_text))
	var stable := true
	for path in pins: stable = stable and FileAccess.get_sha256(path) == pins[path]
	check("all observed production source bytes unchanged", stable)
	kit.free(); army.free()
	var report := {"schema":1,"scope":"Actual original Rama Kit/Army event observation, no audio/render/rig/online claim", "engine":Engine.get_version_info(), "probe_sha256":FileAccess.get_sha256(get_script().resource_path), "source_pins":pins,"checks":checks,"timelines":timelines}
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file == null: quit(2); return
	file.store_string(JSON.stringify(report,"\t")); file.close()
	quit(0 if checks.all(func(row): return row.passed) else 1)
