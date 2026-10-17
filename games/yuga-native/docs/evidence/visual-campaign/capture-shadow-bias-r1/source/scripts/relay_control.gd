extends RefCounted
## Original offline relay rules. No nodes, resources, timers, health or rewards.
## The scene owns fixed-step scheduling and revalidates supply receipts before use.

const CAPTURE_REQUIRED := 8.0
const CAPTURE_RADIUS := 5.0
const SUPPLY_RADIUS := 8.0
const HEIGHT_TOLERANCE := 2.5
const SUPPLY_PERIOD := 5.0
const EMPTY_DECAY := 0.5
const MAX_DELTA := 0.25
const MAX_ACTORS := 97
const MAX_CONTRIBUTORS := 2
const EPSILON := 0.000001
const LABELS := ["Reed Relay", "Lotus Relay", "Sky Relay"]
const SITE_X := [-40.0, 0.0, 40.0]

var _sites: Array = []
var _epoch := 0
var _support_id := 0
var _elapsed := 0.0
var _steps := 0
var _captures := 0
var _neutralizations := 0
var _contests := 0
var _last_actor_counts: Dictionary = {}

func _init() -> void:
	reset()

func reset() -> void:
	_epoch += 1
	_support_id = 0
	_elapsed = 0.0
	_steps = 0
	_captures = 0
	_neutralizations = 0
	_contests = 0
	_last_actor_counts = {"input":0,"unique_alive":0,"invalid_rows":0,"duplicate_rows":0,"conflicting_ids":0}
	_sites.clear()
	for index in range(3):
		_sites.append({"id":index,"label":LABELS[index],"position":Vector3(SITE_X[index],0,0),
			"radius":CAPTURE_RADIUS,"owner":"neutral","progress":0.0,"capture_team":"neutral",
			"pressure_team":"neutral","contested":false,"supply_clock":0.0,
			"contributors":{"sun":0,"moon":0}})

func sites() -> Array:
	return _sites.duplicate(true)

func report() -> Dictionary:
	return {"schema":1,"epoch":_epoch,"last_support_id":_support_id,"elapsed":_elapsed,"steps":_steps,
		"captures":_captures,"neutralizations":_neutralizations,"contests":_contests,
		"actors":_last_actor_counts.duplicate(true),"sites":sites(),
		"limits":{"sites":3,"actors":MAX_ACTORS,"contributors_per_team":MAX_CONTRIBUTORS,
			"events_per_step":3,"support_requests_per_step":3,"max_delta":MAX_DELTA}}

func step(delta: float, actors: Array) -> Dictionary:
	# Validation is transactional: even diagnostics and receipt counters stay intact.
	if not is_finite(delta) or delta < 0.0 or delta > MAX_DELTA:
		return _result(false,"delta must be finite and between 0 and 0.25")
	if actors.size() > MAX_ACTORS:
		return _result(false,"actor array exceeds 97 entries")
	if delta == 0.0:
		return _result(true,"")
	var intake: Dictionary = _sanitize(actors)
	var valid: Array = intake.actors
	_last_actor_counts = intake.counts
	var result := _result(true,"")
	for site in _sites:
		_step_site(site,delta,valid,result.events,result.support_requests)
	_elapsed += delta
	_steps += 1
	return result

func _result(accepted: bool, error: String) -> Dictionary:
	return {"accepted":accepted,"error":error,"events":[],"support_requests":[]}

func _sanitize(actors: Array) -> Dictionary:
	var by_id: Dictionary = {}
	var conflicts: Dictionary = {}
	var counts := {"input":actors.size(),"unique_alive":0,"invalid_rows":0,"duplicate_rows":0,"conflicting_ids":0}
	for row in actors:
		if not _valid_actor(row):
			counts.invalid_rows += 1
			continue
		var actor: Dictionary = {"id":row.id,"team":row.team,"position":row.position,"alive":row.alive}
		if by_id.has(actor.id):
			counts.duplicate_rows += 1
			if by_id[actor.id] != actor:
				conflicts[actor.id] = true
		else:
			by_id[actor.id] = actor
	var accepted: Array = []
	for id in by_id:
		if not conflicts.has(id) and by_id[id].alive:
			accepted.append(by_id[id])
	# Stable order also makes supply actor IDs independent of input array order.
	accepted.sort_custom(func(a: Dictionary,b: Dictionary) -> bool: return _id_before(a.id,b.id))
	counts.unique_alive = accepted.size()
	counts.conflicting_ids = conflicts.size()
	return {"actors":accepted,"counts":counts}

