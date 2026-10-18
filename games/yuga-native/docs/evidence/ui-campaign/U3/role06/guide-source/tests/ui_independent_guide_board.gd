extends Control
## Isolated 2D evidence host. The guide and fonts are unmodified production files.
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var hero_panel: Control

func _ready() -> void:
	Bindings.install("user://independent-guide.cfg")
	name = "IndependentGuideHost"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var background := ColorRect.new()
	background.color = Color("11182b")
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	hero_panel = Guide.new()
	add_child(hero_panel)
	hero_panel.open.call_deferred("confluence")
