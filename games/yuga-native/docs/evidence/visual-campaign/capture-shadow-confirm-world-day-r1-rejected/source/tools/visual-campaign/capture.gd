extends SceneTree
## Unaltered framebuffers from the actual courtyard, fixed camera contract v1.
const SIZE := Vector2i(1280, 960)
const ABILITY_IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
var output := ""
var scene: Node3D
var player: CharacterBody3D
var review_camera: Camera3D
var sources := {}
var shots: Array = []
var events: Array = []
var time_controls: Array = []
var started := Time.get_ticks_msec()
var done := false
var ability_reel := false
var abilities_only := false
var title_night := false
var character_detail := false
var selected_abilities: Array[String] = []
var ability_night := false
var ability_phases: Array = []
var character_pairs: Array = []
var face_ablation := false
var face_diagnostics: Array = []
var shadow_bias_mode := ""
var shadow_night := false
var shadow_diagnostics: Array = []
var shadow_world := false

func _initialize() -> void: call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--ability-reel": ability_reel = true
		elif arg == "--abilities-only": abilities_only = true; ability_reel = true
		elif arg == "--title-night": title_night = true
		elif arg == "--character-detail": character_detail = true
		elif arg == "--face-ablation": face_ablation = true
		elif arg == "--shadow-night": shadow_night = true
		elif arg == "--shadow-world": shadow_world = true
		elif arg.begins_with("--shadow-bias="):
			shadow_bias_mode = arg.trim_prefix("--shadow-bias=")
			if not shadow_bias_mode in ["all","final","confirm","baseline","depth","normal","both","defaults","depth2","depth4"]: finish("Unknown shadow diagnostic mode"); return
		elif arg == "--ability-night": ability_night = true; ability_reel = true
		elif arg.begins_with("--ability="):
			var id: String = arg.trim_prefix("--ability=")
			if not id in ABILITY_IDS or id in selected_abilities: finish("Unknown or repeated ability " + id); return
			selected_abilities.append(id); ability_reel = true
		else: finish("Unknown argument " + arg); return
	if not shadow_bias_mode.is_empty() and (face_ablation or ability_reel or character_detail or title_night): finish("Shadow diagnostic must be separate"); return
	if (shadow_night or shadow_world) and shadow_bias_mode.is_empty(): finish("Shadow night requires a shadow mode"); return
	if face_ablation and (ability_reel or character_detail or title_night): finish("Face ablation is a separate diagnostic run"); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	if DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus": finish("X11 Forward+ required"); return
	seed(741031)
	root.size = SIZE; root.content_scale_size = SIZE; root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA actual visual campaign"; root.show()
	sources = source_hashes()
	scene = load("res://scenes/confluence_world.tscn" if shadow_world else "res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await draw(6)
	player = scene.player
	if not player.model_ready or not (scene.world_ready if shadow_world else scene.environment_ready): finish("Actual hero or courtyard missing"); return
	review_camera = Camera3D.new(); review_camera.name = "CampaignReviewCamera"; scene.add_child(review_camera)
	review_camera.fov = 43.0; review_camera.far = 180.0
	freeze_background_time()
	paused = true
	scene.set_process(false); scene.set_physics_process(false)
	if not shadow_bias_mode.is_empty():
		await capture_shadow_bias()
		if not done: finish("")
		return
	if face_ablation:
		await capture_face_ablation()
		if not done: finish("")
		return
	if abilities_only:
		scene.start_training()
		await draw(8)
		paused = true
		set_light(false)
		scene.rama_runtime.combat_event.connect(record_event)
		await capture_abilities()
		if character_detail and not done: await capture_character_detail()
		if not done: finish("")
		return
	set_light(false)
	await shot("01-title-day", scene.title_camera, "actual title camera and interface")
	if done: return
	if title_night:
		set_light(true)
		await shot("09-title-night", scene.title_camera, "actual title camera and interface; optional night view")
		if done: return
		set_light(false)
	scene.start_training()
	await draw(8)
	paused = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	scene.ui.hide(); scene.title_light.hide()
	place_hero_camera()
	for night in [false, true]:
		set_light(night)
		await shot("03-hero-near-night" if night else "02-hero-near-day", review_camera, "fixed three-quarter hero portrait; real current mesh/materials")
		if done: return
	scene.ui.show()
	for night in [false, true]:
		set_light(night)
		await shot("05-gameplay-night" if night else "04-gameplay-day", player.camera, "actual player camera and gameplay HUD; input idle")
		if done: return
	scene.ui.hide()
	review_camera.fov = 60.0
	review_camera.global_position = Vector3(16, 12, 24)
	review_camera.look_at(Vector3(0, 2, -3))
	for night in [false, true]:
		set_light(night)
		await shot("07-courtyard-overview-night" if night else "06-courtyard-overview-day", review_camera, "staged overview of actual playable courtyard")
		if done: return
	set_light(false)
	scene.ui.show(); player.camera.make_current()
	scene.rama_runtime.combat_event.connect(record_event)
	paused = false
	var accepted: Dictionary = scene.rama_runtime.cast_ability("piercing_dawn")
	if not accepted.get("accepted", false): finish("Normal runtime ability request refused: " + str(accepted)); return
	var released := false
	for index in range(30):
		await draw(1)
		for event in events:
			if event.kind == "release": released = true
		if released: break
	if not released: finish("No authority ability release within 30 fixed-rate frames"); return
	paused = true
	await shot("08-piercing-dawn-release", player.camera, "actual runtime cast and authority release; frozen immediately after release frame")
	if ability_reel and not done: await capture_abilities()
	if character_detail and not done: await capture_character_detail()
	if not done: finish("")

func record_event(event: Dictionary) -> void:
	if event.get("kind") in ["begin", "release", "impact", "recovery", "end", "cancel"]: events.append(normal(event))

func has_event(kind: String, start: int, cast_id: int) -> bool:
	for index in range(start, events.size()):
		if events[index].kind == kind and int(events[index].cast_id) == cast_id: return true
	return false

func capture_abilities() -> void:
	# Every cast uses the real runtime entry point and ordinary 20 Hz army clock.
	# Pauses select review frames; no damage events or poses are fabricated.
	for night in ([false, true] if ability_night else [false]):
		for id in (selected_abilities if not selected_abilities.is_empty() else ABILITY_IDS):
			await capture_ability(id, night)
			if done: return

func capture_ability(id: String, night: bool) -> void:
	scene.reset_training(); scene.start_training(); set_light(night)
	await draw(8)
	player.camera.make_current(); scene.ui.show()
	var event_start := events.size()
	var accepted: Dictionary = scene.rama_runtime.cast_ability(id)
	if not accepted.get("accepted", false): finish("Ability reel request refused: " + id + " " + str(accepted)); return
	var cast_id := int(accepted.cast_id)
	var prefix := "ability-"+id+("-night" if night else "")
	# One real 60 Hz physics interval is shorter than the shortest 100 ms
	# windup. A whole 15 Hz capture frame can straddle two army ticks.
	await physics_frame
	await physics_frame
	paused = true
	if has_event("release", event_start, cast_id): finish("Windup frame already released: " + id); return
	await shot(prefix+"-windup", player.camera, "real runtime windup before authority release")
	if done: return
	for milestone in ["release", "impact", "end"]:
		var frames := 0
		while not has_event(milestone, event_start, cast_id) and frames < 130:
			paused = false
			await draw(1)
			frames += 1
			if has_event("cancel", event_start, cast_id): finish("Ability cancelled before " + milestone + ": " + id); return
		paused = true
		if not has_event(milestone, event_start, cast_id): finish("Missing actual " + milestone + " for " + id); return
		await shot(prefix+"-"+("expiry" if milestone == "end" else milestone), player.camera, "actual authority " + milestone + "; impact may share release frame for ward and step")
		if done: return
	ability_phases.append({"ability_id":id,"night":night,"cast_id":cast_id,"request":accepted,"events":events.slice(event_start),"phases":["windup","release","impact","expiry"],"normal_runtime_request":true,"normal_army_clock":true})

func rig_pose_pin() -> String:
	var poses: Array = []
	var rig: Skeleton3D = player.rama_motion.rig
	for index in rig.get_bone_count(): poses.append(normal(rig.get_bone_global_pose(index)))
	return JSON.stringify({"rig":normal(rig.global_transform),"poses":poses}, "", true, true).sha256_text()

func capture_character_detail() -> void:
	# Review-only candidate, intentionally after all ordinary gameplay views.
	var path := "res://scripts/rama_character_accents.gd"
	if not FileAccess.file_exists(path): finish("Optional character module missing"); return
	scene.reset_training(); scene.start_training()
	await draw(8)
	paused = true
	scene.ui.hide(); scene.title_light.show(); set_light(false)
	var rig: Skeleton3D = player.rama_motion.rig
	var head := rig.find_bone("head")
	if head < 0: finish("Review head bone missing"); return
	var center: Vector3 = rig.global_transform * rig.get_bone_global_pose(head).origin + Vector3(0,.075,0)
	review_camera.fov = 32.0
	for specification in [{"id":"face-front","offset":Vector3(-.10,.01,-.82)},{"id":"temple-three-quarter","offset":Vector3(-.64,.04,-.62)}]:
		review_camera.global_position = center + specification.offset
		review_camera.look_at(center)
		player.rama_lod._selector.reset()
		player.rama_lod.update(review_camera, 1.0/15.0)
		var before_pin := rig_pose_pin()
		var first := shots.size()
		await shot("character-"+specification.id+"-baseline", review_camera, "current runtime hero with existing title portrait light; optional wisps absent")
		if done: return
		var candidate: Node = load(path).new()
		scene.add_child(candidate)
		if not candidate.configure(player.visual): finish("Character candidate refused: " + str(candidate.report())); candidate.free(); return
		var active_report: Dictionary = candidate.report()
		await shot("character-"+specification.id+"-candidate", review_camera, "review-only temple wisps bound through configure; original framebuffer, same frozen camera")
		if done: candidate.release(); candidate.free(); return
		candidate.release()
		var released_report: Dictionary = candidate.report()
		candidate.free()
		var after_pin := rig_pose_pin()
		if before_pin != after_pin or shots[first].camera != shots[first+1].camera or player.visual.has_meta(&"rama_character_accents_owner"):
			finish("Character candidate changed pose/camera or failed release"); return
		character_pairs.append({"id":specification.id,"module":path,"module_sha256":FileAccess.get_sha256(path),"methods":["configure(player.visual)","report()","release()"],"options":{},"configured":active_report,"released":released_report,"baseline":shots[first],"candidate":shots[first+1],"pose_before_sha256":before_pin,"pose_after_sha256":after_pin,"same_pose":true,"same_camera":true,"review_only":true,"runtime_promoted":false,"lighting":"existing title portrait light enabled for both close-ups","acceptance":"independent visual review required"})

func capture_face_ablation() -> void:
	# Review-only single-variable ablations. Runtime source files are untouched.
	scene.start_training()
	await draw(8)
	paused = true
	scene.ui.hide(); scene.title_light.show(); set_light(false)
	var rig: Skeleton3D = player.rama_motion.rig
	var head := rig.find_bone("head")
	if head < 0: finish("Diagnostic head bone missing"); return
	var center: Vector3 = rig.global_transform * rig.get_bone_global_pose(head).origin + Vector3(0,.075,0)
	review_camera.fov = 32.0
	review_camera.global_position = center + Vector3(-.64,.04,-.62)
	review_camera.look_at(center)
	player.rama_lod._selector.reset()
	player.rama_lod.update(review_camera,1.0/15.0)
	var pose_pin := rig_pose_pin()
	var materials: Array[StandardMaterial3D] = []
	var material_state: Array = []
	for mesh in player.visual.find_children("*","MeshInstance3D",true,false):
		if mesh.mesh == null: continue
		for surface in mesh.mesh.get_surface_count():
			var material = mesh.get_active_material(surface)
			if material is StandardMaterial3D and material.resource_name.begins_with("Rama warm skin") and not material in materials:
				materials.append(material)
				material_state.append({"name":material.resource_name,"normal_enabled":material.normal_enabled,"normal_scale":material.normal_scale,"normal_texture":material.normal_texture.resource_path if material.normal_texture != null else ""})
	if materials.is_empty(): finish("No actual skin materials found for diagnostic"); return
	var sun_shadow: bool = scene.sun.shadow_enabled
	var environment: Environment = scene.world_environment.environment
	var ssao: bool = environment.ssao_enabled
	for mode in ["baseline","sun-shadow-off","skin-normal-off","ssao-off"]:
		if mode == "sun-shadow-off": scene.sun.shadow_enabled = false
		if mode == "skin-normal-off":
			for material in materials: material.normal_enabled = false
		if mode == "ssao-off": environment.ssao_enabled = false
		var active_normals: Array = []
		for material in materials: active_normals.append(material.normal_enabled)
		await shot("face-ablation-"+mode,review_camera,"review-only one-variable facial diagnostic: "+mode+"; existing title portrait light enabled")
		if done: return
		face_diagnostics.append({"mode":mode,"sun_shadow_enabled":scene.sun.shadow_enabled,"ssao_enabled":environment.ssao_enabled,"skin_normals_enabled":active_normals,"baseline_skin":material_state.duplicate(true),"baseline_sun_shadow":sun_shadow,"baseline_ssao":ssao,"pose_pin":rig_pose_pin(),"camera":shots.back().camera,"runtime_promoted":false})
		scene.sun.shadow_enabled = sun_shadow
		environment.ssao_enabled = ssao
		for index in materials.size(): materials[index].normal_enabled = material_state[index].normal_enabled
		if pose_pin != rig_pose_pin() or shots[0].camera != shots.back().camera: finish("Face diagnostic changed pose or camera"); return
	for index in materials.size():
		if materials[index].normal_enabled != material_state[index].normal_enabled: finish("Skin normal diagnostic failed restoration"); return

func capture_shadow_bias() -> void:
	# Diagnostic pairs keep dynamic shadows and all authored material data on.
	if shadow_world:
		scene.set_paused(false); scene.set_overview(false)
		scene.teleport_to(Vector3(-40,.05,-10),0)
	else: scene.start_training()
	await draw(8)
	paused = true
	set_light(shadow_night)
	var rig: Skeleton3D = player.rama_motion.rig
	var head := rig.find_bone("head")
	if head < 0: finish("Shadow diagnostic head missing"); return
	var center: Vector3 = rig.global_transform * rig.get_bone_global_pose(head).origin + Vector3(0,.075,0)
	review_camera.fov = 32.0
	review_camera.global_position = center + Vector3(-.64,.04,-.62)
	review_camera.look_at(center)
	player.rama_lod._selector.reset()
	player.rama_lod.update(review_camera,1.0/15.0)
	var pose_pin := rig_pose_pin()
	var baseline := {"shadow_enabled":scene.sun.shadow_enabled,"shadow_bias":scene.sun.shadow_bias,"shadow_normal_bias":scene.sun.shadow_normal_bias}
	if not baseline.shadow_enabled or not is_equal_approx(baseline.shadow_bias,.025) or not is_equal_approx(baseline.shadow_normal_bias,.35): finish("Unexpected baseline shadow values: "+str(baseline)); return
	var modes: Array = shadow_modes()
	var cameras := {}
	for mode in modes:
		scene.sun.shadow_bias = {"baseline":.025,"depth":.1,"normal":.025,"both":.1,"defaults":.1,"depth2":.2,"depth4":.4}[mode]
		scene.sun.shadow_normal_bias = 2.0 if mode == "defaults" else (1.0 if mode in ["normal","both"] else .35)
		for view in ["face","gameplay"]:
			scene.ui.visible = view == "gameplay"
			if not shadow_world: scene.title_light.visible = view == "face"
			var active_camera: Camera3D = review_camera if view == "face" else player.camera
			var id: String = "shadow-bias-"+mode+"-"+view+("-night" if shadow_night else "-day")
			await shot(id,active_camera,"review-only shadow bias diagnosis with shadows enabled; "+view+" view")
			if done: return
			if cameras.has(view) and shots.back().camera != cameras[view]: finish("Shadow diagnostic changed matched camera"); return
			cameras[view] = shots.back().camera
			if pose_pin != rig_pose_pin(): finish("Shadow diagnostic changed pose"); return
			shadow_diagnostics.append({"mode":mode,"view":view,"night":shadow_night,"shadow_enabled":scene.sun.shadow_enabled,"shadow_bias":scene.sun.shadow_bias,"shadow_normal_bias":scene.sun.shadow_normal_bias,"baseline":baseline,"pose_pin":pose_pin,"camera":shots.back().camera,"runtime_promoted":false,"title_portrait_light":false if shadow_world else scene.title_light.visible,"scene":"confluence" if shadow_world else "courtyard"})
	scene.sun.shadow_bias = baseline.shadow_bias
	scene.sun.shadow_normal_bias = baseline.shadow_normal_bias
	if scene.sun.shadow_enabled != baseline.shadow_enabled: finish("Shadow toggle changed unexpectedly")

func shadow_modes() -> Array:
	if shadow_bias_mode == "all": return ["baseline","depth","normal","both"]
	if shadow_bias_mode == "final": return ["defaults","depth2","depth4"]
	if shadow_bias_mode == "confirm": return ["baseline","depth2"]
	return [shadow_bias_mode]

func draw(count: int) -> void:
	for index in range(count):
		await process_frame
		await RenderingServer.frame_post_draw

func set_light(night: bool) -> void:
	if shadow_world: scene.set_review_phase(1.0 if night else 0.0)
	else:
		scene.night = night
		scene._apply_settings()

func place_hero_camera() -> void:
	# Explicit framing in metres, independent of changed vertex bounds.
	review_camera.global_position = player.global_position + Vector3(-1.45, 1.30, -3.55)
	review_camera.look_at(player.global_position + Vector3(0, 1.08, 0))
	review_camera.reset_physics_interpolation()

func shot(id: String, camera: Camera3D, scope: String) -> void:
	camera.make_current(); camera.reset_physics_interpolation()
	if is_instance_valid(player.rama_lod): player.rama_lod.update(camera, 1.0/15.0)
	await draw(4)
	var image := root.get_texture().get_image()
	var filename := id + ".png"
	if image.is_empty() or image.get_size() != SIZE or image.save_png(output.path_join(filename)) != OK: finish("Framebuffer write failed"); return
	shots.append({"id":id,"file":filename,"sha256":FileAccess.get_sha256(output.path_join(filename)),"viewport":[SIZE.x,SIZE.y],"camera":{"transform":normal(camera.global_transform),"fov":camera.fov,"near":camera.near,"far":camera.far},"night":scene.night,"ui_visible":scene.ui.visible,"player_transform":normal(player.global_transform),"lod":player.rama_lod.report(),"motion":player.rama_motion.diagnostics(),"render_frame":Engine.get_frames_drawn(),"physics_frame":Engine.get_physics_frames(),"tree_paused":paused,"scope":scope})
	print("VISUAL_CAMPAIGN_SHOT ", filename)

func normal(value: Variant) -> Variant:
	if value is Vector2: return [value.x,value.y]
	if value is Vector3: return [value.x,value.y,value.z]
	if value is Vector4 or value is Quaternion: return [value.x,value.y,value.z,value.w]
	if value is Transform3D: return [normal(value.basis.x),normal(value.basis.y),normal(value.basis.z),normal(value.origin)]
	if value is Dictionary:
		var result := {}
		for key in value: result[key] = normal(value[key])
		return result
	if value is Array:
		var result := []
		for item in value: result.append(normal(item))
		return result
	return value

func collect_files(path: String, paths: Array[String]) -> void:
	for name in DirAccess.get_files_at(path):
		if not name.ends_with(".import") and not name.ends_with(".uid"): paths.append(path.path_join(name))
	for name in DirAccess.get_directories_at(path): collect_files(path.path_join(name), paths)

func source_hashes() -> Dictionary:
	var paths: Array[String] = ["res://project.godot","res://tools/visual-campaign/capture.gd","res://tools/visual-campaign/run.py"]
	if shadow_world: paths.append("res://art/world/confluence-map.json")
	for directory in ["res://scripts","res://shaders","res://scenes","res://assets"]: collect_files(directory, paths)
	paths.sort()
	var result := {}
	for path in paths: result[path] = FileAccess.get_sha256(path)
	return result

func freeze_background_time() -> void:
	var seen := {}
	for node in scene.find_children("*", "MeshInstance3D", true, false):
		if not node.mesh: continue
		for surface in node.mesh.get_surface_count():
			var material = node.get_active_material(surface)
			if not material is ShaderMaterial or material.shader == null or seen.has(material.get_instance_id()): continue
			seen[material.get_instance_id()] = true
			if material.shader.resource_path in ["res://scripts/world_water.gdshader","res://shaders/production_water.gdshader"]:
				material.set_shader_parameter("animation_speed", 0.0)
				time_controls.append({"shader":material.shader.resource_path,"animation_speed":0.0})

func finish(failure: String) -> void:
	if done: return
	done = true
	var after := source_hashes() if not sources.is_empty() else {}
	var ability_count := selected_abilities.size() if not selected_abilities.is_empty() else ABILITY_IDS.size()
	var expected := (0 if abilities_only else 8) + (4*ability_count*(2 if ability_night else 1) if ability_reel else 0) + (1 if title_night and not abilities_only else 0) + (4 if character_detail else 0)
	if face_ablation: expected = 4
	if not shadow_bias_mode.is_empty(): expected = 2 * shadow_modes().size()
	var report := {"schema":1,"kind":"actual-courtyard-visual-campaign","camera_contract":"courtyard-eight-v1","complete":failure.is_empty() and sources == after and shots.size() == expected,"failure":failure,"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources == after,"shots":shots,"ability_events":events,"ability_reel":ability_reel,"abilities_only":abilities_only,"title_night":title_night,"character_detail":character_detail,"character_pairs":character_pairs,"face_ablation":face_ablation,"face_diagnostics":face_diagnostics,"shadow_bias_mode":shadow_bias_mode,"shadow_world":shadow_world,"shadow_diagnostics":shadow_diagnostics,"ability_phases":ability_phases,"expected_raw_pngs":expected,"time_controls":time_controls,"clocks":{"fixed_capture_process_hz":15,"physics_hz":Engine.physics_ticks_per_second,"army_authority_hz":20,"hardware_fps_measured":false},"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"Original native Forward+ framebuffers. Fixed 15 simulation frames/second is a capture clock, not measured hardware FPS. Paused lifecycle milestones and optional review-only geometry do not qualify continuous motion, gameplay feel or commercial graphics parity."}
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("VISUAL_CAMPAIGN_COMPLETE ", report.complete, " ", failure)
	paused = false
	if is_instance_valid(scene):
		for node in scene.find_children("*","AudioStreamPlayer",true,false): node.stop(); node.stream = null
		scene.queue_free()
	for index in range(3): await process_frame
	await create_timer(.1,true,false,true).timeout
	quit(0 if report.complete else 1)
