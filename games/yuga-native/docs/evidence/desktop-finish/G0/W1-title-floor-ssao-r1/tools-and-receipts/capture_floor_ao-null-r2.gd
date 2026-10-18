extends "res://tools/ui-campaign/observer.gd"
## Source-only AO diagnostic: identical helper in both private branches.
## Two ordinary product cameras; no settings/pose/clock overrides.
## Native parse/preflight and actual pair remain UNRUN.
var preflight := false
var sources: Dictionary = {}
var shots: Array = []
var checkpoints: Array = []
var done := false
var serialization_errors: Array[String] = []
var resource_rows: Dictionary = {}
var material_ids: Dictionary = {}
const ATMOSPHERE_BASELINE = "40739a23b74149cebda62acd6af8a7ca54ac1a39aab2538adbc5211d309a1373"
const ATMOSPHERE_CANDIDATE = "25de5c6186aed64fa2e6df7fdb1eae545b07fea2594a6d2b9fbc0b9af6a85af0"

func _initialize() -> void:
	call_deferred("run")

func _process(_delta: float) -> bool:
	return false

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--case=scene-anchors": pass
		elif arg == "--preflight": preflight = true
		else: finish("Unknown scene-anchor argument " + arg); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus"):
		finish("X11 Forward+ required"); return
	seed(741031)
	mode = "scene-anchors"
	root.size = Vector2i(960, 540)
	root.content_scale_size = Vector2i(1280, 720)
	root.title = "YUGA source-bound ordinary scene anchors"
	if not preflight: root.show()
	sources = source_hashes()
	var scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	checkpoint("before_initial_draw6")
	await draw_frames(6)
	checkpoint("after_initial_draw6")
	if not scene.environment_ready or not scene.player.model_ready: finish("Actual environment/hero missing"); return
	if not await take_anchor("00-title", scene.title_camera): return
	checkpoint("before_start_training")
	scene.start_training()
	await draw_frames(12)
	checkpoint("after_training_draw12")
	if not await take_anchor("01-training", scene.player.camera): return
	finish("")

func draw_frames(count: int) -> void:
	for index in count:
		if preflight:
			for tick in 2: await physics_frame
		else:
			await process_frame
			await RenderingServer.frame_post_draw

func checkpoint(stage: String) -> void:
	var item := {"stage": stage, "wall_ms": Time.get_ticks_msec(), "physics_frame": Engine.get_physics_frames(), "render_frame": Engine.get_frames_drawn(), "paused": paused}
	checkpoints.append(item)
	print("SCENE_ANCHOR_STAGE ", JSON.stringify(item))

func vector(value: Vector3) -> Array:
	return [value.x, value.y, value.z]


func transform_values(value: Transform3D) -> Array:
	return [vector(value.basis.x), vector(value.basis.y), vector(value.basis.z), vector(value.origin)]

