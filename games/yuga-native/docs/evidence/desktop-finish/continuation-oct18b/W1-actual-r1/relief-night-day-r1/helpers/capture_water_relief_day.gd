extends "/workspace/scratch/yuga-next-W4-r1/water-relief-helper-r1/capture_water_relief.gd"
## Separate one-view day observation. Never invokes the parent's temporal loop.
## Parent FRAME_COUNT, source materials, final-pose observer and clocks are untouched.
var day_helper_before: String = ""

func snapshot(id: String) -> Dictionary:
	var state: Dictionary = super.snapshot(id)
	state.temporal_scope={"observations":1,"phase":0.0,"stationary":true,"camera_travel":vector(Vector3.ZERO),"full_snapshot":"single day observation; compressed only"}
	return state

func run() -> void:
	# Pin source inputs before any argument/readiness failure; no simulated step.
	day_helper_before=FileAccess.get_sha256(get_script().resource_path)
	source_start=hashes()
	time_origin_clock=clock_state()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
		elif arg.begins_with("--capture-fixed-fps="):declared_fixed_fps=arg.trim_prefix("--capture-fixed-fps=")
		elif arg.begins_with("--water-role="):water_role=arg.trim_prefix("--water-role=")
		else:finish("Unknown argument:"+arg);return
	if water_role not in ["baseline","candidate"]:finish("Explicit water role required");return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if FileAccess.get_sha256(TIME_PROOF)!=TIME_PROOF_SHA:finish("TIME proof changed");return
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):finish("X11 Forward+ required");return
	# Godot removes parsed engine flags from OS.get_cmdline_args(). W1 must
	# independently pin its actual --fixed-fps30 launch command. This explicit
	# fixture declaration supplements the unchanged measured step/draw gates.
	check("fixture declares fixed30Hz; wrapper pins engine invocation",declared_fixed_fps=="30")
	if checks.any(func(row):return not row.passed):finish("Fixed-step gate failed");return
	branch="baseline-exact79e5"
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
	if not preflight:root.show()
	if change_scene_to_file("res://scenes/confluence_world.tscn")!=OK:finish("World load failed");return
	if not await wait_scene("res://scenes/confluence_world.tscn"):finish("World readiness failed");return
	await frames(12)
	var scene: Node3D = current_scene
	check("full live world/hero",scene.world_ready and scene.player.model_ready and scene.player.active and not paused and not scene.overview)
	if not install_water_shader(scene):finish("Exact water shader/uniform installation failed");return
	scene.player.rama_motion.modification_processed.connect(observe_final_pose);final_observer_connected=true
	review_camera=Camera3D.new();review_camera.name="ReviewWaterCamera";review_camera.fov=65.0;review_camera.near=.1;review_camera.far=400.0;scene.world.add_child(review_camera)
	scene.set_phase(0.0)
	if not reset_animation(scene):finish("Original animation restoration failed");return
	review_camera.global_position=CAMERA_START;review_camera.look_at(CAMERA_TARGET,Vector3.UP);review_camera.make_current()
	await frames(12)
	water_projection=water_contract(scene)
	initial_clock=clock_state();prior_clock=initial_clock.duplicate(true)
	check("fresh runtime clock starts before first draw",preflight or time_origin_clock.draw==0)
	check("stationary day observation is globaldraw24",preflight or initial_clock.draw==24)
	check("window drawable with normal render loop",preflight or (initial_clock.window_visible and initial_clock.window_can_draw and initial_clock.render_loop_enabled and not initial_clock.low_processor_usage_mode))
	if checks.any(func(row):return not row.passed):finish("Initial absolute clock gate failed");return
	var item: Dictionary = compact_state(0)
	# The inherited .6m travel constant is never applied in this stationary route.
	item.camera_travel=vector(Vector3.ZERO)
	var pose_ok: bool = item.final_pose.get("bone_names",[]).size()==164 and item.final_pose.get("bone_global_poses",[]).size()==164 and item.pose_correlation.process_age==0 and item.pose_correlation.physics_age==0 and item.pose_correlation.post_draw_age==(0 if preflight else 1)
	var step_ok: bool = absf(float(item.clock.scaled_node_process_step)-1.0/30.0)<=STEP_TOLERANCE and item.clock.time_scale==1.0
	check("day final164pose, measured step, phase and stationary camera",pose_ok and step_ok and scene.phase==0.0 and scene.target_phase==0.0 and review_camera.global_position==CAMERA_START and serialization_errors.is_empty())
	if checks.any(func(row):return not row.passed):finish("Day observation gate failed");return
	compact_frames.append(item)
	if not save_full("full-day"):finish("Day full snapshot gzip write failed");return
	if not preflight:
		var original: Image = root.get_texture().get_image()
		var name: String = "00-day-swamp.png"
		if original.is_empty() or original.save_png(output.path_join(name))!=OK:finish("Day PNG write failed");return
		image_refs.append({"index":0,"file":name,"sha256":FileAccess.get_sha256(output.path_join(name)),"dimensions":[original.get_width(),original.get_height()],"global_draw":item.clock.draw})
	finish("")

