extends SceneTree
## Real kit/practice/vitals receipts with a small presentation-only player adapter.
## This is not a rendered, ordinary-input, motion, audio or network acceptance.
const Army = preload("res://scripts/rama_practice_army.gd")
const Target = preload("res://scripts/target.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
const HUD = preload("res://scripts/rama_hero_hud.gd")
const GuideScript = preload("res://scripts/rama_hero_panel.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
class PlayerAdapter extends Node3D:
	const MAGAZINE := 12
	var active := true
	var ammo := 12
	var reload_remaining := 0.0
class RuntimeAdapter extends Node3D:
	signal combat_event(event: Dictionary)
	var configured := true
	var suspended := false
	var player: Node3D
	var army: Node3D
	var kit: Node3D
	var vitals: Node
	var action_buffer: Node
	var notice := "Rama is ready"
	func _input_eligibility() -> Dictionary: return {"eligible":true}
var checks: Array = []
var output := ""
var runtime: RuntimeAdapter
var hud: Control
var targets: Array = []
var events: Array[Dictionary] = []
var panel: Control
var practice_sample: Dictionary = {}
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)
func frames(count := 6) -> void:
	for unused in count: await process_frame
func advance(seconds: float) -> void:
	for unused in ceili(seconds/.05):
		runtime.army.step_simulation(.05)
		hud._process(.05)
func cast(id: String, forward := Vector3(0,0,1)) -> Dictionary:
	return runtime.kit.request_ability(id, Vector3.ZERO, forward, Vector3.ZERO)
func reset() -> void:
	runtime.player.active = true
	runtime.suspended = false
	paused = false
	runtime.army.reset("completion UI fixture")
	hud._refresh()
func run() -> void:
	Bindings.install("user://rama-completion-ui-fixture.cfg")
	root.size = Vector2i(1280,720)
	root.content_scale_size = root.size
	runtime = RuntimeAdapter.new()
	root.add_child(runtime)
	runtime.player = PlayerAdapter.new(); runtime.add_child(runtime.player)
	for z in [5,8,11]:
		var target := Target.new()
		runtime.add_child(target)
		target.position = Vector3(0,0,z)
		targets.append(target)
	runtime.army = Army.new(); runtime.add_child(runtime.army); runtime.army.set_physics_process(false)
	check("Actual practice targets configure",runtime.army.configure(targets))
	runtime.kit = Kit.new(); runtime.add_child(runtime.kit)
	runtime.vitals = Vitals.new(); runtime.add_child(runtime.vitals)
	check("Actual fixed-clock kit and vitals configure",runtime.kit.configure(runtime.army) and runtime.vitals.configure(runtime.army))
	runtime.kit.set_hero_receiver(runtime.vitals,func():return runtime.player.position)
	runtime.kit.ability_event.connect(func(event: Dictionary): events.append(event.duplicate(true));runtime.combat_event.emit(event))
	hud = HUD.new(); root.add_child(hud); hud.configure(runtime)
	await frames()
	var feedback: Control = hud.combat_feedback
	check("Hero identity and genuine readiness share unchanged outer bounds",hud.identity.visible and hud.get_global_rect().size == Vector2(820,112) and hud.slots[1].text.contains("READY") and not feedback.visible, hud.report())
	var accepted := cast("kodanda")
	check("Accepted draw alone never invents a confirmed hit",accepted.accepted and not feedback.visible)
	advance(.3)
	check("Real arrow impact gives exact effective damage and target",feedback.visible and feedback.report().damage == 28 and feedback.report().targets == 1 and feedback.report().defeats == 0 and runtime.army.units[0].health == 62,feedback.report())
	var impact: Dictionary = events.filter(func(event):return event.kind == "impact" and not event.receipts.is_empty())[0]
	var prior: Dictionary = feedback.report()
	feedback.consume_event(impact)
	check("Replayed impact cannot duplicate damage or defeat",feedback.report().damage == prior.damage and feedback.report().targets == prior.targets and feedback.report().confirmed_events == prior.confirmed_events)
	var before_kit: Dictionary = runtime.kit.report()
	var before_army: Dictionary = runtime.army.report()
	for unused in 90: hud._process(.1)
	check("UI time cannot deal damage, expire feedback or advance cooldown",runtime.kit.report() == before_kit and runtime.army.report() == before_army and feedback.visible)
	advance(.3)
	accepted = cast("piercing_dawn")
	advance(1.1)
	check("Piercing damage aggregates actual contacts and confirmed down state",accepted.accepted and feedback.report().damage == 202 and feedback.report().targets == 3 and feedback.report().defeats == 1 and feedback.report().hit_text.contains("TARGET DOWN"),feedback.report())
	check("Feedback is a noninteractive bounded viewport overlay",root.get_visible_rect().encloses(feedback.get_global_rect()) and not feedback.get_global_rect().intersects(hud.get_global_rect()) and feedback.mouse_filter == Control.MOUSE_FILTER_IGNORE and feedback.focus_mode == Control.FOCUS_NONE,feedback.report())
	advance(1.2)
	check("Only real simulation time retires a hit badge",not feedback.visible)
	reset()
	check("Reset clears old receipts and aggregates",not feedback.visible and feedback.report().cached_receipts == 0 and feedback.report().damage == 0)
	accepted = cast("kodanda",Vector3.RIGHT)
	advance(1.1)
	check("An actual range miss never becomes a hit marker",accepted.accepted and not feedback.visible)
	reset()
	runtime.army.boxes.append({"position":Vector3(0,2,3),"size":Vector3(10,4,.1)})
	accepted = cast("piercing_dawn")
	advance(1.1)
	check("An actual wall impact never becomes a hit marker",accepted.accepted and not feedback.visible and runtime.army.units[0].health == 90)
	runtime.army.boxes.pop_back()
	reset()
	runtime.army.units[0].apply_shield(100.0,8.0)
	accepted = cast("kodanda")
	advance(.35)
	check("Shield-only contact reports absorption without a health hit",accepted.accepted and feedback.report().damage == 28 and feedback.report().shield_only and runtime.army.units[0].health == 90 and runtime.army.units[0].shield == 72,feedback.report())
	runtime.vitals.apply_shield(55.0,8.0)
	hud._refresh()
	check("Shield stripe reads actual capacity and preserves exact life text",is_equal_approx(hud.health_detail.shield_ratio,.55) and hud.life_text.text == "300 / 300 +55" and hud.life.value == 300)
	var damage: Dictionary = runtime.vitals.receive_damage(20,"completion shield",runtime.vitals.generation,1)
	hud._refresh()
	check("Real incoming shield loss stays distinct from health loss",damage.accepted and feedback.report().hurt_text == "−20 SHIELD" and hud.life_text.text == "300 / 300 +35",feedback.report())
	var serial: int = feedback._damage_serial
	feedback.consume_damage(damage)
	check("Repeated incoming receipt does not change receiver serial",feedback._damage_serial == serial)
	damage = runtime.vitals.receive_damage(45,"completion health",runtime.vitals.generation,1)
	hud._refresh()
	check("Mixed incoming damage reports both actual losses",damage.accepted and feedback.report().hurt_text == "−10 HEALTH  ·  −35 SHIELD" and hud.life_text.text == "290 / 300",feedback.report())
	for dimensions in [Vector2i(1280,720),Vector2i(960,540),Vector2i(640,360),Vector2i(480,270)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await frames()
		hud._refresh()
		var report: Dictionary = feedback.report()
		check("Feedback respects bottom HUD space at "+str(dimensions),not feedback.visible or (root.get_visible_rect().encloses(feedback.get_global_rect()) and not feedback.get_global_rect().intersects(hud.get_global_rect())) ,report)
	root.size = Vector2i(1280,720);root.content_scale_size = root.size
	await frames()
	hud._refresh()
	paused = true
	hud._process(.1)
	check("Pause clears transient hit/hurt and retains authoritative life",not feedback.visible and runtime.vitals.health == 290 and hud.note.text == "Practice paused")
	paused = false
	hud._process(.1)
	check("Resume never resurrects a stale confirmation",not feedback.visible)
	reset()
	cast("kodanda");advance(.35)
	runtime.player.active = false;hud._process(.1)
	check("Inactive input/shop state clears feedback",not feedback.visible)
	runtime.player.active = true
	runtime.vitals.receive_damage(1000,"completion defeat",runtime.vitals.generation,1);hud._process(.1)
	check("Defeat delegates to the existing return timer and hides aim feedback",not feedback.visible and hud.note.text == "RETURNING IN 3.0s")
	reset()
	cast("kodanda");advance(.35)
	root.remove_child(hud)
	await frames()
	check("Detached HUD disconnects feedback consumers",not runtime.combat_event.is_connected(feedback.consume_event) and not runtime.vitals.damaged.is_connected(feedback.consume_damage))
	root.add_child(hud);await frames();hud._refresh()
	check("Reattached HUD reconnects once without stale hit",runtime.combat_event.is_connected(feedback.consume_event) and not feedback.visible)
	panel = GuideScript.new(); root.add_child(panel)
	practice_sample = {"configured":true,"scope":"courtyard","casts_started":4,"hits":3,"damage_dealt":140.0,"healing_applied":10.0,"shield_granted":55.0,"step_distance_m":4.5,"by_ability":[{"ability_id":"kodanda","casts_started":2,"hits":1,"damage_dealt":28.0}]}
	panel.configure_practice_report(func():return practice_sample.duplicate(true))
	panel.open("courtyard")
	check("Guide displays original real-rule hero profile and supplied attempt",panel.profile_label.text.contains("300 health") and panel.profile_label.text.contains("40 m bow") and panel.practice_label.visible and panel.practice_label.text.contains("4 casts · 3 contacts") and panel.practice_label.text.contains("Kodanda · 2 casts"))
	var authority: Dictionary = runtime.kit.report()
	panel.open("confluence")
	check("Training record never appears as a lane match statistic",not panel.practice_label.visible and not panel.practice_heading.visible and authority == runtime.kit.report())
	panel.open("courtyard")
	practice_sample.damage_dealt = NAN;panel._refresh_profile()
	check("Malformed practice readout hides without invented totals",not panel.practice_label.visible)
	panel.configure_practice_report(Callable());panel._refresh_profile()
	check("Missing provider keeps the hero guide usable",not panel.practice_label.visible and panel.ability_buttons.size() == 5)
	panel.close()
	var passed: bool = checks.all(func(row):return row.passed)
	var report := {"passed":passed,"count":checks.size(),"checks":checks,"sources":{},"scope":"Actual configured kit, practice target and vitals receipts with a minimal presentation player adapter; authority clocks advanced explicitly. Guide provider values are UI fixtures. No rendered, physical-input, motion/art/audio/hardware/network claim."}
	for path in ["res://scripts/rama_hero_hud.gd","res://scripts/rama_hero_panel.gd","res://scripts/rama_combat_feedback.gd",get_script().resource_path]:report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		DirAccess.make_dir_recursive_absolute(output.get_base_dir())
		FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	panel.free();hud.free();runtime.free()
	await frames()
	quit(0 if passed else 1)
