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
var _identity_gap: Control
var _footer_gap: Control
var _identity: VBoxContainer
var _practice_prompt: Label

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
	texture.gradient.offsets = PackedFloat32Array([0, .32, .45, .64, 1])
	texture.gradient.colors = PackedColorArray([Color(HeroUITheme.DEEP,.98), Color(HeroUITheme.DEEP,.95), Color(HeroUITheme.DEEP,.62), Color(HeroUITheme.DEEP,0), Color(HeroUITheme.DEEP,0)])
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
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 0)
	scroll.add_child(content)
	_identity = VBoxContainer.new()
	_identity.name = "Identity"
	_identity.add_theme_constant_override("separation", 0)
	content.add_child(_identity)
	title_wordmark = HeroUITheme.label("YUGA", HeroUITheme.TYPE_LAUNCH_WORDMARK)
	title_wordmark.name = "Wordmark"
	title_wordmark.add_theme_font_override("font", HeroUITheme.display_font())
	_identity.add_child(title_wordmark)
	_subtitle = HeroUITheme.label("RAMA  /  THE SOLAR ARCHER", HeroUITheme.TYPE_CAPTION, HeroUITheme.GOLD)
	_identity.add_child(_subtitle)
	_identity_gap = Control.new()
	_identity_gap.name = "IdentityBreathingRoom"
	_identity_gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(_identity_gap)
	var decision := VBoxContainer.new()
	decision.name = "PracticeDecision"
	decision.add_theme_constant_override("separation", HeroUITheme.SPACE_MD)
	content.add_child(decision)
	var choices := VBoxContainer.new()
	choices.name = "ModeChoice"
	choices.add_theme_constant_override("separation", HeroUITheme.SPACE_SM)
	decision.add_child(choices)
	_practice_prompt = HeroUITheme.label("CHOOSE A PRACTICE", HeroUITheme.TYPE_CAPTION, HeroUITheme.MIST)
	choices.add_child(_practice_prompt)
	var modes := HBoxContainer.new()
	modes.name = "PracticeModes"
	modes.add_theme_constant_override("separation", HeroUITheme.SPACE_SM)
	choices.add_child(modes)
	world_mode_button = _button("Confluence", "ConfluenceMode", func(): set_mode(MODE_WORLD), &"selected" if selected_mode == MODE_WORLD else &"secondary")
	train_mode_button = _button("Bow training", "TrainingMode", func(): set_mode(MODE_TRAIN), &"selected" if selected_mode == MODE_TRAIN else &"secondary")
	for mode_button in [world_mode_button, train_mode_button]:
		mode_button.toggle_mode = true
		mode_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		modes.add_child(mode_button)
	var description := VBoxContainer.new()
	description.name = "ModeDescription"
	description.add_theme_constant_override("separation", 6)
	decision.add_child(description)
	mode_title = HeroUITheme.label("", HeroUITheme.TYPE_LAUNCH_PRACTICE)
	mode_title.name = "ModeTitle"
	mode_title.add_theme_font_override("font", HeroUITheme.display_font())
	description.add_child(mode_title)
	mode_description = HeroUITheme.label("", HeroUITheme.TYPE_BODY, HeroUITheme.MIST)
	mode_description.name = "ModeDescriptionText"
	mode_description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.add_child(mode_description)
	# Stable automation ID retained for the selected-mode primary action.
	primary_button = _button("", "ExploreConfluence", _launch, &"primary")
	primary_button.custom_minimum_size.y = 56
	decision.add_child(primary_button)
	_footer_gap = Control.new()
	_footer_gap.name = "FooterBreathingRoom"
	_footer_gap.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_footer_gap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	content.add_child(_footer_gap)
	var footer := VBoxContainer.new()
	footer.name = "LaunchFooter"
	footer.add_theme_constant_override("separation", HeroUITheme.SPACE_XS)
	content.add_child(footer)
	var secondary := HBoxContainer.new()
	secondary.name = "LearnAndWatch"
	secondary.add_theme_constant_override("separation", HeroUITheme.SPACE_SM)
	footer.add_child(secondary)
	guide_button = _button("Rama’s abilities", "RamaAbilities", func(): _emit_utility("guide"), &"utility")
	film_button = _button("Watch duel", "WatchConfluenceDuel", func(): _emit_utility("film"), &"utility")
	for secondary_button in [guide_button, film_button]:
		secondary_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		secondary.add_child(secondary_button)
	footer.add_child(HSeparator.new())
	var utilities := HBoxContainer.new()
	utilities.name = "TitleUtilities"
	utilities.add_theme_constant_override("separation", HeroUITheme.SPACE_SM)
	footer.add_child(utilities)
	for entry in [{"text":"Help", "action":"help"}, {"text":"Settings", "action":"settings"}, {"text":"Quit", "action":"quit"}]:
		var utility := _button(entry.text, entry.text, _emit_utility.bind(entry.action), &"utility")
		utility.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		utilities.add_child(utility)
	menu_hint = HeroUITheme.label("Offline practice  ·  F2 help  ·  F3 abilities", HeroUITheme.TYPE_CAPTION, HeroUITheme.MIST)
	menu_hint.name = "LaunchStatus"
	menu_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	footer.add_child(menu_hint)
	_connect_focus_order()

