extends Control
## Read-only Rama ability guide. Selection here never spends resources or casts.

const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const KIT_PATH := "res://assets/design/rama-ability-kit.json"

signal closed

var card: PanelContainer
var close_button: Button
var ability_buttons: Dictionary = {}
var detail_title: Label
var detail_description: Label
var detail_timing: Label
var detail_range: Label
var detail_context: Label
var key_label: Label
var status_label: Label
var focus_order: Array[Control] = []
var selected_id := "kodanda"
var context := "confluence"
var _actions := {"kodanda":"fire", "piercing_dawn":"pulse", "measured_step":"dash", "guardian_circle":"guardian_circle", "dawn_volley":"ultimate"}
var _rules: Dictionary = {}
var _return_focus: WeakRef
var _split: HBoxContainer
var _list: VBoxContainer
var _last_size := Vector2.ZERO

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UI.create()
	name = "RamaHeroPanel"
	_build()
	_load_kit()
	_layout()
	hide()

func set_action_map(actions: Dictionary) -> void:
	for id in _actions:
		if actions.get(id) is String: _actions[id] = actions[id]
	if card: refresh_bindings()

func _build() -> void:
	var shade := ColorRect.new()
	shade.color = Color(.01, .02, .035, .8)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	card = PanelContainer.new()
	card.name = "Card"
	card.add_theme_stylebox_override("panel", UI.panel_style(true, 24))
	add_child(card)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 16)
	card.add_child(stack)
	var header := HBoxContainer.new()
	stack.add_child(header)
	var heading := VBoxContainer.new()
	heading.add_theme_constant_override("separation", 2)
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(heading)
	heading.add_child(UI.label("RAMA’S ABILITIES", 13, UI.GOLD))
	var title := UI.label("The solar archer", 32)
	title.add_theme_font_override("font", UI.display_font())
	heading.add_child(title)
	status_label = UI.label("Offline practice", 14, UI.MIST)
	status_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	header.add_child(status_label)
	stack.add_child(HSeparator.new())
	_split = HBoxContainer.new()
	_split.add_theme_constant_override("separation", 28)
	_split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	stack.add_child(_split)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 10)
	_list.custom_minimum_size.x = 236
	_split.add_child(_list)
	var scroll := ScrollContainer.new()
	scroll.name = "DetailsScroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.follow_focus = true
	_split.add_child(scroll)
	var detail := VBoxContainer.new()
	detail.add_theme_constant_override("separation", 16)
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(detail)
	key_label = UI.label("LMB  /  PRIMARY", 13, UI.GOLD)
	detail.add_child(key_label)
	detail_title = UI.label("Kodanda", 29)
	detail_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail.add_child(detail_title)
	detail_description = _wrapped("", 18, UI.CREAM)
	detail.add_child(detail_description)
	detail.add_child(HSeparator.new())
	detail_timing = _wrapped("", 15, UI.MIST)
	detail.add_child(detail_timing)
	detail_range = _wrapped("", 15, UI.MIST)
	detail.add_child(detail_range)
	detail_context = _wrapped("", 14, UI.MIST)
	detail.add_child(detail_context)
	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 20)
	stack.add_child(footer)
	var note := _wrapped("Choose an ability to see its use and timing.\nEsc or F3 returns to your previous screen.", 13, UI.MIST)
	note.custom_minimum_size.x = 280
	note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(note)
	close_button = Button.new()
	close_button.name = "Back"
	close_button.text = "Back"
	close_button.custom_minimum_size.x = 140
	UI.button(close_button, true)
	close_button.pressed.connect(close)
	footer.add_child(close_button)

func _load_kit() -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string(KIT_PATH)) if FileAccess.file_exists(KIT_PATH) else null
	if not data is Dictionary or not data.get("abilities") is Array:
		detail_description.text = "Rama’s ability details are unavailable in this build."
		return
	for ability in data.abilities:
		if not ability is Dictionary or not _actions.has(ability.get("id")): continue
		_rules[ability.id] = ability
		var button := Button.new()
		button.name = ability.id
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.custom_minimum_size.y = 48
		UI.button(button)
		button.add_theme_font_size_override("font_size", 16)
		button.pressed.connect(func(): select_ability(ability.id))
		_list.add_child(button)
		ability_buttons[ability.id] = button
		focus_order.append(button)
	focus_order.append(close_button)
	refresh_bindings()
	select_ability(selected_id)

