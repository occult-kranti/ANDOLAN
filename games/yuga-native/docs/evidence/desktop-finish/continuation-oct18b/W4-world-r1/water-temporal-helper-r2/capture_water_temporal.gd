extends "/workspace/scratch/yuga-next-W1-r1/harness/capture_water_pair.gd"
## Compact, identical-role timeline. No extra/forced RenderingServer.draw call.
## CAMERA_TRAVEL is ZERO for isolated water; a separately frozen relief derivative
## may change this one constant to a small matched translation in BOTH branches.
const FRAME_COUNT := 32
const CAMERA_START := Vector3(-48,2.8,8)
const CAMERA_TARGET := Vector3(-61,1,0)
const CAMERA_TRAVEL := Vector3.ZERO
const TIME_PROOF := "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/godot-time-r1/receipt.json"
const TIME_PROOF_SHA := "db8f560fe9b66e8f9c75d2e13736485bcd9a07a81bd5c4cce462230c4d1eba5e"
# Two float32 ULPs at1/30; cross-branch recorded values must still compare exactly.
const STEP_TOLERANCE := 0.000000007450580596923828
var declared_fixed_fps: String = ""
var compact_frames: Array = []
var image_refs: Array = []
var full_refs: Array = []
var draw_history: Array = []
var animation_reset: Array = []
var initial_clock: Dictionary = {}
var prior_clock: Dictionary = {}
var time_origin_clock: Dictionary = {}

func clock_state() -> Dictionary:
	return {"process":Engine.get_process_frames(),"physics":Engine.get_physics_frames(),"draw":Engine.get_frames_drawn(),"time_scale":Engine.time_scale,"scaled_node_process_step":root.get_process_delta_time(),"physics_hz":Engine.physics_ticks_per_second,"window_visible":root.visible,"window_can_draw":DisplayServer.window_can_draw(root.get_window_id()),"render_loop_enabled":RenderingServer.is_render_loop_enabled(),"low_processor_usage_mode":OS.low_processor_usage_mode}

func frames(count: int) -> void:
	for unused in count:
		var before: Dictionary = clock_state()
		await super.frames(1)
		draw_history.append({"before":before,"after":clock_state()})

func light_trace(node: Node, rows: Array) -> void:
	if node is Light3D:rows.append({"path":String(current_scene.get_path_to(node)),"class":node.get_class(),"transform":transform_values(node.global_transform),"visible":node.is_visible_in_tree(),"properties":stored_properties(node)})
	for child in node.get_children():light_trace(child,rows)

func compact_state(index: int) -> Dictionary:
	var scene: Node3D = current_scene
	var units: Array = []
	for unit in scene.army.units:
		units.append({"id":unit.unit_id,"team":unit.team,"role":unit.role,"alive":unit.alive,"health":unit.health,"state":unit.state,"transform":transform_values(unit.global_transform)})
	var lights: Array = []
	light_trace(scene,lights)
	var motion: Dictionary = {}
	for name in ["phase","locomotion_age","transition_age","action_elapsed","action","action_stage","locomotion","grounded","traversal"]:motion[name]=encode_value(scene.player.rama_motion.get(name))
	var animation: Array = []
	for description in scene.manifest.waters:
		var node: MeshInstance3D = scene.world.get_node(String(description.id))
		var material: ShaderMaterial = node.get_active_material(0) as ShaderMaterial
		animation.append({"id":String(description.id),"speed":material.get_shader_parameter("animation_speed")})
	return {"index":index,"clock":clock_state(),"camera":camera_state(review_camera),"camera_travel":vector(CAMERA_TRAVEL),"phase":scene.phase,"target_phase":scene.target_phase,"hero_transform":transform_values(scene.player.global_transform),"hero_visual_transform":transform_values(scene.player.visual.global_transform),"hero_velocity":vector(scene.player.velocity),"hero_active":scene.player.active,"hero_model_ready":scene.player.model_ready,"hero_presentation_suspended":scene.player.presentation_suspended,"final_pose":final_pose.duplicate(true),"pose_correlation":{"process_age":Engine.get_process_frames()-int(final_pose.get("process_frame",-1)),"physics_age":Engine.get_physics_frames()-int(final_pose.get("physics_frame",-1)),"post_draw_age":completed_post_draws-int(final_pose.get("completed_post_draws",-1))},"army_units":units,"authority":encode_value(scene.army.report()),"clocks":{"phase_clock":scene.phase_clock,"ui_clock":scene.ui_clock,"army_elapsed":scene.army.elapsed,"kit_elapsed":scene.rama_runtime.kit.elapsed,"motion":motion,"kit":encode_value(scene.rama_runtime.kit.report()),"traversal":encode_value(scene.player.traversal.report())},"paused":paused,"overview":scene.overview,"runtime_suspended":scene.rama_runtime.suspended,"environment":stored_properties(scene.world_environment.environment),"lights":lights,"water_animation":animation,"window_size":[root.size.x,root.size.y],"content_scale_size":[root.content_scale_size.x,root.content_scale_size.y],"content_scale_factor":root.content_scale_factor,"viewport_msaa":root.msaa_3d,"viewport_taa":root.use_taa}

