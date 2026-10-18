extends SceneTree
## Native input, real effect receiver, transactional preferences and modal scope.
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Controls = preload("res://scripts/controls_overlay.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const UI = preload("res://scripts/hero_ui_theme.gd")
var checks: Array[Dictionary] = []
var output := ""
var closes := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func frames() -> void:
	for unused in range(5): await process_frame

func press(code: int, shift := false) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = down
		event.shift_pressed = shift
		root.push_input(event)
		await process_frame

func _run() -> void:
	Bindings.install("user://u3-guide.cfg")
	Bindings.merge_settings({"audio":{"volume":.25},"video":{"fullscreen":true}},Bindings.config_path)
	var host := Control.new()
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(host)
	var recovery := Button.new()
	recovery.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(recovery)
	var guide := Guide.new()
	host.add_child(guide)
	guide.closed.connect(func(): closes += 1)
	guide.open()
	record("Guide separates a real bow and four abilities",guide.ability_buttons.size()==5 and guide._list.has_node("BowHeading") and guide._list.has_node("AbilitiesHeading") and guide._rules.size()==5)
	record("Absent effect receiver presents unavailable disabled controls",guide.reduced_effects_button.disabled and guide.reduced_motion_button.disabled and guide.effects_notice.text.contains("unavailable"))
	guide.ability_buttons.dawn_volley.grab_focus()
	await press(KEY_TAB)
	record("Keyboard skips unavailable capabilities",root.gui_get_focus_owner()==guide.close_button)
	var effects := Effects.new()
	root.add_child(effects)
	guide.configure_effects(effects)
	guide.reduced_effects_button.grab_focus()
	await press(KEY_ENTER)
	var saved: ConfigFile = Bindings.read_config(Bindings.config_path).config
	record("Native toggle persists to actual Rama effect receiver",effects.report().reduced_effects and guide.reduced_effects_button.button_pressed and saved.get_value("rama_effects","reduced_effects",false))
	record("Effect preference preserves sound/display and simulation-free state",saved.get_value("audio","volume",0)==.25 and saved.get_value("video","fullscreen",false) and effects.report().active==0 and effects.report().counts.accepted==0)
	Bindings.config_path = "user://missing-u3-guide/preferences.cfg"
	guide.reduced_motion_button.grab_focus()
	await press(KEY_ENTER)
	record("Failed persistence keeps prior live effect preference and states truthfully",not effects.report().reduced_motion and not guide.reduced_motion_button.button_pressed and effects.report().reduced_effects and guide.effects_notice.text.contains("Could not save") and guide.effects_notice.text.contains("unchanged"))
	Bindings.config_path = "user://u3-guide.cfg"
	guide.close()
	guide.open()
	record("Reopening reloads saved ability-only preference",guide.reduced_effects_button.button_pressed and effects.report().reduced_effects and guide.effects_notice.text.contains("Rama’s ability effects only"))
	var remap := Bindings.set_binding("pulse",KEY_J)
	guide.refresh_bindings()
	guide.select_ability("piercing_dawn")
	record("Saved keys appear in list and selected ability details",remap.ok and guide.ability_buttons.piercing_dawn.text.begins_with("J") and guide.key_label.text.begins_with("J"))
	var style: StyleBoxFlat = guide.ability_buttons.piercing_dawn.get_theme_stylebox("normal")
	record("Selected guide item uses the shared semantic state",guide.ability_buttons.piercing_dawn.theme_type_variation==UI.BUTTON_TYPES[&"selected"] and style.border_color==UI.GOLD)
	var before_close := closes
	host.hide()
	recovery.grab_focus()
	await press(KEY_ESCAPE)
	record("Hidden guide cannot consume Escape or restore stale focus",closes==before_close and root.gui_get_focus_owner()==recovery)
	host.show()
	host.process_mode = Node.PROCESS_MODE_DISABLED
	guide.open()
	await press(KEY_ESCAPE)
	record("Disabled ancestor isolates ALWAYS guide and recovery focus",closes==before_close and root.gui_get_focus_owner()==recovery)
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	paused = true
	guide.open()
	for dimensions in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await frames()
		var contained := root.get_visible_rect().encloses(guide.card.get_global_rect()) and guide.card.get_global_rect().encloses(guide.close_button.get_global_rect())
		for button in guide.ability_buttons.values():
			button.grab_focus()
			await frames()
			contained = contained and guide.abilities_scroll.get_global_rect().encloses(button.get_global_rect())
		record("Grouped abilities remain reachable at "+str(dimensions),contained,{"card":str(guide.card.get_global_rect())})
		guide.select_ability("guardian_circle")
		guide.ability_buttons.guardian_circle.grab_focus()
		await frames()
		await press(KEY_PAGEDOWN)
		var paged := guide.details_scroll.scroll_vertical>0
		await press(KEY_END)
		var at_end := guide.details_scroll.get_global_rect().encloses(guide.effects_notice.get_global_rect())
		await press(KEY_HOME)
		record("Detail paging reaches bottom and returns without changing selection "+str(dimensions),paged and at_end and guide.details_scroll.scroll_vertical==0 and guide.selected_id=="guardian_circle" and paused)
	guide.close()
	var controls := Controls.new()
	host.add_child(controls)
	controls.open()
	await frames()
	var mapped := []
	for group in controls.BINDING_GROUPS:
		for action in group.actions: mapped.append(action)
	var unique := {}
	for action in mapped: unique[action] = true
	record("Control groups cover every real remappable action once",mapped.size()==Bindings.DEFAULTS.size() and unique.size()==Bindings.DEFAULTS.size() and mapped.all(func(action): return Bindings.DEFAULTS.has(action)))
	controls.begin_capture("reload")
	await frames()
	await press(KEY_END)
	await frames()
	var preferences: Label = controls.card.find_child("PreferencesLocation",true,false)
	var scroll: ScrollContainer = controls.card.find_child("MappingsScroll",true,false)
	record("Keyboard reaches real settings routes while capture remains safe",scroll.get_global_rect().encloses(preferences.get_global_rect()) and controls.capture_action=="reload" and not preferences.text.contains("global"),{"scroll":str(scroll.get_global_rect()),"preferences":str(preferences.get_global_rect()),"position":scroll.scroll_vertical})
	await press(KEY_HOME)
	await press(KEY_ESCAPE)
	record("Paging does not remap keys and Escape retains caller pause",controls.capture_action.is_empty() and controls.visible and Bindings.label("reload")=="R" and paused)
	controls.close()
	paused = false
	host.queue_free()
	recovery.queue_free()
	effects.queue_free()
	await frames()
	Bindings.reset_defaults()
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://u3-guide.cfg"))
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless viewport-dispatched keys with real Rama effects receiver. Transactional local preferences, group completeness, keyboard paging, pause and modal isolation; no OS/window or renderer claim.","sources":{}}
	for path in ["res://scripts/rama_hero_panel.gd","res://scripts/controls_overlay.gd","res://scripts/rama_hero_hud.gd","res://scripts/rama_ability_effects.gd","res://scripts/hero_ui_theme.gd","res://scripts/input_bindings.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	quit(0 if passed else 1)
