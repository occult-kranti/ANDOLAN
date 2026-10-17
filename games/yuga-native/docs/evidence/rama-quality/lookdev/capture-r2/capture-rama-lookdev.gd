extends SceneTree
## Matched actual-scene light/material comparisons. No edited or synthetic images.
const Production = preload("res://scripts/production_lighting.gd")
const WorldLight = preload("res://scripts/world_lighting.gd")
const Surface = preload("res://scripts/rama_surface_materials.gd")
const BEFORE_PRODUCTION := "res://art/lookdev/production_lighting-before.gd.txt"
const BEFORE_WORLD := "res://art/lookdev/world_lighting-before.gd.txt"
var output := ""
var shots: Array = []
var sources := {}
var scene: Node3D
var before_production: GDScript
var before_world: GDScript
var surface: Node
var imports := {}
var completed := false
var started := Time.get_ticks_msec()

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		else: finish("Unknown argument: " + arg); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):
		finish("Require a fresh absolute output directory"); return
	if DisplayServer.get_name() == "headless" or RenderingServer.get_current_rendering_method() != "forward_plus":
		finish("Actual Forward+ display required"); return
	DirAccess.make_dir_recursive_absolute(output)
	for directory in ["scripts", "shaders", "assets", "scenes"]: pin_directory("res://" + directory)
	for path in [BEFORE_PRODUCTION, BEFORE_WORLD, "res://tools/capture-rama-lookdev.gd"]:
		sources[path] = FileAccess.get_sha256(path)
	for path in sources:
		if path.ends_with(".glb") and not fresh_import(path):
			finish("Missing or stale imported scene: " + path); return
	before_production = old_script(BEFORE_PRODUCTION)
	before_world = old_script(BEFORE_WORLD)
	if before_production == null or before_world == null:
		finish("Baseline lighting script did not compile"); return
	root.size = Vector2i(1280, 720)
	root.content_scale_size = root.size
	root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA — matched production quality comparison"
	root.show()
	scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await draw(8)
	paused = true
	var frozen_pose := pose_pin(scene.player.visual)
	for night in [false, true]:
		for candidate in [false, true]:
			apply_courtyard(candidate, night)
			await capture("title-" + ("night" if night else "day") + ("-after" if candidate else "-before"), candidate, float(night), "lighting", frozen_pose)
			if completed: return
	# The same frozen character, environment, pose and close camera isolate PBR.
	scene.ui.hide()
	var close_camera := Camera3D.new()
	scene.world.add_child(close_camera)
	close_camera.fov = 34
	close_camera.global_position = scene.player.global_position + Vector3(.36, 1.77, -1.15)
	close_camera.look_at(scene.player.global_position + Vector3(0, 1.70, 0))
	close_camera.make_current()
	apply_courtyard(true, false)
	# The player may already own the calibration component. Restore it explicitly
	# before making a second owner; do not compare two stacked calibrations.
	var existing: Node = scene.player.get("rama_surface")
	if is_instance_valid(existing): existing.restore_materials()
	await capture("face-material-before", false, 0, "materials", frozen_pose)
	if completed: return
	surface = Surface.new(); scene.player.visual.add_child(surface)
	if not surface.configure(scene.player.visual): finish("Actual material calibration did not bind"); return
	await capture("face-material-after", true, 0, "materials", frozen_pose)
	if completed: return
	surface.restore_materials()
	scene.queue_free(); paused = false
	await process_frame
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await draw(8)
	if not scene.world_ready: finish("Actual world was not ready"); return
	scene.set_paused(false); scene.set_overview(false)
	scene.player.active = false
	scene.ui.hide()
	scene.player.global_position = Vector3(-40, .05, -10)
	scene.player.velocity = Vector3.ZERO
	paused = true
	var camera := Camera3D.new(); scene.add_child(camera)
	camera.fov = 58
	camera.global_position = scene.player.global_position + Vector3(2.7, 1.6, 4.8)
	camera.look_at(scene.player.global_position + Vector3(0, 1.0, 0)); camera.make_current()
	frozen_pose = pose_pin(scene.player.visual)
	for phase in [0.0, .5, 1.0]:
		for candidate in [false, true]:
			if candidate: WorldLight.apply(scene.world_environment.environment, scene.sun, scene.world, phase, true)
			else: before_world.call("apply", scene.world_environment.environment, scene.sun, scene.world, phase, true)
			await capture("world-" + str(int(phase * 100)) + ("-after" if candidate else "-before"), candidate, phase, "lighting", frozen_pose)
			if completed: return
	finish("")

func old_script(path: String) -> GDScript:
	var result := GDScript.new()
	result.source_code = FileAccess.get_file_as_string(path)
	return result if result.reload() == OK else null

func apply_courtyard(candidate: bool, night: bool) -> void:
	if candidate: Production.apply(scene.world_environment.environment, scene.sun, scene.world, night, true)
	else: before_production.call("apply", scene.world_environment.environment, scene.sun, scene.world, night, true)

