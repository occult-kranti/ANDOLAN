extends SceneTree
## Actual-scene projection and camera ownership; pixels require separate review.
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label, "passed":passed, "details":details})
	print("PASS " if passed else "FAIL ", label)

func _settle() -> void:
	for unused in range(5): await process_frame

func _run() -> void:
	var scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await _settle()
	var gameplay_camera_transform: Transform3D = scene.player.camera.transform
	var gameplay_fov: float = scene.player.camera.fov
	for dimensions in [Vector2i(960,540), Vector2i(960,600), Vector2i(1280,720), Vector2i(1920,1080), Vector2i(2560,1440)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await _settle()
		var camera: Camera3D = scene.title_camera
		var origin: Vector3 = scene.player.global_position
		var sole := camera.unproject_position(origin)
		var crown := camera.unproject_position(origin + Vector3.UP * 2.1)
		var face := camera.unproject_position(origin + Vector3.UP * 1.78)
		var frame := root.get_visible_rect()
		var height_fraction := (sole.y - crown.y) / frame.size.y
		var card: Control = scene.main_panel.get_node("Card")
		var scrim: TextureRect = scene.main_panel.get_node("PortraitScrim")
		_record("Portrait fills title without cropping " + str(dimensions),
			height_fraction >= .65 and height_fraction <= .78 and crown.y > frame.size.y * .08 and sole.y < frame.size.y * .94,
			{"crown":str(crown), "sole":str(sole), "height_fraction":height_fraction})
		_record("Face clears controls and wash " + str(dimensions),
			face.x > card.get_global_rect().end.x + 36 and face.x < frame.end.x - 44 and frame.has_point(face)
			and scrim.texture.gradient.sample(face.x / frame.size.x).a <= .03,
			{"face":str(face), "menu_right":card.get_global_rect().end.x})
		_record("Idle side envelope remains in portrait " + str(dimensions),
			frame.has_point(camera.unproject_position(origin + Vector3(-.65,1.0,0)))
			and frame.has_point(camera.unproject_position(origin + Vector3(.65,1.0,0))))
	_record("Framing leaves gameplay camera untouched", scene.player.camera.transform.is_equal_approx(gameplay_camera_transform) and is_equal_approx(scene.player.camera.fov,gameplay_fov))
	scene.start_training()
	await _settle()
	_record("Training owns active camera", root.get_camera_3d() == scene.player.camera and not scene.title_camera.current)
	scene.return_to_menu()
	await _settle()
	_record("Title reacquires its actual portrait camera", root.get_camera_3d() == scene.title_camera and scene.main_panel.visible and not scene.player.active)
	var passed := true
	for check in checks: passed = passed and check.passed
	var sources := {}
	for path in ["res://scripts/courtyard.gd", "res://scripts/launch_shell.gd", get_script().resource_path]: sources[path] = FileAccess.get_sha256(path)
	var report := {"passed":passed, "checks":checks, "sources":sources,
		"scope":"Actual-scene supported-window projection, framing envelope and camera ownership. No rendered silhouette, action-extrema or visual-quality acceptance."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t") + "\n")
		else: passed = false
	scene.queue_free()
	current_scene = null
	paused = false
	await process_frame
	quit(0 if passed else 1)
