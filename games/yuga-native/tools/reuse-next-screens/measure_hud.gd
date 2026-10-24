extends SceneTree
## Source-bound matched layout fixture; --capture adds original native frames.
var output := ""
var capture := false
var world: Node3D
var samples := []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		if arg=="--capture": capture=true
	call_deferred("run")

func frames(count := 3) -> void:
	for unused in count:
		await process_frame
		if capture: await RenderingServer.frame_post_draw

func progress(stage: String) -> void:
	FileAccess.open(output.path_join("progress.json"),FileAccess.WRITE).store_string(JSON.stringify({"stage":stage,"frame":Engine.get_process_frames(),"drawn":Engine.get_frames_drawn(),"paused":paused,"window_visible":root.visible})+"\n")

func rect(control: Control) -> Dictionary:
	var box:=control.get_global_rect()
	return {"x":box.position.x,"y":box.position.y,"w":box.size.x,"h":box.size.y}

func label(label_: Label) -> Dictionary:
	var needed:=label_.get_theme_font("font").get_multiline_string_size(label_.text,HORIZONTAL_ALIGNMENT_LEFT,label_.size.x,label_.get_theme_font_size("font_size"))
	return {"text":label_.text,"rect":rect(label_),"needed":[needed.x,needed.y],"minimum":str(label_.get_combined_minimum_size()),"font_size":label_.get_theme_font_size("font_size")}

func sample(id: String, base: Vector2i, scale_: float) -> void:
	progress("layout "+id)
	root.size=Vector2i(960,540)
	root.content_scale_size=base
	root.content_scale_factor=scale_
	await frames()
	world._update_practice_hud()
	world.rama_hud._refresh()
	await frames()
	var hud:Control=world.rama_hud
	var drawn:Rect2=hud.status_panel.get_global_rect()
	for card in hud.slot_cards: drawn=drawn.merge(card.get_global_rect())
	var data:Dictionary={"id":id,"base":[base.x,base.y],"window":[root.size.x,root.size.y],"scale":scale_,"logical":str(root.get_visible_rect().size),"hud":rect(hud),"drawn_slab":str(drawn),"status":rect(hud.status_panel),"notice":label(hud.note),"health":label(hud.life_text),"slots":hud.slots.map(func(s):return label(s)),"summary":rect(world.compact_world_card),"summary_rows":world.compact_world_labels.map(func(s):return label(s)),"map":rect(world.map_control),"map_plot":str(world.map_control._plot_rect()),"map_footer":label(world.map_control.get_node("AtlasLegend")),"kit":world.rama_runtime.kit.report()}
	if capture:
		progress("framebuffer "+id)
		await RenderingServer.frame_post_draw
		var path:=output.path_join(id+".png")
		var saved:=root.get_texture().get_image().save_png(path)
		data["png"]={"path":path,"sha256":FileAccess.get_sha256(path),"save_error":saved,"frame":Engine.get_process_frames()}
	samples.append(data)

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
	for base in [Vector2i(1280,720),Vector2i(960,540)]:
		for scale_ in [1.0,1.5,2.0]:
			await sample("idle-base"+str(base.x)+"-scale"+str(roundi(scale_*100)),base,scale_)
	# Actual kit request, actual release/ammo use and actual reload API. Timing
	# is stepped by the fixture; these frames are disclosed as arranged states.
	var cast:Dictionary=world.cast_rama_ability("kodanda")
	for unused in 9:world.army.step_simulation(.05)
	var reload_started:bool=world.player.start_reload()
	for base in [Vector2i(1280,720),Vector2i(960,540)]:await sample("reload-base"+str(base.x)+"-scale200",base,2.0)
	var damage:Dictionary=world.rama_runtime.vitals.receive_damage(1000,"HUD layout fixture",world.rama_runtime.vitals.generation,0)
	for base in [Vector2i(1280,720),Vector2i(960,540)]:await sample("returning-base"+str(base.x)+"-scale200",base,2.0)
	var stable := source_before.keys().all(func(path):return source_before[path]==FileAccess.get_sha256(path))
	var report:Dictionary={"schema":1,"scope":"Matched actual-world layout fixture. Authority clocks held after reset; reload entered through real kit/reload APIs with fixture stepping. Returning uses actual vitals damage. Native journey/input is separate.","capture":capture,"engine":Engine.get_version_info(),"display":DisplayServer.get_name(),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"source_sha256":source_before,"source_stable":stable,"staging":{"cast":cast,"reload_started":reload_started,"damage":damage},"samples":samples}
	FileAccess.open(output.path_join("measurement.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	current_scene=null;world.queue_free();await frames()
	quit(0 if stable else 1)
