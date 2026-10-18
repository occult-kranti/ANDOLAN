extends "res://tools/visual-rounds/capture_motion.gd"
## Two support anchors OR one 60-frame actual-runtime cast/cancel tape.
## Reuses the existing final-modifier observer, imported soles and projection gate.
var focus_case := "support"
var released_cast: Dictionary = {}
var focus_checkpoints: Array = []

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg.begins_with("--case="): focus_case=arg.trim_prefix("--case=")
		elif arg=="--preflight": preflight=true
		else: finish("Unknown focused capture argument "+arg);return
	if not focus_case in ["support","entry-cancel"]:finish("Unknown capture case");return
	mode="graphics-six-"+focus_case;context="courtyard"
	expected=2 if focus_case=="support" else 60
	contract={"camera":{"offset_m":[-3.5,1.75,-4.7],"target_m":[0,1.0,0],"fov_degrees":42},"inputs":["move_left","move_right","move_forward","move_back","jump","sprint","fire"],"preflight_bounds_frames":range(expected)}
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh absolute output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):finish("X11 Forward+ required");return
	if Engine.physics_ticks_per_second!=60:finish("Requires60Hz physics");return
	seed(741031);root.size=SIZE;root.content_scale_size=SIZE;root.msaa_3d=Viewport.MSAA_2X
	if not preflight:root.show()
	sources=source_hashes()
	var seal: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://.graphics-six-snapshot.json"))
	for name in seal.files:
		if sources["res://"+name]!=seal.files[name].sha256:finish("Snapshot differs "+name);return
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene);current_scene=scene
	focus_checkpoint("before_initial_draw6")
	await draw(6)
	focus_checkpoint("after_initial_draw6")
	player=scene.player
	if not player.model_ready or not scene.environment_ready:finish("Actual hero/world missing");return
	review_camera=Camera3D.new();scene.add_child(review_camera);review_camera.near=.05;review_camera.far=180
	player.rama_motion.modification_processed.connect(observe_final_pose)
	for action in contract.inputs:
		if not InputMap.has_action(action):finish("Missing InputMap action "+str(action));return
		Input.action_release(action)
	scene.ui.hide();Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	freeze_background_time()
	focus_checkpoint("before_geometry_cache")
	cache_geometry();cache_soles()
	focus_checkpoint("after_geometry_cache")
	follow_camera();review_camera.make_current()
	focus_checkpoint("before_pre_draw_hook")
	if not preflight:RenderingServer.frame_pre_draw.connect(follow_camera)
	focus_checkpoint("after_pre_draw_hook")
	focus_checkpoint("before_settle_draw8")
	await draw(8)
	focus_checkpoint("after_settle_draw8")
	if focus_case=="support":
		tape_index=0
		sequence_controls.append({"frame":0,"kind":"inactive_title_anchor","player_active":player.active,"scene_started":scene.started})
		focus_checkpoint("before_title_anchor")
		motion_frame("00-title-support")
		focus_checkpoint("after_title_anchor")
		if done:return
		scene.start_training();scene.ui.hide()
		# start_training selects the gameplay camera. Restore the declared review
		# camera before waiting for any frame used by this fixture.
		follow_camera();review_camera.make_current()
		focus_checkpoint("before_training_draw12")
		await draw(12)
		focus_checkpoint("after_training_draw12")
		tape_index=1
		sequence_controls.append({"frame":1,"kind":"start_training_then_settle","settle_render_frames":12,"player_active":player.active})
		motion_frame("01-training-support")
	else:
		scene.start_training();scene.ui.hide();scene.title_light.hide()
		follow_camera();review_camera.make_current()
		# Explicit review-only aim setup before the uninterrupted take. Runtime
		# still owns model yaw, authority, casts, contact and every pose update.
		player.pitch=-.45;player.yaw=.6;player._update_camera()
		Input.action_press("move_left");await draw(3);Input.action_release("move_left")
		await draw(12)
		if not final_body.get("on_floor",false):finish("Initial real floor support missing");return
		scene.rama_runtime.combat_event.connect(record_event)
		sequence_controls.append({"frame":-1,"kind":"declared_camera_and_input_preroll","pitch":player.pitch,"yaw":player.yaw,"strafe_render_frames":3,"settle_render_frames":12,"body":final_body.duplicate(true)})
		for index in expected:
			tape_index=index
			if index==15:
				cancelled_cast=scene.rama_runtime.cast_ability("piercing_dawn")
				sequence_controls.append({"frame":index,"kind":"cast","ability":"piercing_dawn","result":normal(cancelled_cast),"physics_frame":Engine.get_physics_frames(),"before_completed_pose":normal(final_body)})
				if not cancelled_cast.get("accepted",false):finish("Piercing request refused");return
			if index==16:
				var before:=action_state()
				var accepted: bool=scene.rama_runtime.kit.cancel_windup("graphics-six early cancel")
				sequence_controls.append({"frame":index,"kind":"cancel_windup","returned":accepted,"physics_frame":Engine.get_physics_frames(),"before":before,"immediate_after":action_state()})
				if not accepted:finish("Actual early cancellation refused");return
			if index==18:
				released_cast=scene.rama_runtime.cast_ability("kodanda")
				sequence_controls.append({"frame":index,"kind":"cast","ability":"kodanda","result":normal(released_cast),"physics_frame":Engine.get_physics_frames(),"before_completed_pose":normal(final_body)})
				if not released_cast.get("accepted",false):finish("Actual Kodanda retrigger refused");return
			await draw(1)
			motion_frame("frame-%03d"%index)
			if done:return
	verify_tape();finish("")

