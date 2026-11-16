extends SceneTree
var output := ""
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func frames(count := 3) -> void:
	for unused in count: await process_frame
func run() -> void:
	root.size = Vector2i(960,540); root.content_scale_size = root.size
	var world = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world); current_scene = world
	await frames()
	world.rama_runtime.set_volume(0)
	world.army.set_physics_process(false);world.player.set_physics_process(false)
	world.set_paused(false)
	world.army.cores.moon = 0
	world.army.step_simulation(.05)
	world.set_paused(true)
	await frames()
	var focused = root.gui_get_focus_owner()
	var restart = world.restart_practice_button
	var result = {"winner":world.army.winner,"summary_visible":world.outcome_summary.visible,"focused":str(focused.get_path()) if is_instance_valid(focused) else "<none>","expected_restart":str(restart.get_path()),"restart_focused":focused==restart,"scroll_vertical":world.pause_scroll.scroll_vertical,"scroll_rect":str(world.pause_scroll.get_global_rect()),"summary_rect":str(world.outcome_summary.get_global_rect()),"restart_rect":str(restart.get_global_rect()),"summary_heading_rect":str(world.outcome_summary.heading.get_global_rect()),"heading_inside_scroll":world.pause_scroll.get_global_rect().encloses(world.outcome_summary.heading.get_global_rect()),"restart_inside_scroll":world.pause_scroll.get_global_rect().encloses(restart.get_global_rect()),"metrics":world.match_metrics.report(),"summary_text":world.outcome_summary.detail.text,"scope":"Headless real terminal tick at960x540; reports actual focus/scroll rectangles, no pixel or OS input claim."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	print(JSON.stringify(result))
	paused=false;world.queue_free();current_scene=null;await frames();quit(0)
