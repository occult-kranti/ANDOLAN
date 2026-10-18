extends SceneTree
## Native resource/input checks; rendered focus and layout remain capture-lane gates.
const UI = preload("res://scripts/hero_ui_theme.gd")
var checks: Array[Dictionary] = []
var report_path := ""
var activations := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name": label, "passed": passed, "details": details})
	print("PASS " if passed else "FAIL ", label)

func _linear(value: float) -> float:
	return value / 12.92 if value <= 0.04045 else pow((value + 0.055) / 1.055, 2.4)

func _luminance(color: Color) -> float:
	return 0.2126 * _linear(color.r) + 0.7152 * _linear(color.g) + 0.0722 * _linear(color.b)

func _contrast(a: Color, b: Color) -> float:
	var light := _luminance(a)
	var dark := _luminance(b)
	return (maxf(light, dark) + 0.05) / (minf(light, dark) + 0.05)

func _check_focus(label: String, focus: StyleBoxFlat, backgrounds: Array[Color]) -> void:
	var wide_enough := true
	for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
		wide_enough = wide_enough and focus.get_border_width(side) >= 2
	_record(label + " focus has all four 2px sides", wide_enough)
	var inside := true
	for size in [Vector2(44, 44), Vector2(240, 48), Vector2(438, 54)]:
		var bounds := Rect2(Vector2.ZERO, size)
		var draw_bounds := bounds.grow_individual(focus.expand_margin_left, focus.expand_margin_top, focus.expand_margin_right, focus.expand_margin_bottom)
		inside = inside and bounds.encloses(draw_bounds) and draw_bounds.position.x >= 2 and draw_bounds.position.y >= 2
	_record(label + " focus stays inset within clipping bounds", inside and focus.shadow_size == 0)
	var ratio := INF
	for background in backgrounds: ratio = minf(ratio, _contrast(focus.border_color, background))
	_record(label + " focus contrasts with every surface", ratio >= 3.0, {"focus_ratio": ratio})

func _key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	await process_frame

