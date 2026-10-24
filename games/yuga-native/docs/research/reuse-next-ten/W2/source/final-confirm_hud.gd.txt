extends "res://tools/reuse-next-screens/measure_hud.gd"
## Two worst-case confirmations after independent visual R1 findings.
func run() -> void:
	if not output.is_absolute_path() or not DirAccess.dir_exists_absolute(output):
		printerr("Existing absolute output directory required"); quit(2); return
	if capture and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):
		printerr("Capture requires actual X11 Forward+ display"); quit(2); return
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.content_scale_size=Vector2i(1280,720)
	root.size=Vector2i(960,540)
	root.msaa_3d=Viewport.MSAA_2X
	if capture: root.show()
	var source_before := {}
	for path in ["res://scripts/confluence_world.gd","res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd","res://scripts/world_atlas.gd",get_script().resource_path]:source_before[path]=FileAccess.get_sha256(path)
	world=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world);current_scene=world
	progress("world instantiated")
	await frames(8)
	progress("initial frames complete")
	while not world.world_ready or not world.player.model_ready: await process_frame
	progress("model ready")
	world._restart_army()
	progress("practice reset")
	for unused in 8:await physics_frame
	progress("grounding complete")
	world.set_process(false);world.set_physics_process(false)
	world.player.set_physics_process(false);world.army.set_physics_process(false)
	world.rama_hud.set_process(false);world.rama_effects.set_process(false)
	await sample("idle-base960-scale200",Vector2i(960,540),2.0)
	var damage:Dictionary=world.rama_runtime.vitals.receive_damage(1000,"HUD layout fixture",world.rama_runtime.vitals.generation,0)
	await sample("returning-base960-scale200",Vector2i(960,540),2.0)
	var stable := source_before.keys().all(func(path):return source_before[path]==FileAccess.get_sha256(path))
	var report:Dictionary={"schema":1,"scope":"Matched actual-world layout fixture. Authority clocks held after reset; reload entered through real kit/reload APIs with fixture stepping. Returning uses actual vitals damage. Native journey/input is separate.","capture":capture,"engine":Engine.get_version_info(),"display":DisplayServer.get_name(),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"source_sha256":source_before,"source_stable":stable,"staging":{"damage":damage},"samples":samples}
	FileAccess.open(output.path_join("measurement.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	current_scene=null;world.queue_free();await frames()
	quit(0 if stable else 1)
