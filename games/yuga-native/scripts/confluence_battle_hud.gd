extends Control
## Presentation only: actual core pressure, elapsed time and match-local wallet.
signal shop_requested
const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var host: Node
var top: PanelContainer
var clock: Label
var sun_value: Label
var moon_value: Label
var sun_bar: ProgressBar
var moon_bar: ProgressBar
var shop_button: Button
var active_layout := false
var _clock := 0.0

func _ready() -> void:
	name = "BattleDashboard"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	size = Vector2.ZERO
	top = PanelContainer.new()
	top.add_theme_stylebox_override("panel", UI.hud_panel_style(&"quiet", 12))
	add_child(top)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 18)
	top.add_child(row)
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(left)
	sun_value = UI.label("SUN CORE · 100", 15, UI.GOLD)
	left.add_child(sun_value)
	sun_bar = _bar(left, UI.GOLD)
	var middle := VBoxContainer.new()
	middle.custom_minimum_size.x = 116
	row.add_child(middle)
	clock = UI.label("00:00", 24, UI.CREAM)
	clock.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	middle.add_child(clock)
	var scope := UI.label("OFFLINE PRACTICE", 11, UI.MIST)
	scope.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	middle.add_child(scope)
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(right)
	moon_value = UI.label("MOON CORE · 100", 15, UI.MOON)
	moon_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(moon_value)
	moon_bar = _bar(right, UI.MOON)
	shop_button = Button.new()
	shop_button.name = "OpenFieldShop"
	shop_button.custom_minimum_size = Vector2(216, 58)
	UI.button(shop_button)
	shop_button.add_theme_font_size_override("font_size", 14)
	shop_button.pressed.connect(func(): shop_requested.emit())
	add_child(shop_button)

func _bar(parent: Control, color: Color) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.custom_minimum_size = Vector2(140, 8)
	bar.show_percentage = false
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	bar.add_theme_stylebox_override("fill", fill)
	parent.add_child(bar)
	return bar

func configure(value: Node) -> void:
	host = value
	refresh()

func apply_layout() -> bool:
	if not is_instance_valid(host) or not is_instance_valid(top): return false
	var screen := get_viewport_rect().size
	active_layout = screen.x >= 1180 and screen.y >= 650 and not host.overview
	visible = active_layout
	if not active_layout: return false
	var title: Control = host.hud.get_node("TitleCard")
	var relay: Control = host.hud.get_node("RelayStatus")
	var controls: Control = host.hud.get_node("ControlsCard")
	var traversal: Control = host.hud.get_node("TraversalStatus")
	for card in [title, relay, controls, traversal, host.map_control]:
		card.show()
		card.set_anchors_preset(Control.PRESET_TOP_LEFT)
	host.status_label.hide()
	host.score_label.hide()
	host.lane_label.hide()
	title.custom_minimum_size = Vector2(264, 112)
	title.size = title.custom_minimum_size
	title.position = Vector2(20, 20)
	top.position = Vector2((screen.x - 580) / 2, 20)
	top.size = Vector2(580, 76)
	relay.custom_minimum_size = Vector2(430, 82)
	relay.size = relay.custom_minimum_size
	relay.position = Vector2((screen.x - 430) / 2, maxf(104, top.position.y + top.size.y + 12))
	controls.custom_minimum_size = Vector2(238, 72)
	controls.size = controls.custom_minimum_size
	controls.position = Vector2(20, maxf(148, title.position.y + title.size.y + 12))
	host.energy_bar.custom_minimum_size.x = 184
	host.goal_label.custom_minimum_size.x = 184
	traversal.custom_minimum_size = Vector2(216, 88 if host._traversal_idle else 116)
	traversal.size = traversal.custom_minimum_size
	var combat_top: float = screen.y + host.rama_hud.offset_top
	traversal.position = Vector2(20, combat_top - 12 - traversal.size.y)
	shop_button.position = Vector2(20, traversal.position.y - 70)
	var atlas: Control = host.map_control
	atlas.position = Vector2(screen.x - 216, combat_top - 308)
	atlas.size = Vector2(196, 296)
	atlas.footer_height = 48
	var legend: Label = atlas.get_node("AtlasLegend")
	legend.text = "● You · □ Relay\n%s Map & key" % Bindings.label("world_overview")
	legend.autowrap_mode = TextServer.AUTOWRAP_OFF
	legend.offset_top = -48
	legend.offset_bottom = -8
	atlas.queue_redraw()
	if is_instance_valid(host.compact_world_card): host.compact_world_card.hide()
	refresh()
	return true

func _process(delta: float) -> void:
	_clock += delta
	if visible and _clock >= .12:
		_clock = 0
		refresh()

func refresh() -> void:
	if not is_instance_valid(host) or not is_instance_valid(host.army) or not is_instance_valid(clock): return
	var battle: Dictionary = host.army.report()
	var cores: Dictionary = battle.get("cores", {})
	var sun_hp := float(cores.get("sun", 100))
	var moon_hp := float(cores.get("moon", 100))
	sun_bar.value = sun_hp
	moon_bar.value = moon_hp
	sun_value.text = "SUN CORE · %d" % ceili(sun_hp)
	moon_value.text = "MOON CORE · %d" % ceili(moon_hp)
	var seconds := maxi(0, floori(float(battle.get("elapsed", 0))))
	clock.text = "%02d:%02d" % [seconds / 60, seconds % 60]
	if is_instance_valid(host.field_shop):
		var wallet: Dictionary = host.field_shop.report()
		var hint := "Base services available"
		if not wallet.eligible:
			if not wallet.near_shop: hint = "Return to Sun base"
			elif wallet.reason == "Round has ended": hint = "Round complete"
			elif wallet.reason == "Wait until Rama has returned": hint = "Waiting for Rama's return"
			else: hint = "Open to view services"
		shop_button.text = "%s  FIELD SHOP   ·   %d GOLD\n%s" % [Bindings.label("open_field_shop"), int(wallet.wallet), hint]
		shop_button.tooltip_text = "Open the field shop. The battle keeps running. " + String(wallet.reason)

func report() -> Dictionary:
	return {"wide_layout": active_layout, "authority": "read-only army and shop reports", "elapsed_text": clock.text if clock else "", "shop_action": Bindings.label("open_field_shop")}
