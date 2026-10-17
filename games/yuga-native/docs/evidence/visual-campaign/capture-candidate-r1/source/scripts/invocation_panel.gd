extends Control
## Offline invocation selector. It never casts, awards payloads, or owns cooldown.
const Bindings = preload("res://scripts/input_bindings.gd")
const CATALOGUE_PATH := "res://assets/design/hero-codex.json"
const RULES_PATH := "res://assets/design/native-ultimate-rules.json"
const INK := Color("10282e")
const GOLD := Color("e7c078")
const CREAM := Color("f1e6ce")
const MIST := Color("b0c9c8")
signal invocation_selected(hero_id: String)
signal closed
signal effects_options_changed(options: Dictionary)

class InvocationSigil extends Control:
	var accent := Color("e7c078")
	var number := 0
	func _draw() -> void:
		var centre := size * 0.5
		var radius := minf(size.x, size.y) * 0.42
		draw_circle(centre, radius, Color("193a42"))
		draw_arc(centre, radius, -.7, 3.9, 40, accent.darkened(.3), 1.0, true)
		var petals := 3 + number % 5
		for i in range(petals):
			var angle := TAU * i / petals - PI * .5
			var direction := Vector2(cos(angle), sin(angle))
			var tangent := Vector2(-direction.y, direction.x)
			var points := PackedVector2Array([centre + direction * radius * .18,
				centre + direction * radius * .52 + tangent * radius * .15,
				centre + direction * radius * .83,
				centre + direction * radius * .52 - tangent * radius * .15])
			draw_colored_polygon(points, accent.darkened(.25))
			draw_polyline(PackedVector2Array([points[0], points[2]]), accent, 1.0, true)
		draw_circle(centre, 3.0, accent)

var card: PanelContainer
var hero_buttons: Dictionary = {}
var choose_button: Button
var close_button: Button
var reduced_effects_button: CheckButton
var reduced_motion_button: CheckButton
var details_scroll: ScrollContainer
var status: Label
var hero_name: Label
var role_label: Label
var ultimate_name: Label
var art_title: Label
var geometry_label: Label
var payload_label: Label
var counterplay_label: Label
var effect_label: Label
var sigil: InvocationSigil
var grid: GridContainer
var focus_order: Array[Control] = []
var _entries: Dictionary = {}
var _order: Array[String] = []
var _preview_id := "rama"
var _selected_id := "rama"
var _cooldown := 0.0
var _phase := "ready"
var _suspended := false
var _shared_cooldown := 12.0
var _configured := false
var _available := true
var _unavailable_reason := "Invocation selection is unavailable."
var _effects_options := {"reduced_effects":false,"reduced_motion":false}
var _notice := ""
var _notice_error := false
var _return_focus: WeakRef
var _last_size := Vector2.ZERO

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_build()
	_load_options()
	if _configured: _populate()
	_layout()
	hide()

func configure(catalogue: Dictionary = {}, rules: Dictionary = {}, selection: String = "rama") -> bool:
	if catalogue.is_empty():
		var loaded = JSON.parse_string(FileAccess.get_file_as_string(CATALOGUE_PATH))
		if not loaded is Dictionary: return false
		catalogue = loaded
	if rules.is_empty():
		var loaded = JSON.parse_string(FileAccess.get_file_as_string(RULES_PATH))
		if not loaded is Dictionary: return false
		rules = loaded
	if not catalogue.get("heroes") is Array or not rules.get("rules") is Array: return false
	if catalogue.heroes.size() != 14 or rules.rules.size() != 14: return false
	if not _finite_number(rules.get("shared_cooldown_s")) or float(rules.shared_cooldown_s) != 12.0: return false
	var incoming := {}
	var ordered: Array[String] = []
	for hero in catalogue.heroes:
		if not hero is Dictionary or not _text(hero.get("id"),40) or not _text(hero.get("name"),40) or not _text(hero.get("role"),40): return false
		if incoming.has(hero.id) or not hero.get("abilities") is Array or not hero.get("art_direction") is Dictionary: return false
		var ultimate := {}
		for ability in hero.abilities:
			if ability is Dictionary and ability.get("slot") == "R": ultimate = ability
		if not _text(ultimate.get("effect"),1200) or not _text(hero.art_direction.get("title"),160): return false
		incoming[hero.id] = {"hero":hero.duplicate(true),"ultimate":ultimate.duplicate(true)}
		ordered.append(hero.id)
	var found := {}
	for rule in rules.rules:
		if not _safe_rule(rule) or not incoming.has(rule.hero_id) or found.has(rule.hero_id): return false
		found[rule.hero_id] = true
		incoming[rule.hero_id]["rule"] = rule.duplicate(true)
	if not incoming.has(selection): return false
	_entries = incoming
	_order = ordered
	_selected_id = selection
	_preview_id = selection
	_shared_cooldown = float(rules.shared_cooldown_s)
	_configured = true
	if card: _populate()
	return true

