extends SceneTree
## Independent mounted geometry/handler probe; no rendered or OS-input claim.
var scene: Node3D
var output := ""
var cases: Array[Dictionary] = []
const FILES := ["res://scripts/confluence_world.gd", "res://scripts/native_field_shop_panel.gd", "res://scripts/native_field_shop.gd", "res://scripts/combat_match_metrics.gd", "res://scripts/confluence_battle_hud.gd", "res://scripts/rama_hero_hud.gd", "res://scripts/hero_ui_theme.gd", "res://scripts/input_bindings.gd", "res://assets/design/native-field-shop.json"]

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func frames(count := 8) -> void:
	for unused in count: await process_frame

func rect(value: Rect2) -> Dictionary:
	return {"x":value.position.x,"y":value.position.y,"w":value.size.x,"h":value.size.y}

func footer_state(shop: Control) -> Dictionary:
	var canvas := root.get_visible_rect()
	var scroll: ScrollContainer = shop.find_children("*","ScrollContainer",true,false)[0]
	var labels := {}
	for key in ["receipt","close_button"]:
		var control: Control = shop.get(key)
		labels[key] = {"text":control.text,"rect":rect(control.get_global_rect()),"panel_contained":shop.panel.get_global_rect().encloses(control.get_global_rect()),"canvas_contained":canvas.encloses(control.get_global_rect()),"inside_scroll":scroll.is_ancestor_of(control),"overlaps_scroll":control.get_global_rect().intersects(scroll.get_global_rect())}
	return {"panel_contained":canvas.encloses(shop.panel.get_global_rect()),"panel":rect(shop.panel.get_global_rect()),"scroll":rect(scroll.get_global_rect()),"controls":labels}

func inspect(label: String, physical: Vector2i, basis: Vector2i, scale: float) -> void:
	root.size = physical
	root.content_scale_size = basis
	root.content_scale_factor = scale
	# Use the actual restart lifecycle, never rewrite wallet/shield/metrics.
	scene._restart_army()
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	await frames()
	scene._layout_world_hud()
	scene._open_field_shop()
	await frames()
	var shop: Control = scene.field_shop_panel
	var initial := footer_state(shop)
	initial["close_focused"] = shop.close_button.has_focus()
	var scroll: ScrollContainer = shop.find_children("*","ScrollContainer",true,false)[0]
	var focus_checks: Array[Dictionary] = []
	for id in ["ward","escort"]:
		var button: Button = shop.rows[id].button
		button.grab_focus()
		await frames()
		focus_checks.append({"id":id,"enabled":not button.disabled,"focused":button.has_focus(),"contained_in_scroll":scroll.get_global_rect().encloses(button.get_global_rect()),"rect":rect(button.get_global_rect())})
	shop.rows.ward.button.pressed.emit()
	await frames()
	var purchased := footer_state(shop)
	purchased["actual_wallet"] = scene.field_shop.report().wallet
	purchased["actual_shield"] = scene.rama_runtime.vitals.shield
	var before_wallet: int = scene.field_shop.report().wallet
	# Adverse real owner rejection via UI handler after scripted out-of-range move.
	scene.player.global_position = Vector3(0,.05,0)
	shop._purchase("escort")
	await frames()
	var rejected := footer_state(shop)
	rejected["wallet_unchanged"] = scene.field_shop.report().wallet == before_wallet
	cases.append({"case":label,"physical":str(physical),"scale":scale,"logical_canvas":rect(root.get_visible_rect()),"initial":initial,"enabled_buy_focus":focus_checks,"valid_purchase":purchased,"rejected_purchase":rejected})
	shop.close()
	await frames(2)

func run() -> void:
	if not output.is_absolute_path() or FileAccess.file_exists(output): push_error("Fresh absolute --report required"); quit(1); return
	var before := {}
	for path in FILES: before[path] = FileAccess.get_sha256(path)
	before[get_script().resource_path] = FileAccess.get_sha256(get_script().resource_path)
	root.size = Vector2i(1280,720)
	root.content_scale_size = root.size
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene._set_volume(0,false)
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	await inspect("wide-1180",Vector2i(1180,650),Vector2i(1180,650),1.0)
	await inspect("wide-1280",Vector2i(1280,720),Vector2i(1280,720),1.0)
	await inspect("physical-960-150",Vector2i(960,540),Vector2i(1280,720),1.5)
	await inspect("physical-960-200",Vector2i(960,540),Vector2i(1280,720),2.0)
	await inspect("wide-return",Vector2i(1280,720),Vector2i(1280,720),1.0)
	var after := {}
	for path in before: after[path] = FileAccess.get_sha256(path)
	var result := {"source_before":before,"source_after":after,"sources_stable":before==after,"cases":cases,"scope":"Mounted headless real containers and owner purchase/rejection via emitted button/handler. Actual restart creates every fresh allowance. Scripted adverse position is explicit. No native rendering or actual OS input claim."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused = false
	current_scene = null
	scene.queue_free()
	await frames()
	quit(0)
