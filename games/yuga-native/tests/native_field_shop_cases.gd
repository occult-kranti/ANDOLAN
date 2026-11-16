extends SceneTree
## Real army rewards/vitals/summons plus an ammo adapter; no UI or online claim.
const Shop = preload("res://scripts/native_field_shop.gd")
const Army = preload("res://scripts/lane_army.gd")
const Unit = preload("res://scripts/lane_minion.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")

class AmmoPlayer extends Node3D:
	signal changed
	var ammo := 12
	var active := false

class RuntimeAdapter extends Node:
	var configured := true
	var suspended := false
	var player: Node3D
	var vitals: Node

var checks: Array[Dictionary] = []
var report_path := ""
var army
var vitals
var player
var runtime
var shop
var spawn := Vector3(0, 0, -112)
var nonce := 0
var on_heal := ""
var on_publish := false
var nested_receipt: Dictionary = {}

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): report_path = argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name": label, "passed": passed, "details": details})
	print("PASS " if passed else "FAIL ", label)

func buy(id: String) -> Dictionary:
	nonce += 1
	return shop.purchase(id, shop.epoch, nonce)

func fresh() -> void:
	on_heal = ""; on_publish = false; nested_receipt.clear()
	paused = false
	runtime.suspended = false
	vitals.set_suspended(false)
	army.winner = ""
	army.reset()
	player.global_position = spawn
	player.ammo = 12

func advance(seconds: float) -> void:
	var remaining := seconds
	while remaining > .000001:
		var dt := minf(.05, remaining)
		army.step_simulation(dt)
		remaining -= dt

func receiver_changed() -> void:
	var action := on_heal
	if action.is_empty(): return
	on_heal = ""
	if action == "round_reset": army.reset()
	elif action == "hero_reset": vitals.reset()
	elif action == "nested": nested_receipt = shop.purchase("arrows", shop.epoch, nonce + 1)

func publication_changed() -> void:
	if not on_publish: return
	on_publish = false
	nested_receipt = shop.purchase("ward", shop.epoch, nonce + 1)

func add_enemy():
	var unit = Unit.new()
	unit.setup(army, army.next_id, "moon", "spearman", 1)
	army.next_id += 1
	unit.render_art = false
	unit.position = spawn + Vector3(0, 0, 4)
	unit.defeated.connect(army._on_defeated)
	army.add_child(unit)
	army.units.append(unit)
	return unit