func _wrapped(text: String, font_size: int, color: Color) -> Label:
	var label := UI.label(text, font_size, color)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return label

func refresh_bindings() -> void:
	for id in ability_buttons:
		ability_buttons[id].text = "%s   %s" % [_binding(id), _rules[id].label]
	if _rules.has(selected_id): select_ability(selected_id)

func _binding(id: String) -> String:
	var action: String = _actions.get(id, "")
	if action == "fire": return "LMB"
	return Bindings.label(action) if InputMap.has_action(action) else str(_rules.get(id, {}).get("key", "—"))

func select_ability(id: String) -> void:
	if not _rules.has(id): return
	selected_id = id
	var rule: Dictionary = _rules[id]
	key_label.text = "%s  /  %s" % [_binding(id), "PRIMARY" if id == "kodanda" else ("ULTIMATE" if id == "dawn_volley" else "ABILITY")]
	detail_title.text = rule.label
	detail_description.text = rule.description
	detail_timing.text = "Cooldown  %s s\nDraw / preparation  %s s" % [_number(rule.get("cooldown_s", 0)), _number(rule.get("windup_s", 0))]
	detail_range.text = "Range  %s m" % _number(rule.get("range_m", 0))
	if id == "guardian_circle": detail_range.text += "  ·  Radius  %s m" % _number(rule.get("radius_m", 0))
	detail_context.text = "Use the bow, movement and abilities against the courtyard targets." if context == "courtyard" else "Aim into Confluence’s lanes. Abilities resolve against troops and solid cover."
	for ability_id in ability_buttons:
		var button: Button = ability_buttons[ability_id]
		var style := UI.panel_style(false, 12)
		style.bg_color = Color("2c4654") if ability_id == id else Color("13232d")
		style.border_color = UI.GOLD if ability_id == id else UI.LINE
		style.border_width_left = 3 if ability_id == id else 1
		style.content_margin_top = 11
		style.content_margin_bottom = 11
		button.add_theme_stylebox_override("normal", style)

func _number(value: Variant) -> String:
	return ("%.2f" % float(value)).trim_suffix("0").trim_suffix(".0")

func open(screen_context: String = "confluence", return_focus: Control = null) -> void:
	context = screen_context
	_return_focus = weakref(return_focus) if is_instance_valid(return_focus) else null
	status_label.text = "Bow training" if context == "courtyard" else "Confluence practice"
	Bindings.release_gameplay()
	refresh_bindings()
	show()
	_layout()
	if ability_buttons.has(selected_id): ability_buttons[selected_id].grab_focus()
	else: close_button.grab_focus()

func close() -> void:
	if not visible: return
	hide()
	Bindings.release_gameplay()
	closed.emit()
	var previous = _return_focus.get_ref() if _return_focus else null
	if is_instance_valid(previous) and previous.is_visible_in_tree(): previous.grab_focus()

func _input(event: InputEvent) -> void:
	if not visible: return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode in [KEY_ESCAPE, KEY_F3]:
			close()
			get_viewport().set_input_as_handled()
		elif event.keycode in [KEY_TAB, KEY_UP, KEY_DOWN]:
			var direction := -1 if (event.keycode == KEY_UP or (event.keycode == KEY_TAB and event.shift_pressed)) else 1
			var current := focus_order.find(get_viewport().gui_get_focus_owner())
			focus_order[posmod(current + direction, focus_order.size())].grab_focus()
			get_viewport().set_input_as_handled()

func _process(_delta: float) -> void:
	if not visible: return
	var viewport := get_viewport_rect().size
	# Wrapped labels settle after the first container sort. Reapply the bounded
	# card rectangle when an earlier zero-width minimum briefly made it taller.
	if _last_size != viewport or card.size.y > minf(520, viewport.y - 48) or card.size.x > minf(920, viewport.x - 48): _layout()

func _layout() -> void:
	if not card: return
	_last_size = get_viewport_rect().size
	card.size = Vector2(minf(920, _last_size.x - 48), minf(520, _last_size.y - 48))
	card.position = (_last_size - card.size) * .5
	_list.custom_minimum_size.x = 236 if _last_size.x >= 1100 else 214
	_split.add_theme_constant_override("separation", 28 if _last_size.x >= 1100 else 20)
