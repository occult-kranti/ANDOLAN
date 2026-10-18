extends SceneTree
## Real configured boot/title/world hosts. Mounted resources are not GPU readiness.
const Transition = preload("res://scripts/scene_transition.gd")
var loader: Control
var checks: Array[Dictionary] = []
var phases: Array[Dictionary] = []
var mounts: Array[Dictionary] = []
var sources: Dictionary = {}
var output := ""

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output=argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)

func frames(count: int = 2) -> void:
	for unused in count: await process_frame

func wait_mount(count: int) -> bool:
	var deadline := Time.get_ticks_msec()+30000
	while mounts.size()<count and Time.get_ticks_msec()<deadline:
		if loader.phase==&"error": return false
		await process_frame
	return mounts.size()==count

func scene_snapshot() -> Dictionary:
	var scene := current_scene
	if not is_instance_valid(scene): return {"scene":"none"}
	var runtime: Node = scene.get("rama_runtime")
	var hud: Control = scene.get("rama_hud")
	var result := {"scene":scene.scene_file_path,"instance":scene.get_instance_id(),
		"process_frame":Engine.get_process_frames(),"physics_frame":Engine.get_physics_frames(),
		"paused":paused,"loader_phase":String(loader.phase),"loader_visible":loader.visible}
	if not is_instance_valid(runtime) or not is_instance_valid(hud): return result
	result.merge({"runtime":runtime.get_instance_id(),"configured":runtime.configured,
		"hero_model_ready":scene.player.model_ready,"player_active":scene.player.active,
		"suspended":runtime.suspended,"kit_generation":runtime.kit.generation,
		"hud_runtime":hud.runtime.get_instance_id(),"hud_visible":hud.is_visible_in_tree(),
		"availability":String(hud._availability()),"note":hud.note.text,
		"slots":hud.slots.map(func(slot):return slot.text),
		"health":runtime.vitals.health,"hud_health":hud.life.value,
		"ready":scene.world_ready if scene.scene_file_path.ends_with("confluence_world.tscn") else scene.environment_ready})
	return result

func on_phase(phase: StringName, message: String, progress: float) -> void:
	phases.append({"phase":String(phase),"destination":String(loader.destination),
		"message":message,"resource_progress":progress,"process_frame":Engine.get_process_frames(),
		"scene":current_scene.scene_file_path if is_instance_valid(current_scene) else "none",
		"hero_huds":root.find_children("RamaHeroHUD","Control",true,false).size()})

func mounted(_destination: StringName) -> void:
	mounts.append(scene_snapshot())

func ready_binding(snapshot: Dictionary) -> bool:
	return snapshot.get("ready",false) and snapshot.get("hero_model_ready",false) and snapshot.get("configured",false) and snapshot.get("runtime",0)==snapshot.get("hud_runtime",-1)

