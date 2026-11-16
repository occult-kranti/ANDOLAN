extends "res://tests/ui_i1_action_hud_cases.gd"
## New feedback is exercised through the mounted kit and actual fixed army clock.
## This suite proves state and geometry, not rendered readability or human feel.

func meter(index: int) -> Dictionary:
	return scene.rama_hud.slot_meters[index].report()

func refresh() -> void:
	scene.rama_hud._refresh()

func run() -> void:
	for path in ["res://scripts/rama_hero_hud.gd", "res://scripts/rama_ability_meter.gd", "res://scripts/rama_hero_panel.gd", "res://scripts/rama_ability_kit.gd", "res://assets/design/rama-ability-kit.json", get_script().resource_path]: source_start[path] = FileAccess.get_sha256(path)
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.rama_runtime.set_volume(0)
	scene.rama_runtime.combat_event.connect(func(event: Dictionary): events.append(event.duplicate(true)))
	await ground_fixture()
	refresh()
	check("Real ready kit has full cooldown strips and no invented lane charges", meter(1).mode == &"ready" and meter(1).fraction == 1 and meter(4).mode == &"ready" and meter(4).lanes.is_empty())
	var accepted: Dictionary = scene.cast_rama_ability("dawn_volley")
	refresh()
	check("Accepted volley starts three pending firing lanes", accepted.get("accepted", false) and meter(4).mode == &"windup" and meter(4).lanes == [false, false, false] and meter(1).mode == &"blocked", meter(4))
	for unused in 18: advance()
	refresh()
	check("Preparation never invents an early projectile launch", count("release") == 0 and meter(4).lanes == [false, false, false] and meter(4).fraction > .9, meter(4))
	advance()
	refresh()
	check("First authority release launches only lane one", count("release") == 1 and meter(4).mode == &"recovery" and meter(4).lanes == [true, false, false], meter(4))
	for unused in 2: advance()
	refresh()
	check("Second lane follows the actual one tenth second projectile delay", meter(4).lanes == [true, true, false], meter(4))
	for unused in 2: advance()
	refresh()
	check("Third lane follows its own authority delay", meter(4).lanes == [true, true, true], meter(4))
	var before: Dictionary = scene.rama_runtime.kit.report()
	var before_meter := meter(4)
	for unused in 60: scene.rama_hud._process(.05)
	check("Presentation-only time cannot launch arrows or advance cooldown", before == scene.rama_runtime.kit.report() and before_meter == meter(4))
	scene.set_paused(true)
	refresh()
	check("Paused meters suppress readiness and launch marks", scene.rama_hud.slot_meters.all(func(control): return control.mode == &"unavailable" and control.lanes.is_empty()), meter(4))
	scene.set_paused(false)
	refresh()
	check("Resume recovers the same actual cast without restarting its timeline", meter(4) == before_meter)
	for unused in 9: advance()
	refresh()
	var remaining: float = scene.rama_runtime.kit.report().cooldowns.dawn_volley
	check("Recovered ultimate returns to actual cooldown with no charge-like lane row", meter(4).mode == &"cooldown" and meter(4).lanes.is_empty() and is_equal_approx(meter(4).fraction, 1.0 - remaining / 18.0), meter(4))
	await ground_fixture()
	accepted = scene.cast_rama_ability("dawn_volley")
	advance()
	var cancelled: bool = scene.rama_runtime.kit.cancel_windup("feedback interruption")
	refresh()
	check("Interrupted preparation clears firing lanes while retaining spent cooldown", accepted.get("accepted", false) and cancelled and meter(4).lanes.is_empty() and meter(4).mode == &"cooldown" and scene.rama_hud._cast_receipts.is_empty(), meter(4))
	scene.rama_runtime.reset("feedback reset")
	refresh()
	check("Reset clears receipt cache and restores real readiness", scene.rama_hud._cast_receipts.is_empty() and meter(4).mode == &"ready" and meter(4).lanes.is_empty() and meter(4).fraction == 1)
	var all_spent := true
	for unused in scene.player.MAGAZINE:
		all_spent = scene.cast_rama_ability("kodanda").get("accepted", false) and all_spent
		for tick in 9: advance()
	refresh()
	check("Empty real magazine never advertises a usable bow", all_spent and scene.player.ammo == 0 and meter(0).mode == &"empty" and meter(0).fraction == 0 and scene.rama_hud.slot_glyphs[0].state == &"cooling" and scene.rama_hud.slots[0].text.contains("0 / 12") and scene.rama_hud.note.text.contains("Bow empty"), meter(0))
	check("Empty bow does not suppress independent ready abilities", scene.rama_hud.slot_meters.slice(1).all(func(control): return control.mode == &"ready"))
	var hit: Dictionary = scene.rama_runtime.vitals.receive_damage(1000, "feedback defeat", scene.rama_runtime.vitals.generation, 0)
	refresh()
	check("Defeat disables every new meter immediately", hit.get("accepted", false) and scene.rama_hud.slot_meters.all(func(control): return control.mode == &"unavailable" and control.fraction == 0 and control.lanes.is_empty()))
	await ground_fixture()
	refresh()
	var guide: Control = scene.rama_panel
	scene.set_paused(true)
	guide.open("confluence")
	await frames()
	before = scene.rama_runtime.kit.report()
	for id in IDS:
		guide.select_ability(id)
		check(id + " guide keeps exact rules and adds truthful counterplay", guide.detail_description.text == guide._rules[id].description and not guide.detail_power.text.is_empty() and guide.detail_tactics.text.contains("COUNTER") and guide.detail_tactics.text.contains("FOLLOW-UP"), {"output":guide.detail_power.text, "tactics":guide.detail_tactics.text})
	check("Reading tactical advice never casts or spends combat resources", before == scene.rama_runtime.kit.report())
	guide.close()
	scene.set_paused(false)
	for scale in [1.0, 1.5, 2.0]:
		root.size = Vector2i(960, 540)
		root.content_scale_size = Vector2i(1280, 720)
		root.content_scale_factor = scale
		refresh()
		await frames(6)
		var contained := true
		for index in 5:
			var control: Control = scene.rama_hud.slot_meters[index]
			contained = contained and scene.rama_hud.slot_cards[index].get_global_rect().encloses(control.get_global_rect()) and control.mouse_filter == Control.MOUSE_FILTER_IGNORE and control.focus_mode == Control.FOCUS_NONE
		check("Timing strips stay inside existing slots and add no input targets at " + str(scale), contained)
	var stable := true
	for path in source_start: stable = stable and source_start[path] == FileAccess.get_sha256(path)
	check("Feedback sources remain unchanged during execution", stable)
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":source_start,"scope":"Mounted fixed-tick ability release/delay, cancellation, pause, reset, defeat, read-only guide and logical 100/150/200% containment. Native rendering, OS input, listening and physical GPU remain separate."}
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(result, "  ") + "\n")
	paused = false
	current_scene = null
	scene.queue_free()
	await frames(8)
	OS.delay_msec(80)
	await process_frame
	quit(0 if result.passed else 1)