func snapshot(id: String) -> Dictionary:
	var state: Dictionary = super.snapshot(id)
	state.review_fixture.animation="original material animation restored before frame24; real TIME, no explicit shader clock override"
	state.water_animation_reset=animation_reset.duplicate(true)
	state.temporal_scope={"frames":FRAME_COUNT,"camera_travel":vector(CAMERA_TRAVEL),"time_proof_sha256":TIME_PROOF_SHA,"full_snapshot":"first/last only"}
	return state

func save_full(id: String) -> bool:
	var state: Dictionary = snapshot(id)
	var decoded: String = JSON.stringify(state)
	var raw: PackedByteArray = decoded.to_utf8_buffer()
	var packed: PackedByteArray = raw.compress(FileAccess.COMPRESSION_GZIP)
	var name: String = id+".json.gz"
	var file: FileAccess = FileAccess.open(output.path_join(name),FileAccess.WRITE)
	if file==null or packed.is_empty():return false
	file.store_buffer(packed);file.close()
	full_refs.append({"id":id,"file":name,"compressed_sha256":FileAccess.get_sha256(output.path_join(name)),"compressed_bytes":packed.size(),"decoded_sha256":decoded.sha256_text(),"decoded_bytes":raw.size()})
	return true

func reset_animation(scene: Node3D) -> bool:
	animation_reset.clear();water_freeze.clear()
	for proof in water_override_proof:
		var node: MeshInstance3D = scene.world.get_node(String(proof.id))
		var material: ShaderMaterial = node.get_active_material(0) as ShaderMaterial
		var original_speed: float = float(proof.uniforms_before.animation_speed)
		var expected: float = .8 if String(proof.id)=="lanka-sea" else .28
		if not is_equal_approx(original_speed,expected):return false
		material.set_shader_parameter("animation_speed",original_speed)
		if material.get_shader_parameter("animation_speed")!=original_speed:return false
		animation_reset.append({"id":String(proof.id),"original_speed":original_speed,"actual_speed":material.get_shader_parameter("animation_speed")})
	return animation_reset.size()==3

