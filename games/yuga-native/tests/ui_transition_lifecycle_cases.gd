extends SceneTree
## Integrated restart/defeat/disposal regression; explicit offline damage fixture.
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func record(label: String, passed: bool) -> void:
	checks.append({"name":label,"passed":passed})
	print("PASS " if passed else "FAIL ",label)

func frames(count: int = 4) -> void:
	for unused in range(count): await process_frame

func until(predicate: Callable, seconds: int = 60) -> bool:
	var deadline := Time.get_ticks_msec() + seconds * 1000
	while Time.get_ticks_msec() < deadline:
		if predicate.call(): return true
		await process_frame
	return false

func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = down
		Input.parse_input_event(event)
		await frames()

func run() -> void:
	root.size = Vector2i(960,600)
	change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
	record("Boot reaches native courtyard", await until(func(): return current_scene != null and current_scene.scene_file_path == "res://scenes/courtyard.tscn"))
	await frames()
	var court := current_scene
	var loader: Control = root.get_node("YugaSceneTransitionLayer/SceneTransition")
	court.start_training()
	var damage: Dictionary = court.rama_runtime.vitals.receive_damage(1000.0,"lifecycle-training",-1,1)
	record("Training defeat fixture uses actual receiver", damage.accepted and not court.rama_runtime.vitals.alive and not court.player.active)
	await key(KEY_F5)
	record("Training reset restores hero without stale loader", court.rama_runtime.vitals.alive and court.player.active and not loader.visible and not root.has_meta(loader.OWNER_META))
	court.rama_runtime.vitals.receive_damage(1000.0,"lifecycle-paused-reset",-1,1)
	await key(KEY_ESCAPE)
	court.reset_training()
	var paused_time: float = court.practice_army.elapsed
	await frames(12)
	record("Paused training reset stays inactive with suspended clocks", paused and court.rama_runtime.vitals.alive and not court.player.active and court.rama_runtime.suspended and court.practice_army.elapsed == paused_time)
	await key(KEY_ESCAPE)
	record("Resuming paused reset restores training input", not paused and court.player.active and not court.rama_runtime.suspended)
	court.return_to_menu()
	record("Title reset never enables gameplay", not court.started and not court.player.active and court.main_panel.visible)
	for index in range(3):
		court.enter_confluence()
		loader.cancel()
		await frames()
		record("Repeated cancel restores title " + str(index + 1), current_scene == court and court.ui.process_mode == Node.PROCESS_MODE_ALWAYS and court.world.process_mode == Node.PROCESS_MODE_PAUSABLE and court.main_panel.launch_state == "ready" and not loader.visible)
	court.enter_confluence()
	record("World loads after cancelled attempts", await until(func(): return current_scene != null and current_scene.scene_file_path == "res://scenes/confluence_world.tscn"))
	await frames()
	var world := current_scene
	damage = world.rama_runtime.vitals.receive_damage(1000.0,"lifecycle-world",-1,1)
	record("World defeat deactivates gameplay", damage.accepted and not world.rama_runtime.vitals.alive and not world.player.active)
	await key(KEY_ESCAPE)
	var death_generation: int = world.rama_runtime.vitals.generation
	var army_time: float = world.army.elapsed
	world.return_to_courtyard()
	loader.cancel()
	await frames(12)
	record("Cancelled return preserves paused defeat and simulation time", current_scene == world and paused and world.paused and not world.rama_runtime.vitals.alive and world.rama_runtime.vitals.generation == death_generation and world.army.elapsed == army_time)
	await key(KEY_ESCAPE)
	record("World resumes and respawns on its actual timer", await until(func(): return world.rama_runtime.vitals.alive, 12))
	record("Respawn restores player without overlay ownership", world.player.active and not loader.visible and not root.has_meta(loader.OWNER_META))
	world.rama_runtime.vitals.receive_damage(1000.0,"lifecycle-restart",-1,1)
	await key(KEY_F5)
	record("World restart clears defeat without stale transition", world.rama_runtime.vitals.alive and world.player.active and not loader.visible and world.army.winner.is_empty())
	await key(KEY_ESCAPE)
	world.return_to_courtyard()
	loader.queue_free()
	await frames()
	record("Disposing active loader restores explicit world and UI modes", world.process_mode == Node.PROCESS_MODE_ALWAYS and world.world.process_mode == Node.PROCESS_MODE_PAUSABLE and world.ui.process_mode == Node.PROCESS_MODE_ALWAYS and world.paused and paused)
	record("Disposed loader releases its root ownership", not root.has_meta(&"yuga_scene_transition_owner"))
	world.return_to_courtyard()
	loader = root.get_node("YugaSceneTransitionLayer/SceneTransition")
	record("Host recreates disposed loader without duplicate layer", is_instance_valid(loader) and root.find_children("YugaSceneTransitionLayer","CanvasLayer",false,false).size() == 1)
	record("Recreated loader completes real return", await until(func(): return current_scene != null and current_scene.scene_file_path == "res://scenes/courtyard.tscn"))
	await frames()
	record("Final title owns usable input", current_scene.main_panel.visible and not paused and not loader.visible and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE)
	var failures := checks.filter(func(item: Dictionary): return not item.passed)
	var result := {"suite":"ui-transition-lifecycle","passed":failures.is_empty(),"passed_count":checks.size()-failures.size(),"count":checks.size(),"failed":failures.size(),"checks":checks,"scope":"Actual imported offline training/world, seeded legitimate damage receiver, normal respawn timer, native keyboard reset/pause, and active loader disposal; no rendered acceptance.","sources":{}}
	for path in ["scripts/scene_transition.gd","scripts/courtyard.gd","scripts/confluence_world.gd","scripts/combat_film.gd","tests/ui_transition_lifecycle_cases.gd"]: result.sources[path] = FileAccess.get_sha256("res://"+path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(result,"\t")+"\n")
	print(JSON.stringify({"passed":result.passed,"failed":result.failed}))
	current_scene.queue_free()
	root.get_node("YugaSceneTransitionLayer").queue_free()
	await frames()
	call_deferred("quit",0 if failures.is_empty() else 1)
