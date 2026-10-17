extends SceneTree
## Staged, actual-render model review. This is not gameplay or animation-continuity evidence.
## Run with a real display/renderer after importing the asset; see HERO_RENDER_REVIEW.md.

const DEFAULT_ASSET := "res://assets/heroes/rama-production.glb"
const REQUIRED_CLIPS := ["cast", "cast1", "cast2", "cast3", "defeat", "fire", "idle", "jump", "run"]
const POSE_FRACTIONS := {
	"cast": 0.50, "cast1": 0.25, "cast2": 0.50, "cast3": 0.6625,
	"defeat": 0.88, "fire": 0.25, "idle": 0.25, "jump": 0.50, "run": 0.25
}
const STUDIO_CAMERA_TARGET := Vector3(0, 1.03, 0)
const STUDIO_CAMERA_DISTANCE := 5.1

var asset_path := DEFAULT_ASSET
var output_path := "/tmp/yuga-production-hero-review"
var width := 960
var height := 960
var timeout_seconds := 240.0
var started_ms := Time.get_ticks_msec()
var studio: Node3D
var hero: Node3D
var animator: AnimationPlayer
var camera: Camera3D
var footer: Label
var clips: Dictionary = {}
var clip_lengths: Dictionary = {}
var source_sha_before := ""
var shots: Array[Dictionary] = []
var skeletons: Array[Skeleton3D] = []
var completed := false
var pose_overrides: Dictionary = {}
var failure := ""
var imported_resource: Dictionary = {}

func _initialize() -> void:
	# The async sequence starts after SceneTree and the root Window exist.
	call_deferred("_run")

func _run() -> void:
	if not _parse_arguments():
		_finish(false)
		return
	var error := DirAccess.make_dir_recursive_absolute(output_path)
	if error != OK:
		failure = "Cannot create output directory: " + error_string(error)
		_finish(false)
		return
	if DisplayServer.get_name() == "headless":
		failure = "A headless dummy renderer cannot produce actual-render review evidence. Use a real display and renderer."
		_finish(false)
		return
	if not ResourceLoader.exists(asset_path):
		failure = "Hero asset is missing or has not been imported: " + asset_path
		_finish(false)
		return
	if not _validate_import():
		_finish(false)
		return
	var packed = load(asset_path)
	if not packed is PackedScene:
		failure = "Hero asset is not an imported PackedScene."
		_finish(false)
		return
	source_sha_before = FileAccess.get_sha256(asset_path)
	if source_sha_before.is_empty():
		failure = "Cannot hash original GLB source. Run from the source project, not an exported PCK."
		_finish(false)
		return
	root.size = Vector2i(width, height)
	root.content_scale_size = Vector2i(width, height)
	root.title = "YUGA — Staged Hero Model Review"
	root.msaa_3d = Viewport.MSAA_2X
	root.transparent_bg = false
	root.show()
	_make_studio()
	hero = packed.instantiate()
	hero.name = "ReviewedHero"
	studio.add_child(hero)
	animator = _find_animation(hero)
	_collect_skeletons(hero)
	if not animator or skeletons.is_empty():
		failure = "Required AnimationPlayer or Skeleton3D is missing."
		_finish(false)
		return
	for name: StringName in animator.get_animation_list():
		var simple := String(name).get_file().to_lower()
		clips[simple] = name
		clip_lengths[simple] = animator.get_animation(name).length
	for name in REQUIRED_CLIPS:
		if not clips.has(name) or float(clip_lengths[name]) <= 0:
			failure = "Required animation is missing or has zero duration: " + name
			_finish(false)
			return
	# Startup settling is real post-draw work, never an image of a dummy renderer.
	await _draw_frames(3)
	var specifications: Array[Dictionary] = [
		{"id": "01-front-idle", "angle_degrees": 0.0, "clip": "idle", "fraction": 0.25, "purpose": "Full-body front silhouette, face and material hierarchy"},
		{"id": "02-rear-idle", "angle_degrees": 180.0, "clip": "idle", "fraction": 0.25, "purpose": "Rear mantle, quiver, bow and silhouette"},
		{"id": "03-side-idle", "angle_degrees": 90.0, "clip": "idle", "fraction": 0.25, "purpose": "Profile depth and attachment placement"},
		{"id": "04-three-quarter-idle", "angle_degrees": 33.0, "clip": "idle", "fraction": 0.25, "purpose": "Facial planes, bow grip and shoulder asymmetry"}
	]
	for index in range(REQUIRED_CLIPS.size()):
		var clip: String = REQUIRED_CLIPS[index]
		specifications.append({"id": "%02d-pose-%s" % [index + 5, clip], "angle_degrees": 33.0, "clip": clip,
			"fraction": float(pose_overrides.get(clip, POSE_FRACTIONS[clip])),
			"purpose": "One static sampled pose; not a motion-continuity or extremum proof"})
	for specification in specifications:
		if Time.get_ticks_msec() - started_ms > timeout_seconds * 1000:
			failure = "Capture exceeded its wall-clock budget. Partial frames remain explicitly incomplete."
			_finish(false)
			return
		if not await _capture(specification):
			_finish(false)
			return
	if FileAccess.get_sha256(asset_path) != source_sha_before:
		failure = "Hero source changed during capture."
		_finish(false)
		return
	_finish(true)

