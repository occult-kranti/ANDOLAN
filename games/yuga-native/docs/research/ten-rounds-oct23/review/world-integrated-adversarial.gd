extends SceneTree
## Actual canonical scene assembly plus a deliberately restored obsolete AABB.
const Builder=preload("res://scripts/traversal_landmarks.gd")
var checks: Array=[]
var report_path:=""
var scene: Node3D
var player_capsule: CapsuleShape3D
func _initialize()->void:call_deferred("run")
func check(label: String, passed: bool, detail: Variant=null)->void:
	checks.append({"name":label,"passed":passed,"detail":detail})
func ray(space: PhysicsDirectSpaceState3D,from: Vector3,to: Vector3)->Dictionary:
	return space.intersect_ray(PhysicsRayQueryParameters3D.create(from,to,1))
func capsule(space: PhysicsDirectSpaceState3D,at: Vector3)->Array[Dictionary]:
	var query:=PhysicsShapeQueryParameters3D.new();query.shape=player_capsule;query.transform=Transform3D(Basis.IDENTITY,at);query.collision_mask=1
	return space.intersect_shape(query,8)
func settle()->void:
	await physics_frame
	await physics_frame
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene)
	await process_frame
	check("actual canonical world is ready",scene.world_ready)
	if not scene.world_ready:finish();return
	scene.set_paused(false)
	# Disable only callbacks that move state; never PROCESS_MODE_DISABLED on
	# the world, which would remove its physics bodies from the active space.
	scene.set_process(false);scene.set_physics_process(false)
	scene.player.active=false;scene.player.set_physics_process(false)
	scene.army.set_process(false);scene.army.set_physics_process(false)
	for child in scene.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:player_capsule=child.shape.duplicate()
	check("query duplicates the actual world player capsule dimensions",player_capsule!=null and is_equal_approx(player_capsule.radius,float(scene.manifest.bounds.hero_radius)),{"radius":player_capsule.radius if player_capsule else null,"height":player_capsule.height if player_capsule else null})
	if player_capsule==null:finish();return
	var pilot: Dictionary=scene.landmark_report.get("wind_court_pilot",{})
	check("canonical pilot declares completed detailed collision integration",pilot.get("enabled",false) and pilot.get("integrated_collision",false),pilot)
	var target: Node3D=scene.world.get_node_or_null("TraversalRelics/"+Builder.WIND_COURT_ID)
	var body: StaticBody3D=target.get_node_or_null("WindCourtDetailedCollision") if target else null
	check("exact obsolete manifest body is absent",not scene.world.has_node(Builder.WIND_COURT_COLLISION_ID))
	check("exactly eight native platforms remain",scene.native_platform_bodies.size()==8 and get_nodes_in_group("confluence_native_platform").size()==8)
	var expected_index:=-1
	for index in scene.manifest.traversal.native_collision_boxes.size():
		if scene.manifest.traversal.native_collision_boxes[index].id==Builder.WIND_COURT_COLLISION_ID:expected_index=index
	check("detailed body replaces original array slot",expected_index>=0 and body!=null and scene.native_platform_bodies[expected_index]==body)
	if body==null:finish();return
	check("detailed body owns thirty-six enabled box shapes",body.get_child_count()==36 and body.get_children().all(func(child):return child is CollisionShape3D and child.shape is BoxShape3D and not child.disabled))
	check("detailed body preserves native-only identity and collision layer",body.is_in_group("confluence_native_platform") and body.get_meta("native_only",false) and body.collision_layer==1 and body.get_meta("replaces_manifest_collision","")==Builder.WIND_COURT_COLLISION_ID)
	await settle()
	var space: PhysicsDirectSpaceState3D=scene.world.get_world_3d().direct_space_state
	var origin:=target.global_position
	var ray_errors:=[]
	for sign_ in [-1.0,1.0]:
		for axis in range(2):
			var from:=Vector3(sign_*6,3.7,1.05) if axis==0 else Vector3(1.05,3.7,sign_*6)
			var to:=Vector3(0,3.7,1.05) if axis==0 else Vector3(1.05,3.7,0)
			var hit:=ray(space,origin+from,origin+to)
			if hit.is_empty() or hit.collider!=body or absf(origin.distance_to(hit.position)-Vector3(3.32,3.7,1.05).length())>.003:
				ray_errors.append({"axis":axis,"sign":sign_,"hit":str(hit.get("position"))})
	check("full world four-sided rays see only actual recessed core",ray_errors.is_empty(),ray_errors)
	var roof_errors:=[]
	for x in [-3.97,-1.5,0.0,1.5,3.97]:
		for z in [-3.97,-1.5,0.0,1.5,3.97]:
			var hit:=ray(space,origin+Vector3(x,12,z),origin+Vector3(x,7,z))
			if hit.is_empty() or hit.collider!=body or absf(hit.position.y-origin.y-8)>.003:roof_errors.append([x,z])
	check("twenty-five canonical roof support rays stay exactly y8",roof_errors.is_empty(),roof_errors)
	# The world radius is 0.65 m (the builder's small isolated fixture uses0.35).
	# This actual-size capsule is clear of piers/core but intersects the former
	# invisible full box, even though its centre lies just outside the old face.
	var clear_at:=origin+Vector3(1.05,3.7,-4.01)
	check("actual player-sized capsule clears visible recessed facade",capsule(space,clear_at).is_empty())
	check("actual player-sized capsule collides at closed core surface",not capsule(space,origin+Vector3(1.05,3.7,-3.55)).is_empty())
	var obsolete:=StaticBody3D.new();obsolete.name="ReviewerObsoleteDeckNegativeControl";obsolete.collision_layer=1;obsolete.collision_mask=0
	var holder:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(8,8,8);holder.shape=box;obsolete.add_child(holder);obsolete.position=origin+Vector3(0,4,0);scene.world.add_child(obsolete)
	await settle()
	var bad_hit:=ray(space,origin+Vector3(1.05,3.7,-6),origin+Vector3(1.05,3.7,0))
	check("negative control identifies restored invisible full-box blocker",not bad_hit.is_empty() and bad_hit.collider==obsolete and absf(bad_hit.position.z-origin.z+4)<.003 and not capsule(space,clear_at).is_empty())
	obsolete.queue_free();await settle()
	var restored:=ray(space,origin+Vector3(1.05,3.7,-6),origin+Vector3(1.05,3.7,0))
	check("removing negative control restores canonical visible recession",not restored.is_empty() and restored.collider==body and absf(restored.position.z-origin.z+3.32)<.003 and capsule(space,clear_at).is_empty())
	finish()
func finish()->void:
	var passed:=checks.all(func(row):return row.passed)
	var result:={"passed":passed,"cases":checks.size(),"checks":checks,"source_sha256":{"world":FileAccess.get_sha256("res://scripts/confluence_world.gd"),"builder":FileAccess.get_sha256("res://scripts/traversal_landmarks.gd"),"manifest":FileAccess.get_sha256("res://assets/world/confluence-map.json"),"probe":FileAccess.get_sha256(get_script().resource_path)},"scope":"Actual canonical scene assembly/physics and obsolete-AABB counterexample. No actual-image, player-input traversal, online authority, art-quality or hardware-performance acceptance."}
	if not report_path.is_empty():
		var file:=FileAccess.open(report_path,FileAccess.WRITE)
		if file==null:
			push_error("Report path must be writable")
			if is_instance_valid(scene):scene.free()
			quit(2)
			return
		file.store_string(JSON.stringify(result,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"cases":checks.size()}))
	if is_instance_valid(scene):scene.free()
	quit(0 if passed else 1)
