extends SceneTree
## Independent real-scene Triad relay lifecycle, reward and physics checks.
## Fixed-step fixture isolation is explicit; no rendered/online claim.

class PhysicsDriver extends Node:
	signal finished
	var work: Callable
	var result: Variant
	func _physics_process(_delta: float) -> void:
		if work.is_valid():
			var task := work
			work = Callable()
			result = task.call()
			finished.emit()

const Unit = preload("res://scripts/lane_minion.gd")
var scene: Node3D
var driver: PhysicsDriver
var checks: Array = []
var hashes: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func record(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	print("RELAY_CASE ",label," ",passed)
	if not passed: push_error("RELAY INTEGRATION FAILED: "+label)

func frames(count_: int = 2) -> void:
	for _i in range(count_): await process_frame

func query(work: Callable) -> Variant:
	driver.work = work
	await driver.finished
	return driver.result

func ticks(count_: int, delta: float = .1) -> void:
	await query(func():
		for _i in range(count_): scene._step_relays(delta)
	)

func site(index: int = 1) -> Dictionary:
	return scene.relays.sites()[index]

func fresh() -> void:
	scene._restart_army()
	scene.player.set_physics_process(false)
	scene.army.set_physics_process(false)
	scene.set_physics_process(false)
	for unit in scene.army.units: unit.free()
	scene.army.units.clear()
	scene.army._attacks.clear()
	scene.player.position = Vector3(20,.05,0)
	scene.player.velocity = Vector3.ZERO
	await frames()

func troop(team: String, point: Vector3):
	var unit = Unit.new()
	unit.setup(scene.army,scene.army.next_id,team,"spearman",1)
	scene.army.next_id += 1
	unit.render_art = false
	unit.position = point
	unit.previous_position = point
	unit.defeated.connect(scene.army._on_defeated)
	scene.army.add_child(unit)
	scene.army.units.append(unit)
	return unit

func capture_solo() -> void:
	scene.player.position = Vector3(0,.05,0)
	await ticks(80)

func issue_receipt() -> Dictionary:
	# Deliberately separate issuance from application to challenge changes in
	# actor life, position and collision between those two production APIs.
	var result: Variant = await query(func():
		for _i in range(60):
			var step: Dictionary = scene.relays.control.step(.1,scene.relays._actors())
			if not step.support_requests.is_empty(): return step.support_requests[0]
		return {}
	)
	return result

func apply_receipt(request: Dictionary) -> Dictionary:
	var value: Variant = await query(func(): return scene.relays._apply_support(request))
	if not value is Dictionary: return {"accepted":false,"healed":0.0,"arrows":0,"malformed_result":true}
	return {"accepted":value.get("accepted",false),"healed":value.get("healed",0.0),"arrows":value.get("arrows",0),"malformed_result":not value.has("accepted")}

func count_nodes(node: Node) -> int:
	var total := 1
	for child in node.get_children(): total += count_nodes(child)
	return total

func gameplay_snapshot(value: Dictionary) -> Dictionary:
	# Neutral station ambience may continue in a drill. Capture clocks, every
	# supply counter, receipt state and last-event text must remain unchanged.
	var result := value.duplicate(true)
	result.erase("art")
	return result

func run() -> void:
	for path in ["res://scripts/confluence_world.gd","res://scripts/relay_session.gd","res://scripts/relay_control.gd","res://scripts/relay_art.gd","res://scripts/lane_army.gd","res://scripts/lane_minion.gd","res://scripts/player.gd","res://scripts/player_traversal.gd","res://assets/world/confluence-map.json","res://tools/test-relay-integration.gd"]:
		hashes[path] = FileAccess.get_sha256(path)
	root.size = Vector2i(1280,720)
	root.content_scale_size = root.size
	driver = PhysicsDriver.new()
	driver.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(driver)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	await frames(4)
	var ready: bool = scene.world_ready and scene.get("relays")!=null and scene.has_method("_step_relays")
	record("actual_world_initializes_three_relays",ready and scene.relays.sites().size()==3 and scene.army.units.size()==30)
	if not ready:
		await finish()
		return
	scene._set_volume(0.0,false)
	scene.set_physics_process(false)
	scene.player.set_physics_process(false)
	scene.army.set_physics_process(false)
	var initial_nodes := count_nodes(scene.relays)
	var initial_boxes: int = scene.army.boxes.size()
	await fresh()
	scene.player.position = Vector3(0,.05,0)
	await ticks(79)
	var before_capture := site()
	await ticks(1)
	record("solo_capture_requires_eight_seconds_and_no_immediate_supply",before_capture.owner=="neutral" and site().owner=="sun" and is_equal_approx(float(site().progress),8) and scene.relays.report().receipts_applied==0,{"before":before_capture,"after":site()})
	await fresh()
	var site_isolation := true
	var captured: Array = []
	for index in range(3):
		scene.player.position = Vector3([-40,0,40][index],.05,0)
		await ticks(80)
		for other in range(3):
			site_isolation = site_isolation and site(other).owner==("sun" if other<=index else "neutral")
		captured.append(scene.relays.sites())
	scene.player.ammo = 0
	await ticks(50)
	record("real_world_captures_all_three_sites_without_cross_site_rewards",site_isolation and scene.player.ammo==3 and scene.relays.report().arrows_total==3,{"stages":captured,"final":scene.relays.report()})
	# Capture contributions include real troop IDs, never duplicate list rows.
	await fresh()
	var ally = troop("sun",Vector3(0,0,0))
	for _i in range(4): scene.army.units.append(ally)
	await ticks(10)
	var dedup := site()
	while scene.army.units.size()>1: scene.army.units.pop_back()
	record("same_troop_reference_counts_once",absf(dedup.progress-1)<.00001 and dedup.contributors.sun==1,{"site":dedup,"intake":scene.relays.control.report().actors})
	var second = troop("sun",Vector3(1,0,0))
	var third = troop("sun",Vector3(-1,0,0))
	var corpse = troop("sun",Vector3(0,0,1))
	corpse.receive_damage(1000,"army")
	await ticks(10)
	record("more_troops_cap_at_two_and_dead_troops_do_not_contribute",absf(site().progress-3)<.00001 and site().contributors.sun==2,{"site":site()})
	var opponent = troop("moon",Vector3(0,0,-1))
	var contested_before: float = site().progress
	await ticks(100)
	record("both_teams_contest_without_progress_or_supply",site().contested and site().progress==contested_before and scene.relays.report().receipts_applied==0,{"site":site()})
	for unit in [ally,second,third,opponent]: unit.position = Vector3(20,0,20)
	await ticks(20)
	record("idle_partial_capture_decays",site().progress<contested_before and site().owner=="neutral",{"before":contested_before,"after":site()})
	await fresh()
	scene.player.position = Vector3(0,2.5001,0)
	await ticks(100)
	record("hero_above_capture_height_cannot_contribute",site().progress==0 and scene.relays.report().receipts_applied==0,{"site":site()})
	scene.player.position.y = 2.5
	await ticks(10)
	record("documented_low_hover_boundary_counts",absf(site().progress-1)<.00001,{"site":site(),"feet_height":2.5})
	await fresh()
	await capture_solo()
	scene.player.position = Vector3(20,.05,0)
	opponent = troop("moon",Vector3.ZERO)
	await ticks(79)
	var prior_neutralization := site()
	await ticks(1)
	var neutral := site()
	await ticks(79)
	var prior_takeover := site()
	await ticks(1)
	record("enemy_must_neutralize_before_capturing",prior_neutralization.owner=="sun" and neutral.owner=="neutral" and neutral.progress==0 and prior_takeover.owner=="neutral" and site().owner=="moon",{"neutral":neutral,"captured":site()})
	# Normal automatic delivery uses actual health/ammo and clamps both maxima.
	await fresh()
	await capture_solo()
	ally = troop("sun",Vector3(0,0,6))
	ally.health = ally.max_health-2
	scene.player.ammo = 11
	await ticks(49)
	var no_early: bool = ally.health==ally.max_health-2 and scene.player.ammo==11
	await ticks(1)
	record("five_second_supply_clamps_real_troop_health_and_hero_ammo",no_early and ally.health==ally.max_health and scene.player.ammo==12 and scene.relays.report().healing_total==2 and scene.relays.report().arrows_total==1,{"report":scene.relays.report()})
	ally.health -= 20
	scene.player.ammo = 0
	var request := await issue_receipt()
	var applied := await apply_receipt(request)
	var health_after: float = ally.health
	var ammo_after: int = scene.player.ammo
	var replayed := await apply_receipt(request)
	var unissued := request.duplicate(true)
	unissued.id = int(request.get("id",0))+100
	var rejected := await apply_receipt(unissued)
	record("issued_support_receipt_applies_once_and_unissued_rejects",not request.is_empty() and applied.accepted and applied.healed==6 and applied.arrows==3 and not replayed.accepted and not rejected.accepted and ally.health==health_after and scene.player.ammo==ammo_after,{"first":applied,"replay":replayed,"unissued":rejected})
	scene.relays.reset()
	var stale := await apply_receipt(request)
	record("reset_invalidates_previous_epoch_receipts",not stale.accepted and scene.player.ammo==ammo_after and ally.health==health_after,{"stale":stale})
	# Queued receipt revalidates life and position rather than trusting old rows.
	await fresh()
	await capture_solo()
	ally = troop("sun",Vector3(0,0,6))
	ally.health -= 20
	request = await issue_receipt()
	ally.receive_damage(1000,"army")
	scene.player.position = Vector3(20,.05,0)
	applied = await apply_receipt(request)
	record("dead_troop_cannot_be_healed_by_old_receipt",applied.accepted and applied.healed==0 and applied.arrows==0 and not ally.alive and ally.health==0,{"result":applied})
	await fresh()
	await capture_solo()
	ally = troop("sun",Vector3(0,0,6))
	ally.health -= 20
	request = await issue_receipt()
	ally.position = Vector3(0,0,8.01)
	scene.player.position = Vector3(0,2.501,0)
	health_after = ally.health
	applied = await apply_receipt(request)
	record("receipt_rechecks_current_range_and_flight_height",applied.accepted and applied.healed==0 and applied.arrows==0 and ally.health==health_after,{"result":applied})
	await fresh()
	await capture_solo()
	ally = troop("sun",Vector3(0,0,6))
	ally.health -= 20
	request = await issue_receipt()
	var wall := StaticBody3D.new()
	wall.collision_layer = 1
	wall.collision_mask = 0
	wall.position = Vector3(0,1.5,3)
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(4,3,.04)
	shape.shape = box
	wall.add_child(shape)
	scene.add_child(wall)
	scene.player.position = Vector3(20,.05,0)
	await frames(3)
	health_after = ally.health
	applied = await apply_receipt(request)
	var blocked: bool = await query(func(): return not scene.relays._line_clear(Vector3.ZERO,ally.position))
	record("new_four_centimetre_wall_blocks_supply_ray",blocked and applied.accepted and applied.healed==0 and ally.health==health_after,{"result":applied})
	wall.queue_free()
	await frames(3)
	request = await issue_receipt()
	applied = await apply_receipt(request)
	record("removing_wall_restores_next_valid_supply",applied.accepted and applied.healed==6 and ally.health==health_after+6,{"result":applied})
	# Malformed actor intake is transactional; restore fixture arrays immediately.
	await fresh()
	ally = troop("sun",Vector3.ZERO)
	var rules_before: Dictionary = scene.relays.control.report()
	for _i in range(97): scene.army.units.append(ally)
	await ticks(1)
	var rules_after: Dictionary = scene.relays.control.report()
	while scene.army.units.size()>1: scene.army.units.pop_back()
	record("oversize_actor_input_cannot_partially_capture_or_reward",rules_before==rules_after and scene.relays.report().receipts_applied==0)
	ally.health = NAN
	await ticks(10)
	record("nonfinite_troop_health_cannot_contribute",site().progress==0 and scene.relays.report().healing_total==0)
	ally.health = ally.max_health
	# Pause/overview/focus/outcome guard both the world scheduler and adapter.
	await fresh()
	await capture_solo()
	scene.player.ammo = 0
	await ticks(49)
	var freeze: Dictionary = scene.relays.report()
	scene.set_paused(true)
	await ticks(100)
	await query(func(): scene.relays.advance(.2))
	record("pause_freezes_capture_clock_and_due_supply",freeze==scene.relays.report() and scene.player.ammo==0)
	scene.set_paused(false)
	scene.set_overview(true)
	await ticks(100)
	await query(func(): scene.relays.advance(.2))
	record("overview_freezes_world_and_direct_adapter",freeze==scene.relays.report() and scene.player.ammo==0)
	scene.set_overview(false)
	scene._focus_lost()
	await ticks(100)
	record("focus_loss_stops_due_supply",scene.paused and freeze==scene.relays.report() and scene.player.ammo==0)
	scene.set_paused(false)
	await ticks(1)
	record("resume_awards_only_one_due_supply",scene.player.ammo==3 and scene.relays.report().receipts_applied==1,{"report":scene.relays.report()})
	scene.army.cores = {"sun":0.0,"moon":0.0}
	await query(func(): scene.army.step_simulation(.05))
	freeze = scene.relays.report()
	await ticks(100)
	await query(func(): scene.relays.advance(.2))
	scene._update_practice_hud()
	record("simultaneous_core_draw_stops_relays_and_has_draw_copy",scene.army.winner=="draw" and freeze==scene.relays.report() and scene.goal_label.text.begins_with("Draw") and not "wins" in scene.goal_label.text,{"text":scene.goal_label.text})
	scene._restart_army()
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	record("ordinary_restart_resets_relays_and_thirty_unit_round",scene.relays.sites().all(func(s): return s.owner=="neutral" and s.progress==0) and scene.army.units.size()==30 and scene.relays.report().healing_total==0 and scene.relays.report().arrows_total==0)
	var entered: bool = scene._start_siege_practice()
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	scene.player.position = Vector3.ZERO
	freeze = scene.relays.report()
	await ticks(100)
	await query(func(): scene.relays.advance(.2))
	var drill_after: Dictionary = scene.relays.report()
	record("siege_drill_leaves_relays_inactive",entered and scene.army.siege_drill and scene.army.units.size()==6 and gameplay_snapshot(freeze)==gameplay_snapshot(drill_after),{"before":gameplay_snapshot(freeze),"after":gameplay_snapshot(drill_after),"ambient_before":freeze.art.animation_seconds,"ambient_after":drill_after.art.animation_seconds})
	scene._restart_army()
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	# Rejected drill must leave the relay round untouched.
	var old_length: float = scene.army.lanes[1].length
	scene.army.lanes[1].length = 10
	freeze = scene.relays.report()
	var refused: bool = not scene._start_siege_practice()
	scene.army.lanes[1].length = old_length
	record("rejected_drill_keeps_existing_relay_state",refused and freeze==scene.relays.report())
	var bounded := true
	for _i in range(30):
		scene._restart_army()
		scene.army.set_physics_process(false)
		bounded = bounded and count_nodes(scene.relays)==initial_nodes and scene.army.boxes.size()==initial_boxes and get_nodes_in_group("relay_plinth").size()==3
	record("thirty_resets_do_not_accumulate_art_colliders_or_boxes",bounded,{"relay_nodes":count_nodes(scene.relays),"army_boxes":scene.army.boxes.size(),"plinths":get_nodes_in_group("relay_plinth").size()})
	await check_physics()
	await check_layout()
	await finish()

func check_physics() -> void:
	scene.player.set_physics_process(false)
	scene.army.set_physics_process(false)
	await frames(3)
	await query(func():
		var space := scene.get_world_3d().direct_space_state
		var physical := true
		var snapshots: Array = []
		for x in [-34.0,-6.0,34.0]:
			var ray := PhysicsRayQueryParameters3D.create(Vector3(x,3,4),Vector3(x,-.1,4),1)
			var hit := space.intersect_ray(ray)
			physical = physical and not hit.is_empty() and hit.collider.is_in_group("relay_plinth") and absf(hit.position.y-.56)<.0001
			snapshots.append({"station_x":x,"hit_y":hit.get("position",Vector3.ZERO).y})
			scene.player.position = Vector3(x-2,.05,4)
			physical = physical and scene.player.test_move(scene.player.global_transform,Vector3(4,0,0))
		record("three_real_plinths_stop_player_at_authored_geometry",physical and scene.player.collision_mask&1==1,{"hits":snapshots})
		var capsule := CapsuleShape3D.new()
		capsule.radius = .65
		capsule.height = 1.8
		var failures: Array = []
		var routes: Array = scene.manifest.lanes.duplicate()
		routes.append_array(scene.manifest.rotations)
		for lane in routes:
			var points: Array = lane.points.duplicate()
			if lane.get("closed",false): points.append(points[0])
			# A 0.65m-radius body centered at +/-1.35m reaches the edges
			# of the authored four-metre-wide clear floor corridor.
			for offset in [-1.35,0.0,1.35]:
				for i in range(points.size()-1):
					var a: Array = points[i]
					var b: Array = points[i+1]
					var from := Vector3(a[0],1.0,a[2])
					var to := Vector3(b[0],1.0,b[2])
					var direction := (to-from).normalized()
					var across: Vector3 = Vector3(direction.z,0,-direction.x)*offset
					from += across
					to += across
					var sweep := PhysicsShapeQueryParameters3D.new()
					sweep.shape = capsule
					sweep.transform = Transform3D(Basis.IDENTITY,from)
					sweep.motion = to-from
					sweep.collision_mask = 1
					var fraction := space.cast_motion(sweep)
					if fraction[0]<.99999: failures.append({"lane":lane.id,"offset":offset,"segment":i,"fraction":fraction[0]})
		record("all_lane_and_rotation_segments_preserve_four_metre_corridor",failures.is_empty(),{"failures":failures,"routes":routes.size(),"capsule_radius":.65,"perpendicular_center_offsets":[-1.35,0,1.35],"clear_floor_half_width":2.0})
		var sphere := SphereShape3D.new()
		sphere.radius = .18
		var sweep := PhysicsShapeQueryParameters3D.new()
		sweep.shape = sphere
		sweep.transform = Transform3D(Basis.IDENTITY,Vector3(-8,.3,4))
		sweep.motion = Vector3(4,0,0)
		sweep.collision_mask = scene.player.spring.collision_mask
		var fraction := space.cast_motion(sweep)
		record("camera_collision_mask_detects_plinth",fraction[0]<.8 and scene.player.spring.collision_mask&1==1,{"safe_fraction":fraction[0]})
		var matching := true
		var art_boxes: Array = scene.relays.art.collision_boxes()
		for expected in art_boxes:
			matching = matching and scene.army.boxes.any(func(b): return b.position.is_equal_approx(expected.position) and b.size.is_equal_approx(expected.size))
		record("all_nine_plinth_shapes_have_matching_army_geometry",art_boxes.size()==9 and matching,{"art_boxes":art_boxes.size(),"army_boxes":scene.army.boxes.size()})
	)

func check_layout() -> void:
	for size_ in [Vector2i(960,600),Vector2i(1280,720)]:
		root.size = size_
		root.content_scale_size = size_
		scene._update_practice_hud()
		await frames(5)
		var panel: Control = scene.ui.find_child("RelayStatus",true,false)
		var inside: bool = panel!=null and Rect2(Vector2.ZERO,Vector2(size_)).encloses(panel.get_global_rect())
		var labels_inside := true
		for label in scene.relay_labels:
			labels_inside = labels_inside and panel.get_global_rect().encloses(label.get_global_rect()) and label.text.length()>0
		record("relay_hud_fits_"+str(size_),inside and labels_inside,{"rect":str(panel.get_global_rect())})
		scene.set_paused(true)
		await frames(3)
		var reachable := true
		for action in scene.pause_actions:
			action.grab_focus()
			await frames(3)
			reachable = reachable and root.gui_get_focus_owner()==action and scene.pause_scroll.get_global_rect().grow(1).encloses(action.get_global_rect())
		record("all_pause_actions_scroll_into_view_"+str(size_),reachable and scene.pause_actions.size()==11,{"actions":scene.pause_actions.size()})
		scene.set_paused(false)

func finish() -> void:
	var same := true
	for path in hashes: same = same and hashes[path]==FileAccess.get_sha256(path)
	record("source_files_unchanged_during_run",same,hashes)
	paused = false
	if is_instance_valid(scene): scene.queue_free()
	if is_instance_valid(driver): driver.queue_free()
	await frames(3)
	OS.delay_msec(80)
	await frames()
	var passed := checks.all(func(c): return c.passed)
	var report := {"passed":passed,"checks":checks,"source_sha256":hashes,"engine":Engine.get_version_info().string,"scope":"Actual instantiated offline world, real army/player health/ammo, production fixed-step relay adapter, retained/delayed receipt fixtures, headless PhysicsServer rays/sweeps and logical UI focus/layout. Troops and time are explicitly isolated for deterministic counterexamples. No OS input, render/beauty, online authorization or hardware-performance claim."}
	var destination := "/tmp/yuga-triad-relay-integration.json"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): destination = argument.trim_prefix("--report=")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(destination).get_base_dir())
	var file := FileAccess.open(destination,FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(report,"\t")+"\n")
	else: passed = false
	print("YUGA_RELAY_INTEGRATION ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
