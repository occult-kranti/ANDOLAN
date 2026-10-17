extends RefCounted
## Shared native Rama interface. All interaction remains ordinary Godot controls.

const INK := Color("101c25")
const DEEP := Color("081119")
const GOLD := Color("e6bd72")
const CREAM := Color("f6ecda")
const MIST := Color("bdcbd2")
const MUTED := Color("8eaaaf")
const LINE := Color("40535c")

static func create() -> Theme:
	var result := Theme.new()
	result.default_font_size = 17
	for control in ["Label", "Button", "CheckButton", "CheckBox", "OptionButton"]:
		result.set_color("font_color", control, CREAM)
		result.set_color("font_hover_color", control, Color.WHITE)
		result.set_color("font_focus_color", control, CREAM)
		result.set_color("font_pressed_color", control, CREAM)
	for state in ["normal", "hover", "pressed", "disabled"]:
		var style := panel_style(false, 16)
		style.bg_color = Color("192c38") if state == "normal" else Color("294452")
		if state == "pressed": style.bg_color = Color("36535e")
		if state == "disabled": style.bg_color = Color("14222b")
		style.border_color = LINE if state == "normal" else GOLD.darkened(.3)
		style.content_margin_top = 10
		style.content_margin_bottom = 10
		result.set_stylebox(state, "Button", style)
	var focus := StyleBoxFlat.new()
	focus.bg_color = Color.TRANSPARENT
	focus.border_color = GOLD
	focus.set_border_width_all(2)
	focus.set_corner_radius_all(3)
	focus.expand_margin_left = 3
	focus.expand_margin_right = 3
	focus.expand_margin_top = 3
	focus.expand_margin_bottom = 3
	for control in ["Button", "CheckButton", "CheckBox", "HSlider", "OptionButton"]:
		result.set_stylebox("focus", control, focus)
	var separator := StyleBoxLine.new()
	separator.color = LINE
	separator.thickness = 1
	result.set_stylebox("separator", "HSeparator", separator)
	var track := StyleBoxFlat.new()
	track.bg_color = Color("425664")
	track.set_content_margin_all(3)
	track.set_corner_radius_all(3)
	result.set_stylebox("slider", "HSlider", track)
	var filled := track.duplicate()
	filled.bg_color = GOLD
	result.set_stylebox("grabber_area", "HSlider", filled)
	result.set_stylebox("grabber_area_highlight", "HSlider", filled)
	result.set_color("font_disabled_color", "Button", MUTED)
	result.set_constant("separation", "VBoxContainer", 12)
	return result

static func panel_style(strong: bool = false, padding: int = 20) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(.035, .066, .094, .97 if strong else .88)
	style.border_color = LINE
	style.set_border_width_all(1)
	style.set_corner_radius_all(4)
	style.set_content_margin_all(padding)
	return style

static func button(control: Button, primary: bool = false, quiet: bool = false) -> void:
	control.custom_minimum_size.y = 44
	control.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	control.focus_mode = Control.FOCUS_ALL
	if primary:
		for state in ["normal", "hover", "pressed"]:
			var style := panel_style(false, 16)
			style.bg_color = GOLD if state == "normal" else Color("f7d79f")
			if state == "pressed": style.bg_color = Color("caa460")
			style.border_color = style.bg_color
			style.content_margin_top = 12
			style.content_margin_bottom = 12
			control.add_theme_stylebox_override(state, style)
		for state in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
			control.add_theme_color_override(state, DEEP)
	elif quiet:
		var style := panel_style(false, 8)
		style.bg_color = Color.TRANSPARENT
		style.set_border_width_all(0)
		control.add_theme_stylebox_override("normal", style)

static func label(text: String, font_size: int = 17, color: Color = CREAM) -> Label:
	var result := Label.new()
	result.text = text
	result.add_theme_font_size_override("font_size", font_size)
	result.add_theme_color_override("font_color", color)
	result.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return result

static func display_font() -> SystemFont:
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Noto Serif", "Georgia", "DejaVu Serif", "serif"])
	font.font_weight = 500
	return font
