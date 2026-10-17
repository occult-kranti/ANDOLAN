extends SceneTree
## Real Confluence render of staged art, no persisted map/runtime mutation.
## Run on the serialized actual-display queue, with fresh absolute --output=.
var output := ""
var asset := "res://art/quality-arrival-court/lotus-arrival-court.glb"
var scene: Node3D
var kit: Node3D
var camera: Camera3D
var shots: Array[Dictionary] = []
var pins := {}

func _initialize() -> void:
	call_deferred("run")

func shot(name_: String, phase: float, staged: bool, view: String) -> bool:
	kit.visible = staged
	scene.lighting.set_phase(phase)
	await process_frame
	await RenderingServer.frame_post_draw
	await process_frame
	await RenderingServer.frame_post_draw
	var png := output.path_join(name_ + ".png")
	var image := root.get_texture().get_image()
	if image.is_empty() or image.save_png(png) != OK:
		return false
	shots.append({"file": name_ + ".png", "sha256": FileAccess.get_sha256(png),
		"phase": phase, "staged_geometry_visible": staged, "view": view,
		"camera_transform": str(camera.global_transform), "fov": camera.fov,
		"exposure": scene.world_environment.environment.tonemap_exposure,
		"viewport": [root.size.x, root.size.y], "frame": Engine.get_frames_drawn()})
	return true

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--asset="): asset = arg.trim_prefix("--asset=")
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output) or not FileAccess.file_exists(asset) or DisplayServer.get_name() == "headless":
		push_error("Require existing staged GLB, new absolute output, actual display renderer")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	for path in [asset, get_script().resource_path, "res://scripts/confluence_world.gd", "res://scripts/world_lighting.gd", "res://assets/world/confluence-map.json", "res://assets/heroes/rama-hero.glb"]:
		pins[path] = FileAccess.get_sha256(path)
	root.size = Vector2i(960, 600)
	root.content_scale_size = root.size
	root.msaa_3d = Viewport.MSAA_2X
	root.show()
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	for i in range(5): await physics_frame
	if not scene.world_ready:
		quit(1)
		return
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	# Stop authority, movement and animation at exactly one current world state;
	# geometry visibility alone changes between each adjacent A/B pair.
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.world.process_mode = Node.PROCESS_MODE_DISABLED
	var player_camera: Camera3D = scene.player.camera
	var spawn_transform := player_camera.global_transform
	var fov := player_camera.fov
	camera = Camera3D.new()
	camera.fov = fov
	camera.far = 380
	root.add_child(camera)
	camera.current = true
	var document := GLTFDocument.new()
	var state := GLTFState.new()
	if document.append_from_file(asset, state) != OK:
		quit(1)
		return
	kit = document.generate_scene(state)
	scene.world.add_child(kit)
	kit.position = Vector3(0, 0, -90)
	kit.name = "StagedArrivalCourt_ART_ONLY"
	var views := ["normal-gameplay", "oblique", "lamp-detail"]
	for phase in [0.0, 1.0]:
		for view in views:
			if view == "normal-gameplay":
				camera.global_transform = spawn_transform
				camera.fov = fov
				scene.ui.visible = true
			elif view == "oblique":
				camera.position = Vector3(19, 5, -109)
				camera.look_at(Vector3(0, 5.1, -90))
				camera.fov = 65
				scene.ui.visible = false
			else:
				camera.position = Vector3(9.1, 2.15, -96.7)
				camera.look_at(Vector3(7.45, 1.1, -93.6))
				camera.fov = 52
				scene.ui.visible = false
			for staged in [false, true]:
				var name_ := "%s-%s-%s" % ["day" if phase == 0 else "night", view, "after" if staged else "before"]
				if not await shot(name_, phase, staged, view):
					quit(1)
					return
	var changed := []
	for path in pins:
		if FileAccess.get_sha256(path) != pins[path]: changed.append(path)
	var report := {"schema_version": 1, "status": "captured; independent actual image review required",
		"engine": Engine.get_version_info(), "renderer": RenderingServer.get_current_rendering_method(),
		"display": DisplayServer.get_name(), "source_pins": pins, "source_changed": changed,
		"asset_origin_godot": [0, 0, -90], "shots": shots,
		"limits": ["Art-only staged runtime import; map/collision not changed", "Software rendering is not physical-GPU performance", "No route or gameplay acceptance implied"]}
	var file := FileAccess.open(output.path_join("capture.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	file.close()
	quit(0 if changed.is_empty() and shots.size() == 12 else 1)
