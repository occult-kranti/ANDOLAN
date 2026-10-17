extends SceneTree
## Actual rendered map evidence. These staged views do not measure hardware FPS.

const SOURCES := ["res://project.godot", "res://assets/world/confluence-map.json", "res://assets/world/architecture.glb",
	"res://assets/world/nature.glb", "res://assets/heroes/rama-production.glb",
	"res://scripts/confluence_world.gd", "res://scripts/world_lighting.gd",
	"res://scripts/world_ground.gdshader", "res://scripts/world_ground_common.gdshaderinc",
	"res://scripts/world_water.gdshader", "res://scripts/player.gd",
	"res://scenes/confluence_world.tscn", "res://tools/capture-world.gd"]
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
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await _draw_frames(3)
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
	var specifications := [
		{"id":"01-city-overview", "position":Vector3(-107,109,-132), "target":Vector3(0,2,0), "phase":0.0},
		{"id":"02-temple-avenue", "position":Vector3(-5,3.0,-48), "target":Vector3(-22,7,-25), "phase":0.0},
		{"id":"03-coastal-ghat", "position":Vector3(-45,3.4,-43), "target":Vector3(-65,5,-15), "phase":0.0},
		{"id":"04-metro-gardens", "position":Vector3(43,5,-47), "target":Vector3(19,9,-23), "phase":0.0},
		{"id":"05-reed-court", "position":Vector3(-47,2.4,7), "target":Vector3(-61,2,-1), "phase":0.0},
		{"id":"06-lantern-night", "position":Vector3(-8,3.2,-43), "target":Vector3(-21,5,-24), "phase":1.0},
		{"id":"07-night-overview", "position":Vector3(-87,82,-114), "target":Vector3(0,2,0), "phase":1.0}
	]
	for specification in specifications:
		scene.set_review_phase(float(specification.phase))
		camera.global_position = specification.position
		camera.look_at(specification.target)
		await _draw_frames(4)
		if not _capture(specification):
			_finish(false)
			return
	# The actual hero camera and HUD establish the playable scale separately.
	scene.set_review_phase(0.0)
	scene.ui.visible = true
	scene.player.camera.make_current()
	await _draw_frames(4)
	if not _capture({"id":"08-player-scale", "position":scene.player.camera.global_position,
		"target":scene.player.global_position, "phase":0.0}):
		_finish(false)
		return
	scene.set_paused(true)
	await _draw_frames(3)
	if not _capture({"id":"09-pause-controls", "position":scene.player.camera.global_position,
		"target":scene.player.global_position, "phase":0.0}):
		_finish(false)
		return
	for path in hashes:
		if hashes[path] != FileAccess.get_sha256(path):
			failure = "Source changed during review: " + path
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
	var report := {"schema":1, "kind":"actual-native-world-render-review", "complete":success,
		"failure":failure, "source_sha256":hashes, "imports":imports, "shots":shots,
		"renderer":RenderingServer.get_current_rendering_method(),
		"adapter":RenderingServer.get_video_adapter_name(), "display":DisplayServer.get_name(),
		"godot":Engine.get_version_info(), "elapsed_ms":Time.get_ticks_msec()-started_ms,
		"scope":"Staged views of the actual native traversal scene. Software rendering is not hardware performance or commercial visual-quality acceptance."}
	if is_instance_valid(scene):
		report["world_build"] = scene.get_build_report()
		paused = false
	var file := FileAccess.open(output_path.path_join("world-render-review.json"), FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "\t") + "\n")
	if not success:
		push_error(failure)
	quit(0 if success else 1)
