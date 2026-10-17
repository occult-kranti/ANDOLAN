extends SceneTree
## Isolated relay geometry/state checks. No import, editor, renderer or packaging.
const Art = preload("res://scripts/relay_art.gd")
var checks: Array = []

func check_case(label: String, passed: bool, evidence = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})

func _initialize() -> void:
	call_deferred("run")

func geometry(node: Node3D, origin := Vector3.ZERO) -> Dictionary:
	var pending: Array = [node]
	var triangles := 0
	var finite := true
	var radius := 0.0
	var low := INF
	var high := -INF
	var extent := Vector2.ZERO
	var collisions := 0
	while not pending.is_empty():
		var child: Node = pending.pop_back()
		pending.append_array(child.get_children())
		if child is CollisionShape3D:collisions+=1
		if child is MeshInstance3D:
			var vertices: PackedVector3Array = child.mesh.get_faces()
			triangles += vertices.size()/3
			finite = finite and vertices.size()>0
			for vertex in vertices:
				var point: Vector3 = child.global_transform*vertex-origin
				finite = finite and point.is_finite()
				radius = maxf(radius,Vector2(point.x,point.z).length())
				extent.x = maxf(extent.x,absf(point.x))
				extent.y = maxf(extent.y,absf(point.z))
				low = minf(low,point.y)
				high = maxf(high,point.y)
	return {"triangles":triangles,"finite":finite,"radius":radius,"minimum_y":low,"maximum_y":high,"extent_x":extent.x,"extent_z":extent.y,"collision_shapes":collisions}

func segment_hits_box(a: Vector2, b: Vector2, box: Dictionary, margin: float) -> bool:
	var low := Vector2(box.position.x-box.size.x*.5-margin,box.position.z-box.size.z*.5-margin)
	var high := Vector2(box.position.x+box.size.x*.5+margin,box.position.z+box.size.z*.5+margin)
	var direction := b-a
	var entry := 0.0
	var leave := 1.0
	for axis in range(2):
		if absf(direction[axis])<.000001:
			if a[axis]<low[axis] or a[axis]>high[axis]:return false
		else:
			var near := (low[axis]-a[axis])/direction[axis]
			var far := (high[axis]-a[axis])/direction[axis]
			entry=maxf(entry,minf(near,far))
			leave=minf(leave,maxf(near,far))
			if entry>leave:return false
	return true

func normal_states() -> Array:
	return [{"id":0,"owner":"neutral","contested":false,"progress":0.0,"capture_team":"neutral"},{"id":1,"owner":"sun","contested":false,"progress":.5,"capture_team":"moon"},{"id":2,"owner":"moon","contested":true,"progress":1.0,"capture_team":"sun"}]

