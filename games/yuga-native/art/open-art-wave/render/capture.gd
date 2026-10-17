extends SceneTree
## Actual native scenes; optional material fixture only. Original framebuffers.
const Fixture := preload("res://art/open-art-wave/integration/cloth_candidate.gd")
const Production := preload("res://scripts/production_lighting.gd")
const WorldLight := preload("res://scripts/world_lighting.gd")
const CANDIDATE := "res://art/open-art-wave/materials/indigo-woven-cloth.tres"
const SIZE := Vector2i(1280,960)
const HERO_IMPORTS := ["res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb"]
const OWNED_UNIFORMS := ["base_color","roughness_value","metallic_value","normal_strength","specular_value","rough_channel","metal_channel","base_texture","rough_texture","metal_texture","normal_texture","use_base_texture","use_rough_texture","use_metal_texture","use_normal_texture"]
var output := ""
var preserve_albedo := false
var scene: Node3D
var player: CharacterBody3D
var lod: Node
var camera: Camera3D
var fixture: Node
var sources := {}
var imports := {}
var pairs: Array = []
var states: Array = []
var time_controls: Array = []
var uncontrolled_time: Array = []
var completed := false
var started := Time.get_ticks_msec()

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--preserve-albedo": preserve_albedo = true
		else: finish("Unknown argument: " + arg); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Require fresh absolute output"); return
	DirAccess.make_dir_recursive_absolute(output)
	if DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus": finish("Actual X11 Forward+ renderer required"); return
	root.size = SIZE; root.content_scale_size = SIZE; root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA — matched CC0 cloth candidate"; root.show()
	sources = source_hashes()
	for path in sources:
		if path.ends_with(".glb") and not fresh_import(path,false): finish("Stale GLB import " + path); return
	for path in ["res://art/open-art-wave/textures/indigo-woven-albedo.png","res://art/open-art-wave/textures/indigo-woven-roughness.png","res://art/open-art-wave/textures/indigo-woven-normal.png"]:
		if not fresh_import(path,true): finish("Missing/stale/nonmip texture " + path); return
	var candidate := load(CANDIDATE) as StandardMaterial3D
	if candidate == null: finish("Candidate StandardMaterial3D missing"); return
	for kind in ["courtyard","confluence"]:
		paused = false
		scene = load("res://scenes/" + ("courtyard" if kind == "courtyard" else "confluence_world") + ".tscn").instantiate()
		root.add_child(scene); current_scene = scene
		await draw(8)
		player = scene.player; lod = player.rama_lod
		if not player.model_ready or not lod.configured or not player.rama_secondary.configured or not player.rama_face.configured: finish("Actual hero controllers not ready"); return
		if kind == "confluence":
			if not scene.world_ready: finish("Actual world not ready"); return
			scene.set_paused(false); scene.set_overview(false); scene.set_review_phase(0.0)
			scene.teleport_to(Vector3(-40,.05,-10),180.0)
		player.active = false
		scene.ui.hide()
		camera = Camera3D.new(); scene.add_child(camera)
		camera.fov = 43.0; camera.keep_aspect = Camera3D.KEEP_HEIGHT; camera.make_current()
		await draw(6)
		paused = true
		var target := 780.0 if kind == "courtyard" else 350.0
		place_camera(target)
		lod._selector.reset()
		if not lod.update(camera,1.0/15.0) or lod.level != (0 if kind == "courtyard" else 1): finish("Unexpected actual selected LOD"); return
		freeze_time(kind)
		fixture = Fixture.new(); scene.add_child(fixture)
		for night in [false,true]:
			if kind == "courtyard": Production.apply(scene.world_environment.environment,scene.sun,scene.world,night,true)
			else: WorldLight.apply(scene.world_environment.environment,scene.sun,scene.world,1.0 if night else 0.0,true)
			await draw(3)
			var frozen := frozen_state(true)
			if not valid_state(frozen): finish("Expected one finite164-bone rig and unique face"); return
			var pin := state_pin(frozen)
			var full_before := frozen_state(false)
			var id: String = kind + ("-night" if night else "-day")
			var before: Dictionary = await shot(id+"-baseline",pin)
			if completed: return
			if not fixture.bind(player.visual,candidate,preserve_albedo): finish("Fixture bind refused: " + str(fixture.report())); return
			var binding: Dictionary = fixture.report()
			var candidate_state := frozen_state(false)
			var after: Dictionary = await shot(id+"-candidate",pin)
			if completed: return
			var unbind: Dictionary = fixture.unbind()
			var full_restored := frozen_state(false)
			if not unbind.conflicts.is_empty() or not unbind.invalidated_materials.is_empty() or full_before != full_restored: finish("Unbind did not restore exact full material state"); return
			if before.camera != after.camera or before.lighting != after.lighting or before.state_sha256 != after.state_sha256: finish("Matched camera/exposure/pose changed"); return
			states.append({"id":id,"frozen_excluding_owned_uniforms":frozen,"baseline_full":full_before,"candidate_full":candidate_state,"restored_full":full_restored,"full_restore_exact":true})
			pairs.append({"id":id,"scene":kind,"night":night,"target_hero_pixels":target,"selected_level":lod.level,"baseline":before,"candidate":after,"binding":binding,"unbind":unbind,"same_camera":true,"same_frozen_state_except_owned_uniforms":true,"same_lighting":true,"full_restore_exact":true})
		await retire_scene()
	finish("")

