extends RefCounted
## YUGA's shared indigo, ivory and beaten-gold interface.
## Native control semantics remain responsible for input and disabled behavior.

const DEEP := Color("0c1222")
const INK := Color("172039")
const SURFACE := Color("202c49")
const HOVER := Color("2b3a5b")
const PRESSED := Color("354562")
const GOLD := Color("e2bb70")
const GOLD_HOVER := Color("f5d69b")
const GOLD_PRESSED := Color("cba45f")
const CREAM := Color("f6eddc")
const MIST := Color("ccd3e1")
const MUTED := Color("adb8d0")
const LINE := Color("7280a3")
const SPACE_XS := 4
const SPACE_SM := 8
const SPACE_MD := 12
const SPACE_LG := 20
const SPACE_XL := 32
const TYPE_DISPLAY := 64
const TYPE_TITLE := 32
const TYPE_SECTION := 22
const TYPE_BODY := 17
const TYPE_CAPTION := 14
const TARGET_MIN := 44
const FOCUS_WIDTH := 2
const CORNER := 3
const BUTTON_TYPES := {&"primary": &"YugaPrimaryButton", &"secondary": &"Button", &"utility": &"YugaUtilityButton", &"selected": &"YugaSelectedButton"}
const BUTTON_STATES := ["normal", "hover", "pressed", "hover_pressed", "disabled"]

static func create() -> Theme:
	var result := Theme.new()
	result.default_font = text_font()
	result.default_font_size = TYPE_BODY
	result.set_color("font_color", "Label", CREAM)
	for control in ["Button", "OptionButton", "CheckButton", "CheckBox"]:
		_set_button_theme(result, control, &"secondary")
	for variant in [&"primary", &"utility", &"selected"]:
		var type: StringName = BUTTON_TYPES[variant]
		result.set_type_variation(type, &"Button")
		_set_button_theme(result, type, variant)
	for role in ["YugaDisplay", "YugaTitle", "YugaSection", "YugaCaption", "YugaEyebrow"]:
		result.set_type_variation(role, "Label")
	var sizes := {"YugaDisplay": TYPE_DISPLAY, "YugaTitle": TYPE_TITLE, "YugaSection": TYPE_SECTION, "YugaCaption": TYPE_CAPTION, "YugaEyebrow": TYPE_CAPTION}
	for role in sizes:
		result.set_font_size("font_size", role, sizes[role])
	for role in ["YugaDisplay", "YugaTitle"]:
		result.set_font("font", role, display_font())
	result.set_color("font_color", "YugaCaption", MIST)
	result.set_color("font_color", "YugaEyebrow", GOLD)
	for container in ["VBoxContainer", "HBoxContainer", "GridContainer"]:
		result.set_constant("separation", container, SPACE_MD)
	result.set_constant("h_separation", "GridContainer", SPACE_MD)
	result.set_constant("v_separation", "GridContainer", SPACE_MD)
	result.set_stylebox("panel", "PanelContainer", panel_style())
	var separator := StyleBoxLine.new()
	separator.color = LINE
	separator.thickness = 1
	result.set_stylebox("separator", "HSeparator", separator)
	_set_choice_controls(result)
	_set_sliders(result)
	_set_scrollbars(result)
	return result

## Convenience alias for standalone UI modules; create() remains the original API.
static func build() -> Theme:
	return create()

static func panel_style(strong: bool = false, padding: int = SPACE_LG) -> StyleBoxFlat:
	var style := _surface(DEEP if strong else INK, LINE, padding, padding)
	return style

static func button(control: Button, primary: bool = false, quiet: bool = false) -> void:
	button_variant(control, &"primary" if primary else (&"utility" if quiet else &"secondary"))

## Explicit roles also work without a themed parent and can be safely changed in place.
static func button_variant(control: Button, variant: StringName = &"secondary") -> void:
	if not BUTTON_TYPES.has(variant): variant = &"secondary"
	control.theme_type_variation = BUTTON_TYPES[variant]
	control.custom_minimum_size.y = maxf(control.custom_minimum_size.y, TARGET_MIN)
	control.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	control.focus_mode = Control.FOCUS_ALL
	for state in BUTTON_STATES:
		control.add_theme_stylebox_override(state, _button_style(variant, state))
	control.add_theme_stylebox_override("focus", _focus())
	for name in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		control.add_theme_color_override(name, DEEP if variant == &"primary" else CREAM)
	control.add_theme_color_override("font_disabled_color", MUTED)

