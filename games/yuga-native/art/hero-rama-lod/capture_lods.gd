extends SceneTree
## Actual Confluence LOD comparisons. Only capture fixtures change visibility.
## Same live rig, face, camera, pose, materials and lighting within every pair.
const SIZE := Vector2i(1280,960)
const FPS := 15
const TAKE_FRAMES := 30
const ORIGIN := Vector3(-40,.05,-10)
const HERO_IMPORTS := ["res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb"]
const CAMERA_SIZES := [780.0,350.0,120.0]
var output := ""
var pairs_only := false
var scene: Node3D
var player: CharacterBody3D
var lod: Node
var camera: Camera3D
var label: Label
var sources := {}
var imports := {}
var texture_pins := {}
var poses: Array = []
var pairs: Array = []
var frames: Array = []
var time_controls: Array = []
var time_uncontrolled: Array = []
var started := Time.get_ticks_msec()
var completed := false

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--pairs-only": pairs_only = true
		else: finish("Unknown argument: " + arg); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Require a fresh absolute output"); return
	DirAccess.make_dir_recursive_absolute(output)
	if DisplayServer.get_name() == "headless" or RenderingServer.get_current_rendering_method() != "forward_plus": finish("Actual Forward+ display required"); return
	if Engine.physics_ticks_per_second != 60: finish("60Hz native physics required"); return
	sources = source_hashes()
	for path in sources:
		if path.ends_with(".glb") and not fresh_import(path): finish("Missing/stale imported GLB: " + path); return
	root.size = SIZE; root.content_scale_size = SIZE; root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA — actual one-rig LOD appearance review"; root.show()
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await draw(8)
	if not scene.world_ready or not scene.player.model_ready or not scene.rama_runtime.configured: finish("Actual world/current hero runtime not configured"); return
	scene.set_paused(false); scene.set_overview(false); scene.set_review_phase(0.0)
	scene.teleport_to(ORIGIN,180.0)
	player = scene.player; lod = player.rama_lod
	if not is_instance_valid(lod) or not lod.configured or lod.report().levels != 3 or not lod.report().errors.is_empty(): finish("Three actual mesh levels must bind without errors"); return
	if not player.rama_face.configured or not player.rama_secondary.configured: finish("Actual face and secondary controllers must bind"); return
	scene.ui.hide()
	scene.rama_effects.visible = false
	camera = Camera3D.new(); scene.add_child(camera)
	camera.fov = 43.0; camera.keep_aspect = Camera3D.KEEP_HEIGHT; camera.make_current()
	var overlay := CanvasLayer.new(); overlay.layer = 100; root.add_child(overlay)
	label = Label.new(); overlay.add_child(label); label.position = Vector2(18,15)
	label.add_theme_font_size_override("font_size",16)
	label.add_theme_color_override("font_color",Color("f1d7a0"))
	label.add_theme_color_override("font_outline_color",Color("101820"))
	label.add_theme_constant_override("outline_size",6)
	freeze_background_time()
	place_camera(780.0)
	await draw(10)
	if not player.is_on_floor(): finish("Actual CharacterBody must be grounded before pose capture"); return
	for pose_id in ["idle","draw"]:
		paused = false
		var accepted := {}
		if pose_id == "draw":
			accepted = scene.cast_rama_ability("piercing_dawn")
			if not accepted.get("accepted",false): finish("Real PiercingDawn cast rejected"); return
			await draw(4)
		paused = true
		await draw(3)
		var frozen := frozen_state()
		if not valid_state(frozen): finish("Expected one live164-bone rig, unique native face and finite frozen state"); return
		if pose_id == "draw" and frozen.controllers.motion.stage not in ["windup","hold"]: finish("Draw fixture missed the actual windup"); return
		var pin := state_pin(frozen)
		poses.append({"id":pose_id,"actual_cast":normal(accepted),"state_sha256":pin,"state":frozen})
		for index in CAMERA_SIZES.size():
			var target: float = CAMERA_SIZES[index]
			place_camera(target)
			lod._selector.reset()
			if not lod.update(camera,1.0/FPS) or lod.level != index: finish("Actual screen-space selector did not choose expected level at " + str(target)); return
			var actual_level: int = lod.level
			label.text = "RAMA / " + String(pose_id).to_upper() + " / %.0fpx / MATCHED CAMERA + FROZEN CONTROLLERS" % target
			# Near reference is a disclosed capture-only visibility override. It
			# changes no selector history, rig pose, material, morph or controller.
			lod._apply_level(0)
			var reference: Dictionary = await shot(String(pose_id)+"-"+str(int(target))+"-reference",pin)
			if completed: return
			if not lod.update(camera,1.0/FPS) or lod.level != actual_level: finish("Candidate selection changed during matched pair"); return
			var candidate: Dictionary = await shot(String(pose_id)+"-"+str(int(target))+"-selected",pin)
			if completed: return
			if reference.camera != candidate.camera or reference.state_sha256 != candidate.state_sha256: finish("Matched pair camera/controller state changed"); return
			pairs.append({"pose":pose_id,"target_hero_pixels":target,"selected_level":actual_level,"reference":reference,"candidate":candidate,"reference_override":"Near meshes only; source face remains unique","same_camera":true,"same_frozen_state":true})
	if not pairs_only:
		var pin := state_pin(frozen_state())
		lod.reset("camera-take start")
		var prior_tick := -1
		var prior_draw := -1
		for index in TAKE_FRAMES:
			var triangle := 1.0-absf(2.0*float(index)/float(TAKE_FRAMES-1)-1.0)
			var target := exp(lerpf(log(780.0),log(75.0),triangle))
			place_camera(target)
			lod.update(camera,1.0/FPS)
			label.text = "RAMA / FROZEN DRAW / CAMERA TAKE / LEVEL " + str(lod.level) + " / 15Hz SAMPLED"
			var image: Dictionary = await shot("frame-%05d"%index,pin,1)
			if completed: return
			var ticks: int = image.physics_tick-prior_tick if prior_tick >= 0 else 0
			var draws: int = image.render_frame-prior_draw if prior_draw >= 0 else 0
			if index > 0 and (ticks != 4 or draws <= 0): finish("Camera take skipped a fixed sample"); return
			frames.append({"index":index,"sample_time_s":float(index)/FPS,"target_hero_pixels":target,"physics_tick_delta":ticks,"render_frame_delta":draws,"image":image})
			prior_tick = image.physics_tick; prior_draw = image.render_frame
	finish("")