func encode_value(value: Variant, depth: int = 0) -> Variant:
	if depth > 16:
		serialization_errors.append("resource/property depth exceeds16")
		return null
	match typeof(value):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING: return value
		TYPE_STRING_NAME, TYPE_NODE_PATH: return String(value)
		TYPE_FLOAT:
			if not is_finite(value): serialization_errors.append("nonfinite scalar")
			return value if is_finite(value) else null
		TYPE_VECTOR2, TYPE_VECTOR2I: return encode_value([value.x,value.y],depth+1)
		TYPE_VECTOR3, TYPE_VECTOR3I: return encode_value([value.x,value.y,value.z],depth+1)
		TYPE_VECTOR4, TYPE_VECTOR4I, TYPE_QUATERNION: return encode_value([value.x,value.y,value.z,value.w],depth+1)
		TYPE_COLOR: return encode_value([value.r,value.g,value.b,value.a],depth+1)
		TYPE_RECT2, TYPE_RECT2I: return encode_value([value.position,value.size],depth+1)
		TYPE_AABB: return encode_value([value.position,value.size],depth+1)
		TYPE_PLANE: return encode_value([value.normal,value.d],depth+1)
		TYPE_BASIS: return encode_value([value.x,value.y,value.z],depth+1)
		TYPE_TRANSFORM3D: return encode_value(transform_values(value),depth+1)
		TYPE_TRANSFORM2D: return encode_value([value.x,value.y,value.origin],depth+1)
		TYPE_PROJECTION: return encode_value([value.x,value.y,value.z,value.w],depth+1)
		TYPE_DICTIONARY:
			var result: Dictionary = {}
			for key in value:
				if typeof(key) not in [TYPE_STRING,TYPE_STRING_NAME]:
					serialization_errors.append("non-string dictionary key")
					continue
				result[String(key)] = encode_value(value[key],depth+1)
			return result
		TYPE_OBJECT:
			if value == null: return null
			if value is Resource: return resource_value(value,depth+1)
			if value is Node: return {"node_path":String(current_scene.get_path_to(value))}
			serialization_errors.append("unsupported object "+value.get_class())
			return null
		TYPE_RID:
			serialization_errors.append("opaque RID in stored property")
			return null
	if value is Array or typeof(value) >= TYPE_PACKED_BYTE_ARRAY:
		var result: Array = []
		for item in value: result.append(encode_value(item,depth+1))
		return result
	serialization_errors.append("unsupported variant "+str(typeof(value)))
	return null

func stored_properties(object: Object, depth: int = 0) -> Dictionary:
	var result: Dictionary = {}
	var names: Array[String] = []
	for property in object.get_property_list():
		var name := String(property.name)
		# Script bytes and imported/raw closure are already pinned separately.
		# Instance IDs, ResourceUIDs and inspector categories are not controls.
		if property.usage & PROPERTY_USAGE_STORAGE and name not in ["script","resource_path","resource_scene_unique_id"]:
			names.append(name)
	names.sort()
	for name in names: result[name] = encode_value(object.get(name),depth+1)
	return result

func resource_value(resource: Resource, depth: int) -> Dictionary:
	var path := resource.resource_path
	var origin := path.get_slice("::",0)
	var row := {"class":resource.get_class(),"path":path}
	if origin.begins_with("res://") and FileAccess.file_exists(origin): row.source_sha256 = FileAccess.get_sha256(origin)
	# External/embedded textures are identified by exact raw source and import
	# closure, never by GPU instance IDs or a readback that changes timing.
	if resource is Texture2D and not path.is_empty(): return row
	if resource is Shader:
		row.code = resource.code
		return row
	row.properties = stored_properties(resource,depth+1)
	if resource is ShaderMaterial and resource.shader:
		row.shader_uniforms = {}
		for uniform in resource.shader.get_shader_uniform_list():
			row.shader_uniforms[String(uniform.name)] = encode_value(resource.get_shader_parameter(uniform.name),depth+1)
	return row

func material_id(material: Material) -> String:
	if not material: return "none"
	var instance := material.get_instance_id()
	if material_ids.has(instance): return material_ids[instance]
	var row := resource_value(material,0)
	var key := JSON.stringify(row).sha256_text()
	resource_rows[key] = row
	material_ids[instance] = key
	return key

func collect_scene_controls(node: Node, lights: Array, meshes: Array) -> void:
	if node is Light3D:
		lights.append({"path":String(current_scene.get_path_to(node)),"class":node.get_class(),"global_transform":encode_value(node.global_transform),"visible":node.is_visible_in_tree(),"properties":stored_properties(node)})
	if node is MeshInstance3D and node.mesh:
		var surfaces: Array = []
		for index in node.mesh.get_surface_count(): surfaces.append(material_id(node.get_active_material(index)))
		meshes.append({"path":String(current_scene.get_path_to(node)),"mesh_path":node.mesh.resource_path,"global_transform":encode_value(node.global_transform),"visible":node.is_visible_in_tree(),"layers":node.layers,"cast_shadow":node.cast_shadow,"transparency":node.transparency,"material_override":material_id(node.material_override),"material_overlay":material_id(node.material_overlay),"surfaces":surfaces})
	for child in node.get_children(): collect_scene_controls(child,lights,meshes)

