extends SceneTree
## View-only coverage; controller lifecycle and actual pixels have separate gates.
const VIEW = preload("res://scripts/loading_presentation.gd")
const UI = preload("res://scripts/hero_ui_theme.gd")
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("_run")

func _frames() -> void:
	for unused in 5: await process_frame

func _check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ", label)

func _run() -> void:
	root.size = Vector2i(1280,720)
	root.content_scale_size = Vector2i(1280,720)
	var view := VIEW.new()
	view.theme = UI.create()
	root.add_child(view)
	await _frames()
	var card_rect := view.card.get_global_rect()
	var row_rect := view.actions.get_global_rect()
	for phase in [&"queued", &"loading", &"constructing", &"error"]:
		view.retry_button.visible = phase == &"error"
		view.progress_bar.visible = phase == &"loading"
		view.heading.text = "Could not open Confluence" if phase == &"error" else "Opening Confluence"
		view.detail.text = "This scene is unavailable. Retry, or go back to the previous screen." if phase == &"error" else "Preparing the scene… This step may take a moment."
		view.present_phase(phase, &"confluence", .475 if phase == &"loading" else -1)
		await _frames()
		_check("Phase does not move the outer plate or recovery row: " + str(phase), view.card.get_global_rect() == card_rect and view.actions.get_global_rect() == row_rect, {"initial_card":str(card_rect),"current_card":str(view.card.get_global_rect()),"initial_row":str(row_rect),"current_row":str(view.actions.get_global_rect())})
	view.present_phase(&"loading", &"confluence", .475)
	_check("Percentage identifies resource scope rather than total readiness", view.progress_scope.text.contains("Resources") and view.progress_scope.text.contains("48%") and view.progress_scope.text.contains("preparation follows") and view.context.text == "OFFLINE LANES")
	view.back_button.disabled = true
	view.progress_bar.value = 47.5
	view.progress_bar.hide()
	view.present_phase(&"constructing", &"courtyard", -1)
	_check("View preserves controller atomic-commit and bar ownership", view.back_button.disabled and not view.progress_bar.visible and is_equal_approx(view.progress_bar.value,47.5) and view.back_button.text == "Cancel loading")
	_check("Construction does not invent a percentage or ready actor", not view.progress_scope.text.contains("%") and view.stage.text == "PREPARING SCENE AND ACTORS" and view.context.text == "PRACTICE MENU")
	view.present_phase(&"loading", &"combat_film", -1)
	_check("Unknown progress remains unavailable and film is explicitly scripted", view.progress_scope.text.contains("unavailable") and not view.progress_scope.text.contains("%") and view.context.text == "SCRIPTED DUEL")
	view.back_button.disabled = false
	view.present_phase(&"error", &"combat_film", -1)
	view.detail.text = "The scene could not be prepared. " .repeat(24) + "Retry, or go back."
	for spec in [[Vector2i(960,540),1.0],[Vector2i(960,540),2.0],[Vector2i(1280,720),1.25]]:
		root.size = spec[0]
		root.content_scale_factor = spec[1]
		await _frames()
		var visible := root.get_visible_rect()
		_check("Long recovery keeps actions outside the scroll and viewport-visible " + str(spec), visible.encloses(view.card.get_global_rect()) and view.card.get_global_rect().encloses(view.actions.get_global_rect()) and view.card.get_global_rect().encloses(view.retry_button.get_global_rect()) and view.card.get_global_rect().encloses(view.back_button.get_global_rect()) and not view.body_scroll.is_ancestor_of(view.back_button), {"viewport":str(visible),"card":str(view.card.get_global_rect()),"actions":str(view.actions.get_global_rect())})
	var peer := VIEW.new()
	peer.theme = UI.create()
	root.add_child(peer)
	await _frames()
	var peer_surface := peer.card.get_theme_stylebox("panel") as StyleBoxFlat
	var old_color := peer_surface.border_color
	(view.card.get_theme_stylebox("panel") as StyleBoxFlat).border_color = Color.MAGENTA
	_check("Loading plates retain private mutable surfaces", peer_surface.border_color == old_color)
	var passed := checks.all(func(row: Dictionary): return row.passed)
	var report := {"passed":passed,"count":checks.size(),"checks":checks,"sources":{},"scope":"Headless view-only geometry, resource labels and controller-state ownership; no lifecycle/pixel/native-window acceptance."}
	for path in ["res://scripts/loading_presentation.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	view.queue_free()
	peer.queue_free()
	await _frames()
	quit(0 if passed else 1)