func run() -> void:
	# Pin source inputs before any argument/readiness failure; no simulated step.
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
	scene.set_phase(1.0)
	if not reset_animation(scene):finish("Original animation restoration failed");return
	review_camera.global_position=CAMERA_START;review_camera.look_at(CAMERA_TARGET,Vector3.UP);review_camera.make_current()
	await frames(12)
	water_projection=water_contract(scene)
	initial_clock=clock_state();prior_clock=initial_clock.duplicate(true)
	check("fresh runtime clock starts before first draw",preflight or time_origin_clock.draw==0)
	check("first temporal sample is globaldraw24",preflight or initial_clock.draw==24)
	check("window drawable with normal render loop",preflight or (initial_clock.window_visible and initial_clock.window_can_draw and initial_clock.render_loop_enabled and not initial_clock.low_processor_usage_mode))
	if checks.any(func(row):return not row.passed):finish("Initial absolute clock gate failed");return
	for index in FRAME_COUNT:
		if index>0:
			var offset: Vector3 = CAMERA_TRAVEL*float(index)/float(FRAME_COUNT-1)
			review_camera.global_position=CAMERA_START+offset
			review_camera.look_at(CAMERA_TARGET+offset,Vector3.UP)
			await frames(1)
		var item: Dictionary = compact_state(index)
		var clock: Dictionary = item.clock
		var expected_draw: int = 24+index
		var pose_ok: bool = item.final_pose.get("bone_names",[]).size()==164 and item.final_pose.get("bone_global_poses",[]).size()==164 and item.pose_correlation.process_age==0 and item.pose_correlation.physics_age==0 and item.pose_correlation.post_draw_age==(0 if preflight else 1)
		var step_ok: bool = absf(float(clock.scaled_node_process_step)-1.0/30.0)<=STEP_TOLERANCE and clock.time_scale==1.0
		var draw_ok: bool = preflight or (clock.draw==expected_draw and (index==0 or (clock.draw==prior_clock.draw+1 and clock.process==prior_clock.process+1)) and clock.window_can_draw and clock.render_loop_enabled and not clock.low_processor_usage_mode)
		check("sample%02d correlated final pose and exact clock"%index,pose_ok and step_ok and draw_ok and serialization_errors.is_empty())
		if checks.any(func(row):return not row.passed):finish("Temporal clock/pose/serialization gate failed");return
		compact_frames.append(item);prior_clock=clock.duplicate(true)
		if index==0 or index==FRAME_COUNT-1:
			if not save_full("full-first" if index==0 else "full-last"):finish("Full snapshot gzip write failed");return
		if not preflight:
			var original: Image = root.get_texture().get_image()
			var name: String = "frame-%02d.png"%index
			if original.is_empty() or original.save_png(output.path_join(name))!=OK:finish("Temporal PNG write failed");return
			image_refs.append({"index":index,"file":name,"sha256":FileAccess.get_sha256(output.path_join(name)),"dimensions":[original.get_width(),original.get_height()],"global_draw":clock.draw})
	finish("")

func finish(failure: String) -> void:
	if done:return
	done=true
	var after: Dictionary = hashes() if not source_start.is_empty() else {}
	check("32compact observations with2full boundary controls",compact_frames.size()==FRAME_COUNT and full_refs.size()==2)
	check("32actual originals or explicit headlesspreflight",image_refs.size()==(0 if preflight else FRAME_COUNT))
	check("external source inputs unchanged",not source_start.is_empty() and source_start==after)
	var trace_ref: Dictionary = {}
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):
		write_json(output.path_join("compact-trace.json"),{"frames":compact_frames,"time_origin_clock":time_origin_clock,"before_first_clock":initial_clock,"draw_history":draw_history,"animation_reset":animation_reset,"time_proof_sha256":TIME_PROOF_SHA,"camera_travel":vector(CAMERA_TRAVEL)})
		trace_ref={"file":"compact-trace.json","sha256":FileAccess.get_sha256(output.path_join("compact-trace.json")),"frames":compact_frames.size()}
	var passed: bool = failure.is_empty() and checks.all(func(row):return row.passed)
	var report: Dictionary = {"complete":passed,"failure":failure,"preflight":preflight,"water_role":water_role,"shots":image_refs,"full_snapshot_refs":full_refs,"trace_ref":trace_ref,"checks":checks,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"time_proof_path":TIME_PROOF,"time_proof_sha256":TIME_PROOF_SHA,"candidate_path":CANDIDATE_PATH,"candidate_sha256":CANDIDATE_SHA256,"override_proof":water_override_proof,"engine_args":Array(OS.get_cmdline_args()),"capture_fixed_fps_declaration":declared_fixed_fps,"camera_travel":vector(CAMERA_TRAVEL),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"32actual consecutive fixed30Hz night-swamp samples with real TIME and restored original water animation. Full world/hero/UI retained. Full controls only first+last, compact correlated trace for all32. No hardwareFPS,long-cycle,whole-world or finished-art acceptance."}
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
	print("WATER_TEMPORAL_COMPLETE ",passed," ",failure)
	quit(0 if passed else 1)
