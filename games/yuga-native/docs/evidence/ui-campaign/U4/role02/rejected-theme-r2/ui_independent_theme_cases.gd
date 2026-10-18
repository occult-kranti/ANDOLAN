extends SceneTree
## Adversarial native theme checks for state transitions omitted by the baseline.
const UI = preload("res://scripts/hero_ui_theme.gd")
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func frames(count := 3) -> void:
	for unused in count: await process_frame

func run() -> void:
	root.size = Vector2i(960,540)
	root.content_scale_size = root.size
	root.gui_embed_subwindows = true
	var before := FileAccess.get_sha256("res://scripts/hero_ui_theme.gd")
	var theme := UI.create()
	for state in ["normal","hover","pressed","hover_pressed","disabled"]:
		var regular := theme.get_stylebox(state,"OptionButton") as StyleBoxFlat
		var mirror_exists := theme.has_stylebox(state+"_mirrored","OptionButton")
		var mirrored := theme.get_stylebox(state+"_mirrored","OptionButton") as StyleBoxFlat if mirror_exists else null
		record("Option "+state+" reserves arrow space in either text direction",mirror_exists and regular.content_margin_right>=UI.SPACE_XL+UI.SPACE_SM and mirrored.content_margin_left==regular.content_margin_right and mirrored.content_margin_right==regular.content_margin_left,{"regular_left":regular.content_margin_left,"regular_right":regular.content_margin_right,"mirrored_exists":mirror_exists})
	var host := Control.new()
	host.theme = theme
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(host)
	var option := OptionButton.new()
	option.position = Vector2(20,20)
	option.size = Vector2(400,48)
	option.add_item("Fullscreen — high contrast display")
	option.add_item("Windowed")
	host.add_child(option)
	await frames()
	var at := option.get_global_rect().get_center()
	var motion := InputEventMouseMotion.new()
	motion.position = at
	Input.parse_input_event(motion)
	for down in [true,false]:
		var mouse := InputEventMouseButton.new()
		mouse.position = at
		mouse.button_index = MOUSE_BUTTON_LEFT
		mouse.pressed = down
		Input.parse_input_event(mouse)
		await frames()
	record("Native option opens its actual popup",option.get_popup().visible,{"draw_mode":option.get_draw_mode(),"pressed":option.button_pressed})
	option.get_popup().hide()
	await frames()
	var primary := Button.new()
	primary.text = "Primary"
	primary.position = Vector2(20,100)
	primary.size = Vector2(240,48)
	host.add_child(primary)
	UI.button(primary,true)
	primary.grab_focus()
	primary.disabled = true
	await frames()
	var focus := primary.get_theme_stylebox("focus") as StyleBoxFlat
	record("Disabling the focused primary retains an inset dark indicator",primary.has_focus() and focus.border_color==UI.DEEP and focus.expand_margin_left<=-2 and focus.expand_margin_right<=-2)
	primary.disabled = false
	UI.button_variant(primary,&"selected")
	await frames()
	record("Changing focused primary to selected replaces every state including hover_pressed",primary.get_theme_stylebox("hover_pressed").bg_color==UI.PRESSED and primary.get_theme_color("font_hover_pressed_color")==UI.CREAM and primary.get_theme_stylebox("focus").border_color==UI.GOLD)
	var after := FileAccess.get_sha256("res://scripts/hero_ui_theme.gd")
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"theme_sha256":before,"source_unchanged":before==after,"test_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Independent native state transitions and full OptionButton directional state metrics. Popup shown through viewport mouse press/release. Actual pixels are separate; no3D or hardware claim."}
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	host.queue_free()
	await frames()
	quit(0 if result.passed else 1)
