extends Control
## Five ability slots; compact widths retain glyphs, keys and real state. Cooldowns and health read the actual simulation.
const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const Glyph = preload("res://scripts/rama_ability_glyph.gd")
const IDS := ["kodanda","piercing_dawn","measured_step","guardian_circle","dawn_volley"]
const ACTIONS := ["fire","pulse","dash","guardian_circle","ultimate"]
const HUD_TEXT_SIZE := UI.TYPE_HUD
const HUD_WIDTH := 820.0
const HUD_HEIGHT := 112.0
const SLOT_REFRESH_SECONDS := .08
const SLOT_WIDTH := 156.0
const SLOT_HEIGHT := 56.0
const COMPACT_HEIGHT := 80.0
const COMPACT_SLOT_HEIGHT := 48.0
var runtime: Node3D
var life: ProgressBar
var life_text: Label
var note: Label
var status_panel: PanelContainer
var slots: Array[Label] = []
var slot_cards: Array[PanelContainer] = []
var slot_glyphs: Array[TextureRect] = []
var _slot_states: Array[StringName] = []
var clock := 0.0
var _last_availability: StringName = &""
var _last_action_signature: Array = []
var _slot_grid: GridContainer
var _compact_slots := false
var _status_heading: HBoxContainer
var _health_row: HBoxContainer
var _names_hint: Label
var _status_column: VBoxContainer
func _ready() -> void:
	name = "RamaHeroHUD"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	offset_left = -HUD_WIDTH / 2; offset_right = HUD_WIDTH / 2
	offset_top = -HUD_HEIGHT - 18; offset_bottom = -18
	theme = UI.create()
	var column := VBoxContainer.new()
	column.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	column.add_theme_constant_override("separation", UI.SPACE_XS)
	add_child(column)
	# Keep live health and combat notices readable over bright and dark worlds.
	# Reserve space for readable stock/cooldowns without moving surrounding panels.
	status_panel = PanelContainer.new()
	status_panel.name = "CombatStatus"
	status_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var status_surface := UI.hud_panel_style(&"status")
	status_surface.content_margin_top = 0
	status_surface.content_margin_bottom = 0
	status_panel.add_theme_stylebox_override("panel", status_surface)
	column.add_child(status_panel)
	_status_column = VBoxContainer.new()
	_status_column.add_theme_constant_override("separation", UI.SPACE_XS)
	status_panel.add_child(_status_column)
	note = UI.label("Practice unavailable", UI.TYPE_HUD_DETAIL)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note.clip_text = true
	note.max_lines_visible = 1
	note.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_status_heading = HBoxContainer.new()
	_status_column.add_child(_status_heading)
	note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_status_heading.add_child(note)
	_names_hint = UI.label("F3 names", UI.TYPE_HUD_DETAIL, UI.MIST)
	_names_hint.visible = false
	_status_heading.add_child(_names_hint)
	_health_row = HBoxContainer.new()
	_status_column.add_child(_health_row)
	life = ProgressBar.new(); life.show_percentage = false
	life.max_value = 1; life.value = 0
	life.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	life.custom_minimum_size.y = 10
	var fill := StyleBoxFlat.new(); fill.bg_color = UI.MARSH
	fill.set_corner_radius_all(UI.CORNER)
	life.add_theme_stylebox_override("fill", fill)
	_health_row.add_child(life)
	life_text = UI.label("—", HUD_TEXT_SIZE)
	_health_row.add_child(life_text)
	_slot_grid = GridContainer.new()
	_slot_grid.name = "AbilitySlots"
	_slot_grid.columns = IDS.size()
	_slot_grid.add_theme_constant_override("h_separation", UI.SPACE_XS)
	_slot_grid.add_theme_constant_override("v_separation", UI.SPACE_XS)
	column.add_child(_slot_grid)
	for i in IDS.size():
		var card := PanelContainer.new()
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.custom_minimum_size = Vector2(SLOT_WIDTH, SLOT_HEIGHT)
		card.add_theme_stylebox_override("panel", _slot_surface(&"unavailable"))
		_slot_grid.add_child(card)
		var label := UI.label("", HUD_TEXT_SIZE)
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		card.add_child(label); slots.append(label); slot_cards.append(card)
		var glyph := Glyph.new()
		glyph.name = "AbilityGlyph"
		label.add_child(glyph)
		slot_glyphs.append(glyph)
		label.resized.connect(_place_slot_glyph.bind(i))
		_slot_states.append(&"unavailable")
	get_viewport().size_changed.connect(_layout_slots)
	_layout_slots()
	_refresh()

