extends RefCounted
## Current training-attempt receipts. This observer never casts or changes rules.
const IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
const MAX_ACTIVE_CASTS := 12
const MAX_RECEIPTS_PER_CAST := 256
var generation := -1
var last_sequence := -1
var elapsed_s := 0.0
var _high_cast := 0
var _active: Dictionary = {}
var _rows: Dictionary = {}

func reset(epoch: int) -> void:
	if epoch < generation: return
	generation = epoch
	last_sequence = -1
	elapsed_s = 0
	_high_cast = 0
	_active.clear()
	_rows.clear()
	for id in IDS:
		_rows[id] = {"ability_id":id,"casts_started":0,"hits":0,"damage_dealt":0.0,"healing_applied":0.0,"shield_granted":0.0,"step_distance_m":0.0,"defeats":0}

func _number(value: Variant, maximum := 100000000.0) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and float(value)>=0 and float(value)<=maximum

func _valid_receipt(receipt: Dictionary, kind: String) -> bool:
	if receipt.get("kind") != kind: return false
	for field in ["health_before","health_after","shield_before","shield_after"]:
		if not _number(receipt.get(field),1000): return false
	if kind == "damage":
		var delta := float(receipt.health_before)+float(receipt.shield_before)-float(receipt.health_after)-float(receipt.shield_after)
		return receipt.get("unit_id") is int and receipt.unit_id>0 and _number(receipt.get("damage_applied"),1000) and delta>0 and absf(delta-float(receipt.damage_applied))<.001
	return receipt.get("receiver_kind") == "hero" and receipt.get("unit_id") == 0 and _number(receipt.get("healing_applied"),1000) and absf(float(receipt.health_after)-float(receipt.health_before)-float(receipt.healing_applied))<.001

func observe(event: Dictionary) -> bool:
	if event.get("hero_id") != "rama" or not event.get("generation") is int or not event.get("event_seq") is int: return false
	var epoch: int = event.generation
	var sequence: int = event.event_seq
	if epoch<generation or sequence<0: return false
	var raw_kind: Variant = event.get("kind","")
	if not raw_kind is String: return false
	var kind: String = raw_kind
	if kind == "reset":
		if epoch == generation and sequence<=last_sequence: return false
		reset(epoch)
		last_sequence = sequence
		return true
	if epoch!=generation or sequence<=last_sequence or not _number(event.get("time_s")) or float(event.time_s)+.000001<elapsed_s: return false
	var raw_id: Variant = event.get("ability_id","")
	if not raw_id is String: return false
	var id: String = raw_id
	var cast: Variant = event.get("cast_id")
	if id not in IDS or not cast is int or cast<1: return false
	if kind not in ["begin","release","impact","tick","recovery","end","cancel"]: return false
	if kind == "begin":
		if cast<=_high_cast or _active.size()>=MAX_ACTIVE_CASTS: return false
		_active[cast] = {"ability_id":id,"seen":{},"moved":false}
		_high_cast = cast
		_rows[id].casts_started += 1
	elif not _active.has(cast) or _active[cast].ability_id != id:
		return false
	last_sequence = sequence
	elapsed_s = maxf(elapsed_s,float(event.time_s))
	var changed := kind == "begin"
	if kind == "impact" and id == "measured_step" and event.get("reason") == "movement_accepted" and not _active[cast].moved:
		var origin: Variant = event.get("origin")
		var destination: Variant = event.get("contact_position")
		if origin is Vector3 and destination is Vector3 and origin.is_finite() and destination.is_finite():
			var distance := Vector2(origin.x-destination.x,origin.z-destination.z).length()
			if distance<=4.5001:
				_rows[id].step_distance_m += distance
				_active[cast].moved = true
				changed = distance>0
	var receipts: Variant = event.get("receipts",[])
	if receipts is Array and receipts.size()<=80:
		for value in receipts:
			if not value is Dictionary: continue
			var receipt: Dictionary = value
			if _active[cast].seen.size()>=MAX_RECEIPTS_PER_CAST: break
			if kind == "impact" and id in ["kodanda","piercing_dawn","dawn_volley"] and event.get("reason") == "unit" and _valid_receipt(receipt,"damage"):
				var index: Variant = event.get("projectile_index")
				if not index is int or index<0 or index>2: continue
				var signature := "%d:%d" % [index,receipt.unit_id]
				if _active[cast].seen.has(signature): continue
				_active[cast].seen[signature] = true
				_rows[id].hits += 1
				_rows[id].damage_dealt += float(receipt.damage_applied)
				if float(receipt.health_before)>0 and float(receipt.health_after)<=0: _rows[id].defeats += 1
				changed = true
			elif kind in ["impact","tick"] and id == "guardian_circle" and _valid_receipt(receipt,"guardian"):
				# Per-cast tick time identifies the effective hero receiver receipt;
				# repeated higher-sequence copies cannot inflate the same tick.
				var signature := "hero:%s:%.6f" % [kind,float(event.time_s)]
				if _active[cast].seen.has(signature): continue
				_active[cast].seen[signature] = true
				_rows[id].healing_applied += float(receipt.healing_applied)
				_rows[id].shield_granted += maxf(0,float(receipt.shield_after)-float(receipt.shield_before))
				changed = true
	if kind in ["end","cancel"]: _active.erase(cast)
	return changed

func report() -> Dictionary:
	var result := {"configured":generation>=0,"scope":"courtyard","generation":generation,"last_sequence":last_sequence,"elapsed_s":elapsed_s,"casts_started":0,"hits":0,"damage_dealt":0.0,"healing_applied":0.0,"shield_granted":0.0,"step_distance_m":0.0,"defeats":0,"by_ability":[],"active_observed_casts":_active.size()}
	for id in IDS:
		if not _rows.has(id): continue
		var row: Dictionary = _rows[id]
		result.by_ability.append(row.duplicate(true))
		for field in ["casts_started","hits","damage_dealt","healing_applied","shield_granted","step_distance_m","defeats"]: result[field] += row[field]
	return result
