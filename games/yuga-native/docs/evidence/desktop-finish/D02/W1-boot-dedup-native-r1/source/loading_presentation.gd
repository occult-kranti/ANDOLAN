extends Control
## Presentation only. The transition controller owns every navigation decision.
const UI = preload("res://scripts/hero_ui_theme.gd")
const CONTEXT := {&"courtyard":"PRACTICE MENU", &"confluence":"OFFLINE LANES", &"combat_film":"SCRIPTED DUEL"}
const STAGES := {&"queued":"STARTING", &"loading":"LOADING SCENE RESOURCES", &"constructing":"PREPARING SCENE AND ACTORS", &"error":"LOADING STOPPED", &"done":"SCENE MOUNTED", &"cancelled":"LOADING CANCELLED"}

var card: PanelContainer
var heading: Label
var detail: Label
var progress_bar: ProgressBar
var retry_button: Button
var back_button: Button
var context: Label
var stage: Label
var progress_scope: Label
var body_scroll: ScrollContainer
var actions: HBoxContainer
var _source: WeakRef

func _ready() -> void:
	name = "LoadingPresentation"
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	resized.connect(_layout)
	_layout()

func bind_transition(source: Control) -> void:
	_source = weakref(source)
	if not source.phase_changed.is_connected(_on_phase_changed):
		source.phase_changed.connect(_on_phase_changed)

func _on_phase_changed(phase: StringName, _message: String, progress: float) -> void:
	var source: Control = _source.get_ref() if _source != null else null
	if not is_instance_valid(source): return
	present_phase(phase, source.destination, progress)

func present_phase(phase: StringName, destination: StringName, progress: float) -> void:
	context.text = CONTEXT.get(destination, "LOCAL SCENE")
	stage.text = STAGES.get(phase, "PREPARING")
	if phase == &"loading" and is_finite(progress) and progress >= 0 and progress <= 1:
		progress_scope.text = "Resources · %d%%  —  scene preparation follows" % roundi(progress * 100)
	elif phase == &"constructing":
		progress_scope.text = "Scene and actors are being prepared. No overall percentage is available."
	elif phase == &"error":
		# The specific controller error above already explains recovery.
		progress_scope.text = ""
	elif phase == &"loading":
		progress_scope.text = "Resource progress is unavailable."
	else:
		progress_scope.text = "Resource progress appears when loading starts."
	# Enabled/visible/focus state remains exclusively controller-owned.
	back_button.text = "Cancel loading" if phase in [&"queued", &"loading", &"constructing"] else "Back"

func _build() -> void:
	var veil := ColorRect.new()
	veil.name = "LoadingVeil"
	veil.color = Color(UI.DEEP, .98)
	veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(veil)
	card = PanelContainer.new()
	card.name = "LoadingCard"
	var surface := UI.panel_style(true)
	surface.border_color = UI.HUD_EDGE
	surface.border_width_top = 2
	card.add_theme_stylebox_override("panel", surface)
	add_child(card)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", UI.SPACE_MD)
	card.add_child(stack)
	body_scroll = ScrollContainer.new()
	body_scroll.name = "LoadingBody"
	body_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	stack.add_child(body_scroll)
	var body := VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", UI.SPACE_MD)
	body_scroll.add_child(body)
	var identity := HBoxContainer.new()
	identity.add_theme_constant_override("separation", UI.SPACE_LG)
	body.add_child(identity)
	var wordmark := UI.label("YUGA", UI.TYPE_TITLE, UI.GOLD)
	wordmark.add_theme_font_override("font", UI.display_font())
	identity.add_child(wordmark)
	context = UI.label("LOCAL SCENE", UI.TYPE_CAPTION, UI.MIST)
	context.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	context.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	context.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	context.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	identity.add_child(context)
	var rule := HSeparator.new()
	var rule_style := StyleBoxLine.new()
	rule_style.color = UI.GOLD
	rule_style.thickness = 1
	rule.add_theme_stylebox_override("separator", rule_style)
	body.add_child(rule)
	heading = UI.label("Opening scene", UI.TYPE_TITLE)
	heading.add_theme_font_override("font", UI.display_font())
	heading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(heading)
	detail = UI.label("")
	detail.custom_minimum_size.y = 64
	detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(detail)
	var progress_slot := VBoxContainer.new()
	progress_slot.name = "ResourceProgressSlot"
	progress_slot.custom_minimum_size.y = 88
	progress_slot.add_theme_constant_override("separation", UI.SPACE_XS)
	body.add_child(progress_slot)
	stage = UI.label("PREPARING", UI.TYPE_CAPTION, UI.GOLD)
	stage.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	progress_slot.add_child(stage)
	var bar_slot := Control.new()
	bar_slot.custom_minimum_size.y = 14
	progress_slot.add_child(bar_slot)
	progress_bar = ProgressBar.new()
	progress_bar.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	progress_bar.show_percentage = false
	bar_slot.add_child(progress_bar)
	progress_scope = UI.label("Resource progress appears when loading starts.", UI.TYPE_CAPTION, UI.MIST)
	progress_scope.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	progress_slot.add_child(progress_scope)
	actions = HBoxContainer.new()
	actions.name = "LoadingActions"
	# Primary Retry has taller font metrics than Back. Reserve the same band
	# when Retry is hidden so changing phase cannot move the recovery row.
	actions.custom_minimum_size.y = UI.TARGET_MIN + UI.SPACE_MD
	actions.add_theme_constant_override("separation", UI.SPACE_MD)
	stack.add_child(actions)
	retry_button = Button.new()
	retry_button.name = "TransitionRetry"
	retry_button.text = "Retry"
	retry_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UI.button(retry_button, true)
	actions.add_child(retry_button)
	back_button = Button.new()
	back_button.name = "TransitionBack"
	back_button.text = "Back"
	back_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UI.button(back_button)
	actions.add_child(back_button)

func _layout() -> void:
	if not is_instance_valid(card): return
	var available := (size - Vector2(48,48)).max(Vector2(160,160))
	card.size = Vector2(minf(520, available.x), minf(440, available.y))
	card.position = (size - card.size) * .5