func run() -> void:
	for path in [get_script().resource_path,"res://project.godot","res://scripts/boot.gd",
		"res://scripts/scene_transition.gd","res://scripts/loading_presentation.gd","res://scripts/rama_hero_hud.gd",
		"res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://scripts/player.gd",
		"res://scripts/rama_hero_runtime.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_motion.gd",
		"res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero.glb.import"]:
		sources[path]=FileAccess.get_sha256(path)
	loader=Transition.ensure_for_tree(self)
	loader.phase_changed.connect(on_phase)
	loader.completed.connect(mounted)
	check("Configured application starts at the light boot scene",ProjectSettings.get_setting("application/run/main_scene","")=="res://scenes/boot.tscn")
	check("Real configured boot mounts successfully",change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))==OK)
	if not await wait_mount(1):
		check("Boot reaches its title mount before the deadline",false,{"phase":loader.snapshot()})
		await finish();return
	check("Queued boot status precedes any hero HUD construction",phases.any(func(row):return row.phase=="queued" and row.scene=="res://scenes/boot.tscn" and row.hero_huds==0))
	check("Title completion binds ready local resources and the current HUD owner",ready_binding(mounts[0]) and mounts[0].scene=="res://scenes/courtyard.tscn",mounts[0])
	await frames()
	var court: Node = current_scene
	var title := scene_snapshot()
	check("Title keeps inactive combat readouts hidden",not court.started and not title.hud_visible and title.availability!="active" and not title.slots.any(func(text):return text.contains("READY")),title)
	court.start_training()
	await frames()
	var training := scene_snapshot()
	check("Training exposes only the current configured kit and actual vitality",training.hud_visible and training.availability=="active" and training.runtime==training.hud_runtime and training.hud_health==training.health,training)
	court.return_to_menu()
	await frames()
	var old_runtime: int=court.rama_runtime.get_instance_id()
	var old_generation: int=court.rama_runtime.kit.generation
	check("World request starts through the actual title host",court._begin_scene_transition(&"confluence",court.main_panel.primary_button))
	check("Pending navigation isolates title world and UI immediately",court.process_mode==Node.PROCESS_MODE_DISABLED and court.world.process_mode==Node.PROCESS_MODE_DISABLED and court.ui.process_mode==Node.PROCESS_MODE_DISABLED)
	loader.cancel()
	await frames()
	check("Cancel retains the same authority and restores the real primary focus",current_scene==court and court.rama_runtime.get_instance_id()==old_runtime and court.rama_runtime.kit.generation==old_generation and root.gui_get_focus_owner()==court.main_panel.primary_button and not loader.visible)
	court._begin_scene_transition(&"confluence",court.main_panel.primary_button)
	# This is a real Godot window signal, deliberately emitted by the fixture;
	# it establishes host pause policy, not operating-system focus acceptance.
	root.focus_exited.emit()
	if not await wait_mount(2):
		check("World reaches its mount before the deadline",false,{"phase":loader.snapshot()})
		await finish();return
	check("World completion follows synchronous resource and HUD configuration",ready_binding(mounts[1]) and mounts[1].scene=="res://scenes/confluence_world.tscn",mounts[1])
	check("Remembered focus loss hands off to the new world's pause policy",mounts[1].paused and mounts[1].suspended and not mounts[1].player_active,mounts[1])
	await frames()
	var world: Node = current_scene
	var held := scene_snapshot()
	check("First processed paused HUD cannot advertise ready actions",held.availability=="paused" and held.note=="Practice paused" and not held.slots.any(func(text):return text.contains("READY")),held)
	root.focus_entered.emit()
	world.set_paused(false)
	await frames()
	var live := scene_snapshot()
	check("Resume reads the current live kit and actual health",live.availability=="active" and live.hud_visible and live.hud_health==live.health and live.runtime==live.hud_runtime,live)
	var retired_runtime: int=world.rama_runtime.get_instance_id()
	world.return_to_courtyard()
	check("World return uses the existing persistent loader",world._return_transition==loader and loader.is_busy())
	if not await wait_mount(3):
		check("Return reaches the title mount before the deadline",false,{"phase":loader.snapshot()})
		await finish();return
	await frames()
	var returned := scene_snapshot()
	check("Return title owns fresh ready resources without a stale HUD binding",ready_binding(returned) and returned.runtime!=retired_runtime and not returned.hud_visible and returned.scene=="res://scenes/courtyard.tscn",returned)
	check("Three scene mounts retain exactly one idle navigation owner",mounts.size()==3 and loader.phase==&"done" and not loader.visible and not root.has_meta(Transition.OWNER_META) and root.find_children("YugaSceneTransitionLayer","CanvasLayer",false,false).size()==1)
	check("Only resource loading exposes bounded progress, never actor or GPU readiness",phases.all(func(row):return (row.resource_progress==-1.0 or (row.phase=="loading" and row.resource_progress>=0.0 and row.resource_progress<=1.0))) and phases.any(func(row):return row.phase=="constructing"))
	await finish()

func finish() -> void:
	var unchanged := true
	for path in sources: unchanged=unchanged and sources[path]==FileAccess.get_sha256(path)
	check("Executed readiness sources remain unchanged",unchanged)
	var passed := checks.all(func(row):return row.passed)
	var report := {"passed":passed,"count":checks.size(),"checks":checks,"phases":phases,"mounts":mounts,"sources":sources,
		"scope":"Actual configured boot, local training, threaded world and return routes with current HUD bindings. Focus loss is an explicitly emitted window signal. Mount/first processed HUD are distinct from first rendered pixels, shader readiness, OS input and performance."}
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	paused=false
	if is_instance_valid(current_scene): current_scene.queue_free()
	var layer := root.get_node_or_null("YugaSceneTransitionLayer")
	if is_instance_valid(layer): layer.queue_free()
	await frames(10)
	quit(0 if passed else 1)
