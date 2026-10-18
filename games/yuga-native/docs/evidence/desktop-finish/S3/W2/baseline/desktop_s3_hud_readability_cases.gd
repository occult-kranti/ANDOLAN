extends "res://tests/ui_i1_action_hud_cases.gd"
## Real remaps and authority states; compact HUD bounds, no pose dumps/pixel claim.
const Bindings = preload("res://scripts/input_bindings.gd")

func inspect_layout(state_name: String) -> void:
	var hud: Control = scene.rama_hud
	var before: Dictionary = scene.rama_runtime.kit.report()
	var army_time: float = scene.army.elapsed
	for scale in [1.0,1.5,2.0]:
		root.size = Vector2i(960,540)
		root.content_scale_size = Vector2i(1280,720)
		root.content_scale_factor = scale
		await frames(5)
		var issues: Array[String] = []
		var viewport := root.get_visible_rect()
		if not viewport.encloses(hud.get_global_rect()): issues.append("HUD outside logical viewport")
		for index in hud.slots.size():
			var slot: Label = hud.slots[index]
			var card: Control = hud.slot_cards[index]
			if not hud.get_global_rect().encloses(card.get_global_rect()) or not viewport.encloses(card.get_global_rect()): issues.append("card outside: " + str(index))
			var font: Font = slot.get_theme_font("font")
			var font_size: int = slot.get_theme_font_size("font_size")
			for line in slot.text.split("\n"):
				if font.get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x > slot.size.x + .5: issues.append("text clipped: " + line)
			if font_size < 16: issues.append("ability type shrunk")
		check(state_name + " remains contained with actual remaps at UI scale " + str(scale), issues.is_empty(), {"issues":issues,"viewport":str(viewport),"hud":str(hud.get_global_rect()),"note":hud.note.text})
	check(state_name + " layout observation preserves combat state", before == scene.rama_runtime.kit.report() and scene.army.elapsed == army_time)

func run() -> void:
	for path in ["res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd","res://scripts/input_bindings.gd",get_script().resource_path]: source_start[path] = FileAccess.get_sha256(path)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.rama_runtime.set_volume(0)
	await ground_fixture()
	var remapped := true
	for pair in [["jump",KEY_J],["sprint",KEY_K],["descend",KEY_L],["pulse",KEY_SPACE],["dash",KEY_SHIFT],["guardian_circle",KEY_CTRL]]:
		remapped = Bindings.set_binding(pair[0],pair[1]).ok and remapped
	check("Supported Space/Shift/Ctrl remaps are saved through the real binding API", remapped and Bindings.label("pulse") == "Space" and Bindings.label("dash") == "Shift" and Bindings.label("guardian_circle") == "Ctrl")
	scene.rama_hud._process(.08)
	await inspect_layout("ready")
	var cast: Dictionary = scene.cast_rama_ability("piercing_dawn")
	scene.rama_hud._process(.001)
	check("Actual accepted cast supplies DRAWING and BUSY", cast.get("accepted",false) and scene.rama_hud.note.text.contains("DRAWING") and scene.rama_hud.slots[2].text.contains("BUSY"))
	await inspect_layout("drawing/busy")
	for unused in 17: advance()
	var queued: Dictionary = scene.rama_runtime.request_input_ability("dawn_volley",4901)
	scene.rama_hud._process(.001)
	check("Real pending buffer supplies RECOVERING and QUEUED", queued.get("queued",false) and scene.rama_hud.note.text.contains("RECOVERING") and scene.rama_hud.slots[4].text.contains("QUEUED"))
	await inspect_layout("recovering/queued")
	var damage: Dictionary = scene.rama_runtime.vitals.receive_damage(1000,"S3 readability defeat",scene.rama_runtime.vitals.generation,0)
	scene.rama_hud._process(.001)
	check("Real defeat retains returning precedence", damage.get("accepted",false) and scene.rama_hud.note.text.begins_with("RETURNING"))
	await inspect_layout("defeated")
	await ground_fixture()
	cast = scene.cast_rama_ability("kodanda")
	for unused in 9: advance()
	var reload_started: bool = scene.player.start_reload()
	scene.rama_hud._process(.08)
	check("Real spent arrow and reload supply RELOADING", cast.get("accepted",false) and reload_started and scene.rama_hud.slots[0].text.contains("RELOADING"))
	await inspect_layout("reloading")
	var stable := true
	for path in source_start: stable = stable and source_start[path] == FileAccess.get_sha256(path)
	check("HUD and fixture source remain stable",stable)
	var passed := checks.all(func(row): return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"sources":source_start,"scope":"Real saved remaps, kit/vitals/reload/buffer states, logical viewport scaling and actual-font containment. Other world HUD peers, rendered legibility, OS input and hardware performance are separate gates."},"  ")+"\n")
	paused = false
	current_scene = null
	scene.queue_free()
	await frames(8)
	OS.delay_msec(80)
	await process_frame
	quit(0 if passed else 1)