func diagnostic_controls(scene: Node3D, camera: Camera3D) -> Dictionary:
	resource_rows.clear()
	material_ids.clear()
	var skeleton: Skeleton3D = scene.player.rama_motion.rig
	var bone_names: Array = []
	var bone_poses: Array = []
	for index in skeleton.get_bone_count():
		bone_names.append(String(skeleton.get_bone_name(index)))
		bone_poses.append(encode_value(skeleton.get_bone_global_pose(index)))
	var environment: Environment = scene.world_environment.environment
	var ao: Dictionary = {}
	for property in environment.get_property_list():
		if String(property.name).begins_with("ssao_"): ao[String(property.name)] = encode_value(environment.get(property.name))
	var lights: Array = []
	var meshes: Array = []
	collect_scene_controls(scene,lights,meshes)
	var motion: Dictionary = {}
	for name in ["phase","locomotion_age","transition_age","action_elapsed","action","action_stage","locomotion","grounded","traversal"]: motion[name] = encode_value(scene.player.rama_motion.get(name))
	var render_settings: Dictionary = {}
	for name in ["rendering/anti_aliasing/quality/msaa_3d","rendering/anti_aliasing/quality/use_taa","rendering/textures/default_filters/anisotropic_filtering_level","rendering/textures/default_filters/use_nearest_mipmap_filter"]:
		render_settings[name] = encode_value(ProjectSettings.get_setting(name))
	return {"hero_skeleton":{"bone_names":bone_names,"bone_global_poses":bone_poses},"hero_global_transform":encode_value(scene.player.global_transform),"hero_velocity":encode_value(scene.player.velocity),"visual_transform":encode_value(scene.player.visual.global_transform),"camera_properties":stored_properties(camera),"environment":stored_properties(environment),"ao":ao,"lights":lights,"meshes":meshes,"materials":resource_rows.duplicate(true),"clocks":{"elapsed":scene.elapsed,"footstep_clock":scene.footstep_clock,"feedback_clock":scene.feedback_clock,"motion":motion,"kit":encode_value(scene.rama_runtime.kit.report()),"traversal":encode_value(scene.player.traversal.report())},"viewport_msaa_3d":root.msaa_3d,"viewport_use_taa":root.use_taa,"render_settings":render_settings,"renderer":RenderingServer.get_current_rendering_method(),"serialization_errors":serialization_errors.duplicate()}

func take_anchor(id: String, camera: Camera3D) -> bool:
	if root.get_camera_3d() != camera: finish("Product camera is not active: " + id); return false
	var state := snapshot()
	state.id = id
	state.diagnostic = diagnostic_controls(current_scene,camera)
	var atmosphere_hash := FileAccess.get_sha256("res://scripts/hero_atmosphere.gd")
	state.atmosphere_sha256 = atmosphere_hash
	state.branch = "baseline" if atmosphere_hash == ATMOSPHERE_BASELINE else "candidate" if atmosphere_hash == ATMOSPHERE_CANDIDATE else "unknown"
	if state.branch == "unknown": finish("Unrecognized atmosphere source"); return false
	if not serialization_errors.is_empty(): finish("Unsupported/nonfinite control serialization: "+str(serialization_errors)); return false
	if state.diagnostic.hero_skeleton.bone_names.size() != 164 or state.diagnostic.hero_skeleton.bone_global_poses.size() != 164: finish("Expected actual164bone skeleton"); return false
	if not preflight and state.diagnostic.ao.ssao_enabled != (state.branch == "baseline"): finish("Actual AO getter disagrees with declared one-parameter branch"); return false
	state.render_frame = Engine.get_frames_drawn()
	state.camera = {"path": str(camera.get_path()), "matches_expected_product_camera": true, "fov": camera.fov, "near": camera.near, "far": camera.far, "transform": [vector(camera.global_basis.x), vector(camera.global_basis.y), vector(camera.global_basis.z), vector(camera.global_position)]}
	state.canvas_size = [root.content_scale_size.x, root.content_scale_size.y]
	state.scope = "Actual product camera/UI/light/pose; direct start_training API is a declared fixture action, not native input. Settled frames do not certify initial support acquisition."
	if not preflight:
		var original := root.get_texture().get_image()
		state.framebuffer_size = [original.get_width(), original.get_height()]
		state.file = id + ".png"
		if original.save_png(output.path_join(state.file)) != OK: finish("PNG write failed"); return false
		state.sha256 = FileAccess.get_sha256(output.path_join(state.file))
	shots.append(state)
	_write(output.path_join(id + ".json"), state)
	print("SCENE_ANCHOR_SHOT ", id)
	return true

