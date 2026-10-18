extends "res://tools/visual-rounds/capture_groom.gd"
## R4: one uninterrupted accepted-runtime input tape; never writes a pose.
var sole_parts: Array = []
var sole_selection: Array = []
var final_body: Dictionary = {}
var final_sole_parts: Array = []
var final_rig := Transform3D.IDENTITY
var tape_index := -1
var cancelled_cast: Dictionary = {}
var capture_checks: Array = []

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg=="--preflight": preflight=true
		else: finish("Unknown motion argument "+arg); return
	mode="motion-continuity"; context="courtyard"
	contract=JSON.parse_string(FileAccess.get_file_as_string("res://tools/visual-rounds/motion_contract.json"))
	expected=int(contract.frames)
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"): finish("X11 Forward+ required"); return
	seed(741031); root.size=SIZE; root.content_scale_size=SIZE; root.msaa_3d=Viewport.MSAA_2X
	if not preflight: root.show()
	sources=source_hashes()
	var freeze: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://motion-freeze.json"))
	for path in freeze.runtime_and_imports:
		if sources["res://"+path]!=freeze.runtime_and_imports[path]:finish("Frozen source/cache changed "+path);return
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene);current_scene=scene
	await draw(6)
	player=scene.player
	if not player.model_ready or not scene.environment_ready: finish("Actual hero/world missing");return
	review_camera=Camera3D.new();scene.add_child(review_camera);review_camera.near=.05;review_camera.far=180
	player.rama_motion.modification_processed.connect(observe_final_pose)
	for action in contract.inputs:
		if not InputMap.has_action(action): finish("Missing actual input "+str(action));return
		Input.action_release(action)
	scene.reset_training();scene.start_training();scene.ui.hide();scene.title_light.hide()
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	freeze_background_time();set_light(false)
	cache_geometry();cache_soles()
	follow_camera();review_camera.make_current()
	if not preflight: RenderingServer.frame_pre_draw.connect(follow_camera)
	await draw(8)
	if not final_body.get("on_floor",false): finish("Initial real floor support missing");return
	scene.rama_runtime.combat_event.connect(record_event)
	sequence_controls.append({"frame":-1,"kind":"initial_reset_only","body":final_body.duplicate(true),"inputs_released":contract.inputs})
	for index in expected:
		tape_index=index
		for edge in contract.edges:
			if int(edge.frame)!=index: continue
			if edge.kind=="press": Input.action_press(edge.action)
			elif edge.kind=="release_input": Input.action_release(edge.action)
			sequence_controls.append(edge.duplicate(true))
		if index==int(contract.cast_frame):
			if not final_body.on_floor: finish("Cast before real jump landed");return
			cancelled_cast=scene.rama_runtime.cast_ability("piercing_dawn")
			sequence_controls.append({"frame":index,"kind":"cast","ability":"piercing_dawn","result":normal(cancelled_cast),"kit_time_s":scene.rama_runtime.kit.elapsed})
			if not cancelled_cast.get("accepted",false): finish("Actual Piercing cast refused");return
		if index==int(contract.cancel_frame):
			var before:=action_state()
			var result: bool=scene.rama_runtime.kit.cancel_windup("R4 moving cancel")
			sequence_controls.append({"frame":index,"kind":"cancel_windup","returned":result,"before":before,"immediate_after":action_state(),"cast":normal(cancelled_cast)})
			if not result: finish("Actual windup cancellation refused");return
		await draw(1)
		motion_frame("frame-%03d"%index)
		if done:return
	for action in contract.inputs:Input.action_release(action)
	paused=true
	verify_tape()
	finish("")

func follow_camera() -> void:
	if done or not is_instance_valid(player):return
	var anchor:=Vector3(player.global_position.x,0,player.global_position.z)
	review_camera.global_position=anchor+v3(contract.camera.offset_m)
	review_camera.look_at(anchor+v3(contract.camera.target_m))
	review_camera.fov=float(contract.camera.fov_degrees)
	review_camera.reset_physics_interpolation()

func ground_contact() -> Dictionary:
	return ray_contact(player.global_position)