static func _text(value: Variant, maximum: int) -> bool:
	return value is String and not value.is_empty() and value.length() <= maximum

static func _finite_number(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value))

static func _safe_rule(value: Variant) -> bool:
	if not value is Dictionary or not _text(value.get("hero_id"),40) or not _text(value.get("name"),80): return false
	if not value.get("geometry") is Dictionary or not value.get("timing") is Dictionary or not value.get("effects") is Array: return false
	if value.effects.is_empty() or value.effects.size() > 3: return false
	for key in ["windup_s","travel_s","active_s","recovery_s"]:
		if not _finite_number(value.timing.get(key)) or float(value.timing[key]) < 0 or float(value.timing[key]) > 12: return false
	var g: Dictionary = value.geometry
	if g.get("kind") not in ["projectile_volley","disk","sector","zone_disk","summon_pair"]: return false
	if g.get("anchor") not in ["caster","ground_target"]: return false
	for key in ["radius_m","range_m","target_range_m","maximum_route_distance_m"]:
		if g.has(key) and (not _finite_number(g[key]) or float(g[key]) <= 0 or float(g[key]) > 100): return false
	if g.kind in ["disk","zone_disk"] and not g.has("radius_m"): return false
	if g.kind in ["projectile_volley","sector"] and not g.has("range_m"): return false
	if g.kind == "projectile_volley" and (not g.get("yaw_offsets_rad") is Array or g.yaw_offsets_rad.is_empty() or g.yaw_offsets_rad.size() > 8): return false
	if g.anchor == "ground_target" and not g.has("target_range_m"): return false
	for payload in value.effects:
		if not payload is Dictionary or payload.get("kind") not in ["damage","heal","shield","heal_rate","damage_rate","slow","summon"]: return false
		if payload.get("team") not in ["enemy","ally"]: return false
		var required: Array = ["amount"]
		match payload.kind:
			"heal_rate", "damage_rate": required = ["amount_per_s"]
			"slow": required = ["multiplier","duration_s"]
			"shield": required = ["amount","duration_s"]
			"summon": required = ["count","duration_s","health","attack_damage"]
		for key in required:
			if not _finite_number(payload.get(key)) or float(payload[key]) <= 0 or float(payload[key]) > 10000: return false
		if payload.kind == "summon" and payload.get("role") not in ["bow_guard","spearman"]: return false
	return true

