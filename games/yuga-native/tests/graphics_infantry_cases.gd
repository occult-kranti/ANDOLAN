extends SceneTree
## G1 geometry/resource/animation ownership checks; no rendered-quality claim.
const Art = preload("res://scripts/lane_infantry_art.gd")
const Unit = preload("res://scripts/lane_minion.gd")
var checks: Array = []
var measurements := {}

func _initialize() -> void:
	call_deferred("run")

func check_case(label: String, passed: bool, evidence = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})

func census(node: Node) -> Dictionary:
	var queue: Array = [node]
	var result := {"nodes":0,"meshes":0,"surfaces":0,"triangles":0,"finite":true,"minimum_y":INF,"maximum_y":-INF,"collisions":0}
	while not queue.is_empty():
		var child: Node = queue.pop_back()
		queue.append_array(child.get_children())
		result.nodes += 1
		if child is CollisionObject3D or child is CollisionShape3D: result.collisions += 1
		if child is Node3D: result.finite = result.finite and child.transform.is_finite()
		if child is MeshInstance3D:
			result.meshes += 1
			result.surfaces += child.mesh.get_surface_count()
			var vertices: PackedVector3Array = child.mesh.get_faces()
			result.triangles += vertices.size()/3
			for vertex in vertices:
				var point: Vector3 = child.global_transform*vertex
				result.finite = result.finite and point.is_finite()
				result.minimum_y = minf(result.minimum_y,point.y)
				result.maximum_y = maxf(result.maximum_y,point.y)
	return result

func signature(node: Node) -> String:
	var queue: Array = [node]
	var values: Array = []
	while not queue.is_empty():
		var child: Node = queue.pop_back()
		queue.append_array(child.get_children())
		if child is Node3D: values.append([str(child.transform),child.visible])
	return JSON.stringify(values)

func cache_counts() -> Array:
	return [Art.mesh_cache.size(),Art.material_cache.size(),Art.primitive_cache.size()]

