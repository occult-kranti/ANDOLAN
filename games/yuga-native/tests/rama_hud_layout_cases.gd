extends SceneTree
## Logical-canvas geometry; screenshots remain required for actual presentation.
var checks: Array[Dictionary] = []
var output := ""
var scene: Node3D

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func _frames() -> void:
	for unused in range(6): await process_frame

func _run() -> void:
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await _frames()
	scene.set_paused(false)
	for unused in range(5): await physics_frame
	scene.player.set_physics_process(false)
	scene.army.set_physics_process(false)
	# Check the initial 1280-wide canvas before any resize can repair stale
	# wrapped-label minimum heights from the first native container sort.
	for dimensions in [Vector2i(1280,720), Vector2i(960,600), Vector2i(1920,1080)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await _frames()
		var viewport := root.get_visible_rect()
		var peers: Array[Control] = []
		var rects := {}
		var outside: Array[String] = []
		var overlaps := []
		# The atlas owns its legend. Intentional parent/child composition is not a
		# sibling collision; every visible top-level HUD surface is checked here.
		for child in scene.hud.get_children():
			if child is Control and child.is_visible_in_tree():
				peers.append(child)
				rects[String(child.name)] = str(child.get_global_rect())
				if not viewport.encloses(child.get_global_rect()): outside.append(String(child.name))
		for first in peers.size():
			for second in range(first+1,peers.size()):
				if peers[first].get_global_rect().intersects(peers[second].get_global_rect()): overlaps.append([peers[first].name,peers[second].name])
		_record("All visible HUD surfaces fit and remain separate "+str(dimensions), peers.size() >= 7 and outside.is_empty() and overlaps.is_empty(), {"outside":outside,"overlaps":overlaps,"rectangles":rects})
		var camera: Camera3D = scene.player.camera
		var torso := Rect2()
		var first_point := true
		for height in [.75,1.80]:
			for side in [-.32,.32]:
				var point := camera.unproject_position(scene.player.global_position + Vector3.UP*height + camera.global_basis.x*side)
				if first_point:
					torso = Rect2(point,Vector2.ZERO)
					first_point = false
				else: torso = torso.expand(point)
		var torso_blocks: Array[String] = []
		for control in peers:
			if control.get_global_rect().intersects(torso): torso_blocks.append(String(control.name))
		_record("Neutral gameplay torso remains clear of HUD "+str(dimensions), viewport.encloses(torso) and torso_blocks.is_empty(), {"torso":str(torso),"blocking":torso_blocks,"scope":"Neutral grounded gameplay camera; not every animation or aim angle."})
		var slot_failures: Array[String] = []
		for slot in scene.rama_hud.slots:
			if not viewport.encloses(slot.get_global_rect()) or not slot.get_parent().get_global_rect().encloses(slot.get_global_rect()): slot_failures.append(slot.text)
			var font: Font = slot.get_theme_font("font")
			var font_size: int = slot.get_theme_font_size("font_size")
			for line in slot.text.split("\n"):
				if font.get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x > slot.size.x + .5: slot_failures.append(line)
		_record("Five ability names and live health remain readable "+str(dimensions), scene.rama_hud.slots.size() == 5 and slot_failures.is_empty() and viewport.encloses(scene.rama_hud.life_text.get_global_rect()) and scene.rama_hud.life.max_value == scene.rama_runtime.vitals.report().max_health, {"clipped":slot_failures})
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless viewport, peer overlap, neutral torso projection and label-width checks. Actual asset appearance and OS rendering require separate review.","sources":{}}
	for path in ["res://scripts/confluence_world.gd","res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	scene.queue_free()
	current_scene = null
	paused = false
	await _frames()
	# Give the native audio mixer one real buffer to retire the scene's voices.
	OS.delay_msec(80)
	await process_frame
	quit(0 if passed else 1)
