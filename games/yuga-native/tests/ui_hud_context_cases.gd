extends SceneTree
## Existing native world authority; only terminal core health is staged for its normal outcome tick.
const Bindings = preload("res://scripts/input_bindings.gd")
const Hud = preload("res://scripts/rama_hero_hud.gd")
var checks: Array[Dictionary] = []
var output := ""
var scene: Node3D

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func frames(count: int = 4) -> void:
	for unused in range(count): await process_frame

func unavailable_slots(hud: Control) -> bool:
	for label in hud.slots:
		if label.text.contains("READY") or not label.text.split("\n")[0].ends_with("—"): return false
	return true

func _run() -> void:
	var unattached := Hud.new()
	root.add_child(unattached)
	record("Unconfigured HUD does not invent full life or ready actions",unattached.life_text.text=="—" and unattached.life.value==0 and unavailable_slots(unattached))
	unattached.queue_free()
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.set_paused(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.player.set_physics_process(false)
	scene.army.set_physics_process(false)
	var runtime: Node3D = scene.rama_runtime
	var hud: Control = scene.rama_hud
	hud.set_process(false)
	runtime.set_volume(0)
	hud._refresh()
	record("Configured world HUD reads real health and available kit",runtime.configured and hud.life.value==runtime.vitals.health and hud.slots[1].text.contains("READY") and hud.slots[0].text.contains(str(scene.player.MAGAZINE)))
	var clocks := Vector3(scene.army.elapsed,runtime.kit.elapsed,runtime.vitals.elapsed)
	var notice: String = runtime.notice
	scene.set_paused(true)
	var pause_focus: Control = root.gui_get_focus_owner()
	hud.clock = 0
	hud._process(1.0/60.0)
	record("Pause clears action readiness on the first presentation frame",hud.note.text=="Practice paused" and unavailable_slots(hud) and root.gui_get_focus_owner()==pause_focus and paused)
	for unused in range(20): hud._process(1.0/60.0)
	record("HUD pause presentation never advances authority or overwrites notices",Vector3(scene.army.elapsed,runtime.kit.elapsed,runtime.vitals.elapsed)==clocks and runtime.notice==notice)
	scene.set_paused(false)
	hud.clock = 0
	hud._process(1.0/60.0)
	record("Resume restores real readiness without waiting for the slot throttle",hud.note.text==runtime.notice and hud.slots[1].text.contains("READY") and not paused)
	scene.set_overview(true)
	hud._process(1.0/60.0)
	record("Overview uses its actual suspended practice state",hud.note.text=="Practice paused" and unavailable_slots(hud) and scene.overview and runtime.suspended)
	scene.set_overview(false)
	var damage: Dictionary = runtime.vitals.receive_damage(1000,"hud_context_defeat",runtime.vitals.generation,0)
	hud.clock = 0
	hud._process(1.0/60.0)
	record("Actual defeat preserves return timer and removes ready actions",damage.get("accepted",false) and hud.note.text=="RETURNING IN 3.0s" and unavailable_slots(hud) and hud.life.value==0)
	runtime.reset("HUD context reset")
	scene.army.reset()
	scene.set_paused(false)
	# Stage the terminal core boundary; the normal authority tick computes winner.
	scene.army.cores.moon = 0
	scene.army.step_simulation(.05)
	hud._process(1.0/60.0)
	record("Actual army outcome supersedes combat availability",scene.army.winner=="sun" and hud.note.text=="Round ended · Sun victory" and unavailable_slots(hud))
	scene.army.reset()
	runtime.reset("HUD context resumed round")
	scene.set_paused(false)
	Bindings.install("user://ui-hud-context.cfg")
	var remap: Dictionary = Bindings.set_binding("pulse",KEY_J)
	hud._refresh()
	record("HUD action names and keys use the saved binding source",remap.ok and hud.slots[1].text.begins_with("J  ·") and hud.slots[1].text.ends_with(Bindings.TITLES.pulse))
	for dimensions in [Vector2i(960,540),Vector2i(1280,720),Vector2i(1920,1080)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await frames()
		var bounds := hud.get_global_rect()
		var fits: bool = root.get_visible_rect().encloses(bounds) and bounds.encloses(hud.status_panel.get_global_rect())
		for slot in hud.slots: fits = fits and bounds.encloses(slot.get_parent().get_global_rect())
		record("HUD status and slots remain contained at "+str(dimensions),fits,{"hud":str(bounds)})
	var real_runtime: Node3D = hud.runtime
	hud.configure(null)
	record("Detaching runtime retires stale live readouts",hud.note.text=="Practice unavailable" and hud.life_text.text=="—" and unavailable_slots(hud))
	hud.configure(real_runtime)
	record("Reattaching actual runtime restores its state",hud.life.value==real_runtime.vitals.health and hud.slots[1].text.contains("READY"))
	Bindings.reset_defaults()
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://ui-hud-context.cfg"))
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless existing world, actual pause/overview/vitals, staged terminal core followed by normal outcome tick, binding persistence and HUD containment. No new render or OS input claim.","sources":{}}
	for path in ["res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_vitals.gd","res://scripts/rama_ability_kit.gd","res://scripts/input_bindings.gd","res://scripts/confluence_world.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	paused = false
	scene.queue_free()
	current_scene = null
	await frames()
	OS.delay_msec(80)
	await process_frame
	quit(0 if passed else 1)