func draw(count: int) -> void:
	for index in count:
		await process_frame
		await RenderingServer.frame_post_draw

func place_camera(target_pixels: float) -> void:
	var rig: Skeleton3D = player.rama_motion.rig
	var center: Vector3 = rig.global_transform * lod._bounds.get_center()
	var height: float = (rig.global_basis*Vector3.UP).length()*lod._bounds.size.y
	var distance: float = float(SIZE.y)*height/(2.0*tan(deg_to_rad(camera.fov)*.5)*target_pixels)
	# Looking along the actual straight western lane avoids moving through
	# unrelated buildings while comparing long camera distances.
	camera.global_position = center+Vector3(0,0,-distance)
	camera.look_at(center); camera.reset_physics_interpolation()

func source_hashes() -> Dictionary:
	var paths: Array[String] = ["res://project.godot","res://art/world/confluence-map.json","res://art/hero-rama-lod/capture_lods.gd","res://art/hero-rama-lod/run_capture.py"]
	for directory in ["res://scripts","res://shaders","res://assets","res://scenes"]: collect_files(directory,paths)
	paths.sort()
	var result := {}
	for path in paths: result[path] = FileAccess.get_sha256(path)
	return result

func collect_files(path: String, result: Array[String]) -> void:
	for file in DirAccess.get_files_at(path): result.append(path.path_join(file))
	for directory in DirAccess.get_directories_at(path): collect_files(path.path_join(directory),result)

func fresh_import(path: String) -> bool:
	var config := ConfigFile.new()
	if config.load(path+".import") != OK: return false
	var imported: String = config.get_value("remap","path","")
	var stamp := imported.get_basename()+".md5"
	if imported.is_empty() or not FileAccess.file_exists(imported) or not FileAccess.file_exists(stamp): return false
	var pattern := RegEx.new()
	var text := FileAccess.get_file_as_string(stamp)
	for entry in [["source_md5",path],["dest_md5",imported]]:
		pattern.compile(String(entry[0])+'="([a-f0-9]+)"')
		var match_ := pattern.search(text)
		if match_ == null or match_.get_string(1) != FileAccess.get_md5(entry[1]): return false
	var auto_lod: bool = config.get_value("params","meshes/generate_lods",true)
	if HERO_IMPORTS.has(path) and auto_lod: return false
	imports[path] = {"fresh":true,"source_sha256":FileAccess.get_sha256(path),"metadata":path+".import","metadata_sha256":FileAccess.get_sha256(path+".import"),"imported":imported,"sha256":FileAccess.get_sha256(imported),"stamp":stamp,"stamp_sha256":FileAccess.get_sha256(stamp),"generate_lods":auto_lod}
	return true

func has_time(shader: Shader) -> bool:
	var comments := RegEx.new(); comments.compile("(?m)//[^\\n]*")
	var code := comments.sub(shader.code,"",true)
	comments.compile("(?s)/\\*.*?\\*/"); code = comments.sub(code,"",true)
	var token := RegEx.new(); token.compile("\\bTIME\\b")
	return token.search(code) != null

