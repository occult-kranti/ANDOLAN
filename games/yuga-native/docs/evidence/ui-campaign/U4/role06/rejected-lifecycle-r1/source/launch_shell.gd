extends Control
## Native title composition over the actual Rama portrait. The host owns scenes,
## dialogs and loading; this shell emits intent and never fabricates availability.

const HeroUITheme = preload("res://scripts/hero_ui_theme.gd")
const MODE_WORLD := "world"
const MODE_TRAIN := "train"
const WINDOW_MINIMUM := Vector2i(960, 540)

signal world_requested
signal train_requested
signal guide_requested
signal settings_requested
signal help_requested
signal quit_requested
signal film_requested
signal mode_changed(mode: String)

var selected_mode := MODE_WORLD
var launch_state := "ready"
var primary_button: Button
var world_mode_button: Button
var train_mode_button: Button
var guide_button: Button
var film_button: Button
var title_wordmark: Label
var menu_hint: Label
var mode_title: Label
var mode_description: Label
var card: PanelContainer
var scroll: ScrollContainer
var content: VBoxContainer
var _subtitle: Label
var _status_message := ""
var _actions: Array[Button] = []
var _compact := false

func _ready() -> void:
	# The native window must keep menu controls usable at the supported base size.
	get_window().min_size = get_window().min_size.max(WINDOW_MINIMUM)
	name = "MainMenu"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = HeroUITheme.create()
	_build()
	resized.connect(_layout)
	visibility_changed.connect(_on_visibility_changed)
	_layout()
	_refresh()

func _build() -> void:
	var wash := TextureRect.new()
	wash.name = "PortraitScrim"
	var texture := GradientTexture2D.new()
	texture.width = 1024
	texture.height = 1
	texture.fill_from = Vector2.ZERO
	texture.fill_to = Vector2.RIGHT
	texture.gradient = Gradient.new()
	texture.gradient.offsets = PackedFloat32Array([0, .32, .47, .66, 1])
	texture.gradient.colors = PackedColorArray([Color(.025,.035,.09,.98), Color(.025,.035,.09,.95), Color(.025,.035,.09,.65), Color(.025,.035,.09,0), Color(.025,.035,.09,0)])
	wash.texture = texture
	wash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	wash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(wash)
	card = PanelContainer.new()
	card.name = "Card"
	card.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	add_child(card)
	scroll = ScrollContainer.new()
	scroll.name = "Scroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.follow_focus = true
	card.add_child(scroll)
	content = VBoxContainer.new()
	content.name = "Content"
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 10)
	scroll.add_child(content)
	var identity := VBoxContainer.new()
	identity.name = "Identity"
	identity.add_theme_constant_override("separation", 0)
	content.add_child(identity)
	title_wordmark = HeroUITheme.label("YUGA", 64)
	title_wordmark.name = "Wordmark"
	title_wordmark.add_theme_font_override("font", HeroUITheme.display_font())
	identity.add_child(title_wordmark)
	_subtitle = HeroUITheme.label("RAMA  /  THE SOLAR ARCHER", 14, HeroUITheme.GOLD)
	identity.add_child(_subtitle)
	content.add_child(HSeparator.new())
	var choices := VBoxContainer.new()
	choices.name = "ModeChoice"
	choices.add_theme_constant_override("separation", 8)
	content.add_child(choices)
	choices.add_child(HeroUITheme.label("CHOOSE YOUR PRACTICE", 14, HeroUITheme.MIST))
	var modes := HBoxContainer.new()
	modes.name = "PracticeModes"
	modes.add_theme_constant_override("separation", 8)
	choices.add_child(modes)
	world_mode_button = _button("Confluence", "ConfluenceMode", func(): set_mode(MODE_WORLD))
	train_mode_button = _button("Bow training", "TrainingMode", func(): set_mode(MODE_TRAIN))
	for mode_button in [world_mode_button, train_mode_button]:
		mode_button.toggle_mode = true
		mode_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		modes.add_child(mode_button)
	var description := VBoxContainer.new()
	description.name = "ModeDescription"
	description.add_theme_constant_override("separation", 6)
	content.add_child(description)
	mode_title = HeroUITheme.label("", 30)
	mode_title.name = "ModeTitle"
	description.add_child(mode_title)
	mode_description = HeroUITheme.label("", 17, HeroUITheme.MIST)
	mode_description.name = "ModeDescriptionText"
	mode_description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.add_child(mode_description)
	# Stable automation ID retained for the selected-mode primary action.
	primary_button = _button("", "ExploreConfluence", _launch)
	HeroUITheme.button(primary_button, true)
	primary_button.custom_minimum_size.y = 54
	content.add_child(primary_button)
	var secondary := HBoxContainer.new()
	secondary.name = "LearnAndWatch"
	secondary.add_theme_constant_override("separation", 8)
	content.add_child(secondary)
	guide_button = _button("Rama’s abilities", "RamaAbilities", func(): _emit_utility("guide"))
	film_button = _button("Watch duel", "WatchConfluenceDuel", func(): _emit_utility("film"))
	for secondary_button in [guide_button, film_button]:
		secondary_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		HeroUITheme.button(secondary_button, false, true)
		secondary.add_child(secondary_button)
	content.add_child(HSeparator.new())
	var utilities := HBoxContainer.new()
	utilities.name = "TitleUtilities"
	utilities.add_theme_constant_override("separation", 8)
	content.add_child(utilities)
	for entry in [{"text":"Help", "action":"help"}, {"text":"Settings", "action":"settings"}, {"text":"Quit", "action":"quit"}]:
		var utility := _button(entry.text, entry.text, _emit_utility.bind(entry.action))
		utility.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		HeroUITheme.button(utility, false, true)
		utilities.add_child(utility)
	menu_hint = HeroUITheme.label("Offline practice  ·  F2 help  ·  F3 abilities", 14, HeroUITheme.MIST)
	menu_hint.name = "LaunchStatus"
	menu_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(menu_hint)
	_connect_focus_order()

