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
var nominal_bounds: Array = []

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

func xy(value: Vector2) -> Array:
	return [value.x,value.y]

func xyz(value: Vector3) -> Array:
	return [value.x,value.y,value.z]

func mapping_snapshot(position_before: Vector3, facing_before: Vector3) -> Dictionary:
	# Expected values come from captured world-manifest bounds and the actual
	# authored visual's +Z facing, never from another atlas projection.
	var plot: Rect2=atlas._plot_rect()
	var point: Vector2=atlas.project(atlas.hero_position)
	var fraction: Vector2=(point-plot.position)/plot.size
	var span:=Vector2(float(nominal_bounds[1])-float(nominal_bounds[0]),float(nominal_bounds[3])-float(nominal_bounds[2]))
	var expected_fraction: Vector2=(Vector2(position_before.x,position_before.z)-Vector2(nominal_bounds[0],nominal_bounds[2]))/span
	var scale: Vector2=plot.size/span
	var expected_heading: Vector2=(Vector2(facing_before.x,facing_before.z)*scale).normalized()
	var heading: Vector2=atlas.project_heading(atlas.hero_forward)
	var diagonal:=Vector3(1,0,-1).normalized()
	var expected_diagonal: Vector2=(Vector2(diagonal.x,diagonal.z)*scale).normalized()
	var actual_diagonal: Vector2=atlas.project_heading(diagonal)
	return {
		"player_xyz":xyz(world.player.global_position),
		"world_root_forward_minus_z":xyz(-world.player.global_basis.z),
		"visual_forward_plus_z":xyz(world.player.visual.global_basis.z),
		"camera_forward_minus_z":xyz(-world.player.pivot.global_basis.z),
		"marker_xyz":xyz(atlas.hero_position),"marker_forward":xyz(atlas.hero_forward),
		"nominal_bounds":nominal_bounds.duplicate(),
		"plot_position":xy(plot.position),"plot_size":xy(plot.size),
		"local_point":xy(point),"normalized_point":xy(fraction),
		"expected_normalized_point":xy(expected_fraction),
		"heading":xy(heading),"expected_heading":xy(expected_heading),
		"diagonal_heading":xy(actual_diagonal),"expected_diagonal_heading":xy(expected_diagonal),
		"parent":String(atlas.get_parent().get_path()),
		"active_camera":String(root.get_camera_3d().get_path()),
		"terms":{
			"player_held":world.player.global_position==position_before,
			"visual_facing_held":world.player.visual.global_basis.z==facing_before,
			"marker_xyz_matches":atlas.hero_position==position_before,
			"marker_facing_matches":atlas.hero_forward==facing_before,
			"normalized_point_matches":fraction.is_equal_approx(expected_fraction),
			"heading_matches":heading.is_equal_approx(expected_heading),
			"diagonal_heading_matches":actual_diagonal.is_equal_approx(expected_diagonal),
			"manifest_bounds_unchanged":world.manifest.bounds.nominal_xz==nominal_bounds},
		"player_camera_current":world.player.camera.current,
		"review_camera_current":world.review_camera.current}

