extends SceneTree
## Independent solid-visual/physics comparison for the opt-in eight-metre pilot.
## It intentionally proves that restoring the old manifest AABB is observable.
const Builder = preload("res://scripts/traversal_landmarks.gd")
var checks: Array[Dictionary] = []
var triangles: Array = []
var report_path := ""

func _initialize() -> void:
	call_deferred("run")

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})

func visible_distance(from: Vector3, to: Vector3) -> float:
	var direction := (to-from).normalized()
	var closest := INF
	for triangle in triangles:
		var hit = Geometry3D.ray_intersects_triangle(from,direction,triangle[0],triangle[1],triangle[2])
		if hit != null:
			var distance_: float = (hit-from).dot(direction)
			if distance_ >= 0 and distance_ <= from.distance_to(to):
				closest = minf(closest,distance_)
	return closest

func physics_distance(space: PhysicsDirectSpaceState3D, from: Vector3, to: Vector3) -> float:
	var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(from,to,1))
	return INF if hit.is_empty() else from.distance_to(hit.position)

func mismatches(space: PhysicsDirectSpaceState3D, samples: Array) -> Array:
	var failed := []
	for sample in samples:
		var visual := visible_distance(sample[0],sample[1])
		var physical := physics_distance(space,sample[0],sample[1])
		if is_inf(visual) != is_inf(physical) or (not is_inf(visual) and absf(visual-physical) > .003):
			failed.append({"from":sample[0],"to":sample[1],"visual_distance":str(visual),"physics_distance":str(physical)})
	return failed

func mesh_signature(node: Node) -> String:
	var rows := []
	for child in node.get_children():
		if child is MeshInstance3D:
			var surfaces := []
			for index in child.mesh.get_surface_count():
				surfaces.append(child.mesh.surface_get_arrays(index))
			# Godot assigns globally advancing names to duplicate-named roof
			# embers; geometry identity does not depend on generated suffixes.
			rows.append([child.position,child.rotation,child.scale,surfaces])
	return var_to_bytes(rows).hex_encode().sha256_text()

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			report_path = arg.trim_prefix("--report=")
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var data: Dictionary = manifest.traversal
	var input_sha := JSON.stringify(data).sha256_text()
	var builder = Builder.new()
	var before := Node3D.new()
	root.add_child(before)
	builder.build(before,data)
	var candidate := Node3D.new()
	root.add_child(candidate)
	var candidate_report: Dictionary = builder.build(candidate,data,{"wind_court_pilot":true})
	var after := Node3D.new()
	root.add_child(after)
	var after_report: Dictionary = builder.build(after,data)
	check("builder reuse does not leak opt-in into next default call",not after_report.wind_court_pilot.enabled and mesh_signature(before.get_node("TraversalRelics/sun-lift-west")) == mesh_signature(after.get_node("TraversalRelics/sun-lift-west")))
	var target: Node3D = candidate.get_node("TraversalRelics/sun-lift-west")
	var origin := target.global_position
	var visual: MeshInstance3D = target.get_node("WindCourtNear")
	# Surface 1 is explicitly non-solid warm ornament. Compare independently
	# extracted actual ArrayMesh triangles for surfaces 0 and 2, not part boxes.
	for surface_index in [0,2]:
		var arrays := visual.mesh.surface_get_arrays(surface_index)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		for offset in range(0,indices.size(),3):
			triangles.append([visual.to_global(vertices[indices[offset]]),visual.to_global(vertices[indices[offset+1]]),visual.to_global(vertices[indices[offset+2]])])
	var samples := []
	for height in [.13,.71,1.08,1.24,1.48,3.13,6.34,6.62,6.81,7.14,7.37,7.73,8.08]:
		for along in [-3.93,-3.57,-3.21,-2.74,-2.03,-1.47,-1.03,-.17,.91,1.39,2.09,2.67,3.17,3.89]:
			for sign_ in [-1.0,1.0]:
				samples.append([origin+Vector3(sign_*6,height,along),origin+Vector3(0,height,along)])
				samples.append([origin+Vector3(along,height,sign_*6),origin+Vector3(along,height,0)])
	for x in [-4.03,-3.97,-3.78,-3.27,-1.07,.13,1.31,3.37,3.97,4.03]:
		for z in [-4.03,-3.97,-3.51,-1.09,.27,1.41,3.67,3.97,4.03]:
			samples.append([origin+Vector3(x,12,z),origin+Vector3(x,-1,z)])
	await physics_frame
	await physics_frame
	var space := target.get_world_3d().direct_space_state
	var normal_failures := mismatches(space,samples)
	check("solid visual triangle rays agree with actual detailed collider on four sides and roof",normal_failures.is_empty(),{"rays":samples.size(),"solid_triangles":triangles.size(),"mismatches":normal_failures})
	check("input manifest stays byte-equivalent as JSON",input_sha == JSON.stringify(data).sha256_text())
	var old_body := StaticBody3D.new()
	old_body.collision_layer = 1
	old_body.collision_mask = 0
	var old_shape := CollisionShape3D.new()
	var old_box := BoxShape3D.new()
	old_box.size = Vector3(8,8,8)
	old_shape.shape = old_box
	old_shape.position = Vector3(0,4,0)
	old_body.add_child(old_shape)
	target.add_child(old_body)
	await physics_frame
	await physics_frame
	var bad_sample := [[origin+Vector3(1.05,3.7,-6),origin+Vector3(1.05,3.7,0)]]
	var obsolete_failures := mismatches(space,bad_sample)
	check("negative control detects invisible obsolete manifest full box",obsolete_failures.size()==1,obsolete_failures)
	old_body.queue_free()
	await physics_frame
	await physics_frame
	check("removing obsolete full box restores visible recession",mismatches(space,bad_sample).is_empty())
	var passed := checks.all(func(item):return item.passed)
	var result := {"passed":passed,"checks":checks,"builder_sha256":FileAccess.get_sha256("res://scripts/traversal_landmarks.gd"),"review_probe_sha256":FileAccess.get_sha256(get_script().resource_path),"manifest_sha256":FileAccess.get_sha256("res://assets/world/confluence-map.json"),"pilot":candidate_report.wind_court_pilot,"scope":"Independent native opt-in fixture. Solid visual triangles compared to real physics, plus an obsolete-AABB negative control. Warm collars/band are deliberately non-solid decoration. No actual-image, full-world integration, traversal route, hardware or production-art acceptance."}
	if not report_path.is_empty():
		FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size(),"samples":samples.size()}))
	quit(0 if passed else 1)