func _build() -> void:
	var shade := ColorRect.new()
	shade.color = Color(0.018,.037,.052,.94)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(shade)
	card = PanelContainer.new()
	card.name = "InvocationCard"
	card.add_theme_stylebox_override("panel", _style(Color("10262e"),Color("536c72"),1,18))
	add_child(card)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation",8)
	card.add_child(column)
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation",12)
	column.add_child(header)
	var heading := _label("INVOCATION PRACTICE",25,CREAM)
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(heading)
	close_button = _button("Back · Esc",close)
	close_button.name = "CloseInvocations"
	close_button.custom_minimum_size = Vector2(116,42)
	header.add_child(close_button)
	var scope := _label("Channel a legend through Rama · offline troop practice",14,MIST)
	scope.name = "InvocationScope"
	column.add_child(scope)
	var body := HBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation",18)
	column.add_child(body)
	var roster := VBoxContainer.new()
	roster.custom_minimum_size.x = 286
	roster.add_theme_constant_override("separation",6)
	body.add_child(roster)
	roster.add_child(_label("CHOOSE AN INVOCATION",12,GOLD))
	grid = GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation",6)
	grid.add_theme_constant_override("v_separation",5)
	roster.add_child(grid)
	var detail := VBoxContainer.new()
	detail.name = "InvocationDetail"
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.add_theme_constant_override("separation",5)
	body.add_child(detail)
	var identity := HBoxContainer.new()
	identity.add_theme_constant_override("separation",12)
	detail.add_child(identity)
	sigil = InvocationSigil.new()
	sigil.custom_minimum_size = Vector2(64,64)
	sigil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	identity.add_child(sigil)
	var names := VBoxContainer.new()
	names.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	names.add_theme_constant_override("separation",0)
	identity.add_child(names)
	hero_name = _label("Rama",26,CREAM)
	role_label = _label("STRIKER",12,GOLD)
	art_title = _label("",13,MIST)
	art_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	for item in [hero_name,role_label,art_title]: names.add_child(item)
	ultimate_name = _label("",20,CREAM)
	ultimate_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail.add_child(ultimate_name)
	geometry_label = _label("",13,GOLD)
	geometry_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail.add_child(geometry_label)
	details_scroll = ScrollContainer.new()
	details_scroll.name = "InvocationReading"
	details_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	details_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	details_scroll.follow_focus = true
	details_scroll.focus_mode = Control.FOCUS_ALL
	details_scroll.custom_minimum_size.y = 140
	detail.add_child(details_scroll)
	var reading := VBoxContainer.new()
	reading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	reading.add_theme_constant_override("separation",7)
	details_scroll.add_child(reading)
	payload_label = _label("",16,CREAM)
	counterplay_label = _label("",14,MIST)
	effect_label = _label("",14,MIST)
	for item in [payload_label,counterplay_label,effect_label]:
		item.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		item.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	reading.add_child(_label("TROOP EFFECT",11,GOLD))
	reading.add_child(payload_label)
	reading.add_child(_label("PLAY AROUND IT",11,GOLD))
	reading.add_child(counterplay_label)
	reading.add_child(_label("ART DIRECTION",11,GOLD))
	reading.add_child(effect_label)
	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation",10)
	column.add_child(footer)
	reduced_effects_button = _check("Reduced effects","Keep exact warnings; reduce decorative layers.")
	reduced_motion_button = _check("Reduced motion","Keep impact and timing; freeze ornamental motion.")
	for checkbox in [reduced_effects_button,reduced_motion_button]: footer.add_child(checkbox)
	reduced_effects_button.toggled.connect(_change_option.bind("reduced_effects"))
	reduced_motion_button.toggled.connect(_change_option.bind("reduced_motion"))
	choose_button = _button("Use invocation",_choose)
	choose_button.name = "ChooseInvocation"
	choose_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	choose_button.custom_minimum_size.x = 202
	footer.add_child(choose_button)
	status = _label("",13,MIST)
	status.name = "InvocationStatus"
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.custom_minimum_size.y = 34
	column.add_child(status)

func _style(background: Color, border: Color, width: int = 1, margin: int = 10) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.border_color = border
	style.set_border_width_all(width)
	style.set_corner_radius_all(4)
	style.set_content_margin_all(margin)
	return style

