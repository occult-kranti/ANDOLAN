extends SceneTree
## Independent adversarial fixture using actual practice receivers and authority
## ticks. It does not claim interactive input or rendered motion.

const PracticeArmy = preload("res://scripts/rama_practice_army.gd")
const Target = preload("res://scripts/target.gd")
const Combat = preload("res://scripts/hanuman_combat.gd")
const FORWARD := Vector3(0, 0, 1)

var army: Node3D
var combat: Node
var targets: Array[Node3D] = []
var events: Array[Dictionary] = []
var checks: Array[Dictionary] = []
var moves: Array = []
var accept_move := false


func _initialize() -> void:
	call_deferred("run")


func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"case": label, "passed": passed, "details": details})
	if not passed:
		print("FAIL ", label, ": ", details)


func request(id: String, point := Vector3(0, 0, 8), direction := FORWARD) -> Dictionary:
	return combat.request_ability(id, Vector3.ZERO, direction, point)


func advance(ticks: int) -> void:
	for _i in ticks:
		army.step_simulation(.05)


func clear() -> void:
	army.reset("independent_reset")
	events.clear()
	moves.clear()


func receive_move(origin: Vector3, target: Vector3, duration: float) -> bool:
	moves.append([origin, target, duration])
	return accept_move


func kinds() -> Array:
	return events.map(func(event): return event.get("kind", ""))


func event_order() -> bool:
	var seq := -1
	var generation := -1
	for event in events:
		var current := int(event.get("generation", -1))
		var next := int(event.get("event_seq", -1))
		if current < 0 or next < 1 or current < generation or (current == generation and next <= seq):
			return false
		generation = current
		seq = next
	return true


func place(index: int, p: Vector3, team: String) -> void:
	targets[index].position = p
	army.units[index].global_position = p
	army.units[index].team = team


