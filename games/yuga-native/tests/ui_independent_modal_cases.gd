extends SceneTree
## Independent U3 modal interruption and compact keyboard access counterexamples.
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var output := ""
var source_start := {}
var closed_count := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func frames(count := 5) -> void:
	for unused in count: await process_frame

func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = down
		root.push_input(event)
		await frames(2)

func record(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(detail))

func run() -> void:
	for path in ["project.godot","scripts/courtyard.gd","scripts/confluence_world.gd","scripts/rama_hero_panel.gd","scripts/rama_hero_hud.gd","scripts/controls_overlay.gd","scripts/hero_ui_theme.gd","scripts/input_bindings.gd","assets/design/rama-ability-kit.json","tests/ui_independent_modal_cases.gd"]:
		source_start[path] = FileAccess.get_sha256("res://"+path)
	Bindings.install("user://ui-independent.cfg")
	root.size = Vector2i(960,540)
	root.content_scale_size = root.size
	var host := Control.new()
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(host)
	var guide := Guide.new()
	host.add_child(guide)
	guide.closed.connect(func(): closed_count += 1)
	guide.open("confluence")
	await frames()
	var detail_scroll: ScrollContainer = guide.find_child("DetailsScroll",true,false)
	for dimensions in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await frames()
		record("Guide fits logical viewport "+str(dimensions),root.get_visible_rect().encloses(guide.card.get_global_rect()),{"card":str(guide.card.get_global_rect())})
		for id in ["kodanda","piercing_dawn","measured_step","guardian_circle","dawn_volley"]:
			guide.select_ability(id)
			guide.ability_buttons[id].grab_focus()
			await frames()
			detail_scroll.scroll_vertical = 0
			await key(KEY_PAGEDOWN)
			var bar := detail_scroll.get_v_scroll_bar()
			var overflow := bar.max_value > bar.page+1
			record("Keyboard reaches overflowing guide detail "+id+" "+str(dimensions),not overflow or detail_scroll.scroll_vertical>0,{"overflow":overflow,"scroll":detail_scroll.scroll_vertical,"max":bar.max_value,"page":bar.page})
			await key(KEY_END)
			var at_end := absf(float(detail_scroll.scroll_vertical)-(bar.max_value-bar.page))<=1
			await key(KEY_HOME)
			record("End then Home traverses full guide detail "+id+" "+str(dimensions),at_end and detail_scroll.scroll_vertical==0)
	root.size = Vector2i(960,540)
	root.content_scale_size = root.size
	guide.detail_description.text = "A deliberately extended ability explanation preserves the final instruction. ".repeat(20)
	await frames()
	await key(KEY_END)
	var long_bar := detail_scroll.get_v_scroll_bar()
	record("Long guide explanation remains bounded and keyboard reachable",root.get_visible_rect().encloses(guide.card.get_global_rect()) and absf(float(detail_scroll.scroll_vertical)-(long_bar.max_value-long_bar.page))<=1,{"max":long_bar.max_value,"page":long_bar.page,"scroll":detail_scroll.scroll_vertical})
	host.hide()
	await key(KEY_ESCAPE)
	record("Hidden guide ancestor does not consume Escape or notify caller",closed_count==0 and guide.visible,{"closed_count":closed_count,"visible":guide.visible})
	host.show()
	guide.open()
	host.process_mode = Node.PROCESS_MODE_DISABLED
	await key(KEY_ESCAPE)
	record("Disabled guide owner isolates ALWAYS guide input",closed_count==0 and guide.visible,{"closed_count":closed_count,"visible":guide.visible})
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	host.queue_free()
	await frames()
	var court: Node3D = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(court)
	current_scene = court
	await frames()
	court.start_training()
	await key(KEY_F3)
	record("F3 suspends live training and opens guide",court.hero_panel.visible and paused and court.rama_runtime.suspended)
	root.focus_exited.emit()
	await key(KEY_ESCAPE)
	record("Focus loss during training guide returns to pause",paused and court.pause_panel.visible and court.rama_runtime.suspended,{"paused":paused,"pause_visible":court.pause_panel.visible,"player_active":court.player.active,"return_owner":court.hero_panel_return})
	court.set_paused(false)
	await key(KEY_F2)
	record("F2 suspends live training and opens help",court.help_panel.visible and paused)
	root.focus_exited.emit()
	await key(KEY_ESCAPE)
	record("Focus loss during training help returns to pause",paused and court.pause_panel.visible and court.rama_runtime.suspended,{"paused":paused,"pause_visible":court.pause_panel.visible,"player_active":court.player.active,"return_owner":court.help_return})
	paused = false
	court.queue_free()
	current_scene = null
	await frames()
	var world: Node3D = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	await frames()
	await key(KEY_ESCAPE)
	await frames()
	var pause_heading: Control = world.pause_scroll.get_child(0).get_child(0)
	record("Fresh compact pause retains full heading beside initial focus",world.pause_scroll.get_global_rect().encloses(pause_heading.get_global_rect()),{"heading":str(pause_heading.get_global_rect()),"scroll":str(world.pause_scroll.get_global_rect()),"offset":world.pause_scroll.scroll_vertical})
	await key(KEY_ESCAPE)
	world.set_overview(true)
	var before: Dictionary = world.army.report()
	await key(KEY_F3)
	await key(KEY_ESCAPE)
	record("Overview survives guide round-trip without enabling gameplay",world.overview and not world.paused and not world.player.active and world.rama_runtime.suspended and world.review_camera.current and world.army.report()==before)
	await key(KEY_F2)
	await key(KEY_ESCAPE)
	record("Overview survives controls round-trip without enabling gameplay",world.overview and not world.paused and not world.player.active and world.rama_runtime.suspended and world.review_camera.current and world.army.report()==before)
	world.set_overview(false)
	await key(KEY_F3)
	root.focus_exited.emit()
	await key(KEY_ESCAPE)
	record("World guide focus loss restores pause and inactive player",world.paused and paused and world.pause_panel.visible and not world.player.active and world.rama_runtime.suspended)
	world.set_paused(false)
	world.army.cores.moon = 0
	world.army.step_simulation(.05)
	world.set_paused(true)
	await frames()
	record("Compact terminal pause contains outcome summary and primary focus",world.pause_scroll.get_global_rect().encloses(world.outcome_summary.get_global_rect()) and world.pause_scroll.get_global_rect().encloses(root.gui_get_focus_owner().get_global_rect()),{"summary":str(world.outcome_summary.get_global_rect()),"focus":str(root.gui_get_focus_owner().get_global_rect()),"offset":world.pause_scroll.scroll_vertical})
	var terminal: Dictionary = world.army.report()
	await key(KEY_F3)
	await key(KEY_ESCAPE)
	record("Terminal guide round-trip preserves outcome and authority",world.army.report()==terminal and world.paused and paused and world.outcome_summary.is_visible_in_tree() and not world.player.active)
	await key(KEY_F2)
	await key(KEY_ESCAPE)
	record("Terminal controls round-trip preserves outcome and authority",world.army.report()==terminal and world.paused and paused and world.outcome_summary.is_visible_in_tree() and not world.player.active)
	paused = false
	world.queue_free()
	current_scene = null
	await frames()
	var source_end := {}
	for path in source_start: source_end[path] = FileAccess.get_sha256("res://"+path)
	var report := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_start":source_start,"source_end":source_end,"source_unchanged":source_start==source_end,"scope":"Independent actual imported offline scenes, native viewport key dispatch and Window.focus_exited signal. Guide logical layout960x540/1280x720; actual world/courtyard960x540. Source isolation and guide scroll probes use a real Control host, with one synthetic long explanation. No OS input, rendered pixels, 2x scale, online or GPU performance claim."}
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	quit(0 if report.passed else 1)
