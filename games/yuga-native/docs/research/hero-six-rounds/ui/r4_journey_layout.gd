extends SceneTree
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array = []
var output := ""
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func frames() -> void:
	for unused in 8: await process_frame
func run() -> void:
	var court: Node3D = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(court)
	current_scene = court
	await frames()
	court.start_training()
	court.set_physics_process(false)
	court.player.set_physics_process(false)
	court.practice_army.set_physics_process(false)
	court.rama_runtime.set_volume(0)
	var saved: Dictionary = Bindings.bindings.duplicate()
	Bindings.bindings.pulse = KEY_SPACE
	Bindings.bindings.dash = KEY_SHIFT
	Bindings.bindings.guardian_circle = KEY_CTRL
	var keys := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
	var top: Control = court.objective_label.get_parent().get_parent().get_parent()
	var card: Control = court.objective_label.get_parent().get_parent()
	for scale in [1.0, 1.5, 2.0]:
		root.size = Vector2i(960, 600)
		root.content_scale_size = Vector2i(1280, 720)
		root.content_scale_factor = scale
		for completed in range(6):
			court.training_journey.completed.clear()
			for index in completed: court.training_journey.completed[keys[index]] = true
			court._refresh_hud()
			await frames()
			var failures := []
			var view := root.get_visible_rect()
			if not view.encloses(card.get_global_rect()): failures.append("title card outside viewport")
			for label in [court.objective_label, court.stats_label, court.status_label]:
				if not card.get_global_rect().encloses(label.get_global_rect()): failures.append("label outside card")
				for line in label.text.split("\n"):
					if label.get_theme_font("font").get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,label.get_theme_font_size("font_size")).x > label.size.x+.5: failures.append("text clipped: " + line)
			for peer in top.get_children():
				if peer is Button and peer.get_global_rect().intersects(card.get_global_rect()): failures.append("pause overlaps card")
			if card.get_global_rect().intersects(court.rama_hud.get_global_rect()): failures.append("hero HUD overlaps card")
			checks.append({"name":"journey stage %d at %s" % [completed,scale],"passed":failures.is_empty(),"failures":failures,"card":str(card.get_global_rect()),"view":str(view),"hint":court.status_label.text})
	Bindings.bindings = saved
	var passed := checks.all(func(row):return row.passed)
	var result := {"passed":passed,"checks":checks,"sources":{}}
	for path in ["res://scripts/courtyard.gd","res://scripts/rama_training_journey.gd",get_script().resource_path]: result.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	print(JSON.stringify(result))
	current_scene = null
	court.queue_free()
	await frames()
	quit(0 if passed else 1)
