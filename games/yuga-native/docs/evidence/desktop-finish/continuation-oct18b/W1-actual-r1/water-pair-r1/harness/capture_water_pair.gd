extends "/workspace/scratch/yuga-next-W1-r1/harness/capture_water_baseline.gd"
## One identical source-only pair helper; W1 owns native parse/transport/rendering.
## Same original 12-ready/12-per-view callback schedule and known mixer cleanup.
const CANDIDATE_PATH := "/workspace/scratch/yuga-next-W4-r1/thin-film-r1/world_water.gdshader"
const CANDIDATE_SHA256 := "3f5a6b89b6bdaaea547c51829da558d829445fb63a690d119e21720b8ce27a7e"
const ORIGINAL_SHADER_SHA256 := "add24973aab0d30ebeae2f2db7d096f74fd304bf22868afc4470e22506f86283"
const REUSED_NIGHT_PATH := "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W1-actual-r1/water-baseline-r1/raw/00-night-swamp.png"
const REUSED_NIGHT_SHA256 := "f169f43710434b3dc871ce792182e424578ceb90226d106b5e165962754b9bb7"
var water_role: String = ""
var water_override_proof: Array = []

func uniform_values(material: ShaderMaterial) -> Dictionary:
	var values: Dictionary = {}
	for entry in material.shader.get_shader_uniform_list():
		values[String(entry.name)] = material.get_shader_parameter(String(entry.name))
	return values

func install_water_shader(scene: Node3D) -> bool:
	if FileAccess.get_sha256(CANDIDATE_PATH) != CANDIDATE_SHA256:return false
	var candidate_shader: Shader
	if water_role == "candidate":
		candidate_shader = load(CANDIDATE_PATH) as Shader
		if candidate_shader == null or candidate_shader.code.sha256_text() != CANDIDATE_SHA256:return false
	water_override_proof.clear()
	for description in scene.manifest.waters:
		var node: MeshInstance3D = scene.world.get_node_or_null(String(description.id))
		if node == null:return false
		var original: ShaderMaterial = node.get_active_material(0) as ShaderMaterial
		if original == null or original.shader == null or node.material_override != original:return false
		var original_code_sha: String = original.shader.code.sha256_text()
		if original_code_sha != ORIGINAL_SHADER_SHA256:return false
		var before: Dictionary = uniform_values(original)
		var active: ShaderMaterial = original
		if water_role == "candidate":
			active = original.duplicate(false) as ShaderMaterial
			active.shader = candidate_shader
			for name in before:active.set_shader_parameter(name,before[name])
			node.material_override = active
		var after: Dictionary = uniform_values(active)
		if before != after:return false
		water_override_proof.append({"id":String(description.id),"applied":water_role=="candidate","original_shader_path":original.shader.resource_path,"original_code_sha256":original_code_sha,"active_shader_path":active.shader.resource_path,"active_code_sha256":active.shader.code.sha256_text(),"uniforms_before":encode_value(before),"uniforms_after_install":encode_value(after),"all_uniforms_copied_exact":before==after})
	check("three real water materials retain every original uniform",water_override_proof.size()==3 and water_override_proof.all(func(row):return row.all_uniforms_copied_exact))
	return water_override_proof.size()==3

func snapshot(id: String) -> Dictionary:
	var result: Dictionary = super.snapshot(id)
	result.water_shader_override = {"role":water_role,"candidate_path":CANDIDATE_PATH,"candidate_sha256":CANDIDATE_SHA256,"rows":water_override_proof.duplicate(true)}
	result.review_fixture.animation = "only water animation_speed frozen0; exact isolated external shader override declared separately"
	for row in result.water_shader_override.rows:
		var node: MeshInstance3D = current_scene.world.get_node(String(row.id))
		var material: ShaderMaterial = node.get_active_material(0) as ShaderMaterial
		row.uniforms_at_snapshot = encode_value(uniform_values(material))
	return result

