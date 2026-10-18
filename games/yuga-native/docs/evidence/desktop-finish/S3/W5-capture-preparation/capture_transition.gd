extends "res://tools/graphics-six/capture_focus.gd"
## Matched full transition take plus a separate120Hz landing diagnostic.
var capture_case:="full"
var physics_hz:=60
var capture_hz:=30
var landing_close:=false

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
		elif arg.begins_with("--case="):capture_case=arg.trim_prefix("--case=")
		else:finish("Unknown S3 capture argument "+arg);return
	if capture_case not in ["full","landing120"]:finish("Unknown transition case");return
	landing_close=capture_case=="landing120"
	physics_hz=120 if landing_close else 60;capture_hz=120 if landing_close else 30
	Engine.physics_ticks_per_second=physics_hz
	focus_case="desktop-s3-"+capture_case;mode=focus_case;context="courtyard";expected=40 if landing_close else 120
	contract={"camera":{"offset_m":[-4.5,2.8,-5.9],"target_m":[0,1.5,0],"fov_degrees":48},"inputs":["move_forward","move_back","move_left","move_right","jump","sprint","fire"],"preflight_bounds_frames":range(expected)}
	if landing_close:contract.camera={"offset_m":[-.85,.48,-1.1],"target_m":[0,.18,0],"fov_degrees":38}
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh absolute output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):finish("X11 Forward+ required");return
	if Engine.physics_ticks_per_second!=physics_hz:finish("Physics rate differs");return
	seed(741031);root.size=SIZE;root.content_scale_size=SIZE;root.msaa_3d=Viewport.MSAA_2X
	if not preflight:root.show()
	sources=source_hashes()
	var seal:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://.graphics-six-snapshot.json"))
	for name_ in seal.files:
		if sources["res://"+name_]!=seal.files[name_].sha256:finish("Snapshot differs "+name_);return
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene);current_scene=scene
	await draw(6);player=scene.player
	if not player.model_ready or not scene.environment_ready:finish("Actual hero/world missing");return
	review_camera=Camera3D.new();scene.add_child(review_camera);review_camera.near=.05;review_camera.far=180
	player.rama_motion.modification_processed.connect(observe_final_pose)
	for action_ in contract.inputs:Input.action_release(action_)
	scene.ui.hide();Input.mouse_mode=Input.MOUSE_MODE_VISIBLE;freeze_background_time();set_light(false)
	cache_geometry();cache_soles();follow_camera();review_camera.make_current()
	if not preflight:RenderingServer.frame_pre_draw.connect(follow_camera)
	await draw(34 if landing_close else 8)
	scene.rama_runtime.combat_event.connect(record_event)
	for index in expected:
		tape_index=index
		var edge:={}
		if index==0:
			scene.start_training();scene.ui.hide();scene.title_light.hide();edge={"kind":"start_training"}
		elif not landing_close and index==15:
			Input.action_press("move_forward",.65);edge={"kind":"press","action":"move_forward","strength":.65}
		elif not landing_close and index==30:
			Input.action_press("move_forward",1.0);edge={"kind":"press","action":"move_forward","strength":1.0}
		elif not landing_close and index==45:
			scene.reset_training();edge={"kind":"public_reset_while_moving"}
		elif not landing_close and index==65:
			Input.action_release("move_forward");edge={"kind":"release","action":"move_forward"}
		elif not landing_close and index==70:
			Input.action_press("jump");edge={"kind":"press","action":"jump"}
		elif not landing_close and index==71:
			Input.action_release("jump");edge={"kind":"release","action":"jump"}
		if not edge.is_empty():
			edge["frame"]=index;edge["physics_before"]=Engine.get_physics_frames();sequence_controls.append(edge)
		follow_camera();review_camera.make_current()
		await draw(1);motion_frame("frame-%03d"%index)
		if done:return
	for action_ in contract.inputs:Input.action_release(action_)
	var gaits:=[]
	for shot in shots:
		var gait:String=shot.final_modifier_body.motion.locomotion
		if gait not in gaits:gaits.append(gait)
	var adjacent:=true;var draw_adjacent:=true
	for index in range(1,shots.size()):
		adjacent=adjacent and shots[index].final_modifier_body.physics_frame-shots[index-1].final_modifier_body.physics_frame==physics_hz/capture_hz
		if not preflight:draw_adjacent=draw_adjacent and shots[index].render_frame-shots[index-1].render_frame==1
	capture_checks=[{"name":"all declared consecutive final-modifier observations","passed":shots.size()==expected,"expected":expected},
		{"name":"callback body and actual sole sample share physics counter","passed":shots.all(func(s):return s.final_modifier_body.physics_frame==s.sole_contacts.physics_frame)},
		{"name":"actual physics step matches capture cadence","passed":adjacent,"physics_hz":physics_hz,"capture_hz":capture_hz},
		{"name":"every actual render is adjacent","passed":draw_adjacent,"scope":"not applicable to headless preflight" if preflight else "draw counter increments exactly one"},
		{"name":"same declared camera active and required geometry framed","passed":shots.all(func(s):return s.actual_camera_identity.matches_requested and s.bounds.passed)},
		{"name":"landing actually occurs","passed":"land" in gaits,"gaits":gaits}]
	if not landing_close:
		capture_checks.append({"name":"walk and run actually occur","passed":"walk" in gaits and "run" in gaits,"gaits":gaits})
		capture_checks.append({"name":"one jump after declared reset and grounded final frame","passed":shots[-1].final_modifier_body.jump_count==1 and shots[-1].final_modifier_body.on_floor})
	finish("")

