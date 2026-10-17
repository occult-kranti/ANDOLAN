extends "res://tools/capture-traversal.gd"
## Six actual seconds spanning relay capture and supply, after 7.5s of real setup.

var before := {}
var after := {}
var captured := false
var supplied := false
var all_finite := true

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): output_path=argument.trim_prefix("--output=")
		else: quit(1);return
	if not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path) or FileAccess.file_exists(output_path): quit(1);return
	if DirAccess.make_dir_recursive_absolute(output_path)!=OK: quit(1);return
	if DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()!="forward_plus": _fail("Actual Forward+ display required");return
	if Engine.physics_ticks_per_second!=60 or not is_equal_approx(Engine.time_scale,1.0): _fail("Fixed 60Hz physics/time scale1 required");return
	sources=_source_hashes()
	for path in REQUIRED_IMPORTS:
		if not _validate_import(path): _finish(false);return
	capture_size=Vector2i(1280,720)
	root.size=capture_size
	root.content_scale_size=capture_size
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.msaa_3d=Viewport.MSAA_2X
	root.title="YUGA — Triad Relay Capture"
	root.show()
	scene=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene=scene
	await _draw_frames(4)
	if not scene.world_ready: _fail("World initialization failed");return
	scene.set_paused(false)
	scene.set_overview(false)
	scene.teleport_to(Vector3(0,.05,0),180)
	scene.player.ammo=3
	scene.player.active=false
	scene.relays.reset()
	scene.set_review_phase(0.0)
	if not _camera(Vector3(7,6,-11),Vector3(-2,1,0)): _fail("Capture camera obstructed");return
	# A fixture sets initial position and ammo once. Capture/supply then use actual physics.
	# The unrecorded preparation uses the same aspect ratio at reduced resolution.
	# This saves software-render time; recorded gameplay always uses1280x720.
	root.size=Vector2i(320,180)
	await _draw_frames(225)
	scene.set_paused(true)
	root.size=capture_size
	await _draw_frames(3)
	scene.set_paused(false)
	scene.player.active=false
	before=scene.relays.report()
	take_start_tick=Engine.get_physics_frames()
	var prior_tick:=take_start_tick
	var prior_draw:=Engine.get_frames_drawn()
	for index in FULL_FRAMES:
		await _draw_frames(1)
		var tick:=Engine.get_physics_frames()
		var draw:=Engine.get_frames_drawn()
		if tick-prior_tick!=2 or draw<=prior_draw: _fail("Nonconsecutive frame");return
		all_finite=all_finite and scene.player.position.is_finite()
		for unit in scene.army.units: all_finite=all_finite and unit.articulation_finite()
		var state: Dictionary=scene.relays.report()
		captured=captured or state.rules.sites[1].owner=="sun"
		supplied=supplied or state.arrows_total>=3
		var image:=_save_image("frame-%05d.png"%index)
		if image.is_empty(): _finish(false);return
		frames.append({"index":index,"physics_tick":tick,"physics_tick_delta":tick-prior_tick,"render_frame":draw,"finite":all_finite,"image":image,"relays":state,"ammo":scene.player.ammo})
		prior_tick=tick
		prior_draw=draw
		take_ticks=tick-take_start_tick
		if index%30==0: print("YUGA_TRIAD_CAPTURE frame=",index)
	after=scene.relays.report()
	if not captured or not supplied or not all_finite or before.rules.sites[1].owner!="neutral": _fail("Capture/supply scenario incomplete");return
	scene.set_overview(true)
	scene.ui.visible=false
	for view in [
		{"id":"lotus-day","position":Vector3(-9,3.4,-6),"target":Vector3(-5,1,4),"phase":0.0},
		{"id":"lotus-night","position":Vector3(-9,3.4,-6),"target":Vector3(-5,1,4),"phase":1.0},
		{"id":"reed-day","position":Vector3(-29,3.4,-6),"target":Vector3(-35,1,4),"phase":0.0},
		{"id":"sky-day","position":Vector3(29,3.4,-6),"target":Vector3(35,1,4),"phase":0.0}]:
		scene.set_review_phase(view.phase)
		if not _camera(view.position,view.target): _fail("Still camera obstructed: "+view.id);return
		await _draw_frames(3)
		stills.append({"id":view.id,"phase":view.phase,"position":view.position,"target":view.target,"image":_save_image("still-"+view.id+".png")})
	if sources!=_source_hashes(): _fail("Runtime changed during capture");return
	_finish(true)

func _camera(position: Vector3,target: Vector3) -> bool:
	scene.review_camera.global_position=position
	scene.review_camera.look_at(target,Vector3.UP)
	scene.review_camera.fov=58
	var point:=PhysicsPointQueryParameters3D.new()
	point.position=position
	point.collision_mask=1
	var ray:=PhysicsRayQueryParameters3D.create(position,target,1)
	if not scene.get_world_3d().direct_space_state.intersect_point(point,8).is_empty() or not scene.get_world_3d().direct_space_state.intersect_ray(ray).is_empty(): return false
	scene.review_camera.make_current()
	return true

func _source_hashes() -> Dictionary:
	var result:=super._source_hashes()
	for path in ["res://tools/capture-triad.gd","res://tools/run-triad-capture.py"]: result[path]=FileAccess.get_sha256(path)
	return result

func _finish(success: bool) -> void:
	var report:={"schema":1,"complete":success,"failure":failure,"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"fps":30,"physics_hz":Engine.physics_ticks_per_second,"time_scale":Engine.time_scale,"width":1280,"height":720,"take_start_tick":take_start_tick,"take_physics_ticks":take_ticks,"frames":frames,"stills":stills,"source_sha256":sources,"imports":imports,"before":before,"after":after,"outcomes":{"captured":captured,"supplied":supplied,"finite":all_finite},"staging":{"hero_position":[0,.05,0],"initial_ammo":3,"pre_take_draw_frames":225,"pre_take_seconds":7.5,"unrecorded_preparation_size":[320,180],"paused_resolution_settle_frames":3},"scope":"Actual offline physics after one initial hero/ammo/camera fixture. Six continuous1280x720 seconds cross capture then first supply; unrecorded preparation uses320x180. Four subsequent frozen-world art views. Silent software render at simulated30FPS; no human-input, hardware-FPS or final-art approval claim."}
	var file:=FileAccess.open(output_path.path_join("triad-render-review.json"),FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(_normal(report),"\t")+"\n")
	if not success: push_error(failure)
	quit(0 if success else 1)
