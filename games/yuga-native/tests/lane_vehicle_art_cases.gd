extends SceneTree
## Isolated original vehicle art contract; no renderer or gameplay substitution.
const Art = preload("res://scripts/lane_vehicle_art.gd")
var checks: Array = []
var measurements: Dictionary = {}

func check_case(label: String, passed: bool, evidence = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})

func _initialize() -> void:
	call_deferred("run")

func collect(art: Dictionary) -> Dictionary:
	var pending: Array = [art.root]
	var finite := true
	var mesh_count := 0
	var triangles := 0
	var radius := 0.0
	var low := INF
	var high := -INF
	var nodes := 0
	var inverse: Transform3D = art.root.global_transform.affine_inverse()
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		nodes += 1
		pending.append_array(node.get_children())
		if node is Node3D:
			finite = finite and node.transform.is_finite()
		if node is MeshInstance3D:
			mesh_count += 1
			var points: PackedVector3Array = node.mesh.get_faces()
			triangles += points.size()/3
			for vertex in points:
				var point: Vector3 = inverse*node.global_transform*vertex
				finite = finite and point.is_finite()
				radius = maxf(radius,Vector2(point.x,point.z).length())
				low = minf(low,point.y)
				high = maxf(high,point.y)
	return {"finite":finite,"nodes":nodes,"meshes":mesh_count,"triangles":triangles,"radius":radius,"minimum_y":low,"maximum_y":high}

func signature(art: Dictionary) -> String:
	var values: Array = []
	var pending: Array = [art.root]
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		pending.append_array(node.get_children())
		if node is Node3D:values.append(str(node.transform))
	return "|".join(values)

