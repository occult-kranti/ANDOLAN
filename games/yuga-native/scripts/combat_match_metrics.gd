extends Node
## Read-only local round recorder. Army time, core health, earnings and last hits
## remain authoritative. Hero totals count only receipts observed after attach.
signal changed
const MAX_CORE_SAMPLES := 240
const INITIAL_SAMPLE_PERIOD := 1.0
var configured := false
var army: Node
var hero_runtime: Node
var _vitals: Node
var _round := 0
var _completed := false
var _awaiting_reset := false
var _recorded_from_s := 0.0
var _sample_period := INITIAL_SAMPLE_PERIOD
var _next_sample_s := 0.0
var _battle: Dictionary = {}
var _timeline: Array = []
var _hero: Dictionary = {}
var _event_generation := -1
var _event_sequence := -1

func configure(battle_army: Node, runtime: Node) -> bool:
	if configured or not is_instance_valid(battle_army) or not battle_army.has_method("report") or not is_instance_valid(runtime) or not runtime.has_signal("combat_event"): return false
	for event_name in ["simulation_stepped", "simulation_reset", "changed", "outcome"]:
		if not battle_army.has_signal(event_name): return false
	var candidate: Dictionary = battle_army.report()
	if not candidate.get("configured", false) or not _valid_battle(candidate): return false
	army = battle_army
	hero_runtime = runtime
	_vitals = runtime.get("vitals")
	army.simulation_stepped.connect(_on_step)
	army.simulation_reset.connect(_on_reset)
	army.changed.connect(_on_changed)
	army.outcome.connect(_on_outcome)
	hero_runtime.combat_event.connect(_on_combat_event)
	if is_instance_valid(_vitals):
		if _vitals.has_signal("damaged"): _vitals.damaged.connect(_on_hero_damaged)
		if _vitals.has_signal("defeated"): _vitals.defeated.connect(_on_hero_defeated)
	configured = true
	_clear_round()
	_recorded_from_s = float(candidate.elapsed)
	_capture(candidate, true)
	_completed = not String(candidate.get("winner", "")).is_empty()
	return true

func _exit_tree() -> void:
	for item in [[army, "simulation_stepped", _on_step], [army, "simulation_reset", _on_reset], [army, "changed", _on_changed], [army, "outcome", _on_outcome], [hero_runtime, "combat_event", _on_combat_event], [_vitals, "damaged", _on_hero_damaged], [_vitals, "defeated", _on_hero_defeated]]:
		if is_instance_valid(item[0]) and item[0].is_connected(item[1], item[2]): item[0].disconnect(item[1], item[2])

func _number(value: Variant) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value))

func _valid_battle(value: Dictionary) -> bool:
	var cores: Variant = value.get("cores")
	return _number(value.get("elapsed")) and float(value.elapsed) >= 0 and cores is Dictionary and _number(cores.get("sun")) and _number(cores.get("moon")) and _number(value.get("gold")) and _number(value.get("kills"))

func _clear_round() -> void:
	_round += 1
	_completed = false
	_recorded_from_s = 0.0
	_sample_period = INITIAL_SAMPLE_PERIOD
	_next_sample_s = 0.0
	_battle.clear()
	_timeline.clear()
	_hero = {"casts_started":0, "releases":0, "damage_receipts":0, "damage_dealt":0.0, "damage_taken":0.0, "deaths":0}
	_event_generation = -1
	_event_sequence = -1

func _on_reset(_reason: String) -> void:
	# The army emits reset before clearing its fields, sometimes twice when a
	# receiver requests reset. Wait for its changed event before reading zeroes.
	if not _awaiting_reset: _clear_round()
	_awaiting_reset = true
	changed.emit()

func _on_changed() -> void:
	if not configured or _completed or not is_instance_valid(army): return
	var current: Dictionary = army.report()
	if not _valid_battle(current): return
	if _awaiting_reset:
		if not String(current.get("winner", "")).is_empty(): return
		_awaiting_reset = false
	_capture(current, _timeline.is_empty())

func _on_step(_delta: float) -> void:
	if not configured or _completed or _awaiting_reset or not is_instance_valid(army): return
	var elapsed: Variant = army.get("elapsed")
	if _number(elapsed) and float(elapsed) + 1e-8 >= _next_sample_s:
		_capture(army.report())

func _on_outcome(_winner: String) -> void:
	if not configured or _completed or _awaiting_reset or not is_instance_valid(army): return
	_capture(army.report(), true)
	_completed = true
	changed.emit()

func _capture(current: Dictionary, force := false) -> void:
	if not _valid_battle(current): return
	_battle = {"elapsed":float(current.elapsed), "cores":current.cores.duplicate(true), "gold":int(current.gold), "kills":int(current.kills), "winner":String(current.get("winner", ""))}
	var time_s := float(current.elapsed)
	if not force and time_s + 1e-8 < _next_sample_s: return
	var sample := {"time_s":time_s, "sun":float(current.cores.sun), "moon":float(current.cores.moon)}
	if not _timeline.is_empty() and is_equal_approx(float(_timeline[-1].time_s), time_s): _timeline[-1] = sample
	else: _timeline.append(sample)
	if _timeline.size() > MAX_CORE_SAMPLES:
		# Keep the whole round at a progressively coarser cadence, including the
		# actual first and latest sample; never synthesize intermediate values.
		var reduced: Array = [_timeline[0]]
		for index in range(2, _timeline.size() - 1, 2): reduced.append(_timeline[index])
		reduced.append(_timeline[-1])
		_timeline = reduced
		_sample_period *= 2.0
	_next_sample_s = time_s + _sample_period

func _on_combat_event(event: Dictionary) -> void:
	if not configured or _completed or _awaiting_reset: return
	if not event.get("generation") is int or not event.get("event_seq") is int: return
	var generation := int(event.generation)
	var sequence := int(event.event_seq)
	if generation < _event_generation or (generation == _event_generation and sequence <= _event_sequence): return
	_event_generation = generation
	_event_sequence = sequence
	match String(event.get("kind", "")):
		"begin": _hero.casts_started += 1
		"release": _hero.releases += 1
		"impact":
			var receipts: Variant = event.get("receipts", [])
			if not receipts is Array: return
			for receipt in receipts:
				if not receipt is Dictionary or receipt.get("kind") != "damage": continue
				var amount: Variant = receipt.get("damage_applied")
				if _number(amount) and float(amount) > 0:
					_hero.damage_receipts += 1
					_hero.damage_dealt += float(amount)

func _on_hero_damaged(receipt: Dictionary) -> void:
	if _completed or _awaiting_reset or not receipt.get("accepted", false): return
	var amount: Variant = receipt.get("damage_applied")
	if _number(amount) and float(amount) > 0: _hero.damage_taken += float(amount)

func _on_hero_defeated(receipt: Dictionary) -> void:
	if not _completed and not _awaiting_reset and receipt.get("accepted", false): _hero.deaths += 1

func report() -> Dictionary:
	var result := _battle.duplicate(true)
	result.merge({"configured":configured, "round":_round, "completed":_completed, "recorded_from_s":_recorded_from_s, "core_timeline":_timeline.duplicate(true), "sample_capacity":MAX_CORE_SAMPLES, "sample_period_s":_sample_period, "hero":_hero.duplicate(true), "scope":"Offline practice; gold is earned total, kills are confirmed player lane last hits; hero receipts observed after attach."})
	return result