func take(id: String) -> bool:
	if water_role != "baseline" or id != "00-night-swamp":return super.take(id)
	# Observe the complete same actual frame, but do not recapture its PNG.
	var state: Dictionary = snapshot(id)
	if not preflight:
		state.framebuffer_size = [root.get_texture().get_width(),root.get_texture().get_height()]
		state.reused_original = {"path":REUSED_NIGHT_PATH,"sha256":REUSED_NIGHT_SHA256,"strict_control_comparison_required":true}
	shots.append(state)
	write_json(output.path_join(id+".json"),state)
	checkpoint("shot:"+id)
	return true

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
		elif arg.begins_with("--water-role="):water_role=arg.trim_prefix("--water-role=")
		else:finish("Unknown argument:"+arg);return
	if water_role not in ["baseline","candidate"]:finish("Explicit water role required");return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):finish("X11 Forward+ required");return
	source_start=hashes();branch="baseline-exact79e5"
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
	if not preflight:root.show()
	if change_scene_to_file("res://scenes/confluence_world.tscn")!=OK:finish("World load failed");return
	if not await wait_scene("res://scenes/confluence_world.tscn"):finish("World readiness failed");return
	await frames(12)
	var scene: Node3D=current_scene
	check("full live world/hero",scene.world_ready and scene.player.model_ready and scene.player.active and not paused and not scene.overview)
	if not install_water_shader(scene):finish("Exact water shader/uniform installation failed");return
	scene.player.rama_motion.modification_processed.connect(observe_final_pose);final_observer_connected=true
	review_camera=Camera3D.new();review_camera.name="ReviewWaterCamera";review_camera.fov=65.0;review_camera.near=.1;review_camera.far=400.0;scene.world.add_child(review_camera)
	var views: Array=[{"id":"00-night-swamp","position":Vector3(-48,2.8,8),"target":Vector3(-61,1,0),"phase":1.0,"water":"shallow"},{"id":"01-coast-day","position":Vector3(-94,4.6,-38),"target":Vector3(-80,-.15,-38),"phase":0.0,"water":"coastal"},{"id":"02-day-swamp","position":Vector3(-48,2.8,8),"target":Vector3(-61,1,0),"phase":0.0,"water":"shallow"}]
	for view in views:
		scene.set_phase(view.phase)
		water_freeze.clear()
		for description in scene.manifest.waters:
			var node: MeshInstance3D=scene.world.get_node_or_null(String(description.id))
			if node!=null:
				var material: ShaderMaterial=node.get_active_material(0)
				water_freeze.append({"id":String(description.id),"original_speed":material.get_shader_parameter("animation_speed"),"fixture_speed":0.0})
				material.set_shader_parameter("animation_speed",0.0)
		review_camera.global_position=view.position;review_camera.look_at(view.target,Vector3.UP);review_camera.make_current()
		await frames(12)
		water_projection=water_contract(scene)
		check("requested water projects in frame "+view.id,water_projection.any(func(row):return row.style==view.water and row.samples_in_frame>=5 and row.sample_rect_frame_fraction>=.01))
		if checks.any(func(row):return not row.passed):finish("Projection/control gate failed");return
		if not take_frontage(view.id):return
	finish("")

func finish(failure: String) -> void:
	if done:return
	done=true
	var after:=hashes() if not source_start.is_empty() else {}
	check("three declared full-world water observations",shots.size()==3)
	check("external inputs unchanged",not source_start.is_empty() and source_start==after)
	var passed:=failure.is_empty() and checks.all(func(row):return row.passed)
	var report:={"water_role":water_role,"candidate_path":CANDIDATE_PATH,"candidate_source_sha256":FileAccess.get_sha256(CANDIDATE_PATH),"override_proof":water_override_proof,"complete":passed,"failure":failure,"preflight":preflight,"shots":shots,"projection_at_exit":water_projection,"checks":checks,"checkpoints":checkpoints,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Exact79e5 PCK full production world; common fixed cameras/phases and water animation0. Candidate changes only the external exact thin-film shader on3water materials, with all original uniforms copied. Baseline night is a JSON observation for strict original-image reuse. No temporal/HW FPS/finished-art acceptance."}
	paused=false
	if is_instance_valid(current_scene):current_scene.queue_free()
	for unused in 8:await process_frame
	var started:=Time.get_ticks_usec();var previous:=AudioServer.get_time_since_last_mix();var observed:=0
	while observed<2 and Time.get_ticks_usec()-started<250000:
		OS.delay_msec(1)
		var now:=AudioServer.get_time_since_last_mix()
		if now+.0002<previous:observed+=1
		previous=now
	for unused in 8:await process_frame
	report.audio_cleanup={"observed_real_mixer_ticks":observed,"budget_usec":250000}
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):write_json(output.path_join("preflight.json" if preflight else "capture.json"),report)
	print("WATER_PAIR_COMPLETE ",passed," ",failure)
	quit(0 if passed else 1)
