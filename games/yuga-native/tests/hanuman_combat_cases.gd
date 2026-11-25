extends SceneTree
## Uses the actual courtyard adapter and receiver nodes, including the real shield clock.
const Army = preload("res://scripts/rama_practice_army.gd")
const Target = preload("res://scripts/target.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
const Combat = preload("res://scripts/hanuman_combat.gd")
const ORIGIN := Vector3.ZERO
const FORWARD := Vector3.FORWARD
const GADA := "vajra_gada"
const WARD := "vajra_kavacha"
const VAULT := "maruti_udayana"
const TAIL := "lanka_dahan"
const MOUNTAIN := "mountain_pulse"

var arena := Node3D.new()
var army := Army.new()
var hero := Vitals.new()
var kit := Combat.new()
var targets: Array[Node3D] = []
var cases: Array = []
var moves: Array = []
var accept_movement := true

func _initialize() -> void:
	call_deferred("_run")

func check(name_: String, passed: bool) -> void:
	cases.append({"name": name_, "passed": passed})
	if not passed:
		printerr("FAIL ", name_)

func step(count: int) -> void:
	for _index in count:
		army.step_simulation(.05)

func cast(id: String, target := Vector3.ZERO) -> Dictionary:
	return kit.request_ability(id, ORIGIN, FORWARD, target)

func close_to(value: float, expected: float) -> bool:
	return absf(value - expected) < 1e-5

func event_times(kind: String, id: String) -> Array:
	var selected: Array = []
	for event in kit.report().history:
		if event.kind == kind and event.ability_id == id:
			selected.append(event.age_s)
	return selected

func _movement(origin: Vector3, destination: Vector3, duration: float) -> bool:
	moves.append([origin, destination, duration])
	return accept_movement

func _run() -> void:
	root.add_child(arena)
	arena.add_child(army)
	arena.add_child(hero)
	arena.add_child(kit)
	for point in [Vector3(0, 0, -3.5), Vector3(0, 0, 2.5), Vector3(3, 0, -2.5), Vector3(-2, 0, -4), Vector3(6, 0, -6)]:
		var target := Target.new()
		target.position = point
		target.number = targets.size() + 1
		arena.add_child(target)
		targets.append(target)
	check("Actual practice clock and hero receiver configured", army.configure(targets) and hero.configure(army))
	army.set_physics_process(false)
	army.units[3].team = "sun"
	check("Five unique profile roles configure", kit.configure(army, _movement, hero, func(): return ORIGIN) and kit.report().abilities.size() == 5)

	check("Unknown and nonfinite requests fail before charging", not cast("unknown").accepted and not kit.request_ability(GADA, ORIGIN, Vector3(INF, 0, 0), ORIGIN).accepted)
	check("Primary accepted on ground", cast(GADA).accepted)
	check("Windup blocks another action", not cast(WARD).accepted)
	step(4)
	check("Nothing applies before the Gada release tick", close_to(army.units[0].health, 90))
	step(1)
	check("Gada hits exactly on sector radius, misses rear, side and ally", close_to(army.units[0].health, 56) and close_to(army.units[1].health, 90) and close_to(army.units[2].health, 90) and close_to(army.units[3].health, 90))
	check("One Gada impact, exact authority timestamp", event_times("impact", GADA).size() == 1 and close_to(event_times("impact", GADA)[0], .25))
	step(6)
	check("Action recovers before cadence cooldown expires", not kit.report().action_locked and not cast(GADA).accepted)
	step(1)
	check("Independent Gada cooldown reopens", cast(GADA).accepted)
	kit.cancel_active("test interrupt")
	step(12)
	check("Cancel before release applies no phantom damage", close_to(army.units[0].health, 56))

	army.reset("ward test")
	check("Kavacha begins", cast(WARD).accepted)
	step(7)
	check("Kavacha supports living caster and forward ally only", close_to(hero.shield, 48) and close_to(army.units[3].shield, 48) and close_to(army.units[0].shield, 0))
	var blocked := hero.receive_damage(23)
	check("Actual vitals absorb ward hit first", blocked.accepted and close_to(hero.health, 300) and close_to(hero.shield, 25))
	step(60)
	check("Ward expires from the actual receiver clock", close_to(hero.shield, 0) and close_to(army.units[3].shield, 0))

	army.reset("rear sector test")
	check("Tail cast accepted", cast(TAIL).accepted)
	step(9)
	check("Tail reverses sector, strikes rear only", close_to(army.units[1].health, 62) and close_to(army.units[0].health, 90))
	step(8)
	check("Lingering zone follows its own clock after action recovery", not kit.report().action_locked and close_to(army.units[1].health, 58.8) and cast(GADA).accepted)
	targets[1].position.z = -2
	step(12)
	check("A target leaving the marked tail sector avoids lingering damage", close_to(army.units[1].health, 24.8))
	targets[1].position.z = 2.5
	step(20)
	check("Tail active expires and old ticks cease", event_times("end", TAIL).size() == 1 and close_to(event_times("end", TAIL)[0], 2.45))
	var after: float = army.units[1].health
	step(10)
	check("No residual tick after exact active window", close_to(army.units[1].health, after))

	army.reset("mountain test")
	hero.receive_damage(25)
	army.units[3].take_hit(20)
	check("Mountain invalid target rejected with no cost", not cast(MOUNTAIN, Vector3(0, 0, -14.01)).accepted)
	var landing := Vector3(0, 0, -3.5)
	check("Mountain accepts visible aimed ground point after rejection", cast(MOUNTAIN, landing).accepted)
	step(22)
	check("Mountain release and travel do not apply early payload", event_times("release", MOUNTAIN).size() == 1 and close_to(army.units[0].health, 90) and close_to(hero.health, 275))
	step(1)
	check("Mountain applies real capped healing and damage on landing", close_to(army.units[0].health, 25) and close_to(army.units[3].health, 90) and close_to(hero.health, 300))
	check("Mountain does not call movement receiver", moves.is_empty())
	var pulse: Array = event_times("impact", MOUNTAIN)
	check("Mountain impact appears once at 1.15s", pulse.size() == 1 and close_to(pulse[0], 1.15))

	army.reset("cover test")
	army.boxes.append({"position": Vector3(0, 1, -2), "size": Vector3(1, 2, .4)})
	check("Cover rejects projected Mountain target before cast", not cast(MOUNTAIN, Vector3(0, 0, -3)).accepted)
	check("Primary sector is allowed to miss through cover", cast(GADA).accepted)
	step(11)
	check("Receiver line cover protects sector target", close_to(army.units[0].health, 90))
	check("Vault requests shorter grounded destination", cast(VAULT).accepted)
	step(4)
	check("Vault calls receiver once at release with conservative wall clearance", moves.size() == 1 and moves[0][1].z < -0.5 and moves[0][1].z > -1.5 and close_to(moves[0][2], .45))
	army.reset("new cover test")
	army.boxes.pop_back()
	check("Clear vault queues", cast(VAULT).accepted)
	army.boxes.append({"position": Vector3(0, 1, -2), "size": Vector3(1, 2, .4)})
	step(4)
	check("New cover cancels movement before actor callback", moves.size() == 1 and event_times("cancel", VAULT).size() == 1)
	army.boxes.pop_back()

	army.reset("pause and reset test")
	check("Fresh Gada", cast(GADA).accepted)
	step(2)
	kit.set_suspended(true)
	step(20)
	check("Suspension freezes windup and rejects casts", close_to(kit.report().elapsed, .10) and not cast(WARD).accepted and close_to(army.units[0].health, 90))
	kit.set_suspended(false)
	var old_generation := kit.generation
	targets[0].struck.connect(func(_target, _defeated): army.reset("inside damage callback"), CONNECT_ONE_SHOT)
	step(3)
	check("Reset during receiver callback invalidates old cast and restores targets", kit.generation > old_generation and kit.report().history.size() == 1 and kit.report().history[0].kind == "reset" and close_to(army.units[0].health, 90))
	check("Fresh generation accepts after reset", cast(GADA).accepted)
	var copy := kit.report()
	copy.abilities[0].effects[0].amount = 500
	copy.history.back().geometry.range_m = 500
	check("Reports do not mutate authority profile or accepted footprint", close_to(kit.report().abilities[0].effects[0].amount, 34) and close_to(kit.report().history.back().geometry.range_m, 3.5))
	var failures := 0
	for result in cases:
		if not result.passed:
			failures += 1
	var report := {"passed": cases.size() - failures, "failed": failures, "cases": cases}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var output := FileAccess.open(argument.trim_prefix("--report="), FileAccess.WRITE)
			if output != null:
				output.store_string(JSON.stringify(report, "  ") + "\n")
	print("YUGA_HANUMAN_COMBAT ", JSON.stringify(report))
	arena.free()
	quit(1 if failures > 0 else 0)