func source_hashes() -> Dictionary:
	var seal: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://.graphics-six-snapshot.json"))
	var result := {}
	for name in seal.files:
		result[name] = FileAccess.get_sha256("res://" + name)
	result[".graphics-six-snapshot.json"] = FileAccess.get_sha256("res://.graphics-six-snapshot.json")
	return result

func finish(failure: String) -> void:
	if done: return
	done = true
	var after := source_hashes() if not sources.is_empty() else {}
	var checks := [{"name": "two ordinary camera observations", "passed": shots.size() == 2}, {"name": "source unchanged", "passed": sources == after}]
	if shots.size() == 2:
		checks.append({"name": "actual inactive title and active training", "passed": not shots[0].state.player_active and shots[1].state.player_active and not shots[0].state.started and shots[1].state.started})
		checks.append({"name": "title menu then gameplay HUD", "passed": shots[0].panels.main_panel and not shots[1].panels.main_panel and shots[1].hero_hud.visible})
		checks.append({"name": "expected product cameras", "passed": shots.all(func(s): return s.camera.matches_expected_product_camera)})
	var passed := failure.is_empty() and checks.all(func(c): return c.passed)
	var report := {"schema": 1, "case": "scene-anchors", "complete": passed, "failure": failure, "shots": shots, "checks": checks, "checkpoints": checkpoints, "source_sha256": sources, "source_after_sha256": after, "source_unchanged": sources == after, "preflight": preflight, "renderer": RenderingServer.get_current_rendering_method(), "adapter": RenderingServer.get_video_adapter_name(), "scope": "Two settled source-bound actual title/gameplay cameras. No quality or hardware performance claim from mechanical checks."}
	print("AO_DIAGNOSTIC_SHOTS ", passed, " ", failure)
	paused = false
	if is_instance_valid(current_scene): current_scene.queue_free()
	for index in 8: await process_frame
	# Identical proven cleanup for both branches; never change runtime audio.
	var started := Time.get_ticks_usec()
	var previous := AudioServer.get_time_since_last_mix()
	var observed := 0
	var samples: Array[Dictionary] = []
	while observed < 2 and Time.get_ticks_usec()-started < 250000:
		OS.delay_msec(1)
		var now := AudioServer.get_time_since_last_mix()
		if now+.0002 < previous: observed += 1
		samples.append({"wall_usec":Time.get_ticks_usec()-started,"since_mix_s":now,"ticks":observed})
		previous = now
	var wait_usec := Time.get_ticks_usec()-started
	for index in 8: await process_frame
	checks.append({"name":"two real mixer ticks within250ms cleanup budget","passed":observed==2 and wait_usec<=250000})
	report.audio_cleanup = {"observed_mixer_ticks":observed,"wait_usec":wait_usec,"budget_usec":250000,"samples":samples,"main_cleanup_frames":8,"scope":"Harness shutdown after scene free; no runtime audio change."}
	report.complete = failure.is_empty() and checks.all(func(c):return c.passed)
	if not output.is_empty(): _write(output.path_join("preflight.json" if preflight else "capture.json"), report)
	print("AO_DIAGNOSTIC_FINAL ",report.complete)
	quit(0 if report.complete else 1)
