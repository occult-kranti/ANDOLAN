extends "res://tools/capture-hero.gd"
## Close actor inspection supplements, and never substitutes for, the full film.
var source_hashes := {}

func _run() -> void:
	width = 960
	height = 960
	timeout_seconds = 600
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			output_path = argument.trim_prefix("--output=")
	if not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path) or DisplayServer.get_name() == "headless":
		push_error("Require an unused absolute output directory and actual renderer")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_path)
	root.size = Vector2i(width, height)
	root.content_scale_size = root.size
	root.msaa_3d = Viewport.MSAA_2X
	root.show()
	_make_studio()
	for label in studio.find_children("*", "Label", true, false):
		if label != footer:
			label.text = "YUGA / DUEL ACTORS   ·   ACTUAL POSE REVIEW"
	for actor_id in ["rama", "ravana"]:
		asset_path = "res://assets/heroes/rama-production.glb" if actor_id == "rama" else "res://assets/cinematics/ravana-sentinel.glb"
		var library_path: String = "res://assets/cinematics/duel-motion-" + actor_id + ".tres"
		if not _validate_import():
			_finish(false)
			return
		source_hashes[asset_path] = FileAccess.get_sha256(asset_path)
		source_hashes[library_path] = FileAccess.get_sha256(library_path)
		hero = load(asset_path).instantiate()
		studio.add_child(hero)
		animator = _find_animation(hero)
		if not animator:
			animator = AnimationPlayer.new()
			hero.add_child(animator)
		animator.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		animator.add_animation_library("film", load(library_path))
		skeletons.clear()
		_collect_skeletons(hero)
		clips.clear()
		clip_lengths.clear()
		for name in animator.get_animation_list():
			if String(name).begins_with("film/"):
				var simple := String(name).get_file()
				clips[simple] = name
				clip_lengths[simple] = animator.get_animation(name).length
		var poses := [{"clip":"ready","fraction":0.5,"angle":33.0},
			{"clip":"draw","fraction":0.95,"angle":33.0},
			{"clip":"release","fraction":0.25,"angle":75.0},
			{"clip":"evade","fraction":0.5,"angle":33.0}] if actor_id == "rama" else [
			{"clip":"ready","fraction":0.5,"angle":33.0},
			{"clip":"guard","fraction":0.5,"angle":33.0},
			{"clip":"cast_windup","fraction":0.95,"angle":33.0},
			{"clip":"recoil","fraction":0.3,"angle":33.0}]
		for specification in poses:
			var entry := {"id":actor_id + "-" + specification.clip, "clip":specification.clip,
				"fraction":specification.fraction, "angle_degrees":specification.angle,
				"purpose":"Actual film library close pose; separate from continuous motion acceptance"}
			if not await _capture(entry):
				_finish(false)
				return
		hero.queue_free()
		await process_frame
	for path in source_hashes:
		if source_hashes[path] != FileAccess.get_sha256(path):
			failure = "Actor source changed during pose capture"
			_finish(false)
			return
	_finish(true)

func _finish(success: bool) -> void:
	var report := {"kind":"actual-duel-actor-pose-review", "complete":success, "failure":failure,
		"source_sha256":source_hashes,"frame_count":shots.size(),"frames":shots,
		"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),
		"scope":"Actual studio views of film animation poses. Not continuous movement, gameplay or visual quality acceptance."}
	var file := FileAccess.open(output_path.path_join("combat-film-render.json"),FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(report,"  ")+"\n")
	print("YUGA_DUEL_POSES ", "PASS" if success else "FAIL", " ", shots.size(), " ", failure)
	quit(0 if success else 1)
