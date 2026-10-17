extends Node
## One deliberate Q/X edge near real recovery; never a combat authority.
## The caller supplies current eligibility and the existing immediate request.
signal intent_changed
signal dispatch_finished(result: Dictionary)

const WINDOW_S := .12
const ABILITIES := ["piercing_dawn", "dawn_volley"]
var _kit: Node
var _request := Callable()
var _eligible := Callable()
var _action: Dictionary = {}
var _pending: Dictionary = {}
var _last_edge := 0
var _serial := 0
var _dispatching := false
var _handling_input := false
var _sampling_state := false
var _invalidating := false
var _configured := false
var queued_count := 0
var dispatched_count := 0
var cleared_count := 0
var rejected_count := 0
var last_reason := "No pending ability"

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE

func configure(kit_value: Node, request: Callable, eligibility: Callable) -> bool:
	if _configured or not is_instance_valid(kit_value) or not kit_value.has_signal("ability_event") or not kit_value.has_method("report") or not request.is_valid() or not eligibility.is_valid(): return false
	_kit = kit_value
	_request = request
	_eligible = eligibility
	_kit.ability_event.connect(_on_event)
	_configured = true
	return true

func _notification(what: int) -> void:
	if what == NOTIFICATION_PAUSED: cancel_pending("Practice paused")

func _exit_tree() -> void:
	cancel_pending("Scene changed")
	if is_instance_valid(_kit) and _kit.ability_event.is_connected(_on_event): _kit.ability_event.disconnect(_on_event)
	_configured = false

func cancel_pending(reason := "Practice changed") -> void:
	_serial += 1
	if not _pending.is_empty(): cleared_count += 1
	_pending.clear()
	last_reason = reason
	if _invalidating: return
	_invalidating = true
	intent_changed.emit()
	_invalidating = false

func _reject(reason: String) -> Dictionary:
	rejected_count += 1
	last_reason = reason
	return {"accepted":false, "queued":false, "reason":reason}

func _snapshot() -> Dictionary:
	if not _configured or not is_instance_valid(_kit): return {}
	var value = _kit.report()
	if not value is Dictionary or not value.get("configured", false) or not value.get("generation") is int: return {}
	var clock = value.get("elapsed")
	if not typeof(clock) in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(clock)) or float(clock) < 0: return {}
	return value

func _eligibility() -> Dictionary:
	if not is_inside_tree() or get_tree().paused: return {"eligible":false, "reason":"Practice paused"}
	_sampling_state = true
	var value = _eligible.call()
	_sampling_state = false
	if not value is Dictionary or value.get("eligible") != true: return {"eligible":false, "reason":String(value.get("reason", "Return to grounded practice")) if value is Dictionary else "Invalid input eligibility"}
	return value

func push_input(ability_id: String, edge_token: int, echoed := false) -> Dictionary:
	if _handling_input or _sampling_state or _invalidating or _dispatching: return _reject("An ability request is already being handled")
	_handling_input = true
	var result := _push_input(ability_id, edge_token, echoed)
	_handling_input = false
	return result

func _push_input(ability_id: String, edge_token: int, echoed: bool) -> Dictionary:
	# The player owns the monotonic edge counter. Holding or keyboard autorepeat
	# must never refresh a pending intent's timestamp.
	if ability_id not in ABILITIES: return _reject("This ability uses immediate input")
	if echoed or edge_token <= 0 or edge_token <= _last_edge: return _reject("A fresh deliberate press is required")
	_last_edge = edge_token
	if _dispatching: return _reject("An ability request is already being handled")
	var snapshot := _snapshot()
	if snapshot.is_empty() or snapshot.get("suspended", true): return _reject("Practice is unavailable")
	var serial := _serial
	var state := _eligibility()
	if not state.eligible: return _reject(state.reason)
	var after := _snapshot()
	if after.is_empty() or _serial != serial or after.generation != snapshot.generation: return _reject("Practice changed during input")
	snapshot = after
	var cooldown = snapshot.get("cooldowns", {}).get(ability_id, INF)
	if not typeof(cooldown) in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(cooldown)) or float(cooldown) > 1e-8: return _reject("Ability is cooling down")
	if not snapshot.get("action_locked", true):
		# A newer intentional press supersedes an older queued action even when
		# the immediate path becomes available before its recovery callback.
		_pending.clear()
		return _attempt(ability_id, int(snapshot.generation), serial, false)
	if _action.is_empty() or _action.generation != snapshot.generation or _action.cast_id != snapshot.get("active_cast_id", 0): return _reject("Finish the current draw or recovery")
	var active: Dictionary = {}
	for cast in snapshot.get("casts", []):
		if cast is Dictionary and cast.get("cast_id") == _action.cast_id: active = cast; break
	if active.get("phase", "") != "recovery" or not active.get("released", false): return _reject("Finish the current draw")
	var remaining: float = float(_action.recovery_at) - float(snapshot.elapsed)
	if remaining <= 1e-8 or remaining > WINDOW_S + 1e-8: return _reject("Finish the current recovery")
	_pending = {"ability_id":ability_id, "edge_token":edge_token, "generation":int(snapshot.generation), "cast_id":int(_action.cast_id), "queued_at":float(snapshot.elapsed), "expires_at":float(snapshot.elapsed) + WINDOW_S, "serial":serial}
	queued_count += 1
	last_reason = ability_id.replace("_", " ").capitalize() + " · queued after recovery"
	intent_changed.emit()
	return {"accepted":false, "queued":true, "reason":last_reason, "generation":snapshot.generation, "edge_token":edge_token}

