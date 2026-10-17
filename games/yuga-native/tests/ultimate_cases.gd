extends SceneTree
## Real offline invocation rules/receivers and adversarial lifecycle checks.
const Army = preload("res://scripts/lane_army.gd")
const Unit = preload("res://scripts/lane_minion.gd")
const Session = preload("res://scripts/ultimate_session.gd")
const Rules = preload("res://scripts/ultimate_rules.gd")
var checks: Array = []
var army
var session
var events: Array = []
var manifest: Dictionary
var data: Dictionary

func _initialize() -> void:call_deferred("run")
func record(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	if not passed:push_error("ULTIMATE FAILED: "+label)
func fresh() -> void:
	army.reset()
	for unit in army.units.duplicate():army.units.erase(unit);unit.free()
	army._rebuild_buckets()
	events.clear()
func unit_at(team: String, point: Vector3, health := 150.0):
	var unit = Unit.new()
	unit.setup(army,army.next_id,team,"commander",1)
	army.next_id += 1
	unit.render_art = false
	unit.position = point
	unit.attack_time = 1000
	unit.attack_cooldown = 1000
	unit.health = health
	unit.defeated.connect(army._on_defeated)
	army.add_child(unit)
	army.units.append(unit)
	return unit
func advance(seconds: float) -> void:
	var remain := seconds
	while remain>1e-8:
		var delta := minf(.05,remain)
		army.step_simulation(delta)
		remain -= delta
func invoke(hero: String, target := Vector3(0,0,5)) -> Dictionary:
	session.select_invocation(hero)
	return session.request_cast(Vector3.ZERO,Vector3(0,0,1),target)
func run() -> void:
	var loaded := Rules.load_rules()
	record("canonical_fourteen_rules_load",loaded.valid and loaded.data.rules.size()==14,{"errors":loaded.errors})
	data = loaded.data
	for field in ["network_enabled","hero_health_enabled","core_spell_damage_enabled","avatar_changes_enabled"]:
		var bad := data.duplicate(true);bad.scope[field] = true
		record("reject_scope_"+field,not Rules.validate(bad).is_empty())
	for pair in [["shared_cooldown_s",1],["max_active_casts",2],["max_receipts_per_event",144],["history_capacity",1000],["grounded_max_height_m",100]]:
		var bad := data.duplicate(true);bad[pair[0]] = pair[1]
		record("reject_limit_"+pair[0],not Rules.validate(bad).is_empty())
	for value in [NAN,INF,-1,true,"12"]:
		var bad := data.duplicate(true);bad.rules[0].geometry.range_m = value
		record("reject_projectile_range_"+str(value),not Rules.validate(bad).is_empty())
	var duplicate := data.duplicate(true);duplicate.rules[1].hero_id="rama"
	record("reject_duplicate_hero",not Rules.validate(duplicate).is_empty())
	var stale := data.duplicate(true);stale.codex_sha256="stale"
	record("reject_stale_source",not Rules.validate(stale).is_empty())
	var angle := data.duplicate(true);angle.rules[3].geometry.half_angle_cos=.01
	record("reject_decorative_width_as_sector",not Rules.validate(angle).is_empty())
	var delay := data.duplicate(true);delay.rules[0].timing.travel_s=0
	record("reject_instant_long_range_projectile",not Rules.validate(delay).is_empty())
	var duration := data.duplicate(true);duration.rules[10].effects[0].duration_s=999
	record("reject_permanent_summons",not Rules.validate(duration).is_empty())
	var short_zone := data.duplicate(true);short_zone.rules[8].timing.active_s=0
	record("reject_hidden_sanctuary_duration",not Rules.validate(short_zone).is_empty())
	var long_shield := data.duplicate(true);long_shield.rules[12].effects[0].duration_s=8
	record("reject_shield_beyond_visible_window",not Rules.validate(long_shield).is_empty())
	var policy := data.duplicate(true);policy.receiver_policy="decorative_width"
	record("reject_receiver_policy_drift",not Rules.validate(policy).is_empty())
	var team := data.duplicate(true);team.rules[0].effects[0].team="ally"
	record("reject_friendly_damage",not Rules.validate(team).is_empty())
	var tmp := "user://ultimate-bad.json"
	for entry in [["duplicate_keys",'{"schema_version":1,"schema_version":1}'],["deep_nesting","[".repeat(20)+"0"+"]".repeat(20)],["deep_valid_object",'{"a":'.repeat(1000)+"0"+"}".repeat(1000)],["oversize"," ".repeat(65537)],["bad_json","{broken"]]:
		var file := FileAccess.open(tmp,FileAccess.WRITE);file.store_string(entry[1]);file.close()
		record("reject_parser_"+entry[0],not Rules.load_rules(tmp).valid)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(tmp))
	var disk := {"kind":"disk","center":Vector3.ZERO,"radius_m":7.0,"height_m":2.5}
	record("disk_exact_boundary_and_height",Rules.contains(disk,Vector3(7,0,0)) and not Rules.contains(disk,Vector3(7.001,0,0)) and not Rules.contains(disk,Vector3(0,2.501,0)))
	for threshold in [.55,.25]:
		var sector := {"kind":"sector","center":Vector3.ZERO,"forward":Vector3(0,0,1),"range_m":12.0,"half_angle_cos":threshold,"height_m":2.5}
		var a := acos(threshold)
		record("sector_true_angle_"+str(threshold),Rules.contains(sector,Vector3(sin(a-.001)*10,0,cos(a-.001)*10)) and not Rules.contains(sector,Vector3(sin(a+.001)*10,0,cos(a+.001)*10)) and not Rules.contains(sector,Vector3(0,0,-1)))
	record("segment_circle_initial_overlap_and_final_contact",Rules.segment_circle_fraction(Vector3.ZERO,Vector3(0,0,2),Vector3.ZERO,.5)==0 and absf(Rules.segment_circle_fraction(Vector3.ZERO,Vector3(0,0,2),Vector3(0,0,2.5),.5)-1)<.00001)
	manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	army = Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	record("army_configuration",army.configure(manifest,null))
	session = Session.new();root.add_child(session)
	session.invocation_event.connect(func(event):events.append(event.duplicate(true)))
	record("session_configuration",session.configure(army))
	for hero in Rules.HEROES:
		fresh()
		var enemy = unit_at("moon",Vector3(0,0,4))
		var ally = unit_at("sun",Vector3(2,0,2),20)
		var result := invoke(hero)
		advance(2.0)
		var kind: String = data.rules[Rules.HEROES.find(hero)].effects[0].kind
		var received := false
		if kind in ["damage","damage_rate"]:received=is_instance_valid(enemy) and enemy.health<150
		elif kind=="heal":received=is_instance_valid(ally) and ally.health>20
		elif kind=="shield":received=is_instance_valid(ally) and ally.shield>0
		elif kind=="summon":received=army.report().temporary_units==2
		var impacts := events.filter(func(e):return e.kind=="impact" and not e.receipts.is_empty())
		record("real_payload_"+hero,result.accepted and received and not impacts.is_empty() if hero!="ulupi" else result.accepted and received,{"kind":kind,"report":session.report(),"impact_count":impacts.size()})
		if hero=="sita":record("sanctuary_has_actual_capped_healing",ally.health>20 and ally.health<=150)
		if hero=="ulupi":record("basin_has_actual_slow_receiver",enemy.slow_multiplier==.55)
	fresh()
	var ally = unit_at("sun",Vector3(2,0,2),140)
	record("healing_caps_at_max",ally.receive_heal(95)==10 and ally.health==150)
	record("shield_absorbs_before_health",ally.apply_shield(80,4) and ally.receive_damage(30,"army") and ally.shield==50 and ally.health==150)
	record("shield_max_not_additive",ally.apply_shield(70,4) and ally.shield==70)
	advance(4.0)
	record("shield_expires_on_army_clock",ally.shield==0)
	var rejected := true
	for value in [NAN,INF,true,-10,0,"40",1001]:rejected = rejected and ally.receive_heal(value)==0 and not ally.apply_shield(value,4)
	record("invalid_receiver_inputs_do_not_mutate",rejected and ally.health==150 and ally.shield==0)
	ally.receive_damage(1000,"army")
	record("dead_receiver_cannot_revive_or_shield",ally.receive_heal(100)==0 and not ally.apply_shield(80,4))
	fresh()
	var slow = unit_at("moon",Vector3(0,0,0))
	slow.attack_time=0;slow.progress=100;slow.position=army.route_sample(1,100,"moon",0).position
	var start: float = slow.progress
	slow.apply_slow(.55,.5)
	advance(.25)
	var reduced: float = slow.progress-start
	record("slow_changes_real_route_displacement",absf(reduced-3.45*.55*.25)<.001,{"distance":reduced})
	advance(.30)
	record("slow_expires_and_speed_recovers",slow.movement_multiplier()==1)
	fresh();invoke("ravana");advance(.1)
	var before: Dictionary = session.report()
	session.select_invocation("sita")
	record("selector_cannot_reset_shared_cooldown",not session.request_cast(Vector3.ZERO,Vector3(0,0,1),Vector3.ZERO).accepted and session.report().cooldown_remaining==before.cooldown_remaining)
	session.cancel_active("teleport")
	record("teleport_cancel_preserves_cooldown",session.report().active_phase=="ready" and session.report().cooldown_remaining>11)
	advance(12)
	record("cooldown_ends_on_fixed_clock",session.request_cast(Vector3.ZERO,Vector3(0,0,1),Vector3.ZERO).accepted)
	fresh();invoke("rama");advance(.5)
	var frozen: float = session.elapsed
	session.set_suspended(true);advance(.5)
	record("suspended_session_does_not_release_or_advance",session.elapsed==frozen and events.filter(func(e):return e.kind=="release").is_empty())
	session.set_suspended(false);advance(.6)
	record("resume_continues_pending_cast",not events.filter(func(e):return e.kind=="release").is_empty())
	fresh()
	for args in [[Vector3(0,1,0),Vector3(0,0,1),Vector3.ZERO],[Vector3.ZERO,Vector3.ZERO,Vector3.ZERO],[Vector3.ZERO,Vector3(1e30,0,1e30),Vector3.ZERO],[Vector3(NAN,0,0),Vector3(0,0,1),Vector3.ZERO]]:
		record("reject_invalid_cast_"+str(args[0])+str(args[1]),not session.request_cast(args[0],args[1],args[2]).accepted and session.report().cooldown_remaining==0)
	session.select_invocation("hanuman")
	record("ground_range_and_height_are_authoritative",not session.request_cast(Vector3.ZERO,Vector3(0,0,1),Vector3(0,0,15)).accepted and not session.request_cast(Vector3.ZERO,Vector3(0,0,1),Vector3(0,1,5)).accepted)
	fresh()
	army.boxes.append({"position":Vector3(0,2,3),"size":Vector3(10,4,.1)})
	var blocked_enemy = unit_at("moon",Vector3(0,0,5))
	invoke("rama");advance(2)
	var wall_contacts := events.filter(func(e):return e.kind=="impact" and e.reason=="wall")
	record("three_projectiles_stop_at_thin_wall",blocked_enemy.health==150 and wall_contacts.size()==3)
	army.boxes.pop_back()
	fresh()
	var far_enemy = unit_at("moon",Vector3(0,0,28.49))
	invoke("arjuna");advance(1.25)
	record("last_partial_projectile_step_reaches_range",far_enemy.health==62,{"health":far_enemy.health})
	fresh()
	invoke("subhadra");advance(1.0)
	var temporary: Array = army.units.filter(func(u):return u.practice_summon)
	record("summons_exactly_two_real_units",temporary.size()==2 and temporary[0].attack_damage()==28 and temporary[0].max_health==105)
	var gold_before: int = army.gold
	for summon in temporary:summon.attack_time=1000
	advance(9.0)
	record("temporary_expiry_no_core_damage_or_gold",army.report().temporary_units==0 and army.cores.sun==100 and army.cores.moon==100 and army.gold==gold_before)
	fresh()
	for i in range(71):unit_at("sun",Vector3(-50+i%10,0,-80+floori(i/10.0)*2))
	var count_before: int = army.units.size()
	var planned: Dictionary = army.plan_temporary_pair(Vector3.ZERO,"spearman")
	record("pair_rejected_at71_live_without_partial_spawn",not planned.valid and army.units.size()==count_before)
	fresh()
	var counter := 0
	for i in range(40):
		invoke(Rules.HEROES[i%14]);advance(.2);army.reset()
		if session.report().active_phase=="ready" and session.report().history_size==1 and army.report().alive==30:counter+=1
		for unit in army.units.duplicate():army.units.erase(unit);unit.free()
	record("forty_restarts_bound_events_nodes_and_cooldown",counter==40 and session.report().cooldown_remaining==0 and army.get_child_count()==0)
	fresh()
	var victim = unit_at("moon",Vector3(0,0,2),1)
	victim.defeated.connect(func(_unit,_by_player):army.reset())
	invoke("ravana");advance(1.0)
	var reset_epoch: int = session.epoch
	var stale_impact := events.any(func(e):return e.kind=="impact" and e.epoch==reset_epoch and not e.receipts.is_empty())
	record("reentrant_defeat_reset_has_no_locked_emitter_or_new_epoch_receipt",army.report().alive==30 and not stale_impact and session.report().active_phase=="ready")
	fresh();invoke("chitrangada");advance(1)
	var old_epoch: int = session.epoch
	army.reset()
	record("reset_invalidates_epoch_and_pending_payload",session.epoch>old_epoch and session.report().active_phase=="ready" and session.report().cooldown_remaining==0)
	var source_sha256 := {}
	for path in ["res://scripts/ultimate_rules.gd","res://scripts/ultimate_session.gd","res://scripts/lane_army.gd","res://scripts/lane_minion.gd","res://assets/design/native-ultimate-rules.json","res://tests/ultimate_cases.gd"]:source_sha256[path]=FileAccess.get_sha256(path)
	var passed := checks.all(func(c):return c.passed)
	var evidence := {"passed":passed,"checks":checks,"source_sha256":source_sha256,"engine":Engine.get_version_info().string,"scope":"Headless native troop invocation rules, receiver behavior and lifecycle; no rendering, consumer GPU, hero health, network or production-model acceptance."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var path := arg.trim_prefix("--report=");DirAccess.make_dir_recursive_absolute(path.get_base_dir());var file := FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(evidence,"\t")+"\n")
	print("YUGA_ULTIMATE_CASES ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	session.free();army.free()
	quit(0 if passed else 1)
