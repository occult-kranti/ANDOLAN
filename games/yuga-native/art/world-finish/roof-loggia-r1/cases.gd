extends SceneTree
## Review-only geometry/query/live flight witness. No renderer/import invocation.
var checks: Array[Dictionary] = []
var world
var candidate
var output := "/tmp/yuga-roof-loggia-r1.json"
func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): output=argument.trim_prefix("--output=")
	call_deferred("run")
func check(label:String,passed:bool,detail:Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)
func frames(count:int) -> void:
	for unused in count: await physics_frame; await process_frame
func ray(from:Vector3,to:Vector3) -> Dictionary:
	return world.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from,to,1,[world.player.get_rid()]))
func hit_receipt(hit:Dictionary) -> Dictionary:
	return {"hit":false} if hit.is_empty() else {"hit":true,"collider":String(hit.collider.name),"position":str(hit.position),"normal":str(hit.normal)}
func flight(x:float) -> Dictionary:
	var player=world.player
	player.global_position=Vector3(x,15.25,-34.8)
	player.velocity=Vector3.ZERO
	player.yaw=PI
	player._update_camera()
	player.traversal.reset()
	var accepted:bool=player.toggle_flight()
	Input.action_press("move_forward")
	var observations:Array[Dictionary]=[]
	var contacts:Array[String]=[]
	var in_bay_samples:=0
	var bay_low_y:=INF
	for index in 110:
		await physics_frame; await process_frame
		if player.global_position.z>=-32.0 and player.global_position.z<=-24.0:
			in_bay_samples+=1
			bay_low_y=minf(bay_low_y,player.global_position.y)
		for collision_index in player.get_slide_collision_count():
			var collider=player.get_slide_collision(collision_index).get_collider()
			if is_instance_valid(collider) and not contacts.has(String(collider.name)): contacts.append(String(collider.name))
		if index%10==0: observations.append({"frame":index,"position":str(player.global_position),"mode":player.traversal.mode})
	Input.action_release("move_forward")
	var result:Dictionary={"accepted":accepted,"position":player.global_position,"mode":player.traversal.mode,"energy":player.traversal.energy,"observations":observations,"contacts":contacts,"in_bay_samples":in_bay_samples,"bay_low_y":bay_low_y if is_finite(bay_low_y) else null}
	player.cancel_traversal("review_trace_complete")
	return result
func stand(point:Vector3) -> Dictionary:
	var player=world.player
	player.global_position=point
	player.velocity=Vector3.ZERO
	player.traversal.reset()
	await frames(45)
	var contact_names:Array[String]=[]
	for index in player.get_slide_collision_count():
		var collider=player.get_slide_collision(index).get_collider()
		if is_instance_valid(collider): contact_names.append(String(collider.name))
	return {"position":str(player.global_position),"height":player.global_position.y,"on_floor":player.is_on_floor(),"contacts":contact_names}
