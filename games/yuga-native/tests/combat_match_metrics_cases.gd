extends SceneTree
## Real lane authority/kit/vitals exercise the recorder; no game assets or render.
const Army = preload("res://scripts/lane_army.gd")
const Unit = preload("res://scripts/lane_minion.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
const Metrics = preload("res://scripts/combat_match_metrics.gd")
const Summary = preload("res://scripts/world_outcome_summary.gd")
class RuntimeEvents extends Node:
	signal combat_event(event: Dictionary)
	var vitals: Node
var army
var kit
var vitals
var runtime
var metrics
var summary
var checks: Array = []
var events: Array = []
var output := "/tmp/combat-match-metrics.json"

func _initialize() -> void: call_deferred("run")
func check(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label, "passed":passed, "evidence":evidence})
	print("PASS " if passed else "FAIL ", label)
func advance(seconds: float) -> void:
	var remaining := seconds
	while remaining > 1e-8:
		var delta := minf(.05, remaining)
		army.step_simulation(delta)
		remaining -= delta
func empty_round() -> void:
	army.reset()
	for unit in army.units.duplicate(): army.units.erase(unit); unit.free()
	army._rebuild_buckets()
	army.siege_drill = true
func target_at(point: Vector3, health: float):
	var unit = Unit.new()
	unit.setup(army, army.next_id, "moon", "commander", 1)
	army.next_id += 1
	unit.render_art = false
	unit.position = point
	unit.attack_time = 1000
	unit.attack_cooldown = 1000
	unit.health = health
	unit.defeated.connect(army._on_defeated)
	army.add_child(unit)
	army.units.append(unit)
	return unit
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	army = Army.new(); army.visual_enabled = false; root.add_child(army); army.set_physics_process(false)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	check("Actual lane authority configures", army.configure(manifest, null))
	kit = Kit.new(); root.add_child(kit)
	vitals = Vitals.new(); root.add_child(vitals)
	check("Actual kit and vitals configure", kit.configure(army) and vitals.configure(army))
	runtime = RuntimeEvents.new(); runtime.vitals = vitals; root.add_child(runtime)
	kit.ability_event.connect(func(event): events.append(event.duplicate(true)); runtime.combat_event.emit(event))
	metrics = Metrics.new(); root.add_child(metrics)
	check("Missing sources are rejected without listeners", not metrics.configure(null, runtime))
	check("Recorder configures once", metrics.configure(army, runtime) and not metrics.configure(army, runtime))
	var authority: Dictionary = army.report()
	var state: Dictionary = metrics.report()
	check("Initial report is real and cannot mutate authority", state.elapsed == authority.elapsed and state.cores == authority.cores and state.gold == authority.gold and state.kills == authority.kills and army.report() == authority)
	state.cores.sun = -999; state.core_timeline[0].sun = -999
	check("Report arrays and dictionaries are independent snapshots", metrics.report().cores.sun == 100 and metrics.report().core_timeline[0].sun == 100)
	empty_round()
	var target = target_at(Vector3(0, 0, 5), 10)
	check("Actual primary cast is accepted", kit.request_ability("kodanda", Vector3.ZERO, Vector3(0, 0, 1), Vector3(0, 0, 5)).accepted)
	advance(.5)
	state = metrics.report()
	check("Actual lethal receipt counts applied health rather than attempted overkill", not target.alive and state.hero.casts_started == 1 and state.hero.releases == 1 and state.hero.damage_receipts == 1 and is_equal_approx(state.hero.damage_dealt, 10), {"hero":state.hero})
	check("Lane last hits and earned gold equal army totals", state.kills == army.kills and state.kills == 1 and state.gold == army.gold and state.gold > 0)
	var impact: Dictionary = events.filter(func(event): return event.kind == "impact" and not event.receipts.is_empty())[-1]
	runtime.combat_event.emit(impact)
	check("Replayed event sequence cannot double count a damage receipt", is_equal_approx(metrics.report().hero.damage_dealt, 10) and metrics.report().hero.damage_receipts == 1)
	vitals.receive_damage(25, "metrics-test", vitals.generation, 0)
	vitals.receive_damage(-20, "metrics-test", vitals.generation, 1)
	check("Only accepted effective hero damage is counted", is_equal_approx(metrics.report().hero.damage_taken, 25))
	vitals.receive_damage(1000, "metrics-test", vitals.generation, 2)
	check("Hero defeat counts once and overkill remains bounded", metrics.report().hero.deaths == 1 and is_equal_approx(metrics.report().hero.damage_taken, 300))
	advance(3.1)
	check("Actual respawn is available without resetting the round", vitals.respawn())
	kit.reset("hero-only reset")
	check("Hero lifecycle reset preserves the match totals", metrics.report().hero.deaths == 1 and metrics.report().hero.releases == 1 and metrics.report().kills == 1)
	for winner in ["sun", "moon", "draw"]:
		empty_round()
		advance(1.1)
		army.cores = {"sun":0.0 if winner in ["moon", "draw"] else 90.0, "moon":0.0 if winner in ["sun", "draw"] else 80.0}
		army.step_simulation(.05)
		state = metrics.report()
		check(winner + " final authority tick freezes exact winner/cores/time", state.completed and state.winner == winner and state.cores == army.cores and is_equal_approx(state.elapsed, army.elapsed) and state.core_timeline.size() >= 2 and state.core_timeline[-1].sun == army.cores.sun and state.core_timeline[-1].moon == army.cores.moon)
		var frozen := state.duplicate(true)
		advance(.5)
		runtime.combat_event.emit({"kind":"release", "generation":999, "event_seq":999})
		check(winner + " terminal report ignores later steps/events", metrics.report() == frozen)
		if not is_instance_valid(summary): summary = Summary.new(); root.add_child(summary)
		authority = army.report()
		summary.present(authority, state)
		check(winner + " native summary shows truthful metrics/chart without changing battle", summary.visible and summary.heading.text == Summary.headline(winner) and summary.detail.text.contains("gold earned") and summary.chart.visible and summary.chart.samples == state.core_timeline and army.report() == authority)
		summary.present(authority)
		check(winner + " old summary caller remains supported", summary.detail.text.contains("Final cores") and not summary.chart.visible)
	var previous_round: int = metrics.report().round
	empty_round()
	state = metrics.report()
	check("Army reset clears terminal and hero data once", not state.completed and state.winner.is_empty() and state.gold == 0 and state.kills == 0 and state.hero.releases == 0 and state.hero.damage_dealt == 0 and state.round == previous_round + 1 and state.core_timeline.size() == 1 and state.core_timeline[0].time_s == 0)
	summary.present(army.report(), state)
	check("Fresh round hides the prior result", not summary.visible)
	advance(300)
	state = metrics.report()
	check("Long-round sampling is bounded and retains real first/latest samples", state.core_timeline.size() <= Metrics.MAX_CORE_SAMPLES and state.sample_period_s > 1 and state.core_timeline[0].time_s == 0 and state.core_timeline[-1].time_s > 298, {"samples":state.core_timeline.size(), "period":state.sample_period_s, "last":state.core_timeline[-1].time_s})
	var late = Metrics.new(); root.add_child(late)
	check("Midround attach declares partial event coverage", late.configure(army, runtime) and is_equal_approx(late.report().recorded_from_s, army.elapsed))
	var army_listeners: int = army.simulation_stepped.get_connections().size()
	late.free()
	check("Recorder removal disconnects its subscriptions", army.simulation_stepped.get_connections().size() == army_listeners - 1)
	var passed := checks.all(func(row): return row.passed)
	var sources := {}
	for path in ["res://scripts/combat_match_metrics.gd", "res://scripts/world_outcome_summary.gd", get_script().resource_path]: sources[path] = FileAccess.get_sha256(path)
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify({"passed":passed, "checks":checks, "count":checks.size(), "sources":sources, "scope":"Actual nonvisual lane/kit/vitals, real damage receipts and event replay, core fixtures through real outcome ticks, bounded time-series and native Control data; no actual pixels or input acceptance."}, "  ") + "\n")
	summary.free(); metrics.free(); runtime.free(); vitals.free(); kit.free(); army.free()
	quit(0 if passed else 1)
