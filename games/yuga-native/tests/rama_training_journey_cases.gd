extends SceneTree
const Journey = preload("res://scripts/rama_training_journey.gd")
const Practice = preload("res://scripts/rama_practice_army.gd")
const Target = preload("res://scripts/target.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array = []
var army
var kit
var vitals
var journey := Journey.new()
var events: Array = []
var targets: Array = []
func _initialize() -> void: call_deferred("run")
func check(label: String, passed: bool) -> void:
	checks.append({"case":label, "passed":passed})
	if not passed: push_error("JOURNEY FAILED: " + label)
func advance(seconds: float) -> void:
	for tick in int(ceil(seconds / .05)): army.step_simulation(.05)
func cast(id: String, facing := Vector3(0, 0, 1), target := Vector3.ZERO) -> bool:
	return kit.request_ability(id, Vector3.ZERO, facing, target).accepted
func run() -> void:
	for distance in [5, 8, 11]:
		var target = Target.new()
		root.add_child(target)
		target.position = Vector3(0, 0, distance)
		targets.append(target)
	army = Practice.new(); root.add_child(army); army.set_physics_process(false)
	check("real practice configures", army.configure(targets))
	kit = Kit.new(); root.add_child(kit)
	check("real kit configures", kit.configure(army))
	vitals = Vitals.new(); root.add_child(vitals)
	check("real hero receiver configures", vitals.configure(army))
	kit.set_hero_receiver(vitals, func(): return Vector3.ZERO)
	kit.set_movement_receiver(func(_origin, destination, _seconds): return {"accepted":true, "destination":destination})
	journey.reset(kit.generation)
	kit.ability_event.connect(func(event): events.append(event.duplicate(true)); journey.observe(event))
	check("initial hint identifies actual primary input", journey.report().hint == "LMB · Hit a target" and journey.report().completed == 0)
	check("miss cast admitted", cast("kodanda", Vector3.RIGHT))
	advance(1.1)
	check("release and range miss grant no learning credit", journey.report().completed == 0)
	check("primary hit cast admitted", cast("kodanda"))
	advance(.6)
	check("actual receiver damage advances primary", journey.report().completed == 1 and army.units[0].health == 62)
	var saved := Bindings.bindings.duplicate()
	Bindings.bindings.pulse = KEY_B
	check("next hint reads live remapping", journey.report().hint == "B · Pierce a target")
	Bindings.bindings = saved
	check("piercing cast admitted", cast("piercing_dawn"))
	advance(1.4)
	check("piercing target receipt advances once", journey.report().completed == 2 and not army.units[0].alive)
	var damage_event: Dictionary = events.filter(func(e): return e.kind == "impact" and e.get("reason") == "unit")[0]
	check("duplicate or stale receipt cannot advance", not journey.observe(damage_event) and journey.report().completed == 2)
	check("step cast admitted", cast("measured_step", Vector3.RIGHT))
	advance(.7)
	check("accepted collision checked step advances", journey.report().completed == 3)
	check("guardian cast admitted", cast("guardian_circle"))
	advance(.6)
	check("actual hero shield receipt advances", vitals.shield > 0 and journey.report().completed == 4)
	# The ward's shielding begins before the caster's actual recovery ends.
	advance(.3)
	check("volley cast admitted", cast("dawn_volley"))
	advance(1.6)
	check("actual volley hit completes all five", journey.report().complete and journey.report().completed == 5)
	var before := journey.report()
	paused = true
	check("pause cannot advance authority", not army.step_simulation(.05) and journey.report() == before)
	paused = false
	army.reset("journey reset")
	check("ordinary practice reset clears progress", journey.report().completed == 0 and journey.report().generation == kit.generation)
	check("old generation hit ignored after reset", not journey.observe(damage_event) and journey.report().completed == 0)
	army.boxes.append({"position":Vector3(0, 2, 3), "size":Vector3(10, 4, .1)})
	check("cover counter cast admitted", cast("piercing_dawn"))
	advance(1.4)
	check("hard cover prevents damage and learning credit", journey.report().completed == 0 and army.units[0].health == 90)
	army.reset("cancel case")
	check("cancel case accepted", cast("dawn_volley"))
	kit.cancel_active("learner paused")
	advance(1.4)
	check("cancelled windup grants no credit", journey.report().completed == 0)
	var hashes := {}
	for path in ["res://scripts/rama_training_journey.gd", "res://scripts/courtyard.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/rama_practice_army.gd"]: hashes[path] = FileAccess.get_sha256(path)
	var passed := checks.all(func(c): return c.passed)
	var result := {"suite":"rama_training_journey_cases", "passed":passed, "checks":checks, "source_sha256":hashes, "scope":"Actual kit and receiver learning receipts, misses/cover/cancel/reset/remap; movement receiver is a fixture, ordinary physical input separately reviewed."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var path := arg.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			var file := FileAccess.open(path, FileAccess.WRITE); file.store_string(JSON.stringify(result, "  ")); file.close()
	print("Training journey: %d/%d" % [checks.filter(func(c): return c.passed).size(), checks.size()])
	kit.free(); vitals.free(); army.free()
	for target in targets: target.free()
	quit(0 if passed else 1)
