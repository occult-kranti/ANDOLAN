extends Node
## Original match-local spending owner. The lane army remains the reward owner.
## The host may stop player input while shopping; battle/receivers keep running.
signal changed
signal purchased(receipt: Dictionary)

const CATALOG_PATH := "res://assets/design/native-field-shop.json"
const MAX_ARROWS := 12
const MAX_GOLD := 1000000000
const MAX_NONCE := 2147483647
const EFFECTS := {"heal":"heal", "arrows":"arrows", "ward":"shield", "escort":"escort"}

var configured := false
var epoch := 0
var army: Node3D
var runtime: Node
var player: Node3D
var spawn := Vector3.ZERO
var _vitals: Node
var _rules: Dictionary = {}
var _items: Array[Dictionary] = []
var _earned := 0
var _spent := 0
var _last_gold := 0
var _pending_cost := 0
var _awaiting_reset := false
var _in_purchase := false
var _publishing := false
var _ever_configured := false
var _highest_nonce := 0
var _receipts: Dictionary = {}
var _receipt_order: Array[int] = []
var _accepted := 0
var _ignored_reward_totals := 0
var _last_reason := "Return to Confluence to use the field shop"

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE

func _number(value: Variant, low: float, high: float) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and float(value) >= low and float(value) <= high

func _whole(value: Variant, low: int, high: int) -> bool:
	return _number(value, low, high) and float(value) == floorf(float(value))

func _load_catalog(path: String) -> Dictionary:
	if not FileAccess.file_exists(path) or FileAccess.get_file_as_bytes(path).size() > 16384: return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary or parsed.get("schema_version") != 1 or not parsed.get("items") is Array or parsed.items.size() != 4: return {}
	if not _whole(parsed.get("starting_gold"), 0, 1000) or not _number(parsed.get("radius_m"), 1, 20) or not _number(parsed.get("height_tolerance_m"), .1, 3) or not _whole(parsed.get("receipt_capacity"), 8, 128): return {}
	var ids: Dictionary = {}
	for item: Variant in parsed.items:
		if not item is Dictionary or not item.get("id") is String or not EFFECTS.has(item.id) or ids.has(item.id) or item.get("effect") != EFFECTS[item.id]: return {}
		ids[item.id] = true
		for key in ["title", "description", "icon"]:
			if not item.get(key) is String or item[key].is_empty() or item[key].length() > 200: return {}
		if not _whole(item.get("cost"), 1, 1000): return {}
		match item.effect:
			"heal":
				if not _number(item.get("amount"), 1, 300): return {}
			"arrows":
				if not _whole(item.get("amount"), 1, MAX_ARROWS): return {}
			"shield":
				if not _number(item.get("amount"), 1, 100) or not _number(item.get("duration_s"), .1, 12): return {}
			"escort":
				if item.get("role") != "spearman" or not _number(item.get("attack_damage"), 1, 40) or item.get("max_health") != 105 or item.get("lifetime_s") != 9: return {}
	return parsed

func configure(army_value: Node3D, runtime_value: Node, player_value: Node3D, spawn_value: Vector3, catalog_path := CATALOG_PATH) -> bool:
	# A live owner cannot be recreated through configure to refresh its allowance.
	if _ever_configured or configured or _in_purchase or _publishing or not spawn_value.is_finite(): return false
	if not is_instance_valid(army_value) or not army_value.get("configured") or not army_value.has_signal("gold_changed") or not army_value.has_signal("simulation_reset"): return false
	if not army_value.has_method("plan_temporary_pair") or not army_value.has_method("spawn_temporary_pair"): return false
	if not is_instance_valid(runtime_value) or not runtime_value.get("configured") or runtime_value.get("player") != player_value: return false
	if not is_instance_valid(player_value) or not player_value.has_signal("changed") or not player_value.get("ammo") is int: return false
	var receiver: Node = runtime_value.get("vitals")
	if not is_instance_valid(receiver) or not receiver.get("configured") or not receiver.has_method("report") or not receiver.has_method("receive_heal") or not receiver.has_method("apply_shield"): return false
	if not _whole(army_value.get("gold"), 0, MAX_GOLD): return false
	var candidate := _load_catalog(catalog_path)
	if candidate.is_empty(): return false
	army = army_value; runtime = runtime_value; player = player_value; spawn = spawn_value; _vitals = receiver
	_rules = candidate.duplicate(true)
	for item: Dictionary in candidate.items:
		var copy := item.duplicate(true)
		copy.cost = int(copy.cost)
		_items.append(copy)
	_earned = int(army.gold); _last_gold = _earned
	configured = true; _ever_configured = true; epoch += 1
	army.gold_changed.connect(_on_gold_changed)
	army.simulation_reset.connect(_on_reset)
	_last_reason = "Field shop ready · battle continues"
	changed.emit()
	return true

