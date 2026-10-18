extends Control
## Shared modal. Callers own pause state; this panel owns keyboard capture and focus.
const Bindings = preload("res://scripts/input_bindings.gd")
const UI = preload("res://scripts/hero_ui_theme.gd")
const BINDING_GROUPS := [
	{"title":"Movement","actions":["move_forward","move_back","move_left","move_right","jump","sprint"]},
	{"title":"Flight and tether","actions":["fly","grapple","descend"]},
	{"title":"Bow and four abilities","actions":["reload","pulse","dash","guardian_circle","ultimate"]}
]
signal closed
signal bindings_changed
var capture_action := ""
var binding_buttons := {}
var status: Label
var card: PanelContainer
var done_button: Button
var cancel_button: Button
var reset_button: Button
var focus_order: Array[Control] = []

func _ready() -> void:
	name = "KeyboardControls"
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var shade := ColorRect.new()
	shade.color = Color(UI.DEEP,0.94)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	card = PanelContainer.new()
	card.name = "ControlsCard"
	card.theme = UI.create()
	add_child(card)
	var content := VBoxContainer.new()
	card.add_child(content)
	var title := Label.new()
	title.text = "Keyboard controls"
	title.theme_type_variation = &"YugaTitle"
	content.add_child(title)
	var intro := Label.new()
	intro.text = "Choose a control, then press a key. Esc cancels capture. Tab moves focus; PgUp / PgDn scroll."
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(intro)
	var scroll := ScrollContainer.new()
	scroll.name = "MappingsScroll"
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.follow_focus = true
	content.add_child(scroll)
	var rows := VBoxContainer.new()
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_theme_constant_override("separation",UI.SPACE_SM)
	scroll.add_child(rows)
	for group in BINDING_GROUPS:
		var heading := UI.label(group.title,UI.TYPE_CAPTION,UI.GOLD)
		heading.name = String(group.title).to_pascal_case()+"Heading"
		rows.add_child(heading)
		for action in group.actions: _binding_row(rows,action)
	rows.add_child(UI.label("Fixed controls",UI.TYPE_CAPTION,UI.GOLD))
	var fixed := Label.new()
	fixed.text = "%s fire · arrow keys move · %s pause / back\n%s help · %s abilities · %s restart\nWorld: %s overview · %s day / night" % [Bindings.label("fire"), Bindings.label("pause_game"), Bindings.label("help_controls"), Bindings.label("open_invocations"), Bindings.label("reset_training"), Bindings.label("world_overview"), Bindings.label("world_night")]
	fixed.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fixed.theme_type_variation = &"YugaCaption"
	rows.add_child(fixed)
	rows.add_child(UI.label("Sound and display",UI.TYPE_CAPTION,UI.GOLD))
	var preferences := UI.label("Settings on the title and training pause screens control sound, sensitivity, fullscreen and courtyard lighting. Confluence’s pause menu has sound volume. Rama’s guide has ability-effect preferences.",UI.TYPE_CAPTION,UI.MIST)
	preferences.name = "PreferencesLocation"
	preferences.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(preferences)
	status = Label.new()
	status.custom_minimum_size.y = UI.TARGET_MIN
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.add_theme_color_override("font_color",UI.GOLD)
	content.add_child(status)
	var footer := HBoxContainer.new()
	content.add_child(footer)
	cancel_button = _button("Cancel capture",cancel_capture)
	reset_button = _button("Reset defaults",reset_bindings)
	done_button = _button("Done",close)
	cancel_button.name = "CancelKeyCapture"
	reset_button.name = "ResetBindings"
	done_button.name = "DoneControls"
	UI.button_variant(cancel_button,&"utility")
	UI.button_variant(done_button,&"primary")
	for button in [cancel_button,reset_button,done_button]:
		footer.add_child(button)
		focus_order.append(button)
	_refresh()
	_layout()
	hide()

func _binding_row(parent: Control, action: String) -> void:
	var row := HBoxContainer.new()
	parent.add_child(row)
	var label_ := UI.label(Bindings.TITLES[action])
	label_.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label_.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	row.add_child(label_)
	var button := Button.new()
	button.name = "Binding_"+action
	button.custom_minimum_size = Vector2(140,UI.TARGET_MIN)
	UI.button_variant(button)
	button.pressed.connect(begin_capture.bind(action))
	row.add_child(button)
	binding_buttons[action] = button
	focus_order.append(button)

