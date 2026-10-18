extends Control
## Tiny production-modal fixture. F8 is a capture-only display-scale hook.
const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const Controls = preload("res://scripts/controls_overlay.gd")
const Guide = preload("res://scripts/rama_hero_panel.gd")
class ResizeGate extends Node:
	func _input(event: InputEvent) -> void:
		if not event is InputEventKey or not event.pressed or event.echo: return
		var key: int = event.physical_keycode if event.physical_keycode else event.keycode
		if key == KEY_F8:
			get_window().content_scale_factor = 2.0 if get_window().content_scale_factor == 1.0 else 1.0
			get_viewport().set_input_as_handled()
var controls_overlay: Control
var rama_panel: Control
var controls_opener: Button
var guide_opener: Button
var page_title := "Modal resize fixture"
func _ready() -> void:
	name = "ModalResizeBoard"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme=UI.create()
	Bindings.install("user://modal-resize-visual.cfg")
	var bg := ColorRect.new()
	bg.color=UI.DEEP;bg.mouse_filter=Control.MOUSE_FILTER_IGNORE
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);add_child(bg)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);add_child(center)
	var stack := VBoxContainer.new();center.add_child(stack)
	stack.add_child(UI.label("Modal resize fixture",UI.TYPE_SECTION))
	stack.add_child(UI.label("F8 changes fixture scale. No world or hero is loaded.",UI.TYPE_CAPTION))
	controls_opener=_button(stack,"OpenKeyboard","Keyboard controls")
	guide_opener=_button(stack,"OpenGuide","Rama’s abilities")
	controls_overlay=Controls.new();add_child(controls_overlay)
	rama_panel=Guide.new();add_child(rama_panel)
	controls_opener.pressed.connect(func():page_title="controls";controls_overlay.open())
	guide_opener.pressed.connect(func():page_title="guide";rama_panel.open("courtyard",guide_opener))
	controls_overlay.closed.connect(func():page_title="board";controls_opener.grab_focus())
	rama_panel.closed.connect(func():page_title="board")
	controls_opener.grab_focus()
	_install_resize_gate.call_deferred()
func _install_resize_gate() -> void:
	# _input visits later root nodes first, before remap capture sees the key.
	var gate := ResizeGate.new()
	gate.name="FixtureResizeInputGate"
	gate.process_mode=Node.PROCESS_MODE_ALWAYS
	get_tree().root.add_child(gate)
func _button(parent: Node, id: String, text: String) -> Button:
	var button := Button.new();button.name=id;button.text=text
	UI.button(button,true);parent.add_child(button)
	return button
func fixture_report() -> Dictionary:
	var focus := get_viewport().gui_get_focus_owner()
	var scroll: ScrollContainer
	if controls_overlay.is_visible_in_tree():scroll=controls_overlay.card.find_child("MappingsScroll",true,false)
	elif rama_panel.is_visible_in_tree() and is_instance_valid(focus):scroll=rama_panel.abilities_scroll if rama_panel.abilities_scroll.is_ancestor_of(focus) else rama_panel.details_scroll
	var target := focus.get_global_rect() if is_instance_valid(focus) else Rect2()
	var clip := scroll.get_global_rect() if is_instance_valid(scroll) else Rect2()
	return {"scope":"Production 2D modals with native keyboard route; F8 is fixture-only scale change, not a shipping shortcut.","scale":get_window().content_scale_factor,"focus_name":str(focus.name) if is_instance_valid(focus) else "","target":[target.position.x,target.position.y,target.size.x,target.size.y],"scroll_clip":[clip.position.x,clip.position.y,clip.size.x,clip.size.y],"focused_control_in_scroll":is_instance_valid(scroll) and is_instance_valid(focus) and scroll.is_ancestor_of(focus) and clip.encloses(target),"capture_action":controls_overlay.capture_action,"capture_status":controls_overlay.status.text,"selected_id":rama_panel.selected_id,"logical_viewport":str(get_viewport_rect())}
