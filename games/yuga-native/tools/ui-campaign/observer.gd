extends SceneTree
## Observer-only bridge. Product transitions are driven by native XTest input.
var output := ""
var mode := "component"
var elapsed := 0.0
var capturing := false
var captured: Array[String] = []
var observed_loaders: Dictionary = {}
var transition_events: Array[Dictionary] = []

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
		change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))

func _process(delta: float) -> bool:
	for node in root.find_children("*", "Control", true, false):
		if node.get_script() and node.get_script().resource_path.ends_with("scene_transition.gd"):
			_observe_transition(node)
	# Capture a real transient preparation frame without holding or changing its phase.
	if not capturing:
		var candidates := root.find_children("*", "Control", true, false)
		for node in candidates:
			if node.get_script() and node.get_script().resource_path.ends_with("scene_transition.gd") and node.is_busy():
				var id := "auto-" + str(node.phase) + "-" + str(node.snapshot().attempt)
				if not id in captured: _capture(id)
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

func _observe_transition(node: Control) -> void:
	var id := node.get_instance_id()
	if observed_loaders.has(id): return
	observed_loaders[id] = true
	node.phase_changed.connect(func(_phase,_message,_progress):_record_transition("phase",node))
	node.completed.connect(func(_destination):_record_transition("completed",node))
	node.failed.connect(func(_destination,_message):_record_transition("failed",node))
	node.cancelled.connect(func(_destination):_record_transition("cancelled",node))
	_record_transition("observed",node)