func source_hashes() -> Dictionary:
	var result:Dictionary=super.source_hashes()
	result[get_script().resource_path]=FileAccess.get_sha256(get_script().resource_path)
	return result

func finish(failure:String) -> void:
	if done:return
	done=true
	var after:=source_hashes() if not sources.is_empty() else {}
	var passed:bool=failure.is_empty() and sources==after and shots.size()==expected and capture_checks.all(func(c):return c.passed)
	var report:={"task":"desktop-S3-W5 optional matched transition tape","complete":passed,"failure":failure,"shots":shots,"checks":capture_checks,"sequence_controls":sequence_controls,"ability_events":events,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"sole_selection":sole_selection,"time_controls":time_controls,"expected_raw_pngs":0 if preflight else expected,"bone_names":[],"physics_hz":physics_hz,"fixed_capture_hz":capture_hz,"case":capture_case,"camera_contract":contract.get("camera",{}),"godot":Engine.get_version_info(),"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"scope":"Public start/reset and declared Input strengths only; no root, pose, action clock or anchor assignment.Full120-frame30Hz/60physics take OR separate40-frame120Hz/120physics landing close view after matched40-tick title preroll. The close view intentionally crops the upper body; it supplements the full take. Projection does not prove a difference visibly resolved. This does not observe earliest title acquisition or native physical-device input. Geometry/preflight gates do not approve visual quality."}
	if is_instance_valid(player):
		for index in player.rama_motion.rig.get_bone_count():report.bone_names.append(player.rama_motion.rig.get_bone_name(index))
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output):FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("S3_TRANSITION_CAPTURE_COMPLETE ",passed," ",failure)
	paused=false
	if is_instance_valid(scene):scene.queue_free()
	for unused in 3:await process_frame
	quit(0 if passed else 1)

func draw(count:int) -> void:
	for unused in count:
		if preflight:
			for tick in int(physics_hz/capture_hz):await physics_frame
			await process_frame
			if is_instance_valid(player):follow_camera()
		else:
			await process_frame;await RenderingServer.frame_post_draw

func body_state() -> Dictionary:
	var result:Dictionary=super.body_state()
	result["kit_report"]=normal(scene.rama_runtime.kit.report())
	result["army_elapsed"]=scene.practice_army.elapsed
	result["transition_age"]=player.rama_motion.transition_age
	result["transition_duration"]=player.rama_motion.transition_duration
	return result

