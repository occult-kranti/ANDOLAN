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
	shell._layout()
	var newer: Control = shell._actions[-1]
	newer.grab_focus()
	await frames()
	record("Delayed launch reveal preserves a newer action focus",root.gui_get_focus_owner()==newer)
	print("PROBE shell queued reveal then detach")
	shell._layout()
	shell._reveal_resized_focus()
	root.remove_child(shell)
	recovery.grab_focus()
	await frames()
	record("Detached launch cannot steal recovery focus",root.gui_get_focus_owner()==recovery)
	shell.free()
	var guide := Guide.new()
	root.add_child(guide)
	guide.open()
	guide._reveal_initial_choice()
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
	root.content_scale_factor = 2.0
	await frames()
	court._open_settings(true)
	court.settings_back.grab_focus()
	await frames()
	record("Settings settle preserves newer Done focus at 2x scale",root.gui_get_focus_owner()==court.settings_back and root.get_visible_rect().encloses(court.settings_back.get_global_rect()))
	print("PROBE courtyard queued settings and resize reveal then detach")
	court._open_settings(true)
	court._layout_interface()
	court._settle_settings_entry()
	court._reveal_resized_modal_focus()
	current_scene = null
	root.remove_child(court)
	recovery.grab_focus()
	await frames()
	record("Detached courtyard leaves recovery focus and tree running",root.gui_get_focus_owner()==recovery and not paused)
	court.free()
	root.content_scale_factor = 1.0
	var world: Node3D = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	await frames()
	world.set_paused(true)
	var opener: Control = world.pause_actions[-1]
	opener.grab_focus()
	world._open_rama_panel()
	root.content_scale_factor = 2.0
	await frames()
	var guide_focus := root.gui_get_focus_owner()
	record("Queued pause reveal leaves the newer guide in control through 2x resize",world.rama_panel.visible and is_instance_valid(guide_focus) and world.rama_panel.is_ancestor_of(guide_focus) and paused)
	world.rama_panel.close()
	await frames()
	record("Guide close restores exact lower pause opener after 2x resize",root.gui_get_focus_owner()==opener and world.pause_scroll.get_global_rect().encloses(opener.get_global_rect()) and paused)
	print("PROBE world queued pause and started HUD settle then detach")
	world.set_paused(true)
	world._reveal_pause_focus()
	world._settle_world_hud()
	current_scene = null
	root.remove_child(world)
	paused = false
	recovery.grab_focus()
	await frames()
	record("Detached world leaves recovery focus without stale modal restoration",root.gui_get_focus_owner()==recovery and not paused)
	world.free()
	var retiring := Shell.new()
	root.add_child(retiring)
	await frames()
	retiring._layout()
	retiring._reveal_resized_focus()
	retiring.queue_free()
	recovery.grab_focus()
	await frames()
	record("Queued-free launch cancels queued and suspended focus work",not is_instance_valid(retiring) and root.gui_get_focus_owner()==recovery)
	var stable := true
	for path in sources: stable = stable and FileAccess.get_sha256("res://"+path)==sources[path]
	var report := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_start":sources,"source_unchanged":stable,"scope":"Real native UI and imported scenes, explicit queued/start-then-detach lifecycle counterexamples. The execution wrapper must reject any ERROR or SCRIPT ERROR even if focus assertions pass. No renderer or OS input claim."}
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	recovery.queue_free()
	await frames()
	quit(0 if report.passed else 1)
