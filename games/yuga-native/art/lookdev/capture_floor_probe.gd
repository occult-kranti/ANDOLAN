extends "res://tools/capture-rama-lookdev.gd"
## Finite actual-scene shadow isolation. Does not change runtime sources/assets.
var floor_nodes: Array[MeshInstance3D] = []
var floor_original: Array[int] = []
var settings_by_shot: Dictionary = {}
const VARIANTS := ["candidate", "restored_bias", "shadows_off", "ground_cast_off"]

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		else: finish("Unknown argument: " + arg); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Require fresh absolute output"); return
	if DisplayServer.get_name() == "headless" or RenderingServer.get_current_rendering_method() != "forward_plus": finish("Actual Forward+ required"); return
	DirAccess.make_dir_recursive_absolute(output)
	for directory in ["scripts", "shaders", "assets", "scenes"]: pin_directory("res://" + directory)
	for path in ["res://tools/capture-rama-lookdev.gd", "res://art/lookdev/capture_floor_probe.gd"]: sources[path] = FileAccess.get_sha256(path)
	for path in sources:
		if path.ends_with(".glb") and not fresh_import(path): finish("Stale import: " + path); return
	root.size = Vector2i(1280,720); root.content_scale_size = root.size
	root.msaa_3d = Viewport.MSAA_2X; root.title = "YUGA floor shadow isolation"; root.show()
	scene = load("res://scenes/courtyard.tscn").instantiate(); root.add_child(scene); current_scene = scene
	await draw(8); paused = true
	var frozen_pose := pose_pin(scene.player.visual)
	collect_floor("courtyard")
	if floor_nodes.size() != 5: finish("Expected courtyard four slab groups plus foundation"); return
	for variant in VARIANTS:
		Production.apply(scene.world_environment.environment, scene.sun, scene.world, false, true)
		apply_variant(variant, .7)
		await capture("title-day-" + variant, true, 0.0, variant, frozen_pose)
		if completed: return
	clear_floor()
	scene.queue_free(); paused = false; await process_frame
	scene = load("res://scenes/confluence_world.tscn").instantiate(); root.add_child(scene); current_scene = scene
	await draw(8)
	if not scene.world_ready: finish("Actual world not ready"); return
	scene.set_paused(false); scene.set_overview(false); scene.player.active = false; scene.ui.hide()
	scene.player.global_position = Vector3(-40,.05,-10); scene.player.velocity = Vector3.ZERO
	paused = true
	var camera := Camera3D.new(); scene.add_child(camera); camera.fov = 58
	camera.global_position = scene.player.global_position + Vector3(2.7,1.6,4.8)
	camera.look_at(scene.player.global_position + Vector3(0,1.0,0)); camera.make_current()
	frozen_pose = pose_pin(scene.player.visual)
	collect_floor("world")
	if floor_nodes.size() != 2: finish("Expected world paving and apron"); return
	for variant in VARIANTS:
		WorldLight.apply(scene.world_environment.environment, scene.sun, scene.world, .5, true)
		apply_variant(variant, .55)
		await capture("world-50-" + variant, true, .5, variant, frozen_pose)
		if completed: return
	clear_floor()
	finish("")

func collect_floor(kind: String) -> void:
	floor_nodes.clear(); floor_original.clear()
	for mesh in scene.world.find_children("*", "MeshInstance3D", true, false):
		var match_floor: bool = (String(mesh.name).begins_with("FLOOR_BEVEL_") or mesh.name == "COL_Limestone_mortar") if kind == "courtyard" else mesh.name in ["FlatCityPaving", "NoncollidingTerrainApron"]
		if match_floor:
			floor_nodes.append(mesh); floor_original.append(mesh.cast_shadow)

func clear_floor() -> void:
	for index in floor_nodes.size(): floor_nodes[index].cast_shadow = floor_original[index]
	floor_nodes.clear(); floor_original.clear()

func apply_variant(variant: String, old_normal_bias: float) -> void:
	for index in floor_nodes.size(): floor_nodes[index].cast_shadow = floor_original[index]
	if variant == "restored_bias":
		scene.sun.shadow_bias = .035; scene.sun.shadow_normal_bias = old_normal_bias
	elif variant == "shadows_off": scene.sun.shadow_enabled = false
	elif variant == "ground_cast_off":
		for mesh in floor_nodes: mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var nodes := []
	for mesh in floor_nodes: nodes.append({"path":String(mesh.get_path()),"cast_shadow":mesh.cast_shadow,"visible":mesh.visible,"position":str(mesh.global_position)})
	var id: String = ("title-day-" if old_normal_bias == .7 else "world-50-") + variant
	settings_by_shot[id] = {"variant":variant,"shadow_enabled":scene.sun.shadow_enabled,"shadow_bias":scene.sun.shadow_bias,"shadow_normal_bias":scene.sun.shadow_normal_bias,"sun_rotation":str(scene.sun.rotation_degrees),"sun_energy":scene.sun.light_energy,"ambient_energy":scene.world_environment.environment.ambient_light_energy,"ssao_enabled":scene.world_environment.environment.ssao_enabled,"ground_cast_nodes":nodes,"sun_shadow_receiving_preserved":variant=="ground_cast_off"}

func finish(failure: String) -> void:
	if completed: return
	completed = true
	var unchanged := true
	for path in sources:
		if FileAccess.get_sha256(path) != sources[path]: unchanged = false
	for path in imports:
		if FileAccess.get_sha256(imports[path].imported) != imports[path].sha256: unchanged = false
	for shot in shots: shot["settings"] = settings_by_shot.get(shot.id,{})
	var cleanup := {"retired":true, "scene_present":false}
	if is_instance_valid(scene): cleanup = await _retire_scene_audio(scene)
	var report := {"complete":failure.is_empty() and unchanged and shots.size()==8 and cleanup.retired,"failure":failure,"source_unchanged":unchanged,"sources":sources,"imports":imports,"shots":shots,"harness_cleanup":cleanup,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"display":DisplayServer.get_name(),"scope":"Finite matched-camera/pose/exposure actual-scene shadow-causality probe only; no runtime edits, physical-GPU or finished-art acceptance."}
	if output.is_absolute_path() and DirAccess.dir_exists_absolute(output): FileAccess.open(output.path_join("floor-probe.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	paused = false
	print("RAMA_FLOOR_PROBE ",report.complete," ",failure)
	quit(0 if report.complete else 1)

func _retire_scene_audio(owner_: Node3D) -> Dictionary:
	var playbacks: Array[WeakRef] = []
	for type_ in ["AudioStreamPlayer", "AudioStreamPlayer2D", "AudioStreamPlayer3D"]:
		for voice in owner_.find_children("*", type_, true, false):
			if voice.playing:
				var playback = voice.get_stream_playback()
				if playback != null: playbacks.append(weakref(playback))
				playback = null
			voice.stop()
	paused = false
	owner_.queue_free()
	await process_frame
	await process_frame
	var begin := Time.get_ticks_msec()
	# A stopped/paused voice may already have a null playback property while the
	# Dummy mixer still owns a retiring WAV buffer. Do not quit in that interval.
	await create_timer(.1, true, false, true).timeout
	while playbacks.any(func(reference: WeakRef): return reference.get_ref() != null) and Time.get_ticks_msec() - begin < 1000:
		await create_timer(.025).timeout
	return {"retired":not playbacks.any(func(reference: WeakRef): return reference.get_ref() != null),
		"scene_present":true, "sampled_playbacks":playbacks.size(), "minimum_mixer_wait_s":.1,
		"wait_ms":Time.get_ticks_msec()-begin, "driver":AudioServer.get_driver_name()}
