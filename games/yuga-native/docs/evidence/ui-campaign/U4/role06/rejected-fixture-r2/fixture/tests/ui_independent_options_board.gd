extends Control
## Production guide attached to an actual idle effect receiver; no cast or mesh.
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var hero_panel: Control
var effects: Node3D

func _ready() -> void:
	Bindings.install("user://independent-options.cfg")
	name = "IndependentOptionsHost"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var background := ColorRect.new()
	background.color = Color("11182b")
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	effects = Effects.new()
	add_child(effects)
	hero_panel = Guide.new()
	add_child(hero_panel)
	hero_panel.configure_effects(effects)
	hero_panel.open.call_deferred("confluence")

func independent_snapshot() -> Dictionary:
	var saved := ConfigFile.new()
	var status := saved.load(Bindings.config_path)
	var state: Dictionary = effects.report()
	return {
		"selected":hero_panel.selected_id,
		"ability_scroll":hero_panel.abilities_scroll.scroll_vertical,
		"detail_scroll":hero_panel.detail_scroll.scroll_vertical,
		"effects_enabled":not hero_panel.reduced_effects_button.disabled,
		"motion_enabled":not hero_panel.reduced_motion_button.disabled,
		"effects_checked":hero_panel.reduced_effects_button.button_pressed,
		"motion_checked":hero_panel.reduced_motion_button.button_pressed,
		"receiver_effects":state.reduced_effects,"receiver_motion":state.reduced_motion,
		"receiver_meshes":state.meshes,"receiver_casts":state.active,
		"save_status":status,"saved_effects":saved.get_value("rama_effects","reduced_effects",false),
		"saved_motion":saved.get_value("rama_effects","reduced_motion",false),
		"notice":hero_panel.effects_notice.text,
	}
