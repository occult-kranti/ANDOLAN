extends Control
## Five fixed ability slots. Cooldowns and health read the actual simulation.
const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const IDS := ["kodanda","piercing_dawn","measured_step","guardian_circle","dawn_volley"]
const ACTIONS := ["fire","pulse","dash","guardian_circle","ultimate"]
const LABELS := ["Kodanda","Piercing Dawn","Measured Step","Guardian Circle","Dawn Volley"]
var runtime: Node3D
var life: ProgressBar
var life_text: Label
var note: Label
var slots: Array[Label] = []
var slot_cards: Array[PanelContainer] = []
var clock := 0.0
func _ready() -> void:
	name = "RamaHeroHUD"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	offset_left = -300; offset_right = 300; offset_top = -121; offset_bottom = -18
	theme = UI.create()
	var column := VBoxContainer.new()
	column.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	column.add_theme_constant_override("separation", 5)
	add_child(column)
	note = UI.label("Rama · steady the horizon", 12, UI.CREAM)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note.clip_text = true
	column.add_child(note)
	var health_row := HBoxContainer.new()
	column.add_child(health_row)
	life = ProgressBar.new(); life.show_percentage = false
	life.max_value = 300; life.value = 300
	life.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	life.custom_minimum_size.y = 10
	var fill := StyleBoxFlat.new(); fill.bg_color = Color("72c4b6")
	fill.set_corner_radius_all(3)
	life.add_theme_stylebox_override("fill", fill)
	health_row.add_child(life)
	life_text = UI.label("300 / 300", 12, UI.CREAM)
	health_row.add_child(life_text)
	var row := HBoxContainer.new(); row.add_theme_constant_override("separation", 5)
	column.add_child(row)
	for i in IDS.size():
		var card := PanelContainer.new()
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.custom_minimum_size = Vector2(116, 56)
		card.add_theme_stylebox_override("panel", UI.panel_style(false, 8))
		row.add_child(card)
		var label := UI.label("", 12, UI.CREAM)
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		card.add_child(label); slots.append(label); slot_cards.append(card)
	_refresh()
func configure(value: Node3D) -> void:
	runtime = value
	_refresh()
func _process(delta: float) -> void:
	# Authority can expire a ward or change life between slot-format updates.
	# Critical status must describe that state on the very next rendered frame.
	_refresh_vitals()
	clock += delta
	if clock >= .08: clock = 0; _refresh_slots()
func _refresh() -> void:
	_refresh_vitals()
	_refresh_slots()
func _refresh_vitals() -> void:
	if not life or not runtime or not runtime.configured: return
	var vitality: Dictionary = runtime.vitals.report()
	life.max_value = vitality.max_health
	life.value = vitality.health
	life_text.text = "%.0f / %.0f%s" % [vitality.health, vitality.max_health, " +%.0f" % vitality.shield if vitality.shield > 0 else ""]
	note.text = runtime.notice if vitality.alive else "RETURNING IN %.1fs" % vitality.respawn_remaining
func _refresh_slots() -> void:
	if not life or not runtime or not runtime.configured: return
	var state: Dictionary = runtime.kit.report()
	for i in IDS.size():
		var cooldown := float(state.cooldowns.get(IDS[i], 0))
		var status := "%.1fs" % cooldown if cooldown > .05 else "READY"
		if IDS[i] == "kodanda": status = "%d / 12" % runtime.player.ammo if runtime.player.reload_remaining <= 0 else "RELOADING"
		slots[i].text = "%s  ·  %s\n%s" % [Bindings.label(ACTIONS[i]), status, LABELS[i]]
		slots[i].modulate = Color("bdc7cd") if cooldown > .05 else Color.WHITE