func _parse_arguments() -> bool:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--asset="):
			asset_path = argument.trim_prefix("--asset=")
		elif argument.begins_with("--output="):
			output_path = argument.trim_prefix("--output=")
		elif argument.begins_with("--width="):
			width = argument.trim_prefix("--width=").to_int()
		elif argument.begins_with("--height="):
			height = argument.trim_prefix("--height=").to_int()
		elif argument.begins_with("--timeout="):
			timeout_seconds = argument.trim_prefix("--timeout=").to_float()
		elif argument.begins_with("--fractions="):
			var fractions_path := argument.trim_prefix("--fractions=")
			var file := FileAccess.open(fractions_path, FileAccess.READ)
			if not file:
				failure = "Cannot open authored pose-fraction overrides."
				return false
			var parsed = JSON.parse_string(file.get_as_text())
			if not parsed is Dictionary:
				failure = "Pose-fraction overrides must be a JSON object keyed by clip name."
				return false
			for key in parsed:
				if not key in REQUIRED_CLIPS or not (parsed[key] is float or parsed[key] is int) or not is_finite(float(parsed[key])) or float(parsed[key]) < 0 or float(parsed[key]) >= 1:
					failure = "Pose fractions must name a required clip and lie in [0, 1)."
					return false
			pose_overrides = parsed
		else:
			failure = "Unknown capture argument: " + argument
			return false
	if not asset_path.begins_with("res://") or not asset_path.ends_with(".glb"):
		failure = "--asset must identify an imported res:// GLB in this project."
		return false
	if not output_path.is_absolute_path():
		failure = "--output must be an absolute directory path."
		return false
	if width < 480 or width > 1600 or height < 480 or height > 1600 or timeout_seconds < 10 or timeout_seconds > 600:
		failure = "Capture dimensions must be 480–1600; timeout must be 10–600 seconds."
		return false
	return true

func _validate_import() -> bool:
	var configuration := ConfigFile.new()
	if configuration.load(asset_path + ".import") != OK:
		failure = "Missing GLB import metadata; import the final asset first."
		return false
	var imported_path: String = configuration.get_value("remap", "path", "")
	var checksum_path := imported_path.get_basename() + ".md5"
	if imported_path.is_empty() or not FileAccess.file_exists(imported_path) or not FileAccess.file_exists(checksum_path):
		failure = "Imported scene or import checksum is missing."
		return false
	var checksum_file := FileAccess.open(checksum_path, FileAccess.READ)
	var checksum_text := checksum_file.get_as_text()
	var pattern := RegEx.new()
	pattern.compile('source_md5="([a-f0-9]+)"')
	var matched := pattern.search(checksum_text)
	if not matched or matched.get_string(1) != FileAccess.get_md5(asset_path):
		failure = "GLB import cache is stale. Reimport the final asset before capturing."
		return false
	pattern.compile('dest_md5="([a-f0-9]+)"')
	matched = pattern.search(checksum_text)
	if not matched or matched.get_string(1) != FileAccess.get_md5(imported_path):
		failure = "Imported GLB scene checksum does not match its import stamp."
		return false
	imported_resource = {"path": imported_path, "sha256": FileAccess.get_sha256(imported_path), "source_md5_matches": true, "destination_md5_matches": true}
	return true

