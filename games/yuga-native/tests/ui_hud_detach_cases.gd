extends SceneTree
## Real runtime resources remain valid when their HUD leaves the tree first.
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool) -> void:
	checks.append({"name":label,"passed":passed})
	print("PASS " if passed else "FAIL ",label)

func frames() -> void:
	for unused in range(5): await process_frame

func retire(scene: Node) -> void:
	paused = false
	scene.queue_free()
	current_scene = null
	await frames()
	OS.delay_msec(80)
	await process_frame

func _run() -> void:
	Bindings.install()
	Bindings.merge_settings({"rama_effects":{"reduced_effects":true,"reduced_motion":true}})
	var world: Node3D = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	await frames()
	world.set_paused(true)
	record("World guide connects the actual effect owner and saved preferences",world.rama_panel._effect_receiver()==world.rama_effects and world.rama_effects.report().reduced_effects and world.rama_effects.report().reduced_motion)
	var hud: Control = world.rama_hud
	var parent: Node = hud.get_parent()
	var before: Dictionary = world.rama_runtime.kit.report()
	parent.remove_child(hud)
	for unused in range(8): hud._refresh()
	var no_ready := true
	for label in hud.slots: no_ready = no_ready and not label.text.contains("READY")
	record("Detached live HUD retires readiness without accessing a missing tree",hud.note.text=="Practice unavailable" and hud.life_text.text=="—" and no_ready)
	record("Detached presentation leaves its actual runtime untouched",world.rama_runtime.kit.report()==before)
	parent.add_child(hud)
	hud._refresh()
	record("Reattached HUD reads the caller's actual paused state",hud.note.text=="Practice paused" and hud.life.value==world.rama_runtime.vitals.health)
	await retire(world)
	var court: Node3D = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(court)
	current_scene = court
	await frames()
	record("Training guide connects the actual effect owner and saved preferences",court.hero_panel._effect_receiver()==court.rama_effects and court.rama_effects.report().reduced_effects and court.rama_effects.report().reduced_motion)
	await retire(court)
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless real world/training scene resources, explicit HUD removal before owner teardown, and actual guide/effect receiver hooks. No rendering, OS input or hardware claim.","sources":{}}
	for path in ["res://scripts/rama_hero_hud.gd","res://scripts/rama_hero_panel.gd","res://scripts/confluence_world.gd","res://scripts/courtyard.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	quit(0 if passed else 1)
