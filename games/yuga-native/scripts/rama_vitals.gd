extends Node
## Explicit local hero receiver. Army time controls shield expiry/respawn readiness.
## Only callers wired by the world can deal damage; this is not network authority.
signal changed
signal damaged(receipt: Dictionary)
signal defeated(receipt: Dictionary)
signal respawn_ready
signal respawned
const MAX_HEALTH := 300.0
const MAX_SHIELD := 100.0
const RESPAWN_DELAY := 3.0
var health := MAX_HEALTH
var shield := 0.0
var shield_until := 0.0
var alive := true
var elapsed := 0.0
var generation := 0
var suspended := false
var configured := false
var army: Node3D
var damage_receipts := 0
var deaths := 0
var rejected := 0
var _dead_at := 0.0
var _ready_announced := false
var _sources: Dictionary = {}
var _history: Array = []
var _army_elapsed := 0.0

func _ready() -> void:process_mode = Node.PROCESS_MODE_PAUSABLE
func configure(army_value: Node3D) -> bool:
	if not is_instance_valid(army_value) or not army_value.get("configured") or not army_value.has_signal("simulation_stepped"):return false
	_disconnect()
	army = army_value
	army.simulation_stepped.connect(_on_step)
	army.simulation_reset.connect(_on_reset)
	configured = true
	reset()
	return true
func _disconnect() -> void:
	if not is_instance_valid(army):return
	if army.simulation_stepped.is_connected(_on_step):army.simulation_stepped.disconnect(_on_step)
	if army.simulation_reset.is_connected(_on_reset):army.simulation_reset.disconnect(_on_reset)
func _exit_tree() -> void:_disconnect()
func _valid_number(value: Variant, maximum: float) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and float(value)>0 and float(value)<=maximum
func _sample_army_clock() -> float:
	if is_instance_valid(army):
		var value = army.get("elapsed")
		if typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)):return float(value)
	return _army_elapsed
func _clock_now() -> float:
	if not configured or suspended:return elapsed
	# Earlier listeners can deliver a receipt before this receiver consumes the
	# current step. Only that single pending tick belongs to this local clock.
	var pending:=_sample_army_clock()-_army_elapsed
	return elapsed+(pending if pending>=0 and pending<=.050001 else 0.0)
func set_suspended(value: bool) -> void:
	suspended=value
	_army_elapsed=_sample_army_clock()
func reset() -> void:
	generation += 1
	health=MAX_HEALTH;shield=0;shield_until=0;alive=true;elapsed=0
	_army_elapsed=_sample_army_clock()
	_dead_at=0;_ready_announced=false;_sources.clear();_history.clear()
	changed.emit()
func _on_reset(_reason: String) -> void:reset()
func _available() -> bool:
	return configured and is_instance_valid(army) and army.winner.is_empty() and not suspended and is_inside_tree() and not get_tree().paused
func receive_damage(amount: Variant, source_id := "practice", expected_generation := -1, sequence := -1) -> Dictionary:
	if not _available() or not alive or not _valid_number(amount,1000) or source_id.is_empty() or source_id.length()>80 or (expected_generation>=0 and expected_generation!=generation) or (sequence>=0 and sequence<=int(_sources.get(source_id,-1))):
		rejected+=1
		return {"accepted":false,"generation":generation}
	# Explicit receipt sequence prevents a repeated hazard event causing a second hit.
	if sequence>=0:
		if _sources.size()>=64 and not _sources.has(source_id):_sources.erase(_sources.keys()[0])
		_sources[source_id]=sequence
	var now:=_clock_now()
	if shield>0 and now+1e-8>=shield_until:shield=0;shield_until=0
	var before:=health
	var before_shield:=shield
	var absorbed:=minf(shield,float(amount))
	shield-=absorbed
	health=maxf(0,health-float(amount)+absorbed)
	damage_receipts+=1
	var receipt:={"accepted":true,"generation":generation,"source_id":source_id,"sequence":sequence,"health_before":before,"health_after":health,"shield_before":before_shield,"shield_after":shield,"damage_applied":before+before_shield-health-shield,"time_s":now}
	_history.append(receipt.duplicate(true))
	if _history.size()>48:_history.pop_front()
	if health<=0:
		alive=false;shield=0;shield_until=0;_dead_at=now;_ready_announced=false;deaths+=1
	damaged.emit(receipt)
	# An observer may reset during damage; never emit a stale defeat afterward.
	if not alive and generation==int(receipt.generation):defeated.emit(receipt)
	changed.emit()
	return receipt
func receive_heal(amount: Variant) -> float:
	if not _available() or not alive or not _valid_number(amount,1000):return 0.0
	var before:=health
	health=minf(MAX_HEALTH,health+float(amount))
	var applied:=health-before
	changed.emit()
	return applied
func apply_shield(amount: Variant, duration: Variant) -> bool:
	if not _available() or not alive or not _valid_number(amount,MAX_SHIELD) or not _valid_number(duration,12):return false
	var now:=_clock_now()
	if shield>0 and now+1e-8>=shield_until:shield=0;shield_until=0
	shield=maxf(shield,float(amount));shield_until=maxf(shield_until,now+float(duration));changed.emit()
	return true
func respawn() -> bool:
	if not _available() or alive or _clock_now()-_dead_at+1e-8<RESPAWN_DELAY:return false
	generation+=1;health=MAX_HEALTH;shield=0;shield_until=0;alive=true;_ready_announced=false;_sources.clear()
	respawned.emit();changed.emit()
	return true
func _on_step(delta: float) -> void:
	if not _available() or not is_finite(delta) or delta<=0 or delta>.050001:return
	_army_elapsed=_sample_army_clock()
	elapsed+=delta
	if shield>0 and elapsed+1e-8>=shield_until:shield=0;shield_until=0;changed.emit()
	if not alive and not _ready_announced and elapsed-_dead_at+1e-8>=RESPAWN_DELAY:
		_ready_announced=true
		respawn_ready.emit()
func report() -> Dictionary:
	return {"configured":configured,"health":health,"max_health":MAX_HEALTH,"shield":shield,"max_shield":MAX_SHIELD,"alive":alive,"generation":generation,"elapsed":elapsed,"respawn_remaining":maxf(0,RESPAWN_DELAY-(_clock_now()-_dead_at)) if not alive else 0.0,"damage_receipts":damage_receipts,"deaths":deaths,"rejected":rejected,"history_size":_history.size(),"network_enabled":false,"scope":"Explicitly wired offline practice damage receiver"}
