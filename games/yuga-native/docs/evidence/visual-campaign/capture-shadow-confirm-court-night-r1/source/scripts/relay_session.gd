extends Node3D
## Offline relay adapter. The fixed-step rules never mutate actors directly.

const ControlRules = preload("res://scripts/relay_control.gd")
const RelayArt = preload("res://scripts/relay_art.gd")
const STEP := .1
const HERO_ID := "hero"

var control = ControlRules.new()
var art: Node3D
var army: Node3D
var player: CharacterBody3D
var _accumulator := 0.0
var _last_receipt := 0
var healing_total := 0.0
var arrows_total := 0
var receipts_applied := 0
var receipts_rejected := 0
var last_event := "Capture a relay with your soldiers"

func configure(army_value: Node3D, player_value: CharacterBody3D) -> void:
	army = army_value
	player = player_value
	process_mode = Node.PROCESS_MODE_PAUSABLE
	if not art:
		art = RelayArt.new()
		art.name = "RelayStations"
		add_child(art)
		art.setup()
		for box in art.collision_boxes(): army.boxes.append(box)
	reset()

func reset() -> void:
	control.reset()
	_accumulator = 0
	_last_receipt = 0
	healing_total = 0
	arrows_total = 0
	receipts_applied = 0
	receipts_rejected = 0
	last_event = "Capture a relay with your soldiers"
	_update_art()

func _enabled() -> bool:
	if not is_instance_valid(army) or not is_instance_valid(player): return false
	if not is_inside_tree() or get_tree().paused or process_mode == Node.PROCESS_MODE_DISABLED: return false
	return army.winner.is_empty() and not army.siege_drill

func advance(delta: float) -> void:
	if not _enabled() or not is_finite(delta) or delta <= 0 or delta > .25: return
	_accumulator += delta
	while _accumulator >= STEP - .000001:
		_accumulator = maxf(0, _accumulator - STEP)
		var result: Dictionary = control.step(STEP, _actors())
		if not result.get("accepted", false): continue
		for event in result.events:
			var label: String = control.sites()[event.site_id].label
			if event.kind == "captured": last_event = "%s secured by %s" % [label, String(event.team).capitalize()]
			elif event.kind == "neutralized": last_event = "%s neutralized" % label
			elif event.kind == "contested": last_event = "%s contested · supplies stopped" % label
		for request in result.support_requests: _apply_support(request)
	_update_art()

func _actors() -> Array:
	var actors: Array = []
	if not is_instance_valid(army) or not is_instance_valid(player): return actors
	actors.append({"id":HERO_ID,"team":"sun","position":player.global_position,"alive":true})
	for unit in army.units:
		if not is_instance_valid(unit): continue
		actors.append({"id":unit.unit_id,"team":unit.team,"position":unit.global_position,"alive":unit.alive and is_finite(unit.health) and unit.health > 0})
	return actors

func _line_clear(origin: Vector3, target: Vector3) -> bool:
	if not origin.is_finite() or not target.is_finite() or not is_inside_tree(): return false
	var ray := PhysicsRayQueryParameters3D.create(origin + Vector3.UP, target + Vector3.UP, 1)
	return get_world_3d().direct_space_state.intersect_ray(ray).is_empty()

func _apply_support(request: Dictionary) -> Dictionary:
	var result := {"accepted":false,"healed":0.0,"arrows":0}
	var rules: Dictionary = control.report()
	var epoch: Variant = request.get("epoch")
	var identity: Variant = request.get("id")
	var site_id: Variant = request.get("site_id")
	if not _enabled() or not epoch is int or not identity is int or not site_id is int:
		receipts_rejected += 1
		return result
	if epoch != rules.epoch or identity <= _last_receipt or identity > rules.last_support_id or site_id < 0 or site_id > 2:
		receipts_rejected += 1
		return result
	_last_receipt = identity
	var site: Dictionary = control.sites()[site_id]
	var team: Variant = request.get("team")
	var ids: Variant = request.get("actor_ids")
	if not ids is Array or ids.size() > 97 or not team is String or team not in ["sun","moon"] or team != site.owner or site.contested or site.pressure_team not in ["neutral",team]:
		receipts_rejected += 1
		return result
	var candidates: Dictionary = {}
	var duplicate: Dictionary = {}
	for unit in army.units:
		if not is_instance_valid(unit): continue
		if candidates.has(unit.unit_id): duplicate[unit.unit_id] = true
		else: candidates[unit.unit_id] = unit
	var seen: Dictionary = {}
	for actor_id in ids:
		if not (actor_id is int or actor_id is String) or seen.has(actor_id): continue
		seen[actor_id] = true
		var is_hero: bool = actor_id is String and actor_id == HERO_ID
		var actor: Node3D = player if is_hero and team == "sun" else candidates.get(actor_id)
		if not is_instance_valid(actor) or duplicate.has(actor_id): continue
		if actor != player and (not actor.alive or actor.team != team or not is_finite(actor.health) or not is_finite(actor.max_health) or actor.health <= 0 or actor.max_health <= 0): continue
		var point := actor.global_position
		if not point.is_finite() or absf(point.y-site.position.y) > 2.5 or Vector2(point.x-site.position.x,point.z-site.position.z).length() > 8: continue
		if not _line_clear(site.position,point): continue
		if actor == player:
			var before: int = player.ammo
			player.ammo = clampi(player.ammo + 3, 0, 12)
			result.arrows += maxi(0,player.ammo-before)
			player.changed.emit()
		else:
			var before: float = actor.health
			actor.health = minf(actor.max_health,actor.health+6)
			actor._update_health_bar()
			result.healed += maxf(0,actor.health-before)
	result.accepted = true
	healing_total += result.healed
	arrows_total += result.arrows
	receipts_applied += 1
	if result.arrows > 0: last_event = "%s supplied +%d arrows" % [site.label,result.arrows]
	return result

func _update_art() -> void:
	if not is_instance_valid(art): return
	var values := control.sites()
	for site in values: site.progress = absf(site.progress) / 8.0
	art.set_states(values)

func sites() -> Array:
	return control.sites()

func report() -> Dictionary:
	return {"rules":control.report(),"art":art.report() if is_instance_valid(art) else {},"healing_total":healing_total,"arrows_total":arrows_total,"receipts_applied":receipts_applied,"receipts_rejected":receipts_rejected,"last_receipt":_last_receipt,"last_event":last_event,"scope":"Offline relay capture and supplies; no hero health or network authority."}
