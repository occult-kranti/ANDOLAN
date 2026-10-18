extends SceneTree
## Observer-only bridge. Product transitions are driven by native XTest input.
var output := ""
var mode := "component"
var elapsed := 0.0
var capturing := false
var captured: Array[String] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		if arg.begins_with("--mode="): mode = arg.trim_prefix("--mode=")
	call_deferred("_boot")

func _boot() -> void:
	root.title = "YUGA UI campaign"
	if mode == "component":
		var board = load("res://tools/ui-campaign/board.gd").new()
		root.add_child(board)
		current_scene = board
	else:
		change_scene_to_file("res://scenes/courtyard.tscn")

func _process(delta: float) -> bool:
	elapsed += delta
	if elapsed < .1: return false
	elapsed = 0.0
	_write(output + "/state.json", snapshot())
	var request := output + "/capture-request.json"
	if not capturing and FileAccess.file_exists(request):
		var data = JSON.parse_string(FileAccess.get_file_as_string(request))
		if data is Dictionary and not str(data.get("name", "")).is_empty() and not str(data.name) in captured:
			_capture(str(data.name))
	return false

func _write(path: String, data: Dictionary) -> void:
	var file := FileAccess.open(path + ".tmp", FileAccess.WRITE)
	file.store_string(JSON.stringify(data, "\t"))
	file.close()
	DirAccess.rename_absolute(path + ".tmp", path)

func _capture(id: String) -> void:
	capturing = true
	await RenderingServer.frame_post_draw
	var path := output + "/" + id + ".png"
	var status := root.get_texture().get_image().save_png(path)
	var state := snapshot()
	state.merge({"file": id + ".png", "png_status":status, "sha256":FileAccess.get_sha256(path)}, true)
	_write(output + "/" + id + ".json", state)
	captured.append(id)
	capturing = false

func snapshot() -> Dictionary:
	var result := {"mode":mode,"frame":Engine.get_process_frames(),"paused":paused,"mouse_mode":Input.mouse_mode,"window_focused":DisplayServer.window_is_focused(),"size":[root.size.x,root.size.y],"scene":str(current_scene.name) if current_scene else "", "controls":[],"panels":{},"state":{}}
	var focus := root.gui_get_focus_owner()
	result.focus = str(focus.get_path()) if focus else ""
	result.focus_text = str(focus.get("text")) if focus and "text" in focus else ""
	_walk(root, result)
	if current_scene:
		for key in ["started","world_ready","paused","overview"]:
			if key in current_scene: result.state[key] = current_scene.get(key)
	return result

func _walk(node: Node, result: Dictionary) -> void:
	if node is Control:
		if node.name in ["MainMenu","PauseMenu","Settings","ControlsHelp","RamaHeroPanel","SceneTransition"]:
			result.panels[str(node.name)] = node.is_visible_in_tree()
		if node is BaseButton and node.is_visible_in_tree():
			var rect: Rect2 = node.get_global_rect()
			result.controls.append({"path":str(node.get_path()),"name":str(node.name),"text":node.text,"disabled":node.disabled,"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"focus":node.has_focus()})
		if node.get_script() and node.get_script().resource_path.ends_with("launch_shell.gd"):
			result.launch = node.snapshot()
		if node.get_script() and node.get_script().resource_path.ends_with("scene_transition.gd"):
			result.transition = node.snapshot()
	for child in node.get_children(): _walk(child, result)