func ray_contact(point: Vector3) -> Dictionary:
	var hit: Dictionary=scene.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(point+Vector3.UP*3,point-Vector3.UP*5,1,[player.get_rid()]))
	if hit.is_empty():return {"hit":false}
	return {"hit":true,"point":normal(hit.position),"normal":normal(hit.normal),"collider":String(hit.collider.name),"signed_point_clearance_m":(point-hit.position).dot(hit.normal)}

func action_state() -> Dictionary:
	var motion=player.rama_motion
	var warnings:=[]
	for node in scene.rama_runtime.effects.find_children("ExactSweepBoundary","MeshInstance3D",true,false):
		warnings.append({"visible":node.is_visible_in_tree(),"queued_for_deletion":node.is_queued_for_deletion(),"transform":normal(node.global_transform)})
	return {"stage":motion.action_stage,"action_fade_s":motion.action_fade,"cancelled_pose":motion.cancelled_pose,"nocked":motion.nocked,"nocked_node_visible":motion.nocked_arrow.visible if is_instance_valid(motion.nocked_arrow) else false,"rama_committed":player.rama_committed,"rama_action_locked":player.rama_action_locked,"runtime_action_time":player.action_time,"kit_time_s":scene.rama_runtime.kit.elapsed,"effects":normal(scene.rama_runtime.effects.report()),"warning_nodes":warnings}

func body_state() -> Dictionary:
	var contacts:=[]
	for index in player.get_slide_collision_count():
		var collision:=player.get_slide_collision(index);var collider:=collision.get_collider()
		contacts.append({"position":normal(collision.get_position()),"normal":normal(collision.get_normal()),"collider":str(collider.name) if is_instance_valid(collider) else "missing"})
	var capsules:=[]
	for child in player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:capsules.append({"transform":normal(child.global_transform),"radius":child.shape.radius,"height":child.shape.height})
	return {"physics_frame":Engine.get_physics_frames(),"process_frame":Engine.get_process_frames(),"player_transform":normal(player.global_transform),"rig_transform":normal(player.rama_motion.rig.global_transform),"velocity":normal(player.velocity),"on_floor":player.is_on_floor(),"floor_normal":normal(player.get_floor_normal()) if player.is_on_floor() else [],"ground_ray":ground_contact(),"slide_contacts":contacts,"capsules":capsules,"jump_count":player.jump_count,"traversal_mode":player.traversal.mode,"lod":normal(player.rama_lod.report()),"motion":normal(player.rama_motion.diagnostics()),"foot_targets_rig":normal(player.rama_motion.foot_targets),"action":action_state()}

func observe_final_pose() -> void:
	super.observe_final_pose()
	final_rig=player.rama_motion.rig.global_transform
	final_body=body_state()
	final_sole_parts.clear()
	for item in sole_parts:
		var material: Material=item.part.material
		var offset:=Vector3.ZERO
		if material is ShaderMaterial:
			var value: Variant=material.get_shader_parameter("secondary_offset")
			if value is Vector3:offset=value
		final_sole_parts.append({"visible":item.part.node.is_visible_in_tree(),"secondary":offset})

func cache_soles() -> void:
	var rig: Skeleton3D=player.rama_motion.rig
	for part in geometry:
		if part.binds.is_empty():continue
		var selected:=[];var counts:={"L":0,"R":0}
		var slots: int=part.bones.size()/part.vertices.size()
		for index in part.vertices.size():
			if part.vertices[index].y>=.30:continue
			var sums:={"L":0.0,"R":0.0}
			for slot in slots:
				var bind: int=part.bones[index*slots+slot]
				var name_: String=String(rig.get_bone_name(part.binds[bind].bone))
				if name_.begins_with("foot") or name_.begins_with("toe"):
					for side in ["L","R"]:
						if name_.ends_with("."+side):sums[side]+=part.weights[index*slots+slot]
			var side: String="L" if sums.L>.5 else "R" if sums.R>.5 else ""
			if side.is_empty():continue
			selected.append({"index":index,"side":side});counts[side]+=1
		if selected.is_empty():continue
		sole_parts.append({"part":part,"selected":selected,"slots":slots})
		sole_selection.append({"node":String(part.node.name),"surface":part.surface,"material":part.name,"selected":selected,"counts":counts,"blend_shapes":part.shapes.size()})

