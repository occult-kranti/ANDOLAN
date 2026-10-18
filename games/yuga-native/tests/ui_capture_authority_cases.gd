extends SceneTree
## Real rule authority staging contract; no rendering or native-input claim.
var checks: Array = []
var output := ""
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")
func _run() -> void:
	var fixture = load("res://tools/ui-campaign/authority_stage.gd").new()
	var scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	for unused in 6: await process_frame
	for action in ["lane","relay-held","relay-contested","defeat","respawn","outcome-sun","outcome-moon","outcome-draw","release"]:
		var result: Dictionary = fixture.perform(scene,action)
		checks.append({"name":action,"passed":result.get("passed",false),"receipt":result})
		print("PASS " if result.get("passed",false) else "FAIL ",action)
	var passed: bool = checks.all(func(c): return c.passed)
	var result := {"passed":passed,"passed_count":checks.filter(func(c):return c.passed).size(),"count":checks.size(),"checks":checks,"sources":{}}
	for file in ["res://tools/ui-campaign/authority_stage.gd","res://scripts/confluence_world.gd","res://scripts/lane_army.gd","res://scripts/relay_control.gd",get_script().resource_path]: result.sources[file] = FileAccess.get_sha256(file)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(result,"\t")+"\n")
	paused = false
	scene.queue_free()
	current_scene = null
	for unused in 6: await process_frame
	OS.delay_msec(100)
	await process_frame
	quit(0 if passed else 1)