func focus_checkpoint(stage: String) -> void:
	var entry:={"stage":stage,"wall_ms":Time.get_ticks_msec(),"physics_frame":Engine.get_physics_frames(),"process_frame":Engine.get_process_frames(),"render_frame":Engine.get_frames_drawn(),"tree_paused":paused,"final_pose_callbacks":pose_signal_count,"preflight":preflight}
	focus_checkpoints.append(entry)
	print("GRAPHICS_FOCUS_STAGE ",JSON.stringify(entry))

func verify_tape() -> void:
	capture_checks=[{"name":"all requested original observations","passed":shots.size()==expected},
		{"name":"actual viewport camera matches declared review camera","passed":shots.all(func(s):return s.get("actual_camera_identity",{}).get("matches_requested",false))},
		{"name":"imported fullbody bounds all sampled","passed":shots.all(func(s):return s.bounds.get("passed",false))},
		{"name":"final pose body and soles share physics frame","passed":shots.all(func(s):return s.final_modifier_body.physics_frame==s.sole_contacts.physics_frame)},
		{"name":"actual support rays hit","passed":shots.all(func(s):return s.final_modifier_body.ground_ray.hit and s.sole_contacts.sides.has("L") and s.sole_contacts.sides.has("R") and s.sole_contacts.sides.L.ground_ray.hit and s.sole_contacts.sides.R.ground_ray.hit)}]
	if focus_case=="support":
		capture_checks.append({"name":"inactive title then grounded active training","passed":not sequence_controls[0].player_active and sequence_controls[1].player_active and shots[1].final_modifier_body.on_floor})
	else:
		var cancels:=0;var forbidden:=0;var releases:=0
		for event in events:
			if event.cast_id==cancelled_cast.cast_id and event.generation==cancelled_cast.generation:
				if event.kind=="cancel":cancels+=1
				if event.kind in ["release","impact"]:forbidden+=1
			if event.cast_id==released_cast.cast_id and event.generation==released_cast.generation and event.kind=="release":releases+=1
		capture_checks.append({"name":"cancelled Piercing never releases or impacts","passed":cancels==1 and forbidden==0,"cancels":cancels,"forbidden":forbidden})
		capture_checks.append({"name":"actual Kodanda releases exactly once","passed":releases==1,"releases":releases})
		capture_checks.append({"name":"presentation settles after release","passed":shots[-1].action.stage=="none" and not shots[-1].action.nocked})

func motion_frame(id: String) -> void:
	if root.get_camera_3d()!=review_camera:
		finish("Active viewport camera differs from declared review camera: "+id);return
	super.motion_frame(id)
	if not done and not shots.is_empty():
		shots[-1]["actual_camera_identity"]={"matches_requested":true,"path":str(review_camera.get_path()),"scope":"Active viewport Camera3D checked at capture; review camera selected before awaited frames."}
		shots[-1]["scope"]="Graphics-six "+focus_case+"; source-bound final modifier observation, declared review camera and actual runtime control paths."

func body_state() -> Dictionary:
	var result: Dictionary=super.body_state()
	if is_instance_valid(player.rama_motion):
		var motion=player.rama_motion
		result["idle_support_ready"]=motion.idle_support_ready if "idle_support_ready" in motion else null
		result["idle_support_y"]=normal(motion.idle_support_y) if "idle_support_y" in motion else {}
		result["support_floor_input_y"]=motion.floor_y
		result["player_active"]=player.active
	return result

func source_hashes() -> Dictionary:
	var seal: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://.graphics-six-snapshot.json"))
	var result:={}
	for name in seal.files:result["res://"+name]=FileAccess.get_sha256("res://"+name)
	for name in [".graphics-six-snapshot.json","tools/graphics-six/capture_focus.gd","tools/graphics-six/run_focus.py"]:
		result["res://"+name]=FileAccess.get_sha256("res://"+name)
	return result

func finish(failure: String) -> void:
	if done:return
	done=true
	var after:=source_hashes() if not sources.is_empty() else {}
	var passed: bool=failure.is_empty() and sources==after and shots.size()==expected and capture_checks.all(func(c):return c.passed)
	var report:={"schema":1,"task":"graphics-six focused motion","case":focus_case,"complete":passed,"failure":failure,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"shots":shots,"ability_events":events,"sequence_controls":sequence_controls,"checks":capture_checks,"sole_selection":sole_selection,"time_controls":time_controls,"expected_raw_pngs":0 if preflight else expected,"clocks":{"fixed_capture_process_hz":30,"physics_hz":Engine.physics_ticks_per_second,"hardware_fps_measured":false},"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Two nonconsecutive support anchors OR one uninterrupted60-frame actual-runtime cast/cancel/retrigger tape. Review camera/aim and API casts are explicit fixture controls, not native XTest. Final modified pose/rig/body sampled together; actual imported soles+rays. No manual pose/authority clock write. Ray hits and framing do not approve art, contact quality or FPS."}
	report["checkpoints"]=focus_checkpoints
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output):FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("GRAPHICS_FOCUS_COMPLETE ",passed," ",failure)
	paused=false
	if is_instance_valid(scene):scene.queue_free()
	for index in 3:await process_frame
	quit(0 if passed else 1)
