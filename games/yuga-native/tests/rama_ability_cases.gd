extends SceneTree
## Actual lane receivers, independent hero vitals, and bounded event-only presentation.
const Army = preload("res://scripts/lane_army.gd")
const Unit = preload("res://scripts/lane_minion.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
var army
var kit
var fx
var vitals
var events: Array=[]
var checks: Array=[]
var origin:=Vector3.ZERO
var step_calls:=0
var cancel_spawn:=false
var callback_accepted:=false
var sample_reset:=false
var sampler_calls:=0
var heal_reset:=false
func _initialize() -> void:call_deferred("run")
func check(label: String, passed: bool, evidence: Dictionary={}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	if not passed:push_error("RAMA FAILED: "+label)
func advance(seconds: float, presentation := true) -> void:
	var remaining:=seconds
	while remaining>1e-8:
		var dt:=minf(.05,remaining)
		army.step_simulation(dt)
		if presentation:fx.step(dt)
		remaining-=dt
func fresh() -> void:
	army.reset()
	for unit in army.units.duplicate():army.units.erase(unit);unit.free()
	army._rebuild_buckets()
	events.clear();origin=Vector3.ZERO;step_calls=0
	kit.set_suspended(false);vitals.set_suspended(false);fx.set_suspended(false)
func unit_at(team: String, point: Vector3, health:=150.0):
	var unit=Unit.new()
	unit.setup(army,army.next_id,team,"commander",1)
	army.next_id+=1;unit.render_art=false;unit.position=point
	unit.attack_time=1000;unit.attack_cooldown=1000;unit.health=health
	unit.defeated.connect(army._on_defeated)
	army.add_child(unit);army.units.append(unit)
	return unit
func cast(id: String,target:=Vector3(0,0,4),options: Dictionary={}) -> Dictionary:
	return kit.request_ability(id,origin,Vector3(0,0,1),target,options)
func release_events() -> Array:return events.filter(func(e):return e.kind=="release")
func reentrant_cancel(event: Dictionary) -> void:
	if event.kind=="cancel" and cancel_spawn:
		cancel_spawn=false
		callback_accepted=cast("piercing_dawn").accepted
func resetting_sampler() -> Vector3:
	sampler_calls+=1
	if sample_reset and sampler_calls==2:
		sample_reset=false
		kit.reset("attachment_sampler_reset")
	return origin
func reset_during_heal() -> void:
	if heal_reset:
		heal_reset=false
		vitals.reset()
func run() -> void:
	army=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	check("real_army_configures",army.configure(manifest,null))
	kit=Kit.new();root.add_child(kit)
	fx=Effects.new();root.add_child(fx);fx.set_process(false)
	vitals=Vitals.new();root.add_child(vitals)
	kit.ability_event.connect(func(event):events.append(event.duplicate(true));fx.consume_event(event))
	check("kit_and_vitals_configure",kit.configure(army) and vitals.configure(army))
	kit.set_origin_sampler(func():return origin)
	kit.set_movement_receiver(func(_start,destination,_duration):step_calls+=1;return {"accepted":true,"destination":destination})
	kit.set_hero_receiver(vitals,func():return origin)
	fresh()
	var enemy=unit_at("moon",Vector3(0,0,5))
	check("primary_accepted",cast("kodanda").accepted)
	fx.step(.5)
	check("presentation_cannot_release_damage",enemy.health==150 and release_events().is_empty() and fx.report().live_arrows==0)
	advance(.15)
	check("draw_has_no_early_damage",enemy.health==150 and release_events().is_empty())
	advance(.05)
	check("primary_releases_once_first_tick_after_point18",release_events().size()==1 and absf(release_events()[0].age_s-.20)<.0001)
	advance(.20)
	check("primary_real_damage_and_action_recovery",enemy.health==122 and not kit.report().action_locked)
	check("primary_recovers_at_point40",cast("kodanda").accepted)
	advance(1)
	check("primary_event_consumer_accepts_real_schema",fx.report().counts.invalid==0)
	fresh()
	enemy=unit_at("moon",Vector3(0,0,8))
	cast("kodanda");origin=Vector3(1,0,0);advance(.2)
	check("moving_draw_samples_release_origin_keeps_aim",release_events().size()==1 and release_events()[0].origin==origin and release_events()[0].forward==Vector3(0,0,1))
	fresh()
	kit.set_muzzle_sampler(func():return origin+Vector3(.2,1.65,.4))
	cast("kodanda");advance(.2)
	check("actual_muzzle_sample_is_locked_at_release",release_events().size()==1 and release_events()[0].geometry.projectiles[0].origin==origin+Vector3(.2,1.65,.4))
	check("muzzle_change_is_accepted_by_presentation",fx.report().counts.invalid==0 and fx.report().casts[0].released)
	fresh();kit.set_muzzle_sampler(func():return Vector3(INF,0,0))
	cast("kodanda");advance(.4)
	check("invalid_muzzle_cancels_before_release",release_events().is_empty() and events.any(func(e):return e.kind=="cancel" and e.get("reason")=="muzzle_invalid"))
	kit.set_muzzle_sampler(Callable())
	fresh()
	var enemies: Array=[]
	for z in [3,5,7,9,11,13,15]:enemies.append(unit_at("moon",Vector3(0,0,z)))
	cast("piercing_dawn");advance(1.6)
	var wounded:=enemies.filter(func(e):return e.health==80)
	check("piercing_arrow_hits_six_unique_targets_once",wounded.size()==6 and enemies[-1].health==150,{"wounded":wounded.size()})
	check("piercing_independent_cooldown",not cast("piercing_dawn").accepted and cast("kodanda").accepted)
	fresh()
	army.boxes.append({"position":Vector3(0,2,3),"size":Vector3(10,4,.1)})
	enemy=unit_at("moon",Vector3(0,0,5));cast("piercing_dawn");advance(1.6)
	check("thin_solid_cover_stops_piercing",enemy.health==150 and events.any(func(e):return e.kind=="impact" and e.get("reason")=="wall"))
	army.boxes.pop_back()
	fresh()
	cast("measured_step",Vector3.ZERO,{"step_direction":Vector3.RIGHT});advance(.05)
	check("step_waits_for_authority_release",step_calls==0)
	advance(.05)
	check("step_calls_explicit_receiver_once",step_calls==1 and events.any(func(e):return e.get("reason")=="movement_accepted"))
	advance(.5)
	check("step_does_not_repeat",step_calls==1)
	fresh()
	army.boxes.append({"position":Vector3(2,2,0),"size":Vector3(.1,4,8)})
	var accepted:=cast("measured_step",Vector3.ZERO,{"step_direction":Vector3.RIGHT})
	check("step_plans_collision_limited_destination",accepted.accepted and events[0].target.x<1.5 and events[0].target.x>0)
	army.boxes.pop_back()
	fresh()
	var ally=unit_at("sun",Vector3(1,0,1),90)
	vitals.receive_damage(80,"fixture")
	cast("guardian_circle",Vector3.ZERO);advance(.55)
	check("guardian_shields_real_hero_and_ally_on_release",ally.shield==55 and vitals.shield==55)
	advance(1)
	check("guardian_heals_real_hero_and_ally_on_army_clock",absf(ally.health-100)<.001 and absf(vitals.health-230)<.001)
	check("guardian_hero_receipt_is_explicit",events.any(func(e):return e.receipts.any(func(r):return r.get("receiver_kind")=="hero")))
	kit.cancel_active("teleport")
	check("cancel_removes_owned_guardian_status",ally.shield==0 and vitals.shield==0)
	fresh()
	ally=unit_at("sun",Vector3(1,0,1),90);ally.apply_shield(80,8)
	cast("guardian_circle",Vector3.ZERO);advance(.7);kit.cancel_active("cancel")
	check("guardian_preserves_stronger_independent_shield",ally.shield==80 and absf(ally.shield_until-8)<.0001)
	fresh()
	ally=unit_at("sun",Vector3(1,0,1),90);ally.apply_shield(20,8)
	cast("guardian_circle",Vector3.ZERO);advance(.7);kit.cancel_active("cancel")
	check("guardian_preserves_longer_independent_status",ally.shield_until>=8 and ally.shield==20)
	fresh()
	ally=unit_at("sun",Vector3(1,0,1),90);ally.apply_shield(20,8)
	cast("guardian_circle",Vector3.ZERO);advance(5.05)
	check("guardian_natural_expiry_restores_prior_status",ally.shield==20 and absf(ally.shield_until-8)<.0001)
	check("guardian_healing_stops_at_field_expiry",absf(ally.health-135)<.001)
	fresh()
	cast("guardian_circle",Vector3.ZERO);advance(1)
	cast("piercing_dawn");advance(.2)
	check("cancel_windup_preserves_existing_ward",kit.cancel_windup("damage") and kit.report().casts.size()==1 and kit.report().casts[0].ability_id=="guardian_circle" and vitals.shield==55)
	fresh()
	enemy=unit_at("moon",Vector3(0,0,8));cast("dawn_volley");advance(.9)
	check("volley_warning_precedes_gameplay",enemy.health==150 and release_events().is_empty() and fx.report().casts[0].warning_visible)
	advance(.05)
	check("volley_has_one_hero_release_and_three_paced_arrows",release_events().size()==1 and release_events()[0].geometry.projectiles.size()==3 and release_events()[0].geometry.projectiles[2].delay_s==.2)
	advance(1.4)
	check("volley_has_actual_damage_receipts",enemy.health<150 and events.any(func(e):return e.kind=="impact" and not e.receipts.is_empty()))
	fresh();cast("dawn_volley");advance(.4)
	var frozen: float=kit.elapsed
	var age: float=fx.report().casts[0].age_s
	kit.set_suspended(true);fx.set_suspended(true);advance(.7)
	check("suspension_freezes_cast_and_fx",kit.elapsed==frozen and fx.report().casts[0].age_s==age and release_events().is_empty())
	kit.set_suspended(false);fx.set_suspended(false);advance(.55)
	check("resume_releases_exactly_once",release_events().size()==1)
	fresh();cast("piercing_dawn");advance(.25);kit.cancel_active("dodge");advance(1)
	check("cancel_before_release_has_no_projectile",release_events().is_empty() and fx.report().active==0 and kit.report().cooldowns.piercing_dawn>0)
	fresh();cast("dawn_volley");var stale: Dictionary=events[0].duplicate(true);army.reset()
	check("reset_invalidates_old_generation",not fx.consume_event(stale) and kit.report().casts.is_empty() and kit.report().cooldowns.dawn_volley==0)
	fresh()
	for id in Kit.IDS:
		check("reject_nonfinite_"+id,not kit.request_ability(id,Vector3(NAN,0,0),Vector3.FORWARD,Vector3.ZERO).accepted)
	check("invalid_casts_do_not_spend_cooldowns",kit.report().cooldowns.values().all(func(v):return v==0))
	fresh();cast("guardian_circle",Vector3.ZERO);advance(.6)
	fx.set_options({"reduced_effects":true,"reduced_motion":true})
	check("reduced_options_retain_authoritative_boundary",fx.report().reduced_motion and fx.report().reduced_effects and fx.report().casts[0].warning_visible)
	var event: Dictionary=events[-1].duplicate(true)
	check("fx_rejects_duplicate_event",not fx.consume_event(event))
	var before_age: float=fx.report().casts[0].age_s
	fx.step(.4)
	check("presentation_extrapolation_is_bounded_to_one_army_tick",fx.report().casts[0].age_s-before_age<=.050001)
	event.event_seq+=100;event.origin=Vector3(INF,0,0)
	check("fx_rejects_nonfinite_event",not fx.consume_event(event))
	event=events[-1].duplicate(true);event.event_seq+=101;event.geometry.radius_m=4.9
	check("fx_rejects_midcast_geometry_mutation",not fx.consume_event(event))
	advance(6)
	check("fx_has_bounded_finite_retirement",fx.report().active==0 and fx.report().impacts==0 and fx.report().finite)
	fresh()
	check("vitals_damage_receipt",vitals.receive_damage(50,"hazard",vitals.generation,1).accepted and vitals.health==250)
	check("vitals_rejects_duplicate_receipt",not vitals.receive_damage(50,"hazard",vitals.generation,1).accepted and vitals.health==250)
	check("vitals_shield_absorbs_first",vitals.apply_shield(30,1) and vitals.receive_damage(40,"hazard",vitals.generation,2).accepted and vitals.health==240 and vitals.shield==0)
	check("vitals_rejects_nonfinite_and_old_generation",not vitals.receive_damage(NAN).accepted and not vitals.receive_damage(50,"hazard",vitals.generation-1).accepted)
	vitals.receive_damage(500,"hazard",vitals.generation,3)
	check("vitals_defeat_and_no_early_respawn",not vitals.alive and not vitals.respawn() and vitals.receive_heal(50)==0)
	advance(3)
	check("vitals_respawn_after_three_army_seconds",vitals.respawn() and vitals.alive and vitals.health==300)
	fresh();kit.ability_event.connect(reentrant_cancel)
	cast("kodanda");cancel_spawn=true;kit.reset("reentrant_reset")
	check("reset_rejects_reentrant_cancel_listener_cast",not callback_accepted and kit.report().casts.is_empty() and not kit.report().action_locked)
	kit.ability_event.disconnect(reentrant_cancel)
	fresh();sampler_calls=0;sample_reset=true
	kit.set_hero_receiver(vitals,resetting_sampler)
	cast("guardian_circle",Vector3.ZERO);advance(.6)
	var current_generation: int=kit.generation
	var new_generation_events: Array=events.filter(func(e):return e.generation==current_generation)
	check("attachment_sampler_reset_cannot_emit_stale_new_generation_impact",new_generation_events.size()==1 and new_generation_events[0].kind=="reset" and new_generation_events[0].event_seq==1)
	kit.set_hero_receiver(vitals,func():return origin)
	fresh();cast("dawn_volley")
	var isolated=Effects.new();root.add_child(isolated);isolated.set_process(false)
	var volley_begin: Dictionary=events[0].duplicate(true)
	isolated.consume_event(volley_begin)
	var truncated:=volley_begin.duplicate(true);truncated.kind="release";truncated.event_seq+=1;truncated.age_s=.95;truncated.geometry.projectiles.resize(1)
	check("fx_rejects_truncated_projectile_array_without_index_error",not isolated.consume_event(truncated))
	var missing_kind:=volley_begin.duplicate(true);missing_kind.kind="impact";missing_kind.event_seq+=2;missing_kind.age_s=.95
	missing_kind.projectile_index=0;missing_kind.contact_position=Vector3.ZERO;missing_kind.terminal=true;missing_kind.reason="unit"
	missing_kind.receipts=[{"unit_id":1,"position":Vector3.ZERO}]
	check("fx_rejects_missing_receipt_kind",not isolated.consume_event(missing_kind))
	isolated.free()
	fresh();vitals.receive_damage(100,"heal_fixture");vitals.changed.connect(reset_during_heal);heal_reset=true
	var actual_heal: float=vitals.receive_heal(10)
	check("heal_delta_is_committed_before_reset_observer",actual_heal==10 and vitals.health==300)
	vitals.changed.disconnect(reset_during_heal)
	var source_hashes: Dictionary={}
	for path in ["res://scripts/rama_ability_kit.gd","res://scripts/rama_ability_effects.gd","res://scripts/rama_vitals.gd","res://shaders/rama_ribbon.gdshader","res://assets/design/rama-ability-kit.json"]:source_hashes[path]=FileAccess.get_sha256(path)
	var passed:=checks.all(func(c):return c.passed)
	var report:={"schema":1,"suite":"rama_ability_cases","passed":passed,"checks":checks,"source_sha256":source_hashes,"scope":"Actual offline lane units and hero receiver; headless event/lifetime checks are not a visual or balance review."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path:=argument.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("Rama ability checks: %d/%d"%[checks.filter(func(c):return c.passed).size(),checks.size()])
	kit.free();fx.free();vitals.free();army.free()
	quit(0 if passed else 1)
