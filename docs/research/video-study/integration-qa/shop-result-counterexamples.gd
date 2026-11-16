extends SceneTree
## Independent read-only integration probes. Only test fixtures alter initial state.
const SOURCE_PATHS := ["res://scripts/confluence_world.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_vitals.gd","res://scripts/rama_ability_kit.gd","res://scripts/lane_army.gd","res://scripts/native_field_shop.gd","res://scripts/native_field_shop_panel.gd","res://assets/design/native-field-shop.json","res://scripts/combat_match_metrics.gd","res://scripts/world_outcome_summary.gd","res://scripts/input_bindings.gd"]
var scene: Node3D
var checks: Array = []
var sources: Dictionary = {}
var output := ""
var next_event := 810000
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func check(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"evidence":evidence})
	print("PASS " if passed else "FAIL ",label)
func frames(count := 3) -> void:
	for unused in count: await process_frame
func key(code: int) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code; event.physical_keycode = code; event.pressed = down
		root.push_input(event)
		await frames(2)
func impact(overrides: Dictionary = {}) -> Dictionary:
	next_event += 1
	var value := {"kind":"impact","team":"moon","id":next_event,"target":scene.player.global_position,"radius":3.0,"damage":40.0,"cancelled":false}
	value.merge(overrides,true)
	return value
func send(value: Dictionary) -> void: scene.army.siege_event.emit(value)
func run() -> void:
	for path in SOURCE_PATHS: sources[path] = FileAccess.get_sha256(path)
	sources[get_script().resource_path] = FileAccess.get_sha256(get_script().resource_path)
	root.size = Vector2i(960,540);root.content_scale_size = root.size
	scene = load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene = scene
	await frames()
	scene.rama_runtime.set_volume(0)
	scene.army.set_physics_process(false);scene.player.set_physics_process(false)
	var vitals = scene.rama_runtime.vitals
	await key(KEY_F4)
	check("Actual F4 dispatch opens live input-blocking shop",scene.field_shop_panel.visible and not scene.player.active and not scene.rama_runtime.suspended and not paused)
	var before: float = vitals.health
	var event := impact()
	send(event)
	check("Accepted enemy impact reduces real health while shop remains open",is_equal_approx(vitals.health,before-40) and scene.field_shop_panel.visible and not scene.player.active)
	check("Recorder counts actual shop-time damage rather than UI state",is_equal_approx(scene.match_metrics.report().hero.damage_taken,40))
	before = vitals.health
	send(event)
	check("Repeated siege ID cannot apply its receipt twice",is_equal_approx(vitals.health,before) and is_equal_approx(scene.match_metrics.report().hero.damage_taken,40))
	for fixture in [{"cancelled":true},{"team":"sun"},{"kind":"windup"},{"radius":-1.0},{"target":scene.player.global_position+Vector3(20,0,0)},{"target":scene.player.global_position+Vector3(0,5,0)}]: send(impact(fixture))
	check("Cancelled friendly nonimpact invalid and distant events do not damage",is_equal_approx(vitals.health,before) and is_equal_approx(scene.match_metrics.report().hero.damage_taken,40))
	var accepted_casts: int = scene.rama_runtime.kit.accepted_casts
	var response: Dictionary = scene.cast_rama_ability("kodanda")
	check("Shop blocks a real cast without spending ability state",not response.accepted and scene.rama_runtime.kit.accepted_casts==accepted_casts)
	scene.field_shop_panel.refresh()
	scene.field_shop_panel.rows.heal.button.pressed.emit()
	check("Actual buy heals without erasing recorded damage or inventing lane earnings",vitals.health==300 and scene.field_shop.report().wallet==85 and scene.match_metrics.report().gold==scene.army.gold and is_equal_approx(scene.match_metrics.report().hero.damage_taken,40))
	scene.set_paused(true)
	before = vitals.health
	send(impact())
	check("Pause closes shop and retains genuine damage immunity",not scene.field_shop_panel.visible and scene.rama_runtime.suspended and is_equal_approx(vitals.health,before))
	scene.set_paused(false);scene.set_overview(true)
	send(impact())
	check("Overview remains suspended after the active-input guard removal",scene.rama_runtime.suspended and is_equal_approx(vitals.health,before))
	scene.set_overview(false)
	for unused in 24: scene.army.step_simulation(.05)
	for winner in ["sun","moon","draw"]:
		if winner!="sun":
			scene._restart_army()
			for unused in 24: scene.army.step_simulation(.05)
		scene.army.cores = {"sun":0.0 if winner in ["moon","draw"] else 87.0,"moon":0.0 if winner in ["sun","draw"] else 63.0}
		scene.army.step_simulation(.05);scene._update_practice_hud()
		await frames()
		var battle: Dictionary = scene.army.report()
		var metrics: Dictionary = scene.match_metrics.report()
		var text: String = scene.outcome_summary.detail.text
		check(winner+" summary uses the exact authority winner cores elapsed and counters",metrics.completed and metrics.winner==winner and metrics.cores==battle.cores and is_equal_approx(metrics.elapsed,battle.elapsed) and metrics.gold==battle.gold and metrics.kills==battle.kills and text.contains("%d lane last hits · %d gold earned" % [metrics.kills,metrics.gold]) and text.contains("Final cores · Sun %d / Moon %d" % [battle.cores.sun,battle.cores.moon]),{"metrics":metrics,"summary":text})
		check(winner+" chart contains only detached real recorder samples",scene.outcome_summary.chart.visible and scene.outcome_summary.chart.samples==metrics.core_timeline and metrics.core_timeline[0].time_s==0 and metrics.core_timeline[-1].sun==battle.cores.sun and metrics.core_timeline[-1].moon==battle.cores.moon)
		var frozen := metrics.duplicate(true)
		for unused in 3: scene._update_practice_hud()
		check(winner+" result presentation cannot mutate the frozen round",scene.army.report()==battle and scene.match_metrics.report()==frozen)
	var stable := true
	for path in sources: stable = stable and sources[path]==FileAccess.get_sha256(path)
	check("Integration sources stayed unchanged",stable)
	var passed := checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"checks":checks,"count":checks.size(),"sources":sources,"scope":"Headless actual F4 key dispatch and mounted native scene; accepted siege signals versus cancelled/team/replayed/range/pause guards; real purchase; actual terminal ticks compare summary/chart with recorder. Core fixtures are test setup only. No rendered or OS-window-input acceptance."},"  ")+"\n")
	paused=false;scene.queue_free();current_scene=null;await frames();quit(0 if passed else 1)