func projected_soles(contacts:Dictionary) -> Dictionary:
	var low:=Vector2(INF,INF);var high:=-low;var behind:=0;var count:=0
	for part_index in sole_parts.size():
		var item:Dictionary=sole_parts[part_index];var part:Dictionary=item.part
		if not final_sole_parts[part_index].visible:continue
		var transforms:Array[Transform3D]=[]
		for bind in part.binds:transforms.append(posed_globals[bind.bone]*bind.inverse)
		for selected in item.selected:
			var index:int=selected.index;var rest:Vector3=part.vertices[index];var point:=rest
			for shape in part.shapes.size():
				var delta:Vector3=part.shapes[shape][Mesh.ARRAY_VERTEX][index]
				if part.shape_mode==Mesh.BLEND_SHAPE_MODE_NORMALIZED:delta-=rest
				point+=delta*part.node.get_blend_shape_value(shape)
			var posed:=Vector3.ZERO
			for slot in item.slots:posed+=(transforms[part.bones[index*item.slots+slot]]*point)*part.weights[index*item.slots+slot]
			var mask:float=clampf(part.colors[index].a,0,1) if part.colors!=null else 0.0
			posed+=Vector3(final_sole_parts[part_index].secondary)*mask*mask
			var world:Vector3=final_rig*posed;var screen:Vector2=review_camera.unproject_position(world)
			low=low.min(screen);high=high.max(screen);count+=1
			if review_camera.is_position_behind(world):behind+=1
	var result:={"passed":count>0 and behind==0 and low.x>=24 and low.y>=24 and high.x<=SIZE.x-24 and high.y<=SIZE.y-24,"min":normal(low),"max":normal(high),"vertices":count,"behind":behind,"scope":"Actual visible foot/toe skin projection only; upper-body cropping is deliberate for landing120","sides":{}}
	for side in contacts.sides:
		var point:=v3(contacts.sides[side].lowest_world)
		var screen:Vector2=review_camera.unproject_position(point)
		var foot:int=player.rama_motion.rig.find_bone("foot."+side)
		var ankle:Vector3=final_rig*posed_globals[foot].origin
		result.sides[side]={"lowest_sole_px":normal(screen),"ankle_world":normal(ankle),"ankle_px":normal(review_camera.unproject_position(ankle)),"reference_2_435mm_vertical_px":screen.distance_to(review_camera.unproject_position(point+Vector3.UP*.002435))}
	return result

func motion_frame(id:String) -> void:
	if root.get_camera_3d()!=review_camera:finish("Requested camera is not actual camera");return
	var contacts:=sole_contacts();var projection:=projected_soles(contacts)
	if landing_close:
		if not projection.passed:finish("Actual sole crop failed "+id);return
		if preflight:shots.append({"id":id,"physics_frame":Engine.get_physics_frames(),"render_frame":Engine.get_frames_drawn(),"camera":{"transform":normal(review_camera.global_transform),"fov":review_camera.fov},"viewport":[SIZE.x,SIZE.y]})
		else:write_frame(id,review_camera,"S3 matched120Hz landing close view, unmodified original framebuffer")
		if done:return
		var entry:Dictionary=shots[-1]
		entry["bounds"]=projection;entry["tape_index"]=tape_index;entry["final_modifier_body"]=final_body.duplicate(true)
		entry["draw_observed_body"]=body_state();entry["rendered_pose_globals"]=normal(posed_globals)
		entry["rendered_pose_pin"]=JSON.stringify(normal(posed_globals),"",true,true).sha256_text()
		entry["sole_contacts"]=contacts;entry["secondary"]=normal(player.rama_secondary.report());entry["action"]=action_state();entry["events_observed"]=events.size()
		entry["actual_camera_identity"]={"matches_requested":true,"path":str(review_camera.get_path())}
	else:super.motion_frame(id)
	if not done:
		shots[-1]["sole_projection"]=projection
		shots[-1]["physics_hz"]=Engine.physics_ticks_per_second
		shots[-1]["capture_hz"]=capture_hz