func run() -> void:
	for i in 5:
		var target := Target.new()
		target.name = "ReviewTarget%d" % i
		root.add_child(target)
		targets.append(target)
	army = PracticeArmy.new()
	root.add_child(army)
	army.set_physics_process(false)
	if not army.configure(targets):
		check("real practice army configures", false)
		finish()
		return
	combat = Combat.new()
	root.add_child(combat)
	combat.ability_event.connect(func(event): events.append(event.duplicate(true)))
	if not combat.configure(army, Callable(self, "receive_move")):
		check("real Hanuman combat configures", false)
		finish()
		return

	# Five actual receivers exercise angle, distance, team and wall filtering.
	place(0, Vector3(-.35, 0, 1.4), "moon")
	place(1, Vector3(0, 0, -1.4), "moon")
	place(2, Vector3(0, 0, 1.5), "sun")
	place(3, Vector3(1.2, 0, 3.4), "moon")
	place(4, Vector3(15, 0, 13), "moon")
	clear()
	var main_receipt := request("vajra_gada")
	check("valid primary receives a cast", main_receipt.get("accepted", false), main_receipt)
	advance(24)
	check("primary reaches forward enemy and spares ally/rear/distant enemies",
		army.units[0].health < 90 and army.units[1].health == 90 and army.units[2].health == 90 and army.units[4].health == 90)
	check("primary emits exactly one release and a single terminal end",
		kinds().count("release") == 1 and kinds().count("end") == 1 and event_order(), {"kinds": kinds()})

	clear()
	army.boxes.append({"position": Vector3(0, 2, 1), "size": Vector3(16, 4, .08)})
	var wall := request("vajra_gada")
	advance(24)
	check("thin wall prevents real damage", wall.get("accepted", false) and army.units[0].health == 90 and army.units[3].health == 90)
	army.boxes.pop_back()

	clear()
	check("zero and nonfinite aim are rejected without receipts",
		not request("vajra_gada", Vector3.ZERO, Vector3.ZERO).get("accepted", false)
		and not request("vajra_gada", Vector3(NAN, 0, 0)).get("accepted", false) and events.is_empty())
	check("out-of-range landing is rejected before beginning",
		not request("mountain_pulse", Vector3(0, 0, 24)).get("accepted", false) and events.is_empty())

	clear()
	place(0, Vector3(0, 0, 8.0), "moon")
	place(2, Vector3(.5, 0, 8.0), "sun")
	army.units[2].take_hit(5.5)
	var ultimate := request("mountain_pulse")
	check("clear in-range ultimate is accepted", ultimate.get("accepted", false), ultimate)
	advance(4)
	army.set_suspended(true)
	advance(30)
	check("pause leaves pending ultimate and receiver state untouched",
		army.units[0].health == 90 and army.units[2].health == 84.5 and kinds().count("release") == 0 and kinds().count("impact") == 0,
		{"kinds": kinds()})
	army.set_suspended(false)
	advance(40)
	check("resumed ultimate reaches enemy once and caps ally heal",
		army.units[0].health < 90 and army.units[2].health == 90 and kinds().count("impact") == 1 and event_order(),
		{"kinds": kinds(), "enemy_health": army.units[0].health, "ally_health": army.units[2].health})

	clear()
	request("mountain_pulse")
	advance(2)
	var pending_kinds := kinds()
	army.reset("cancel_pending")
	advance(60)
	check("reset invalidates a started ultimate before it can damage or heal",
		pending_kinds.has("begin") and army.units[0].health == 90 and kinds().count("impact") == 0 and event_order(),
		{"kinds": kinds(), "pending": pending_kinds})

	clear()
	request("maruti_udayana", Vector3(0, 0, 4))
	advance(35)
	check("blocked movement receiver is called once and cannot apply damage",
		moves.size() == 1 and army.units[0].health == 90 and kinds().count("impact") == 0 and event_order(),
		{"move_count": moves.size(), "kinds": kinds()})

	clear()
	place(0, Vector3(-.35, 0, 1.4), "moon")
	place(2, Vector3(0, 0, 1.5), "sun")
	place(3, Vector3(0, 0, -1.4), "sun")
	request("vajra_kavacha")
	advance(12)
	check("ward shields only its forward ally", army.units[2].shield == 48 and army.units[3].shield == 0 and army.units[0].shield == 0)
	advance(65)
	check("ward expires on the receiving clock", army.units[2].shield == 0 and army.units[2].shield_until == 0)

	clear()
	place(3, Vector3(1, 0, -1.5), "moon")
	request("lanka_dahan")
	advance(19)
	var left_health: float = army.units[1].health
	place(1, Vector3(0, 0, -6.0), "moon")
	advance(50)
	check("rear embers damage once on release and only while exposed",
		is_equal_approx(left_health, 58.0) and is_equal_approx(float(army.units[1].health), left_health)
		and is_equal_approx(float(army.units[3].health), 46.0) and army.units[0].health == 90,
		{"left_health": left_health, "remaining_health": army.units[3].health, "forward_health": army.units[0].health})

	clear()
	var reset_callback := func(_target, _defeated): army.reset("receiver_reentry")
	targets[0].struck.connect(reset_callback, CONNECT_ONE_SHOT)
	request("vajra_gada")
	advance(14)
	check("reset during a receiver callback stops stale payload and events",
		army.units[0].health == 90 and kinds().count("reset") == 1 and kinds().count("impact") == 0 and event_order(),
		{"kinds": kinds()})

	clear()
	var mutation := func(event):
		if event.get("kind") != "begin": return
		event.geometry["range_m"] = .01
		event.timing["windup_s"] = 20.0
	combat.ability_event.connect(mutation)
	request("vajra_gada")
	advance(14)
	check("subscriber mutation cannot alter geometry or timing applied to receivers",
		army.units[0].health == 56 and kinds().count("impact") == 1 and event_order())
	combat.ability_event.disconnect(mutation)
	finish()


func finish() -> void:
	var report := {"checks": checks, "passed": checks.all(func(entry): return entry.passed), "source_sha256": {}}
	for path in [get_script().resource_path, "res://scripts/hanuman_combat.gd",
		"res://assets/design/hanuman-ability-kit.json", "res://scripts/rama_practice_army.gd",
		"res://scripts/rama_practice_target.gd", "res://scripts/target.gd"]:
		report.source_sha256[path] = FileAccess.get_sha256(path)
	for argument in OS.get_cmdline_user_args():
		if not argument.begins_with("--report="):
			continue
		var path := argument.trim_prefix("--report=")
		var file := FileAccess.open(path, FileAccess.WRITE) if not FileAccess.file_exists(path) else null
		if file == null:
			printerr("Review output path must be writable and fresh: ", path)
			quit(2)
			return
		file.store_string(JSON.stringify(report, "  ") + "\n")
		file.close()
	print("Hanuman independent checks: %d/%d" % [checks.filter(func(entry): return entry.passed).size(), checks.size()])
	if is_instance_valid(combat): combat.free()
	if is_instance_valid(army): army.free()
	for target in targets:
		target.free()
	quit(0 if report.passed else 1)
