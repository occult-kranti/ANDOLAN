extends SceneTree
## Render each absolute-time sample with the real renderer. This is not an FPS benchmark.

var output_path := ""
var preview := false
var width := 960
var height := 540
var sample_hz := 24
var started_ms := Time.get_ticks_msec()
var failure := ""
var hashes: Dictionary = {}
var imports: Dictionary = {}
var frames: Array[Dictionary] = []
var scene: Node3D

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			output_path = argument.trim_prefix("--output=")
		elif argument == "--preview":
			preview = true
		elif argument.begins_with("--width="):
			width = argument.trim_prefix("--width=").to_int()
		elif argument.begins_with("--height="):
			height = argument.trim_prefix("--height=").to_int()
		else:
			failure = "Unknown argument: " + argument
	if not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path) or width < 480 or width > 1920 or height < 270 or height > 1080 or not failure.is_empty():
		push_error("Require a new absolute output path and bounded dimensions. " + failure)
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_path)
	if DisplayServer.get_name() == "headless":
		failure = "Actual rendering is required; headless is not accepted"
		_finish(false)
		return
	for directory in ["res://scripts", "res://scenes", "res://assets"]:
		_hash_directory(directory)
	for path in ["res://project.godot", "res://tools/capture-combat-film.gd"]:
		hashes[path] = FileAccess.get_sha256(path)
	for path in ["res://assets/heroes/rama-production.glb", "res://assets/cinematics/ravana-sentinel.glb", "res://assets/environment/lanka_courtyard.glb"]:
		if not _validate_import(path):
			_finish(false)
			return
	root.size = Vector2i(width, height)
	root.content_scale_size = Vector2i(1280, 720)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA — Confluence Duel Capture"
	root.show()
	scene = load("res://scenes/combat_film.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	if not scene.has_method("sample_time") or not scene.has_method("get_diagnostics"):
		failure = "Film does not implement the capture contract"
		_finish(false)
		return
	scene.sample_time(0.0, true)
	await _draw_frames(3)
	var times: Array[float] = []
	if preview:
		for second in [0.0, 2.75, 4.3, 4.85, 6.7, 7.65, 8.55, 13.9, 15.45, 16.1, 18.5, 23.95]:
			times.append(second)
	else:
		for index in range(24 * sample_hz):
			times.append(float(index) / sample_hz)
	for index in times.size():
		if Time.get_ticks_msec() - started_ms > 3600000:
			failure = "Capture exceeded one-hour budget; incomplete evidence preserved"
			_finish(false)
			return
		scene.sample_time(times[index], true)
		await _draw_frames(2 if preview else 1)
		var diagnostics: Dictionary = scene.get_diagnostics()
		if not diagnostics.get("ready", false) or not diagnostics.get("finite", false) or diagnostics.get("errors", []).size() > 0:
			failure = "Film reports invalid state: " + JSON.stringify(diagnostics)
			_finish(false)
			return
		if diagnostics.get("effects", {}).has("state"):
			# Keep full evaluated VFX state as a digest, not 57 transforms repeated in JSON.
			var context := HashingContext.new()
			context.start(HashingContext.HASH_SHA256)
			context.update(JSON.stringify(diagnostics.effects.state).to_utf8_buffer())
			diagnostics.effects["state_sha256"] = context.finish().hex_encode()
			diagnostics.effects.erase("state")
		var pixels := root.get_texture().get_image()
		var name := "frame-%05d.png" % index
		var destination := output_path.path_join(name)
		if pixels.is_empty() or pixels.get_width() != width or pixels.get_height() != height or pixels.save_png(destination) != OK:
			failure = "Invalid or unsaved rendered frame"
			_finish(false)
			return
		frames.append({"file":name, "sha256":FileAccess.get_sha256(destination),
			"t_seconds":times[index], "width":width, "height":height,
			"rendered_frame_counter":Engine.get_frames_drawn(), "diagnostics":diagnostics})
		if index % 24 == 0 or preview:
			print("YUGA_FILM_CAPTURE ", index + 1, "/", times.size(), " t=", times[index])
	for path in hashes:
		if hashes[path] != FileAccess.get_sha256(path):
			failure = "Source changed during capture: " + path
			_finish(false)
			return
	_finish(true)

func _hash_directory(path: String) -> void:
	for filename in DirAccess.get_files_at(path):
		var full := path.path_join(filename)
		hashes[full] = FileAccess.get_sha256(full)
	for directory in DirAccess.get_directories_at(path):
		_hash_directory(path.path_join(directory))

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

func _finish(success: bool) -> void:
	var report := {"schema":1, "kind":"actual-native-combat-film", "complete":success,
		"failure":failure, "preview":preview, "sample_hz":sample_hz, "duration_seconds":24,
		"frame_count":frames.size(), "frames":frames, "source_sha256":hashes, "imports":imports,
		"renderer":RenderingServer.get_current_rendering_method(),
		"adapter":RenderingServer.get_video_adapter_name(), "display":DisplayServer.get_name(),
		"godot":Engine.get_version_info(), "elapsed_ms":Time.get_ticks_msec()-started_ms,
		"scope":"Actual sequential animated 3D renders sampled at absolute times, not hardware FPS or commercial visual parity. Visual review required separately."}
	var file := FileAccess.open(output_path.path_join("combat-film-render.json"), FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "  ") + "\n")
	print("YUGA_FILM_CAPTURE ", "PASS" if success else "FAIL", " ", frames.size(), " ", failure)
	quit(0 if success else 1)