func _run() -> void:
	var theme := UI.create()
	for type in ["Button", "OptionButton", "CheckButton", "CheckBox", "YugaPrimaryButton", "YugaUtilityButton", "YugaSelectedButton"]:
		var active_backgrounds: Array[Color] = []
		for pair in [["normal", "font_color"], ["hover", "font_hover_color"], ["pressed", "font_pressed_color"], ["disabled", "font_disabled_color"]]:
			var style := theme.get_stylebox(pair[0], type) as StyleBoxFlat
			var ratio := _contrast(theme.get_color(pair[1], type), style.bg_color)
			_record(type + " " + pair[0] + " readable at 4.5:1", style.bg_color.a == 1.0 and ratio >= 4.5, {"ratio": ratio})
			active_backgrounds.append(style.bg_color)
		var focus := theme.get_stylebox("focus", type) as StyleBoxFlat
		_check_focus(type, focus, active_backgrounds)
	for type in ["HSlider", "VSlider"]:
		var normal := theme.get_icon("grabber", type).get_image()
		var focus := theme.get_icon("grabber_highlight", type).get_image()
		var disabled := theme.get_icon("grabber_disabled", type).get_image()
		_record(type + " native focus icon has distinct 2px ring", focus.get_size() == normal.get_size() and focus.get_pixel(12, 1).a > 0.9 and focus.get_pixel(12, 2).a > 0.9 and normal.get_pixel(12, 1).a == 0)
		_record(type + " disabled thumb remains readable and distinct", _contrast(disabled.get_pixel(12, 12), UI.DEEP) >= 3.0 and disabled.get_pixel(12, 12) != normal.get_pixel(12, 12))
	for type in ["HScrollBar", "VScrollBar"]:
		var focus := theme.get_stylebox("scroll_focus", type) as StyleBoxFlat
		_record(type + " native focused track has visible border", focus.border_width_left >= 2 and _contrast(focus.border_color, focus.bg_color) >= 3.0)
		for state in ["grabber", "grabber_highlight", "grabber_pressed"]:
			var thumb := theme.get_stylebox(state, type) as StyleBoxFlat
			_record(type + " " + state + " identifies scrolling position", _contrast(thumb.bg_color, UI.DEEP) >= 3.0)
	for state in ["normal", "hover", "pressed", "disabled"]:
		var regular := theme.get_stylebox(state, "OptionButton") as StyleBoxFlat
		var mirrored := theme.get_stylebox(state + "_mirrored", "OptionButton") as StyleBoxFlat
		_record("OptionButton " + state + " reserves arrow space in both directions", regular.content_margin_right >= 32 and mirrored.content_margin_left == regular.content_margin_right and mirrored.content_margin_right == regular.content_margin_left)
	for disabled in [false, true]:
		var suffix := "_disabled" if disabled else ""
		var off := theme.get_icon("unchecked" + suffix, "CheckButton").get_image()
		var on := theme.get_icon("checked" + suffix, "CheckButton").get_image()
		_record("Toggle " + suffix + " changes knob position beyond color", off.get_pixel(12, 13) != on.get_pixel(12, 13) and off.get_pixel(30, 13) != on.get_pixel(30, 13))
	var other_theme := UI.create()
	var first := theme.get_stylebox("normal", "Button") as StyleBoxFlat
	var second := other_theme.get_stylebox("normal", "Button") as StyleBoxFlat
	first.bg_color = Color.MAGENTA
	_record("Independent screens cannot mutate each other's theme", second.bg_color != first.bg_color)
	var surface := Control.new()
	surface.theme = other_theme
	root.add_child(surface)
	var primary := Button.new()
	primary.text = "Enter Confluence"
	primary.position = Vector2(20, 20)
	surface.add_child(primary)
	UI.button(primary, true)
	var peer := Button.new()
	surface.add_child(peer)
	UI.button(peer, true)
	var primary_style := primary.get_theme_stylebox("normal") as StyleBoxFlat
	primary_style.bg_color = Color.MAGENTA
	_record("Button state styles are privately owned", (peer.get_theme_stylebox("normal") as StyleBoxFlat).bg_color != primary_style.bg_color)
	UI.button_variant(primary, &"utility")
	_record("Changing primary to utility clears old text/surface overrides", primary.get_theme_color("font_color") == UI.CREAM and (primary.get_theme_stylebox("normal") as StyleBoxFlat).bg_color == UI.DEEP)
	for variant in [&"primary", &"secondary", &"utility", &"selected"]:
		UI.button_variant(primary, variant)
		var backgrounds: Array[Color] = []
		for state in ["normal", "hover", "pressed", "hover_pressed", "disabled"]:
			backgrounds.append((primary.get_theme_stylebox(state) as StyleBoxFlat).bg_color)
		_check_focus("Reassigned " + variant, primary.get_theme_stylebox("focus") as StyleBoxFlat, backgrounds)
	UI.button_variant(primary, &"primary")
	primary.size = Vector2(240, 44)
	primary.pressed.connect(func(): activations += 1)
	await process_frame
	_record("Primary action retains minimum 44px and keyboard focus", primary.get_combined_minimum_size().y >= 44 and primary.focus_mode == Control.FOCUS_ALL)
	primary.grab_focus()
	await _key(KEY_SPACE, true)
	await _key(KEY_SPACE, false)
	_record("Native primary accepts keyboard activation", activations == 1)
	primary.disabled = true
	var disabled_focus := primary.get_theme_stylebox("focus") as StyleBoxFlat
	var disabled_surface := primary.get_theme_stylebox("disabled") as StyleBoxFlat
	_record("Disabled primary retains visible keyboard focus", primary.has_focus() and _contrast(disabled_focus.border_color, disabled_surface.bg_color) >= 3.0)
	await _key(KEY_SPACE, true)
	await _key(KEY_SPACE, false)
	_record("Native disabled primary rejects keyboard activation", activations == 1)
	var slider := HSlider.new()
	slider.position = Vector2(20, 100)
	slider.size = Vector2(240, 44)
	slider.value = 50
	surface.add_child(slider)
	slider.grab_focus()
	await _key(KEY_RIGHT, true)
	await _key(KEY_RIGHT, false)
	_record("Native slider keyboard operation is preserved", slider.value > 50)
	slider.editable = false
	var before := slider.value
	await _key(KEY_RIGHT, true)
	await _key(KEY_RIGHT, false)
	_record("Native disabled slider rejects changes", slider.value == before)
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed": passed, "checks": checks, "scope": "Headless native theme resources, contrast and keyboard state ownership; no rendering, screen-reader or integrated layout acceptance.", "sources": {}}
	for path in ["res://scripts/hero_ui_theme.gd", get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not report_path.is_empty():
		var file := FileAccess.open(report_path, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report, "\t") + "\n")
		else: passed = false
	surface.queue_free()
	await process_frame
	quit(0 if passed else 1)
