extends SceneTree
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Controls = preload("res://scripts/controls_overlay.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const UI = preload("res://scripts/hero_ui_theme.gd")
var checks: Array[Dictionary] = []
var output := ""
var settings := "user://u4-preferences.cfg"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func frames() -> void:
	for unused in range(6): await process_frame

func press(code: int) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode=code;event.physical_keycode=code;event.pressed=down
		root.push_input(event)
		await process_frame

func _run() -> void:
	Bindings.install(settings)
	Bindings.merge_settings({"audio":{"volume":.3},"video":{"fullscreen":false},"rama_effects":{"reduced_effects":true,"reduced_motion":true}},settings)
	var effects := Effects.new()
	root.add_child(effects)
	var guide := Guide.new()
	root.add_child(guide)
	guide.configure_effects(effects)
	root.size=Vector2i(960,540);root.content_scale_size=root.size
	guide.open()
	await frames()
	var bow: Label = guide._list.get_node("BowHeading")
	record("Compact initial focus retains Bow heading and selected button",guide.abilities_scroll.get_global_rect().encloses(bow.get_global_rect()) and guide.abilities_scroll.get_global_rect().encloses(guide.ability_buttons.kodanda.get_global_rect()) and root.gui_get_focus_owner()==guide.ability_buttons.kodanda,{"scroll":guide.abilities_scroll.scroll_vertical,"heading":str(bow.get_global_rect())})
	guide.close()
	Bindings.merge_settings({"rama_effects":{"reduced_effects":false,"reduced_motion":"invalid boolean"}},settings)
	guide.open()
	record("Invalid typed preference rejects the pair without silently changing active effects",effects.report().reduced_effects and effects.report().reduced_motion and guide.effects_notice.text.contains("Invalid"))
	guide.close()
	var corrupt := "[rama_effects]\nreduced_effects = Object(\"Node\")\n"
	var file := FileAccess.open(settings,FileAccess.WRITE)
	file.store_string(corrupt);file.close()
	guide.open()
	record("Unsupported settings bytes preserve current effects with visible error",effects.report().reduced_motion and guide.effects_notice.text.contains("Could not read") and guide.effects_notice.get_theme_color("font_color")==UI.GOLD)
	guide.reduced_motion_button.grab_focus()
	await press(KEY_ENTER)
	record("Failed option write preserves corrupt bytes and active value",FileAccess.get_file_as_string(settings)==corrupt and guide.reduced_motion_button.button_pressed and effects.report().reduced_motion and guide.effects_notice.text.contains("Could not save"))
	guide.close()
	var controls := Controls.new()
	root.add_child(controls)
	controls.open()
	await frames()
	controls.reset_button.grab_focus()
	await press(KEY_ENTER)
	var backups := []
	for name in DirAccess.get_files_at("user://"):
		if name.begins_with("u4-preferences.cfg.invalid-") and name.ends_with(".bak"): backups.append(name)
	record("Explicit corrupt reset preserves original bytes in one backup",backups.size()==1 and FileAccess.get_file_as_string("user://"+backups[0])==corrupt and Bindings.current()==Bindings.DEFAULTS and root.gui_get_focus_owner()==controls.reset_button)
	var before := FileAccess.get_sha256(settings)
	var cycles_ok := true
	for unused in range(8):
		controls.begin_capture("reload")
		await press(KEY_W)
		cycles_ok = cycles_ok and controls.capture_action=="reload" and controls.status.text.contains("already assigned")
		await press(KEY_ESCAPE)
		cycles_ok = cycles_ok and controls.visible and controls.capture_action.is_empty() and Bindings.label("reload")=="R"
	record("Repeated conflicts and cancellations never save or close the modal",cycles_ok and FileAccess.get_sha256(settings)==before)
	controls.close()
	guide.open()
	record("Reopening after explicit reset loads actual default effect values",not effects.report().reduced_motion and not effects.report().reduced_effects and not guide.reduced_motion_button.button_pressed and guide.effects_notice.get_theme_color("font_color")==UI.MIST)
	guide.reduced_effects_button.grab_focus()
	await press(KEY_ENTER)
	guide.close()
	Bindings.merge_settings({"audio":{"volume":.3},"video":{"fullscreen":false}},settings)
	Bindings.set_binding("reload",KEY_T)
	controls.open()
	controls.reset_bindings()
	var config: ConfigFile = Bindings.read_config(settings).config
	record("Normal key reset preserves real sound display and effect preferences",Bindings.label("reload")=="R" and config.get_value("rama_effects","reduced_effects",false) and config.get_value("audio","volume",0)==.3 and config.get_value("video","fullscreen",true)==false)
	controls.close()
	guide.open()
	effects.queue_free()
	await frames()
	record("Disposed effect owner retires capability instead of offering dead controls",guide.reduced_effects_button.disabled and guide.reduced_motion_button.disabled and guide.effects_notice.text.contains("unavailable"))
	guide.close()
	guide.queue_free();controls.queue_free()
	await frames()
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless native input with actual effect receiver and isolated user settings. Explicit typed/unsupported corruption, rollback, backup reset, repeated conflict/cancel, compact initial focus and disposed capability. No renderer/OS input claim.","sources":{}}
	for path in ["res://scripts/rama_hero_panel.gd","res://scripts/controls_overlay.gd","res://scripts/input_bindings.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]: report.sources[path]=FileAccess.get_sha256(path)
	if not output.is_empty():
		var result := FileAccess.open(output,FileAccess.WRITE)
		if result: result.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed=false
	quit(0 if passed else 1)
