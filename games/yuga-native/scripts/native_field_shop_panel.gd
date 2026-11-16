extends Control
## A live shop view. Only native_field_shop owns eligibility, spending and effects.
signal closed
const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var owner_shop: Node
var panel: PanelContainer
var wallet: Label
var location: Label
var receipt: Label
var close_button: Button
var scroll: ScrollContainer
var rows: Dictionary = {}
var _nonce := 0
var _epoch := -1
var _refresh_clock := 0.0
var _layout_queued := false

func _ready() -> void:
	name = "FieldShop"
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var shade := ColorRect.new()
	shade.color = Color(0.015, .025, .035, .78)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	panel = PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UI.panel_style(true, 20))
	add_child(panel)
	panel.minimum_size_changed.connect(_queue_layout)
	var frame := VBoxContainer.new()
	frame.add_theme_constant_override("separation", 12)
	panel.add_child(frame)
	scroll = ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.follow_focus = true
	frame.add_child(scroll)
	var column := VBoxContainer.new()
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	column.add_theme_constant_override("separation", 12)
	scroll.add_child(column)
	var heading := UI.label("SUN BASE  /  FIELD SHOP", 26, UI.GOLD)
	heading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(heading)
	var subtitle := UI.label("Original Confluence services · battle continues while you browse", 14, UI.MIST)
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(subtitle)
	wallet = UI.label("", 20, UI.CREAM)
	wallet.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(wallet)
	location = UI.label("", 14, UI.MIST)
	location.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(location)
	for id in ["heal", "arrows", "ward", "escort"]:
		var card := PanelContainer.new()
		card.add_theme_stylebox_override("panel", UI.hud_panel_style(&"quiet", 12))
		column.add_child(card)
		var line := HBoxContainer.new()
		line.add_theme_constant_override("separation", 14)
		card.add_child(line)
		var copy := VBoxContainer.new()
		copy.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		line.add_child(copy)
		var title := UI.label("", 18, UI.CREAM)
		title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		copy.add_child(title)
		var description := UI.label("", 14, UI.MIST)
		description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		copy.add_child(description)
		var reason := UI.label("", 13, UI.MIST)
		reason.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		copy.add_child(reason)
		var buy := Button.new()
		buy.name = "Buy_" + id
		buy.custom_minimum_size = Vector2(116, 58)
		UI.button(buy)
		buy.pressed.connect(_purchase.bind(id))
		line.add_child(buy)
		rows[id] = {"title":title, "description":description, "reason":reason, "button":buy}
	receipt = UI.label("No purchase yet. Services use match-local gold.", 14, UI.CREAM)
	receipt.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	frame.add_child(receipt)
	close_button = Button.new()
	close_button.text = "Return to battle\n%s / %s" % [Bindings.label("open_field_shop"), Bindings.label("pause_game")]
	close_button.custom_minimum_size.y = 60
	UI.button(close_button, true)
	close_button.pressed.connect(close)
	frame.add_child(close_button)
	resized.connect(_layout)
	_layout()
	hide()

func configure(value: Node) -> void:
	owner_shop = value
	refresh()

func _queue_layout() -> void:
	if _layout_queued: return
	_layout_queued = true
	call_deferred("_settle_layout")

func _settle_layout() -> void:
	_layout_queued = false
	_layout()

func _layout() -> void:
	if not panel: return
	var screen := get_viewport_rect().size
	panel.size = Vector2(minf(760, screen.x - 32), minf(640, screen.y - 32))
	panel.position = (screen - panel.size) / 2

func open() -> void:
	refresh()
	show()
	_layout()
	_queue_layout()
	close_button.grab_focus()

func close() -> void:
	if not visible: return
	hide()
	closed.emit()

func _unhandled_input(event: InputEvent) -> void:
	if not visible or (event is InputEventKey and event.echo): return
	if event.is_action_pressed("pause_game") or event.is_action_pressed("open_field_shop"):
		close()
		get_viewport().set_input_as_handled()

func _process(delta: float) -> void:
	_refresh_clock += delta
	if visible and _refresh_clock >= .1:
		_refresh_clock = 0
		refresh()

func refresh() -> void:
	if not is_instance_valid(owner_shop) or not is_instance_valid(wallet): return
	var state: Dictionary = owner_shop.report()
	if _epoch != int(state.epoch):
		_epoch = int(state.epoch)
		_nonce = 0
		receipt.text = "New round · field allowance restored."
	wallet.text = "%d GOLD   ·   %d earned   ·   %d spent" % [int(state.wallet), int(state.earned), int(state.spent)]
	location.text = "At Sun base · choose a service. You remain vulnerable." if state.eligible else String(state.reason)
	for item: Dictionary in state.catalog:
		if not rows.has(item.id): continue
		var row: Dictionary = rows[item.id]
		row.title.text = item.title
		row.description.text = item.description
		row.reason.text = "Ready" if item.available else String(item.disabled_reason)
		row.button.text = "%d GOLD\nBuy" % int(item.cost)
		row.button.disabled = not item.available
		row.button.tooltip_text = item.title + ": " + ("Purchase" if item.available else String(item.disabled_reason))

func _purchase(id: String) -> void:
	if not is_instance_valid(owner_shop): return
	_nonce += 1
	var result: Dictionary = owner_shop.purchase(id, _epoch, _nonce)
	receipt.text = ("Purchased · " if result.accepted else "Unavailable · ") + String(result.reason)
	refresh()

func report() -> Dictionary:
	return {"open": visible, "epoch":_epoch, "nonce":_nonce, "receipt":receipt.text if receipt else "", "authority":"native_field_shop"}
