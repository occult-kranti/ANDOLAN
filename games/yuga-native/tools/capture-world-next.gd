extends SceneTree
## Actual rendered map evidence. These staged views do not measure hardware FPS.

const SOURCES := ["res://project.godot", "res://assets/world/confluence-map.json", "res://assets/world/architecture.glb",
	"res://assets/world/nature.glb", "res://assets/heroes/rama-production.glb", "res://assets/environment/lanka_courtyard.glb",
	"res://scripts/confluence_world.gd", "res://scripts/world_lighting.gd", "res://scripts/mythic_environment.gd",
	"res://scripts/courtyard.gd", "res://scripts/production_lighting.gd", "res://shaders/production_water.gdshader",
	"res://scripts/world_ground.gdshader", "res://scripts/world_ground_common.gdshaderinc",
	"res://scripts/world_water.gdshader", "res://scripts/player.gd",
	"res://scenes/confluence_world.tscn", "res://scenes/courtyard.tscn", "res://tools/capture-world-next.gd"]
const Art = preload("res://scripts/mythic_environment.gd")
var scene_reports: Dictionary = {}
var output_path := ""
var hashes: Dictionary = {}
var imports: Dictionary = {}
var shots: Array[Dictionary] = []
var failure := ""
var scene: Node3D
var camera: Camera3D
var started_ms := Time.get_ticks_msec()

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			output_path = argument.trim_prefix("--output=")
	if not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path):
		push_error("A new absolute output directory is required")
		quit(1)
		return
	if DirAccess.make_dir_recursive_absolute(output_path) != OK:
		quit(1)
		return
	if DisplayServer.get_name() == "headless":
		failure = "A real renderer/display is required"
		_finish(false)
		return
	hashes = _source_hashes()
	for path in SOURCES:
		if not FileAccess.file_exists(path):
			failure = "Missing runtime source " + path
			_finish(false)
			return
		hashes[path] = FileAccess.get_sha256(path)
		if path.ends_with(".glb") and not _validate_import(path):
			_finish(false)
			return
	root.size = Vector2i(1280, 720)
	root.content_scale_size = root.size
	root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA — Confluence Render Review"
	root.show()
	for scene_name in ["courtyard", "confluence_world"]:
		scene = load("res://scenes/" + scene_name + ".tscn").instantiate()
		root.add_child(scene)
		current_scene = scene
		await _draw_frames(3)
		paused = false
		scene.player.active = false
		scene.player.set_physics_process(false)
		scene.set_process(false)
		scene.set_physics_process(false)
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		scene.ui.visible = false
		camera = Camera3D.new()
		camera.far = 400
		camera.fov = 65
		scene.add_child(camera)
		camera.make_current()
		var specifications: Array = []
		if scene_name == "courtyard":
			specifications = [
				{"id":"01-courtyard-dusk", "position":Vector3(0,3.1,17), "target":Vector3(0,5,-22), "phase":0.0},
				{"id":"02-courtyard-night", "position":Vector3(0,3.1,17), "target":Vector3(0,5,-22), "phase":1.0},
				{"id":"03-gallery-day", "position":Vector3(9,3.2,15), "target":Vector3(17,4.2,-8), "phase":0.0},
				{"id":"04-gallery-night", "position":Vector3(9,3.2,15), "target":Vector3(17,4.2,-8), "phase":1.0},
				{"id":"05-courtyard-coastal-water", "position":Vector3(-25,2.5,8), "target":Vector3(-29,0.1,-3), "phase":0.0}
			]
		else:
			specifications = [
				{"id":"06-reed-court-day", "position":Vector3(-48,2.8,8), "target":Vector3(-72,3.5,2), "phase":0.0},
				{"id":"07-reed-court-dusk", "position":Vector3(-48,2.8,8), "target":Vector3(-72,3.5,2), "phase":0.5},
				{"id":"08-reed-court-night", "position":Vector3(-48,2.8,8), "target":Vector3(-72,3.5,2), "phase":1.0},
				{"id":"09-city-dusk", "position":Vector3(-85,68,-110), "target":Vector3(0,3,0), "phase":0.5},
				{"id":"10-coastal-river-loom-detail", "position":Vector3(-71,4,-16), "target":Vector3(-88,4.5,-18), "phase":0.5}
			]
		for specification in specifications:
			if scene_name == "courtyard":
				scene.night = specification.phase > 0.5
				scene._apply_settings()
			else: scene.set_review_phase(float(specification.phase))
			camera.global_position = specification.position
			camera.look_at(specification.target)
			await _draw_frames(4)
			if not _capture(specification):
				_finish(false)
				return
		scene_reports[scene_name] = {"art":Art.diagnostics(scene.world)}
		if scene_name == "courtyard": scene_reports[scene_name]["collidable_meshes"] = scene.collidable_meshes
		else: scene_reports[scene_name]["world_build"] = scene.get_build_report()
		current_scene = null
		scene.free()
		scene = null
		await process_frame
	if hashes != _source_hashes():
		failure = "Runtime source inventory changed during review"
		_finish(false)
		return
	_finish(true)

