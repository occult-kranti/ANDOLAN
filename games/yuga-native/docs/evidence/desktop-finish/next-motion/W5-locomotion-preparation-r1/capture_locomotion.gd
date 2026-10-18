extends "res://tools/graphics-six/capture_transition.gd"
## Source-only preparation. Inherits the sealed final-modifier/skin observer.
## No engine/preflight/raster execution has qualified this derivative yet.
var sequence_plan: Dictionary = {}
var walk_strength := 0.0
var measured_generation := -1
var measured_jump_count := -1
var preparation: Dictionary = {}

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg=="--preflight": preflight=true
		elif arg!="--case=locomotion": finish("Unknown locomotion capture argument "+arg);return
	var loaded: Variant=JSON.parse_string(FileAccess.get_file_as_string("res://tools/graphics-six/locomotion-sequence.json"))
	if not (loaded is Dictionary): finish("Missing locomotion sequence");return
	sequence_plan=loaded
	if int(sequence_plan.get("frames",0))!=270 or int(sequence_plan.get("physics_hz",0))!=60 or int(sequence_plan.get("capture_hz",0))!=30:
		finish("Unexpected declared cadence/count");return
	capture_case="locomotion";focus_case="desktop-natural-locomotion";mode=focus_case;context="courtyard"
	physics_hz=60;capture_hz=30;landing_close=false;expected=270
	Engine.physics_ticks_per_second=physics_hz
	contract={"camera":sequence_plan.camera,"inputs":sequence_plan.inputs,"preflight_bounds_frames":range(expected)}
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):
		finish("X11 Forward+ required");return
	seed(int(sequence_plan.seed));root.size=SIZE;root.content_scale_size=SIZE;root.msaa_3d=Viewport.MSAA_2X
	if not preflight: root.show()
	sources=source_hashes()
	var seal: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://.graphics-six-snapshot.json"))
	for name_ in seal.files:
		if sources["res://"+name_]!=seal.files[name_].sha256: finish("Snapshot differs "+name_);return
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene);current_scene=scene
	await draw(6);player=scene.player
	if not player.model_ready or not scene.environment_ready: finish("Actual hero/world missing");return
	review_camera=Camera3D.new();scene.add_child(review_camera);review_camera.near=.05;review_camera.far=180
	player.rama_motion.modification_processed.connect(observe_final_pose)
	var deadzones: Dictionary={}
	for action_ in contract.inputs:
		if not InputMap.has_action(action_): finish("Missing action "+str(action_));return
		Input.action_release(action_)
	for action_ in ["move_left","move_right","move_forward","move_back"]:
		deadzones[action_]=InputMap.action_get_deadzone(action_)
	var deadzone: float=(float(deadzones.move_left)+float(deadzones.move_right)+float(deadzones.move_forward)+float(deadzones.move_back))/4.0
	if deadzone<0 or deadzone>=1: finish("Unsupported movement deadzone");return
	# Input.get_vector remaps radial length above the mean action deadzone.
	# Record this prediction and verify actual velocity/gait; never change it.
	walk_strength=deadzone+(1.0-deadzone)*float(sequence_plan.walk_normalized_input)
	preparation={"action_deadzones":deadzones,"mean_deadzone":deadzone,"walk_raw_strength":walk_strength,"expected_normalized_input":sequence_plan.walk_normalized_input,"expected_walk_speed_mps":sequence_plan.expected_walk_speed_mps}
	scene.ui.hide();Input.mouse_mode=Input.MOUSE_MODE_VISIBLE;freeze_background_time();set_light(false)
	cache_geometry();cache_soles();follow_camera();review_camera.make_current()
	if not preflight: RenderingServer.frame_pre_draw.connect(follow_camera)
	await draw(int(sequence_plan.title_preroll_draws)-6)
	# Public start and all reset/teleport side effects are outside measurement.
	scene.start_training();scene.ui.hide();scene.title_light.hide()
	follow_camera();review_camera.make_current()
	await draw(int(sequence_plan.training_settle_draws))
	if not final_body.get("on_floor",false) or player.rama_motion.locomotion!="idle" or player.velocity.length()>.12:
		finish("Declared fixed preroll did not settle; do not adapt or reset the tape");return
	measured_generation=scene.rama_runtime.kit.generation;measured_jump_count=player.jump_count
	preparation["settled_body"]=final_body.duplicate(true)
	preparation["settle_render_frames"]=sequence_plan.training_settle_draws
	scene.rama_runtime.combat_event.connect(record_event)
	for index in expected:
		tape_index=index
		for raw_event in sequence_plan.events:
			var event_: Dictionary=raw_event
			if int(event_.frame)!=index: continue
			var edge: Dictionary=event_.duplicate(true)
			edge["physics_before"]=Engine.get_physics_frames()
			if event_.kind=="press":
				var strength_value: Variant=event_.get("strength",1.0)
				var strength: float=walk_strength if strength_value is String else float(strength_value)
				Input.action_press(event_.action,strength);edge["applied_strength"]=strength
			else: Input.action_release(event_.action)
			edge["actual_input_after"]=normal(Input.get_vector("move_left","move_right","move_forward","move_back"))
			sequence_controls.append(edge)
		follow_camera();review_camera.make_current()
		await draw(1);motion_frame("frame-%03d"%index)
		if done: return
	for action_ in contract.inputs: Input.action_release(action_)
	verify_locomotion();finish("")

