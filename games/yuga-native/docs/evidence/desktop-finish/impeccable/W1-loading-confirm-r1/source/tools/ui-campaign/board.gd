extends Control
## Visual fixture only. Keys 1/2/3 hold declared sample phases, not loading timings.
## Keys 4/5 begin real missing-resource/error or queued-cancel controller attempts.
const UI = preload("res://scripts/hero_ui_theme.gd")
const Transition = preload("res://scripts/scene_transition.gd")
var loader: Control
var open_button: Button
var page_title := "Loading visual fixture"
var phase := &"idle"
var held_sample := false

func _ready() -> void:
	name = "LoadingVisualBoard"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = UI.create()
	var background := ColorRect.new()
	background.color = UI.DEEP
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var stack := VBoxContainer.new()
	center.add_child(stack)
	stack.add_child(UI.label("Loading visual fixture", UI.TYPE_SECTION))
	stack.add_child(UI.label("1 / 2 / 3: held phase samples. 4: missing scene. 5 then Escape: cancel."))
	open_button = Button.new()
	open_button.name = "OpenMissingScene"
	open_button.text = "Open missing local scene"
	UI.button(open_button, true)
	open_button.pressed.connect(_real_attempt.bind(&"confluence"))
	stack.add_child(open_button)
	_mount_loader.call_deferred()

func _mount_loader() -> void:
	loader = Transition.ensure_for_tree(get_tree())
	loader.phase_changed.connect(_phase_changed)
	open_button.grab_focus()

func _input(event: InputEvent) -> void:
	if not is_instance_valid(loader): return
	if not event is InputEventKey or not event.pressed or event.echo: return
	var key: int = event.physical_keycode if event.physical_keycode != 0 else event.keycode
	if key in [KEY_1,KEY_2,KEY_3]:
		_hold_sample([&"queued",&"loading",&"constructing"][key-KEY_1])
	elif key == KEY_4:
		_real_attempt(&"confluence")
	elif key == KEY_5:
		_real_attempt(&"courtyard")
	else: return
	get_viewport().set_input_as_handled()

func _clear_sample() -> void:
	if held_sample:
		held_sample = false
		loader.cancel()
	loader.set_process(true)

func _hold_sample(next: StringName) -> void:
	_clear_sample()
	held_sample = true
	if not loader.begin(&"courtyard", null, open_button):
		held_sample = false
		return
	loader.set_process(false)
	var messages := {&"queued":"Preparing to load…",&"loading":"Loading scene resources…",&"constructing":"Preparing the scene… This step may take a moment."}
	loader._set_phase(next,messages[next],.475 if next == &"loading" else -1.0)
	page_title = "sample-" + str(next)

func _real_attempt(destination: StringName) -> void:
	_clear_sample()
	loader.begin(destination,self,open_button)

func _phase_changed(next: StringName, _message: String, _progress: float) -> void:
	phase = next
	if not held_sample: page_title = "controller-" + str(next)

func fixture_report() -> Dictionary:
	var view: Control = loader.get_node("LoadingPresentation")
	var rows := {}
	for key in ["heading","detail","progress_bar","progress_scope","back_button","retry_button"]:
		var control: Control = view.get(key)
		var rect := control.get_global_rect()
		var inside := control.is_visible_in_tree() and get_viewport().get_visible_rect().encloses(rect)
		var ancestor := control.get_parent()
		while ancestor != null:
			if ancestor is Control and (ancestor is ScrollContainer or ancestor.clip_contents):
				inside = inside and ancestor.get_global_rect().encloses(rect)
			ancestor = ancestor.get_parent()
		rows[key] = {"visible":control.is_visible_in_tree(),"inside_ancestor_clips":inside,"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y]}
	return {"scope":"Held visual phases use sample .475 only, not native resource timing. Error/retry/back/cancel use the production controller.","held_sample":held_sample,"phase":str(loader.phase),"resource_progress":loader.resource_progress,"logical_size":str(size),"controls":rows}