func draw(count: int) -> void:
	for index in count:
		await process_frame
		await RenderingServer.frame_post_draw

func place_camera(target: float) -> void:
	var rig: Skeleton3D = player.rama_motion.rig
	var center: Vector3 = rig.global_transform * lod._bounds.get_center()
	var height: float = (rig.global_basis*Vector3.UP).length()*lod._bounds.size.y
	var distance: float = float(SIZE.y)*height/(2.0*tan(deg_to_rad(camera.fov)*.5)*target)
	# Fixed three-quarter front view exposes fitted front cloth and mantle side.
	camera.global_position = center + Vector3(-.38,0,-.925).normalized()*distance
	camera.look_at(center); camera.reset_physics_interpolation()

func source_hashes() -> Dictionary:
	var paths: Array[String] = ["res://project.godot","res://art/world/confluence-map.json","res://art/open-art-wave/render/capture.gd","res://art/open-art-wave/render/run.py","res://art/open-art-wave/integration/cloth_candidate.gd","res://art/open-art-wave/materials/indigo-woven-cloth.tres","res://art/open-art-wave/source-manifest.json","res://art/open-art-wave/build-manifest.json"]
	for directory in ["res://scripts","res://shaders","res://assets","res://scenes","res://art/open-art-wave/textures"]: collect_files(directory,paths)
	paths.sort()
	var result := {}
	for path in paths: result[path] = FileAccess.get_sha256(path)
	return result

func collect_files(path: String,result: Array[String]) -> void:
	for file in DirAccess.get_files_at(path): result.append(path.path_join(file))
	for directory in DirAccess.get_directories_at(path): collect_files(path.path_join(directory),result)

func fresh_import(path: String,texture: bool) -> bool:
	var config := ConfigFile.new()
	if config.load(path+".import") != OK: return false
	var imported: String = config.get_value("remap","path","")
	var stamp := imported.get_basename()+".md5"
	if imported.is_empty() or not FileAccess.file_exists(imported) or not FileAccess.file_exists(stamp): return false
	var pattern := RegEx.new()
	for entry in [["source_md5",path],["dest_md5",imported]]:
		pattern.compile(String(entry[0])+'="([a-f0-9]+)"')
		var match_ := pattern.search(FileAccess.get_file_as_string(stamp))
		if match_ == null or match_.get_string(1) != FileAccess.get_md5(entry[1]): return false
	var row := {"fresh":true,"source_sha256":FileAccess.get_sha256(path),"metadata":path+".import","metadata_sha256":FileAccess.get_sha256(path+".import"),"imported":imported,"sha256":FileAccess.get_sha256(imported),"stamp":stamp,"stamp_sha256":FileAccess.get_sha256(stamp),"generate_lods":config.get_value("params","meshes/generate_lods",true)}
	if HERO_IMPORTS.has(path) and row.generate_lods: return false
	if texture:
		var loaded := load(path) as Texture2D
		if loaded == null: return false
		var image := loaded.get_image()
		row.mipmaps_generate = config.get_value("params","mipmaps/generate",false)
		row.actual_has_mipmaps = image.has_mipmaps()
		row.dimensions = [loaded.get_width(),loaded.get_height()]
		row.compress_mode = config.get_value("params","compress/mode",-1)
		row.normal_map = config.get_value("params","compress/normal_map",-1)
		row.image_format = image.get_format()
		if not row.mipmaps_generate or not row.actual_has_mipmaps or row.dimensions != [1024,1024]: return false
	imports[path] = row
	return true

func normal(value: Variant) -> Variant:
	if value is Vector2: return [value.x,value.y]
	if value is Vector3: return [value.x,value.y,value.z]
	if value is Vector4 or value is Quaternion: return [value.x,value.y,value.z,value.w]
	if value is Color: return [value.r,value.g,value.b,value.a]
	if value is Transform3D: return [normal(value.basis.x),normal(value.basis.y),normal(value.basis.z),normal(value.origin)]
	if value is Resource: return {"class":value.get_class(),"name":value.resource_name,"path":value.resource_path,"id":value.get_instance_id()}
	if value is Dictionary:
		var result := {}
		for key in value: result[key] = normal(value[key])
		return result
	if value is Array:
		var result := []
		for item in value: result.append(normal(item))
		return result
	return value

