extends RefCounted
## Original tactical composition; shared bundled YUGA fonts and saved settings.
const Legacy = preload("res://scripts/hero_ui_theme.gd")
const SETTINGS_PATH := "user://tactical-settings.cfg"
const INK := Color("101723")
const SURFACE := Color("182433")
const IVORY := Color("f5efdf")
const MUTED := Color("a9b9c6")
const GOLD := Color("e5bd78")
const TEAL := Color("86d1c6")
const RED := Color("ef8b83")
const DEFAULTS := {"sensitivity":0.0025,"master_volume":0.8,"fov":90.0,"reduced_motion":false,"ui_scale":1.0}
static var current_scale := 1.0
const ABILITIES := [
	{"key":"Q","id":"veil","name":"Solar veil","detail":"Throw a veil seed to interrupt sightlines for 12 seconds. Carry up to two."},
	{"key":"E","id":"step","name":"Measured step","detail":"A short grounded dash. One charge refreshes each round."},
	{"key":"C","id":"wall","name":"Ward wall","detail":"Raise a wall for 10 seconds to reshape an approach. Carry one charge."},
	{"key":"X","id":"surge","name":"Dawn volley","detail":"Three piercing solar shots. Spend six points, earned from kills and objectives."}
]

static func sanitize_settings(values: Dictionary) -> Dictionary:
	var result := DEFAULTS.duplicate()
	for key in ["sensitivity","master_volume","fov","ui_scale"]:
		var value = values.get(key,result[key])
		if (value is float or value is int) and is_finite(float(value)): result[key]=float(value)
	result.sensitivity=clampf(result.sensitivity,.0005,.01)
	result.master_volume=clampf(result.master_volume,0,1)
	result.fov=clampf(result.fov,70,110)
	result.ui_scale=clampf(result.ui_scale,1,1.5)
	if values.get("reduced_motion") is bool: result.reduced_motion=values.reduced_motion
	return result

static func load_settings(path: String = SETTINGS_PATH) -> Dictionary:
	var config := ConfigFile.new()
	if config.load(path)!=OK: return DEFAULTS.duplicate()
	var values := {}
	for key in DEFAULTS: values[key]=config.get_value("player",key,DEFAULTS[key])
	return sanitize_settings(values)

static func save_settings(values: Dictionary, path: String = SETTINGS_PATH) -> Error:
	var config := ConfigFile.new()
	for key in sanitize_settings(values): config.set_value("player",key,sanitize_settings(values)[key])
	return config.save(path)

static func panel(color: Color = SURFACE, inset: int = 20, border: Color = Color.TRANSPARENT) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color=color
	style.set_content_margin_all(inset)
	style.border_color=border
	style.set_border_width_all(1 if border.a>0 else 0)
	style.corner_radius_top_left=2
	style.corner_radius_bottom_right=2
	return style

static func create(scale_: float = 1.0) -> Theme:
	current_scale=clampf(scale_,1,1.5)
	var value := Legacy.create()
	value.default_font_size=roundi(16*scale_)
	value.set_color("font_color","Label",IVORY)
	value.set_color("font_color","Button",IVORY)
	value.set_color("font_disabled_color","Button",Color("6d7c89"))
	value.set_stylebox("normal","Button",panel(Color("1d2b3a"),12,Color("435362")))
	value.set_stylebox("hover","Button",panel(Color("2b3e4c"),12,GOLD))
	value.set_stylebox("pressed","Button",panel(Color("334857"),12,TEAL))
	value.set_stylebox("disabled","Button",panel(Color("17212c"),12,Color("2d3b48")))
	var focus := panel(Color.TRANSPARENT,0,GOLD)
	focus.set_border_width_all(2)
	value.set_stylebox("focus","Button",focus)
	value.set_stylebox("panel","PanelContainer",panel())
	return value

static func label(text_: String, size_: int = 16, color: Color = IVORY, serif: bool = false) -> Label:
	var node := Label.new()
	node.text=text_
	node.set_meta("tactical_base_font_size",size_)
	node.add_theme_font_size_override("font_size",roundi(size_*current_scale))
	node.add_theme_color_override("font_color",color)
	if serif: node.add_theme_font_override("font",Legacy.display_font())
	return node