func run() -> void:
	var source := FileAccess.get_sha256("res://scripts/relay_art.gd")
	var owner := Node3D.new()
	root.add_child(owner)
	var art := Art.new()
	owner.add_child(art)
	check_case("setup_three_sites",art.setup(),art.report())
	var initial: Dictionary = art.report()
	check_case("bounded_resource_counts",initial.nodes<=300 and initial.mesh_instances<=200 and initial.materials<=16 and initial.cached_meshes<=40 and initial.static_bodies==3 and initial.collision_shapes==9,initial)
	for i in range(100):art.setup()
	var repeated: Dictionary = art.report()
	check_case("setup_idempotent_no_growth",repeated.nodes==initial.nodes and repeated.materials==initial.materials and repeated.cached_meshes==initial.cached_meshes)
	var boxes: Array = art.collision_boxes()
	var clear := boxes.size()==9
	for box in boxes:
		for lane_x in Art.SITE_X:
			clear = clear and absf(box.position.x-lane_x)-box.size.x*.5>4.0
	check_case("all_solid_boxes_outside_three_clear_lanes",clear,{"boxes":boxes})
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var route_clear := true
	var checked_routes := 0
	for route in manifest.lanes+manifest.rotations:
		var points: Array=route.points.duplicate(true)
		if route.get("closed",false):points.append(points[0])
		for i in range(points.size()-1):
			var a:=Vector2(points[i][0],points[i][2])
			var b:=Vector2(points[i+1][0],points[i+1][2])
			for box in boxes:route_clear=route_clear and not segment_hits_box(a,b,box,float(route.clear_half_width))
		checked_routes+=1
	check_case("canonical_lanes_and_rotation_corridors_clear",route_clear,{"routes":checked_routes,"manifest_sha256":FileAccess.get_sha256("res://assets/world/confluence-map.json")})
	var old_box: Dictionary=boxes[0].duplicate()
	old_box.position.z=0
	check_case("former_z0_plinth_counterexample_detected",segment_hits_box(Vector2(-54,0),Vector2(54,0),old_box,2.0))
	var matching := true
	for shape in art._solid_shapes:
		var visual: MeshInstance3D = art.get_node(shape.get_meta("matching_visual"))
		matching = matching and shape.shape is BoxShape3D and visual.mesh is BoxMesh and shape.shape.size.is_equal_approx(visual.mesh.size) and shape.global_transform.is_equal_approx(visual.global_transform) and shape.get_parent().collision_layer==1 and shape.get_parent().collision_mask==0
	check_case("every_collider_matches_visible_plinth_step",matching)
	var measurements := {}
	var total_triangles := 0
	for id in range(3):
		var site: Dictionary = art._sites[id]
		var ground := geometry(site.ground,Vector3(Art.SITE_X[id],0,0))
		check_case("site%d_flat_radius5_non_solid_tiles"%id,ground.finite and ground.radius<=5 and ground.minimum_y>=0 and ground.maximum_y<=.05 and ground.collision_shapes==0,ground)
		var bounded := true
		for frame in range(20):
			art._elapsed = float(frame)*2.5
			art._animate()
			var sample := geometry(site.station,Vector3(Art.STATION_X[id],0,Art.STATION_Z))
			bounded = bounded and sample.finite and sample.extent_x<=.751 and sample.extent_z<=.751 and sample.minimum_y>=-.001 and sample.maximum_y<=2.5
		measurements[Art.SITE_NAMES[id]]=geometry(site.station,Vector3(Art.STATION_X[id],0,Art.STATION_Z))
		check_case("site%d_rotating_station_within_plinth_footprint"%id,bounded,measurements[Art.SITE_NAMES[id]])
		total_triangles += measurements[Art.SITE_NAMES[id]].triangles+ground.triangles
	check_case("total_geometry_budget",total_triangles<=15000,{"triangles":total_triangles})
	check_case("state_assignment_valid",art.set_states(normal_states()))
	check_case("owner_symbol_stable_during_enemy_capture",art._sites[1].symbols.sun.visible and not art._sites[1].symbols.moon.visible and art._sites[1].progress[0].material_override==art._materials.progress_moon)
	check_case("contested_two_team_flags_are_steady",art._sites[2].flags.visible and not art._sites[1].flags.visible)
	var names := []
	for team in Art.OWNERS:names.append(art._owner_mesh(team).get_rid())
	check_case("ownership_has_three_distinct_geometry_symbols",names[0]!=names[1] and names[1]!=names[2] and names[0]!=names[2])
	var before: Array = art.report().states
	var rejected := true
	for key_value in [["progress",NAN],["progress",INF],["progress",-1],["progress",1.1],["progress",true],["contested",1],["owner","invalid"],["capture_team","invalid"],["id",3]]:
		var bad := normal_states()
		bad[0][key_value[0]]=key_value[1]
		rejected = rejected and not art.set_states(bad) and art.report().states==before
	var duplicates := normal_states()
	duplicates[0].id=1
	rejected = rejected and not art.set_states(duplicates) and not art.set_states([]) and not art.set_states([1,2,3]) and art.report().states==before
	check_case("invalid_states_rejected_atomically",rejected)
	var order := normal_states()
	order.reverse()
	check_case("state_ids_ignore_input_array_order",art.set_states(order) and art.report().states==before)
	for i in range(10000):
		var states := normal_states()
		states[0].progress=float(i%9)/8
		states[0].capture_team="sun" if i%2==0 else "moon"
		states[0].contested=i%3==0
		art.set_states(states)
		art.set_night_blend(float(i%2))
	var after: Dictionary=art.report()
	check_case("10000_state_updates_no_node_mesh_material_growth",after.nodes==initial.nodes and after.mesh_instances==initial.mesh_instances and after.materials==initial.materials and after.cached_meshes==initial.cached_meshes and after.finite,after)
	art.set_night_blend(1)
	var emission: float=art._materials.lantern.emission_energy_multiplier
	check_case("night_changes_existing_lantern_material_only",emission>1 and not art.set_night_blend(NAN) and is_equal_approx(emission,art._materials.lantern.emission_energy_multiplier))
	art.reset()
	check_case("reset_neutral_and_finite",art.report().states.all(func(state):return state.owner=="neutral" and state.progress==0 and not state.contested) and art.report().finite and is_zero_approx(art._elapsed))
	var start: float=art._elapsed
	owner.process_mode=Node.PROCESS_MODE_DISABLED
	art._process(.05)
	check_case("disabled_session_freezes_animation",is_equal_approx(art._elapsed,start))
	owner.process_mode=Node.PROCESS_MODE_INHERIT
	art.process_mode=Node.PROCESS_MODE_DISABLED
	art._process(.05)
	check_case("disabled_art_freezes_animation",is_equal_approx(art._elapsed,start))
	art.process_mode=Node.PROCESS_MODE_PAUSABLE
	paused=true
	art._process(.05)
	check_case("scene_pause_freezes_animation",is_equal_approx(art._elapsed,start))
	paused=false
	art._process(NAN)
	art._process(INF)
	art._process(-.1)
	check_case("nonfinite_negative_delta_ignored",is_equal_approx(art._elapsed,start))
	for i in range(72000):art._process(1.0/60)
	check_case("20_minute_animation_stress_finite_no_growth",art.report().finite and art.report().nodes==initial.nodes and absf(art._elapsed-1200)<.01,{"elapsed":art._elapsed,"calls":72000})
	await physics_frame
	await physics_frame
	var rays := true
	for x in Art.STATION_X:
		var query := PhysicsRayQueryParameters3D.create(Vector3(x,4,Art.STATION_Z),Vector3(x,-1,Art.STATION_Z),1)
		var hit: Dictionary = art.get_world_3d().direct_space_state.intersect_ray(query)
		rays = rays and not hit.is_empty() and hit.collider.is_in_group("relay_plinth") and absf(hit.position.y-.56)<.002
	check_case("actual_physics_rays_hit_visible_top_plinth",rays)
	check_case("source_unchanged_during_check",source==FileAccess.get_sha256("res://scripts/relay_art.gd"))
	var passed := checks.all(func(item):return item.passed)
	var report := {"passed":passed,"checks":checks,"source_sha256":source,"measurements":measurements,"scope":"Headless original relay geometry/state/physics checks; actual art, player-camera flow and hardware performance require separate integration review."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var file := FileAccess.open(argument.trim_prefix("--report="),FileAccess.WRITE)
			if file:file.store_string(JSON.stringify(report,"  ")+"\n")
	print("YUGA_RELAY_ART_CASES "+JSON.stringify({"passed":passed,"checks":checks.size()}))
	for item in checks:
		if not item.passed:print(JSON.stringify(item))
	owner.free()
	quit(0 if passed else 1)