func _layout_slots() -> void:
	if not is_instance_valid(_slot_grid): return
	# UI scaling changes logical canvas size even when the OS window stays large.
	# Compact slots retain real keys/states and glyphs; full names stay in F3 and action status.
	var width := minf(HUD_WIDTH, maxf(SLOT_WIDTH, get_viewport_rect().size.x - UI.SPACE_MD * 2))
	var compact := width < HUD_WIDTH
	var changed := compact != _compact_slots
	_compact_slots = compact
	_slot_grid.columns = IDS.size()
	for card in slot_cards:
		# Let the real key/state minima allocate each compact column. Equal
		# forced widths waste space beside short keys and overflow a long key.
		card.custom_minimum_size.x = 0 if compact else SLOT_WIDTH
		card.custom_minimum_size.y = COMPACT_SLOT_HEIGHT if compact else SLOT_HEIGHT
	# Retain the same two lines of 16-unit text and 20-unit glyphs. The short
	# canvas gives space back through padding/bar thickness, never smaller type.
	_status_column.add_theme_constant_override("separation", 0 if compact else UI.SPACE_XS)
	life.custom_minimum_size.y = 4 if compact else 10
	_names_hint.text = "%s names" % Bindings.label("open_invocations")
	if changed:
		life_text.reparent(_status_heading if compact else _health_row)
		_names_hint.visible = compact
		for index in slot_cards.size():
			slot_cards[index].add_theme_stylebox_override("panel", _slot_surface(_slot_states[index]))
	var height := COMPACT_HEIGHT if compact else HUD_HEIGHT
	var bottom := float(UI.SPACE_SM if compact else 18)
	offset_left = -width * .5
	offset_right = width * .5
	offset_top = -height - bottom
	offset_bottom = -bottom
	_layout_status_notice()
	if changed: _refresh()

func _layout_status_notice() -> void:
	if not is_instance_valid(note): return
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART if _compact_slots else TextServer.AUTOWRAP_OFF
	note.max_lines_visible = -1 if _compact_slots else 1
	if not _compact_slots:
		note.custom_minimum_size.y=0
		return
	var width := offset_right-offset_left
	var available := width-UI.SPACE_SM*2-_status_heading.get_theme_constant("separation")*2
	for label in [life_text,_names_hint]:
		available-=label.get_theme_font("font").get_string_size(label.text,HORIZONTAL_ALIGNMENT_LEFT,-1,label.get_theme_font_size("font_size")).x
	var notice_height := note.get_theme_font("font").get_multiline_string_size(note.text,HORIZONTAL_ALIGNMENT_LEFT,maxf(1,floorf(available)),note.get_theme_font_size("font_size")).y
	var line_height := note.get_theme_font("font").get_string_size("M",HORIZONTAL_ALIGNMENT_LEFT,-1,note.get_theme_font_size("font_size")).y
	var line_count := maxi(1,roundi(notice_height/maxf(1,line_height)))
	notice_height+=(line_count-1)*note.get_theme_constant("line_spacing")
	note.custom_minimum_size.y=notice_height
	var heading_height := life_text.get_theme_font("font").get_height(HUD_TEXT_SIZE)
	# Long queued-action feedback earns another readable line only while that
	# feedback is present; it must not push the health or key row off screen.
	var height := COMPACT_HEIGHT+maxf(0,notice_height-heading_height)
	offset_top = -height-UI.SPACE_SM

func _slot_surface(state: StringName) -> StyleBoxFlat:
	var surface := UI.hud_panel_style(state)
	surface.content_margin_top = 0 if _compact_slots else UI.SPACE_XS
	surface.content_margin_bottom = 0 if _compact_slots else UI.SPACE_XS
	surface.content_margin_left = UI.SPACE_XS if _compact_slots else UI.SPACE_SM
	surface.content_margin_right = UI.SPACE_XS if _compact_slots else UI.SPACE_SM
	return surface