func pin_directory(path: String) -> void:
	var directory := DirAccess.open(path)
	if directory == null: return
	for name_ in directory.get_files():
		var source := path.path_join(name_)
		sources[source] = FileAccess.get_sha256(source)
	for child in directory.get_directories(): pin_directory(path.path_join(child))

func fresh_import(path: String) -> bool:
	var config := ConfigFile.new()
	if config.load(path + ".import") != OK: return false
	var imported: String = config.get_value("remap", "path", "")
	var stamp := imported.get_basename() + ".md5"
	if imported.is_empty() or not FileAccess.file_exists(imported) or not FileAccess.file_exists(stamp): return false
	var text := FileAccess.get_file_as_string(stamp)
	var regex := RegEx.new()
	for entry in [["source_md5", path], ["dest_md5", imported]]:
		regex.compile(String(entry[0]) + '="([a-f0-9]+)"')
		var match_ := regex.search(text)
		if match_ == null or match_.get_string(1) != FileAccess.get_md5(entry[1]): return false
	imports[path] = {"fresh":true, "imported":imported, "sha256":FileAccess.get_sha256(imported), "stamp_sha256":FileAccess.get_sha256(stamp)}
	return true

func pose_pin(node: Node) -> String:
	var rows := []
	for rig in node.find_children("*", "Skeleton3D", true, false):
		for index in rig.get_bone_count():
			var pose: Transform3D = rig.get_bone_global_pose(index)
			rows.append([pose.basis.x.x,pose.basis.x.y,pose.basis.x.z,pose.basis.y.x,pose.basis.y.y,pose.basis.y.z,pose.basis.z.x,pose.basis.z.y,pose.basis.z.z,pose.origin.x,pose.origin.y,pose.origin.z])
	for mesh in node.find_children("*", "MeshInstance3D", true, false):
		if not mesh.mesh: continue
		rows.append([String(mesh.get_path()), "mesh_visibility", mesh.visible, mesh.is_visible_in_tree(), mesh.mesh.resource_path])
		if mesh.mesh is ArrayMesh:
			for index in mesh.mesh.get_blend_shape_count(): rows.append([String(mesh.get_path()), "morph", index, mesh.get_blend_shape_value(index)])
		for surface_index in mesh.mesh.get_surface_count():
			var material: Material = mesh.get_active_material(surface_index)
			if material is ShaderMaterial and String(material.resource_name).ends_with("bounded secondary"):
				var offset: Vector3 = material.get_shader_parameter("secondary_offset")
				rows.append([String(mesh.get_path()), "secondary", surface_index, offset.x, offset.y, offset.z])
	return JSON.stringify(rows,"",true,true).sha256_text()

func draw(count: int) -> void:
	for index in count:
		await process_frame
		await RenderingServer.frame_post_draw

func capture(id: String, candidate: bool, phase: float, kind: String, pose: String) -> void:
	await draw(3)
	if pose_pin(scene.player.visual) != pose: finish("Frozen comparison pose changed"); return
	var image := root.get_texture().get_image()
	var name_ := id + ".png"
	if image.is_empty() or image.get_size() != Vector2i(1280,720) or image.save_png(output.path_join(name_)) != OK:
		finish("Image write failed"); return
	var camera := root.get_camera_3d()
	shots.append({"id":id, "file":name_, "sha256":FileAccess.get_sha256(output.path_join(name_)), "candidate":candidate, "phase":phase, "comparison":kind, "pose_sha256":pose, "camera_transform":str(camera.global_transform), "camera_fov":camera.fov, "exposure":scene.world_environment.environment.tonemap_exposure, "rendered_counter":Engine.get_frames_drawn()})
	if Time.get_ticks_msec()-started > 900000: finish("Capture exceeded wall budget")

func finish(failure: String) -> void:
	if completed: return
	completed = true
	var unchanged := true
	for path in sources:
		if FileAccess.get_sha256(path) != sources[path]: unchanged = false
	for path in imports:
		if FileAccess.get_sha256(imports[path].imported) != imports[path].sha256: unchanged = false
	var report := {"complete":failure.is_empty() and unchanged and shots.size()==12, "failure":failure, "source_unchanged":unchanged, "sources":sources, "imports":imports, "shots":shots, "renderer":RenderingServer.get_current_rendering_method(), "adapter":RenderingServer.get_video_adapter_name(), "display":DisplayServer.get_name(), "scope":"Actual frozen-scene matched camera/pose/morph/secondary/exposure comparisons, fresh source and imported scenes. Water/shader global TIME can still differ; this is not real-time performance, human playtest or finished-art acceptance."}
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("lookdev-capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	paused = false
	print("RAMA_LOOKDEV_CAPTURE ", report.complete, " ", failure)
	quit(0 if report.complete else 1)