func _exit_tree() -> void:
	if is_instance_valid(army):
		if army.gold_changed.is_connected(_on_gold_changed): army.gold_changed.disconnect(_on_gold_changed)
		if army.simulation_reset.is_connected(_on_reset): army.simulation_reset.disconnect(_on_reset)
	configured = false

func _on_reset(_reason: String) -> void:
	# Army emits this before zeroing gold. Do not sample the old total here.
	epoch += 1
	_earned = 0; _spent = 0; _last_gold = 0; _pending_cost = 0
	_highest_nonce = 0; _receipts.clear(); _receipt_order.clear(); _accepted = 0
	_awaiting_reset = true
	_last_reason = "Round is resetting"
	changed.emit()

func _on_gold_changed(total: Variant) -> void:
	if not configured or not _whole(total, 0, MAX_GOLD):
		_ignored_reward_totals += 1
		return
	var value := int(total)
	if _awaiting_reset:
		if value != 0: return
		_awaiting_reset = false
		_last_reason = "New round · field allowance restored"
	elif value < _last_gold:
		_ignored_reward_totals += 1
		return
	_earned += value - _last_gold
	_last_gold = value
	changed.emit()

func _wallet() -> int:
	return maxi(0, int(_rules.get("starting_gold", 0)) + _earned - _spent - _pending_cost)

func _near_shop() -> bool:
	if not configured or not is_instance_valid(player) or not player.global_position.is_finite(): return false
	var point := player.global_position
	return absf(point.y - spawn.y) <= float(_rules.height_tolerance_m) and Vector2(point.x - spawn.x, point.z - spawn.z).length() <= float(_rules.radius_m)

func _base_reason() -> String:
	if not configured or not is_inside_tree() or is_queued_for_deletion() or not is_instance_valid(army) or not is_instance_valid(runtime) or not is_instance_valid(player) or not is_instance_valid(_vitals): return "Field shop is unavailable"
	if _awaiting_reset: return "Round is resetting"
	if get_tree().paused: return "Resume practice before buying"
	if not army.get("configured") or not runtime.get("configured") or not _vitals.get("configured"): return "Practice receivers are unavailable"
	if runtime.get("vitals") != _vitals or runtime.get("player") != player: return "Practice receivers changed"
	if not String(army.get("winner")).is_empty(): return "Round has ended"
	if not _vitals.get("alive"): return "Wait until Rama has returned"
	if runtime.get("suspended") or _vitals.get("suspended"): return "Resume practice before buying"
	if not _near_shop(): return "Return within 14 m of your base on the ground"
	return ""

func _benefit(item: Dictionary) -> Dictionary:
	var state: Dictionary = _vitals.report()
	match item.effect:
		"heal":
			var amount := minf(float(item.amount), maxf(0, float(state.max_health) - float(state.health)))
			return {"possible": amount > 0, "reason": "Health is already full" if amount <= 0 else "", "amount": amount}
		"arrows":
			var ammo: Variant = player.get("ammo")
			if not ammo is int or ammo < 0 or ammo > MAX_ARROWS: return {"possible": false, "reason": "Arrow receiver is unavailable"}
			var amount := mini(int(item.amount), MAX_ARROWS - ammo)
			return {"possible": amount > 0, "reason": "Arrows are already full" if amount <= 0 else "", "amount": amount}
		"shield":
			var expires := float(_vitals.get("shield_until"))
			var now := float(state.elapsed)
			var possible := float(state.shield) < float(item.amount) or expires + .000001 < now + float(item.duration_s)
			return {"possible": possible, "reason": "This ward is already active" if not possible else "", "amount": float(item.amount), "duration_s": float(item.duration_s)}
		"escort":
			var plan: Dictionary = army.plan_temporary_pair(player.global_position, String(item.role))
			return {"possible": plan.get("valid", false), "reason": String(plan.get("reason", "Clear lane space is required")), "plan": plan, "amount": 2}
	return {"possible": false, "reason": "Unknown service"}

func report() -> Dictionary:
	var reason := _base_reason()
	var catalog: Array[Dictionary] = []
	for item: Dictionary in _items:
		var row := item.duplicate(true)
		var disabled := reason
		var benefit: Dictionary = {}
		if disabled.is_empty():
			benefit = _benefit(item)
			if not benefit.possible: disabled = String(benefit.reason)
			elif _wallet() < int(item.cost): disabled = "Not enough gold"
		row.available = disabled.is_empty() and not _in_purchase
		row.disabled_reason = "Finishing purchase" if _in_purchase else disabled
		row.benefit = benefit.get("amount", 0)
		catalog.append(row)
	return {"configured": configured, "epoch": epoch, "wallet": _wallet(), "starting_allowance": int(_rules.get("starting_gold", 0)), "earned": _earned, "spent": _spent, "near_shop": _near_shop(), "eligible": reason.is_empty(), "reason": reason, "catalog": catalog, "accepted_purchases": _accepted, "pending": _in_purchase, "last_reason": _last_reason, "ignored_reward_totals": _ignored_reward_totals, "scope": "Offline match-local services; battle continues. No payment, account or network authority."}

