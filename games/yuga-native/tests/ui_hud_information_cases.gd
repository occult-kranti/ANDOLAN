extends SceneTree
## Real-world HUD containment and readable critical text; no rendered-input claim.
var checks: Array[Dictionary] = []
var output := ""
var scene: Node3D
var sources := {}

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func frames() -> void:
	for unused in range(6): await process_frame

func opaque_surface(label: Label) -> PanelContainer:
	var parent := label.get_parent()
	while parent is Control:
		if parent is PanelContainer:
			var style := parent.get_theme_stylebox("panel") as StyleBoxFlat
			if style and style.bg_color.a >= .999: return parent
		parent = parent.get_parent()
	return null

func luminance(color: Color) -> float:
	var linear := color.srgb_to_linear()
	return .2126 * linear.r + .7152 * linear.g + .0722 * linear.b

func contrast(label: Label, surface: PanelContainer) -> float:
	if not surface: return 0
	var style := surface.get_theme_stylebox("panel") as StyleBoxFlat
	var text_light := luminance(label.get_theme_color("font_color"))
	var back_light := luminance(style.bg_color)
	return (maxf(text_light,back_light)+.05)/(minf(text_light,back_light)+.05)

func count_nodes(node: Node) -> int:
	var result := 1
	for child in node.get_children(): result += count_nodes(child)
	return result

func _run() -> void:
	for path in ["res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_vitals.gd","res://scripts/confluence_world.gd",get_script().resource_path]:
		sources[path] = FileAccess.get_sha256(path)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.set_paused(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.player.set_physics_process(false)
	scene.army.set_physics_process(false)
	scene.rama_effects.set_process(false)
	var runtime: Node3D = scene.rama_runtime
	var hud: Control = scene.rama_hud
	hud.set_process(false)
	runtime.set_volume(0)
	var node_count := count_nodes(hud)
	var authority_time: float = scene.army.elapsed
	var vitality_time: float = runtime.vitals.elapsed
	var kit_time: float = runtime.kit.elapsed
	var notices: Array[String] = ["Rama is ready", "Guardian Circle · field active", "Field active · " + "Stay close to allies and watch incoming siege blasts. ".repeat(8), "A".repeat(300), ""]
	for dimensions in [Vector2i(960,600),Vector2i(1280,720),Vector2i(1920,1080)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await frames()
		var initial_rect: Rect2 = hud.get_global_rect()
		var failures: Array[String] = []
		for notice in notices:
			runtime.notice = notice
			for unused in range(12): hud._process(1.0/60.0)
			await frames()
			var status_surface := opaque_surface(hud.note)
			var health_surface := opaque_surface(hud.life_text)
			if not status_surface or not health_surface:
				failures.append("critical labels have no opaque backing")
				continue
			if contrast(hud.note,status_surface) < 4.5 or contrast(hud.life_text,health_surface) < 4.5: failures.append("critical text contrast below 4.5:1")
			for label in [hud.note,hud.life_text]:
				if not opaque_surface(label).get_global_rect().encloses(label.get_global_rect()): failures.append("critical label escapes its backing")
			if not initial_rect.is_equal_approx(hud.get_global_rect()): failures.append("notice changes the HUD footprint")
			if not hud.get_global_rect().encloses(status_surface.get_global_rect()): failures.append("status backing escapes the HUD")
			if hud.note.text != notice or hud.life_text.text != "300 / 300": failures.append("notice changes health or source copy")
			if hud.note.text_overrun_behavior != TextServer.OVERRUN_TRIM_ELLIPSIS: failures.append("long notice has no visible truncation cue")
			for card in hud.slot_cards:
				if status_surface.get_global_rect().intersects(card.get_global_rect()): failures.append("critical status overlaps ability card")
			if not root.get_visible_rect().encloses(hud.get_global_rect()): failures.append("HUD outside viewport")
		var surface := opaque_surface(hud.note)
		record("Critical information retains readable backing and stable bounds "+str(dimensions), failures.is_empty(), {"failures":failures,"notice_cases":notices.size(),"hud_rect":str(hud.get_global_rect()),"status_contrast":contrast(hud.note,surface),"health_contrast":contrast(hud.life_text,opaque_surface(hud.life_text))})
	record("Repeated presentation updates neither grow nodes nor advance authority", count_nodes(hud)==node_count and scene.army.elapsed==authority_time and runtime.vitals.elapsed==vitality_time and runtime.kit.elapsed==kit_time, {"nodes_before":node_count,"nodes_after":count_nodes(hud),"updates":180,"army_time":scene.army.elapsed,"vitals_time":runtime.vitals.elapsed,"kit_time":runtime.kit.elapsed})
	runtime.notice = "Rama is ready"
	var hit: Dictionary = runtime.vitals.receive_damage(299,"information_low_life",runtime.vitals.generation,0)
	hud._process(1.0/60.0)
	record("Actual low health is visible on the first presentation update", hit.get("accepted",false) and hud.life.value==1 and hud.life_text.text=="1 / 300" and hud.note.text=="Hit · 1 health", {"health":hud.life_text.text,"notice":hud.note.text})
	var defeated: Dictionary = runtime.vitals.receive_damage(1,"information_defeat",runtime.vitals.generation,0)
	hud._process(1.0/60.0)
	record("Actual defeat replaces an ordinary notice immediately", defeated.get("accepted",false) and hud.life.value==0 and hud.life_text.text=="0 / 300" and hud.note.text=="RETURNING IN 3.0s", {"health":hud.life_text.text,"notice":hud.note.text})
	runtime.reset("information fixture reset")
	hud._process(1.0/60.0)
	record("Reset restores maximum health and clears defeat copy", hud.life.value==300 and hud.life_text.text=="300 / 300" and hud.note.text=="Rama is ready")
	var unchanged := true
	for path in sources: unchanged = unchanged and FileAccess.get_sha256(path)==sources[path]
	record("Tested source files remain unchanged during the fixture",unchanged)
	var passed := true
	for check in checks: passed = passed and check.passed
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify({"passed":passed,"checks":checks,"sources":sources,"scope":"Headless real-world layout and runtime vitals, synthetic long/empty status text, computed shared-surface text contrast. No rendered pixels, OS input, localization or arbitrary narrow-window claim."},"\t")+"\n")
		else: passed = false
	scene.queue_free()
	current_scene = null
	paused = false
	await frames()
	OS.delay_msec(80)
	await process_frame
	quit(0 if passed else 1)