func body_state() -> Dictionary:
	var result: Dictionary=super.body_state()
	result["position_world"]=normal(player.global_position)
	result["controller_yaw"]=player.yaw
	result["visual_yaw"]=player.visual.global_rotation.y
	result["controller_local_velocity"]=normal(Basis(Vector3.UP,player.yaw).inverse()*player.velocity)
	result["visual_local_velocity"]=normal(player.visual.global_basis.inverse()*player.velocity)
	result["actual_move_input"]=normal(Input.get_vector("move_left","move_right","move_forward","move_back"))
	return result

func phase_name(index: int) -> String:
	for raw_window in sequence_plan.windows:
		var window: Dictionary=raw_window
		if index>=int(window.first) and index<=int(window.last): return str(window.name)
	return "outside_declared_window"

func motion_frame(id: String) -> void:
	super.motion_frame(id)
	if not done:
		shots[-1]["segment"]=phase_name(tape_index)
		shots[-1]["scope"]="Declared uninterrupted locomotion input tape; final modifier pose and actual skin/ground data. No quality acceptance from coverage gates."

func verify_locomotion() -> void:
	var walk_count:=0;var run_count:=0;var left_count:=0;var right_count:=0;var stopped_count:=0
	var airborne:=false;var landed:=false;var consecutive:=true;var adjacent_draws:=true
	var no_reset:=true;var no_root_jump:=true;var maximum_horizontal:=0.0;var maximum_vertical:=0.0
	for index in shots.size():
		var shot: Dictionary=shots[index];var body: Dictionary=shot.final_modifier_body
		var speed: float=Vector2(float(body.velocity[0]),float(body.velocity[2])).length()
		if index>=15 and index<75 and body.motion.locomotion=="walk" and absf(speed-2.4)<.05: walk_count+=1
		if index>=90 and index<120 and body.motion.locomotion=="run" and absf(speed-6.0)<.05: run_count+=1
		if index>=150 and index<180 and float(body.controller_local_velocity[0])< -5.9: left_count+=1
		if index>=180 and index<210 and float(body.controller_local_velocity[0])>5.9: right_count+=1
		if index>=135 and index<150 and speed<=.12 and body.motion.locomotion=="idle": stopped_count+=1
		if index>=225 and not body.on_floor: airborne=true
		if index>=225 and airborne and body.on_floor: landed=true
		no_reset=no_reset and int(body.kit_report.generation)==measured_generation
		if index==0: continue
		var prior: Dictionary=shots[index-1]
		consecutive=consecutive and int(body.physics_frame)-int(prior.final_modifier_body.physics_frame)==2
		if not preflight: adjacent_draws=adjacent_draws and int(shot.render_frame)-int(prior.render_frame)==1
		var delta: Vector3=v3(body.position_world)-v3(prior.final_modifier_body.position_world)
		var horizontal: float=Vector2(delta.x,delta.z).length()
		maximum_horizontal=maxf(maximum_horizontal,horizontal);maximum_vertical=maxf(maximum_vertical,absf(delta.y))
		# Execution guard, not foot-quality tolerance: declared6m/s movement and
		# native7.2m/s jump cannot teleport a root beyond these frame distances.
		no_root_jump=no_root_jump and horizontal<=.205 and absf(delta.y)<=.25
	capture_checks=[
		{"name":"all270 consecutive final-modifier observations","passed":shots.size()==270},
		{"name":"actual60Hz physics and30Hz capture counters","passed":consecutive and adjacent_draws,"draw_scope":"not applicable to headless preflight" if preflight else "all native renders adjacent"},
		{"name":"pose body and imported soles share physics counter","passed":shots.all(func(s):return s.final_modifier_body.physics_frame==s.sole_contacts.physics_frame)},
		{"name":"requested camera and imported fullbody bounds retained","passed":shots.all(func(s):return s.actual_camera_identity.matches_requested and s.bounds.passed)},
		{"name":"sustained actual walk covers at least1.6seconds","passed":walk_count>=48,"matching_samples":walk_count,"declared_window_frames":[15,74]},
		{"name":"actual run precedes natural release and settled stop","passed":run_count>=20 and stopped_count==15,"run_samples":run_count,"idle_stop_samples":stopped_count},
		{"name":"both lateral control directions sustain actual movement","passed":left_count>=20 and right_count>=20,"left_samples":left_count,"right_samples":right_count,"scope":"Controller-relative lateral motion; visual rotation/local velocity remain unforced and recorded."},
		{"name":"one public jump becomes airborne then grounded and settles","passed":airborne and landed and shots[-1].final_modifier_body.on_floor and int(shots[-1].final_modifier_body.jump_count)==measured_jump_count+1 and shots[-1].final_modifier_body.motion.locomotion=="idle"},
		{"name":"no reset generation or root teleport during measurement","passed":no_reset and no_root_jump,"maximum_horizontal_frame_m":maximum_horizontal,"maximum_vertical_frame_m":maximum_vertical},
		{"name":"no incidental combat cast changes locomotion premise","passed":events.is_empty() and shots.all(func(s):return s.action.stage=="none")}
	]