func run() -> void:
	Engine.max_fps=60
	root.size=Vector2i(960,540)
	world=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world)
	await frames(4)
	check("actual_world_ready",world.world_ready and world.player.active)
	var from:=Vector3(18.084,16.2,-36)
	var to:=Vector3(18.084,16.2,-20)
	var before:=ray(from,to)
	check("counterexample_old_visual_roof_has_no_column_solid",before.is_empty(),hit_receipt(before))
	candidate=load("res://art/world-finish/roof-loggia-r1/candidate.gd")
	var result:Dictionary=candidate.configure(world.world)
	check("candidate_binds_exact_existing_target",result.get("ok",false),{"reason":result.get("reason","")})
	if not result.get("ok",false): await finish(); return
	await frames(3)
	var mesh:ArrayMesh=result.mesh.mesh
	var geometry_valid:=true
	var same_faces:=PackedVector3Array()
	var material_ids:Array[int]=[]
	for surface in mesh.get_surface_count():
		var arrays:=mesh.surface_get_arrays(surface)
		var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
		var tangents:PackedFloat32Array=arrays[Mesh.ARRAY_TANGENT]
		material_ids.append(mesh.surface_get_material(surface).get_instance_id())
		geometry_valid=geometry_valid and tangents.size()==vertices.size()*4 and normals.size()==vertices.size()
		for vertex in vertices:
			geometry_valid=geometry_valid and vertex.is_finite() and absf(vertex.x)<=6.841 and vertex.y>=-.001 and vertex.y<=2.801 and absf(vertex.z)<=6.841
		for normal in normals: geometry_valid=geometry_valid and normal.is_finite() and absf(normal.length()-1)<.001
		same_faces.append_array(vertices)
	var shape:ConcavePolygonShape3D=result.body.get_child(0).shape
	# Surface grouping changes triangle order. Compare ordered triangle keys as sets.
	var render_keys:Array[String]=[]
	var solid_keys:Array[String]=[]
	for vertices in [same_faces,shape.get_faces()]:
		var keys:Array[String]=[]
		for index in range(0,vertices.size(),3): keys.append(str(vertices[index])+str(vertices[index+1])+str(vertices[index+2]))
		keys.sort()
		if render_keys.is_empty(): render_keys=keys
		else: solid_keys=keys
	check("finite_envelope_normals_tangents_and_budget",geometry_valid and result.triangles<=900 and result.mesh_instances==1 and mesh.get_surface_count()==2,{"triangles":result.triangles,"surfaces":mesh.get_surface_count()})
	var roof_arrays:=mesh.surface_get_arrays(1)
	var roof_vertices:PackedVector3Array=roof_arrays[Mesh.ARRAY_VERTEX]
	var roof_normals:PackedVector3Array=roof_arrays[Mesh.ARRAY_NORMAL]
	var outward_cap:=true
	# Last12 triangles are the closed hipped cap, with an interior reference point.
	for index in range(roof_vertices.size()-36,roof_vertices.size(),3):
		var centroid:Vector3=(roof_vertices[index]+roof_vertices[index+1]+roof_vertices[index+2])/3.0
		outward_cap=outward_cap and roof_normals[index].dot(centroid-Vector3(0,2.632,0))>.001
	check("hipped_cap_normals_face_outward_on_all_twelve_triangles",outward_cap)
	check("collision_exactly_matches_all_visible_solid_triangles",render_keys==solid_keys and result.body.global_basis.get_scale().is_equal_approx(Vector3.ONE))
	check("material_resources_reused_without_new_maps_or_lights",material_ids==[result.materials[0].get_instance_id(),result.materials[1].get_instance_id()] and result.new_materials==0 and result.new_textures==0 and result.new_lights==0)
	var bay:=ray(Vector3(20,16.2,-36),Vector3(20,16.2,-20))
	var column:=ray(from,to)
	var beam:=ray(Vector3(20,17.30,-36),Vector3(20,17.30,-20))
	check("three_bay_centre_sightline_remains_open",bay.is_empty(),hit_receipt(bay))
	check("column_blocks_environment_aim_ray",not column.is_empty() and column.collider==result.body,hit_receipt(column))
	check("solid_eave_does_not_masquerade_as_open_space",not beam.is_empty() and beam.collider==result.body,hit_receipt(beam))
	check("actual_tether_occlusion_query_clear_bay_blocked_column",world.player.traversal._clear_ray(Vector3(20,16.2,-36),Vector3(20,16.2,-20)) and not world.player.traversal._clear_ray(from,to))
	var roof:=ray(Vector3(20,20,-28),Vector3(20,14,-28))
	var prior_roof:=ray(Vector3(28.4,20,-28),Vector3(28.4,14,-28))
	check("new_cap_support_is_visible_top_17_8m",not roof.is_empty() and roof.collider==result.body and absf(roof.position.y-17.8)<.002,hit_receipt(roof))
	check("existing_building_roof_support_15m_preserved",not prior_roof.is_empty() and prior_roof.collider!=result.body and absf(prior_roof.position.y-15)<.002,hit_receipt(prior_roof))
	var cap_stand:Dictionary=await stand(Vector3(20,18.2,-28))
	check("actual_character_lands_on_visible_cap",cap_stand.on_floor and absf(cap_stand.height-17.8)<.005 and cap_stand.contacts.has("LoggiaTruthfulSolid"),cap_stand)
	var old_roof_stand:Dictionary=await stand(Vector3(28.4,15.4,-28))
	check("actual_character_keeps_existing_roof_support",old_roof_stand.on_floor and absf(old_roof_stand.height-15)<.005 and not old_roof_stand.contacts.has("LoggiaTruthfulSolid"),old_roof_stand)
	var clear_flight:Dictionary=await flight(20)
	check("real_flight_move_and_slide_passes_open_bay",clear_flight.accepted and clear_flight.position.z>-23 and clear_flight.mode=="flight" and clear_flight.in_bay_samples>20 and clear_flight.bay_low_y>=14.99 and not clear_flight.contacts.has("LoggiaTruthfulSolid"),clear_flight)
	var blocked_flight:Dictionary=await flight(18.084)
	check("real_flight_stops_on_visible_column",blocked_flight.accepted and blocked_flight.position.z<-32.2 and blocked_flight.position.z>-34.7 and blocked_flight.mode=="flight" and blocked_flight.contacts.has("LoggiaTruthfulSolid") and blocked_flight.in_bay_samples==0,blocked_flight)
	var duplicate:Dictionary=candidate.configure(world.world)
	check("second_configure_refuses_duplicate_body",not duplicate.ok and duplicate.reason=="already_present")
	candidate.remove(world.world)
	await frames(3)
	check("removal_restores_visual_and_removes_collision",world.world.get_node(candidate.TARGET).visible and ray(from,to).is_empty())
	await finish()
func finish() -> void:
	Input.action_release("move_forward")
	var failures:=0
	for entry in checks:
		if not entry.passed: failures+=1
	var report:={"passed":checks.size()-failures,"total":checks.size(),"checks":checks,"scope":"One isolated review module: actual local3D environment ray/tether occlusion and staged live flight traces; not full combat damage/army elevation authority or pixels."}
	var file:=FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")+"\n")
	file.close()
	world.queue_free()
	await process_frame
	quit(0 if failures==0 else 1)
