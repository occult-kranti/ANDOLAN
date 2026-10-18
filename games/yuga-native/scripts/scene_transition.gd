extends Control
## Mount outside the current scene (for example under a root CanvasLayer).
## Threading covers resource loading only. Scene instantiation/_ready run on the main thread.

signal phase_changed(phase: StringName, message: String, resource_progress: float)
signal completed(destination: StringName)
signal failed(destination: StringName, message: String)
signal cancelled(destination: StringName)

const UI = preload("res://scripts/hero_ui_theme.gd")
const SCENES := {
	&"courtyard": "res://scenes/courtyard.tscn",
	&"confluence": "res://scenes/confluence_world.tscn",
	&"combat_film": "res://scenes/combat_film.tscn",
}
const TITLES := {&"courtyard": "YUGA", &"confluence": "Confluence", &"combat_film": "Confluence duel"}
const OWNER_META := &"yuga_scene_transition_owner"

# Disposing the overlay never waits for an uncancellable worker to finish.
# A root-owned janitor consumes its result without retaining any navigation callback.
class AbandonedLoads extends Node:
	var paths: Array = []
	func _process(_delta: float) -> void:
		for path in paths.duplicate():
			var status := ResourceLoader.load_threaded_get_status(path)
			if status in [ResourceLoader.THREAD_LOAD_LOADED, ResourceLoader.THREAD_LOAD_FAILED]:
				ResourceLoader.load_threaded_get(path)
				paths.erase(path)
			elif status == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
				paths.erase(path)
		if paths.is_empty(): queue_free()

var phase: StringName = &"idle"
var destination: StringName = &""
var resource_progress := -1.0
var message := ""
var card: PanelContainer
var heading: Label
var detail: Label
var progress_bar: ProgressBar
var retry_button: Button
var back_button: Button
var _ticket := 0
var _terminal_ticket := -1
var _path := ""
var _caller: WeakRef
var _return_focus: WeakRef
var _caller_process_mode := Node.PROCESS_MODE_INHERIT
var _previous_pause := false
var _previous_mouse_mode := Input.MOUSE_MODE_VISIBLE
var _owns_input := false
var _committing := false
var _abandoned: Dictionary = {}
var _wait_frames := 0
var _packed: PackedScene
var _focus_lost_during_transition := false

## Shared by boot and scene hosts. The persistent owner survives scene replacement.
static func ensure_for_tree(tree: SceneTree) -> Control:
	var layer := tree.root.get_node_or_null("YugaSceneTransitionLayer") as CanvasLayer
	if layer == null:
		layer = CanvasLayer.new()
		layer.name = "YugaSceneTransitionLayer"
		layer.layer = 100
		layer.process_mode = Node.PROCESS_MODE_ALWAYS
		tree.root.add_child(layer)
	var existing := layer.get_node_or_null("SceneTransition") as Control
	if existing != null: return existing
	var instance := load("res://scripts/scene_transition.gd").new() as Control
	instance.name = "SceneTransition"
	layer.add_child(instance)
	return instance

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UI.create()
	_build()
	get_window().focus_exited.connect(_remember_focus_loss)
	get_window().focus_entered.connect(_remember_focus_gain)
	hide()

## Returns false for unknown IDs, duplicate activation, detached controls or competing owners.
## Callers may release held gameplay actions immediately before an accepted transition.
func begin(id: StringName, caller: Node = null, return_focus: Control = null) -> bool:
	if not is_inside_tree() or not SCENES.has(id) or is_busy() or phase == &"error":
		return false
	# A caller owning this overlay would delete it during scene replacement.
	if is_instance_valid(caller) and (caller == self or caller.is_ancestor_of(self)):
		return false
	var owner: Variant = get_tree().root.get_meta(OWNER_META) if get_tree().root.has_meta(OWNER_META) else null
	if is_instance_valid(owner) and owner != self:
		return false
	get_tree().root.set_meta(OWNER_META, self)
	destination = id
	_path = SCENES[id]
	_caller = weakref(caller) if is_instance_valid(caller) else null
	var focus := return_focus if is_instance_valid(return_focus) else get_viewport().gui_get_focus_owner()
	_return_focus = weakref(focus) if is_instance_valid(focus) else null
	_previous_pause = get_tree().paused
	_previous_mouse_mode = Input.mouse_mode
	if is_instance_valid(caller):
		_caller_process_mode = caller.process_mode
		caller.process_mode = Node.PROCESS_MODE_DISABLED
	_owns_input = true
	_focus_lost_during_transition = DisplayServer.get_name() != "headless" and not get_window().has_focus()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_start_attempt()
	return true

func is_busy() -> bool:
	return phase in [&"queued", &"loading", &"constructing"]

func retry() -> bool:
	if phase != &"error": return false
	_start_attempt()
	return true

