extends VBoxContainer
## A read-only field briefing for the two actual practices. Never owns navigation,
## combat values or focus. Small/scaled windows retain the launcher's description.

const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const Glyph = preload("res://scripts/rama_ability_glyph.gd")
const ACTIONS := ["fire", "pulse", "dash", "guardian_circle", "ultimate"]
const ABILITIES := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
const NAMES := ["Kodanda", "Piercing Dawn", "Measured Step", "Guardian Circle", "Dawn Volley"]

var mode := "world"
var first_move: Label
var field_label: Label
var key_labels: Array[Label] = []
var diagram: FieldDiagram

class FieldDiagram extends Control:
	var mode := "world"
	func _draw() -> void:
		var center := size * .5
		if mode == "train":
			for radius in [24.0, 16.0, 7.0]:
				draw_arc(center, radius, 0, TAU, 48, UI.GOLD if radius == 7.0 else UI.LINE, 1.5, true)
			draw_line(center + Vector2(-29, 0), center + Vector2(29, 0), UI.MUTED, 1.0, true)
			draw_line(center + Vector2(0, -29), center + Vector2(0, 29), UI.MUTED, 1.0, true)
		else:
			for column in [16.0, 36.0, 56.0]:
				draw_line(Vector2(column, 12), Vector2(column, 54), UI.LINE, 1.5, true)
				draw_circle(Vector2(column, 12), 3.0, UI.MOON, true)
				draw_circle(Vector2(column, 54), 3.0, UI.GOLD, true)
				draw_circle(Vector2(column, 33), 4.0, UI.GOLD, false, 1.5, true)
			draw_line(Vector2(16, 54), Vector2(56, 54), UI.GOLD, 1.5, true)
			draw_line(Vector2(16, 12), Vector2(56, 12), UI.MOON, 1.5, true)

func _ready() -> void:
	name = "FieldBriefing"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_mode = Control.FOCUS_NONE
	add_theme_constant_override("separation", UI.SPACE_SM)
	var field := HBoxContainer.new()
	field.add_theme_constant_override("separation", UI.SPACE_MD)
	add_child(field)
	diagram = FieldDiagram.new()
	diagram.custom_minimum_size = Vector2(72, 64)
	diagram.mouse_filter = Control.MOUSE_FILTER_IGNORE
	field.add_child(diagram)
	var copy := VBoxContainer.new()
	copy.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	copy.add_theme_constant_override("separation", UI.SPACE_XS)
	field.add_child(copy)
	field_label = UI.label("", UI.TYPE_CAPTION, UI.GOLD)
	field_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	copy.add_child(field_label)
	first_move = UI.label("", UI.TYPE_BODY, UI.MIST)
	first_move.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	copy.add_child(first_move)
	var keys := HBoxContainer.new()
	keys.add_theme_constant_override("separation", UI.SPACE_SM)
	keys.name = "RamaBindings"
	copy.add_child(keys)
	for index in ACTIONS.size():
		var slot := HBoxContainer.new()
		slot.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		slot.add_theme_constant_override("separation", 6)
		slot.tooltip_text = NAMES[index]
		keys.add_child(slot)
		var glyph := Glyph.new()
		slot.add_child(glyph)
		glyph.present(ABILITIES[index], &"selected")
		var key := UI.label("", UI.TYPE_CAPTION, UI.CREAM)
		key.name = ACTIONS[index]
		slot.add_child(key)
		key_labels.append(key)
	refresh(mode)

func refresh(selected_mode: String) -> void:
	mode = selected_mode if selected_mode in ["world", "train"] else "world"
	if not is_instance_valid(first_move): return
	field_label.text = "THREE LANES / RELAYS" if mode == "world" else "COURTYARD / TARGETS"
	first_move.text = "Follow a wave; hold relays for arrows." if mode == "world" else "Move, draw, release. Try each ability."
	diagram.mode = mode
	diagram.queue_redraw()
	for index in ACTIONS.size():
		key_labels[index].text = Bindings.label(ACTIONS[index])
		key_labels[index].tooltip_text = NAMES[index] + " · " + key_labels[index].text

func snapshot() -> Dictionary:
	var keys := {}
	for index in key_labels.size(): keys[ACTIONS[index]] = key_labels[index].text
	return {"mode": mode, "visible": is_visible_in_tree(), "first_move": first_move.text if is_instance_valid(first_move) else "", "bindings": keys, "schematic": true}
