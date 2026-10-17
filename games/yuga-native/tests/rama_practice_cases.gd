extends SceneTree
## Same actual kit, original visible bullseye, and fractional damage receiver.
const Practice = preload("res://scripts/rama_practice_army.gd")
const Target = preload("res://scripts/target.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
var checks: Array = []
var strikes: Array = []
var events: Array = []
var army
var kit
var target

func _initialize() -> void:call_deferred("run")

func check(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label, "passed":passed, "evidence":evidence})
	if not passed:push_error("PRACTICE FAILED: " + label)

func advance(seconds: float) -> void:
	var remaining := seconds
	while remaining > .000001:
		var delta := minf(.05, remaining)
		army.step_simulation(delta)
		remaining -= delta

func run() -> void:
	target = Target.new()
	root.add_child(target)
	target.position = Vector3(0,0,5)
	target.struck.connect(func(_target, defeated):strikes.append(defeated))
	army = Practice.new()
	root.add_child(army)
	army.set_physics_process(false)
	check("original_target_configures", army.configure([target]) and army.units.size() == 1)
	var receiver = army.units[0]
	check("adapter_owns_target_clock", not target.is_physics_processing() and target.reset_after == 0 and receiver.health == 90)
	check("fractional_damage_is_real", receiver.take_hit(12.5) and receiver.health == 77.5 and target.get_meta("rama_health") == 77.5 and strikes == [false])
	check("invalid_damage_has_no_hit_callback", not receiver.take_hit(NAN) and not receiver.take_hit(-1) and strikes.size() == 1)
	check("shield_absorbs_before_health", receiver.apply_shield(20.0, .1) and receiver.take_hit(22.5) and receiver.shield == 0 and receiver.health == 75 and strikes.size() == 2)
	check("heal_caps_at_max", receiver.receive_heal(100) == 15 and receiver.health == 90 and target.get_meta("rama_health") == 90)
	receiver.apply_shield(10.0, .1)
	army.set_suspended(true)
	check("suspension_freezes_damage_and_time", not army.step_simulation(.05) and army.elapsed == 0 and not receiver.take_hit(1))
	army.set_suspended(false)
	advance(.1)
	check("shield_expiry_uses_army_clock", receiver.shield == 0 and receiver.shield_until == 0)
	paused = true
	check("tree_pause_freezes_manual_steps", not army.step_simulation(.05))
	paused = false
	check("large_or_nonfinite_steps_rejected", not army.step_simulation(.051) and not army.step_simulation(NAN))
	army.reset()
	strikes.clear()
	kit = Kit.new()
	root.add_child(kit)
	kit.ability_event.connect(func(event):events.append(event.duplicate(true)))
	check("actual_rama_kit_configures", kit.configure(army))
	check("actual_primary_accepted", kit.request_ability("kodanda", Vector3.ZERO, Vector3(0,0,1), Vector3(0,0,5)).accepted)
	advance(.4)
	check("primary_damage_reaches_bullseye_once", receiver.health == 62 and target.get_meta("rama_health") == 62 and strikes == [false])
	check("actual_damage_receipt_is_matching", events.any(func(event):return event.get("receipts",[]).any(func(receipt):return receipt.get("damage_applied",0) == 28 and receipt.unit_id == receiver.unit_id)))
	army.reset("fixture_reset")
	strikes.clear();events.clear()
	army.boxes.append({"position":Vector3(0,2,3),"size":Vector3(10,4,.05)})
	check("thin_cover_geometry_matches_lanes", not army.line_clear(Vector3.ZERO, Vector3(0,0,5)) and army.segment_wall_fraction(Vector3.ZERO, Vector3(0,0,5)) < .61)
	kit.request_ability("piercing_dawn", Vector3.ZERO, Vector3(0,0,1), Vector3(0,0,5))
	advance(1.5)
	check("real_cover_prevents_bullseye_damage", receiver.health == 90 and strikes.is_empty())
	army.boxes.pop_back()
	var actual_wall := StaticBody3D.new()
	actual_wall.collision_layer = 1
	var wall_shape := CollisionShape3D.new()
	var box_shape := BoxShape3D.new()
	box_shape.size = Vector3(8, 3, .1)
	wall_shape.shape = box_shape
	actual_wall.add_child(wall_shape)
	root.add_child(actual_wall)
	actual_wall.position = Vector3(0,1.5,3)
	await physics_frame
	await physics_frame
	check("actual_courtyard_layer_one_wall_occludes", not army.line_clear(Vector3.ZERO, Vector3(0,0,5)) and army.line_clear(Vector3(8,0,0), Vector3(8,0,5)))
	actual_wall.free()
	army.reset("fixture_reset")
	receiver.take_hit(100)
	check("defeat_syncs_visuals_and_callback", not receiver.alive and not target.body.visible and target.health == 0 and strikes == [true] and target.label.text.contains("F5 RESET"))
	advance(5.0)
	check("legacy_four_second_respawn_disabled", not receiver.alive and receiver.health == 0 and not target.body.visible and target.reset_remaining == 0)
	check("dead_target_does_not_emit_extra_hits", not receiver.take_hit(10) and strikes.size() == 1)
	army.reset("manual_reset")
	check("manual_reset_restores_target_and_kit", receiver.alive and receiver.health == 90 and target.body.visible and army.elapsed == 0 and kit.report().casts.is_empty() and kit.report().cooldowns.kodanda == 0)
	check("invalid_reconfigure_preserves_receivers", not army.configure([target,target]) and army.configured and army.units.size() == 1)
	army.clear()
	check("clear_restores_original_contract", not army.configured and army.units.is_empty() and target.max_health == 3 and target.health == 3 and target.is_physics_processing() and target.reset_after == 4.0 and not target.has_meta("rama_health"))
	var hashes := {}
	for path in ["res://scripts/rama_practice_army.gd", "res://scripts/rama_practice_target.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/target.gd"]:hashes[path] = FileAccess.get_sha256(path)
	var passed := checks.all(func(entry):return entry.passed)
	var report := {"suite":"rama_practice_cases", "passed":passed, "checks":checks, "source_sha256":hashes, "scope":"Headless courtyard adapter, actual kit, target state/callback/visual properties; no rendered visual or player-experience claim."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path := argument.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			var file := FileAccess.open(path,FileAccess.WRITE)
			file.store_string(JSON.stringify(report,"  "));file.close()
	print("Rama practice checks: %d/%d" % [checks.filter(func(entry):return entry.passed).size(),checks.size()])
	kit.free();army.free();target.free()
	quit(0 if passed else 1)
