extends SceneTree
## Bounded primary-route / actual physics / atlas / overview parity.
## Predictive capsule sweeps are not a complete traversal or visual acceptance.
const MANIFEST := "res://assets/world/confluence-map.json"
var output := "/tmp/desktop-world-route-parity.json"
var checks: Array[Dictionary] = []
var observations: Dictionary = {}
var world: Node3D
var atlas: Control
var source_start: Dictionary = {}

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output=argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)

func frames(count:=10) -> void:
	for unused in count: await process_frame

func physics_flush() -> void:
	await physics_frame
	await process_frame
	await physics_frame
	await process_frame

func vec(value: Array) -> Vector3:
	return Vector3(value[0],value[1],value[2])

func ray(from: Vector3, to: Vector3) -> Dictionary:
	var query:=PhysicsRayQueryParameters3D.create(from,to,1,[world.player.get_rid()])
	return world.get_world_3d().direct_space_state.intersect_ray(query)

func ray_receipt(hit: Dictionary) -> Dictionary:
	if hit.is_empty(): return {"hit":false}
	return {"hit":true,"collider":String(hit.collider.name),"position":str(hit.position),"normal":str(hit.normal)}

func sweep(from: Vector3, to: Vector3) -> Dictionary:
	var collision:=KinematicCollision3D.new()
	var transform:Transform3D=world.player.global_transform
	transform.origin=from
	var blocked: bool=world.player.test_move(transform,to-from,collision,.001)
	if not blocked: return {"blocked":false}
	return {"blocked":true,"collider":collision.get_collider(),"position":collision.get_position(),"normal":collision.get_normal(),"travel":collision.get_travel()}

func sweep_receipt(result: Dictionary) -> Dictionary:
	if not result.blocked: return {"blocked":false}
	return {"blocked":true,"collider":String(result.collider.name),"position":str(result.position),"normal":str(result.normal),"travel":str(result.travel)}

func wall_edge_match() -> Dictionary:
	# Independent observed wall boundary, not body metadata or mesh AABB.
	var hit:=ray(Vector3(-35,1,-28),Vector3(-5,1,-28))
	if hit.is_empty(): return {"passed":false,"ray":ray_receipt(hit)}
	var footprint: Rect2=atlas._footprint(atlas.data.authority_collision_boxes[0])
	var projected: Vector2=atlas.project(hit.position)
	var valid: bool=hit.collider==world.authority_bodies[0] and absf(projected.x-footprint.position.x)<.001 and projected.y>=footprint.position.y and projected.y<=footprint.end.y
	return {"passed":valid,"ray":ray_receipt(hit),"map_west_edge":footprint.position.x,"projected_hit":str(projected)}

