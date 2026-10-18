extends Control
## Mount outside the current scene (for example under a root CanvasLayer).
## Threading covers resource loading only. Scene instantiation/_ready run on the main thread.

signal phase_changed(phase: StringName, message: String, resource_progress: float)
signal completed(destination: StringName)
signal failed(destination: StringName, message: String)
signal cancelled(destination: StringName)

const UI = preload("res://scripts/hero_ui_theme.gd")
const LoadingPresentation = preload("res://scripts/loading_presentation.gd")
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
var _source_scene: WeakRef
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
	if is_instance_valid(caller) and (not caller.is_inside_tree() or caller.get_tree() != get_tree()):
		return false
	var owner: Variant = get_tree().root.get_meta(OWNER_META) if get_tree().root.has_meta(OWNER_META) else null
	if is_instance_valid(owner) and owner != self:
		return false
	get_tree().root.set_meta(OWNER_META, self)
	destination = id
	_path = SCENES[id]
	_caller = weakref(caller) if is_instance_valid(caller) else null
	_source_scene = weakref(get_tree().current_scene) if is_instance_valid(get_tree().current_scene) else null
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
	var return_focus := _return_focus
	var source_scene := _source_scene
	var restore_focus_loss := _focus_lost_during_transition and not _host_was_replaced()
	_focus_lost_during_transition = false
	_abandon_pending()
	_ticket += 1
	var cancelled_ticket := _ticket
	_packed = null
	hide()
	_restore_caller()
	_release_owner()
	_set_phase(&"cancelled", "Returned to the previous screen.", -1.0)
	cancelled.emit(cancelled_id)
	_restore_cancel_focus(return_focus, source_scene, cancelled_ticket)
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
	if _owns_input and not _committing and _host_was_replaced():
		cancel()
		return
	if _owns_input and not _committing and _caller != null:
		var caller: Node = _caller.get_ref()
		if not is_instance_valid(caller) or not caller.is_inside_tree() or caller.get_tree() != get_tree():
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
	_source_scene = null
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
	# Polling can report the same resource state many times between worker updates.
	# Keep exact values: even a sub-percent change remains observable.
	if phase == next and message == text and resource_progress == progress:
		return
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

func _host_was_replaced() -> bool:
	# A detached or freed source may leave a different scene in charge before
	# the next poll. Its pause, mouse and focus policy must remain authoritative.
	return (_source_scene != null and is_instance_valid(get_tree().current_scene)
		and get_tree().current_scene != _source_scene.get_ref())

func _restore_caller() -> void:
	if not _owns_input: return
	var replaced := _host_was_replaced()
	_owns_input = false
	if not replaced:
		get_tree().paused = _previous_pause
		Input.mouse_mode = _previous_mouse_mode
	var caller: Node = _caller.get_ref() if _caller != null else null
	if is_instance_valid(caller): caller.process_mode = _caller_process_mode
	var focus: Control = _return_focus.get_ref() if _return_focus != null else null
	if not replaced: _restore_focus(focus)
	_caller = null
	_source_scene = null
	_return_focus = null

func _restore_focus(focus: Control) -> void:
	# A paused caller can legitimately retain focus. Reject explicitly disabled
	# processing owners without treating the restored SceneTree pause as disposal.
	var process_owner: Node = focus
	while is_instance_valid(process_owner) and process_owner.process_mode == Node.PROCESS_MODE_INHERIT:
		process_owner = process_owner.get_parent()
	var disabled_owner := is_instance_valid(process_owner) and process_owner.process_mode == Node.PROCESS_MODE_DISABLED
	if (is_instance_valid(focus) and not focus.is_queued_for_deletion() and focus.is_inside_tree() and focus.is_visible_in_tree()
			and not disabled_owner and focus.focus_mode != Control.FOCUS_NONE
			and (not focus is BaseButton or not focus.disabled)):
		focus.grab_focus()

func _restore_cancel_focus(reference: WeakRef, source: WeakRef, ticket: int) -> void:
	# Hosts restore explicitly processing children in their cancelled callbacks.
	# Retry focus only after those callbacks, without overriding a new attempt,
	# scene owner or deliberately selected callback focus. No deferred frame can
	# later steal focus from input that arrived after cancellation.
	var tree := get_tree()
	if tree == null or _ticket != ticket or phase != &"cancelled" or reference == null: return
	if tree.root.has_meta(OWNER_META) or tree.root.gui_get_focus_owner() != null: return
	if source != null and is_instance_valid(tree.current_scene) and tree.current_scene != source.get_ref(): return
	_restore_focus(reference.get_ref())

func _release_owner() -> void:
	if get_tree().root.has_meta(OWNER_META) and get_tree().root.get_meta(OWNER_META) == self:
		get_tree().root.remove_meta(OWNER_META)

func _exit_tree() -> void:
	var notify_cancel := not _committing and (is_busy() or phase == &"error")
	var cancelled_id := destination
	var return_focus := _return_focus
	var source_scene := _source_scene
	_abandon_pending()
	if not _abandoned.is_empty():
		var janitor := AbandonedLoads.new()
		janitor.process_mode = Node.PROCESS_MODE_ALWAYS
		janitor.paths = _abandoned.keys()
		get_tree().root.call_deferred("add_child", janitor)
		_abandoned.clear()
	_ticket += 1
	var cancelled_ticket := _ticket
	if not _committing: _restore_caller()
	_release_owner()
	# Hosts may have explicitly processing children outside inherited caller mode.
	# Disposal must run their cancellation restoration just like Back does.
	if notify_cancel:
		phase = &"cancelled"
		cancelled.emit(cancelled_id)
		_restore_cancel_focus(return_focus, source_scene, cancelled_ticket)

func _input(event: InputEvent) -> void:
	if not visible: return
	if event.is_action_pressed("ui_cancel"):
		cancel()
		get_viewport().set_input_as_handled()

func _build() -> void:
	var view := LoadingPresentation.new()
	add_child(view)
	card = view.card
	heading = view.heading
	detail = view.detail
	progress_bar = view.progress_bar
	retry_button = view.retry_button
	back_button = view.back_button
	view.bind_transition(self)
	retry_button.pressed.connect(retry)
	back_button.pressed.connect(cancel)
	retry_button.focus_neighbor_left = retry_button.get_path_to(back_button)
	retry_button.focus_neighbor_right = retry_button.get_path_to(back_button)
	retry_button.focus_next = retry_button.get_path_to(back_button)
	retry_button.focus_previous = retry_button.get_path_to(back_button)
	back_button.focus_neighbor_left = back_button.get_path_to(retry_button)
	back_button.focus_neighbor_right = back_button.get_path_to(retry_button)