func _button(text: String,callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	UI.button_variant(button)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.pressed.connect(callback)
	return button

func _process(_delta: float) -> void:
	if not _accepts_input():
		if not capture_action.is_empty(): cancel_capture(false)
		return
	_layout()

func _notification(what: int) -> void:
	if what == NOTIFICATION_VISIBILITY_CHANGED and is_node_ready() and not is_visible_in_tree() and not capture_action.is_empty():
		cancel_capture(false)

func _accepts_input() -> bool:
	if not is_visible_in_tree(): return false
	# The modal runs while paused, but an explicitly disabled owner (for example
	# scene loading/recovery) must still be able to isolate its entire interface.
	var owner_node := get_parent()
	while owner_node:
		if owner_node.process_mode == Node.PROCESS_MODE_DISABLED: return false
		owner_node = owner_node.get_parent()
	return true

func _layout() -> void:
	if not card: return
	var viewport := get_viewport_rect().size
	var target := Vector2(minf(680,viewport.x-UI.SPACE_XL),minf(700,viewport.y-UI.SPACE_XL))
	card.size = target
	card.position = (viewport-card.size)/2

func open() -> void:
	Bindings.release_gameplay()
	capture_action = ""
	_refresh()
	status.text = Bindings.load_notice if not Bindings.load_notice.is_empty() else "Choose a control to change it. Changes save immediately."
	show()
	_layout()
	if _accepts_input(): binding_buttons.move_forward.grab_focus()

func close() -> void:
	if not visible: return
	cancel_capture(false)
	Bindings.release_gameplay()
	hide()
	closed.emit()

func _refresh() -> void:
	for action in binding_buttons:
		binding_buttons[action].text = "Press key…" if capture_action == action else Bindings.label(action)
	if cancel_button: cancel_button.disabled = capture_action.is_empty()

func begin_capture(action: String) -> void:
	if not _accepts_input() or not binding_buttons.has(action): return
	Bindings.release_gameplay()
	capture_action = action
	status.text = "Press a new key for " + Bindings.TITLES[action] + ". Esc cancels."
	_refresh()
	binding_buttons[action].grab_focus()

func cancel_capture(restore_focus: bool = true) -> void:
	var previous := capture_action
	capture_action = ""
	_refresh()
	if not previous.is_empty():
		status.text = "Capture cancelled; your existing key is unchanged."
		if restore_focus and _accepts_input(): binding_buttons[previous].grab_focus()

func reset_bindings() -> void:
	cancel_capture(false)
	var result := Bindings.reset_defaults()
	status.text = result.message
	_refresh()
	if result.ok: bindings_changed.emit()

func _input(event: InputEvent) -> void:
	if not _accepts_input() or not event is InputEventKey or not event.pressed or event.echo: return
	var key: int = event.physical_keycode if event.physical_keycode else event.keycode
	if key == KEY_TAB:
		_move_focus(event.shift_pressed)
		get_viewport().set_input_as_handled()
	elif key in [KEY_PAGEUP,KEY_PAGEDOWN,KEY_HOME,KEY_END]:
		var scroll: ScrollContainer = card.find_child("MappingsScroll",true,false)
		var step := maxi(1,int(scroll.size.y)-UI.SPACE_LG)
		if key == KEY_HOME: scroll.scroll_vertical = 0
		elif key == KEY_END: scroll.scroll_vertical = int(scroll.get_v_scroll_bar().max_value)
		else: scroll.scroll_vertical += step * (-1 if key == KEY_PAGEUP else 1)
		get_viewport().set_input_as_handled()
	elif not capture_action.is_empty():
		# Enter activates another focused mapping or footer action. Space remains
		# a valid captured key, and Esc always cancels the active capture first.
		var focused := get_viewport().gui_get_focus_owner()
		if key in [KEY_ENTER,KEY_KP_ENTER] and focused in focus_order and focused != binding_buttons[capture_action]: return
		if key == KEY_ESCAPE: cancel_capture()
		else:
			var action := capture_action
			var result := Bindings.set_binding(action,key)
			status.text = result.message
			if result.ok:
				capture_action = ""
				_refresh()
				bindings_changed.emit()
		get_viewport().set_input_as_handled()
	elif key == KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()

func _move_focus(backward: bool) -> void:
	var available: Array[Control] = []
	for control in focus_order:
		if is_instance_valid(control) and control.is_visible_in_tree() and not control.disabled: available.append(control)
	if available.is_empty(): return
	var index := available.find(get_viewport().gui_get_focus_owner())
	if index < 0:
		if backward: available.back().grab_focus()
		else: available.front().grab_focus()
	else:
		available[posmod(index + (-1 if backward else 1),available.size())].grab_focus()

func diagnostics() -> Dictionary:
	return {"visible":visible,"capture_action":capture_action,"status":status.text,"bindings":Bindings.current(),"card_rect":card.get_global_rect(),"viewport":get_viewport_rect(),"button_count":binding_buttons.size()}
