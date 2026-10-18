extends SceneTree
## Detach after scheduling or starting asynchronous UI work; runner rejects logs.
const Shell = preload("res://scripts/launch_shell.gd")
const Guide = preload("res://scripts/rama_hero_panel.gd")
var output := ""
var checks: Array[Dictionary] = []
var sources := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func frames(count := 5) -> void:
	for unused in count: await process_frame

func record(label: String, ok: bool) -> void:
	checks.append({"name":label,"passed":ok})
	print("PASS " if ok else "FAIL ",label)

func run() -> void:
	for path in ["scripts/launch_shell.gd","scripts/courtyard.gd","scripts/confluence_world.gd","scripts/rama_hero_panel.gd","scripts/rama_hero_hud.gd", "tests/ui_independent_lifecycle_cases.gd"]:
		sources[path] = FileAccess.get_sha256("res://"+path)
	root.size = Vector2i(960,540)
	root.content_scale_size = Vector2i(1280,720)
	var recovery := Button.new()
	recovery.text = "Recovery owner"
	recovery.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(recovery)
	var shell := Shell.new()
	root.add_child(shell)
	await frames()
	print("PROBE shell queued reveal then detach")
	shell._layout()
	root.remove_child(shell)
	recovery.grab_focus()
	await frames()
	record("Detached launch cannot steal recovery focus",root.gui_get_focus_owner()==recovery)
	shell.free()
	var guide := Guide.new()
	root.add_child(guide)
	guide.open()
	print("PROBE guide deferred initial reveal then detach")
	root.remove_child(guide)
	recovery.grab_focus()
	await frames()
	record("Detached guide cannot steal recovery focus",root.gui_get_focus_owner()==recovery)
	guide.free()
	var court: Node3D = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(court)
	current_scene = court
	await frames()
	print("PROBE courtyard queued settings and resize reveal then detach")
	court._open_settings(true)
	court._layout_interface()
	current_scene = null
	root.remove_child(court)
	recovery.grab_focus()
	await frames()
	record("Detached courtyard leaves recovery focus and tree running",root.gui_get_focus_owner()==recovery and not paused)
	court.free()
	var world: Node3D = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	await frames()
	print("PROBE world queued pause and started HUD settle then detach")
	world.set_paused(true)
	world._settle_world_hud()
	current_scene = null
	root.remove_child(world)
	paused = false
	recovery.grab_focus()
	await frames()
	record("Detached world leaves recovery focus without stale modal restoration",root.gui_get_focus_owner()==recovery and not paused)
	world.free()
	var stable := true
	for path in sources: stable = stable and FileAccess.get_sha256("res://"+path)==sources[path]
	var report := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_start":sources,"source_unchanged":stable,"scope":"Real native UI and imported scenes, explicit queued/start-then-detach lifecycle counterexamples. The execution wrapper must reject any ERROR or SCRIPT ERROR even if focus assertions pass. No renderer or OS input claim."}
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	recovery.queue_free()
	await frames()
	quit(0 if report.passed else 1)