func _button(text: String, node_name: String, callback: Callable, role: StringName = &"secondary") -> Button:
	var result := Button.new()
	result.name = node_name
	result.text = text
	HeroUITheme.button_variant(result, role)
	# Flat launcher navigation keeps its native hover/focus/disabled behavior.
	# Other screens retain the shared opaque utility surfaces.
	result.flat = role == &"utility"
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
	var width := minf(column_width, size.x - inset * 2)
	var top := 24.0 if _compact else 42.0
	var bottom := top
	var short_canvas := size.y < 420
	title_wordmark.add_theme_font_size_override("font_size", HeroUITheme.TYPE_LAUNCH_WORDMARK_COMPACT if _compact else HeroUITheme.TYPE_LAUNCH_WORDMARK)
	mode_title.add_theme_font_size_override("font_size", HeroUITheme.TYPE_LAUNCH_PRACTICE_COMPACT if _compact else HeroUITheme.TYPE_LAUNCH_PRACTICE)
	# At200% the identity must not be scrolled out by initial primary focus.
	# Named mode buttons and the named action already identify the selection;
	# remove only their repeated headings, retaining readable type and copy.
	_practice_prompt.visible = not short_canvas
	mode_title.visible = not short_canvas
	_identity_gap.visible = not short_canvas
	if short_canvas:
		if _identity.get_parent() != self: _identity.reparent(self)
		_identity.position = Vector2(inset, top)
		_identity.size = Vector2(width, _identity.get_combined_minimum_size().y)
		top += _identity.size.y + HeroUITheme.SPACE_MD
	else:
		if _identity.get_parent() != content:
			_identity.reparent(content)
			content.move_child(_identity, 0)
	card.position = Vector2(inset, top)
	card.size = Vector2(width, maxf(100, size.y - top - bottom))
	_identity_gap.custom_minimum_size.y = HeroUITheme.SPACE_MD if _compact else HeroUITheme.SPACE_LG
	_footer_gap.custom_minimum_size.y = HeroUITheme.SPACE_MD if _compact else HeroUITheme.SPACE_LG
	queue_redraw()
	call_deferred("_reveal_resized_focus")

func _reveal_resized_focus() -> void:
	if not is_inside_tree() or is_queued_for_deletion(): return
	await get_tree().process_frame
	if not is_inside_tree() or is_queued_for_deletion() or not is_visible_in_tree(): return
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
	mode_description.text = "Offline practice with local armies, three lanes and capture relays as Rama." if world_selected else "Offline practice with Rama’s bow and four abilities against courtyard targets. Reset anytime."
	primary_button.text = ("Enter Confluence  →" if world_selected else "Begin bow training  →")
	var loading := launch_state == "loading"
	for action in _actions: action.disabled = loading
	if loading: primary_button.text = "Opening Confluence…" if world_selected else "Opening bow training…"
	menu_hint.text = _status_message if not _status_message.is_empty() else ("Opening your local practice…" if loading else "Offline practice  ·  F2 help  ·  F3 abilities")
	if launch_state == "error" and _status_message.is_empty(): menu_hint.text = "Practice could not open. Try again or choose another mode."
	menu_hint.add_theme_color_override("font_color", HeroUITheme.GOLD if launch_state == "error" else HeroUITheme.MIST)

func _style_mode(button: Button, selected: bool) -> void:
	var role: StringName = &"selected" if selected else &"secondary"
	if button.theme_type_variation != HeroUITheme.BUTTON_TYPES[role]:
		HeroUITheme.button_variant(button, role)
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
	if not is_inside_tree() or is_queued_for_deletion() or not is_visible_in_tree(): return
	var focused := get_viewport().gui_get_focus_owner()
	# A host may already have restored the Settings/Help/Guide opener.
	if focused != null and is_ancestor_of(focused): return
	focus_primary()

func snapshot() -> Dictionary:
	return {"selected_mode":selected_mode, "launch_state":launch_state, "offline":true, "compact":_compact, "status":menu_hint.text if is_instance_valid(menu_hint) else _status_message}