func _make_studio() -> void:
	studio = Node3D.new()
	studio.name = "StagedHeroReviewStudio"
	root.add_child(studio)
	current_scene = studio
	var world_environment := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("202a35")
	sky_material.sky_horizon_color = Color("3e474b")
	sky_material.ground_bottom_color = Color("182128")
	sky_material.ground_horizon_color = Color("3e474b")
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("c5d2df")
	environment.ambient_light_energy = 0.42
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = 1.0
	if RenderingServer.get_current_rendering_method() == "forward_plus":
		environment.ssao_enabled = true
		environment.ssao_radius = 0.8
		environment.ssao_intensity = 0.55
		# Studio material inspection avoids a bloom halo masking surface detail.
		environment.glow_enabled = false
	world_environment.environment = environment
	studio.add_child(world_environment)
	var floor := MeshInstance3D.new()
	floor.name = "NeutralStudioFloor"
	var floor_mesh := PlaneMesh.new()
	floor_mesh.size = Vector2(30, 30)
	floor.mesh = floor_mesh
	var floor_material := StandardMaterial3D.new()
	floor_material.albedo_color = Color("384047")
	floor_material.roughness = 0.82
	floor.material_override = floor_material
	studio.add_child(floor)
	_light("WarmKey", Vector3(-35, -35, 0), Color("ffe9d1"), 1.45, true)
	_light("CoolFill", Vector3(-20, 130, 0), Color("a7c6e4"), 0.55, false)
	_light("SoftRim", Vector3(-45, 190, 0), Color("e7e8f6"), 0.8, false)
	camera = Camera3D.new()
	camera.name = "ReviewCamera"
	camera.fov = 32.0
	camera.near = 0.05
	camera.far = 60.0
	studio.add_child(camera)
	camera.current = true
	var canvas := CanvasLayer.new()
	studio.add_child(canvas)
	var header := Label.new()
	header.position = Vector2(24, 20)
	header.text = "YUGA / RAMA   ·   STAGED MODEL REVIEW"
	header.add_theme_font_size_override("font_size", 16)
	header.add_theme_color_override("font_color", Color("e6dbc2"))
	header.add_theme_color_override("font_shadow_color", Color.BLACK)
	header.add_theme_constant_override("shadow_offset_x", 1)
	header.add_theme_constant_override("shadow_offset_y", 1)
	canvas.add_child(header)
	footer = Label.new()
	footer.position = Vector2(24, height - 62)
	footer.add_theme_font_size_override("font_size", 15)
	footer.add_theme_color_override("font_color", Color("c8d5db"))
	footer.add_theme_color_override("font_shadow_color", Color.BLACK)
	footer.add_theme_constant_override("shadow_offset_x", 1)
	footer.add_theme_constant_override("shadow_offset_y", 1)
	canvas.add_child(footer)

func _light(label: String, rotation: Vector3, color: Color, energy: float, shadows: bool) -> void:
	var light := DirectionalLight3D.new()
	light.name = label
	light.rotation_degrees = rotation
	light.light_color = color
	light.light_energy = energy
	light.shadow_enabled = shadows
	light.directional_shadow_max_distance = 15
	light.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	studio.add_child(light)