func _valid_actor(value: Variant) -> bool:
	if not value is Dictionary:
		return false
	for field in ["id","team","position","alive"]:
		if not value.has(field):
			return false
	var id: Variant = value.id
	if not id is int and not id is String:
		return false
	if id is String and (id.is_empty() or id.length() > 128):
		return false
	return value.team is String and value.team in ["sun","moon"] and value.position is Vector3 \
		and value.position.is_finite() and value.alive is bool

func _id_before(a: Variant, b: Variant) -> bool:
	if typeof(a) != typeof(b):
		return typeof(a) < typeof(b)
	return a < b

func _within(position: Vector3, site_position: Vector3, radius: float) -> bool:
	var offset := position-site_position
	return absf(offset.y) <= HEIGHT_TOLERANCE and Vector2(offset.x,offset.z).length_squared() <= radius*radius

func _step_site(site: Dictionary, delta: float, actors: Array, events: Array, support: Array) -> void:
	var sun := 0
	var moon := 0
	var eligible: Dictionary = {"sun":[],"moon":[]}
	for actor in actors:
		if _within(actor.position,site.position,SUPPLY_RADIUS):
			eligible[actor.team].append(actor.id)
		if _within(actor.position,site.position,CAPTURE_RADIUS):
			if actor.team == "sun": sun = mini(MAX_CONTRIBUTORS,sun+1)
			else: moon = mini(MAX_CONTRIBUTORS,moon+1)
	var contested: bool = sun > 0 and moon > 0
	if contested and not site.contested:
		events.append({"kind":"contested","site_id":site.id,"team":"neutral"})
		_contests += 1
	site.contested = contested
	site.contributors = {"sun":sun,"moon":moon}
	site.pressure_team = "neutral" if contested or (sun == 0 and moon == 0) else ("sun" if sun > 0 else "moon")
	if contested:
		site.supply_clock = 0.0
		return
	var prior_owner: String = site.owner
	if sun == 0 and moon == 0:
		var stable := CAPTURE_REQUIRED if prior_owner == "sun" else (-CAPTURE_REQUIRED if prior_owner == "moon" else 0.0)
		site.progress = move_toward(site.progress,stable,EMPTY_DECAY*delta)
	else:
		var rate := float(sun-moon)
		site.progress = clampf(site.progress+rate*delta,-CAPTURE_REQUIRED,CAPTURE_REQUIRED)
		if (prior_owner == "sun" and site.progress <= EPSILON) or (prior_owner == "moon" and site.progress >= -EPSILON):
			site.owner = "neutral"
			if absf(site.progress) <= EPSILON: site.progress = 0.0
			events.append({"kind":"neutralized","site_id":site.id,"team":"sun" if rate>0 else "moon"})
			_neutralizations += 1
		if site.owner == "neutral" and absf(site.progress) >= CAPTURE_REQUIRED-EPSILON:
			site.owner = "sun" if site.progress > 0 else "moon"
			site.progress = CAPTURE_REQUIRED if site.owner == "sun" else -CAPTURE_REQUIRED
			events.append({"kind":"captured","site_id":site.id,"team":site.owner})
			_captures += 1
	if absf(site.progress) <= EPSILON: site.progress = 0.0
	site.capture_team = "sun" if site.progress > 0 else ("moon" if site.progress < 0 else "neutral")
	# No supply is credited for the tick that changes ownership. Opposing pressure
	# interrupts the cadence even while the prior owner is still being neutralized.
	if site.owner == "neutral" or site.owner != prior_owner or (site.owner == "sun" and moon>0) or (site.owner == "moon" and sun>0):
		site.supply_clock = 0.0
		return
	site.supply_clock += delta
	if site.supply_clock >= SUPPLY_PERIOD-EPSILON:
		site.supply_clock = maxf(0.0,site.supply_clock-SUPPLY_PERIOD)
		if not eligible[site.owner].is_empty():
			_support_id += 1
			support.append({"epoch":_epoch,"id":_support_id,"site_id":site.id,"team":site.owner,
				"actor_ids":eligible[site.owner].duplicate()})