func state_pin(state: Dictionary) -> String:
	return JSON.stringify(state,"",true,true).sha256_text()

func owned_uniforms() -> Array:
	var result: Array = OWNED_UNIFORMS.duplicate()
	if preserve_albedo:
		for key in ["base_color","base_texture","use_base_texture"]: result.erase(key)
	return result

func profile_state() -> Dictionary:
	return {"id":"preserve-original-albedo_cc0-roughness-normal-v1" if preserve_albedo else "cc0-albedo-roughness-normal-v1","preserve_albedo":preserve_albedo,"owned_uniforms":owned_uniforms(),"preserved_albedo_fields":["base_color","base_texture","use_base_texture"] if preserve_albedo else [],"scope":"Optional review-only material profile; no runtime promotion"}

func frozen_state(exclude_owned: bool) -> Dictionary:
	var rig: Skeleton3D = player.rama_motion.rig
	var bones := []
	for index in rig.get_bone_count(): bones.append({"name":String(rig.get_bone_name(index)),"parent":rig.get_bone_parent(index),"rest":normal(rig.get_bone_rest(index)),"pose":normal(rig.get_bone_global_pose(index))})
	var meshes := []
	var faces := 0
	for node in player.visual.find_children("*","MeshInstance3D",true,false):
		var mesh: MeshInstance3D = node
		if not mesh.mesh: continue
		if mesh.name == "RamaFace": faces += 1
		var row := {"path":String(mesh.get_path()),"transform":normal(mesh.global_transform),"visible":mesh.visible,"mesh_id":mesh.mesh.get_instance_id(),"skin_id":mesh.skin.get_instance_id() if mesh.skin else 0,"skeleton":String(mesh.skeleton),"morphs":{},"materials":[]}
		if mesh.mesh is ArrayMesh:
			for index in mesh.mesh.get_blend_shape_count(): row.morphs[String(mesh.mesh.get_blend_shape_name(index))] = mesh.get_blend_shape_value(index)
		for index in mesh.mesh.get_surface_count():
			var material := mesh.get_active_material(index)
			var material_state := {"surface":index,"material":normal(material)}
			if material is ShaderMaterial:
				material_state.shader_sha256 = material.shader.code.sha256_text()
				material_state.uniforms = {}
				for uniform in material.shader.get_shader_uniform_list():
					var key: String = uniform.name
					if exclude_owned and material.resource_name == Fixture.TARGET_NAME and key in owned_uniforms(): continue
					material_state.uniforms[key] = normal(material.get_shader_parameter(key))
			elif material is StandardMaterial3D:
				material_state.pbr = normal({"albedo":material.albedo_color,"roughness":material.roughness,"metallic":material.metallic,"specular":material.metallic_specular,"normal_scale":material.normal_scale,"base_texture":material.albedo_texture,"normal_texture":material.normal_texture,"roughness_texture":material.roughness_texture})
			row.materials.append(material_state)
		meshes.append(row)
	var motion: Dictionary = player.rama_motion.diagnostics()
	for key in ["modified_samples","max_contact_error_m","max_string_error_m"]: motion.erase(key)
	return normal({"rig_transform":rig.global_transform,"bones":bones,"live_rigs":player.visual.find_children("*","Skeleton3D",true,false).size(),"face_meshes":faces,"meshes":meshes,"controllers":{"motion":motion,"secondary":player.rama_secondary.report(),"face":player.rama_face.report(),"kit":scene.rama_runtime.kit.report(),"vitals":scene.rama_runtime.vitals.report()},"paused":paused})

func valid_state(state: Dictionary) -> bool:
	return state.live_rigs == 1 and state.bones.size() == 164 and state.face_meshes == 1 and state.controllers.motion.finite and state.controllers.secondary.finite and state.paused

func lighting_state() -> Dictionary:
	return normal({"environment_id":scene.world_environment.environment.get_instance_id(),"exposure":scene.world_environment.environment.tonemap_exposure,"sun_transform":scene.sun.global_transform,"sun_energy":scene.sun.light_energy,"sun_color":scene.sun.light_color})