func _glyph_indent(label: Label) -> String:
	# Reserve a measured inline emblem before the second-line name. Keeping the
	# native Label text preserves the existing readout and observer contract.
	var space := label.get_theme_font("font").get_string_size(" ", HORIZONTAL_ALIGNMENT_LEFT, -1, HUD_TEXT_SIZE).x
	return " ".repeat(ceili((Glyph.SIZE + UI.SPACE_XS) / maxf(space, 1)))

func _place_slot_glyph(index: int) -> void:
	var label := slots[index]
	var lines := label.text.split("\n")
	if lines.size() != 2: return
	var font := label.get_theme_font("font")
	var line_height := font.get_height(HUD_TEXT_SIZE)
	var line_index := 0 if _compact_slots else 1
	var width := font.get_string_size(lines[line_index], HORIZONTAL_ALIGNMENT_LEFT, -1, HUD_TEXT_SIZE).x
	var indent := font.get_string_size(_glyph_indent(label), HORIZONTAL_ALIGNMENT_LEFT, -1, HUD_TEXT_SIZE).x
	slot_glyphs[index].size = Vector2(Glyph.SIZE, Glyph.SIZE)
	slot_glyphs[index].position = Vector2((label.size.x-width+indent-Glyph.SIZE)*.5, (label.size.y-Glyph.SIZE+line_height*(-1 if _compact_slots else 1))*.5)
func configure(value: Node3D) -> void:
	runtime = value
	_refresh()
func _process(delta: float) -> void:
	# Authority can expire a ward or change life between slot-format updates.
	# Critical status must describe that state on the very next rendered frame.
	var availability := _availability()
	var feedback := _action_feedback(availability)
	_refresh_vitals(availability, feedback)
	clock += delta
	if clock >= SLOT_REFRESH_SECONDS or feedback.signature != _last_action_signature:
		clock = 0
		_refresh_slots(availability, feedback)
	_last_availability = availability
	_last_action_signature = feedback.signature
func _refresh() -> void:
	var availability := _availability()
	var feedback := _action_feedback(availability)
	_refresh_vitals(availability, feedback)
	_refresh_slots(availability, feedback)
	_last_availability = availability
	_last_action_signature = feedback.signature
func _availability() -> StringName:
	if not is_inside_tree(): return &"unavailable"
	if not is_instance_valid(runtime) or not runtime.is_inside_tree() or runtime.is_queued_for_deletion() or not runtime.configured: return &"unavailable"
	for node in [runtime.vitals, runtime.kit, runtime.player, runtime.army]:
		if not is_instance_valid(node): return &"unavailable"
	if not String(runtime.army.winner).is_empty(): return &"ended"
	if not runtime.vitals.alive: return &"returning"
	if runtime.suspended or get_tree().paused: return &"paused"
	if not runtime.player.active: return &"inactive"
	return &"active"

func _action_feedback(availability: StringName) -> Dictionary:
	var state: Dictionary = runtime.kit.report() if availability != &"unavailable" else {}
	var active_id := ""
	var phase := ""
	var queued_id := ""
	var locked: bool = availability == &"active" and state.get("action_locked", false)
	if locked:
		for cast in state.get("casts", []):
			if int(cast.cast_id) == int(state.active_cast_id):
				active_id = String(cast.ability_id)
				phase = "RECOVERING" if cast.released else "DRAWING"
				break
		if is_instance_valid(runtime.action_buffer):
			var pending: Dictionary = runtime.action_buffer.report().get("pending", {})
			if not pending.is_empty() and int(pending.generation) == int(state.generation) and int(pending.cast_id) == int(state.active_cast_id) and float(pending.expires_at) + 1e-8 >= float(state.elapsed):
				queued_id = String(pending.ability_id)
	var signature: Array = [availability, state.get("generation", -1), state.get("active_cast_id", 0), phase, queued_id]
	if availability != &"unavailable":
		signature.append(runtime.player.ammo)
		signature.append(runtime.player.reload_remaining > 0)
	for id in IDS: signature.append(float(state.get("cooldowns", {}).get(id, 0)) > .05)
	# Reload is a real mounted-input block; retain independent cooldown clocks.
	var reloading: bool = availability == &"active" and runtime.player.reload_remaining > 0 and not runtime._input_eligibility().get("eligible", false)
	return {"reloading":reloading,"state":state,"locked":locked,"active_id":active_id,"phase":phase,"queued_id":queued_id,"signature":signature}

