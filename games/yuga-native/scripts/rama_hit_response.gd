extends RefCounted
## Pure presentation classification. Never applies damage or grants rewards.
## Older minimal damage receipts remain generic contacts; only complete,
## consistent receiver snapshots may claim shield absorption or defeat.
const STATES := [&"contact", &"health", &"shield", &"defeat"]
const FIELDS := ["health_before", "health_after", "shield_before", "shield_after"]

static func _number(value: Variant) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and float(value) >= 0.0 and float(value) <= 10000.0

static func classify(receipt: Variant) -> StringName:
	if not receipt is Dictionary or receipt.get("kind") != "damage" or not _number(receipt.get("damage_applied")) or float(receipt.damage_applied) <= 0.0:
		return &""
	var present := 0
	for key in FIELDS:
		if receipt.has(key): present += 1
	# Generic acknowledgement remains compatible with the earlier consumer
	# contract, without inferring a health/shield/defeat state from missing data.
	if present == 0: return &"contact"
	if present != FIELDS.size(): return &""
	for key in FIELDS:
		if not _number(receipt[key]): return &""
	var health_loss := float(receipt.health_before) - float(receipt.health_after)
	var shield_loss := float(receipt.shield_before) - float(receipt.shield_after)
	if health_loss < 0.0 or shield_loss < 0.0 or absf(health_loss + shield_loss - float(receipt.damage_applied)) > .00001:
		return &""
	if float(receipt.health_before) > 0.0 and float(receipt.health_after) <= 0.0: return &"defeat"
	if health_loss > 0.0: return &"health"
	if shield_loss > 0.0: return &"shield"
	return &""

static func rank(kind: StringName) -> int:
	match kind:
		&"defeat": return 3
		&"health", &"contact": return 2
		&"shield": return 1
	return 0