## ResourceLoader has no cancellation API. The job may finish, but its result cannot navigate.
## Once synchronous scene replacement starts it is atomic and Back is disabled.
func cancel() -> bool:
	if (not is_busy() and phase != &"error") or _committing: return false
	var cancelled_id := destination
	var restore_focus_loss := _focus_lost_during_transition
	_focus_lost_during_transition = false
	_abandon_pending()
	_ticket += 1
	_packed = null
	hide()
	_restore_caller()
	_release_owner()
	_set_phase(&"cancelled", "Returned to the previous screen.", -1.0)
	cancelled.emit(cancelled_id)
	if restore_focus_loss: get_window().focus_exited.emit()
	return true

func snapshot() -> Dictionary:
	return {"phase": str(phase), "destination": str(destination), "resource_progress": resource_progress,
		"message": message, "busy": is_busy(), "visible": visible, "committing": _committing, "attempt": _ticket}

func _start_attempt() -> void:
	_ticket += 1
	var ticket := _ticket
	_committing = false
	_packed = null
	_wait_frames = 2
	show()
	heading.text = "Opening " + TITLES[destination]
	retry_button.hide()
	back_button.text = "Back"
	back_button.disabled = false
	back_button.focus_next = NodePath(".")
	back_button.focus_previous = NodePath(".")
	_set_phase(&"queued", "Preparing to load…", -1.0)
	if not _is_current(ticket): return
	back_button.grab_focus()

func _start_loading() -> void:
	if not ResourceLoader.exists(_path, "PackedScene"):
		_fail("This scene is unavailable. Retry, or go back to the previous screen.")
		return
	# Reuse an uncancellable job from a previous attempt instead of requesting it twice.
	if not _abandoned.has(_path):
		var error := ResourceLoader.load_threaded_request(_path, "PackedScene", false)
		if error != OK:
			_fail("The scene could not begin loading. Retry, or go back. (" + error_string(error) + ")")
			return
	_abandoned.erase(_path)
	_set_phase(&"loading", "Loading scene resources…", -1.0)

func _process(_delta: float) -> void:
	_drain_abandoned()
	if _owns_input and not _committing and _caller != null and not is_instance_valid(_caller.get_ref()):
		cancel()
		return
	# Frame counters let the status paint before work, without orphaned await states on disposal.
	if phase in [&"queued", &"constructing"] and not _committing:
		_wait_frames -= 1
		if _wait_frames <= 0:
			if phase == &"queued": _start_loading()
			else: _commit(_ticket, _packed)
		return
	if phase != &"loading": return
	var progress: Array = []
	var status := ResourceLoader.load_threaded_get_status(_path, progress)
	if status == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
		var value := -1.0
		if progress.size() == 1 and (progress[0] is float or progress[0] is int):
			var reported := float(progress[0])
			if is_finite(reported) and reported >= 0.0 and reported <= 1.0: value = reported
		_set_phase(&"loading", "Loading scene resources…", value)
	elif status == ResourceLoader.THREAD_LOAD_LOADED:
		var resource := ResourceLoader.load_threaded_get(_path)
		if not resource is PackedScene or not resource.can_instantiate():
			_fail("The scene could not be opened. Retry, or go back.")
			return
		_packed = resource as PackedScene
		_wait_frames = 2
		_set_phase(&"constructing", "Preparing the scene… This step may take a moment.", -1.0)
	elif status in [ResourceLoader.THREAD_LOAD_FAILED, ResourceLoader.THREAD_LOAD_INVALID_RESOURCE]:
		if status == ResourceLoader.THREAD_LOAD_FAILED:
			ResourceLoader.load_threaded_get(_path) # Release the failed request's engine token.
		_fail("The scene could not finish loading. Retry, or go back.")

func _commit(ticket: int, packed: PackedScene) -> void:
	if not _is_current(ticket): return
	_committing = true
	back_button.disabled = true
	get_tree().scene_changed.connect(_scene_changed.bind(ticket), CONNECT_ONE_SHOT)
	get_tree().paused = false
	var error := get_tree().change_scene_to_packed(packed)
	if error != OK:
		get_tree().scene_changed.disconnect(_scene_changed.bind(ticket))
		_committing = false
		get_tree().paused = _previous_pause
		_fail("The scene could not be prepared. Retry, or go back. (" + error_string(error) + ")")

func _scene_changed(ticket: int) -> void:
	if not _is_current(ticket) or _terminal_ticket == ticket: return
	_terminal_ticket = ticket
	var completed_id := destination
	var restore_focus_loss := _focus_lost_during_transition
	_focus_lost_during_transition = false
	_committing = false
	_owns_input = false # The new scene owns its input and focus state.
	_caller = null
	_return_focus = null
	_packed = null
	hide()
	_release_owner()
	_set_phase(&"done", "Ready.", -1.0)
	# The old scene was isolated when focus left. Let the newly mounted scene's
	# existing window-focus handler apply its own pause policy (including --smoke).
	if restore_focus_loss: get_window().focus_exited.emit()
	completed.emit(completed_id)

func _remember_focus_loss() -> void:
	if is_busy() or phase == &"error": _focus_lost_during_transition = true

func _remember_focus_gain() -> void:
	_focus_lost_during_transition = false

