extends "res://tools/capture-hero.gd"
## Real rendered motion samples. Manual animation time is not a frame-rate benchmark.

var library_path := "res://assets/animations/tps_rama_motion_library.tres"
var library_sha := ""
var capture_sha := ""
var helper_sha := ""
var sequence := ["reference/tps_idle", "reference/tps_run", "fire", "reference/tps_idle"]
var max_clip_seconds := 3.0
var sample_hz := 24.0
var selected: Array[StringName] = []

func _run() -> void:
	width = 640
	height = 640
	timeout_seconds = 540
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			output_path = argument.trim_prefix("--output=")
		elif argument.begins_with("--library="):
			library_path = argument.trim_prefix("--library=")
		elif argument.begins_with("--max-clip-seconds="):
			max_clip_seconds = argument.trim_prefix("--max-clip-seconds=").to_float()
		else:
			failure = "Unknown motion capture argument: " + argument
	if not failure.is_empty() or not output_path.is_absolute_path() or not is_finite(max_clip_seconds) or max_clip_seconds < 0.5 or max_clip_seconds > 10:
		failure = "Require an absolute new output directory, finite clip duration in [0.5,10], and known arguments. " + failure
		_finish(false)
		return
	if DirAccess.dir_exists_absolute(output_path):
		push_error("Refusing to overwrite previous motion evidence: " + output_path)
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_path)
	if DisplayServer.get_name() == "headless" or not _validate_import():
		failure = "Require a real renderer and current imported asset. " + failure
		_finish(false)
		return
	var library = load(library_path)
	var packed = load(asset_path)
	if not library is AnimationLibrary or not packed is PackedScene:
		failure = "Missing animation library or hero scene."
		_finish(false)
		return
	source_sha_before = FileAccess.get_sha256(asset_path)
	library_sha = FileAccess.get_sha256(library_path)
	capture_sha = FileAccess.get_sha256("res://tools/capture-motion.gd")
	helper_sha = FileAccess.get_sha256("res://tools/capture-hero.gd")
	root.size = Vector2i(width, height)
	root.content_scale_size = root.size
	root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA / Bow Carry Motion Review"
	root.show()
	_make_studio()
	hero = packed.instantiate()
	studio.add_child(hero)
	animator = _find_animation(hero)
	_collect_skeletons(hero)
	if not animator or skeletons.is_empty() or animator.add_animation_library("reference", library) != OK:
		failure = "Cannot attach the candidate library to the target rig."
		_finish(false)
		return
	animator.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	for wanted in sequence:
		var found := StringName()
		for candidate in animator.get_animation_list():
			if String(candidate) == wanted or (not "/" in wanted and String(candidate).get_file().to_lower() == wanted):
				found = candidate
		if found.is_empty():
			failure = "Missing requested motion: " + wanted
			_finish(false)
			return
		selected.append(found)
	camera.position = Vector3(sin(deg_to_rad(33.0)) * STUDIO_CAMERA_DISTANCE, 1.10, cos(deg_to_rad(33.0)) * STUDIO_CAMERA_DISTANCE)
	camera.look_at(STUDIO_CAMERA_TARGET)
	await _draw_frames(3)
	var frame_id := 0
	for clip_index in selected.size():
		var clip := selected[clip_index]
		var animation := animator.get_animation(clip)
		var duration := minf(max_clip_seconds, animation.length * 2.0 + 0.25)
		animator.play(clip, 0.0 if clip_index == 0 else 0.18)
		animator.advance(0)
		for index in range(int(ceil(duration * sample_hz))):
			if index > 0:
				animator.advance(1.0 / sample_hz)
			footer.text = "%s / sample %d\n24 Hz sampled motion / 0.18 s blend / visual review pending" % [clip, index]
			await _draw_frames(1)
			if Time.get_ticks_msec() - started_ms > timeout_seconds * 1000:
				failure = "Capture wall-time budget exhausted."
				_finish(false)
				return
			for skeleton in skeletons:
				for bone in skeleton.get_bone_count():
					var pose: Transform3D = skeleton.get_bone_global_pose(bone)
					if not pose.is_finite() or absf(pose.basis.determinant()) < 0.000001:
						failure = "Invalid sampled bone transform."
						_finish(false)
						return
			var pixels := root.get_texture().get_image()
			var name := "frame-%05d.png" % frame_id
			var destination := output_path.path_join(name)
			if pixels.is_empty() or pixels.save_png(destination) != OK:
				failure = "Failed to save rendered frame."
				_finish(false)
				return
			shots.append({"file": name, "sha256": FileAccess.get_sha256(destination), "clip": clip,
				"clip_index": clip_index, "sample_time_seconds": index / sample_hz,
				"animation_position_seconds": animator.current_animation_position,
				"rendered_frame_counter": Engine.get_frames_drawn()})
			frame_id += 1
	if FileAccess.get_sha256(asset_path) != source_sha_before or FileAccess.get_sha256(library_path) != library_sha or FileAccess.get_sha256("res://tools/capture-motion.gd") != capture_sha or FileAccess.get_sha256("res://tools/capture-hero.gd") != helper_sha:
		failure = "Source changed during capture."
		_finish(false)
		return
	_finish(true)

func _finish(success: bool) -> void:
	if completed:
		return
	completed = true
	if output_path.is_absolute_path():
		DirAccess.make_dir_recursive_absolute(output_path)
		var report := {"complete": success, "failure": failure, "asset_sha256": source_sha_before,
			"library_sha256": library_sha, "capture_sha256": capture_sha, "studio_helper_sha256": helper_sha,
			"imported_resource": imported_resource, "godot": Engine.get_version_info(),
			"renderer": RenderingServer.get_current_rendering_method(), "graphics_adapter": RenderingServer.get_video_adapter_name(),
			"display_server": DisplayServer.get_name(), "sample_hz": sample_hz, "blend_seconds": 0.18,
			"sequence": sequence, "frame_count": shots.size(), "frames": shots,
			"scope": "Actual sequential rendered poses on exact target bytes; manual 24 Hz animation advance, not measured real-time FPS. Requires separate visual acceptance; no runtime promotion."}
		var file := FileAccess.open(output_path.path_join("motion-render-review.json"), FileAccess.WRITE)
		if file:
			file.store_string(JSON.stringify(report, "  ") + "\n")
		for script in ["capture-motion.gd", "capture-hero.gd"]:
			DirAccess.copy_absolute("res://tools/" + script, output_path.path_join(script))
	print("MOTION_CAPTURE ", "PASS" if success else "FAIL", " ", shots.size(), " frames ", failure)
	quit(0 if success else 1)
