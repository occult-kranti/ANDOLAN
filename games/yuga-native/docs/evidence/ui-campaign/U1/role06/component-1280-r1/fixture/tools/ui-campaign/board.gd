extends Control
## Component fixture only. Uses production controls, without world/portrait assets.
## Missing allowlisted Confluence file produces a genuine resource-availability error.
const Shell = preload("res://scripts/launch_shell.gd")
const Transition = preload("res://scripts/scene_transition.gd")
var shell: Control
var loader: Control
func _ready() -> void:
	name = "UIComponentBoard"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var background := ColorRect.new()
	background.color = Color("11182b")
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	shell = Shell.new()
	add_child(shell)
	loader = Transition.new()
	loader.name = "SceneTransition"
	get_tree().root.add_child.call_deferred(loader)
	shell.world_requested.connect(_launch)
	shell.train_requested.connect(_launch)
	shell.focus_primary.call_deferred()
func _launch() -> void:
	loader.begin(&"confluence", self, shell.primary_button)