func run() -> void:
	var source_hash := FileAccess.get_sha256("res://scripts/lane_vehicle_art.gd")
	for team in ["sun","moon"]:
		for role in Art.ROLES:
			var id: String = team+"_"+role
			var art: Dictionary = Art.build(team,role)
			root.add_child(art.root)
			var initial := collect(art)
			measurements[id] = initial.duplicate()
			var cap := .82 if role == "cannon_cart" else .88
			check_case(id+"_contract_and_budget",art.valid and art.joints.has("weapon") and art.joints.wheels.size()==4 and initial.finite and initial.meshes<=40 and initial.triangles<=7000 and initial.radius<=cap+.001 and initial.minimum_y>=-.001,initial)
			var max_radius: float = initial.radius
			var all_finite := true
			var stable_nodes := true
			for i in range(120):
				var time := float(i)/60
				var duration := 1.20 if role == "cannon_cart" else 1.0
				Art.pose(art,role,time,.15,maxf(0,duration-time),.18 if i%17==0 else 0,true,0)
				var sample := collect(art)
				all_finite = all_finite and sample.finite and sample.minimum_y>=-.001
				stable_nodes = stable_nodes and sample.nodes==initial.nodes and sample.meshes==initial.meshes
				max_radius = maxf(max_radius,sample.radius)
			check_case(id+"_motion_recoil_finite_bounded",all_finite and stable_nodes and max_radius<=cap+.005,{"maximum_radius":max_radius,"nodes":initial.nodes})
			if role == "royal_chariot":
				var attached := true
				for remaining in [1.0,.70,.46,.45,0.0]:
					Art.pose(art,role,2,0,remaining,0,true,0)
					for index in range(2):
						var cord: MeshInstance3D = art.joints.cords[index]
						var endpoint := cord.transform*Vector3(0,-.5,0)
						var tip := Vector3(-.64 if index == 0 else .64,0,.27)
						attached = attached and endpoint.distance_to(tip)<.00001
				check_case(id+"_draw_string_keeps_bow_tips_attached",attached)
			var angle: float = art.wheel_angle
			Art.pose(art,role,2.0,0,0,0,true,0)
			check_case(id+"_roll_visible_and_stop_stable",absf(angle)>.01 and is_equal_approx(angle,art.wheel_angle))
			var rest_z: float = art.weapon_rest.z
			var impact := .40 if role == "cannon_cart" else .45
			Art.pose(art,role,2.1,0,impact,0,true,0)
			check_case(id+"_recoil_at_impact",art.joints.weapon.position.z<rest_z-.08)
			Art.pose(art,role,2.4,0,0,0,true,0)
			check_case(id+"_recoil_returns_to_rest",art.joints.weapon.position.is_equal_approx(art.weapon_rest))
			var before := signature(art)
			for invalid in [NAN,INF,-INF]:
				Art.pose(art,role,invalid,0,0,0,true,0)
				Art.pose(art,role,2.4,invalid,0,0,true,0)
				Art.pose(art,role,2.4,0,invalid,0,true,0)
				Art.pose(art,role,2.4,0,0,invalid,true,0)
				Art.pose(art,role,2.4,0,0,0,false,invalid)
			check_case(id+"_nonfinite_inputs_atomic",signature(art)==before)
			Art.pose(art,role,3,0,0,0,false,1)
			var death := collect(art)
			check_case(id+"_contained_death",death.finite and death.nodes==initial.nodes and death.minimum_y>=-.001 and death.radius<=cap+.01 and art.joints.chassis.position.y<-.1,death)
			Art.pose(art,role,0,0,0,0,true,0)
			check_case(id+"_rewind_reset_restores_pose",art.joints.chassis.position.is_equal_approx(Vector3.ZERO) and art.joints.weapon.position.is_equal_approx(art.weapon_rest) and is_zero_approx(art.wheel_angle) and collect(art).finite)
			art.root.position = Vector3(4,5,6)
			art.root.rotation = Vector3(.1,.3,0)
			var root_transform: Transform3D = art.root.transform
			Art.pose(art,role,1e30,1e30,1e30,1e30,false,1e30)
			check_case(id+"_large_finite_input_and_root_ownership",collect(art).finite and art.root.transform.is_equal_approx(root_transform))
			art.root.free()
	for role in Art.ROLES:
		var a: Dictionary = Art.build("sun",role)
		var b: Dictionary = Art.build("sun",role)
		for i in range(1,61):Art.pose(a,role,float(i)/30,.15,0,0,true,0)
		for i in range(1,121):Art.pose(b,role,float(i)/60,.15,0,0,true,0)
		check_case(role+"_wheel_roll_30_vs60_hz",absf(a.wheel_angle-b.wheel_angle)<.00001)
		var frozen := signature(a)
		for i in range(120):Art.pose(a,role,2,.15,0,0,true,0)
		check_case(role+"_paused_clock_does_not_roll",signature(a)==frozen)
		a.root.free()
		b.root.free()
	for role in Art.ROLES:
		var art: Dictionary = Art.build("sun",role)
		root.add_child(art.root)
		var start_count := collect(art)
		var finite := true
		for i in range(72000):
			var time := float(i)/60
			var phase := fmod(time,60)
			var duration := 1.20 if role == "cannon_cart" else 1.0
			var cooldown := 4.0 if role == "cannon_cart" else 2.6
			Art.pose(art,role,time,.15,maxf(0,duration-fmod(time,cooldown)),0,phase<58,maxf(0,phase-58))
			if i%1200==0:
				var sample := collect(art)
				finite = finite and sample.finite and sample.nodes==start_count.nodes and sample.minimum_y>=-.001
		check_case(role+"_20_minute_pose_stress",finite,{"pose_calls":72000,"simulated_seconds":1200,"nodes":start_count.nodes})
		art.root.free()
	var meshes := Art.mesh_cache.size()
	var materials := Art.material_cache.size()
	for i in range(100):
		var art: Dictionary = Art.build("sun" if i%2==0 else "moon",Art.ROLES[i%2])
		art.root.free()
	check_case("repeated_builds_reuse_bounded_resources",meshes==Art.mesh_cache.size() and materials==Art.material_cache.size(),{"meshes":meshes,"materials":materials})
	var invalid: Dictionary = Art.build("sun","unknown")
	Art.pose(invalid,"unknown",1,0,0,0,true,0)
	check_case("unknown_role_is_inert",not invalid.valid and invalid.root.get_child_count()==0)
	invalid.root.free()
	var wrong_team: Dictionary = Art.build("unrecognised_team","cannon_cart")
	check_case("invalid_team_cannot_expand_material_cache",not wrong_team.valid and wrong_team.root.get_child_count()==0 and materials==Art.material_cache.size())
	wrong_team.root.free()
	check_case("source_unchanged_during_test",source_hash==FileAccess.get_sha256("res://scripts/lane_vehicle_art.gd"))
	var passed := true
	for item in checks:passed = passed and item.passed
	var report := {"schema":1,"passed":passed,"checks":checks,"measurements":measurements,"source_sha256":source_hash,"scope":"Original procedural vehicle geometry and pose checks; no rendered-quality or real-time performance claim"}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var file := FileAccess.open(argument.trim_prefix("--report="),FileAccess.WRITE)
			if file:file.store_string(JSON.stringify(report,"  ")+"\n")
	print("YUGA_LANE_VEHICLE_ART_CASES "+JSON.stringify({"passed":passed,"checks":checks.size()}))
	for item in checks:
		if not item.passed:print(JSON.stringify(item))
	quit(0 if passed else 1)
