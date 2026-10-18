extends Control
## Five fixed ability slots. Cooldowns and health read the actual simulation.
const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const Glyph = preload("res://scripts/rama_ability_glyph.gd")
const IDS := ["kodanda","piercing_dawn","measured_step","guardian_circle","dawn_volley"]
const ACTIONS := ["fire","pulse","dash","guardian_circle","ultimate"]
const HUD_TEXT_SIZE := UI.TYPE_HUD
const HUD_WIDTH := 820.0
const HUD_HEIGHT := 112.0
const SLOT_REFRESH_SECONDS := .08
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
	var status_column := VBoxContainer.new()
	status_column.add_theme_constant_override("separation", UI.SPACE_XS)
	status_panel.add_child(status_column)
	note = UI.label("Practice unavailable", UI.TYPE_HUD_DETAIL)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note.clip_text = true
	note.max_lines_visible = 1
	note.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	status_column.add_child(note)
	var health_row := HBoxContainer.new()
	status_column.add_child(health_row)
	life = ProgressBar.new(); life.show_percentage = false
	life.max_value = 1; life.value = 0
	life.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	life.custom_minimum_size.y = 10
	var fill := StyleBoxFlat.new(); fill.bg_color = UI.MARSH
	fill.set_corner_radius_all(UI.CORNER)
	life.add_theme_stylebox_override("fill", fill)
	health_row.add_child(life)
	life_text = UI.label("—", HUD_TEXT_SIZE)
	health_row.add_child(life_text)
	var row := HBoxContainer.new(); row.add_theme_constant_override("separation", UI.SPACE_XS)
	column.add_child(row)
	for i in IDS.size():
		var card := PanelContainer.new()
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.custom_minimum_size = Vector2(156, 56)
		card.add_theme_stylebox_override("panel", _slot_surface(&"unavailable"))
		row.add_child(card)
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
	_refresh()

func _slot_surface(state: StringName) -> StyleBoxFlat:
	var surface := UI.hud_panel_style(state)
	surface.content_margin_top = UI.SPACE_XS
	surface.content_margin_bottom = UI.SPACE_XS
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
	var width := font.get_string_size(lines[1], HORIZONTAL_ALIGNMENT_LEFT, -1, HUD_TEXT_SIZE).x
	var indent := font.get_string_size(_glyph_indent(label), HORIZONTAL_ALIGNMENT_LEFT, -1, HUD_TEXT_SIZE).x
	slot_glyphs[index].size = Vector2(Glyph.SIZE, Glyph.SIZE)
	slot_glyphs[index].position = Vector2((label.size.x-width+indent-Glyph.SIZE)*.5, (label.size.y-Glyph.SIZE+line_height)*.5)
func configure(value: Node3D) -> void:
	runtime = value
	_refresh()
func _process(delta: float) -> void:
	# Authority can expire a ward or change life between slot-format updates.
	# Critical status must describe that state on the very next rendered frame.
	var availability := _availability()
	_refresh_vitals(availability)
	clock += delta
	if clock >= SLOT_REFRESH_SECONDS or availability != _last_availability:
		clock = 0
		_refresh_slots(availability)
	_last_availability = availability
func _refresh() -> void:
	var availability := _availability()
	_refresh_vitals(availability)
	_refresh_slots(availability)
	_last_availability = availability
func _availability() -> StringName:
	if not is_inside_tree(): return &"unavailable"
	if not is_instance_valid(runtime) or not runtime.configured: return &"unavailable"
	for node in [runtime.vitals, runtime.kit, runtime.player, runtime.army]:
		if not is_instance_valid(node): return &"unavailable"
	if not String(runtime.army.winner).is_empty(): return &"ended"
	if not runtime.vitals.alive: return &"returning"
	if runtime.suspended or get_tree().paused: return &"paused"
	if not runtime.player.active: return &"inactive"
	return &"active"
func _refresh_vitals(availability: StringName = &"") -> void:
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
		_: note.text = runtime.notice
func _refresh_slots(availability: StringName = &"") -> void:
	if not life: return
	if availability.is_empty(): availability = _availability()
	var state: Dictionary = runtime.kit.report() if availability != &"unavailable" else {}
	for i in IDS.size():
		var cooldown := float(state.get("cooldowns", {}).get(IDS[i], 0))
		var status := "%.1fs" % cooldown if cooldown > .05 else "READY"
		if availability != &"active": status = "—"
		elif IDS[i] == "kodanda": status = "%d / %d" % [runtime.player.ammo, runtime.player.MAGAZINE] if runtime.player.reload_remaining <= 0 else "RELOADING"
		var title := "Kodanda" if i == 0 else String(Bindings.TITLES[ACTIONS[i]])
		slots[i].text = "%s  ·  %s\n%s%s" % [Bindings.label(ACTIONS[i]), status, _glyph_indent(slots[i]), title]
		var waiting: bool = cooldown > .05 or (i == 0 and availability == &"active" and runtime.player.reload_remaining > 0)
		slots[i].add_theme_color_override("font_color", UI.MUTED if availability != &"active" else (UI.MIST if waiting else UI.CREAM))
		var visual_state: StringName = &"unavailable" if availability != &"active" else (&"cooling" if waiting else &"ready")
		slot_glyphs[i].present(IDS[i], visual_state)
		_place_slot_glyph(i)
		if _slot_states[i] != visual_state:
			_slot_states[i] = visual_state
			slot_cards[i].add_theme_stylebox_override("panel", _slot_surface(visual_state))