func _fail(reason: String) -> void:
	if _terminal_ticket == _ticket: return
	_terminal_ticket = _ticket
	var failed_id := destination
	heading.text = "Could not open " + TITLES[destination]
	retry_button.show()
	back_button.disabled = false
	back_button.focus_next = back_button.get_path_to(retry_button)
	back_button.focus_previous = back_button.get_path_to(retry_button)
	retry_button.grab_focus()
	_set_phase(&"error", reason, -1.0)
	failed.emit(failed_id, reason)

func _is_current(ticket: int) -> bool:
	return is_inside_tree() and ticket == _ticket and is_busy()

func _set_phase(next: StringName, text: String, progress: float) -> void:
	phase = next
	message = text
	resource_progress = progress
	detail.text = text
	progress_bar.visible = next == &"loading" and progress >= 0.0
	progress_bar.value = progress * 100.0 if progress >= 0.0 else 0.0
	phase_changed.emit(next, text, progress)

func _abandon_pending() -> void:
	if phase == &"loading": _abandoned[_path] = true

func _drain_abandoned() -> void:
	for path in _abandoned.keys():
		# A queued retry reserves this job until _start_loading adopts it.
		if path == _path and phase == &"queued": continue
		var status := ResourceLoader.load_threaded_get_status(path)
		if status == ResourceLoader.THREAD_LOAD_LOADED:
			ResourceLoader.load_threaded_get(path)
			_abandoned.erase(path)
		elif status != ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			if status == ResourceLoader.THREAD_LOAD_FAILED: ResourceLoader.load_threaded_get(path)
			_abandoned.erase(path)

func _restore_caller() -> void:
	if not _owns_input: return
	_owns_input = false
	get_tree().paused = _previous_pause
	Input.mouse_mode = _previous_mouse_mode
	var caller: Node = _caller.get_ref() if _caller != null else null
	if is_instance_valid(caller): caller.process_mode = _caller_process_mode
	var focus: Control = _return_focus.get_ref() if _return_focus != null else null
	if is_instance_valid(focus) and focus.is_inside_tree() and focus.is_visible_in_tree(): focus.grab_focus()
	_caller = null
	_return_focus = null

func _release_owner() -> void:
	if get_tree().root.has_meta(OWNER_META) and get_tree().root.get_meta(OWNER_META) == self:
		get_tree().root.remove_meta(OWNER_META)

func _exit_tree() -> void:
	var notify_cancel := not _committing and (is_busy() or phase == &"error")
	var cancelled_id := destination
	_abandon_pending()
	if not _abandoned.is_empty():
		var janitor := AbandonedLoads.new()
		janitor.process_mode = Node.PROCESS_MODE_ALWAYS
		janitor.paths = _abandoned.keys()
		get_tree().root.call_deferred("add_child", janitor)
		_abandoned.clear()
	_ticket += 1
	if not _committing: _restore_caller()
	_release_owner()
	# Hosts may have explicitly processing children outside inherited caller mode.
	# Disposal must run their cancellation restoration just like Back does.
	if notify_cancel:
		phase = &"cancelled"
		cancelled.emit(cancelled_id)

func _input(event: InputEvent) -> void:
	if not visible: return
	if event.is_action_pressed("ui_cancel"):
		cancel()
		get_viewport().set_input_as_handled()

func _build() -> void:
	var veil := ColorRect.new()
	veil.color = Color(0.02, 0.035, 0.07, 0.96)
	veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(veil)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]: margin.add_theme_constant_override("margin_" + side, 24)
	add_child(margin)
	var center := CenterContainer.new()
	margin.add_child(center)
	card = PanelContainer.new()
	card.custom_minimum_size.x = 280
	center.add_child(card)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", UI.SPACE_LG)
	card.add_child(stack)
	var wordmark := UI.label("YUGA", UI.TYPE_DISPLAY, UI.GOLD)
	wordmark.theme_type_variation = &"YugaDisplay"
	stack.add_child(wordmark)
	heading = UI.label("Opening scene", UI.TYPE_SECTION)
	stack.add_child(heading)
	detail = UI.label("")
	detail.custom_minimum_size = Vector2(280, 64)
	detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(detail)
	progress_bar = ProgressBar.new()
	progress_bar.custom_minimum_size.y = 12
	progress_bar.show_percentage = true
	stack.add_child(progress_bar)
	var actions := HBoxContainer.new()
	stack.add_child(actions)
	retry_button = Button.new()
	retry_button.text = "Retry"
	UI.button(retry_button, true)
	retry_button.pressed.connect(retry)
	actions.add_child(retry_button)
	back_button = Button.new()
	back_button.text = "Back"
	UI.button(back_button)
	back_button.pressed.connect(cancel)
	actions.add_child(back_button)
	retry_button.focus_neighbor_left = retry_button.get_path_to(back_button)
	retry_button.focus_neighbor_right = retry_button.get_path_to(back_button)
	retry_button.focus_next = retry_button.get_path_to(back_button)
	retry_button.focus_previous = retry_button.get_path_to(back_button)
	back_button.focus_neighbor_left = back_button.get_path_to(retry_button)
	back_button.focus_neighbor_right = back_button.get_path_to(retry_button)
