extends SceneTree
## Independent real-container probe. It observes mounted UI; no purchases,
## authority writes, source edits, renderer or real OS-input claims.
var scene: Node3D
var output := ""
var rows: Array[Dictionary] = []
var sources := {}
const FILES := ["res://scripts/confluence_world.gd", "res://scripts/confluence_battle_hud.gd", "res://scripts/native_field_shop_panel.gd", "res://scripts/native_field_shop.gd", "res://scripts/rama_hero_hud.gd", "res://scripts/hero_ui_theme.gd", "res://scripts/input_bindings.gd", "res://assets/design/native-field-shop.json"]

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func frames(count := 10) -> void:
	for unused in count: await process_frame

func rect(value: Rect2) -> Dictionary:
	return {"x":value.position.x,"y":value.position.y,"w":value.size.x,"h":value.size.y}

func inspect(label: String, physical: Vector2i, basis: Vector2i, scale: float) -> void:
	root.size = physical
	root.content_scale_size = basis
	root.content_scale_factor = scale
	await frames()
	scene._layout_world_hud()
	await frames()
	var canvas := root.get_visible_rect()
	var peers: Array[Control] = [scene.hud.get_node("TitleCard"), scene.hud.get_node("ControlsCard"), scene.hud.get_node("RelayStatus"), scene.hud.get_node("TraversalStatus"), scene.map_control, scene.rama_hud, scene.battle_hud.top, scene.battle_hud.shop_button]
	var controls: Array[Dictionary] = []
	var errors: Array[String] = []
	for index in peers.size():
		var control: Control = peers[index]
		controls.append({"path":str(control.get_path()),"visible":control.is_visible_in_tree(),"rect":rect(control.get_global_rect()),"minimum":str(control.get_combined_minimum_size())})
		if not control.is_visible_in_tree(): continue
		if not canvas.encloses(control.get_global_rect()): errors.append(str(control.name)+" outside canvas")
		for other in range(index+1, peers.size()):
			if peers[other].is_visible_in_tree() and control.get_global_rect().intersects(peers[other].get_global_rect()): errors.append(str(control.name)+" / "+str(peers[other].name))
	scene._open_field_shop()
	await frames()
	var shop: Control = scene.field_shop_panel
	var scroll: ScrollContainer = shop.panel.get_child(0)
	var shop_checks := {"panel_contained":canvas.encloses(shop.panel.get_global_rect()),"close_focused":shop.close_button.has_focus(),"close_in_scroll_clip":scroll.get_global_rect().encloses(shop.close_button.get_global_rect()),"panel":rect(shop.panel.get_global_rect()),"panel_minimum":str(shop.panel.get_combined_minimum_size()),"close":rect(shop.close_button.get_global_rect()),"scroll":rect(scroll.get_global_rect()),"scroll_vertical":scroll.scroll_vertical}
	rows.append({"case":label,"physical":str(physical),"content_basis":str(basis),"scale":scale,"canvas":rect(canvas),"wide_active":scene.battle_hud.active_layout,"controls":controls,"dashboard_errors":errors,"shop":shop_checks})
	shop.close()
	await frames(2)

func run() -> void:
	for path in FILES: sources[path] = FileAccess.get_sha256(path)
	root.size = Vector2i(1280,720)
	root.content_scale_size = root.size
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.rama_runtime.set_volume(0)
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	await inspect("wide-1180",Vector2i(1180,650),Vector2i(1180,650),1.0)
	await inspect("wide-1280",Vector2i(1280,720),Vector2i(1280,720),1.0)
	await inspect("compact-960-150",Vector2i(960,540),Vector2i(1280,720),1.5)
	await inspect("compact-960-200",Vector2i(960,540),Vector2i(1280,720),2.0)
	var after := {}
	for path in FILES: after[path] = FileAccess.get_sha256(path)
	var result := {"sources_before":sources,"sources_after":after,"sources_stable":sources==after,"cases":rows,"scope":"Real mounted Godot container geometry and focus/scroll observations. No renderer, OS input, purchase or human readability claim."}
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused = false
	current_scene = null
	scene.queue_free()
	await frames()
	quit(0)
