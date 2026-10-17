extends Control
## Shared modal. Callers own pause state; this panel owns keyboard capture and focus.
const Bindings = preload("res://scripts/input_bindings.gd")
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
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var shade := ColorRect.new()
	shade.color = Color(0.015,0.04,0.055,0.94)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	card = PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = Color("10282e")
	style.border_color = Color("e7c078")
	style.set_border_width_all(1)
	style.set_content_margin_all(20)
	card.add_theme_stylebox_override("panel",style)
	add_child(card)
	var theme_ := Theme.new()
	theme_.default_font_size = 18
	theme_.set_color("font_color","Label",Color("f1e6ce"))
	theme_.set_color("font_color","Button",Color("f1e6ce"))
	for state in ["normal","hover","pressed","focus"]:
		var button_style := StyleBoxFlat.new()
		button_style.bg_color = Color("20444a") if state != "normal" else Color("17343a")
		button_style.border_color = Color("e7c078") if state == "focus" else Color("537873")
		button_style.set_border_width_all(2 if state == "focus" else 1)
		button_style.content_margin_left = 14
		button_style.content_margin_right = 14
		theme_.set_stylebox(state,"Button",button_style)
	card.theme = theme_
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation",10)
	card.add_child(content)
	var title := Label.new()
	title.text = "Keyboard controls"
	title.add_theme_font_size_override("font_size",28)
	content.add_child(title)
	var intro := Label.new()
	intro.text = "Choose a control, then press a key. Esc cancels capture. Tab moves focus."
	intro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(intro)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.follow_focus = true
	content.add_child(scroll)
	var rows := VBoxContainer.new()
	rows.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rows.add_theme_constant_override("separation",7)
	scroll.add_child(rows)
	for action in Bindings.DEFAULTS:
		var row := HBoxContainer.new()
		rows.add_child(row)
		var label_ := Label.new()
		label_.text = Bindings.TITLES[action]
		label_.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(label_)
		var button := Button.new()
		button.custom_minimum_size = Vector2(120,42)
		button.pressed.connect(begin_capture.bind(action))
		row.add_child(button)
		binding_buttons[action] = button
		focus_order.append(button)
	var fixed := Label.new()
	fixed.text = "Fixed: LMB fire · arrows move · Esc pause/back · F2 help\nWorld: F1 overview · F5 respawn · N day/night"
	fixed.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fixed.add_theme_font_size_override("font_size",14)
	content.add_child(fixed)
	status = Label.new()
	status.custom_minimum_size.y = 42
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.add_theme_font_size_override("font_size",16)
	status.add_theme_color_override("font_color",Color("e7c078"))
	content.add_child(status)
	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation",10)
	content.add_child(footer)
	cancel_button = _button("Cancel capture",cancel_capture)
	reset_button = _button("Reset defaults",reset_bindings)
	done_button = _button("Done",close)
	for button in [cancel_button,reset_button,done_button]:
		footer.add_child(button)
		focus_order.append(button)
	_refresh()
	_layout()
	hide()

func _button(text: String,callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size.y = 44
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.pressed.connect(callback)
	return button

func _process(_delta: float) -> void:
	if visible: _layout()

func _layout() -> void:
	if not card: return
	var viewport := get_viewport_rect().size
	var target := Vector2(minf(680,viewport.x-32),minf(700,viewport.y-32))
	card.size = target
	card.position = (viewport-card.size)/2

func open() -> void:
	Bindings.release_gameplay()
	capture_action = ""
	_refresh()
	status.text = Bindings.load_notice if not Bindings.load_notice.is_empty() else "Choose a control to change it. Changes save immediately."
	show()
	_layout()
	binding_buttons.move_forward.grab_focus()

func close() -> void:
	cancel_capture()
	Bindings.release_gameplay()
	hide()
	closed.emit()

func _refresh() -> void:
	for action in binding_buttons:
		binding_buttons[action].text = "Press key…" if capture_action == action else Bindings.label(action)
	if cancel_button: cancel_button.disabled = capture_action.is_empty()

func begin_capture(action: String) -> void:
	if not binding_buttons.has(action): return
	Bindings.release_gameplay()
	capture_action = action
	status.text = "Press a new key for " + Bindings.TITLES[action] + ". Esc cancels."
	_refresh()
	binding_buttons[action].grab_focus()

func cancel_capture() -> void:
	var previous := capture_action
	capture_action = ""
	_refresh()
	if not previous.is_empty():
		status.text = "Capture cancelled; your existing key is unchanged."
		binding_buttons[previous].grab_focus()

func reset_bindings() -> void:
	cancel_capture()
	var result := Bindings.reset_defaults()
	status.text = result.message
	_refresh()
	if result.ok: bindings_changed.emit()

func _input(event: InputEvent) -> void:
	if not visible or not event is InputEventKey or not event.pressed or event.echo: return
	var key: int = event.physical_keycode if event.physical_keycode else event.keycode
	if not capture_action.is_empty():
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
	elif key == KEY_TAB:
		var available: Array[Control] = []
		for control in focus_order:
			if not control.disabled: available.append(control)
		var index := available.find(get_viewport().gui_get_focus_owner())
		available[posmod(index + (-1 if event.shift_pressed else 1),available.size())].grab_focus()
		get_viewport().set_input_as_handled()

func diagnostics() -> Dictionary:
	return {"visible":visible,"capture_action":capture_action,"status":status.text,"bindings":Bindings.current(),"card_rect":card.get_global_rect(),"viewport":get_viewport_rect(),"button_count":binding_buttons.size()}