func run() -> void:
	if not report_path.is_absolute_path() or FileAccess.file_exists(report_path):
		push_error("Use a fresh absolute --report path"); quit(1); return
	DirAccess.make_dir_recursive_absolute(report_path.get_base_dir())
	var paths := ["res://scripts/native_field_shop.gd", Shop.CATALOG_PATH, "res://scripts/lane_army.gd", "res://scripts/lane_minion.gd", "res://scripts/rama_vitals.gd", get_script().resource_path]
	var hashes := {}
	for path in paths: hashes[path] = FileAccess.get_sha256(path)
	player = AmmoPlayer.new(); root.add_child(player); player.position = spawn
	army = Army.new(); army.visual_enabled = false; root.add_child(army); army.set_physics_process(false)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	check("actual three-lane army configures", army.configure(manifest, player))
	vitals = Vitals.new(); root.add_child(vitals)
	check("actual hero vitals receiver configures", vitals.configure(army))
	runtime = RuntimeAdapter.new(); runtime.player = player; runtime.vitals = vitals; root.add_child(runtime)
	shop = Shop.new(); root.add_child(shop)
	check("field shop configures actual army and vitals", shop.configure(army, runtime, player, spawn))
	shop.changed.connect(publication_changed)
	vitals.changed.connect(receiver_changed)
	check("original allowance is distinct from earned army gold", shop.report().wallet == 120 and shop.report().earned == 0 and army.gold == 0 and shop.report().starting_allowance == 120)
	var catalog: Array = shop.report().catalog
	check("four original catalog rows expose live UI fields", catalog.size() == 4 and catalog.all(func(row): return row.has_all(["id", "title", "description", "cost", "icon", "available", "disabled_reason", "benefit"])))
	check("live shop does not require player input activity", not player.active and shop.report().eligible)
	check("reconfigure cannot mint another allowance", not shop.configure(army, runtime, player, spawn) and shop.report().wallet == 120)
	var empty_shop := Shop.new(); root.add_child(empty_shop)
	var empty_result: Dictionary = empty_shop.purchase("heal", 0, 1)
	check("unconfigured command is rejected without property errors", not empty_result.accepted and empty_result.charged == 0)
	empty_shop.free()
	var full := buy("heal")
	var full_nonce := nonce
	check("full health rejects without charge", not full.accepted and full.charged == 0 and shop.report().wallet == 120)
	vitals.receive_damage(70, "fixture-heal")
	var heal := buy("heal")
	var heal_nonce := nonce
	check("real heal is capped and only then charged", heal.accepted and heal.charged == 35 and heal.effect.health_restored == 70 and vitals.health == 300 and shop.report().wallet == 85 and army.gold == 0)
	var duplicate: Dictionary = shop.purchase("heal", shop.epoch, heal_nonce)
	check("duplicate receipt cannot heal or spend twice", duplicate.accepted and duplicate.get("duplicate") == true and shop.report().wallet == 85 and shop.report().accepted_purchases == 1)
	duplicate.effect.health_restored = 999
	check("returned receipt mutation cannot poison deduplication", shop.purchase("heal", shop.epoch, heal_nonce).effect.health_restored == 70)
	check("same nonce cannot buy another item", not shop.purchase("ward", shop.epoch, heal_nonce).accepted and shop.report().wallet == 85 and vitals.shield == 0)
	vitals.receive_damage(5, "fixture-cached-rejection")
	var cached_reject: Dictionary = shop.purchase("heal", shop.epoch, full_nonce)
	check("retry of an old rejected command cannot become a new purchase", not cached_reject.accepted and cached_reject.get("duplicate") == true and vitals.health == 295 and shop.report().wallet == 85)
	fresh()
	player.ammo = 9
	var arrows := buy("arrows")
	check("arrow service uses real capped ammo state with input inactive", arrows.accepted and arrows.effect.arrows_added == 3 and player.ammo == 12 and shop.report().wallet == 105 and not player.active)
	check("full arrows are never charged", not buy("arrows").accepted and shop.report().wallet == 105)
	fresh()
	var ward := buy("ward")
	check("ward uses actual shield and army-clock lifetime", ward.accepted and vitals.shield == 55 and absf(vitals.shield_until - 8) < .00001 and shop.report().wallet == 80)
	check("same-time no-benefit ward is not charged", not buy("ward").accepted and shop.report().wallet == 80)
	advance(.5)
	check("ward can buy a real expiry extension", buy("ward").accepted and vitals.shield_until > 8.49 and shop.report().wallet == 40)
	check("insufficient funds cannot summon units", not buy("escort").accepted and shop.report().wallet == 40)
	advance(8.1)
	check("purchased ward expires using the existing army clock", vitals.shield == 0 and vitals.shield_until == 0)
	fresh()
	vitals.apply_shield(90, 10)
	check("stronger longer existing shield is preserved without charge", not buy("ward").accepted and vitals.shield == 90 and shop.report().wallet == 120)
	fresh()
	var count_before: int = army.units.size()
	var escort := buy("escort")
	var escort_nonce := nonce
	check("escort creates exactly two existing temporary spearmen", escort.accepted and escort.effect.units_spawned == 2 and army.units.size() == count_before + 2 and shop.report().wallet == 30, {"receipt": escort})
	var created: Array = army.units.filter(func(unit): return unit.practice_summon)
	check("escort retains existing bounded summon stats", created.size() == 2 and created.all(func(unit): return unit.team == "sun" and unit.role == "spearman" and unit.max_health == 105 and unit.summon_attack_damage == 18 and absf(unit.summon_expires_at - 9) < .00001))
	shop.purchase("escort", shop.epoch, escort_nonce)
	check("duplicate escort cannot create another pair", army.units.size() == count_before + 2 and shop.report().wallet == 30)
	advance(9.1)
	check("escort expiry grants no new gold or permanent troop", army.units.filter(func(unit): return unit.alive and unit.practice_summon).is_empty() and army.gold == 0 and shop.report().earned == 0)
	fresh()
	var original_boxes: Array = army.boxes.duplicate(true)
	army.boxes.append({"position": spawn + Vector3(0, 1, 0), "size": Vector3(20, 4, 20)})
	check("blocked summon placements never consume gold", not buy("escort").accepted and shop.report().wallet == 120 and army.units.filter(func(unit): return unit.practice_summon).is_empty())
	army.boxes = original_boxes
	fresh()
	var enemy = add_enemy()
	check("actual player last-hit receiver produces the earned reward", enemy.take_hit(100) and army.gold == 18 and shop.report().earned == 18 and shop.report().wallet == 138)
	enemy.take_hit(100); army.gold_changed.emit(18); army.gold_changed.emit(17)
	check("duplicate/decreasing reward totals cannot mint gold", army.gold == 18 and shop.report().earned == 18 and shop.report().wallet == 138)
	var old_epoch: int = shop.epoch
	army.reset()
	check("army reset clears spending/rewards and restores one allowance", shop.epoch > old_epoch and shop.report().wallet == 120 and shop.report().earned == 0 and shop.report().spent == 0 and army.gold == 0)
	check("stale previous-round ticket is rejected", not shop.purchase("ward", old_epoch, nonce + 1).accepted and shop.report().wallet == 120)
	player.position = spawn + Vector3(15, 0, 0)
	check("outside base radius cannot buy", not buy("ward").accepted and not shop.report().near_shop and shop.report().wallet == 120)
	player.position = spawn + Vector3(0, 3, 0)
	check("vertical route over base cannot use ground shop", not buy("ward").accepted and not shop.report().near_shop)
	player.position = spawn
	paused = true
	check("tree pause forbids spending", not buy("ward").accepted and shop.report().wallet == 120)
	paused = false
	army.winner = "sun"
	check("terminal outcome forbids spending", not buy("ward").accepted and shop.report().wallet == 120)
	army.winner = ""
	vitals.receive_damage(500, "fixture-defeat")
	check("defeated hero cannot buy", not buy("ward").accepted and shop.report().wallet == 120)
	fresh()
	runtime.suspended = true
	check("suspended runtime cannot buy", not buy("ward").accepted and shop.report().wallet == 120)
	runtime.suspended = false
	vitals.set_suspended(true)
	check("suspended receiver cannot buy", not buy("ward").accepted and shop.report().wallet == 120)
	vitals.set_suspended(false)
	check("invalid epoch/nonce types and unknown items cannot spend", not shop.purchase("ward", float(shop.epoch), nonce + 1).accepted and not shop.purchase("ward", shop.epoch, NAN).accepted and not shop.purchase(9, shop.epoch, nonce + 1).accepted and not buy("unknown").accepted and shop.report().wallet == 120)
	fresh()
	player.ammo = 4
	vitals.receive_damage(100, "fixture-reentrant")
	on_heal = "nested"
	var outer := buy("heal")
	check("receiver callback cannot buy during a reservation", outer.accepted and not nested_receipt.accepted and player.ammo == 4 and shop.report().wallet == 85)
	check("reentrant rejection does not steal the next valid nonce", buy("arrows").accepted and player.ammo == 10 and shop.report().wallet == 70)
	fresh()
	vitals.receive_damage(100, "fixture-publish")
	on_publish = true
	outer = buy("heal")
	check("published change callbacks cannot recursively buy", outer.accepted and not nested_receipt.accepted and vitals.shield == 0 and shop.report().wallet == 85)
	fresh()
	vitals.receive_damage(100, "fixture-round-reset")
	on_heal = "round_reset"
	old_epoch = shop.epoch
	outer = buy("heal")
	check("receiver reset cannot charge the successor round", not outer.accepted and outer.charged == 0 and shop.epoch > old_epoch and shop.report().wallet == 120 and shop.report().spent == 0 and vitals.health == 300)
	fresh()
	vitals.receive_damage(100, "fixture-hero-reset")
	on_heal = "hero_reset"
	outer = buy("heal")
	check("receiver generation change cannot charge restored hero", not outer.accepted and outer.charged == 0 and shop.report().wallet == 120 and vitals.health == 300)
	fresh()
	var first_nonce := nonce + 1
	for unused in 70: buy("heal")
	var evicted: Dictionary = shop.purchase("heal", shop.epoch, first_nonce)
	check("bounded receipt cache still rejects evicted old nonces", not evicted.accepted and not evicted.get("duplicate") and evicted.reason.contains("stale") and shop.report().wallet == 120 and shop._receipts.size() == 64)
	var mutable_report: Dictionary = shop.report()
	mutable_report.catalog[0].cost = 0
	check("report mutation cannot edit service prices", shop.report().catalog[0].cost == 35)
	var invalid_path := report_path.get_base_dir().path_join("invalid-shop-catalog.json")
	var invalid_catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Shop.CATALOG_PATH))
	invalid_catalog.items[0].cost = -1
	FileAccess.open(invalid_path, FileAccess.WRITE).store_string(JSON.stringify(invalid_catalog))
	var invalid_shop := Shop.new(); root.add_child(invalid_shop)
	check("malformed declarative cost rejected before configuring", not invalid_shop.configure(army, runtime, player, spawn, invalid_path) and not invalid_shop.configured)
	invalid_shop.free()
	root.remove_child(shop)
	check("detached owner rejects commands and disconnects reward listener", not shop.configured and not shop.purchase("ward", shop.epoch, nonce + 1).accepted and not army.gold_changed.is_connected(shop._on_gold_changed))
	check("detached owner cannot be reconfigured to refresh allowance", not shop.configure(army, runtime, player, spawn))
	shop.free()
	var after := {}
	for path in paths: after[path] = FileAccess.get_sha256(path)
	check("selected source bytes remain unchanged during tests", hashes == after)
	var passed := checks.all(func(row): return row.passed)
	var result := {"passed": passed, "count": checks.size(), "checks": checks, "sources_before": hashes, "sources_after": after, "scope": "Actual lane reward/vitals/shield/summon receivers and original spending owner; ammo uses a minimal player adapter. No actual-window UI, human balance, online authority or full-match acceptance."}
	FileAccess.open(report_path, FileAccess.WRITE).store_string(JSON.stringify(result, "  ") + "\n")
	runtime.free(); vitals.free(); army.free(); player.free()
	await process_frame
	quit(0 if passed else 1)