func _ability_title(id: String) -> String:
	var index := IDS.find(id)
	return "Kodanda" if index == 0 else (String(Bindings.TITLES[ACTIONS[index]]) if index > 0 else id)

func _refresh_vitals(availability: StringName = &"", feedback: Dictionary = {}) -> void:
	if not life: return
	if availability.is_empty(): availability = _availability()
	if availability == &"unavailable":
		life.value = 0
		life_text.text = "—"
		note.text = "Practice unavailable"
		return
	var vitality: Dictionary = runtime.vitals.report()
	life.max_value = vitality.max_health
	life.value = vitality.health
	life_text.text = "%.0f / %.0f%s" % [vitality.health, vitality.max_health, " +%.0f" % vitality.shield if vitality.shield > 0 else ""]
	match availability:
		&"ended":
			var winner := String(runtime.army.winner)
			note.text = "Round ended · " + ("Draw" if winner == "draw" else winner.capitalize() + " victory")
		&"returning": note.text = "RETURNING IN %.1fs" % vitality.respawn_remaining
		&"paused": note.text = "Practice paused"
		_:
			if feedback.is_empty(): feedback = _action_feedback(availability)
			if not String(feedback.phase).is_empty():
				note.text = _ability_title(feedback.active_id) + " · " + String(feedback.phase)
				if not String(feedback.queued_id).is_empty(): note.text += " · " + _ability_title(feedback.queued_id) + " QUEUED"
			elif feedback.reloading: note.text = "Reloading bow"
			else: note.text = runtime.notice
	_layout_status_notice()
func _refresh_slots(availability: StringName = &"", feedback: Dictionary = {}) -> void:
	if not life: return
	if availability.is_empty(): availability = _availability()
	if feedback.is_empty(): feedback = _action_feedback(availability)
	var state: Dictionary = feedback.state
	for i in IDS.size():
		var cooldown := float(state.get("cooldowns", {}).get(IDS[i], 0))
		var status := "%.1fs" % cooldown if cooldown > .05 else "READY"
		if availability != &"active": status = "—"
		elif IDS[i] == "kodanda": status = "%d / %d" % [runtime.player.ammo, runtime.player.MAGAZINE] if runtime.player.reload_remaining <= 0 else "RELOADING"
		elif feedback.reloading and cooldown <= .05: status = "BUSY"
		if availability == &"active" and feedback.locked:
			if IDS[i] == feedback.queued_id: status = "QUEUED"
			elif IDS[i] != feedback.active_id and cooldown <= .05:
				status = "BUSY %d/%d" % [runtime.player.ammo, runtime.player.MAGAZINE] if i == 0 and runtime.player.reload_remaining <= 0 else "BUSY"
		var title := "Kodanda" if i == 0 else String(Bindings.TITLES[ACTIONS[i]])
		slots[i].text = "%s%s\n%s" % [_glyph_indent(slots[i]), Bindings.label(ACTIONS[i]), status] if _compact_slots else "%s  ·  %s\n%s%s" % [Bindings.label(ACTIONS[i]), status, _glyph_indent(slots[i]), title]
		slot_cards[i].tooltip_text = "%s · %s · %s" % [Bindings.label(ACTIONS[i]), title, status]
		var waiting: bool = cooldown > .05 or feedback.locked or feedback.reloading
		slots[i].add_theme_color_override("font_color", UI.MUTED if availability != &"active" else (UI.MIST if waiting else UI.CREAM))
		var visual_state: StringName = &"unavailable" if availability != &"active" else (&"cooling" if waiting else &"ready")
		slot_glyphs[i].present(IDS[i], visual_state)
		_place_slot_glyph(i)
		if _slot_states[i] != visual_state:
			_slot_states[i] = visual_state
			slot_cards[i].add_theme_stylebox_override("panel", _slot_surface(visual_state))
