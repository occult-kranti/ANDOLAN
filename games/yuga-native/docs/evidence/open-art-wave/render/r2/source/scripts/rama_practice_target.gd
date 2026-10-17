extends Node3D
## Float-health receiver for an existing courtyard bullseye. Only this adapter
## advances the target's state while attached; the old four-second respawn stops.
var army: Node3D
var original: Node3D
var unit_id := 0
var team := "moon"
var radius := .56
var max_health := 90.0
var health := 90.0
var alive := true
var shield := 0.0
var shield_until := 0.0
var hit_time := 0.0
var _original_physics := true
var _original_reset_after := 4.0
var _original_max_health := 3

func configure(owner_army: Node3D, target: Node3D, id: int) -> void:
	army = owner_army
	original = target
	unit_id = id
	_original_physics = target.is_physics_processing()
	_original_reset_after = float(target.reset_after)
	_original_max_health = int(target.max_health)
	target.set_physics_process(false)
	target.reset_after = 0.0
	target.max_health = int(max_health)
	global_position = target.global_position
	reset()

func _available() -> bool:
	return alive and is_instance_valid(original) and is_instance_valid(army) and army.configured and not army.suspended and army.winner.is_empty() and not get_tree().paused

func _valid_number(value: Variant, maximum: float) -> bool:
	return typeof(value) in [TYPE_FLOAT, TYPE_INT] and is_finite(float(value)) and float(value) > 0.0 and float(value) <= maximum

func take_hit(amount: Variant = 1.0) -> bool:
	if not _available() or not _valid_number(amount, 1000.0):return false
	var absorbed := minf(shield, float(amount))
	shield -= absorbed
	health = maxf(0.0, health - (float(amount) - absorbed))
	hit_time = .18
	alive = health > 0.0
	if not alive:
		shield = 0.0
		shield_until = 0.0
	_sync_visual()
	# Existing courtyard hit/clear feedback observes the same accepted outcome.
	original.struck.emit(original, not alive)
	return true

func receive_heal(amount: Variant) -> float:
	if not _available() or not _valid_number(amount, 1000.0):return 0.0
	var before := health
	health = minf(max_health, health + float(amount))
	_update_health_bar()
	return health - before

func apply_shield(amount: Variant, duration: Variant) -> bool:
	if not _available() or not _valid_number(amount, 100.0) or not _valid_number(duration, 12.0):return false
	shield = maxf(shield, float(amount))
	shield_until = maxf(shield_until, float(army.elapsed) + float(duration))
	_update_health_bar()
	return true

func step_statuses(now: float, delta: float) -> void:
	if not is_instance_valid(original):return
	global_position = original.global_position
	if shield > 0.0 and now + 1e-8 >= shield_until:
		shield = 0.0
		shield_until = 0.0
	hit_time = maxf(0.0, hit_time - delta)
	_sync_visual()

func reset() -> void:
	health = max_health
	alive = true
	shield = 0.0
	shield_until = 0.0
	hit_time = 0.0
	_sync_visual()

func _sync_visual() -> void:
	if not is_instance_valid(original):return
	# The legacy target exposes integer hit points. This proxy preserves its alive
	# checks; exact fractional state is authoritative here and exposed as metadata.
	original.health = ceili(health)
	original.set_meta("rama_health", health)
	original.set_meta("rama_shield", shield)
	original.reset_remaining = 0.0
	original.impact_timer = hit_time
	if is_instance_valid(original.body):original.body.visible = alive
	if is_instance_valid(original.collision):original.collision.set_deferred("disabled", not alive)
	if is_instance_valid(original.ring):original.ring.scale = Vector3.ONE * (1.0 + hit_time * .5)
	if original.ring_material:original.ring_material.emission_energy_multiplier = .45 + hit_time * 6.0
	_update_health_bar()

func _update_health_bar() -> void:
	if not is_instance_valid(original) or not is_instance_valid(original.label):return
	original.health = ceili(health)
	original.set_meta("rama_health", health)
	original.set_meta("rama_shield", shield)
	if not alive:
		original.label.text = "%02d  CLEARED · F5 RESET" % int(original.number)
	else:
		original.label.text = "%02d  %.1f / %.0f" % [int(original.number), health, max_health]
		if shield > 0.0:original.label.text += "  +%.0f SHIELD" % shield

func detach() -> void:
	if not is_instance_valid(original):return
	original.max_health = _original_max_health
	original.reset_after = _original_reset_after
	original.remove_meta("rama_health")
	original.remove_meta("rama_shield")
	original.reset_target()
	original.set_physics_process(_original_physics)
	original = null

func report() -> Dictionary:
	return {"unit_id":unit_id, "team":team, "health":health, "max_health":max_health, "alive":alive, "shield":shield, "shield_until":shield_until}