func _capture(specification: Dictionary) -> bool:
	var clip: String = specification.clip
	var fraction: float = specification.fraction
	var sample_time: float = float(clip_lengths[clip]) * fraction
	animator.play(clips[clip], 0)
	animator.seek(sample_time, true)
	animator.advance(0)
	animator.pause()
	var angle := deg_to_rad(float(specification.angle_degrees))
	camera.position = Vector3(sin(angle) * STUDIO_CAMERA_DISTANCE, 1.10, cos(angle) * STUDIO_CAMERA_DISTANCE)
	camera.look_at(STUDIO_CAMERA_TARGET)
	footer.text = "%s  ·  %s @ %.3fs\nStatic sampled pose / authored studio / no gameplay claim" % [specification.id, clip, sample_time]
	var frame_before := Engine.get_frames_drawn()
	await _draw_frames(2)
	if Time.get_ticks_msec() - started_ms > timeout_seconds * 1000:
		failure = "Capture exceeded its cooperative wall-clock budget."
		return false
	var bone_count := 0
	for skeleton in skeletons:
		for bone in skeleton.get_bone_count():
			var transform: Transform3D = skeleton.get_bone_global_pose(bone)
			if not transform.is_finite() or absf(transform.basis.determinant()) < 0.000001:
				failure = "Non-finite or singular sampled bone transform: " + clip
				return false
			bone_count += 1
	var image := root.get_texture().get_image()
	if not image or image.is_empty() or image.get_width() != width or image.get_height() != height:
		failure = "Rendered image is empty or has unexpected dimensions."
		return false
	var filename: String = specification.id + ".png"
	var destination := output_path.path_join(filename)
	var result := image.save_png(destination)
	if result != OK:
		failure = "Could not write captured PNG: " + error_string(result)
		return false
	var record := specification.duplicate(true)
	record["file"] = filename
	record["sha256"] = FileAccess.get_sha256(destination)
	var file := FileAccess.open(destination, FileAccess.READ)
	record["bytes"] = file.get_length()
	record["width"] = image.get_width()
	record["height"] = image.get_height()
	record["animation_time_seconds"] = sample_time
	record["animation_duration_seconds"] = clip_lengths[clip]
	record["bone_transforms_sampled_finite"] = bone_count
	record["camera"] = {"position": _vector(camera.position), "target": _vector(STUDIO_CAMERA_TARGET), "vertical_fov_degrees": camera.fov}
	record["rendered_frame_counter_before"] = frame_before
	record["rendered_frame_counter_after"] = Engine.get_frames_drawn()
	shots.append(record)
	print("YUGA_HERO_CAPTURE ", filename, " ", record.sha256)
	return true

func _draw_frames(count: int) -> void:
	# Await from this coroutine, never from _process(), which can deadlock a capture.
	for _index in range(count):
		await process_frame
		await RenderingServer.frame_post_draw

func _find_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node
	for child in node.get_children():
		var found := _find_animation(child)
		if found:
			return found
	return null

func _collect_skeletons(node: Node) -> void:
	if node is Skeleton3D:
		skeletons.append(node)
	for child in node.get_children():
		_collect_skeletons(child)

func _vector(value: Vector3) -> Array[float]:
	return [value.x, value.y, value.z]

func _finish(success: bool) -> void:
	if completed:
		return
	completed = true
	var report := {
		"schema": 1, "kind": "staged-actual-render-hero-review", "complete": success,
		"failure": failure, "asset_path": asset_path, "asset_sha256_before": source_sha_before,
		"asset_sha256_after": FileAccess.get_sha256(asset_path) if FileAccess.file_exists(asset_path) else "",
		"imported_resource": imported_resource,
		"capture_script_sha256": FileAccess.get_sha256("res://tools/capture-hero.gd"),
		"godot": Engine.get_version_info(), "renderer": RenderingServer.get_current_rendering_method(),
		"graphics_adapter": RenderingServer.get_video_adapter_name(), "display_server": DisplayServer.get_name(),
		"expected_shot_count": 13, "actual_shot_count": shots.size(), "clip_lengths_seconds": clip_lengths,
		"pose_fraction_overrides": pose_overrides, "wall_elapsed_ms": Time.get_ticks_msec() - started_ms,
		"studio": {"neutral_floor_y": 0, "tonemap": "Filmic", "exposure": 1.0, "glow": false,
			"key": {"color": "ffe9d1", "energy": 1.45}, "fill": {"color": "a7c6e4", "energy": 0.55}, "rim": {"color": "e7e8f6", "energy": 0.8}},
		"scope": ["Actual Godot-rendered pixels from an explicitly staged studio.",
			"Frozen AnimationPlayer poses; not gameplay, performance, animation-continuity or commercial-quality parity evidence.",
			"Pose fractions are representative samples unless separately evaluated; no automatic extremum claim.",
			"A human/agent visual review is still required for clipping, anatomy, framing and material quality."],
		"shots": shots
	}
	if output_path.is_absolute_path():
		DirAccess.make_dir_recursive_absolute(output_path)
		var file := FileAccess.open(output_path.path_join("hero-render-review.json"), FileAccess.WRITE)
		if file:
			file.store_string(JSON.stringify(report, "  ") + "\n")
	if success:
		print("YUGA_HERO_REVIEW_COMPLETE ", shots.size(), " staged frames")
	else:
		push_error("YUGA_HERO_REVIEW_FAILED: " + failure)
	quit(0 if success else 1)