func _record_transition(kind: String, node: Control) -> void:
	var focus := root.gui_get_focus_owner()
	var event: Dictionary = node.snapshot()
	event.merge({"kind":kind,"frame":Engine.get_process_frames(),"instance_id":node.get_instance_id(),"scene_path":current_scene.scene_file_path if current_scene else "","scene_process_mode":current_scene.process_mode if current_scene else -1,"paused":paused,"focus":str(focus.get_path()) if focus else "","focus_can_process":focus.can_process() if focus else false,"owner_present":root.has_meta("yuga_scene_transition_owner")},true)
	transition_events.append(event)
	_write(output+"/transition-events.json",{"events":transition_events})
	# Publish observed short-lived phases immediately; do not hold or alter them.
	_write(output+"/state.json",snapshot())

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
	var result := {"mode":mode,"frame":Engine.get_process_frames(),"physics_frame":Engine.get_physics_frames(),"paused":paused,"mouse_mode":Input.mouse_mode,"window_focused":DisplayServer.window_is_focused(),"size":[root.size.x,root.size.y],"scene":str(current_scene.name) if current_scene else "", "scene_path":current_scene.scene_file_path if current_scene else "", "scene_process_mode":current_scene.process_mode if current_scene else -1,"scene_can_process":current_scene.can_process() if current_scene else false,"loader_count":0,"transition_layer_count":root.find_children("YugaSceneTransitionLayer","CanvasLayer",false,false).size(),"transition_event_count":transition_events.size(),"transition_owner_present":root.has_meta("yuga_scene_transition_owner"),"controls":[],"panels":{},"state":{}}
	var focus := root.gui_get_focus_owner()
	result.focus_name = str(focus.name) if focus else ""
	result.logical_viewport_size = [root.get_visible_rect().size.x,root.get_visible_rect().size.y]
	result.content_scale_factor = root.content_scale_factor
	result.focus = str(focus.get_path()) if focus else ""
	result.focus_text = str(focus.get("text")) if focus and "text" in focus else ""
	_walk(root, result)
	if current_scene:
		for key in ["started","world_ready","paused","overview","ready_to_play","playing","page_title","night","phase","target_phase","sensitivity","volume","invert_y","shadows"]:
			if key in current_scene: result.state[key] = current_scene.get(key)
		result.modal_scroll = {}
		for key in ["main_panel","pause_panel","settings_panel","controls_overlay","hero_panel","help_panel"]:
			if key in current_scene:
				var panel: Control = current_scene.get(key)
				if is_instance_valid(panel):
					result.panels[key] = panel.is_visible_in_tree()
					var scroll := panel.get_node_or_null("Card/Scroll")
					if scroll is ScrollContainer: result.modal_scroll[key] = scroll.scroll_vertical
		if "rama_panel" in current_scene and is_instance_valid(current_scene.rama_panel):
			var guide: Control = current_scene.rama_panel
			result.panels.rama_panel = guide.is_visible_in_tree()
			result.guide = {"selected_id":guide.selected_id,"detail_title":guide.detail_title.text,"details_scroll":guide.details_scroll.scroll_vertical,"abilities_scroll":guide.abilities_scroll.scroll_vertical,"notice":guide.effects_notice.text,"reduced_effects":guide.reduced_effects_button.button_pressed,"reduced_motion":guide.reduced_motion_button.button_pressed,"effects_enabled":not guide.reduced_effects_button.disabled,"receiver_present":is_instance_valid(guide._effect_receiver())}
			result.guide.key_text = guide.key_label.text if "key_label" in guide else ""
			result.guide.notice_fully_visible = guide.details_scroll.get_global_rect().encloses(guide.effects_notice.get_global_rect())
		if "rama_effects" in current_scene and is_instance_valid(current_scene.rama_effects):
			result.effect_options = current_scene.rama_effects.report()
		if "rama_hud" in current_scene and is_instance_valid(current_scene.rama_hud):
			var hero_hud: Control = current_scene.rama_hud
			result.hero_hud = {"visible":hero_hud.is_visible_in_tree(),"health":hero_hud.life.value,"health_text":hero_hud.life_text.text,"notice":hero_hud.note.text,"slots":hero_hud.slots.map(func(label):return label.text)}
		if "army" in current_scene and is_instance_valid(current_scene.army):
			result.army = current_scene.army.report()
			result.world = {}
			for key in ["lane_label","objective_label","goal_label","relay_hint","score_label"]:
				if key in current_scene: result.world[key] = current_scene.get(key).text
			if "compact_world_card" in current_scene and is_instance_valid(current_scene.compact_world_card):
				result.world.compact_visible = current_scene.compact_world_card.is_visible_in_tree()
				result.world.compact_lines = current_scene.compact_world_labels.map(func(label):return label.text)
			if "outcome_summary" in current_scene:
				result.world.outcome_visible = current_scene.outcome_summary.is_visible_in_tree()
				result.world.outcome_heading = current_scene.outcome_summary.heading.text
				result.world.outcome_detail = current_scene.outcome_summary.detail.text
		if "controls_overlay" in current_scene and is_instance_valid(current_scene.controls_overlay):
			result.state.capture_action = current_scene.controls_overlay.capture_action
		if "player" in current_scene and is_instance_valid(current_scene.player):
			result.state.player_active = current_scene.player.active
			result.state.hero_ready = current_scene.player.model_ready
			result.state.player_grounded = current_scene.player.is_on_floor()
			var actor: Node3D = current_scene.player
			result.presentation = {"suspended":actor.presentation_suspended,"player_sensitivity":actor.sensitivity,"player_invert_y":actor.invert_y,"player_position":[actor.global_position.x,actor.global_position.y,actor.global_position.z]}
			if is_instance_valid(actor.rama_motion):
				result.presentation.motion = actor.rama_motion.diagnostics()
				result.presentation.motion.locomotion_age = actor.rama_motion.locomotion_age
			if is_instance_valid(actor.rama_secondary): result.presentation.secondary = actor.rama_secondary.report()
			if is_instance_valid(actor.rama_face): result.presentation.face = actor.rama_face.report()
			if "map_control" in current_scene and is_instance_valid(current_scene.map_control):
				var location: Vector3=current_scene.map_control.hero_position
				result.presentation.atlas_position=[location.x,location.y,location.z]
				result.presentation.position_spaces="Player global; atlas world-local (identity world transform)."
		if "rama_runtime" in current_scene and is_instance_valid(current_scene.rama_runtime) and is_instance_valid(current_scene.rama_runtime.kit):
			result.kit=current_scene.rama_runtime.kit.report()
		var config:=ConfigFile.new()
		if config.load("user://courtyard-settings.cfg")==OK:
			result.preferences={}
			for section in config.get_sections():
				result.preferences[section]={}
				for key in config.get_section_keys(section): result.preferences[section][key]=config.get_value(section,key)
		result.audio_state={"master_bus_muted":AudioServer.is_bus_mute(0)}
		if "volume" in current_scene: result.audio_state.volume=current_scene.volume
		for key in ["audio","siege_effects","invocation_audio"]:
			if key in current_scene:
				var receiver: Node=current_scene.get(key)
				if is_instance_valid(receiver):
					if "volume" in receiver: result.audio_state[key+"_volume"]=receiver.volume
					if receiver.has_method("report"): result.audio_state[key]=receiver.report()
		if "rama_runtime" in current_scene and is_instance_valid(current_scene.rama_runtime) and is_instance_valid(current_scene.rama_runtime.action_audio):
			result.audio_state.action_audio=current_scene.rama_runtime.action_audio.report()
	return result

func _walk(node: Node, result: Dictionary) -> void:
	if node is Control:
		if node.name in ["MainMenu","PauseMenu","Settings","ControlsHelp","RamaHeroPanel","SceneTransition"]:
			result.panels[str(node.name)] = node.is_visible_in_tree()
		if node is BaseButton and node.is_visible_in_tree():
			var rect: Rect2 = node.get_global_rect()
			var screen_rect: Rect2 = root.get_screen_transform() * rect
			result.controls.append({"path":str(node.get_path()),"name":str(node.name),"text":node.text,"disabled":node.disabled,"interactive":node.can_process() and not node.disabled,"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"input_rect":[screen_rect.position.x,screen_rect.position.y,screen_rect.size.x,screen_rect.size.y],"focus":node.has_focus()})
		if node.get_script() and node.get_script().resource_path.ends_with("launch_shell.gd"):
			result.launch = node.snapshot()
		if node.get_script() and node.get_script().resource_path.ends_with("scene_transition.gd"):
			result.loader_count += 1
			result.transition = node.snapshot()
	for child in node.get_children(): _walk(child, result)