static func label(text: String, font_size: int = TYPE_BODY, color: Color = CREAM) -> Label:
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

static func text_font() -> SystemFont:
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["Noto Sans", "DejaVu Sans", "sans-serif"])
	return font

static func _surface(fill: Color, border: Color, horizontal: int, vertical: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(CORNER)
	style.content_margin_left = horizontal
	style.content_margin_right = horizontal
	style.content_margin_top = vertical
	style.content_margin_bottom = vertical
	return style

static func _button_style(variant: StringName, state: String) -> StyleBoxFlat:
	var fill := SURFACE
	var border := LINE
	if state == "hover": fill = HOVER
	if state in ["pressed", "hover_pressed"]: fill = PRESSED
	if variant == &"primary":
		fill = GOLD
		if state == "hover": fill = GOLD_HOVER
		if state in ["pressed", "hover_pressed"]: fill = GOLD_PRESSED
		border = fill
	elif variant == &"utility":
		if state == "normal": fill = DEEP
		border = fill
	elif variant == &"selected":
		border = GOLD
		if state == "normal": fill = HOVER
	if state == "disabled":
		fill = INK
		border = LINE
	var style := _surface(fill, border, SPACE_LG, SPACE_MD)
	if variant == &"selected" and state != "disabled": style.border_width_left = SPACE_XS
	return style

static func _focus() -> StyleBoxFlat:
	var style := _surface(Color.TRANSPARENT, GOLD, 0, 0)
	style.draw_center = false
	style.set_border_width_all(FOCUS_WIDTH)
	# A dark moat keeps the gold ring visible beside the gold primary surface.
	style.shadow_color = DEEP
	style.shadow_size = FOCUS_WIDTH
	style.set_expand_margin_all(SPACE_XS)
	return style

static func _set_button_theme(theme: Theme, type: StringName, variant: StringName) -> void:
	for state in BUTTON_STATES:
		theme.set_stylebox(state, type, _button_style(variant, state))
	for name in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		theme.set_color(name, type, DEEP if variant == &"primary" else CREAM)
	theme.set_color("font_disabled_color", type, MUTED)
	theme.set_color("icon_disabled_color", type, MUTED)
	theme.set_constant("h_separation", type, SPACE_MD)
	theme.set_stylebox("focus", type, _focus())

static func _set_choice_controls(theme: Theme) -> void:
	for state in ["normal", "hover", "pressed", "disabled"]:
		var regular: StyleBoxFlat = theme.get_stylebox(state, "OptionButton")
		regular.content_margin_right = SPACE_XL + SPACE_SM
		var mirrored := regular.duplicate() as StyleBoxFlat
		mirrored.content_margin_left = regular.content_margin_right
		mirrored.content_margin_right = SPACE_LG
		theme.set_stylebox(state + "_mirrored", "OptionButton", mirrored)
	theme.set_icon("arrow", "OptionButton", _icon('<path d="m5 7 5 5 5-5" fill="none" stroke="#ffffff" stroke-width="2"/>', 20, 20))
	theme.set_constant("modulate_arrow", "OptionButton", 1)
	theme.set_constant("arrow_margin", "OptionButton", SPACE_MD)
	for disabled in [false, true]:
		for checked in [false, true]:
			for mirrored in [false, true]:
				var key := ("checked" if checked else "unchecked") + ("_disabled" if disabled else "") + ("_mirrored" if mirrored else "")
				theme.set_icon(key, "CheckButton", _toggle(checked, disabled, mirrored))
			var key := ("checked" if checked else "unchecked") + ("_disabled" if disabled else "")
			var body := '<rect x="2" y="2" width="20" height="20" rx="2" fill="#%s" stroke="#%s" stroke-width="2"/>' % [INK.to_html(false), (MUTED if disabled else GOLD).to_html(false)]
			if checked: body += '<path d="m6 12 4 4 8-9" fill="none" stroke="#%s" stroke-width="2"/>' % (MUTED if disabled else CREAM).to_html(false)
			theme.set_icon(key, "CheckBox", _icon(body, 24, 24))
	# The opened native option list must share the same surface and readable states.
	theme.set_stylebox("panel", "PopupMenu", panel_style(true, SPACE_SM))
	theme.set_stylebox("hover", "PopupMenu", _surface(HOVER, GOLD, SPACE_MD, SPACE_SM))
	theme.set_color("font_color", "PopupMenu", CREAM)
	theme.set_color("font_hover_color", "PopupMenu", CREAM)
	theme.set_color("font_disabled_color", "PopupMenu", MUTED)
	theme.set_constant("v_separation", "PopupMenu", SPACE_MD)

static func _toggle(checked: bool, disabled: bool, mirrored: bool) -> Texture2D:
	var knob_right := checked != mirrored
	var accent := MUTED if disabled else GOLD
	var body := '<rect x="2" y="3" width="38" height="20" rx="10" fill="#%s" stroke="#%s" stroke-width="2"/>' % [DEEP.to_html(false), accent.to_html(false)]
	body += '<circle cx="%d" cy="13" r="7" fill="#%s"/>' % [30 if knob_right else 12, (MUTED if disabled else CREAM).to_html(false)]
	if checked: body += '<path d="m%s 13 2 2 4-5" fill="none" stroke="#%s" stroke-width="2"/>' % ["8" if knob_right else "26", accent.to_html(false)]
	return _icon(body, 44, 26)

static func _set_sliders(theme: Theme) -> void:
	for type in ["HSlider", "VSlider"]:
		var track := _surface(LINE, LINE, 3, 3)
		track.set_border_width_all(0)
		theme.set_stylebox("slider", type, track)
		for state in ["grabber_area", "grabber_area_highlight"]:
			var filled := track.duplicate() as StyleBoxFlat
			filled.bg_color = GOLD
			theme.set_stylebox(state, type, filled)
		# Godot uses grabber_highlight for keyboard focus as well as hover;
		# Slider has no native focus StyleBox. The separate 2px ring is intentional.
		for state in ["grabber", "grabber_highlight", "grabber_disabled"]:
			var color := MUTED if state == "grabber_disabled" else CREAM
			var body := '<circle cx="12" cy="12" r="8" fill="#%s" stroke="#%s" stroke-width="2"/>' % [color.to_html(false), DEEP.to_html(false)]
			if state == "grabber_highlight": body = '<circle cx="12" cy="12" r="11" fill="#%s" stroke="#%s" stroke-width="2"/>' % [DEEP.to_html(false), GOLD.to_html(false)] + body
			theme.set_icon(state, type, _icon(body, 24, 24))
		theme.set_constant("grabber_offset", type, 0)

static func _set_scrollbars(theme: Theme) -> void:
	theme.set_stylebox("panel", "ScrollContainer", StyleBoxEmpty.new())
	theme.set_stylebox("focus", "ScrollContainer", _focus())
	for type in ["HScrollBar", "VScrollBar"]:
		theme.set_stylebox("scroll", type, _surface(DEEP, LINE, SPACE_SM, SPACE_SM))
		var focused := _surface(DEEP, GOLD, SPACE_SM, SPACE_SM)
		focused.set_border_width_all(FOCUS_WIDTH)
		theme.set_stylebox("scroll_focus", type, focused)
		for state in ["grabber", "grabber_highlight", "grabber_pressed"]:
			theme.set_stylebox(state, type, _surface(GOLD if state != "grabber" else MIST, DEEP, SPACE_SM, SPACE_SM))
		# ScrollBar has no disabled state. Native scrolling remains its input owner.

static func _icon(body: String, width: int, height: int) -> Texture2D:
	var image := Image.new()
	var svg := '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>' % [width, height, width, height, body]
	image.load_svg_from_string(svg)
	return ImageTexture.create_from_image(image)