func _label(text: String, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size",font_size)
	label.add_theme_color_override("font_color",color)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label

func _button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.focus_mode = Control.FOCUS_ALL
	button.custom_minimum_size = Vector2(140,40)
	button.add_theme_font_size_override("font_size",15)
	button.add_theme_color_override("font_color",CREAM)
	button.add_theme_color_override("font_disabled_color",Color("819596"))
	for state in ["normal","hover","pressed","focus","disabled"]:
		var background := Color("193840") if state == "normal" else Color("284c53")
		if state == "disabled": background = Color("192d33")
		button.add_theme_stylebox_override(state,_style(background,GOLD if state == "focus" else Color("456169"),2 if state == "focus" else 1,8))
	button.pressed.connect(callback)
	return button

func _check(text: String, hint: String) -> CheckButton:
	var check := CheckButton.new()
	check.text = text
	check.tooltip_text = hint
	check.custom_minimum_size = Vector2(192,44)
	check.add_theme_font_size_override("font_size",14)
	check.add_theme_color_override("font_color",CREAM)
	check.add_theme_stylebox_override("focus",_style(Color("23424a"),GOLD,2,3))
	return check

func _populate() -> void:
	for child in grid.get_children():
		grid.remove_child(child)
		child.free()
	hero_buttons.clear()
	focus_order.clear()
	for id in _order:
		var button := _button(_entries[id].hero.name,_preview.bind(id))
		button.name = "Invocation_" + id
		button.custom_minimum_size = Vector2(140,39)
		button.tooltip_text = _entries[id].hero.name + " · " + _entries[id].rule.name
		button.focus_entered.connect(_preview.bind(id))
		grid.add_child(button)
		hero_buttons[id] = button
		focus_order.append(button)
	focus_order.append_array([details_scroll,reduced_effects_button,reduced_motion_button,choose_button,close_button])
	_refresh_detail()
	_refresh_status()

func _preview(id: String) -> void:
	if not _entries.has(id) or not _available: return
	_preview_id = id
	_notice = ""
	_notice_error = false
	_refresh_detail()
	_refresh_status()

func _refresh_detail(reset_scroll: bool = true) -> void:
	if not _configured or not hero_name: return
	var entry: Dictionary = _entries[_preview_id]
	var hero: Dictionary = entry.hero
	var rule: Dictionary = entry.rule
	hero_name.text = hero.name
	role_label.text = hero.role.to_upper() + (" · EQUIPPED" if _preview_id == _selected_id else " · PREVIEW")
	art_title.text = hero.art_direction.title
	ultimate_name.text = rule.name
	geometry_label.text = _geometry_text(rule) + " · " + _n(rule.timing.windup_s) + " s preparation"
	payload_label.text = _payload_text(rule)
	counterplay_label.text = _counterplay(rule)
	effect_label.text = entry.ultimate.effect
	var palette = hero.art_direction.get("palette",{})
	var accent: Variant = palette.get("accent", "#e7c078") if palette is Dictionary else "#e7c078"
	sigil.accent = Color(accent) if accent is String and Color.html_is_valid(accent) else GOLD
	sigil.number = _order.find(_preview_id)
	sigil.queue_redraw()
	if reset_scroll: details_scroll.scroll_vertical = 0
	for id in hero_buttons:
		hero_buttons[id].text = _entries[id].hero.name + (" ·" if id == _selected_id else "")
		hero_buttons[id].disabled = not _available
	choose_button.disabled = not _configured or not _available
	choose_button.text = "Return to practice" if _preview_id == _selected_id else "Use invocation"

static func _n(value: Variant) -> String:
	return ("%.2f" % float(value)).trim_suffix("0").trim_suffix("0").trim_suffix(".")

func _geometry_text(rule: Dictionary) -> String:
	var geometry: Dictionary = rule.geometry
	match geometry.kind:
		"projectile_volley": return str(geometry.yaw_offsets_rad.size()) + (" arrow" if geometry.yaw_offsets_rad.size() == 1 else " arrows") + " · " + _n(geometry.range_m) + " m lane"
		"sector": return "Forward fan · " + _n(geometry.range_m) + " m reach"
		"summon_pair": return "Two sentinels · lane placement"
	var anchor := "Aimed ground" if geometry.anchor == "ground_target" else "Around you"
	return anchor + " · " + _n(geometry.radius_m) + " m radius" + (" · " + _n(geometry.target_range_m) + " m aim" if geometry.anchor == "ground_target" else "")

func _payload_text(rule: Dictionary) -> String:
	var lines := PackedStringArray()
	for effect in rule.effects:
		match effect.kind:
			"damage": lines.append(_n(effect.amount) + " damage to enemy troops" + (" per arrow." if rule.geometry.kind == "projectile_volley" else "."))
			"heal": lines.append("Restore up to " + _n(effect.amount) + " health to allied troops.")
			"shield": lines.append(_n(effect.amount) + " allied shield for " + _n(effect.duration_s) + " s; strongest shield applies.")
			"heal_rate": lines.append(_n(effect.amount_per_s) + " allied health/s while inside the " + _n(rule.timing.active_s) + " s zone.")
			"damage_rate": lines.append(_n(effect.amount_per_s) + " enemy damage/s while inside the " + _n(rule.timing.active_s) + " s zone.")
			"slow": lines.append("Enemy movement becomes " + _n(float(effect.multiplier) * 100.0) + "% while affected.")
			"summon": lines.append(str(int(effect.count)) + " " + ("bow" if effect.role == "bow_guard" else "spear") + " sentinels for " + _n(effect.duration_s) + " s · " + _n(effect.health) + " health / " + _n(effect.attack_damage) + " attack each.")
	return "\n".join(lines)

func _counterplay(rule: Dictionary) -> String:
	match rule.geometry.kind:
		"projectile_volley": return "Sidestep the locked firing lane or use solid cover. Each arrow stops at its first target or wall."
		"sector": return "Leave the marked fan during preparation. Solid cover blocks the strike."
		"summon_pair": return "Both lane positions need space and army capacity. Sentinels expire without core damage or expiry gold."
	if rule.hero_id == "hanuman": return "Leave the landing circle or use cover. This projection does not move Rama; allied healing is capped."
	if rule.hero_id == "ulupi": return "Leave the basin or break line of sight. The slow clears shortly after leaving; the zone stays where it was cast."
	for effect in rule.effects:
		if effect.team == "ally": return "Allies must be inside the marked area with clear sight. Healing is capped; fallen troops are not revived."
	return "Leave the marked radius before impact or use solid cover. Only living enemy troops receive damage."

func update_session(state: Dictionary) -> bool:
	var selection: Variant = state.get("selected_hero")
	var cooldown: Variant = state.get("cooldown_remaining")
	if not selection is String or not _entries.has(selection) or not _finite_number(cooldown): return false
	if float(cooldown) < 0 or float(cooldown) > _shared_cooldown + .001: return false
	if state.get("active_phase") not in ["windup","travel","active","recovery","ready"] or not state.get("suspended") is bool: return false
	var selection_changed: bool = _selected_id != selection
	_selected_id = selection
	_cooldown = float(cooldown)
	_phase = state.active_phase
	_suspended = state.suspended
	if selection_changed: _refresh_detail(false)
	_refresh_status()
	return true

func open(return_focus: Control = null) -> void:
	Bindings.release_gameplay()
	_return_focus = weakref(return_focus) if is_instance_valid(return_focus) else null
	_preview_id = _selected_id
	_notice = ""
	_load_options()
	_refresh_detail()
	_refresh_status()
	show()
	_layout()
	call_deferred("_focus_initial")

func _focus_initial() -> void:
	if not visible: return
	if hero_buttons.has(_preview_id) and not hero_buttons[_preview_id].disabled: hero_buttons[_preview_id].grab_focus()
	else: close_button.grab_focus()

func close() -> void:
	if not visible: return
	Bindings.release_gameplay()
	hide()
	var target = _return_focus.get_ref() if _return_focus != null else null
	if is_instance_valid(target) and target is Control and target.is_inside_tree() and target.is_visible_in_tree(): target.grab_focus()
	_return_focus = null
	closed.emit()

func _choose() -> void:
	if not _configured or not _available: return
	Bindings.release_gameplay()
	if _preview_id == _selected_id:
		close()
		return
	_notice = "Selection requested; waiting for practice."
	_notice_error = false
	_refresh_status()
	invocation_selected.emit(_preview_id)

func set_available(enabled: bool, reason: String = "Invocation selection is unavailable.") -> void:
	_available = enabled
	_unavailable_reason = reason.left(180)
	_refresh_detail()
	_refresh_status()

func set_notice(text: String, is_error: bool = false) -> void:
	_notice = text.left(220)
	_notice_error = is_error
	_refresh_status()

func options() -> Dictionary:
	return _effects_options.duplicate()

func _load_options() -> void:
	var previous := _effects_options.duplicate()
	var result := Bindings.read_config(Bindings.config_path)
	_notice_error = false
	_effects_options = {"reduced_effects":false,"reduced_motion":false}
	if result.ok:
		for key in _effects_options:
			var value: Variant = result.config.get_value("invocations",key,false)
			if value is bool: _effects_options[key] = value
			else: _notice = "Invalid effect preference; defaults are active."
	else:
		_notice = result.message
		_notice_error = true
	if reduced_effects_button:
		reduced_effects_button.set_pressed_no_signal(_effects_options.reduced_effects)
		reduced_motion_button.set_pressed_no_signal(_effects_options.reduced_motion)
	# Reopening can observe an external settings edit. Keep the live effect owner
	# synchronized with what the toggles actually display, including safe defaults.
	if previous != _effects_options: effects_options_changed.emit(options())

func _change_option(value: bool, key: String) -> void:
	var candidate := _effects_options.duplicate()
	candidate[key] = value
	var result := Bindings.merge_settings({"invocations":candidate},Bindings.config_path)
	if not result.ok:
		_load_options()
		set_notice("Could not save effects: " + result.message,true)
		return
	_effects_options = candidate
	set_notice("Effect preferences saved. Exact warnings stay visible.")
	effects_options_changed.emit(options())

func _refresh_status() -> void:
	if not status: return
	status.add_theme_color_override("font_color", Color("efbd9c") if _notice_error else MIST)
	if not _configured: status.text = "Invocation data is unavailable. Return to practice."; return
	if not _available: status.text = _unavailable_reason; return
	if not _notice.is_empty(): status.text = _notice; return
	var key := Bindings.label("ultimate")
	var control := key if not key.is_empty() else "Invocation control"
	var state := "Ready after returning · " + control + " to invoke"
	if _cooldown > .01: state = "Shared recovery: " + ("%.1f" % _cooldown) + " s · choosing preserves this cooldown"
	if _phase != "ready": state += " · current cast: " + _phase
	status.text = state + "\nArrows browse · Enter selects · Tab moves focus · Esc / " + Bindings.label("open_invocations") + " back"

func _process(_delta: float) -> void:
	if visible: _layout()

func _layout() -> void:
	if not card: return
	var viewport := get_viewport_rect().size
	if viewport == _last_size: return
	_last_size = viewport
	card.size = Vector2(minf(1040,viewport.x-32),minf(620,viewport.y-32))
	card.position = (viewport-card.size) * .5

func _input(event: InputEvent) -> void:
	if not visible or not event is InputEventKey or not event.pressed or event.echo: return
	var key: int = event.physical_keycode if event.physical_keycode else event.keycode
	if key == KEY_ESCAPE or event.is_action_pressed("open_invocations"):
		close()
		get_viewport().set_input_as_handled()
		return
	var focus := get_viewport().gui_get_focus_owner()
	if key == KEY_TAB:
		var available: Array[Control] = []
		for item in focus_order:
			if item.is_visible_in_tree() and (not item is BaseButton or not item.disabled): available.append(item)
		if not available.is_empty(): available[posmod(available.find(focus)+(-1 if event.shift_pressed else 1),available.size())].grab_focus()
		get_viewport().set_input_as_handled()
		return
	if focus == details_scroll and key in [KEY_UP,KEY_DOWN,KEY_PAGEUP,KEY_PAGEDOWN]:
		details_scroll.scroll_vertical += (-1 if key in [KEY_UP,KEY_PAGEUP] else 1) * (120 if key in [KEY_PAGEUP,KEY_PAGEDOWN] else 28)
		get_viewport().set_input_as_handled()
		return
	if focus in hero_buttons.values():
		var focused_id := ""
		for id in hero_buttons:
			if hero_buttons[id] == focus: focused_id = id
		if key in [KEY_ENTER,KEY_KP_ENTER]:
			_preview(focused_id)
			_choose()
		elif key in [KEY_LEFT,KEY_RIGHT,KEY_UP,KEY_DOWN]:
			var direction := -1 if key == KEY_LEFT else (1 if key == KEY_RIGHT else (-2 if key == KEY_UP else 2))
			var index := posmod(_order.find(focused_id)+direction,_order.size())
			hero_buttons[_order[index]].grab_focus()
		else: return
		get_viewport().set_input_as_handled()

func report() -> Dictionary:
	var rectangles := {}
	for control in focus_order:
		if is_instance_valid(control): rectangles[str(control.name)] = control.get_global_rect()
	return {"visible":visible,"configured":_configured,"available":_available,"preview_id":_preview_id,
		"selected_hero":_selected_id,"cooldown_remaining":_cooldown,"active_phase":_phase,"suspended":_suspended,
		"effects_options":options(),"focusable_count":focus_order.size(),"hero_count":hero_buttons.size(),
		"choose_disabled":choose_button.disabled if choose_button else true,"card_rect":card.get_global_rect() if card else Rect2(),
		"control_rects":rectangles,"status":status.text if status else "","payload":payload_label.text if payload_label else "",
		"geometry":geometry_label.text if geometry_label else "","counterplay":counterplay_label.text if counterplay_label else "",
		"receiver_scope":"living lane troops; current Rama avatar; offline practice"}
