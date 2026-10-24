extends SceneTree
## Matched actual native textured comparisons + continuous shared-motion footage.
## This is an isolated presentation fixture, not an ordinary-input game journey.
const Adapter = preload("res://tools/hero-donor-groom/mpfb_native/native_candidate.gd")
const Motion = preload("res://scripts/rama_motion.gd")
var output := ""
var base := ""
var hair := ""
var camera: Camera3D
var models: Array[Node3D] = []
var motions: Array[Node] = []
var originals: Array = []
var frame_rows: Array = []
var phase := "all"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--base="): base = arg.trim_prefix("--base=")
		elif arg.begins_with("--hair="): hair = arg.trim_prefix("--hair=")
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--phase="): phase = arg.trim_prefix("--phase=")
	call_deferred("run")

func present() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func capture(label: String) -> Dictionary:
	var path := output.path_join(label + ".png")
	var image := root.get_texture().get_image()
	if image.save_png(path) != OK: push_error("PNG write failed"); quit(1)
	return {"name": label, "path": path, "sha256": FileAccess.get_sha256(path), "width": image.get_width(), "height": image.get_height(), "camera_transform": str(camera.global_transform), "fov": camera.fov}

func camera_view(view: String, close: bool) -> void:
	var target := Vector3(0, 1.65, -.03) if close else Vector3(0, 1.05, 0)
	var direction := Vector3(.25, .12, -1) if view == "rear" else Vector3(1, .12, .08)
	camera.position = target + direction.normalized() * (1.25 if close else 5.6)
	camera.fov = 32.0 if close else 40.0
	camera.look_at(target)

func run() -> void:
	if not base.is_absolute_path() or not hair.is_absolute_path() or not output.is_absolute_path() or not DirAccess.dir_exists_absolute(output): quit(2); return
	if DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus": quit(2); return
	root.size = Vector2i(960, 540)
	root.msaa_3d = Viewport.MSAA_2X
	root.show()
	var stage := Node3D.new()
	root.add_child(stage)
	var world := WorldEnvironment.new()
	world.environment = Environment.new()
	world.environment.background_mode = Environment.BG_COLOR
	world.environment.background_color = Color(.035, .045, .065)
	world.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	world.environment.ambient_light_color = Color(.65, .72, .85)
	world.environment.ambient_light_energy = .55
	world.environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	stage.add_child(world)
	for item in [[Vector3(-35,-35,0), Color(1,.86,.70), 2.2], [Vector3(-15,150,0), Color(.55,.7,1), 1.1]]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees = item[0]
		light.light_color = item[1]
		light.light_energy = item[2]
		stage.add_child(light)
	var floor := MeshInstance3D.new()
	floor.mesh = PlaneMesh.new()
	(floor.mesh as PlaneMesh).size = Vector2(12,12)
	var floor_mat := StandardMaterial3D.new()
	floor_mat.albedo_color = Color(.065,.07,.085)
	floor_mat.roughness = 1
	floor.material_override = floor_mat
	stage.add_child(floor)
	camera = Camera3D.new()
	stage.add_child(camera)
	camera.current = true
	for path in [ProjectSettings.globalize_path("res://assets/heroes/rama-hero.glb"), base]:
		var model := Adapter.load_glb(path)
		if not model: quit(1); return
		stage.add_child(model)
		var motion := Motion.new()
		if not motion.configure(model, Adapter.first(model, "AnimationPlayer")): quit(1); return
		motion.active = false
		models.append(model)
		motions.append(motion)
	var attachment := Adapter.attach(models[1], hair)
	if not attachment.ok: push_error(str(attachment)); quit(1); return
	var state := {"velocity": Vector3.ZERO, "grounded": true, "floor_y": 0.0, "aiming": false, "aim_pitch": 0.0, "aim_yaw": 0.0}
	for unused in 30:
		for motion in motions:
			motion.update_motion(1.0/30.0, state)
			motion.evaluate_pose()
	camera_view("rear", true)
	for unused in 6: await present()
	print("MPFB_CAPTURE_READY")
	for view in ([] if phase == "motion" else ["rear", "profile"]):
		for close in [false, true]:
			if phase == "correction" and view == "profile" and not close: continue
			camera_view(view, close)
			for variant in ([1] if phase == "correction" else [0, 1]):
				models[0].visible = variant == 0
				models[1].visible = variant == 1
				await present()
				originals.append(capture(view + ("-close" if close else "-ordinary") + ("-baseline" if variant == 0 else "-candidate")))
	models[0].visible = false
	models[1].visible = true
	camera.position = Vector3(.7,1.95,-2.5)
	camera.fov = 38
	camera.look_at(Vector3(0,1.26,0))
	var frame_total := 0 if phase in ["stills", "correction"] else 120
	for frame in frame_total:
		if frame == 0: state.velocity = Vector3(0,0,-4)
		if frame == 25:
			state.velocity = Vector3.ZERO
			state.aiming = true
			motions[1].request_action("kodanda", .18,.22)
		if frame == 45: motions[1].release_action("kodanda")
		if frame == 60:
			state.velocity = Vector3(2,0,-3)
			state.aim_yaw = .55
		if frame == 85: state.aim_yaw = -.55
		if frame == 100:
			state.velocity = Vector3.ZERO
			motions[1].request_action("piercing_dawn", .18,.22)
		if frame == 112: motions[1].cancel_action("capture interrupted")
		motions[1].update_motion(1.0/30.0, state)
		motions[1].evaluate_pose()
		await present()
		var record := capture("motion-%04d" % frame)
		record.frame = frame
		record.action = motions[1].action
		record.action_stage = motions[1].action_stage
		record.release_count = motions[1].release_count
		frame_rows.append(record)
	var report := {"schema_version":1,"scope":"Actual native textured isolated presentation, explicitly pinned body derivative + canonical motion; staged states, not human input/gameplay acceptance", "engine": Engine.get_version_info(), "renderer": RenderingServer.get_current_rendering_method(), "adapter": RenderingServer.get_video_adapter_name(), "originals":originals,"frames":frame_rows,"frame_count":frame_total,"playback_fps":30,"playback_seconds":frame_total / 30.0,"source_pins":{"canonical":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb"),"body_derivative":FileAccess.get_sha256(base),"hair":FileAccess.get_sha256(hair),"motion":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"adapter":FileAccess.get_sha256("res://tools/hero-donor-groom/mpfb_native/native_candidate.gd"),"driver":FileAccess.get_sha256(get_script().resource_path)},"canonical_promoted":false}
	FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	for model in models: model.free()
	stage.free()
	quit(0)