func run() -> void:
	var source := {}
	for path in ["res://scripts/lane_infantry_art.gd","res://scripts/lane_minion.gd",get_script().resource_path]: source[path] = FileAccess.get_sha256(path)
	var entry_nodes := int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	for team in ["sun","moon"]:
		for role in Art.ROLES:
			var label: String = team+"_"+role
			var art: Dictionary = Art.build(team,role)
			root.add_child(art.root)
			var initial := census(art.root)
			measurements[label] = initial
			check_case(label+"_geometry_budget_and_no_collision",art.valid and initial.finite and initial.meshes<=24 and initial.surfaces<=65 and initial.triangles<=15000 and initial.collisions==0 and initial.minimum_y>=-.025 and initial.maximum_y<=3.0,initial)
			var caches := cache_counts()
			var moving := false
			var last := signature(art.root)
			var finite := true
			for tick in range(240):
				var time := float(tick)/60
				Art.pose(art,time,.14,maxf(0,.52-fmod(time,1.1)),.18 if tick%41==0 else 0,true,7)
				moving = moving or last != signature(art.root)
				if tick % 30 == 0: finite = finite and census(art.root).finite
			check_case(label+"_walk_attack_no_resource_growth",moving and finite and cache_counts()==caches and census(art.root).nodes==initial.nodes,{"cache_counts":caches})
			var root_before: Transform3D = art.root.transform
			Art.pose(art,2,.14,.31,0,true,7)
			var held := signature(art.root)
			for tick in range(120): Art.pose(art,2,.14,.31,0,true,7)
			check_case(label+"_repeated_army_clock_exactly_frozen",signature(art.root)==held and art.root.transform==root_before)
			for invalid in [NAN,INF,-INF]:
				Art.pose(art,invalid,.14,.31,0,true,7)
				Art.pose(art,2,invalid,.31,0,true,7)
				Art.pose(art,2,.14,invalid,0,true,7)
				Art.pose(art,2,.14,.31,invalid,true,7)
			check_case(label+"_nonfinite_input_atomic",signature(art.root)==held)
			if role == "bow_guard":
				var contact := true
				var tip_contact := true
				for remaining in [.52,.49,.46,.43,.401]:
					Art.pose(art,3,0,remaining,0,true,0)
					var weapon: Node3D = art.joints.weapon
					var draw_hand: Vector3 = weapon.global_transform.affine_inverse()*art.joints.right_hand.global_position
					for index in range(2):
						var cord: MeshInstance3D = art.joints.cords[index]
						var tip := Vector3(0,-.60 if index==0 else .60,-.05)
						tip_contact = tip_contact and (cord.transform*Vector3(0,-.5,0)).distance_to(tip)<.00001
						contact = contact and (cord.transform*Vector3(0,.5,0)).distance_to(draw_hand)<.00001
					contact = contact and art.joints.nock.position.distance_to(draw_hand)<.00001 and art.joints.nock.visible
				check_case(label+"_draw_hand_nock_and_both_cords_contact",contact and tip_contact)
				Art.pose(art,3,0,.40,0,true,0)
				check_case(label+"_nock_releases_before_fixed_bow_impact",not art.joints.nock.visible)
				Art.pose(art,3,0,.4,0,false,0)
				check_case(label+"_dead_archer_has_no_loaded_arrow",not art.joints.nock.visible)
			Art.pose(art,1e30,1e30,1e30,1e30,true,7)
			check_case(label+"_large_finite_inputs_bounded",census(art.root).finite and art.root.transform==root_before)
			Art.pose(art,0,0,0,0,true,7)
			var reset := signature(art.root)
			Art.pose(art,50,.14,.3,.1,false,7)
			Art.pose(art,0,0,0,0,true,7)
			check_case(label+"_rewind_recreates_exact_rest_pose",signature(art.root)==reset)
			art.root.free()
	var warm := cache_counts()
	var all_nodes: Array = []
	for index in range(96):
		var art := Art.build("sun" if index%2==0 else "moon",Art.ROLES[index%3])
		root.add_child(art.root)
		all_nodes.append(art.root)
	check_case("maximum_96_units_share_warmed_resources",cache_counts()==warm and warm[0]<=45 and warm[1]<=12 and warm[2]<=80,{"cache_counts":warm,"assemblies":all_nodes.size()})
	for node in all_nodes: node.free()
	check_case("all_96_assemblies_dispose_without_orphan_nodes",int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==entry_nodes)
	for invalid in [["other","spearman"],["sun","unknown"]]:
		var art := Art.build(invalid[0],invalid[1])
		check_case("invalid_build_"+str(invalid),not art.valid and art.root.get_child_count()==0 and cache_counts()==warm)
		art.root.free()
	# Real receiver integration: presentation sampling cannot change collision/rule state.
	for role in Art.ROLES:
		var unit = Unit.new()
		unit.setup(null,4,"moon",role,0)
		root.add_child(unit)
		var collision: Transform3D = unit.shape.transform
		var radius: float = unit.shape.shape.radius
		var health: float = unit.health
		var timing: float = unit.start_attack(Vector3(0,0,4))
		var state := [unit.health,unit.attack_time,unit.attack_cooldown,unit.state,unit.position,unit.collision_layer]
		for tick in range(60): unit.update_pose(float(tick)/60,.5)
		check_case(role+"_real_receiver_pose_preserves_rules_and_collider",state==[unit.health,unit.attack_time,unit.attack_cooldown,unit.state,unit.position,unit.collision_layer] and collision==unit.shape.transform and is_equal_approx(radius,.39) and health==Unit.STATS[role].health and timing==(.26 if role=="bow_guard" else .18) and unit.articulation_finite(),{"radius":radius,"height":unit.shape.shape.height,"health":health,"windup":timing,"finite":unit.articulation_finite()})
		unit.receive_damage(1000,"army")
		unit.dead_age=.8
		unit.update_pose(2,1)
		check_case(role+"_actual_death_receiver_and_art_disposal",not unit.alive and unit.collision_layer==0 and unit.articulation_finite())
		unit.free()
	var unchanged := true
	for path in source: unchanged = unchanged and source[path]==FileAccess.get_sha256(path)
	check_case("scoped_sources_unchanged_during_test",unchanged)
	var passed: bool = checks.all(func(row):return row.passed)
	var report := {"passed":passed,"passed_count":checks.filter(func(row):return row.passed).size(),"count":checks.size(),"checks":checks,"measurements":measurements,"cache_counts":cache_counts(),"source_sha256":source,"engine":Engine.get_version_info().string,"scope":"Headless actual geometry, shared-resource census, real receiver ownership and pose/weapon-contact checks. No final pixels, hardware FPS or collision/rule changes."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var file := FileAccess.open(argument.trim_prefix("--report="),FileAccess.WRITE)
			file.store_string(JSON.stringify(report,"  ")+"\n")
	print("G1_INFANTRY "+JSON.stringify({"passed":passed,"passed_count":report.passed_count,"count":checks.size(),"measurements":measurements,"caches":cache_counts()}))
	for row in checks:
		if not row.passed: print(JSON.stringify(row))
	quit(0 if passed else 1)
