extends SceneTree
## Samples actual lane_minion vehicle dispatch, not a standalone art mock.
const Army = preload("res://scripts/lane_army.gd")
var checks: Array = []
var hashes: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func record(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	if not passed: push_error("SIEGE POSE FAILED: "+label)

func nodes(node: Node) -> Array:
	var result: Array = [node]
	for child in node.get_children(): result.append_array(nodes(child))
	return result

func snapshot(node: Node) -> Dictionary:
	var value := {}
	for child in nodes(node):
		if child is Node3D: value[str(node.get_path_to(child))] = child.transform
	return value

func run() -> void:
	for path in ["res://scripts/lane_army.gd","res://scripts/lane_minion.gd","res://scripts/lane_vehicle_art.gd","res://assets/world/confluence-map.json"]:
		hashes[path] = FileAccess.get_sha256(path)
	var army = Army.new()
	root.add_child(army)
	army.set_physics_process(false)
	var manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var ready: bool = army.configure(manifest,null) and army.start_siege_drill()
	record("actual_drill_constructs_both_team_vehicle_nodes",ready and army.units.size()==6)
	var vehicles: Array = army.units.filter(func(u): return u.role in ["cannon_cart","royal_chariot"])
	var emitted: Array = []
	army.siege_event.connect(func(event): emitted.append(event.duplicate(true)))
	for unit in vehicles:
		unit.set_process(false)
		var identity: String = unit.team+"/"+unit.role
		var descendants := nodes(unit)
		var original_ids: Array = descendants.map(func(n): return n.get_instance_id())
		var body_origin: Vector3 = unit.position
		var before_health: float = unit.health
		var expected_radius := .82 if unit.role=="cannon_cart" else .88
		record(identity+"_actual_collider_and_art_dispatch",unit.visual!=null and not unit.vehicle_art.is_empty() and unit.joints.has("wheels") and unit.joints.wheels.size()==4 and absf(unit.shape.shape.radius-expected_radius)<.000001 and unit.collision_layer==(4 if unit.team=="moon" else 0),{"radius":unit.shape.shape.radius,"node_count":descendants.size()})
		# Independent reference comes from the actual authored muzzle mesh / bolt
		# apex, including the actor heading and transformed parent coordinate space.
		var origin_error := 0.0
		for heading in [0.0,1.07,-2.6]:
			army.position = Vector3(13,2,-7)
			army.rotation.y = .35
			unit.heading = heading
			unit.previous_yaw = heading
			unit.previous_position = unit.position
			unit.moved = 0
			unit.attack_time = 0
			unit.update_pose(0,1)
			var reference_node: Node3D = unit.visual.find_child("DarkBore" if unit.role=="cannon_cart" else "BoltPoint",true,false)
			var reference_point: Vector3 = reference_node.global_position if unit.role=="cannon_cart" else reference_node.to_global(Vector3(0,.09,0))
			army._queue_siege_attack(unit,unit.position+Vector3(0,0,5),.8)
			origin_error = maxf(origin_error,reference_point.distance_to(emitted[-1].origin))
		record(identity+"_emitted_origin_matches_actual_authored_muzzle",origin_error<.00002,{"max_origin_error_m":origin_error,"headings_radians":[0,1.07,-2.6],"parent_translation":"(13,2,-7)","parent_yaw_radians":.35})
		army.position = Vector3.ZERO
		army.rotation = Vector3.ZERO
		unit.heading = 0
		unit.previous_yaw = 0
		army._attacks.clear()
		var duration: float = unit.start_attack(unit.position+Vector3(0,0,4))
		var initial_attack: float = unit.attack_time
		var finite := true
		var max_wheel_gap := 0.0
		var max_wheel_tilt := 0.0
		var max_recoil := 0.0
		var moved_wheel := false
		var previous_angle: float = unit.vehicle_art.wheel_angle
		var stationary_origin := true
		for i in range(601):
			var time := float(i)/60.0
			unit.moved = .14 if i<300 else 0.0
			unit.attack_time = maxf(0,initial_attack-time)
			unit.hit_time = .18 if i==90 else 0.0
			unit.previous_position = unit.position
			unit.previous_yaw = unit.heading
			unit.update_pose(time,1.0)
			for child in descendants:
				if child is Node3D: finite = finite and child.transform.is_finite() and absf(child.basis.determinant())>.000001
			stationary_origin = stationary_origin and unit.position==body_origin and unit.health==before_health
			max_recoil = maxf(max_recoil,absf(unit.joints.weapon.position.z-unit.vehicle_art.weapon_rest.z))
			moved_wheel = moved_wheel or not is_equal_approx(previous_angle,float(unit.vehicle_art.wheel_angle))
			previous_angle = unit.vehicle_art.wheel_angle
			for wheel in unit.joints.wheels:
				var local_transform: Transform3D = unit.visual.global_transform.affine_inverse()*wheel.global_transform
				var wheel_radius: float = .22 if unit.role=="cannon_cart" else .25
				max_wheel_gap = maxf(max_wheel_gap,absf(local_transform.origin.y-wheel_radius))
				max_wheel_tilt = maxf(max_wheel_tilt,absf(local_transform.basis.x.dot(Vector3.UP)))
		record(identity+"_601_actual_pose_samples_finite_planted_and_stationary",finite and stationary_origin and max_wheel_gap<.00002 and max_wheel_tilt<.00002,{"samples":601,"wheel_contact_center_error_m":max_wheel_gap,"wheel_axle_vertical_component":max_wheel_tilt})
		record(identity+"_walk_and_attack_drive_integrated_joints",duration>0 and moved_wheel and max_recoil>.05,{"windup_seconds":duration,"max_recoil_m":max_recoil})
		var before := snapshot(unit)
		unit.update_pose(NAN,1.0)
		unit.update_pose(INF,1.0)
		unit.update_pose(0,NAN)
		record(identity+"_invalid_sampler_time_is_atomic",before==snapshot(unit))
		# The production death path must disable the hostile collider while keeping
		# the whole carriage upright, rather than applying a human 85-degree fall.
		unit.receive_damage(1000,"army")
		unit.dead_age = .8
		unit.update_pose(11,1.0)
		var death_finite: bool = unit.articulation_finite()
		var ids_after: Array = nodes(unit).map(func(n): return n.get_instance_id())
		record(identity+"_death_dispatch_finite_no_new_nodes_or_human_roll",death_finite and not unit.alive and unit.collision_layer==0 and absf(unit.visual.rotation.z)<.001 and original_ids==ids_after,{"root_roll_radians":unit.visual.rotation.z,"nodes":ids_after.size()})
	army.reset()
	var reset_ok: bool = army.units.size()==30 and army.get_child_count()==30
	reset_ok = army.start_siege_drill() and reset_ok
	var new_vehicles: Array = army.units.filter(func(u): return u.role in ["cannon_cart","royal_chariot"])
	for unit in new_vehicles:
		unit.update_pose(0,1)
		reset_ok = reset_ok and unit.alive and unit.health==unit.max_health and unit.articulation_finite() and absf(unit.joints.weapon.position.z-unit.vehicle_art.weapon_rest.z)<.000001
	record("reset_rebuilds_clean_vehicle_pose_and_health",reset_ok and new_vehicles.size()==4)
	army.free()
	await process_frame
	var stable := true
	for path in hashes: stable = stable and hashes[path]==FileAccess.get_sha256(path)
	record("tested_sources_unchanged",stable,hashes)
	var passed := checks.all(func(c): return c.passed)
	var evidence := {"passed":passed,"checks":checks,"source_sha256":hashes,"engine":Engine.get_version_info().string,"scope":"Actual lane_minion collision/art dispatch, 601 sampled poses per role/team, wheel-axis/contact-center geometry, finite transforms, attack/death/reset lifecycle. No rendered-quality, animation beauty, hardware-performance or physical terrain suspension claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var path := arg.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path).get_base_dir())
			var file := FileAccess.open(path,FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(evidence,"\t")+"\n")
			else: passed = false
	print("YUGA_SIEGE_POSE_CASES ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