func camera_state() -> Dictionary:
	var rig: Skeleton3D = player.rama_motion.rig
	var bounds: AABB = lod._bounds
	var minimum := Vector2(INF,INF)
	var maximum := Vector2(-INF,-INF)
	for index in range(8):
		var point := bounds.position+Vector3(bounds.size.x if index&1 else 0.0,bounds.size.y if index&2 else 0.0,bounds.size.z if index&4 else 0.0)
		var projected := camera.unproject_position(rig.global_transform*point)
		minimum = minimum.min(projected); maximum = maximum.max(projected)
	return {"transform":normal(camera.global_transform),"fov":camera.fov,"viewport":[SIZE.x,SIZE.y],"rest_aabb_pixels":[normal(minimum),normal(maximum)],"rest_aabb_height_pixels":maximum.y-minimum.y}

func shot(id: String,pin: String) -> Dictionary:
	await draw(4)
	var state := frozen_state(true)
	if not valid_state(state) or state_pin(state) != pin: finish("Frozen functional state changed at " + id); return {}
	var image := root.get_texture().get_image()
	var filename := id+".png"
	if image.is_empty() or image.get_size() != SIZE or image.save_png(output.path_join(filename)) != OK: finish("Actual framebuffer write failed"); return {}
	if Time.get_ticks_msec()-started > 1000000: finish("Finite capture exceeded wall budget"); return {}
	return {"file":filename,"sha256":FileAccess.get_sha256(output.path_join(filename)),"state_sha256":pin,"camera":camera_state(),"lighting":lighting_state(),"lod":lod.report(),"render_frame":Engine.get_frames_drawn(),"physics_clock":Engine.get_physics_frames(),"tree_paused":paused}

func freeze_time(kind: String) -> void:
	var seen := {}
	for node in scene.find_children("*","MeshInstance3D",true,false):
		if not node.mesh: continue
		for index in node.mesh.get_surface_count():
			var material = node.get_active_material(index)
			if not material is ShaderMaterial or material.shader == null or seen.has(material.get_instance_id()): continue
			seen[material.get_instance_id()] = true
			var comments := RegEx.new(); comments.compile("(?m)//[^\\n]*")
			var code: String = comments.sub(material.shader.code,"",true)
			comments.compile("(?s)/\\*.*?\\*/"); code = comments.sub(code,"",true)
			var token := RegEx.new(); token.compile("\\bTIME\\b")
			if token.search(code) == null: continue
			var row := {"scene":kind,"mesh":String(node.get_path()),"surface":index,"shader":material.shader.resource_path,"shader_sha256":material.shader.code.sha256_text()}
			if material.shader.resource_path in ["res://scripts/world_water.gdshader","res://shaders/production_water.gdshader"]:
				row.before = normal(material.get_shader_parameter("animation_speed")); row.capture_animation_speed = 0.0
				material.set_shader_parameter("animation_speed",0.0); time_controls.append(row)
			else: uncontrolled_time.append(row)

func retire_scene() -> void:
	if is_instance_valid(fixture): fixture.unbind()
	paused = false
	if is_instance_valid(scene):
		for node in scene.find_children("*","AudioStreamPlayer",true,false): node.stop(); node.stream = null
		scene.queue_free()
	# Pending HUD layout coroutines and Dummy playback references must retire.
	for index in range(3): await process_frame
	await create_timer(.1,true,false,true).timeout
	scene = null; player = null; camera = null; lod = null; fixture = null

func finish(failure: String) -> void:
	if completed: return
	completed = true
	var after := source_hashes() if not sources.is_empty() else {}
	var unchanged := sources == after
	for path in imports:
		var entry: Dictionary = imports[path]
		if FileAccess.get_sha256(entry.imported) != entry.sha256 or FileAccess.get_sha256(entry.stamp) != entry.stamp_sha256: unchanged = false
	var report := {"schema":1,"kind":"actual-open-art-cloth-comparison","complete":failure.is_empty() and unchanged and pairs.size()==4,"failure":failure,"profile":profile_state(),"source_unchanged":unchanged,"source_sha256":sources,"source_after_sha256":after,"imports":imports,"states":states,"pairs":pairs,"width":SIZE.x,"height":SIZE.y,"time_controls":time_controls,"uncontrolled_background_TIME":uncontrolled_time,"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"Actual original framebuffers from frozen native courtyard780pxnear and Confluence350pxmid day/night. Only optional cloth uniforms differ; pose/material-owner/secondary/lighting/camera and exact unbind checked. Integer-target sizing is a camera placement target; report projected actual bounds. Temporal renderer history can differ. No continuous gameplay deformation, finished-art, KHRsheen or hardwareFPS acceptance."}
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("material-capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("OPEN_ART_MATERIAL_CAPTURE ",report.complete," pairs=",pairs.size()," ",failure)
	await retire_scene()
	quit(0 if report.complete else 1)
