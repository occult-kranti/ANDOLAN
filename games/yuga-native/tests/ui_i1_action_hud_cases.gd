extends SceneTree
## New I1 combined-source contract: actual request -> army event -> motion/HUD,
## with real pause/overview interruptions. No rendered or OS-input claim.
const IDS := ["kodanda","piercing_dawn","measured_step","guardian_circle","dawn_volley"]
const STEP := .05
var output := "/tmp/ui-i1-action-hud.json"
var checks: Array[Dictionary] = []
var events: Array[Dictionary] = []
var scene: Node3D
var source_start := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func count(kind: String) -> int:
	return events.filter(func(event): return event.kind==kind).size()

func frames(number := 4) -> void:
	for unused in number: await process_frame

func ground_fixture() -> void:
	scene.set_overview(false)
	scene._restart_army()
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.army.set_physics_process(false)
	scene.rama_effects.set_process(false)
	scene.rama_hud.set_process(false)
	scene.teleport_to(Vector3(-40,.05,-10),0)
	scene.player.yaw = PI
	scene.player.pitch = -.32
	scene.player._update_camera()
	scene.player.set_physics_process(true)
	for unused in 8: await physics_frame
	scene.player.set_physics_process(false)
	scene.army._decision_clock = 10000
	scene.army._next_wave = 10000
	events.clear()

func advance() -> void:
	scene.army.step_simulation(STEP)
	for unused in 3: scene.player._physics_process(1.0/60)
	scene.rama_effects.step(STEP)
	scene.rama_hud._process(STEP)

func run() -> void:
	for path in ["res://scripts/confluence_world.gd","res://scripts/player.gd","res://scripts/rama_motion.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_hero_hud.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_ability_effects.gd","res://scripts/lane_army.gd","res://assets/heroes/rama-hero.glb","res://assets/design/rama-ability-kit.json",get_script().resource_path]: source_start[path] = FileAccess.get_sha256(path)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.rama_runtime.set_volume(0)
	scene.rama_runtime.combat_event.connect(func(event: Dictionary): events.append(event.duplicate(true)))
	for id in IDS:
		await ground_fixture()
		var accepted: Dictionary = scene.cast_rama_ability(id)
		var motion: Node = scene.player.rama_motion
		check(id+" enters actual runtime and one rig action",accepted.get("accepted",false) and count("begin")==1 and scene.player.is_on_floor() and motion.action==id and motion.action_stage=="windup",{"response":accepted})
		if not accepted.get("accepted",false): continue
		scene.rama_hud._process(.08)
		var release_before: int = motion.release_count
		scene.army.set_physics_process(true)
		scene.player.set_physics_process(true)
		scene.set_paused(true)
		scene.rama_hud._process(1.0/60)
		var kit_before: Dictionary = scene.rama_runtime.kit.report()
		var motion_before: Dictionary = motion.diagnostics()
		var army_clock: float = scene.army.elapsed
		await frames(6)
		check(id+" real pause holds clocks and hides READY",kit_before==scene.rama_runtime.kit.report() and motion_before==motion.diagnostics() and scene.army.elapsed==army_clock and count("release")==0 and scene.rama_hud.note.text=="Practice paused" and not scene.rama_hud.slots.any(func(slot):return slot.text.contains("READY")))
		scene.army.set_physics_process(false)
		scene.player.set_physics_process(false)
		scene.set_paused(false)
		var ticks := 0
		while count("release")==0 and ticks<60:
			advance()
			ticks += 1
		check(id+" resumed army release reaches motion once",count("release")==1 and motion.release_count==release_before+1 and not motion.nocked and scene.rama_runtime.kit.elapsed>kit_before.elapsed,{"release_ticks":ticks,"events":events.filter(func(event):return event.kind in ["begin","release"])})
		scene.rama_hud._process(.08)
		var slot_index := IDS.find(id)
		var cooldown: float = scene.rama_runtime.kit.report().cooldowns.get(id,0)
		check(id+" HUD reports current authoritative resource",scene.rama_hud.slots[slot_index].text.contains("%.1fs"%cooldown) if id!="kodanda" else scene.rama_hud.slots[0].text.contains("%d / %d"%[scene.player.ammo,scene.player.MAGAZINE]),{"slot":scene.rama_hud.slots[slot_index].text,"cooldown":cooldown})
		var authority: Dictionary = scene.rama_runtime.kit.report()
		var army: Dictionary = scene.army.report()
		for unused in 12: scene.rama_hud._process(1.0/60)
		check(id+" HUD-only refresh cannot advance combat or cooldown",authority==scene.rama_runtime.kit.report() and army==scene.army.report())
	await ground_fixture()
	var accepted: Dictionary = scene.cast_rama_ability("kodanda")
	scene.set_overview(true)
	scene.player.set_physics_process(true)
	scene.army.set_physics_process(true)
	scene.rama_hud._process(1.0/60)
	var overview_kit: Dictionary = scene.rama_runtime.kit.report()
	var overview_motion: Dictionary = scene.player.rama_motion.diagnostics()
	var overview_army: float = scene.army.elapsed
	for unused in 8: await physics_frame
	check("overview holds active action authority and HUD availability",accepted.get("accepted",false) and overview_kit==scene.rama_runtime.kit.report() and overview_army==scene.army.elapsed and count("release")==0 and scene.rama_hud.note.text=="Practice paused")
	check("overview holds the same unreleased presentation clock",overview_motion.action_elapsed==scene.player.rama_motion.action_elapsed and overview_motion.stage==scene.player.rama_motion.action_stage,{"before":overview_motion,"after":scene.player.rama_motion.diagnostics()})
	scene.player.set_physics_process(false)
	scene.army.set_physics_process(false)
	scene.set_overview(false)
	scene.rama_runtime.reset("I1 reset witness")
	scene.rama_hud._process(1.0/60)
	check("reset clears action effects and restores truthful HUD",scene.player.rama_motion.action_stage=="none" and scene.rama_runtime.kit.report().casts.is_empty() and scene.rama_effects.report().active==0 and scene.rama_hud.note.text=="Rama is ready")
	scene.army.cores = {"sun":100.0,"moon":0.0}
	scene.army.step_simulation(STEP)
	scene.rama_hud._process(1.0/60)
	scene._update_practice_hud()
	check("real terminal tick synchronizes outcome and unavailable action slots",scene.army.winner=="sun" and scene.outcome_summary.is_visible_in_tree() and scene.rama_hud.note.text=="Round ended · Sun victory" and not scene.rama_hud.slots.any(func(slot):return slot.text.contains("READY")))
	var source_stable := true
	for path in source_start: source_stable = source_stable and FileAccess.get_sha256(path)==source_start[path]
	check("combined sources unchanged during new integration contract",source_stable)
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":source_start,"scope":"I1 newly executed actual combined scene requests, army fixed ticks, rig events and HUD process callbacks; real tree pause and overview with enabled native player callbacks. Terminal cores explicitly staged through real rules. No renderer, OS input, audible quality or FPS claim."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused = false
	current_scene = null
	scene.queue_free()
	await frames(8)
	OS.delay_msec(100)
	await process_frame
	quit(0 if result.passed else 1)
