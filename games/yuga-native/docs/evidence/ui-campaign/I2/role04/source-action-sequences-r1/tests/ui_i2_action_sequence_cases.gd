extends SceneTree
## I2 sequence stress on one actual world: capped frame hitches, death while
## acting, held respawn clocks, generation rejection, terminal/reset reentry.
const IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
var output := "/tmp/ui-i2-action-sequences.json"
var checks: Array[Dictionary] = []
var events: Array[Dictionary] = []
var scene: Node3D
var sources := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func frames(number := 5) -> void:
	for unused in number: await process_frame

func ground() -> void:
	scene.teleport_to(Vector3(-40,.05,-10),0)
	scene.player.yaw = PI
	scene.player.pitch = -.32
	scene.player._update_camera()
	scene.player.set_physics_process(true)
	for unused in 8: await physics_frame
	scene.player.set_physics_process(false)

func refresh() -> void:
	scene.rama_hud._process(.08)
	scene._update_practice_hud()

func held_snapshot() -> Dictionary:
	return {"army":scene.army.elapsed,"kit":scene.rama_runtime.kit.report(),"vitals":scene.rama_runtime.vitals.report(),"motion":scene.player.rama_motion.diagnostics()}

func run() -> void:
	for path in ["res://scripts/confluence_world.gd","res://scripts/player.gd","res://scripts/rama_motion.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_hero_hud.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_action_buffer.gd","res://scripts/rama_vitals.gd","res://scripts/lane_army.gd","res://assets/heroes/rama-hero.glb",get_script().resource_path]: sources[path] = FileAccess.get_sha256(path)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.rama_effects.set_process(false)
	scene.rama_hud.set_process(false)
	scene.rama_runtime.set_volume(0)
	scene.rama_runtime.combat_event.connect(func(event: Dictionary): events.append(event.duplicate(true)))
	for index in IDS.size():
		var id: String = IDS[index]
		scene.set_overview(false)
		scene._restart_army()
		scene.army.set_physics_process(false)
		await ground()
		scene.army._decision_clock = 10000
		scene.army._next_wave = 10000
		events.clear()
		var accepted: Dictionary = scene.cast_rama_ability(id)
		var before: float = scene.army.elapsed
		var kit_before: float = scene.rama_runtime.kit.elapsed
		scene.army._physics_process(.8)
		refresh()
		check(id+" hitch executes five bounded authoritative ticks",accepted.get("accepted",false) and is_equal_approx(scene.army.elapsed-before,.25) and is_equal_approx(scene.rama_runtime.kit.elapsed-kit_before,.25),{"army_before":before,"army_after":scene.army.elapsed,"kit_after":scene.rama_runtime.kit.elapsed})
		var invalid_before: Dictionary = scene.army.report()
		var kit_invalid_before: Dictionary = scene.rama_runtime.kit.report()
		for delta in [NAN, INF, -.2, 0.0]: scene.army._physics_process(delta)
		check(id+" invalid frame deltas cannot alter the active action",scene.army.report()==invalid_before and scene.rama_runtime.kit.report()==kit_invalid_before)
		var generation: int = scene.rama_runtime.vitals.generation
		var lethal: Dictionary = scene.rama_runtime.vitals.receive_damage(1000,"i2-lethal",generation,index+1)
		refresh()
		var old_releases := events.filter(func(event): return event.kind=="release").size()
		check(id+" lethal receipt cancels action and unavailable HUD together",lethal.accepted and not scene.rama_runtime.vitals.alive and scene.rama_runtime.kit.report().casts.is_empty() and scene.rama_runtime.action_buffer.report().pending.is_empty() and not scene.player.rama_action_locked and scene.rama_hud.note.text=="RETURNING IN 3.0s" and not scene.rama_hud.slots.any(func(slot):return slot.text.contains("READY")))
		scene.set_overview(true)
		scene.army.set_physics_process(true)
		scene.player.set_physics_process(true)
		var held := held_snapshot()
		for unused in 8: await physics_frame
		check(id+" defeated overview holds death pose and respawn clocks",held_snapshot()==held)
		scene.set_paused(true)
		var paused_state := held_snapshot()
		await frames(5)
		check(id+" overview plus pause preserves the same death generation",held_snapshot()==paused_state and scene.rama_hud.note.text.begins_with("RETURNING"))
		scene.army.set_physics_process(false)
		scene.player.set_physics_process(false)
		scene.set_overview(false)
		scene.set_paused(false)
		for unused in 11: scene.army._physics_process(.8)
		refresh()
		check(id+" repeated hitches stop before the real respawn deadline",not scene.rama_runtime.vitals.alive and is_equal_approx(scene.rama_runtime.vitals.report().respawn_remaining,.25) and scene.rama_hud.note.text=="RETURNING IN 0.3s",{"vitals":scene.rama_runtime.vitals.report(),"hud":scene.rama_hud.note.text})
		scene.army._physics_process(.8)
		refresh()
		var stale: Dictionary = scene.rama_runtime.vitals.receive_damage(1000,"i2-stale-generation",generation,999)
		check(id+" exact rule respawn rejects old damage and old releases",scene.rama_runtime.vitals.alive and scene.rama_hud.life.value==300 and scene.rama_runtime.vitals.generation>generation and not stale.accepted and events.filter(func(event):return event.kind=="release").size()==old_releases and scene.rama_runtime.action_buffer.report().pending.is_empty())
		# Same instance reentry: reset on actual grounded spawn, then end this
		# next action through the real core rule, not a fabricated outcome label.
		await ground()
		var next: Dictionary = scene.cast_rama_ability("dawn_volley")
		var winner: String = ["sun","moon","draw"][index%3]
		scene.army.cores = {"sun":0.0 if winner in ["moon","draw"] else 100.0,"moon":0.0 if winner in ["sun","draw"] else 100.0}
		scene.army.step_simulation(.05)
		refresh()
		check(id+" reentry terminal tick cancels the next action and disables slots",next.get("accepted",false) and scene.army.winner==winner and scene.paused and scene.outcome_summary.visible and scene.rama_runtime.kit.report().casts.is_empty() and scene.player.rama_motion.action_stage=="none" and not scene.rama_hud.slots.any(func(slot):return slot.text.contains("READY")),{"winner":scene.army.winner,"hud":scene.rama_hud.note.text})
		var terminal_clock: float = scene.army.elapsed
		for unused in 4: scene.army._physics_process(.8)
		refresh()
		check(id+" terminal hitches cannot revive authority or stale action",scene.army.elapsed==terminal_clock and scene.rama_runtime.kit.report().casts.is_empty() and scene.rama_hud.note.text.begins_with("Round ended"))
		scene._restart_army()
		refresh()
		check(id+" restart clears terminal presentation before the next sequence",scene.army.winner.is_empty() and not scene.outcome_summary.visible and scene.rama_hud.life.value==300 and not paused and scene.rama_hud.note.text=="Rama is ready")
	var stable := true
	for path in sources: stable = stable and sources[path]==FileAccess.get_sha256(path)
	check("I2 sequence sources stable",stable)
	var result := {"passed":checks.all(func(row):return row.passed),"checks":checks,"sources":sources,"scope":"New I2 repeated sequences in one actual world. Explicit .8s frame hitches use existing five-tick cap; actual damage and core inputs are declared fixtures through real rules. Real native pause/overview frames; no render, OS input, FPS or imported-asset regeneration."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused = false
	current_scene = null
	scene.queue_free()
	await frames(8)
	OS.delay_msec(100)
	await process_frame
	quit(0 if result.passed else 1)