func _button(text: String, node_name: String, callback: Callable) -> Button:
	var result := Button.new()
	result.name = node_name
	result.text = text
	HeroUITheme.button(result)
	result.pressed.connect(callback)
	_actions.append(result)
	return result

func _connect_focus_order() -> void:
	for index in range(_actions.size()):
		var action := _actions[index]
		action.focus_next = action.get_path_to(_actions[(index + 1) % _actions.size()])
		action.focus_previous = action.get_path_to(_actions[(index - 1 + _actions.size()) % _actions.size()])

func _layout() -> void:
	if not is_instance_valid(card): return
	_compact = size.y < 680 or size.x < 1100
	var inset := 28.0 if _compact else 52.0
	var column_width := clampf(size.x * .35, 364, 438)
	# Reflow the column rather than scaling text; shorter windows can scroll.
	card.position = Vector2(inset, 24 if _compact else 42)
	card.size = Vector2(minf(column_width, size.x - inset * 2), maxf(100, size.y - card.position.y * 2))
	title_wordmark.add_theme_font_size_override("font_size", 44 if _compact else 64)
	mode_title.add_theme_font_size_override("font_size", 24 if _compact else 30)
	content.add_theme_constant_override("separation", 8 if _compact else 12)
	queue_redraw()
	call_deferred("_reveal_resized_focus")

func _reveal_resized_focus() -> void:
	await get_tree().process_frame
	if not is_visible_in_tree(): return
	var focused := get_viewport().gui_get_focus_owner()
	if is_instance_valid(focused) and scroll.is_ancestor_of(focused):
		scroll.ensure_control_visible(focused)

func set_mode(mode: String) -> bool:
	if mode not in [MODE_WORLD, MODE_TRAIN] or launch_state == "loading": return false
	selected_mode = mode
	if launch_state == "error":
		launch_state = "ready"
		_status_message = ""
	if is_instance_valid(primary_button): _refresh()
	mode_changed.emit(selected_mode)
	return true

func set_launch_state(state: String, message: String = "") -> bool:
	if state not in ["ready", "loading", "error"]: return false
	launch_state = state
	_status_message = message
	if is_instance_valid(primary_button): _refresh()
	return true

func _refresh() -> void:
	var world_selected := selected_mode == MODE_WORLD
	world_mode_button.set_pressed_no_signal(world_selected)
	train_mode_button.set_pressed_no_signal(not world_selected)
	for item in [world_mode_button, train_mode_button]:
		_style_mode(item, item.button_pressed)
	mode_title.text = "Confluence" if world_selected else "Bow training"
	mode_description.text = "Explore three lanes, join local army battles, and capture relays as Rama." if world_selected else "Practice Rama’s bow and four abilities against courtyard targets. Reset and practice at your own pace."
	primary_button.text = ("Enter Confluence  →" if world_selected else "Begin bow training  →")
	var loading := launch_state == "loading"
	for action in _actions: action.disabled = loading
	if loading: primary_button.text = "Opening Confluence…" if world_selected else "Opening bow training…"
	menu_hint.text = _status_message if not _status_message.is_empty() else ("Opening your local practice…" if loading else "Offline practice  ·  F2 help  ·  F3 abilities")
	if launch_state == "error" and _status_message.is_empty(): menu_hint.text = "Practice could not open. Try again or choose another mode."
	menu_hint.add_theme_color_override("font_color", HeroUITheme.GOLD if launch_state == "error" else HeroUITheme.MIST)

func _style_mode(button: Button, selected: bool) -> void:
	HeroUITheme.button_variant(button, &"selected" if selected else &"secondary")
	button.tooltip_text = "Selected practice: " + button.text if selected else "Choose " + button.text

func _launch() -> void:
	if launch_state == "loading" or not is_visible_in_tree(): return
	if selected_mode == MODE_WORLD: world_requested.emit()
	else: train_requested.emit()

func _emit_utility(action: String) -> void:
	if launch_state == "loading" or not is_visible_in_tree(): return
	match action:
		"guide": guide_requested.emit()
		"film": film_requested.emit()
		"help": help_requested.emit()
		"settings": settings_requested.emit()
		"quit": quit_requested.emit()

func focus_primary() -> void:
	if is_instance_valid(primary_button) and not primary_button.disabled and is_visible_in_tree():
		primary_button.grab_focus()
		scroll.ensure_control_visible(primary_button)

func _on_visibility_changed() -> void:
	if is_visible_in_tree(): call_deferred("_focus_when_unclaimed")

func _focus_when_unclaimed() -> void:
	var focused := get_viewport().gui_get_focus_owner()
	# A host may already have restored the Settings/Help/Guide opener.
	if focused != null and is_ancestor_of(focused): return
	focus_primary()

func snapshot() -> Dictionary:
	return {"selected_mode":selected_mode, "launch_state":launch_state, "offline":true, "compact":_compact, "status":menu_hint.text if is_instance_valid(menu_hint) else _status_message}