func source_hashes() -> Dictionary:
	var result: Dictionary=super.source_hashes()
	result["res://tools/graphics-six/locomotion-sequence.json"]=FileAccess.get_sha256("res://tools/graphics-six/locomotion-sequence.json")
	return result

func finish(failure: String) -> void:
	if done: return
	done=true
	for action_ in contract.get("inputs",[]): Input.action_release(action_)
	var after: Dictionary=source_hashes() if not sources.is_empty() else {}
	var passed: bool=failure.is_empty() and sources==after and shots.size()==270 and not capture_checks.is_empty() and capture_checks.all(func(c):return c.passed)
	var report: Dictionary={"task":"Next natural locomotion coverage","case":"locomotion","complete":passed,"failure":failure,"shots":shots,"checks":capture_checks,"sequence_controls":sequence_controls,"sequence_plan":sequence_plan,"preparation":preparation,"ability_events":events,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"sole_selection":sole_selection,"time_controls":time_controls,"expected_raw_pngs":0 if preflight else 270,"bone_names":[],"physics_hz":60,"fixed_capture_hz":30,"camera_contract":contract.get("camera",{}),"godot":Engine.get_version_info(),"adapter":RenderingServer.get_video_adapter_name(),"renderer":RenderingServer.get_current_rendering_method(),"scope":"One uninterrupted9s declared-input take after fixed public-start settle. Complete164-bone final poses and actual skin/ground observations retained. No reset/teleport/root/pose/clock/anchor assignment during measurement. Coverage is not motion-quality or physical-device-input acceptance; original26/27 limit remains."}
	if is_instance_valid(player):
		for index in player.rama_motion.rig.get_bone_count(): report.bone_names.append(player.rama_motion.rig.get_bone_name(index))
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output):
		# Compact formatting retains every float, pose and assertion, not a summary.
		FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"",true,true)+"\n")
	print("NATURAL_LOCOMOTION_CAPTURE_COMPLETE ",passed," ",failure)
	paused=false
	if is_instance_valid(scene): scene.queue_free()
	for unused in 3: await process_frame
	quit(0 if passed else 1)