func freeze_background_time() -> void:
	var seen := {}
	for node in scene.find_children("*","MeshInstance3D",true,false):
		var mesh: MeshInstance3D = node
		if not mesh.mesh: continue
		for surface in mesh.mesh.get_surface_count():
			var material := mesh.get_active_material(surface)
			if not material is ShaderMaterial or material.shader == null or not has_time(material.shader) or seen.has(material.get_instance_id()): continue
			seen[material.get_instance_id()] = true
			var entry := {"mesh":String(mesh.get_path()),"surface":surface,"shader":material.shader.resource_path,"shader_sha256":material.shader.code.sha256_text()}
			if material.shader.resource_path in ["res://scripts/world_water.gdshader","res://shaders/production_water.gdshader"]:
				entry.before = normal(material.get_shader_parameter("animation_speed"))
				material.set_shader_parameter("animation_speed",0.0)
				entry.capture_animation_speed = 0.0
				time_controls.append(entry)
			else: time_uncontrolled.append(entry)

func normal(value: Variant) -> Variant:
	if value is Vector2: return [value.x,value.y]
	if value is Vector3: return [value.x,value.y,value.z]
	if value is Vector4 or value is Quaternion: return [value.x,value.y,value.z,value.w]
	if value is Color: return [value.r,value.g,value.b,value.a]
	if value is Transform3D: return [normal(value.basis.x),normal(value.basis.y),normal(value.basis.z),normal(value.origin)]
	if value is Resource:
		var path: String = value.resource_path
		if not path.is_empty() and FileAccess.file_exists(path): texture_pins[path] = FileAccess.get_sha256(path)
		return {"class":value.get_class(),"name":value.resource_name,"path":path,"id":value.get_instance_id()}
	if value is Dictionary:
		var result := {}
		for key in value: result[key] = normal(value[key])
		return result
	if value is Array:
		var result := []
		for item in value: result.append(normal(item))
		return result
	return value

func frozen_state() -> Dictionary:
	var rig: Skeleton3D = player.rama_motion.rig
	var bones := []
	for index in rig.get_bone_count(): bones.append({"name":String(rig.get_bone_name(index)),"parent":rig.get_bone_parent(index),"rest":normal(rig.get_bone_rest(index)),"global_pose":normal(rig.get_bone_global_pose(index))})
	var meshes := []
	var faces := 0
	var hero_time := []
	for node in player.visual.find_children("*","MeshInstance3D",true,false):
		var mesh: MeshInstance3D = node
		if not mesh.mesh: continue
		if mesh.name == "RamaFace": faces += 1
		var row := {"path":String(mesh.get_path()),"transform":normal(mesh.global_transform),"mesh":normal(mesh.mesh),"skin_id":mesh.skin.get_instance_id() if mesh.skin else 0,"skeleton_path":String(mesh.skeleton),"materials":[],"morphs":{}}
		if mesh.mesh is ArrayMesh:
			for index in mesh.mesh.get_blend_shape_count(): row.morphs[String(mesh.mesh.get_blend_shape_name(index))] = mesh.get_blend_shape_value(index)
		for index in mesh.mesh.get_surface_count():
			var material := mesh.get_active_material(index)
			var state := {"surface":index,"material":normal(material)}
			if material is ShaderMaterial and material.shader != null:
				state.shader_sha256 = material.shader.code.sha256_text()
				state.uniforms = {}
				for uniform in material.shader.get_shader_uniform_list(): state.uniforms[String(uniform.name)] = normal(material.get_shader_parameter(uniform.name))
				if has_time(material.shader): hero_time.append(String(mesh.get_path()))
			elif material is StandardMaterial3D:
				state.pbr = normal({"albedo":material.albedo_color,"roughness":material.roughness,"metallic":material.metallic,"specular":material.metallic_specular,"normal_scale":material.normal_scale,"base_texture":material.albedo_texture,"normal_texture":material.normal_texture,"roughness_texture":material.roughness_texture,"metallic_texture":material.metallic_texture})
			row.materials.append(state)
		meshes.append(row)
	var motion: Dictionary = player.rama_motion.diagnostics()
	# Rendering may increment observation counters with the same functional
	# controller state. Keep the raw report separately, not in equality hashes.
	for key in ["modified_samples","max_contact_error_m","max_string_error_m"]: motion.erase(key)
	return normal({"rig_transform":rig.global_transform,"bones":bones,"live_rigs":player.visual.find_children("*","Skeleton3D",true,false).size(),"face_meshes":faces,"meshes":meshes,"hero_time_shaders":hero_time,"controllers":{"motion":motion,"face":player.rama_face.report(),"secondary":player.rama_secondary.report(),"kit":scene.rama_runtime.kit.report(),"vitals":scene.rama_runtime.vitals.report()},"lighting":{"phase":scene.phase,"exposure":scene.world_environment.environment.tonemap_exposure,"sun_transform":scene.sun.global_transform,"sun_energy":scene.sun.light_energy,"sun_color":scene.sun.light_color}})