static func prose(text_: String, size_: int = 16, color: Color = MUTED) -> Label:
	var node := label(text_,size_,color)
	node.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	node.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	return node

static func button(text_: String, action: Callable, primary: bool = false) -> Button:
	var node := Button.new()
	node.text=text_
	node.custom_minimum_size.y=46
	node.set_meta("tactical_base_font_size",18)
	node.add_theme_font_size_override("font_size",roundi(18*current_scale))
	node.mouse_default_cursor_shape=Control.CURSOR_POINTING_HAND
	if primary:
		for state in ["normal","hover","pressed","hover_pressed"]:
			node.add_theme_stylebox_override(state,panel(Color("f1ce91") if state=="hover" else GOLD,12))
		for state in ["font_color","font_hover_color","font_pressed_color","font_hover_pressed_color","font_focus_color"]:node.add_theme_color_override(state,INK)
	node.pressed.connect(action)
	return node

static func quiet(button_: Button, selected: bool = false) -> void:
	var base:=panel(Color.TRANSPARENT,8)
	base.border_width_bottom=2 if selected else 0;base.border_color=GOLD
	button_.add_theme_stylebox_override("normal",base)
	button_.add_theme_stylebox_override("hover",panel(Color(.9,.8,.6,.08),8))
	button_.add_theme_stylebox_override("pressed",panel(Color(.9,.8,.6,.13),8))
	button_.add_theme_color_override("font_color",GOLD if selected else IVORY)

static func rescale(root: Node, scale_: float) -> void:
	current_scale=clampf(scale_,1,1.5)
	if root is Control and root.has_meta("tactical_base_font_size"):
		root.add_theme_font_size_override("font_size",roundi(float(root.get_meta("tactical_base_font_size"))*current_scale))
	for child in root.get_children():rescale(child,current_scale)

static func stack(separation: int = 12) -> VBoxContainer:
	var node := VBoxContainer.new()
	node.add_theme_constant_override("separation",separation)
	return node

static func row(separation: int = 12) -> HBoxContainer:
	var node := HBoxContainer.new()
	node.add_theme_constant_override("separation",separation)
	return node

static func icon(id: String, size_: int = 32) -> TextureRect:
	var node := TextureRect.new()
	var path := "res://assets/tactical/ui/"+id+".svg"
	if ResourceLoader.exists(path): node.texture=load(path)
	node.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	node.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	node.custom_minimum_size=Vector2(size_,size_)
	node.mouse_filter=Control.MOUSE_FILTER_IGNORE
	return node

static func settings_form(parent: VBoxContainer, values: Dictionary) -> Dictionary:
	var controls := {}
	for data in [["sensitivity","Aim sensitivity",.0005,.01,.0001],["master_volume","Master volume",0.0,1.0,.05],["fov","Field of view",70.0,110.0,1.0],["ui_scale","Interface scale",1.0,1.5,.1]]:
		var heading := row()
		var title := label(data[1]); title.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		heading.add_child(title)
		var number := label("",15,GOLD); heading.add_child(number); parent.add_child(heading)
		var slider := HSlider.new(); slider.min_value=data[2];slider.max_value=data[3];slider.step=data[4];slider.value=values[data[0]];slider.custom_minimum_size.y=28
		var update_number := func(v): number.text=("%.4f"%v if data[0]=="sensitivity" else ("%d%%"%roundi(v*100) if data[0] in ["master_volume","ui_scale"] else "%d°"%roundi(v)))
		slider.value_changed.connect(update_number);update_number.call(slider.value)
		parent.add_child(slider);controls[data[0]]=slider
	var reduced := CheckButton.new();reduced.text="Reduced motion";reduced.button_pressed=values.reduced_motion;reduced.custom_minimum_size.y=44;reduced.set_meta("tactical_base_font_size",16);reduced.add_theme_font_size_override("font_size",roundi(16*current_scale));parent.add_child(reduced);controls.reduced_motion=reduced
	return controls

static func settings_values(controls: Dictionary) -> Dictionary:
	var values := {}
	for key in controls: values[key]=controls[key].button_pressed if key=="reduced_motion" else controls[key].value
	return sanitize_settings(values)
