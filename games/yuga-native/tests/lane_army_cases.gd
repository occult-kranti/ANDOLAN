extends SceneTree
## Headless behavior, lifecycle, source-art and 20-minute fixed-step soak.
## This is not rendered performance, online play, or final art acceptance.

const Army = preload("res://scripts/lane_army.gd")
var checks: Array = []
var army
var manifest: Dictionary
var source_hashes: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func record(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	if not passed:push_error("LANE ARMY FAILED: "+label)

func run() -> void:
	for path in ["res://scripts/lane_army.gd","res://scripts/lane_minion.gd","res://scripts/lane_unit_art.gd","res://assets/world/confluence-map.json"]:
		source_hashes[path] = FileAccess.get_sha256(path)
	manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	army = Army.new()
	army.visual_enabled = false
	root.add_child(army)
	army.set_physics_process(false)
	record("valid_three_lane_config_spawns30",army.configure(manifest,null) and army.report().alive==30,army.report())
	var classes := {}
	for unit in army.units:
		var key: String = unit.team+unit.role
		classes[key] = classes.get(key,0)+1
	record("mirrored_composition_three_roles",classes.get("sunspearman")==6 and classes.get("moonspearman")==6 and classes.get("sunbow_guard")==6 and classes.get("moonbow_guard")==6 and classes.get("suncommander")==3 and classes.get("mooncommander")==3,classes)
	var enemy = army.units.filter(func(u):return u.team=="moon")[0]
	var health_before: float = enemy.health
	var rejected := true
	for value in [-10,0,NAN,INF,true,"25",1001]:
		rejected = rejected and not enemy.take_hit(value)
	record("invalid_damage_never_heals_kills_or_awards",rejected and enemy.health==health_before and army.gold==0,{"rejections":enemy.invalid_damage})
	var expected_gold: int = enemy.STATS[enemy.role].gold
	var accepted: bool = enemy.take_hit(1000)
	var repeated: bool = enemy.take_hit(1000)
	record("projectile_compatible_player_last_hit_gold_once",accepted and not repeated and army.gold==expected_gold and army.kills==1,army.report())
	var ally = army.units.filter(func(u):return u.team=="sun")[0]
	record("friendly_projectile_damage_ignored",not ally.take_hit(25) and ally.health==ally.max_health,{})
	var enemy_two = army.units.filter(func(u):return u.team=="moon" and u.alive)[0]
	enemy_two.take_hit(1)
	enemy_two.receive_damage(1000,"army")
	record("assist_does_not_fake_confirmed_gold",army.gold==expected_gold and army.kills==1,{})
	var old_state := JSON.stringify(army.report())
	var invalid := manifest.duplicate(true)
	invalid.lanes[0].points[0][0] = NAN
	var invalid_boxes := manifest.duplicate(true)
	invalid_boxes.authority_collision_boxes = 7
	record("malformed_config_rejected_atomically",not army.configure(invalid,null) and not army.configure(invalid_boxes,null) and JSON.stringify(army.report())==old_state,{})
	var elapsed_before: float = army.elapsed
	record("nonfinite_or_unbounded_step_rejected",not army.step_simulation(NAN) and not army.step_simulation(INF) and not army.step_simulation(-.1) and not army.step_simulation(.5) and army.elapsed==elapsed_before,{})
	record("wall_occludes_pulse_and_target_line",not army.line_clear(Vector3(-32,0,-28),Vector3(-8,0,-28)) and army.line_clear(Vector3(-40,0,-10),Vector3(-40,0,10)),{})
	army.reset()
	var reset_ok := true
	for i in range(12):
		army.reset()
		reset_ok = reset_ok and army.units.size()==30 and army.get_child_count()==30 and army.report().queued_for_deletion==0 and army.gold==0 and army._attacks.is_empty()
	record("same_frame_reset_has_no_queued_node_accumulation",reset_ok,army.report())
	for unit in army.units.duplicate():
		if is_instance_valid(unit):unit.receive_damage(1000,"army")
	record("same_frame_death_burst_corpses_bounded",army.report().pending_cleanup<=24 and army.units.size()<=96 and army.gold==0,army.report())
	for i in range(25):army.step_simulation(.05)
	record("dead_units_cleaned_after_fall",army.units.is_empty(),army.report())
	army.reset()
	var next_waves: int = army.waves
	for i in range(599):army.step_simulation(.05)
	record("wave_not_early",army.waves==next_waves and army.elapsed<30,{"elapsed":army.elapsed,"waves":army.waves})
	army.step_simulation(.05)
	record("paired_wave_on30_seconds",army.waves==next_waves+1 and army.report().alive<=72,army.report())
	# Capacity pressure uses valid damage and explicit route repositioning to keep
	# spawn slots clear while exceeding the ordinary symmetric soak population.
	army.reset()
	for round_index in range(2):
		for unit in army.units:
			unit.progress += 20
			unit.position = army.route_sample(unit.lane_id,unit.progress,unit.team,unit.lateral).position
		army._spawn_wave()
	var reached70: bool = army.report().alive==70 and army.rejected_waves>0
	for unit in army.units.duplicate().slice(0,8):unit.receive_damage(1000,"army")
	for unit in army.units:
		if unit.alive:
			unit.progress += 10
			unit.position = army.route_sample(unit.lane_id,unit.progress,unit.team,unit.lateral).position
	army._spawn_wave()
	var pressure: Dictionary = army.report()
	army._spawn_wave()
	record("exact72_capacity_and_paired_overflow_policy",reached70 and pressure.alive==72 and army.report().alive==72 and army.report().unit_nodes<=96,army.report())
	# Force full-route endpoints with no opponents to exercise every lane/core.
	# Isolate one arrival per fixture; retaining overlapping endpoint units would
	# let unselected lanes arrive during an earlier fixture and invalidate it.
	var arrivals := 0
	var arrival_reports: Array = []
	for lane_id in range(3):
		army.reset()
		var selected = army.units.filter(func(u):return u.lane_id==lane_id and u.team=="sun")[0]
		for other in army.units.duplicate():
			if other != selected:
				army.units.erase(other)
				other.free()
		selected.progress = army.lanes[lane_id].length-.02
		selected.lateral = 0
		selected.position = army.route_sample(lane_id,selected.progress,"sun").position
		army.step_simulation(.05)
		arrivals += army.core_arrivals[lane_id]
		arrival_reports.append(army.report())
	record("all_three_lane_ends_damage_enemy_core",arrivals==3 and army.cores.moon<100 and army.cores.sun==100,{"lanes":arrival_reports})
	# Full deterministic soak; unassisted symmetric armies should remain bounded.
	army.reset()
	var bounded := true
	var finite := true
	var ticks := 0
	var started := Time.get_ticks_msec()
	for i in range(24000):
		army.step_simulation(.05)
		ticks += 1
		if i%200==0:
			var stats: Dictionary = army.report()
			bounded = bounded and stats.alive<=72 and stats.pending_cleanup<=24 and stats.unit_nodes<=96 and stats.queued_attacks<=72
			finite = finite and stats.finite
			await process_frame
	var soak: Dictionary = army.report()
	soak.ticks = ticks
	soak.wall_ms = Time.get_ticks_msec()-started
	record("20_minute_fixed_step_soak_bounded_finite",bounded and finite and ticks==24000 and army.elapsed>=1199.9,soak)
	record("all_three_lanes_meet_and_fight",soak.kills_by_lane[0]>0 and soak.kills_by_lane[1]>0 and soak.kills_by_lane[2]>0,soak)
	record("no_route_enters_static_blockers",soak.route_blocked_moves==0,{"blocked_moves":soak.route_blocked_moves})
	# Original articulated visual nodes on all roles, without a renderer claim.
	army.visual_enabled = true
	army.reset()
	var visual_finite := true
	var roles := {}
	for unit in army.units:
		unit.start_attack(unit.position+Vector3(0,0,3))
		for phase in [0.0,.1,.3,.5,4.0,1000.0]:
			unit.moved = .14
			unit.update_pose(phase,1.0)
			visual_finite = visual_finite and unit.articulation_finite()
		roles[unit.role] = unit.joints.size()
	record("all_original_role_articulations_finite",visual_finite and roles.size()==3,roles)
	army.free()
	await process_frame
	var source_same := true
	for path in source_hashes:source_same = source_same and source_hashes[path]==FileAccess.get_sha256(path)
	record("tested_source_unchanged",source_same,source_hashes)
	var passed := true
	for check in checks:passed = passed and check.passed
	var evidence := {"passed":passed,"checks":checks,"source_sha256":source_hashes,"engine":Engine.get_version_info().string,
		"scope":"Headless deterministic offline behavior, actual Node lifecycle and original procedural articulation; no renderer, hardware-FPS, online match or production art claim."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var file := FileAccess.open(argument.trim_prefix("--report="),FileAccess.WRITE)
			if file:file.store_string(JSON.stringify(evidence,"\t")+"\n")
	print("YUGA_LANE_ARMY_CASES ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
