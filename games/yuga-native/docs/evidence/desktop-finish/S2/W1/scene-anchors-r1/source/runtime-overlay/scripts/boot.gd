extends Control
## Initial dependencies are only native controls, the shared theme and loader.
## Courtyard/gameplay resources enter through ResourceLoader after this screen paints.
const UI = preload("res://scripts/hero_ui_theme.gd")
const SceneTransition = preload("res://scripts/scene_transition.gd")

var scene_transition: Control
var open_button: Button
var quit_button: Button
var status: Label
var _last_error := ""

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = UI.create()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_build()
	print("YUGA_NATIVE_BOOT_READY")
	call_deferred("open_game")

func open_game() -> bool:
	if not _is_active_host(): return false
	scene_transition = SceneTransition.ensure_for_tree(get_tree())
	if not scene_transition.cancelled.is_connected(_on_cancelled):
		scene_transition.cancelled.connect(_on_cancelled)
		scene_transition.failed.connect(_on_failed)
	if scene_transition.is_busy() or scene_transition.phase == &"error": return false
	_last_error = ""
	status.text = "Opening YUGA…"
	if not scene_transition.begin(&"courtyard", self, open_button):
		status.text = "YUGA could not start loading. Retry, or quit and open the game again."
		open_button.grab_focus()
		return false
	return true

func _on_failed(_destination: StringName, message: String) -> void:
	if not _is_active_host(): return
	_last_error = message

func _on_cancelled(_destination: StringName) -> void:
	# The persistent loader can cancel after its live caller leaves the tree.
	# A hidden/disabled boot screen must not take focus from the replacement host.
	if not _is_active_host(): return
	status.text = "Loading stopped. Open YUGA when you are ready." if _last_error.is_empty() else "YUGA could not open. Retry, or quit and open the game again."
	open_button.text = "Retry opening YUGA" if not _last_error.is_empty() else "Open YUGA"
	if is_visible_in_tree() and can_process() and not open_button.disabled:
		open_button.grab_focus()

func _is_active_host() -> bool:
	return is_inside_tree() and (get_tree().current_scene == null or get_tree().current_scene == self)

func quit_game() -> void:
	if is_instance_valid(scene_transition) and scene_transition.is_busy():
		if not scene_transition.cancel(): return
	get_tree().quit()

func _build() -> void:
	var background := ColorRect.new()
	background.color = UI.DEEP
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var card := PanelContainer.new()
	card.custom_minimum_size.x = 320
	center.add_child(card)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", UI.SPACE_LG)
	card.add_child(stack)
	var wordmark := UI.label("YUGA", UI.TYPE_DISPLAY, UI.GOLD)
	wordmark.theme_type_variation = &"YugaDisplay"
	stack.add_child(wordmark)
	stack.add_child(UI.label("Offline practice", UI.TYPE_SECTION))
	status = UI.label("Opening YUGA…")
	status.custom_minimum_size = Vector2(280, 60)
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(status)
	open_button = Button.new()
	open_button.text = "Open YUGA"
	UI.button(open_button, true)
	open_button.pressed.connect(open_game)
	stack.add_child(open_button)
	quit_button = Button.new()
	quit_button.text = "Quit"
	UI.button(quit_button)
	quit_button.pressed.connect(quit_game)
	stack.add_child(quit_button)
	open_button.focus_next = open_button.get_path_to(quit_button)
	open_button.focus_previous = open_button.get_path_to(quit_button)
	quit_button.focus_next = quit_button.get_path_to(open_button)
	quit_button.focus_previous = quit_button.get_path_to(open_button)
	open_button.grab_focus()