func state_pin(state: Dictionary) -> String:
	return JSON.stringify(state,"",true,true).sha256_text()

func valid_state(state: Dictionary) -> bool:
	return state.live_rigs == 1 and state.bones.size() == 164 and state.face_meshes == 1 and state.hero_time_shaders.is_empty() and state.controllers.motion.finite and state.controllers.secondary.finite

func camera_state() -> Dictionary:
	var rig: Skeleton3D = player.rama_motion.rig
	var bounds: AABB = lod._bounds
	var minimum := Vector2(INF,INF)
	var maximum := Vector2(-INF,-INF)
	for index in range(8):
		var p := bounds.position+Vector3(bounds.size.x if index&1 else 0.0,bounds.size.y if index&2 else 0.0,bounds.size.z if index&4 else 0.0)
		var projected := camera.unproject_position(rig.global_transform*p)
		minimum = minimum.min(projected); maximum = maximum.max(projected)
	var query := PhysicsRayQueryParameters3D.create(camera.global_position,rig.global_transform*bounds.get_center(),1|4,[player.get_rid()])
	var hit := player.get_world_3d().direct_space_state.intersect_ray(query)
	var occlusion := {}
	if not hit.is_empty(): occlusion = {"collider":String(hit.collider.name),"position":normal(hit.position),"scope":"Static/native collision proxy; not a GPU visibility query"}
	return {"transform":normal(camera.global_transform),"fov":camera.fov,"projection":camera.projection,"keep_aspect":camera.keep_aspect,"near":camera.near,"far":camera.far,"viewport":[SIZE.x,SIZE.y],"rest_aabb_pixels":[normal(minimum),normal(maximum)],"rest_aabb_height_pixels":maximum.y-minimum.y,"camera_center_ray_hit":occlusion}

func shot(id: String, expected_pin: String, settle_frames: int = 2) -> Dictionary:
	await draw(settle_frames)
	var state := frozen_state()
	if not valid_state(state) or state_pin(state) != expected_pin: finish("Frozen bone/morph/secondary/material/controller state changed at " + id); return {}
	var data := root.get_texture().get_image()
	var filename := id+".png"
	if data.is_empty() or data.get_size() != SIZE or data.save_png(output.path_join(filename)) != OK: finish("Actual framebuffer write failed"); return {}
	if Time.get_ticks_msec()-started > 1000000: finish("Finite capture wall budget exceeded"); return {}
	return {"id":id,"file":filename,"sha256":FileAccess.get_sha256(output.path_join(filename)),"width":SIZE.x,"height":SIZE.y,"state_sha256":expected_pin,"camera":camera_state(),"lod":lod.report(),"motion_observation":normal(player.rama_motion.diagnostics()),"render_frame":Engine.get_frames_drawn(),"physics_tick":Engine.get_physics_frames(),"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"rendered_primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),"tree_paused":paused}

func finish(failure: String) -> void:
	if completed: return
	completed = true
	var after := source_hashes() if not sources.is_empty() else {}
	var unchanged := sources == after
	for path in texture_pins:
		if FileAccess.get_sha256(path) != texture_pins[path]: unchanged = false
	for path in imports:
		var entry: Dictionary = imports[path]
		if FileAccess.get_sha256(entry.imported) != entry.sha256 or FileAccess.get_sha256(entry.stamp) != entry.stamp_sha256: unchanged = false
	var report := {"schema":1,"kind":"actual-rama-lod-comparison","complete":failure.is_empty() and unchanged and pairs.size()==6 and frames.size()==(0 if pairs_only else TAKE_FRAMES),"failure":failure,"source_unchanged":unchanged,"source_sha256":sources,"source_after_sha256":after,"imports":imports,"material_texture_pins":texture_pins,"width":SIZE.x,"height":SIZE.y,"fps":FPS,"pairs_only":pairs_only,"poses":poses,"pairs":pairs,"frames":frames,"time_controls":time_controls,"uncontrolled_background_TIME":time_uncontrolled,"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"Actual Confluence/player one-rig LOD appearance. Pair references force near visibility; candidates use actual screen-space selection. Frozen idle/actual accepted windup preserve rig,morph,secondary,materials,controllers,camera and exposure. Camera take moves around a frozen draw pose;15Hz video is not achieved FPS or gameplay progression. Known water TIME is frozen through capture-only animation_speed=0; any uncontrolled background TIME and temporal renderer history prevent a pixel-identity claim. No human input, finished-art or physicalGPU acceptance."}
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("lod-capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("RAMA_LOD_CAPTURE ",report.complete," pairs=",pairs.size()," frames=",frames.size()," ",failure)
	quit(0 if report.complete else 1)
