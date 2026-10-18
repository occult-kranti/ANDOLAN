extends SceneTree
## Real native layout: offline context remains visible before launch and retry.
const Shell = preload("res://scripts/launch_shell.gd")
var output := "/tmp/impeccable-title-context.json"
var checks: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func frames(count := 8) -> void:
	for unused in count: await process_frame

func fully_visible(control: Control) -> bool:
	if not control.is_visible_in_tree() or control.size.x <= 0.0 or control.size.y <= 0.0: return false
	var rect := control.get_global_rect()
	if not root.get_visible_rect().encloses(rect): return false
	var parent := control.get_parent()
	while parent != null:
		if parent is Control and (parent.clip_contents or parent is ScrollContainer):
			if not parent.get_global_rect().encloses(rect): return false
		parent = parent.get_parent()
	return true

func offline_labels(node: Node, rows: Array[Dictionary]) -> void:
	if node is Label and node.text.to_lower().contains("offline"):
		rows.append({"node": str(node.get_path()), "text": node.text, "visible": fully_visible(node), "rect": str(node.get_global_rect())})
	for child in node.get_children(): offline_labels(child, rows)

func sources() -> Dictionary:
	var result := {}
	for path in ["res://scripts/launch_shell.gd", "res://scripts/hero_ui_theme.gd", get_script().resource_path]:
		result[path] = FileAccess.get_sha256(path)
	return result

func run() -> void:
	var before := sources()
	root.size = Vector2i(960, 540)
	root.content_scale_size = Vector2i(1280, 720)
	for scale in [1.0, 1.25, 1.5, 2.0]:
		root.content_scale_factor = scale
		for mode in ["world", "train"]:
			var shell := Shell.new()
			shell.set_mode(mode)
			root.add_child(shell)
			shell.focus_primary()
			await frames()
			for state in ["ready", "error"]:
				var message := "Practice could not open. Try again."
				if state == "error":
					shell.set_launch_state(state, message)
					await frames()
				var labels: Array[Dictionary] = []
				offline_labels(shell, labels)
				var context_visible := labels.any(func(row: Dictionary): return row.visible)
				var decision_visible := fully_visible(shell.world_mode_button) and fully_visible(shell.train_mode_button) and fully_visible(shell.mode_description) and fully_visible(shell.primary_button)
				var state_preserved: bool = shell.selected_mode == mode and shell.launch_state == state and not shell.primary_button.disabled and root.gui_get_focus_owner() == shell.primary_button
				if state == "error": state_preserved = state_preserved and shell.menu_hint.text == message
				var passed := context_visible and decision_visible and state_preserved
				var label: String = "Visible offline context and launch decision: " + mode + " / " + state + " / " + str(scale)
				checks.append({"name": label, "passed": passed, "details": {"offline_labels": labels, "context_visible": context_visible, "decision_visible": decision_visible, "state_preserved": state_preserved, "description": shell.mode_description.text, "description_rect": str(shell.mode_description.get_global_rect()), "description_lines": shell.mode_description.get_line_count(), "primary_rect": str(shell.primary_button.get_global_rect()), "scroll_rect": str(shell.scroll.get_global_rect()), "scroll_offset": shell.scroll.scroll_vertical, "viewport": str(root.get_visible_rect())}})
				print("PASS " if passed else "FAIL ", label)
			shell.queue_free()
			await frames()
	var after := sources()
	var stable := before == after
	checks.append({"name": "Source bytes remain stable during observations", "passed": stable})
	var passed := checks.all(func(row: Dictionary): return row.passed)
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify({"passed": passed, "count": checks.size(), "checks": checks, "sources_before": before, "sources_after": after, "scope": "Native 2D Control geometry and selection/focus at 960x540, logical 1280x720, 100/125/150/200% content scaling. Explicit offline context must be fully visible through viewport and ancestor clips before launch or retry. No rendering, OS input, scene navigation or new art acceptance."}, "  ") + "\n")
	await frames()
	quit(0 if passed else 1)