func finish(failure: String) -> void:
	if done:return
	done=true
	var after: Dictionary = hashes() if not source_start.is_empty() else {}
	var day_helper_after: String = FileAccess.get_sha256(get_script().resource_path)
	check("one compact observation and one compressed full control",compact_frames.size()==1 and full_refs.size()==1)
	check("one actual original or explicit headless preflight",image_refs.size()==(0 if preflight else 1))
	check("external source inputs and separate day helper unchanged",not source_start.is_empty() and source_start==after and not day_helper_before.is_empty() and day_helper_before==day_helper_after)
	var trace_ref: Dictionary = {}
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):
		write_json(output.path_join("day-trace.json"),{"frames":compact_frames,"time_origin_clock":time_origin_clock,"before_first_clock":initial_clock,"draw_history":draw_history,"animation_reset":animation_reset,"time_proof_sha256":TIME_PROOF_SHA,"camera_travel":vector(Vector3.ZERO),"phase":0.0})
		trace_ref={"file":"day-trace.json","sha256":FileAccess.get_sha256(output.path_join("day-trace.json")),"frames":compact_frames.size()}
	var passed: bool = failure.is_empty() and checks.all(func(row):return row.passed)
	var report: Dictionary = {"complete":passed,"failure":failure,"preflight":preflight,"water_role":water_role,"shots":image_refs,"full_snapshot_refs":full_refs,"trace_ref":trace_ref,"checks":checks,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"day_helper_path":get_script().resource_path,"day_helper_sha256":day_helper_before,"day_helper_after_sha256":day_helper_after,"parent_helper_sha256":"019eb29c140e296d5549df02aad653593eeb37e144d3cd8a2b8966295888c15a","time_proof_path":TIME_PROOF,"time_proof_sha256":TIME_PROOF_SHA,"candidate_path":COMBINED_WATER_PATH,"candidate_sha256":COMBINED_WATER_SHA,"baseline_water_path":CANDIDATE_PATH,"baseline_water_sha256":CANDIDATE_SHA256,"combined_source_pins":COMBINED_PINS,"ground_override_proof":ground_override_proof,"override_proof":water_override_proof,"engine_args":Array(OS.get_cmdline_args()),"capture_fixed_fps_declaration":declared_fixed_fps,"camera_travel":vector(Vector3.ZERO),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Separate stationary day observation at globaldraw24, phase0, same night-review camera and full world/hero/UI. Thin-film baseline versus exact combined root ground/water relief. Single full control compressed with raw+gzip hashes. Not the existing night sequence or a temporal day test."}
	paused=false
	if is_instance_valid(current_scene):current_scene.queue_free()
	for unused in 8:await process_frame
	var started: int = Time.get_ticks_usec();var previous: float = AudioServer.get_time_since_last_mix();var observed: int = 0
	while observed<2 and Time.get_ticks_usec()-started<250000:
		OS.delay_msec(1)
		var now: float = AudioServer.get_time_since_last_mix()
		if now+.0002<previous:observed+=1
		previous=now
	for unused in 8:await process_frame
	report.audio_cleanup={"observed_real_mixer_ticks":observed,"budget_usec":250000}
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):write_json(output.path_join("preflight.json" if preflight else "capture.json"),report)
	print("WATER_RELIEF_DAY_COMPLETE ",passed," ",failure)
	quit(0 if passed else 1)