func _validate_import(path: String) -> bool:
	var configuration := ConfigFile.new()
	if configuration.load(path + ".import") != OK:
		failure = "Missing GLB import metadata: " + path
		return false
	var imported: String = configuration.get_value("remap", "path", "")
	var checksum := imported.get_basename() + ".md5"
	if not FileAccess.file_exists(imported) or not FileAccess.file_exists(checksum):
		failure = "Missing imported scene/checksum: " + path
		return false
	var pattern := RegEx.new()
	var stamp := FileAccess.get_file_as_string(checksum)
	for item in [["source_md5", path], ["dest_md5", imported]]:
		pattern.compile(String(item[0]) + '="([a-f0-9]+)"')
		var matched := pattern.search(stamp)
		if not matched or matched.get_string(1) != FileAccess.get_md5(item[1]):
			failure = "Stale GLB import: " + path
			return false
	imports[path] = {"imported":imported, "sha256":FileAccess.get_sha256(imported), "fresh":true}
	return true

func _draw_frames(count: int) -> void:
	for _index in range(count):
		await process_frame
		await RenderingServer.frame_post_draw

func _capture(specification: Dictionary) -> bool:
	var rendered := root.get_texture().get_image()
	if rendered.is_empty() or Engine.get_frames_drawn() < 1:
		failure = "Renderer returned no image"
		return false
	var filename: String = specification.id + ".png"
	if rendered.save_png(output_path.path_join(filename)) != OK:
		failure = "Cannot save rendered image"
		return false
	var position: Vector3 = specification.position
	var target: Vector3 = specification.target
	shots.append({"file":filename, "sha256":FileAccess.get_sha256(output_path.path_join(filename)),
		"width":rendered.get_width(), "height":rendered.get_height(), "phase":specification.phase,
		"camera_position":[position.x,position.y,position.z], "camera_target":[target.x,target.y,target.z],
		"frames_drawn":Engine.get_frames_drawn(),
		"rendered_objects":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
		"rendered_primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),
		"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)})
	print("YUGA_WORLD_CAPTURE ", filename)
	return true

func _finish(success: bool) -> void:
	var report := {"schema":1, "kind":"actual-native-world-presentation-review", "complete":success,
		"failure":failure, "source_sha256":hashes, "imports":imports, "shots":shots, "scene_reports":scene_reports,
		"renderer":RenderingServer.get_current_rendering_method(),
		"adapter":RenderingServer.get_video_adapter_name(), "display":DisplayServer.get_name(),
		"godot":Engine.get_version_info(), "elapsed_ms":Time.get_ticks_msec()-started_ms,
		"scope":"Staged views of the actual native traversal scene. Software rendering is not hardware performance or commercial visual-quality acceptance."}
	if is_instance_valid(scene):
		report["remaining_scene"] = true
		paused = false
	var file := FileAccess.open(output_path.path_join("world-presentation-review.json"), FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "\t") + "\n")
	if not success:
		push_error(failure)
	quit(0 if success else 1)

func _source_hashes() -> Dictionary:
	var paths: Array[String] = ["res://project.godot", "res://tools/capture-world-next.gd", "res://art/world/confluence-map.json"]
	for directory in ["res://scripts", "res://scenes", "res://assets", "res://shaders"]:
		_collect_sources(directory, paths)
	paths.sort()
	var result := {}
	for path in paths:
		result[path] = FileAccess.get_sha256(path) if FileAccess.file_exists(path) else "MISSING"
	return result

func _collect_sources(directory: String, paths: Array[String]) -> void:
	for filename in DirAccess.get_files_at(directory): paths.append(directory.path_join(filename))
	for dirname in DirAccess.get_directories_at(directory): _collect_sources(directory.path_join(dirname), paths)
