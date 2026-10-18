extends "res://tools/graphics-six/capture_focus.gd"
## Optional S3 review overlay. Root owns snapshot, preflight and render execution.

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
		else:finish("Unknown S3 capture argument "+arg);return
	focus_case="desktop-s3-transition";mode=focus_case;context="courtyard";expected=120
	contract={"camera":{"offset_m":[-4.5,2.8,-5.9],"target_m":[0,1.5,0],"fov_degrees":48},"inputs":["move_forward","move_back","move_left","move_right","jump","sprint","fire"],"preflight_bounds_frames":range(expected)}
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh absolute output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):finish("X11 Forward+ required");return
	if Engine.physics_ticks_per_second!=60:finish("Requires60Hz physics");return
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
	await draw(8)
	scene.rama_runtime.combat_event.connect(record_event)
	for index in expected:
		tape_index=index
		var edge:={}
		if index==0:
			scene.start_training();scene.ui.hide();scene.title_light.hide();edge={"kind":"start_training"}
		elif index==15:
			Input.action_press("move_forward",.65);edge={"kind":"press","action":"move_forward","strength":.65}
		elif index==30:
			Input.action_press("move_forward",1.0);edge={"kind":"press","action":"move_forward","strength":1.0}
		elif index==45:
			scene.reset_training();edge={"kind":"public_reset_while_moving"}
		elif index==65:
			Input.action_release("move_forward");edge={"kind":"release","action":"move_forward"}
		elif index==70:
			Input.action_press("jump");edge={"kind":"press","action":"jump"}
		elif index==71:
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
	capture_checks=[{"name":"all120 consecutive final-modifier observations","passed":shots.size()==120},
		{"name":"callback body and actual sole sample share physics counter","passed":shots.all(func(s):return s.final_modifier_body.physics_frame==s.sole_contacts.physics_frame)},
		{"name":"same declared camera actually active and fullbody framed","passed":shots.all(func(s):return s.actual_camera_identity.matches_requested and s.bounds.passed)},
		{"name":"walk run and landing actually occur","passed":"walk" in gaits and "run" in gaits and "land" in gaits,"gaits":gaits},
		{"name":"one jump after declared reset and grounded final frame","passed":shots[-1].final_modifier_body.jump_count==1 and shots[-1].final_modifier_body.on_floor}]
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
	var report:={"task":"desktop-S3-W5 optional matched transition tape","complete":passed,"failure":failure,"shots":shots,"checks":capture_checks,"sequence_controls":sequence_controls,"ability_events":events,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"sole_selection":sole_selection,"time_controls":time_controls,"expected_raw_pngs":0 if preflight else expected,"bone_names":[],"physics_hz":60,"fixed_capture_hz":30,"scope":"Public start/reset and declared Input strengths only; no root, pose, action clock or anchor assignment.120 consecutive review-camera frames after settled title preroll. This does not observe earliest title acquisition or native physical-device input. Geometry/preflight gates do not approve visual quality."}
	if is_instance_valid(player):
		for index in player.rama_motion.rig.get_bone_count():report.bone_names.append(player.rama_motion.rig.get_bone_name(index))
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output):FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("S3_TRANSITION_CAPTURE_COMPLETE ",passed," ",failure)
	paused=false
	if is_instance_valid(scene):scene.queue_free()
	for unused in 3:await process_frame
	quit(0 if passed else 1)
