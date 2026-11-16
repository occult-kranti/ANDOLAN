extends RefCounted
## Read-only learning progress from the real kit's ordered combat receipts.
## This observer never casts, grants damage, changes cooldowns or awards currency.
const Bindings = preload("res://scripts/input_bindings.gd")
const IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
const ACTIONS := ["fire", "pulse", "dash", "guardian_circle", "ultimate"]
const HINTS := ["Hit a target", "Pierce a target", "Step into open ground", "Stand inside your field", "Hit with Dawn Volley"]
var generation := -1
var last_sequence := -1
var completed: Dictionary = {}

func reset(epoch: int) -> void:
	if epoch < generation: return
	generation = epoch
	last_sequence = -1
	completed.clear()

func observe(event: Dictionary) -> bool:
	if event.get("hero_id", "") != "rama" or not event.get("generation") is int or not event.get("event_seq") is int: return false
	var epoch: int = event.generation
	var sequence: int = event.event_seq
	if epoch < generation or sequence < 0: return false
	if event.get("kind") == "reset":
		if epoch == generation and sequence <= last_sequence: return false
		reset(epoch)
		last_sequence = sequence
		return true
	if epoch != generation or sequence <= last_sequence: return false
	last_sequence = sequence
	var id := String(event.get("ability_id", ""))
	if id not in IDS or completed.has(id): return false
	if event.get("kind") not in ["impact", "tick"]: return false
	var succeeded := false
	if id == "measured_step" and event.get("kind") == "impact" and event.get("reason") == "movement_accepted":
		var origin = event.get("origin")
		var destination = event.get("contact_position")
		# An obstructed/no-distance request does not teach a usable escape.
		succeeded = origin is Vector3 and destination is Vector3 and origin.is_finite() and destination.is_finite() and origin.distance_to(destination) >= .5
	else:
		for receipt in event.get("receipts", []):
			if not receipt is Dictionary: continue
			if id == "guardian_circle":
				succeeded = receipt.get("receiver_kind") == "hero" and (float(receipt.get("shield_after", 0)) > float(receipt.get("shield_before", 0)) or float(receipt.get("healing_applied", 0)) > 0)
			else:
				succeeded = event.get("kind") == "impact" and event.get("reason") == "unit" and float(receipt.get("damage_applied", 0)) > 0
			if succeeded: break
	if succeeded: completed[id] = true
	return succeeded

func report() -> Dictionary:
	var next := ""
	var hint := "Free practice · F5 starts again"
	for index in IDS.size():
		if not completed.has(IDS[index]):
			next = IDS[index]
			hint = "%s · %s" % [Bindings.label(ACTIONS[index]), HINTS[index]]
			break
	return {"completed":completed.size(), "total":IDS.size(), "complete":completed.size() == IDS.size(), "next_ability":next,
		"title":"Kit practiced · 5/5" if next.is_empty() else "Hero practice · %d/5" % completed.size(), "hint":hint,
		"generation":generation, "last_sequence":last_sequence, "abilities":completed.duplicate()}
