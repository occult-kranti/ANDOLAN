extends SceneTree
## Measures real current native layout; no pixel or input-journey acceptance.
var output := ""
var world: Node3D

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func frames(count: int = 8) -> void:
	for unused in count: await process_frame

func bounds(control: Control, label: String) -> Dictionary:
	var rect := control.get_global_rect()
	return {"label":label,"visible":control.is_visible_in_tree(),"x":rect.position.x,"y":rect.position.y,"w":rect.size.x,"h":rect.size.y}

func run() -> void:
	Engine.max_fps = 60
	root.size = Vector2i(960,540)
	root.content_scale_size = Vector2i(1280,720)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	world = load("res://scripts/confluence_world.gd").new()
	root.add_child(world)
	current_scene = world
	await frames(20)
	world.set_process(false)
	world.set_physics_process(false)
	world.player.set_physics_process(false)
	world.army.set_physics_process(false)
	var samples := []
	for scale_ in [1.0,2.0]:
		root.content_scale_factor = scale_
		await frames()
		world._update_practice_hud()
		await frames()
		var cards := []
		for name_ in ["TitleCard","RelayStatus","ControlsCard","TraversalStatus"]:
			cards.append(bounds(world.hud.get_node(name_),name_))
		cards.append(bounds(world.compact_world_card,"compact-summary"))
		cards.append(bounds(world.map_control,"minimap"))
		cards.append(bounds(world.rama_hud.status_panel,"combat-status"))
		for index in world.rama_hud.slot_cards.size():
			cards.append(bounds(world.rama_hud.slot_cards[index],"ability-"+str(index)))
		var canvas := root.get_visible_rect().size
		samples.append({"scale":scale_,"window":[root.size.x,root.size.y],"canvas":[canvas.x,canvas.y],"cards":cards,"summary_rows":world.compact_world_labels.map(func(row):return row.text),"rama_hud_height":world.rama_hud.size.y})
	var report := {"schema":1,"scope":"Current canonical headless layout measurement only. Actual starting image references are separate; no current render, input, artistic or gameplay pass.","samples":samples,"source_hashes":{},"engine":Engine.get_version_info()}
	for path in ["res://scripts/confluence_world.gd","res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd","res://scripts/world_atlas.gd",get_script().resource_path]:
		report.source_hashes[path] = FileAccess.get_sha256(path)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	current_scene = null
	world.queue_free()
	await frames()
	quit(0)