func _attempt(ability_id: String, expected_generation: int, expected_serial: int, from_buffer: bool) -> Dictionary:
	# Consume before invoking the runtime: begin listeners can reset practice or
	# reenter input. Only the normal request is allowed to emit a real begin.
	_pending.clear()
	_dispatching = true
	var response = _request.call(ability_id)
	var snapshot := _snapshot()
	var result: Dictionary
	if not response is Dictionary:
		result = _reject("Ability request returned an invalid result")
	elif snapshot.is_empty() or snapshot.generation != expected_generation or _serial != expected_serial:
		result = _reject("Practice changed during the request")
	else:
		result = response.duplicate(true)
		result["queued"] = false
		result["from_buffer"] = from_buffer
		if from_buffer: dispatched_count += 1
		last_reason = String(result.get("reason", "Ability request finished"))
	dispatch_finished.emit(result.duplicate(true))
	_dispatching = false
	return result

func _on_event(event: Dictionary) -> void:
	var snapshot := _snapshot()
	if snapshot.is_empty(): cancel_pending("Combat is unavailable"); _action.clear(); return
	var kind := String(event.get("kind", ""))
	if event.get("generation", -1) != snapshot.generation: return
	if kind == "reset":
		cancel_pending("Combat reset"); _action.clear(); return
	if not _pending.is_empty() and (_pending.generation != snapshot.generation or float(snapshot.elapsed) > float(_pending.expires_at) + 1e-8): cancel_pending("Queued ability expired")
	if kind == "cancel":
		cancel_pending("Action cancelled")
		if _action.get("cast_id", 0) == event.get("cast_id", -1): _action.clear()
		return
	if kind == "begin":
		if not _pending.is_empty(): cancel_pending("A newer action began")
		var timing = event.get("timing", {})
		if not timing is Dictionary: return
		var windup = timing.get("windup_s", NAN)
		var recovery = timing.get("recovery_s", NAN)
		var started = event.get("time_s", NAN)
		for value in [windup, recovery, started]:
			if not typeof(value) in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(value)) or float(value) < 0: return
		_action = {"cast_id":int(event.get("cast_id", 0)), "generation":int(snapshot.generation), "recovery_at":float(started) + float(windup) + float(recovery)}
		return
	if kind != "recovery" or _action.get("cast_id", 0) != event.get("cast_id", -1): return
	_action.clear()
	if _pending.is_empty(): return
	var intent := _pending.duplicate(true)
	_pending.clear()
	if snapshot.get("suspended", true) or snapshot.get("action_locked", true) or intent.generation != snapshot.generation or intent.cast_id != event.get("cast_id", -1) or int(intent.serial) != _serial or float(snapshot.elapsed) > float(intent.expires_at) + 1e-8: cancel_pending("Practice changed before recovery"); return
	var serial := _serial
	var state := _eligibility()
	var after := _snapshot()
	if not state.eligible or after.is_empty() or _serial != serial or after.generation != intent.generation or after.get("suspended", true) or after.get("action_locked", true): cancel_pending(String(state.get("reason", "Practice changed before recovery"))); return
	var cooldown = after.get("cooldowns", {}).get(intent.ability_id, INF)
	if not typeof(cooldown) in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(cooldown)) or float(cooldown) > 1e-8: cancel_pending("Ability is cooling down"); return
	_attempt(String(intent.ability_id), int(intent.generation), serial, true)

func report() -> Dictionary:
	return {"configured":_configured, "window_s":WINDOW_S, "scope":"One deliberate Q/X edge near accepted recovery; no gameplay authority", "pending":_pending.duplicate(true), "last_edge":_last_edge, "dispatching":_dispatching, "queued_count":queued_count, "dispatched_count":dispatched_count, "cleared_count":cleared_count, "rejected_count":rejected_count, "last_reason":last_reason}