func sole_contacts() -> Dictionary:
	var points:={"L":[],"R":[]};var refs:={"L":[],"R":[]}
	for part_index in sole_parts.size():
		var item: Dictionary=sole_parts[part_index]
		var part: Dictionary=item.part
		if not final_sole_parts[part_index].visible:continue
		var transforms: Array[Transform3D]=[]
		for bind in part.binds:transforms.append(posed_globals[bind.bone]*bind.inverse)
		var secondary: Vector3=final_sole_parts[part_index].secondary
		for selected in item.selected:
			var index: int=selected.index;var rest: Vector3=part.vertices[index];var point:=rest
			for shape in part.shapes.size():
				var delta: Vector3=part.shapes[shape][Mesh.ARRAY_VERTEX][index]
				if part.shape_mode==Mesh.BLEND_SHAPE_MODE_NORMALIZED:delta-=rest
				point+=delta*part.node.get_blend_shape_value(shape)
			var posed:=Vector3.ZERO
			for slot in item.slots:posed+=(transforms[part.bones[index*item.slots+slot]]*point)*part.weights[index*item.slots+slot]
			var mask: float=clampf(part.colors[index].a,0,1) if part.colors!=null else 0.0
			posed+=secondary*mask*mask
			points[selected.side].append(final_rig*posed)
			refs[selected.side].append({"node":String(part.node.name),"surface":part.surface,"vertex":index})
	var result:={"physics_frame":last_pose_signal,"rig_transform":normal(final_rig),"sides":{}}
	for side in ["L","R"]:
		if points[side].is_empty():continue
		var lowest: Vector3=points[side][0]
		for point: Vector3 in points[side]:
			if point.y<lowest.y:lowest=point
		var ray:=ray_contact(lowest)
		var minimum:=INF;var maximum:=-INF;var minimum_index:=-1;var penetrating:=0
		if ray.hit:
			var origin:=v3(ray.point);var n:=v3(ray.normal)
			for index in points[side].size():
				var distance: float=(points[side][index]-origin).dot(n)
				if distance<minimum:minimum=distance;minimum_index=index
				maximum=maxf(maximum,distance)
				if distance<-.005:penetrating+=1
		result.sides[side]={"vertices":points[side].size(),"lowest_world":normal(lowest),"ground_ray":ray,"minimum_signed_m":minimum if ray.hit else null,"maximum_signed_m":maximum if ray.hit else null,"minimum_vertex":refs[side][minimum_index] if minimum_index>=0 else {},"vertices_below_minus5mm":penetrating,"locked":final_body.motion.foot_locks[side],"foot_target_rig":final_body.foot_targets_rig[side]}
	return result

func motion_frame(id: String) -> void:
	var bounds: Dictionary={"sampled":false}
	if not preflight or contract.preflight_bounds_frames.any(func(value):return int(value)==tape_index):
		bounds=imported_bounds(review_camera,"fullbody")
		if not bounds.passed:finish("Actual imported framing failed "+id+": "+str(bounds));return
	if preflight:
		shots.append({"id":id,"physics_frame":Engine.get_physics_frames(),"render_frame":Engine.get_frames_drawn(),"camera":{"transform":normal(review_camera.global_transform),"fov":review_camera.fov},"bounds":bounds})
	else:
		write_frame(id,review_camera,"R4 uninterrupted real-input motion tape; actual final modifier pose and coherent callback contact observation")
		if done:return
		shots[-1]["bounds"]=bounds
	var entry: Dictionary=shots[-1]
	entry["tape_index"]=tape_index;entry["final_modifier_body"]=final_body.duplicate(true)
	entry["draw_observed_body"]=body_state();entry["rendered_pose_globals"]=normal(posed_globals)
	entry["rendered_pose_pin"]=JSON.stringify(normal(posed_globals),"",true,true).sha256_text()
	entry["sole_contacts"]=sole_contacts();entry["secondary"]=normal(player.rama_secondary.report())
	entry["action"]=action_state();entry["events_observed"]=events.size()