func run() -> void:
	root.size=Vector2i(1280,720)
	root.content_scale_size=Vector2i(1280,720)
	for path in [MANIFEST,"res://scripts/confluence_world.gd","res://scripts/world_atlas.gd","res://scripts/player.gd","res://scripts/player_traversal.gd",get_script().resource_path]: source_start[path]=FileAccess.get_sha256(path)
	world=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world);current_scene=world
	await frames(6)
	world.player.set_physics_process(false)
	world.army.set_physics_process(false)
	world.set_physics_process(false)
	# The live presentation process remains active. --fixed-fps60 makes the
	# ordinary .12s HUD refresh observable without manually invoking layout.
	atlas=world.map_control
	await physics_flush()
	var manifest_before:=JSON.stringify(world.manifest)
	var army_before: Dictionary=world.army.report()
	var capsule_radius:=-1.0
	for child in world.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D: capsule_radius=child.shape.radius
	check("queries use the actual configured native hero capsule",is_equal_approx(capsule_radius,float(world.manifest.bounds.hero_radius)),{"capsule_radius":capsule_radius})

	var paving: ShaderMaterial=world.world.get_node("FlatCityPaving").material_override
	var painted: PackedVector4Array=paving.get_shader_parameter("lane_segments")
	var lane_count: int=paving.get_shader_parameter("lane_count")
	var lane_segments:Array[Vector4]=[]
	for lane in atlas.data.lanes:
		for index in range(lane.points.size()-1):
			var a: Array=lane.points[index];var b: Array=lane.points[index+1]
			lane_segments.append(Vector4(a[0],a[2],b[0],b[2]))
	var primary_match:=lane_count==lane_segments.size() and lane_count<=painted.size()
	for index in mini(lane_count,lane_segments.size()): primary_match=primary_match and painted[index].is_equal_approx(lane_segments[index])
	check("actual paving primary segments agree with atlas lane data",primary_match,{"paving_count":lane_count,"atlas_primary_segments":lane_segments.size()})
	observations.secondary_routes={"painted_rotation_segments":paving.get_shader_parameter("rotation_count"),"scope":"Current atlas draws primary lanes only; this gate does not claim all painted rotation/circuit links appear on the atlas."}

	for fixture in [
		{"id":"temple-mid","lane":1,"from":Vector3(0,.05,-64),"to":Vector3(0,.05,-56),"floor":Vector3(0,0,-60)},
		{"id":"ghat-spawn-bend","lane":0,"from":Vector3(-34,.05,-91.6),"to":Vector3(-40,.05,-88),"floor":Vector3(-40,0,-88)},
		{"id":"metro-spawn-bend","lane":2,"from":Vector3(34,.05,-91.6),"to":Vector3(40,.05,-88),"floor":Vector3(40,0,-88)}]:
		var floor_hit:=ray(fixture.floor+Vector3.UP*3,fixture.floor-Vector3.UP)
		var motion:=sweep(fixture.from,fixture.to)
		var clear: bool=not motion.blocked and not floor_hit.is_empty() and floor_hit.collider==world.floor_body and absf(floor_hit.position.y)<.001
		check("sampled primary route has real floor and capsule clearance: "+fixture.id,clear,{"lane":fixture.lane,"from":str(fixture.from),"to":str(fixture.to),"floor":ray_receipt(floor_hit),"capsule":sweep_receipt(motion)})

	var baseline:=wall_edge_match()
	check("observed blocker west wall agrees with atlas footprint",baseline.passed,baseline)
	var wall_motion:=sweep(Vector3(-35,.05,-28),Vector3(-5,.05,-28))
	check("same wall actually blocks the hero capsule",wall_motion.blocked and wall_motion.collider==world.authority_bodies[0],sweep_receipt(wall_motion))

	# Counterexamples mutate only this disposable scene instance, then restore.
	# If the validator still passes, the gate is incapable of detecting drift.
	var body: StaticBody3D=world.authority_bodies[0]
	var original_layer:=body.collision_layer
	body.collision_layer=0
	await physics_flush()
	var missing_wall:=wall_edge_match()
	check("counterexample rejects a map wall whose actual collider is disabled",not missing_wall.passed,missing_wall)
	body.collision_layer=original_layer
	await physics_flush()
	check("restored real collider restores wall parity",wall_edge_match().passed)
	var original_data: Dictionary=atlas.data
	var displaced: Dictionary=original_data.duplicate(true)
	displaced.authority_collision_boxes[0].position[0]+=3
	atlas.data=displaced
	var misplaced:=wall_edge_match()
	check("counterexample rejects a three-metre atlas-only wall shift",not misplaced.passed,misplaced)
	atlas.data=original_data
	check("restored atlas data restores wall parity",wall_edge_match().passed)

	for deck_index in [0,7]:
		var entry: Dictionary=world.manifest.traversal.native_collision_boxes[deck_index]
		var base:=vec(entry.position);var size_:=vec(entry.size)
		var top:=base.y+size_.y
		var hit:=ray(Vector3(base.x,24,base.z),Vector3(base.x,-1,base.z))
		var landing:=sweep(Vector3(base.x,20,base.z),Vector3(base.x,-1,base.z))
		var at_street:=sweep(base+Vector3(-size_.x*.5-2,.05,0),base+Vector3(size_.x*.5+2,.05,0))
		var above_top:=sweep(base+Vector3(-size_.x*.5-2,top+.05-base.y,0),base+Vector3(size_.x*.5+2,top+.05-base.y,0))
		var footprint: Rect2=atlas._footprint(entry)
		var height_flattened: bool=atlas.project(base).is_equal_approx(atlas.project(Vector3(base.x,top,base.z)))
		var actual: bool=not hit.is_empty() and hit.collider==world.native_platform_bodies[deck_index] and absf(hit.position.y-top)<.001 and landing.blocked and landing.collider==world.native_platform_bodies[deck_index] and absf(landing.position.y-top)<.01 and at_street.blocked and at_street.collider==world.native_platform_bodies[deck_index] and not above_top.blocked and footprint.has_point(atlas.project(base)) and height_flattened
		check("deck footprint is XZ truth while street/top collisions differ: "+entry.id,actual,{"top_y":top,"ray":ray_receipt(hit),"landing_capsule":sweep_receipt(landing),"street_capsule":sweep_receipt(at_street),"above_top_capsule":sweep_receipt(above_top),"footprint":str(footprint),"XZ_projection_discards_height":height_flattened})

	var sky: Dictionary={}
	for anchor in world.manifest.traversal.anchors:
		if anchor.id=="temple-ring--44":sky=anchor
	var sky_position:=vec(sky.position)
	var sky_floor:=ray(sky_position+Vector3.UP*5,Vector3(sky_position.x,-1,sky_position.z))
	check("sky-ring marker does not invent a landing platform at ring height",sky.kind=="sky_ring" and not sky_floor.is_empty() and sky_floor.collider==world.floor_body and absf(sky_floor.position.y)<.001 and atlas.project(sky_position).is_equal_approx(atlas.project(Vector3(sky_position.x,0,sky_position.z))),{"ring_y":sky_position.y,"actual_surface":ray_receipt(sky_floor)})
	var apron:=ray(Vector3(90,5,0),Vector3(90,-1,0))
	check("visible terrain apron outside native floor is not counted as walkable",apron.is_empty(),{"sample":str(Vector3(90,0,0)),"actual_surface":ray_receipt(apron)})
	var clear_anchor:bool=world.player.traversal._clear_ray(Vector3(0,1.28,-112),Vector3(-20,12,-88))
	var occluded_anchor:bool=world.player.traversal._clear_ray(Vector3(-35,1.28,-28),sky_position)
	check("anchor marker does not bypass the real tether obstruction test",clear_anchor and not occluded_anchor,{"clear_spawn_to_landing_ring":clear_anchor,"blocked_street_to_sky_ring":not occluded_anchor})

	for fixture in [{"position":Vector3(0,.05,-112),"yaw":45.0},{"position":Vector3(54,10.05,88),"yaw":-45.0}]:
		world.teleport_to(fixture.position,fixture.yaw)
		await frames(12)
		var position_before: Vector3=world.player.global_position
		var point_before: Vector2=atlas.project(atlas.hero_position)
		var heading_before: Vector2=atlas.project_heading(atlas.hero_forward)
		var marker_correct: bool=atlas.hero_position.is_equal_approx(position_before) and point_before.is_equal_approx(atlas.project(position_before))
		world.set_overview(true)
		await frames(12)
		var held: bool=world.review_camera.current and world.player.global_position.is_equal_approx(position_before) and atlas.hero_position.is_equal_approx(position_before) and atlas.project(atlas.hero_position).is_equal_approx(point_before) and atlas.project_heading(atlas.hero_forward).is_equal_approx(heading_before)
		world.set_overview(false)
		await frames(12)
		check("actual live/overview camera switch preserves marker position and heading: "+str(fixture.position),marker_correct and held and world.player.camera.current and world.player.global_position.is_equal_approx(position_before) and atlas.project(atlas.hero_position).is_equal_approx(point_before),{"world_position":str(position_before),"map_point":str(point_before),"heading":str(heading_before)})

	var stable:bool=JSON.stringify(world.manifest)==manifest_before and atlas.data==original_data and world.army.report()==army_before
	for path in source_start:stable=stable and source_start[path]==FileAccess.get_sha256(path)
	check("fixture restores collision/map mutations and preserves source manifest army and files",stable and body.collision_layer==original_layer)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"observations":observations,"source_sha256":source_start,"physics_frames":Engine.get_physics_frames(),"scope":"Actual current native world/PhysicsSpace, configured hero predictive capsule sweeps, real ray hits, paving uniforms, atlas projection and live overview camera switch. Three short primary-route samples, one blocker, two decks, one sky ring and one visual apron point only. Two isolated scene-instance counterexamples are restored. XZ map footprints do not encode elevation, ramps, navmesh connectivity, all-terrain clearance, army elevation, browser/online authority or rendered art acceptance."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	current_scene=null;world.queue_free();await frames(8)
	quit(0 if result.passed else 1)
