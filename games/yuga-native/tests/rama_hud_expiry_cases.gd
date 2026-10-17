extends SceneTree
## Real kit/vitals clocks followed by one normal 60 Hz HUD render update.
## No forced HUD refresh at expiry; no rendered or OS-input claim.
const STEP := .05
const FRAME := 1.0 / 60.0
var output := ""
var checks: Array[Dictionary] = []
var events: Array[Dictionary] = []
var sources: Dictionary = {}
var scene: Node3D

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func _run() -> void:
	for path in ["res://scripts/rama_hero_hud.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_vitals.gd","res://scripts/lane_army.gd","res://scripts/confluence_world.gd","res://assets/design/rama-ability-kit.json",get_script().resource_path]:
		sources[path] = FileAccess.get_sha256(path)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	for unused in range(6): await process_frame
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
	scene.army.reset()
	var vitals: Node = runtime.vitals
	var kit: Node3D = runtime.kit
	runtime.combat_event.connect(func(event: Dictionary): events.append(event.duplicate(true)))
	record("Fixture uses configured real kit, vitals and visible HUD", runtime.configured and kit.configured and vitals.configured and hud.is_visible_in_tree() and hud.slots.size() == 5)
	var origin: Vector3 = scene.player.global_position
	origin.y = 0
	var accepted: Dictionary = kit.request_ability("guardian_circle", origin, Vector3.FORWARD, origin)
	var begin := {}
	for event in events:
		if event.kind == "begin": begin = event
	record("Actual Guardian cast accepted around its real hero receiver", accepted.get("accepted",false) and not begin.is_empty(), accepted)
	if not accepted.get("accepted",false) or begin.is_empty():
		await finish()
		return
	var expiry: float = float(begin.timing.windup_s) + float(begin.timing.active_s)
	var expiry_tick := ceili(expiry / STEP - 1e-7)
	for unused in range(expiry_tick - 1): scene.army.step_simulation(STEP)
	# Establish the final live display through the ordinary process path.
	hud._process(.08)
	record("Final live authority tick displays real shield and field status", is_equal_approx(kit.elapsed,(expiry_tick-1)*STEP) and vitals.shield == 55 and hud.life_text.text == "300 / 300 +55" and hud.note.text == "Guardian Circle · field active", {"authority_s":kit.elapsed,"expiry_s":expiry,"shield":vitals.shield,"life_text":hud.life_text.text,"note":hud.note.text})
	# Worst phase of the previous 80 ms refresh throttle: it has just refreshed.
	hud.clock = 0
	scene.army.step_simulation(STEP)
	record("Exact authority expiry removes the ward before presentation retirement", is_equal_approx(kit.elapsed,expiry_tick*STEP) and vitals.shield == 0 and runtime.notice == "Rama is ready" and not kit.report().casts.is_empty(), {"authority_s":kit.elapsed,"shield":vitals.shield,"notice":runtime.notice})
	hud._process(FRAME)
	record("First 16.7 ms render after expiry removes visible shield and active note", hud.life_text.text == "300 / 300" and hud.note.text == "Rama is ready", {"render_delta":FRAME,"life_text":hud.life_text.text,"note":hud.note.text})
	hud.clock = 0
	var damage: Dictionary = vitals.receive_damage(25,"hud_expiry_damage",vitals.generation,0)
	hud._process(FRAME)
	record("First render after real damage updates health bar and number", damage.get("accepted",false) and hud.life.value == 275 and hud.life_text.text == "275 / 300" and hud.note.text == "Hit · 275 health", {"life":hud.life.value,"life_text":hud.life_text.text,"note":hud.note.text})
	hud.clock = 0
	var defeated: Dictionary = vitals.receive_damage(1000,"hud_expiry_defeat",vitals.generation,0)
	hud._process(FRAME)
	record("First render after defeat displays the live return timer", defeated.get("accepted",false) and not vitals.alive and hud.life.value == 0 and hud.life_text.text == "0 / 300" and hud.note.text == "RETURNING IN 3.0s", {"life":hud.life.value,"life_text":hud.life_text.text,"note":hud.note.text})
	hud.clock = 0
	runtime.reset("hud expiry fixture reset")
	hud._process(FRAME)
	record("First render after real reset clears stale defeat and shield data", vitals.alive and hud.life.value == 300 and hud.life_text.text == "300 / 300" and hud.note.text == "Rama is ready", {"life":hud.life.value,"life_text":hud.life_text.text,"note":hud.note.text})
	await finish()

func finish() -> void:
	var unchanged := true
	for path in sources: unchanged = unchanged and FileAccess.get_sha256(path) == sources[path]
	record("HUD authority sources remain unchanged during the fixture",unchanged)
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"sources":sources,"scope":"Real native-world kit/vitals authority steps followed by normal HUD _process(1/60). No forced refresh at expiry, renderer, OS input or performance claim."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	scene.queue_free()
	current_scene = null
	paused = false
	for unused in range(6): await process_frame
	OS.delay_msec(80)
	await process_frame
	quit(0 if passed else 1)