func verify_tape() -> void:
	var airborne:=false;var maximum:=0.0;var minimum_vx:=0.0;var maximum_vx:=0.0;var framed:=0
	for shot in shots:
		airborne=airborne or not shot.final_modifier_body.on_floor
		minimum_vx=minf(minimum_vx,float(shot.final_modifier_body.velocity[0]));maximum_vx=maxf(maximum_vx,float(shot.final_modifier_body.velocity[0]))
		if shot.bounds.get("passed",false):framed+=1
		maximum=maxf(maximum,float(shot.final_modifier_body.player_transform[3][1]))
	var cancels:=0;var forbidden:=0
	for event in events:
		if event.cast_id!=cancelled_cast.cast_id or event.generation!=cancelled_cast.generation:continue
		if event.kind=="cancel":cancels+=1
		if event.kind in ["release","impact"]:forbidden+=1
	capture_checks=[{"name":"real jump airborne and landed","passed":airborne and maximum>1.4 and shots[-1].final_modifier_body.on_floor,"maximum_root_y_m":maximum},{"name":"cast-specific cancel and zero release/impact","passed":cancels==1 and forbidden==0,"cancel_events":cancels,"forbidden_events":forbidden},{"name":"callback body/pose/sole share physics frame","passed":shots.all(func(s):return s.final_modifier_body.physics_frame==s.sole_contacts.physics_frame)},{"name":"no reset inside tape","passed":sequence_controls.filter(func(c):return c.kind=="initial_reset_only").size()==1},{"name":"cancel presentation settled","passed":shots[-1].action.stage=="none" and not shots[-1].action.nocked}]

	capture_checks.append({"name":"required actual imported framing samples executed","passed":framed==(contract.preflight_bounds_frames.size() if preflight else expected),"sample_count":framed})
	capture_checks.append({"name":"real opposite horizontal velocities","passed":minimum_vx< -1 and maximum_vx>1,"minimum_vx":minimum_vx,"maximum_vx":maximum_vx})
	capture_checks.append({"name":"ordinary stops settled before next edge","passed":absf(shots[44].final_modifier_body.velocity[0])<.01 and absf(shots[89].final_modifier_body.velocity[0])<.01})
	capture_checks.append({"name":"real one-jump counter","passed":shots[-1].final_modifier_body.jump_count-shots[0].final_modifier_body.jump_count==1})

func draw(count: int) -> void:
	for index in count:
		if preflight:
			for tick in 2:await physics_frame
			if is_instance_valid(player):follow_camera()
		else:
			await process_frame;await RenderingServer.frame_post_draw

func source_hashes() -> Dictionary:
	var freeze: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://motion-freeze.json"))
	var result:={}
	for path in freeze.runtime_and_imports:result["res://"+path]=FileAccess.get_sha256("res://"+path)
	for path in ["motion-freeze.json","tools/visual-rounds/capture_motion.gd","tools/visual-rounds/motion_contract.json","tools/visual-rounds/run_motion.py"]:result["res://"+path]=FileAccess.get_sha256("res://"+path)
	return result

func finish(failure: String) -> void:
	if done:return
	done=true
	var after:=source_hashes() if not sources.is_empty() else {}
	var passed: bool=failure.is_empty() and sources==after and shots.size()==expected and capture_checks.all(func(c):return c.passed)
	var report:={"schema":1,"task":"R4-06","mode":mode,"complete":passed,"failure":failure,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"shots":shots,"ability_events":events,"sequence_controls":sequence_controls,"checks":capture_checks,"sole_selection":sole_selection,"bone_names":[],"time_controls":time_controls,"expected_raw_pngs":0 if preflight else expected,"clocks":{"fixed_capture_process_hz":30,"physics_hz":Engine.physics_ticks_per_second,"army_authority_hz":20,"hardware_fps_measured":false},"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"One uninterrupted accepted-source input tape. Contact uses coherent final-modifier callback pose+rig+body. Separate post-draw body preserves phase lead explicitly. Full original framebuffers only in actual Forward+ mode; no motion correction or FPS claim."}
	if is_instance_valid(player):
		for index in player.rama_motion.rig.get_bone_count():report.bone_names.append(String(player.rama_motion.rig.get_bone_name(index)))
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output):FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("MOTION_CAPTURE_COMPLETE ",passed," ",failure)
	paused=false
	if is_instance_valid(scene):scene.queue_free()
	for index in 3:await process_frame
	quit(0 if passed else 1)
