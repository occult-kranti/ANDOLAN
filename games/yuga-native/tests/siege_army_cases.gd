extends SceneTree
## Independent actual-simulation adversarial checks. No renderer/network claim.

const Army = preload("res://scripts/lane_army.gd")
const Unit = preload("res://scripts/lane_minion.gd")
var army
var checks: Array = []
var events: Array = []
var original_boxes: Array = []
var source_hashes: Dictionary = {}
var manifest: Dictionary

func _initialize() -> void:
	call_deferred("run")

func record(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	print("SIEGE_CASE ",label," ",passed)
	if not passed: push_error("SIEGE FAILED: "+label)

func _event(value: Dictionary) -> void:
	var entry := value.duplicate(true)
	entry.observed_time = army.elapsed
	events.append(entry)

func tick(count_: int = 1) -> void:
	for _i in range(count_): army.step_simulation(.05)

func hold(unit) -> void:
	unit.attack_time = 100.0
	unit.attack_cooldown = 100.0
	unit.target = null

func clear_units() -> void:
	for unit in army.units: unit.free()
	army.units.clear()
	army._attacks.clear()

func add_unit(team: String, role: String, point: Vector3):
	var unit = Unit.new()
	unit.setup(army,army.next_id,team,role,1)
	army.next_id += 1
	unit.render_art = false
	unit.position = point
	unit.previous_position = point
	unit.progress = float(army.lanes[1].length)*.5+point.z*(1 if team=="sun" else -1)
	unit.defeated.connect(army._on_defeated)
	army.add_child(unit)
	army.units.append(unit)
	return unit

func fixture(role: String = "cannon_cart") -> Dictionary:
	army.boxes = original_boxes.duplicate(true)
	army.start_siege_drill()
	clear_units()
	events.clear()
	var distance := 8.0 if role=="cannon_cart" else 2.0
	var source = add_unit("sun",role,Vector3(0,0,-distance))
	var victim = add_unit("moon","spearman",Vector3(0,0,distance))
	var friend = add_unit("sun","spearman",Vector3(.9,0,distance))
	hold(victim)
	hold(friend)
	army._decision_clock = 0
	return {"source":source,"victim":victim,"friend":friend}

func windup(source) -> Dictionary:
	for _i in range(120):
		tick()
		for event in events:
			if event.kind=="windup" and event.team==source.team and event.role==source.role:
				return event
	return {}

func finish_shot(event: Dictionary, extra: float = .1) -> void:
	if event.is_empty(): return
	var deadline: float = event.observed_time+event.delay+extra
	while army.elapsed < deadline-1e-8: tick()

func receipts(event: Dictionary) -> Array:
	if event.is_empty(): return []
	return events.filter(func(e): return e.kind=="impact" and e.id==event.id)

func run() -> void:
	for path in ["res://scripts/lane_army.gd","res://scripts/lane_minion.gd","res://scripts/lane_vehicle_art.gd","res://scripts/lane_unit_art.gd","res://assets/world/confluence-map.json"]:
		source_hashes[path] = FileAccess.get_sha256(path)
	manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	army = Army.new()
	army.visual_enabled = false
	root.add_child(army)
	army.set_physics_process(false)
	army.siege_event.connect(_event)
	var configured: bool = army.configure(manifest,null)
	original_boxes = army.boxes.duplicate(true)
	record("initial_thirty_remain_humans",configured and army.units.size()==30 and army.units.all(func(u): return u.role not in Unit.VEHICLE_ROLES),army.report())
	record("drill_is_six_mirrored_center_units",army.start_siege_drill() and army.units.size()==6 and army.units.all(func(u): return u.lane_id==1) and balanced(),army.report())
	for role in ["cannon_cart","royal_chariot"]:
		var f := fixture(role)
		var event := windup(f.source)
		var valid: bool = not event.is_empty()
		if valid:
			var deadline: float = event.observed_time+event.delay
			var no_early_damage: bool = f.victim.health==f.victim.max_health
			while army.elapsed+.05 < deadline-1e-7:
				tick()
				no_early_damage = no_early_damage and f.victim.health==f.victim.max_health
			finish_shot(event)
			var impacts := receipts(event)
			record(role+"_telegraph_precedes_exactly_one_impact",no_early_damage and event.delay >= (.75 if role=="cannon_cart" else .5) and impacts.size()==1 and impacts[0].observed_time+1e-7>=deadline and f.victim.health<f.victim.max_health,{"windup":event,"receipts":impacts,"health":f.victim.health})
			record(role+"_splash_never_hurts_friends_or_credits_player",f.friend.health==f.friend.max_health and army.gold==0 and army.kills==0,army.report())
		else:
			record(role+"_telegraph_precedes_exactly_one_impact",false,{"events":events})
		f = fixture(role)
		event = windup(f.source)
		if not event.is_empty(): f.victim.position += Vector3(float(event.radius)+2,0,0)
		finish_shot(event)
		record(role+"_moving_target_dodges_committed_ground_point",not event.is_empty() and f.victim.health==f.victim.max_health and receipts(event).size()==1 and receipts(event)[0].target==event.target,{"windup":event,"receipts":receipts(event)})
		f = fixture(role)
		event = windup(f.source)
		var point: Vector3 = f.victim.position
		army.units.erase(f.victim)
		f.victim.free()
		var replacement = add_unit("moon","spearman",point)
		hold(replacement)
		finish_shot(event)
		record(role+"_fixed_blast_survives_original_target_lifetime",not event.is_empty() and replacement.health<replacement.max_health and receipts(event).size()==1,{"new_victim_health":replacement.health,"receipts":receipts(event)})
		f = fixture(role)
		event = windup(f.source)
		f.source.receive_damage(1000,"army")
		finish_shot(event)
		var cancelled := receipts(event)
		record(role+"_source_death_cancels_once_before_impact",not event.is_empty() and f.victim.health==f.victim.max_health and cancelled.size()==1 and cancelled[0].cancelled and cancelled[0].damage==0 and army.report().siege.pending==0,{"receipts":cancelled})
		f = fixture(role)
		army.boxes.append({"position":Vector3.ZERO,"size":Vector3(4,4,.04)})
		tick(30)
		record(role+"_thin_wall_prevents_commit",events.filter(func(e): return e.kind=="windup").is_empty() and f.victim.health==f.victim.max_health,{"events":events})
		f = fixture(role)
		event = windup(f.source)
		army.boxes.append({"position":Vector3.ZERO,"size":Vector3(4,4,.04)})
		finish_shot(event)
		cancelled = receipts(event)
		record(role+"_new_wall_cancels_pending_impact",not event.is_empty() and f.victim.health==f.victim.max_health and cancelled.size()==1 and cancelled[0].cancelled,{"receipts":cancelled})
		f = fixture(role)
		event = windup(f.source)
		var shielded = add_unit("moon","spearman",f.victim.position+Vector3(2,0,0))
		hold(shielded)
		army.boxes.append({"position":f.victim.position+Vector3(1,0,0),"size":Vector3(.04,4,3)})
		finish_shot(event)
		record(role+"_splash_respects_victim_side_wall",not event.is_empty() and f.victim.health<f.victim.max_health and shielded.health==shielded.max_health,{"primary_health":f.victim.health,"behind_wall_health":shielded.health})
		f = fixture(role)
		var reward_unit = add_unit("moon",role,Vector3(10,0,0))
		var bad_ok := true
		for amount in [NAN,INF,-1,0,true,"100",1001]: bad_ok = not reward_unit.take_hit(amount) and bad_ok
		var hp: float = reward_unit.health
		var first: bool = reward_unit.take_hit(1000)
		var paid: int = army.gold
		var again: bool = reward_unit.take_hit(1000)
		record(role+"_invalid_damage_and_exact_once_reward",bad_ok and hp==reward_unit.max_health and first and not again and paid>0 and army.gold==paid and army.kills==1,{"reward":paid,"rejections":reward_unit.invalid_damage})
	# Repeated mode transitions destroy outstanding attacks and nodes immediately.
	var lifecycle_ok := true
	for i in range(40):
		var f := fixture()
		var event := windup(f.source)
		army.boxes = original_boxes.duplicate(true)
		if i%2==0: army.reset()
		else: lifecycle_ok = army.start_siege_drill() and lifecycle_ok
		lifecycle_ok = lifecycle_ok and not event.is_empty() and army._attacks.is_empty() and army.get_child_count()==(30 if i%2==0 else 6) and army.gold==0 and events[-1].kind=="reset"
	record("forty_same_frame_reset_drill_cycles_clear_pending_work",lifecycle_ok,army.report())
	var f := fixture()
	var event := windup(f.source)
	army.cores = {"sun":0.0,"moon":0.0}
	tick()
	var elapsed: float = army.elapsed
	var health: float = f.victim.health
	tick(100)
	record("outcome_clears_telegraphs_and_stops_future_damage",not event.is_empty() and army.winner=="draw" and army._attacks.is_empty() and army.elapsed==elapsed and f.victim.health==health and events[-1].kind=="reset",army.report())
	# Actual same-tick target acquisition and damage, including corpse-retirement pressure.
	army.boxes = original_boxes.duplicate(true)
	army.start_siege_drill()
	clear_units()
	events.clear()
	var left = add_unit("sun","royal_chariot",Vector3(0,0,-2))
	var right = add_unit("moon","royal_chariot",Vector3(0,0,2))
	left.health = 1
	right.health = 1
	tick(15)
	record("simultaneous_lethal_siege_trade_is_symmetric",not left.alive and not right.alive and army.siege_impacts==2 and army.gold==0,{"siege":army.report().siege})
	army.start_siege_drill()
	clear_units()
	events.clear()
	var shooters: Array = []
	for i in range(32): shooters.append(add_unit("sun","cannon_cart",Vector3(-.2+float(i%4)*.1,0,-8-float(i/4)*.01)))
	for i in range(40):
		var victim = add_unit("moon","spearman",Vector3(-.2+float(i%5)*.1,0,8+float(i/5)*.01))
		victim.health = 1
		hold(victim)
	tick(20)
	var burst: Dictionary = army.report()
	record("72_unit_repeated_aoe_burst_safe_during_corpse_retirement",burst.alive==32 and burst.pending_cleanup<=24 and burst.unit_nodes<=96 and burst.queued_attacks<=72 and burst.siege.pending<=32 and burst.kills_by_lane[1]==40 and burst.gold==0 and burst.finite,burst)
	army.start_siege_drill()
	clear_units()
	events.clear()
	shooters.clear()
	for i in range(33): shooters.append(add_unit("sun","cannon_cart",Vector3(0,0,-8-float(i)*.001)))
	for i in range(39):
		var victim = add_unit("moon","spearman",Vector3(0,0,8+float(i)*.001))
		hold(victim)
	tick()
	var queue_pressure: Dictionary = army.report()
	var unspent: int = shooters.filter(func(u): return u.attack_cooldown==0).size()
	record("33_eligible_shooters_bound_siege_queue_without_spending_rejected_cooldown",queue_pressure.alive==72 and queue_pressure.siege.pending==32 and queue_pressure.queued_attacks==32 and unspent==1,{"report":queue_pressure,"unspent_cooldowns":unspent})
	# Wave cadence in a cleared-spawn fixture, retaining real wave logic.
	army.reset()
	var cadence: Array = []
	var cadence_ok := true
	for wave in range(2,16):
		clear_units()
		army._spawn_wave()
		var stats: Dictionary = army.report()
		cadence.append({"wave":wave,"roles":stats.roles_alive,"balanced":balanced()})
		cadence_ok = cadence_ok and balanced() and (stats.roles_alive.cannon_cart>0)==(wave%3==0) and (stats.roles_alive.royal_chariot>0)==(wave%5==0) and stats.alive<=72
	record("fifteen_wave_events_keep_mirrored_siege_cadence",cadence_ok,{"waves":cadence})
	army.reset()
	for _round in range(2):
		for unit in army.units:
			unit.progress += 20
			unit.position = army.route_sample(unit.lane_id,unit.progress,unit.team,unit.lateral).position
		army._spawn_wave()
	var cap_ok: bool = army.report().alive==72 and balanced()
	army._spawn_wave()
	record("real_wave_pressure_reaches72_without_unpaired_overflow",cap_ok and army.report().alive==72 and balanced() and army.report().unit_nodes<=96,army.report())
	# 24000 accepted advancing ticks = 1200s. An outcome triggers a fresh match;
	# no-op post-outcome ticks must never be counted as simulated time.
	army.reset()
	events.clear()
	var simulated := 0.0
	var valid_steps := true
	var bounds_ok := true
	var finite := true
	var outcomes := 0
	var peak := {"alive":0,"nodes":0,"corpses":0,"attacks":0,"siege_attacks":0}
	var observed := {}
	var windups_seen := 0
	var impacts_seen := 0
	var defeats := [0,0,0]
	var blocked := 0
	var begin := Time.get_ticks_msec()
	for i in range(24000):
		if not army.winner.is_empty():
			outcomes += 1
			army.reset()
		var before: float = army.elapsed
		valid_steps = army.step_simulation(.05) and valid_steps
		simulated += army.elapsed-before
		if i%20==0 or i==23999:
			var stats: Dictionary = army.report()
			bounds_ok = bounds_ok and stats.max_alive_seen<=72 and stats.max_corpses_seen<=24 and stats.max_nodes_seen<=96 and stats.max_attacks_seen<=72 and stats.siege.pending<=32
			finite = finite and stats.finite
			peak.alive = maxi(peak.alive,stats.max_alive_seen)
			peak.nodes = maxi(peak.nodes,stats.max_nodes_seen)
			peak.corpses = maxi(peak.corpses,stats.max_corpses_seen)
			peak.attacks = maxi(peak.attacks,stats.max_attacks_seen)
			peak.siege_attacks = maxi(peak.siege_attacks,stats.siege.pending)
			for role in stats.roles_alive:
				if stats.roles_alive[role]>0: observed[role] = true
		if i%200==0:
			await process_frame
	# Event observation survives reset so long-run siege receipts cannot disappear.
	for e in events:
		if e.kind=="windup": windups_seen += 1
		elif e.kind=="impact" and not e.get("cancelled",false): impacts_seen += 1
	var soak: Dictionary = army.report()
	defeats = soak.kills_by_lane
	blocked = soak.route_blocked_moves
	var metrics := {"ticks":24000,"advancing_simulation_seconds":simulated,"outcomes":outcomes,"peak":peak,"roles_seen":observed.keys(),"windups":windups_seen,"impacts":impacts_seen,"last_match_defeats_by_lane":defeats,"last_match_blocked_moves":blocked,"wall_ms":Time.get_ticks_msec()-begin}
	record("twenty_minute_advancing_simulation_stays_finite_and_bounded",valid_steps and bounds_ok and finite and absf(simulated-1200)<.001,metrics)
	record("soak_exercises_both_siege_roles_and_actual_impacts",observed.has("cannon_cart") and observed.has("royal_chariot") and windups_seen>0 and impacts_seen>0,metrics)
	record("soak_all_lanes_fight_without_static_route_collisions",defeats.all(func(value): return value>0) and blocked==0,metrics)
	army.free()
	await process_frame
	var same := true
	for path in source_hashes: same = same and source_hashes[path]==FileAccess.get_sha256(path)
	record("sources_unchanged_during_independent_run",same,source_hashes)
	var passed := checks.all(func(c): return c.passed)
	var report := {"passed":passed,"checks":checks,"engine":Engine.get_version_info().string,"source_sha256":source_hashes,"scope":"Actual offline fixed-step army and Node lifecycle. Explicit fixture isolation/repositioning exercises ground targeting, thin-wall LOS, death/reset/outcome and simultaneous burst pressure. No renderer, network, player-health, hardware-performance or commercial-game parity claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var path := arg.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path).get_base_dir())
			var output := FileAccess.open(path,FileAccess.WRITE)
			if output: output.store_string(JSON.stringify(report,"\t")+"\n")
			else: passed = false
	print("YUGA_SIEGE_ARMY_CASES ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)

func balanced() -> bool:
	var composition := {}
	for unit in army.units:
		if not unit.alive: continue
		var key: String = str(unit.lane_id)+"/"+unit.role
		if not composition.has(key): composition[key] = {"sun":0,"moon":0}
		composition[key][unit.team] += 1
	return composition.values().all(func(c): return c.sun==c.moon)