func _finish(receipt: Dictionary, cache := true) -> Dictionary:
	_in_purchase = false
	_pending_cost = 0
	receipt.wallet_after = _wallet()
	_last_reason = String(receipt.reason)
	if cache and configured and int(receipt.epoch) == epoch:
		_highest_nonce = maxi(_highest_nonce, int(receipt.nonce))
		_receipts[int(receipt.nonce)] = receipt.duplicate(true)
		_receipt_order.append(int(receipt.nonce))
		while _receipt_order.size() > int(_rules.receipt_capacity): _receipts.erase(_receipt_order.pop_front())
	# UI observes the completed wallet, while callbacks cannot recursively buy.
	_publishing = true
	changed.emit()
	if receipt.accepted and int(receipt.epoch) == epoch: purchased.emit(receipt.duplicate(true))
	_publishing = false
	return receipt.duplicate(true)

func purchase(item_id: Variant, expected_epoch: Variant, nonce: Variant) -> Dictionary:
	var ticket := {"accepted": false, "duplicate": false, "item_id": item_id if item_id is String else "", "epoch": epoch, "nonce": nonce if nonce is int else 0, "charged": 0, "wallet_before": _wallet(), "wallet_after": _wallet(), "reason": "", "effect": {}}
	if _in_purchase or _publishing:
		ticket.reason = "A purchase is already finishing"
		return ticket
	if not expected_epoch is int or expected_epoch != epoch:
		ticket.reason = "The round changed; refresh the field shop"
		return ticket
	if not nonce is int or nonce < 1 or nonce > MAX_NONCE or not item_id is String:
		ticket.reason = "Invalid purchase ticket"
		return ticket
	if _receipts.has(nonce):
		if _receipts[nonce].item_id != item_id:
			ticket.reason = "Purchase ticket was already used for another service"
			return ticket
		var repeated: Dictionary = _receipts[nonce].duplicate(true)
		repeated.duplicate = true
		return repeated
	if nonce <= _highest_nonce:
		ticket.reason = "Purchase ticket is stale"
		return ticket
	var item: Dictionary = {}
	for candidate in _items:
		if candidate.id == item_id: item = candidate; break
	if item.is_empty():
		ticket.reason = "Unknown field service"
		return _finish(ticket)
	var unavailable := _base_reason()
	if not unavailable.is_empty():
		ticket.reason = unavailable
		return _finish(ticket)
	var benefit := _benefit(item)
	if not benefit.possible:
		ticket.reason = String(benefit.reason)
		return _finish(ticket)
	if _wallet() < int(item.cost):
		ticket.reason = "Not enough gold"
		return _finish(ticket)
	var command_epoch := epoch
	var generation: int = _vitals.generation
	_in_purchase = true
	_pending_cost = int(item.cost)
	var applied := false
	match item.effect:
		"heal":
			var amount: float = _vitals.receive_heal(float(item.amount))
			ticket.effect = {"health_restored": amount}
			applied = amount > 0
		"arrows":
			var before: int = player.ammo
			player.ammo = clampi(before + int(item.amount), 0, MAX_ARROWS)
			ticket.effect = {"arrows_added": player.ammo - before}
			applied = player.ammo > before
			player.changed.emit()
		"shield":
			var before: float = _vitals.shield
			var expires: float = _vitals.shield_until
			var accepted: bool = _vitals.apply_shield(float(item.amount), float(item.duration_s))
			applied = accepted and (_vitals.shield > before or _vitals.shield_until > expires + .000001)
			ticket.effect = {"shield_before": before, "shield_after": _vitals.shield, "expires_at_s": _vitals.shield_until}
		"escort":
			var plan: Dictionary = benefit.plan
			var units: Array = army.spawn_temporary_pair(plan.specifications, float(item.attack_damage), float(item.max_health), float(item.lifetime_s))
			var ids: Array[int] = []
			for unit in units:
				if is_instance_valid(unit): ids.append(unit.unit_id)
			applied = ids.size() == 2
			ticket.effect = {"units_spawned": ids.size(), "unit_ids": ids, "lifetime_s": float(item.lifetime_s)}
	# A synchronous receiver may reset the round/generation from its signal.
	# Never charge its successor or retain that old ticket in the new epoch.
	if epoch != command_epoch or not is_instance_valid(_vitals) or _vitals.generation != generation:
		ticket.epoch = command_epoch
		ticket.reason = "Practice changed during purchase; no gold charged"
		return _finish(ticket, false)
	if not applied:
		ticket.reason = "No service was applied; no gold charged"
		return _finish(ticket)
	_spent += int(item.cost)
	_accepted += 1
	ticket.accepted = true
	ticket.charged = int(item.cost)
	ticket.reason = String(item.title) + " supplied"
	return _finish(ticket)
