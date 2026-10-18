extends Control
## Explicit tiny two-page fixture. It uses production loader/theme and real local scenes.
const UI = preload("res://scripts/hero_ui_theme.gd")
const Transition = preload("res://scripts/scene_transition.gd")
@export var page_title := "Sample A"
var loader: Control
var open_button: Button

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = UI.create()
	var background := ColorRect.new()
	background.color = UI.DEEP
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size.x = 520
	center.add_child(panel)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation",20)
	panel.add_child(stack)
	stack.add_child(UI.label("YUGA · loading fixture",32,UI.GOLD))
	stack.add_child(UI.label(page_title,22))
	stack.add_child(UI.label("Two local 2D scenes. No world or hero is loaded.",14))
	open_button = _button(stack,"OpenLocalSample","Open other local sample")
	open_button.pressed.connect(func():loader.begin(&"confluence" if page_title=="Sample A" else &"courtyard",self,open_button))
	var missing := _button(stack,"OpenMissingSample","Open unavailable sample")
	missing.pressed.connect(func():loader.begin(&"combat_film",self,missing))
	var pause := _button(stack,"PauseFixture","Pause fixture")
	pause.toggle_mode = true
	pause.button_pressed = get_tree().paused
	pause.toggled.connect(func(value: bool):get_tree().paused=value)
	loader = Transition.ensure_for_tree(get_tree())
	open_button.grab_focus()

func _button(parent: Node, id: String, text: String) -> Button:
	var button := Button.new()
	button.name = id
	button.text = text
	UI.button(button,id=="OpenLocalSample")
	parent.add_child(button)
	return button
