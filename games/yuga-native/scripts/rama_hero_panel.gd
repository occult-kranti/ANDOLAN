extends Control
## Read-only Rama ability guide. Selection here never spends resources or casts.

const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const Glyph = preload("res://scripts/rama_ability_glyph.gd")
const ScrollFocus = preload("res://scripts/ui_scroll_focus.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
const KIT_PATH := "res://assets/design/rama-ability-kit.json"
const TACTICS := {
	"kodanda": ["CONTROL THE GAP", "Use cover between draws and keep the next target in view.", "Solid cover stops the arrow. Move across the archer's aim rather than toward it.", "Use Measured Step to change your angle, then draw again."],
	"piercing_dawn": ["BREAK A FORMATION", "Line up a troop column before committing to the longer draw.", "Break the firing line behind solid cover; piercing does not pass through walls.", "Reposition with Measured Step after recovery to avoid returning fire."],
	"measured_step": ["KEEP YOUR SIGHTLINE", "Choose a movement direction to reach nearby cover while keeping your aim.", "The step gives no invulnerability. Cover shortens the route.", "Create a new angle before Piercing Dawn or Dawn Volley locks your aim."],
	"guardian_circle": ["HOLD GROUND TOGETHER", "Place the fixed circle where you and allied troops can stay inside it.", "Healing requires staying inside the fixed circle; an existing shield lasts until expiry. Solid cover blocks placement.", "Protect a lane position, then draw while your allies advance."],
	"dawn_volley": ["COMMIT THREE LANES", "Aim before casting: all three firing lanes lock when the draw begins.", "Move sideways during the warning or use solid cover; every arrow stops at its first target.", "Use Measured Step first to open an angle. Three marks during the cast show pending and launched lanes, not charges or hits."]
}

signal closed

var card: PanelContainer
var close_button: Button
var ability_buttons: Dictionary = {}
var detail_title: Label
var detail_glyph: TextureRect
var detail_description: Label
var detail_timing: Label
var detail_range: Label
var detail_context: Label
var detail_power: Label
var detail_tactics: Label
var key_label: Label
var status_label: Label
var effects_notice: Label
var reduced_effects_button: CheckButton
var reduced_motion_button: CheckButton
var details_scroll: ScrollContainer
var abilities_scroll: ScrollContainer
var focus_order: Array[Control] = []
var selected_id := "kodanda"
var context := "confluence"
var _actions := {"kodanda":"fire", "piercing_dawn":"pulse", "measured_step":"dash", "guardian_circle":"guardian_circle", "dawn_volley":"ultimate"}
var _rules: Dictionary = {}
var _return_focus: WeakRef
var _split: HBoxContainer
var _list: VBoxContainer
var _last_size := Vector2.ZERO
var _effects_receiver: WeakRef
var _effects_options := {"reduced_effects":false,"reduced_motion":false}
var _reveal_pending := false
var _feedback_revision := 0
var profile_label: Label
var hero_identity_label: Label
var _profile_box: VBoxContainer
var practice_heading: Label
var practice_label: Label
var _practice_report_provider := Callable()
var _practice_clock := 0.0

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
	shade.color = Color(UI.DEEP, .94)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	card = PanelContainer.new()
	card.name = "Card"
	card.add_theme_stylebox_override("panel", UI.panel_style(true, UI.SPACE_LG))
	add_child(card)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", UI.SPACE_MD)
	card.add_child(stack)
	var header := HBoxContainer.new()
	stack.add_child(header)
	var heading := VBoxContainer.new()
	heading.add_theme_constant_override("separation", 2)
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(heading)
	hero_identity_label = UI.label("RAMA · BOW + FOUR ABILITIES", UI.TYPE_CAPTION, UI.GOLD)
	hero_identity_label.clip_text = true
	hero_identity_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	heading.add_child(hero_identity_label)
	var title := UI.label("The solar archer", UI.TYPE_TITLE)
	title.add_theme_font_override("font", UI.display_font())
	heading.add_child(title)
	status_label = UI.label("Offline practice", 14, UI.MIST)
	status_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	header.add_child(status_label)
	stack.add_child(HSeparator.new())
	_split = HBoxContainer.new()
	_split.add_theme_constant_override("separation", UI.SPACE_LG)
	_split.size_flags_vertical = Control.SIZE_EXPAND_FILL
	stack.add_child(_split)
	abilities_scroll = ScrollContainer.new()
	abilities_scroll.name = "AbilitiesScroll"
	abilities_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	abilities_scroll.follow_focus = true
	_split.add_child(abilities_scroll)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", UI.SPACE_SM)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	abilities_scroll.add_child(_list)
	details_scroll = ScrollContainer.new()
	details_scroll.name = "DetailsScroll"
	details_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	details_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details_scroll.follow_focus = true
	_split.add_child(details_scroll)
	var detail := VBoxContainer.new()
	detail.add_theme_constant_override("separation", UI.SPACE_MD)
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details_scroll.add_child(detail)
	var ability_heading := HBoxContainer.new()
	ability_heading.add_theme_constant_override("separation", UI.SPACE_MD)
	detail.add_child(ability_heading)
	detail_glyph = Glyph.new()
	detail_glyph.name = "SelectedAbilityGlyph"
	detail_glyph.custom_minimum_size = Vector2(48, 48)
	detail_glyph.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	ability_heading.add_child(detail_glyph)
	var title_stack := VBoxContainer.new()
	title_stack.add_theme_constant_override("separation", UI.SPACE_XS)
	title_stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ability_heading.add_child(title_stack)
	key_label = UI.label("LMB  /  PRIMARY", UI.TYPE_CAPTION, UI.GOLD)
	title_stack.add_child(key_label)
	detail_title = UI.label("Kodanda", 29)
	detail_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title_stack.add_child(detail_title)
	detail_description = _wrapped("", 18, UI.CREAM)
	detail.add_child(detail_description)
	detail_power = _wrapped("", UI.TYPE_CAPTION, UI.GOLD)
	detail_power.name = "AbilityOutput"
	detail.add_child(detail_power)
	detail.add_child(HSeparator.new())
	detail_timing = _wrapped("", 15, UI.MIST)
	detail.add_child(detail_timing)
	detail_range = _wrapped("", 15, UI.MIST)
	detail.add_child(detail_range)
	detail_context = _wrapped("", 14, UI.MIST)
	detail.add_child(detail_context)
	detail.add_child(HSeparator.new())
	detail_tactics = _wrapped("", UI.TYPE_BODY, UI.CREAM)
	detail_tactics.name = "TacticalGuide"
	detail.add_child(detail_tactics)
	detail.add_child(HSeparator.new())
	detail.add_child(UI.label("Ability effects", UI.TYPE_BODY, UI.GOLD))
	for item in [{"key":"reduced_effects","text":"Fewer decorative layers"},{"key":"reduced_motion","text":"Still ornamental motion"}]:
		var toggle := CheckButton.new()
		toggle.name = item.key
		toggle.text = item.text
		toggle.custom_minimum_size.y = UI.TARGET_MIN
		toggle.disabled = true
		toggle.toggled.connect(_change_effect_option.bind(item.key))
		detail.add_child(toggle)
		if item.key == "reduced_effects": reduced_effects_button = toggle
		else: reduced_motion_button = toggle
	effects_notice = _wrapped("Ability effects settings are unavailable in this view.", UI.TYPE_CAPTION, UI.MIST)
	detail.add_child(effects_notice)
	_profile_box = VBoxContainer.new()
	_profile_box.name = "HeroProfileAndPractice"
	_profile_box.add_theme_constant_override("separation", UI.SPACE_SM)
	_profile_box.add_child(HSeparator.new())
	_profile_box.add_child(UI.label("HERO PROFILE", UI.TYPE_CAPTION, UI.GOLD))
	profile_label = _wrapped("", UI.TYPE_CAPTION, UI.CREAM)
	profile_label.name = "HeroProfile"
	_profile_box.add_child(profile_label)
	practice_heading = _wrapped("CURRENT TRAINING ATTEMPT", UI.TYPE_CAPTION, UI.GOLD)
	practice_heading.name = "PracticeRecordHeading"
	_profile_box.add_child(practice_heading)
	practice_label = _wrapped("", UI.TYPE_CAPTION, UI.CREAM)
	practice_label.name = "PracticeRecord"
	_profile_box.add_child(practice_label)
	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", UI.SPACE_LG)
	stack.add_child(footer)
	var note := _wrapped("PgUp / PgDn: details · Shift: profile\n%s or %s returns to your previous screen." % [Bindings.label("pause_game"),Bindings.label("open_invocations")], 13, UI.MIST)
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
		if ability.id in ["kodanda","piercing_dawn"]:
			var group := UI.label("Bow" if ability.id == "kodanda" else "Four abilities", UI.TYPE_CAPTION, UI.MIST)
			group.name = "BowHeading" if ability.id == "kodanda" else "AbilitiesHeading"
			_list.add_child(group)
		_rules[ability.id] = ability
		var button := Button.new()
		button.name = ability.id
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.custom_minimum_size.y = UI.TARGET_MIN
		UI.button(button)
		button.add_theme_font_size_override("font_size", 16)
		button.icon = Glyph.texture_for(ability.id)
		button.expand_icon = true
		button.add_theme_constant_override("icon_max_width", Glyph.GUIDE_SIZE)
		button.add_theme_constant_override("h_separation", UI.SPACE_SM)
		button.pressed.connect(func(): select_ability(ability.id))
		_list.add_child(button)
		ability_buttons[ability.id] = button
		focus_order.append(button)
	_list.add_child(_profile_box)
	focus_order.append_array([reduced_effects_button,reduced_motion_button,close_button])
	refresh_bindings()
	select_ability(selected_id)
	_refresh_profile()

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
	if action == "fire": return Bindings.label(action)
	return Bindings.label(action) if InputMap.has_action(action) else str(_rules.get(id, {}).get("key", "—"))

func select_ability(id: String) -> void:
	_feedback_revision += 1
	if not _rules.has(id): return
	selected_id = id
	detail_glyph.present(id, &"selected")
	var rule: Dictionary = _rules[id]
	key_label.text = "%s  /  %s" % [_binding(id), "PRIMARY" if id == "kodanda" else ("ULTIMATE" if id == "dawn_volley" else "ABILITY")]
	detail_title.text = rule.label
	detail_description.text = rule.description
	if id == "guardian_circle":
		detail_power.text = "%s shield on entry · %s healing / s" % [_number(rule.shield), _number(rule.heal_per_s)]
	elif id == "measured_step":
		detail_power.text = "%s m step · %s s movement · No invulnerability" % [_number(rule.range_m), _number(rule.movement_s)]
	else:
		detail_power.text = "%s damage / arrow · %s" % [_number(rule.damage), ("Up to %s enemies" % _number(rule.max_hits)) if int(rule.max_hits) > 1 else "First target only"]
		if id == "dawn_volley": detail_power.text += " · 3 paced arrows"
	var tactic: Array = TACTICS.get(id, [])
	detail_tactics.text = "%s\n\nUSE  %s\n\nCOUNTER  %s\n\nFOLLOW-UP  %s" % tactic if tactic.size() == 4 else ""
	detail_timing.text = "Cooldown  %s s\nDraw / preparation  %s s\nRecovery  %s s" % [_number(rule.get("cooldown_s", 0)), _number(rule.get("windup_s", 0)), _number(rule.get("recovery_s", 0))]
	if rule.has("active_s"): detail_timing.text += "\nDuration  %s s" % _number(rule.active_s)
	detail_range.text = "Range  %s m" % _number(rule.get("range_m", 0))
	if id == "guardian_circle": detail_range.text += "  ·  Radius  %s m" % _number(rule.get("radius_m", 0))
	detail_context.text = "Use the bow, movement and abilities against the courtyard targets." if context == "courtyard" else "Aim into Confluence’s lanes. Abilities resolve against troops and solid cover."
	for ability_id in ability_buttons:
		var button: Button = ability_buttons[ability_id]
		UI.button_variant(button,&"selected" if ability_id == id else &"secondary")
		for color_name in ["icon_normal_color", "icon_hover_color", "icon_pressed_color", "icon_focus_color"]:
			button.add_theme_color_override(color_name, Glyph.color_for(&"selected" if ability_id == id else &"unavailable"))
	details_scroll.scroll_vertical = 0
	_refresh_profile()

func configure_effects(receiver: Node) -> void:
	_effects_receiver = weakref(receiver) if is_instance_valid(receiver) and receiver.has_method("set_options") else null
	_load_effect_options()

func _effect_receiver() -> Node:
	return _effects_receiver.get_ref() if _effects_receiver else null

func _load_effect_options() -> void:
	var receiver := _effect_receiver()
	for toggle in [reduced_effects_button,reduced_motion_button]: toggle.disabled = not is_instance_valid(receiver)
	if not is_instance_valid(receiver):
		_effect_notice("Ability effects settings are unavailable in this view.")
		return
	var result := Bindings.read_config(Bindings.config_path)
	if not result.ok:
		_effect_notice("Could not read effect preferences. Current ability effects are unchanged.",true)
	else:
		var candidate := {}
		for key in _effects_options:
			var value: Variant = result.config.get_value("rama_effects",key,false)
			if not value is bool:
				_effect_notice("Invalid effect preference. Current ability effects are unchanged.",true)
				_sync_effect_controls()
				return
			candidate[key] = value
		_effects_options = candidate
		_effect_notice("Rama’s ability effects only. Warnings and timing stay visible.")
	receiver.set_options(_effects_options)
	_sync_effect_controls()

func _effect_notice(message: String, error := false) -> void:
	effects_notice.text = message
	effects_notice.add_theme_color_override("font_color",UI.GOLD if error else UI.MIST)

func _sync_effect_controls() -> void:
	reduced_effects_button.set_pressed_no_signal(_effects_options.reduced_effects)
	reduced_motion_button.set_pressed_no_signal(_effects_options.reduced_motion)

func _change_effect_option(value: bool, key: String) -> void:
	var receiver := _effect_receiver()
	if not _accepts_input() or not is_instance_valid(receiver) or not _effects_options.has(key):
		_sync_effect_controls()
		return
	var candidate := _effects_options.duplicate()
	candidate[key] = value
	var result := Bindings.merge_settings({"rama_effects":candidate},Bindings.config_path)
	if not result.ok:
		_sync_effect_controls()
		_effect_notice("Could not save effect preferences. Current ability effects are unchanged.",true)
		_schedule_effect_feedback()
		return
	_effects_options = candidate
	receiver.set_options(_effects_options)
	_effect_notice("Ability effect preferences saved. Warnings and timing stay visible.")
	_schedule_effect_feedback()

func _schedule_effect_feedback() -> void:
	_feedback_revision += 1
	if not _accepts_input(): return
	var focused := get_viewport().gui_get_focus_owner()
	if focused not in [reduced_effects_button,reduced_motion_button]: return
	_reveal_effect_feedback.call_deferred(_feedback_revision,selected_id,weakref(focused))

func _reveal_effect_feedback(revision: int, ability_id: String, focus_ref: WeakRef) -> void:
	# Text wrapping and focus scrolling settle in separate native layout passes.
	# Reveal the outcome without changing focus or following an obsolete action.
	if not _accepts_input(): return
	var tree := get_tree()
	for unused in 2:
		await tree.process_frame
		if not _accepts_input() or get_tree()!=tree or revision!=_feedback_revision or selected_id!=ability_id: return
		var focused: Control = focus_ref.get_ref()
		if not is_instance_valid(focused) or get_viewport().gui_get_focus_owner()!=focused: return
	details_scroll.ensure_control_visible(effects_notice)

func _number(value: Variant) -> String:
	return ("%.2f" % float(value)).trim_suffix("0").trim_suffix(".0")

func open(screen_context: String = "confluence", return_focus: Control = null) -> void:
	context = screen_context
	_return_focus = weakref(return_focus) if is_instance_valid(return_focus) else null
	status_label.text = "Bow training" if context == "courtyard" else "Confluence practice"
	Bindings.release_gameplay()
	refresh_bindings()
	_load_effect_options()
	show()
	_layout()
	if _accepts_input():
		if ability_buttons.has(selected_id): ability_buttons[selected_id].grab_focus()
		else: close_button.grab_focus()
	_schedule_initial_choice()

func close() -> void:
	if not visible: return
	_feedback_revision += 1
	hide()
	Bindings.release_gameplay()
	closed.emit()
	var previous = _return_focus.get_ref() if _return_focus else null
	if _can_restore_focus(previous): previous.grab_focus()

func _can_restore_focus(previous: Control) -> bool:
	if not is_instance_valid(previous) or not previous.is_inside_tree() or previous.is_queued_for_deletion() or not previous.is_visible_in_tree(): return false
	if previous.focus_mode == Control.FOCUS_NONE: return false
	if previous is BaseButton and previous.disabled: return false
	# Paused callers are valid. An explicitly isolated/retiring owner is not.
	var ancestor: Node = previous
	while ancestor:
		if ancestor.process_mode == Node.PROCESS_MODE_DISABLED or ancestor.is_queued_for_deletion(): return false
		ancestor = ancestor.get_parent()
	return true

func _input(event: InputEvent) -> void:
	if not _accepts_input(): return
	if event is InputEventKey and event.pressed and not event.echo:
		var key: int = event.physical_keycode if event.physical_keycode else event.keycode
		if key in [KEY_ESCAPE, KEY_F3]:
			close()
			get_viewport().set_input_as_handled()
		elif key in [KEY_PAGEUP,KEY_PAGEDOWN,KEY_HOME,KEY_END]:
			var reading: ScrollContainer = abilities_scroll if event.shift_pressed else details_scroll
			var step := maxi(1,int(reading.size.y)-UI.SPACE_LG)
			if key == KEY_HOME: reading.scroll_vertical = 0
			elif key == KEY_END: reading.scroll_vertical = int(reading.get_v_scroll_bar().max_value)
			else: reading.scroll_vertical += step * (-1 if key == KEY_PAGEUP else 1)
			get_viewport().set_input_as_handled()
		elif key in [KEY_TAB, KEY_UP, KEY_DOWN]:
			var available: Array[Control] = []
			for control in focus_order:
				if is_instance_valid(control) and control.is_visible_in_tree() and (not control is BaseButton or not control.disabled): available.append(control)
			if available.is_empty(): return
			var direction := -1 if (key == KEY_UP or (key == KEY_TAB and event.shift_pressed)) else 1
			var current := available.find(get_viewport().gui_get_focus_owner())
			if current < 0:
				if direction < 0: available.back().grab_focus()
				else: available.front().grab_focus()
			else:
				available[posmod(current + direction, available.size())].grab_focus()
			get_viewport().set_input_as_handled()

func _accepts_input() -> bool:
	if not is_visible_in_tree(): return false
	var ancestor := get_parent()
	while ancestor:
		if ancestor.process_mode == Node.PROCESS_MODE_DISABLED: return false
		ancestor = ancestor.get_parent()
	return true

func _process(_delta: float) -> void:
	if not visible: return
	_practice_clock += _delta
	if _practice_clock >= .2:
		_practice_clock = 0
		_refresh_profile()
	if not is_instance_valid(_effect_receiver()) and not reduced_effects_button.disabled: _load_effect_options()
	var viewport := get_viewport_rect().size
	# Wrapped labels settle after the first container sort. Reapply the bounded
	# card rectangle when an earlier zero-width minimum briefly made it taller.
	if _last_size != viewport or card.size.y > minf(520, viewport.y - 48) or card.size.x > minf(920, viewport.x - 48): _layout()

func _layout() -> void:
	if not card: return
	var resized_viewport := _last_size != get_viewport_rect().size
	_last_size = get_viewport_rect().size
	card.size = Vector2(minf(920, _last_size.x - 48), minf(520, _last_size.y - 48))
	card.position = (_last_size - card.size) * .5
	abilities_scroll.custom_minimum_size.x = 252 if _last_size.x >= 1100 else 236
	_split.add_theme_constant_override("separation", UI.SPACE_LG)
	_schedule_initial_choice()
	if resized_viewport:
		ScrollFocus.reveal_after_layout(self,abilities_scroll)
		ScrollFocus.reveal_after_layout(self,details_scroll)

func _schedule_initial_choice() -> void:
	if _reveal_pending: return
	_reveal_pending = true
	_reveal_initial_choice.call_deferred()

func _reveal_initial_choice() -> void:
	# Native focus scrolling can run after the first container sort. Preserve
	# the Bow heading only while that initial choice still owns focus.
	for unused in range(2):
		if not is_inside_tree():
			_reveal_pending = false
			return
		await get_tree().process_frame
	_reveal_pending = false
	if _accepts_input() and selected_id=="kodanda" and get_viewport().gui_get_focus_owner()==ability_buttons.get("kodanda"):
		abilities_scroll.scroll_vertical = 0

func configure_practice_report(provider: Callable) -> void:
	_practice_report_provider = provider
	_refresh_profile()

func _practice_number(value: Variant) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and float(value) >= 0 and float(value) <= 100000000

func _refresh_profile() -> void:
	if not is_instance_valid(profile_label): return
	var bow: Dictionary = _rules.get("kodanda", {})
	var volley: Dictionary = _rules.get("dawn_volley", {})
	profile_label.text = "%d health · %d shield capacity\nPrecision arrows, formation pressure and fixed protection.\n%s m bow · %s m volley · Land before casting." % [Vitals.MAX_HEALTH, Vitals.MAX_SHIELD, _number(bow.get("range_m",0)), _number(volley.get("range_m",0))]
	hero_identity_label.text = "RAMA · BOW + FOUR ABILITIES"
	hero_identity_label.tooltip_text = "Rama · The solar archer"
	practice_heading.hide()
	practice_label.hide()
	if context != "courtyard" or not _practice_report_provider.is_valid(): return
	var value: Variant = _practice_report_provider.call()
	if not value is Dictionary or not value.get("configured",false) or value.get("scope") != "courtyard": return
	for field in ["casts_started", "hits", "damage_dealt", "healing_applied", "shield_granted", "step_distance_m"]:
		if not _practice_number(value.get(field)): return
	practice_label.text = "%d casts · %d contacts · %.0f effective damage\n%.0f healing · %.0f shield granted\n%.1f m accepted steps" % [int(value.casts_started), int(value.hits), float(value.damage_dealt), float(value.healing_applied), float(value.shield_granted), float(value.step_distance_m)]
	var rows: Variant = value.get("by_ability", [])
	if rows is Array:
		for item: Variant in rows:
			if not item is Dictionary or item.get("ability_id") != selected_id: continue
			if _practice_number(item.get("casts_started")) and _practice_number(item.get("hits")) and _practice_number(item.get("damage_dealt")):
				practice_label.text += "\n%s · %d casts · %d contacts · %.0f damage" % [_rules.get(selected_id,{}).get("label",selected_id), int(item.casts_started), int(item.hits), float(item.damage_dealt)]
			break
	practice_label.text += "\nObserved this training attempt; reset clears this record."
	hero_identity_label.text = "RAMA · %d casts · %d contacts · %.0f damage" % [int(value.casts_started), int(value.hits), float(value.damage_dealt)]
	hero_identity_label.tooltip_text = "Current training attempt\n" + practice_label.text
	practice_heading.show()
	practice_label.show()