func mapping_valid(snapshot: Dictionary) -> bool:
	return snapshot.terms.values().all(func(value):return value==true)

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
	# A bounded process cap makes live .12s HUD refresh deterministic under
	# the ordinary headless test command, without an external fixed-fps flag.
	Engine.max_fps=60
	root.size=Vector2i(1280,720)
	root.content_scale_size=Vector2i(1280,720)
	for path in [MANIFEST,"res://scripts/confluence_world.gd","res://scripts/world_atlas.gd","res://scripts/player.gd","res://scripts/player_traversal.gd",get_script().resource_path]: source_start[path]=FileAccess.get_sha256(path)
	world=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world);current_scene=world
	await frames(6)
	world.player.set_physics_process(false)
	world.army.set_physics_process(false)
	world.set_physics_process(false)
	# The live presentation process remains active; the local frame cap lets
	# ordinary .12s HUD refresh run without manually invoking layout.
	atlas=world.map_control
	await physics_flush()
	var manifest_before:=JSON.stringify(world.manifest)
	nominal_bounds=world.manifest.bounds.nominal_xz.duplicate()
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

	observations.overview_mapping=[]
	for fixture in [{"position":Vector3(0,.05,-112),"yaw":45.0},{"position":Vector3(54,10.05,88),"yaw":-45.0}]:
		world.teleport_to(fixture.position,fixture.yaw)
		await frames(12)
		var position_before: Vector3=world.player.global_position
		var facing_before: Vector3=world.player.visual.global_basis.z
		var parent_before: Node=atlas.get_parent()
		var plot_before: Rect2=atlas._plot_rect()
		var point_before: Vector2=atlas.project(atlas.hero_position)
		var heading_before: Vector2=atlas.project_heading(atlas.hero_forward)
		var camera_before: Transform3D=world.player.camera.global_transform
		var before:=mapping_snapshot(position_before,facing_before)
		world.set_overview(true)
		await frames(12)
		var during:=mapping_snapshot(position_before,facing_before)
		var overview_terms:={
			"review_camera_active":root.get_camera_3d()==world.review_camera and world.review_camera.current and not world.player.camera.current,
			"map_in_guide":world.atlas_guide.is_ancestor_of(atlas) and atlas.get_parent()!=parent_before,
			"player_camera_transform_held":world.player.camera.global_transform==camera_before,
			"root_forward_held":during.world_root_forward_minus_z==before.world_root_forward_minus_z,
			"aspect_witness_changes_as_expected":during.diagonal_heading!=before.diagonal_heading and during.expected_diagonal_heading!=before.expected_diagonal_heading}

		# Mutate only this disposable map instance, synchronously. An awaited
		# live refresh could overwrite the corruption before it is observed.
		var marker_before: Vector3=atlas.hero_position
		var marker_facing_before: Vector3=atlas.hero_forward
		atlas.hero_position+=Vector3(.25,0,0)
		var corrupt_marker:=mapping_snapshot(position_before,facing_before)
		atlas.hero_position=marker_before
		check("counterexample rejects a 25cm marker-only shift: "+str(fixture.position),not mapping_valid(corrupt_marker) and not corrupt_marker.terms.normalized_point_matches,corrupt_marker)
		atlas.hero_forward=(marker_facing_before+Vector3(.1,0,0)).normalized()
		var corrupt_heading:=mapping_snapshot(position_before,facing_before)
		atlas.hero_forward=marker_facing_before
		check("counterexample rejects marker-only facing corruption: "+str(fixture.position),not mapping_valid(corrupt_heading) and not corrupt_heading.terms.heading_matches,corrupt_heading)
		var restored:=mapping_snapshot(position_before,facing_before)
		check("synchronous marker restoration recovers the same mapping: "+str(fixture.position),mapping_valid(restored) and atlas.hero_position==marker_before and atlas.hero_forward==marker_facing_before,restored)

		world.set_overview(false)
		await frames(12)
		var after:=mapping_snapshot(position_before,facing_before)
		var restoration_terms:={
			"same_live_parent":atlas.get_parent()==parent_before,
			"exact_plot_restored":atlas._plot_rect()==plot_before,
			"exact_raw_point_restored":atlas.project(atlas.hero_position)==point_before,
			"exact_heading_restored":atlas.project_heading(atlas.hero_forward)==heading_before,
			"same_player_camera_active":root.get_camera_3d()==world.player.camera and world.player.camera.current and not world.review_camera.current,
			"exact_player_camera_transform_restored":world.player.camera.global_transform==camera_before,
			"root_forward_held":after.world_root_forward_minus_z==before.world_root_forward_minus_z}
		var valid: bool=mapping_valid(before) and mapping_valid(during) and mapping_valid(after) and overview_terms.values().all(func(value):return value==true) and restoration_terms.values().all(func(value):return value==true)
		var detail:={"position":xyz(fixture.position),"teleport_facing_degrees":fixture.yaw,"before":before,"during":during,"after":after,"overview_terms":overview_terms,"restoration_terms":restoration_terms}
		observations.overview_mapping.append(detail)
		check("live/overview preserves manifest XZ and actual hero facing, then exactly restores live layout: "+str(fixture.position),valid,detail)

	var stable:bool=JSON.stringify(world.manifest)==manifest_before and atlas.data==original_data and world.army.report()==army_before
	for path in source_start:stable=stable and source_start[path]==FileAccess.get_sha256(path)
	check("fixture restores collision/map mutations and preserves source manifest army and files",stable and body.collision_layer==original_layer)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"observations":observations,"source_sha256":source_start,"physics_frames":Engine.get_physics_frames(),"scope":"Actual current native world/PhysicsSpace, configured hero predictive capsule sweeps, real ray hits, paving uniforms, atlas projection and live overview camera switch. Three short primary-route samples, one blocker, two decks, one sky ring and one visual apron point only. Two collision/map counterexamples and four marker/facing counterexamples are restored. Overview mapping expectations use captured manifest bounds and actual visual +Z facing; exact parent, pixels, plot, heading and player-camera restoration are required. XZ map footprints do not encode elevation, ramps, navmesh connectivity, all-terrain clearance, army elevation, browser/online authority or rendered art acceptance."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	current_scene=null;world.queue_free();await frames(8)
	# Fixed-fps headless frames are unthrottled; give the real audio mixer a
	# bounded disposal grace, as existing native HUD fixtures do.
	OS.delay_msec(80)
	await frames(2)
	quit(0 if result.passed else 1)
