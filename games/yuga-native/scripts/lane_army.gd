extends Node3D
## Original offline three-lane simulation. Fixed20Hz, 5Hz target decisions.
## Hard72 live/24 corpse/96 total unit nodes; no emitted audio or transient nodes.

signal changed
signal gold_changed(total: int)
signal outcome(winning_team: String)
signal siege_event(event: Dictionary)

const Unit = preload("res://scripts/lane_minion.gd")
const STEP := .05
const CAP := 72
const CORPSE_CAP := 24
const TOTAL_CAP := 96
const SIEGE_ATTACK_CAP := 32
const MAX_UNIT_RADIUS := .88
const WAVE_INTERVAL := 30.0
const FORMATION := ["spearman","spearman","bow_guard","bow_guard","commander"]
const OFFSETS := [-1.20,1.20,-1.20,1.20,0.0]
const START_DISTANCE := [8.0,8.0,5.4,5.4,2.8]

var player: Node3D
var configured := false
var visual_enabled := true
var units: Array = []
var lanes: Array = []
var boxes: Array = []
var actor_bounds := [-68.0,68.0,-128.0,128.0]
var elapsed := 0.0
var waves := 0
var wave_events := 0
var gold := 0
var kills := 0
var cores := {"sun":100.0,"moon":100.0}
var winner := ""
var max_alive_seen := 0
var max_nodes_seen := 0
var max_corpses_seen := 0
var max_attacks_seen := 0
var route_blocked_moves := 0
var separation_waits := 0
var invalid_steps := 0
var invalid_pulses := 0
var kills_by_lane := [0,0,0]
var core_arrivals := [0,0,0]
var rejected_waves := 0
var next_id := 1
var _accumulator := 0.0
var _decision_clock := 0.0
var _next_wave := WAVE_INTERVAL
var _attacks: Array = []
var _grid: Dictionary = {}
var _lane_buckets: Dictionary = {}
var _invalid_damage_retired := 0
var siege_drill := false
var siege_windups := 0
var siege_impacts := 0
var siege_cancelled := 0
var siege_hits := 0
var siege_spawned_pairs := 0
var siege_rejected_pairs := 0
var _next_siege_id := 1

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE

func _number(value) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value))

func _vector(value) -> bool:
	return value is Array and value.size() == 3 and _number(value[0]) and _number(value[1]) and _number(value[2])

func configure(manifest: Dictionary, player_value: Node3D) -> bool:
	# Validate candidate data before mutating the current game, including NaN.
	var proposed = manifest.get("lanes",null)
	if not proposed is Array or proposed.size() != 3:
		return false
	var candidate_lanes: Array = []
	var ids: Array = []
	for lane in proposed:
		if not lane is Dictionary or not _number(lane.get("id")):
			return false
		var identity := int(lane.id)
		if float(identity) != float(lane.id) or identity not in [0,1,2] or ids.has(identity):
			return false
		ids.append(identity)
		var points = lane.get("points",null)
		if not points is Array or points.size() < 2 or points.size() > 32:
			return false
		var converted: Array[Vector3] = []
		var lengths: Array[float] = []
		var length_total := 0.0
		for value in points:
			if not _vector(value) or absf(float(value[1])) > .001:
				return false
			var point := Vector3(value[0],value[1],value[2])
			if not converted.is_empty():
				var distance := point.distance_to(converted[-1])
				if distance < .1 or distance > 1000:
					return false
				lengths.append(distance)
				length_total += distance
			converted.append(point)
		if length_total < 10 or length_total > 2000:
			return false
		candidate_lanes.append({"id":identity,"points":converted,"segments":lengths,"length":length_total})
	candidate_lanes.sort_custom(func(a,b):return a.id < b.id)
	var candidate_boxes: Array = []
	var supplied_boxes = manifest.get("authority_collision_boxes",[])
	var traversal = manifest.get("traversal",{})
	if not traversal is Dictionary or not supplied_boxes is Array:
		return false
	var all_boxes: Array = supplied_boxes.duplicate()
	var native_boxes = traversal.get("native_collision_boxes",[])
	if not native_boxes is Array:
		return false
	all_boxes.append_array(native_boxes)
	if all_boxes.size() > 128:
		return false
	for box in all_boxes:
		if not box is Dictionary or not _vector(box.get("position")) or not _vector(box.get("size")):
			return false
		var size := Vector3(box.size[0],box.size[1],box.size[2])
		if size.x <= 0 or size.y <= 0 or size.z <= 0:
			return false
		candidate_boxes.append({"position":Vector3(box.position[0],box.position[1],box.position[2]),"size":size})
	var bounds_data = manifest.get("bounds",{})
	if not bounds_data is Dictionary:
		return false
	var bounds = bounds_data.get("actor_xz",bounds_data.get("authority_xz",[-68,68,-128,128]))
	if not bounds is Array or bounds.size() != 4:
		return false
	for value in bounds:
		if not _number(value):return false
	if bounds[0] >= bounds[1] or bounds[2] >= bounds[3]:return false
	for lane in candidate_lanes:
		for i in range(int(ceil(lane.length/.5))+1):
			var sampled := _sample(lane,minf(i*.5,lane.length),0.0)
			if _blocked_with(sampled.position,candidate_boxes,bounds,.45):return false
	lanes = candidate_lanes
	boxes = candidate_boxes
	actor_bounds = bounds.duplicate()
	player = player_value
	configured = true
	reset()
	return true

func reset() -> void:
	_reset_state(true)

func _reset_state(normal_wave: bool) -> void:
	# Immediate destruction outside unit callbacks bounds same-frame repeated resets.
	for unit in units:
		if is_instance_valid(unit):
			unit.free()
	units.clear()
	_attacks.clear()
	_grid.clear()
	_lane_buckets.clear()
	elapsed = 0
	waves = 0
	wave_events = 0
	gold = 0
	kills = 0
	cores = {"sun":100.0,"moon":100.0}
	winner = ""
	max_alive_seen = 0
	max_nodes_seen = 0
	max_corpses_seen = 0
	max_attacks_seen = 0
	route_blocked_moves = 0
	separation_waits = 0
	invalid_steps = 0
	invalid_pulses = 0
	_invalid_damage_retired = 0
	kills_by_lane = [0,0,0]
	core_arrivals = [0,0,0]
	rejected_waves = 0
	next_id = 1
	_accumulator = 0
	_decision_clock = 0
	_next_wave = WAVE_INTERVAL
	siege_drill = false
	siege_windups = 0
	siege_impacts = 0
	siege_cancelled = 0
	siege_hits = 0
	siege_spawned_pairs = 0
	siege_rejected_pairs = 0
	_next_siege_id = 1
	_emit_siege_reset()
	if configured and normal_wave:
		_spawn_wave()
	gold_changed.emit(gold)
	changed.emit()

func _emit_siege_reset() -> void:
	siege_event.emit({"kind":"reset","id":0,"role":"","team":"","origin":Vector3.ZERO,"target":Vector3.ZERO,"delay":0.0,"radius":0.0,"damage":0.0})

func start_siege_drill() -> bool:
	if not configured or lanes.size() != 3 or float(lanes[1].length) < 40.0:
		return false
	var specification: Array = []
	for team_value in ["sun","moon"]:
		for pair in [["cannon_cart",16.0],["royal_chariot",12.0],["spearman",8.0]]:
			specification.append({"team":team_value,"role":pair[0],"lane":1,"progress":float(lanes[1].length)*.5-float(pair[1]),"lateral":0.0})
	if not _placements_clear(specification,true):
		return false
	_reset_state(false)
	siege_drill = true
	_spawn_specifications(specification)
	siege_spawned_pairs = 2
	_rebuild_buckets()
	_record_limits()
	changed.emit()
	return true

func interpolation_alpha() -> float:
	return clampf(_accumulator/STEP,0,1)

func _physics_process(delta: float) -> void:
	if not configured or not is_finite(delta) or delta <= 0:
		return
	_accumulator += minf(delta,.25)
	var steps := 0
	while _accumulator+1e-9 >= STEP and steps < 5:
		step_simulation(STEP)
		_accumulator = maxf(0,_accumulator-STEP)
		steps += 1

func step_simulation(delta := STEP) -> bool:
	if not configured or not is_finite(delta) or delta <= 0 or delta > STEP+.000001:
		invalid_steps += 1
		return false
	if not winner.is_empty():
		return true
	elapsed += delta
	_decision_clock -= delta
	for unit in units:
		unit.previous_position = unit.position
		unit.previous_yaw = unit.heading
		unit.moved = 0
		unit.attack_cooldown = maxf(0,unit.attack_cooldown-delta)
		unit.attack_time = maxf(0,unit.attack_time-delta)
		unit.hit_time = maxf(0,unit.hit_time-delta)
		if not unit.alive:
			unit.dead_age += delta
	_cleanup()
	_rebuild_buckets()
	if _decision_clock <= 0:
		_decision_clock += .20
		_acquire_targets()
	var attacks_due: Array = []
	var remaining: Array = []
	for attack in _attacks:
		if attack.at <= elapsed+1e-8:
			var source = instance_from_id(attack.source)
			if attack.get("kind", "normal") == "siege":
				if not is_instance_valid(source) or not source.alive or not line_clear(source.position,attack.point):
					_cancel_siege_attack(attack)
					continue
				# Commitment is a fixed ground point: never query the old target ID.
				for victim in units:
					if victim.alive and victim.team != attack.team and victim.position.distance_to(attack.point) <= float(attack.radius)+victim.radius and line_clear(attack.point,victim.position):
						attacks_due.append({"target":victim,"damage":attack.damage,"siege":true})
				siege_impacts += 1
				siege_event.emit(_siege_receipt(attack,false))
				continue
			var target = instance_from_id(attack.target)
			if is_instance_valid(source) and is_instance_valid(target) and source.alive and target.alive and source.position.distance_to(target.position) <= attack.reach+1.0 and line_clear(source.position,target.position):
				attacks_due.append({"target":target,"damage":attack.damage})
		else:
			remaining.append(attack)
	_attacks = remaining
	# Resolve valid simultaneous attacks after eligibility, avoiding first-team order bias.
	for attack in attacks_due:
		if is_instance_valid(attack.target) and attack.target.receive_damage(attack.damage,"army") and attack.get("siege",false):
			siege_hits += 1
	_rebuild_buckets()
	var core_damage := {"sun":0.0,"moon":0.0}
	for unit in units:
		if not unit.alive:continue
		var stats: Dictionary = Unit.STATS[unit.role]
		var valid_target: bool = is_instance_valid(unit.target) and unit.target.alive and unit.target.team != unit.team
		var in_range: bool = valid_target and unit.position.distance_to(unit.target.position) <= float(stats.range)
		if in_range and line_clear(unit.position,unit.target.position):
			var aim: Vector3 = unit.target.position-unit.position
			unit.heading = atan2(aim.x,aim.z)
			var siege: bool = unit.role in Unit.VEHICLE_ROLES
			if unit.attack_cooldown <= 0 and _attacks.size() < CAP and (not siege or _pending_siege_count() < SIEGE_ATTACK_CAP):
				var windup: float = unit.start_attack(unit.target.position)
				if siege:
					_queue_siege_attack(unit,unit.target.position,windup)
				else:
					_attacks.append({"kind":"normal","source":unit.get_instance_id(),"target":unit.target.get_instance_id(),"at":elapsed+windup,"damage":stats.damage,"reach":stats.range})
			continue
		if unit.attack_time > .1:continue
		var old_position: Vector3 = unit.position
		var next_progress := minf(float(lanes[unit.lane_id].length),unit.progress+float(stats.speed)*delta)
		var sample := route_sample(unit.lane_id,next_progress,unit.team,unit.lateral)
		if _blocked_with(sample.position,boxes,actor_bounds,unit.radius) or not line_clear(old_position,sample.position,unit.radius):
			route_blocked_moves += 1
			continue
		if _occupied(sample.position,unit):
			separation_waits += 1
			continue
		_grid_remove(unit)
		unit.progress = next_progress
		unit.position = sample.position
		unit.heading = sample.yaw
		unit.moved = old_position.distance_to(unit.position)
		unit.state = "walk"
		_grid_add(unit)
		if unit.progress >= float(lanes[unit.lane_id].length)-.05:
			var enemy := "moon" if unit.team == "sun" else "sun"
			core_damage[enemy] += float(stats.core_damage)
			core_arrivals[unit.lane_id] += 1
			unit.arrive()
	cores.sun = maxf(0,cores.sun-core_damage.sun)
	cores.moon = maxf(0,cores.moon-core_damage.moon)
	_cleanup()
	if cores.sun <= 0 and cores.moon <= 0:winner = "draw"
	elif cores.sun <= 0:winner = "moon"
	elif cores.moon <= 0:winner = "sun"
	if not winner.is_empty():
		_attacks.clear()
		_emit_siege_reset()
		outcome.emit(winner)
		changed.emit()
	elif not siege_drill and elapsed+1e-8 >= _next_wave:
		_next_wave += WAVE_INTERVAL
		_spawn_wave()
	_cleanup()
	_record_limits()
	return true

func _pending_siege_count() -> int:
	var count := 0
	for attack in _attacks:
		if attack.get("kind", "normal") == "siege":count += 1
	return count

func _queue_siege_attack(unit, point: Vector3, delay: float) -> void:
	var stats: Dictionary = Unit.STATS[unit.role]
	var fixed_point := Vector3(point.x,0.0,point.z)
	# Match original vehicle weapon geometry without depending on rendered nodes.
	var muzzle := Vector3(0,.99,.632) if unit.role == "cannon_cart" else Vector3(0,1.33,.70)
	var origin := to_global(unit.position+Basis(Vector3.UP,unit.heading)*muzzle)
	var attack := {"kind":"siege","id":_next_siege_id,"role":unit.role,"team":unit.team,
		"source":unit.get_instance_id(),"point":fixed_point,"origin":origin,
		"target_world":to_global(fixed_point),"at":elapsed+delay,"delay":delay,"radius":float(stats.blast_radius),"damage":float(stats.damage)}
	_next_siege_id += 1
	_attacks.append(attack)
	siege_windups += 1
	var event := _siege_receipt(attack,false)
	event.kind = "windup"
	event.delay = delay
	siege_event.emit(event)

func _siege_receipt(attack: Dictionary, cancelled: bool) -> Dictionary:
	return {"kind":"impact","id":attack.id,"role":attack.role,"team":attack.team,"origin":attack.origin,
		"target":attack.target_world,"delay":0.0,"radius":attack.radius,"damage":0.0 if cancelled else attack.damage,"cancelled":cancelled}

func _cancel_siege_attack(attack: Dictionary) -> void:
	siege_cancelled += 1
	siege_event.emit(_siege_receipt(attack,true))

func _cancel_source_attacks(source_id: int) -> void:
	var retained: Array = []
	for attack in _attacks:
		if attack.source == source_id:
			if attack.get("kind", "normal") == "siege":_cancel_siege_attack(attack)
		else:
			retained.append(attack)
	_attacks = retained

func _sample(lane: Dictionary, distance: float, offset: float) -> Dictionary:
	var remaining := clampf(distance,0,lane.length)
	for index in range(lane.segments.size()):
		var segment: float = lane.segments[index]
		if remaining <= segment or index == lane.segments.size()-1:
			var direction: Vector3 = (lane.points[index+1]-lane.points[index]).normalized()
			var point: Vector3 = lane.points[index].lerp(lane.points[index+1],clampf(remaining/segment,0,1))
			point += Vector3(direction.z,0,-direction.x)*offset
			return {"position":point,"yaw":atan2(direction.x,direction.z)}
		remaining -= segment
	return {"position":lane.points[-1],"yaw":0.0}

func route_sample(lane_id: int, distance: float, team: String, offset := 0.0) -> Dictionary:
	var lane: Dictionary = lanes[lane_id]
	var result := _sample(lane,distance if team == "sun" else lane.length-distance,offset if team == "sun" else -offset)
	if team == "moon":result.yaw = wrapf(result.yaw+PI,-PI,PI)
	return result

func _spawn_wave() -> void:
	wave_events += 1
	var spawned := false
	for order in range(3):
		var lane_id := (order+wave_events-1)%3
		var specifications: Array = []
		for team_value in ["sun","moon"]:
			for slot in range(5):
				specifications.append({"team":team_value,"role":FORMATION[slot],"lane":lane_id,"progress":START_DISTANCE[slot],"lateral":OFFSETS[slot]})
		if _spawn_specifications(specifications):
			spawned = true
		else:
			rejected_waves += 1
	# Initial thirty remain unchanged. Whole mirrored pairs are accepted or refused.
	if wave_events%3 == 0:
		for order in range(3):
			spawned = _spawn_siege_pair((order+wave_events-1)%3,"cannon_cart") or spawned
	if wave_events%5 == 0:
		spawned = _spawn_siege_pair(1,"royal_chariot") or spawned
	if spawned:waves += 1
	_record_limits()
	changed.emit()

func _spawn_siege_pair(lane_id: int, role: String) -> bool:
	# All lanes share one endpoint. Five metres separates their branching routes
	# and fits the cart between the existing offset bow ranks without overlap.
	var progress := 5.0 if role == "cannon_cart" else 11.8
	var specs: Array = []
	for team_value in ["sun","moon"]:
		specs.append({"team":team_value,"role":role,"lane":lane_id,"progress":progress,"lateral":0.0})
	if _spawn_specifications(specs):
		siege_spawned_pairs += 1
		return true
	siege_rejected_pairs += 1
	return false

func _vehicle_route_clear(lane_id: int, radius: float) -> bool:
	var points: Array = lanes[lane_id].points
	for index in points.size():
		if _blocked_with(points[index],boxes,actor_bounds,radius):return false
		if index > 0 and not line_clear(points[index-1],points[index],radius):return false
	return true

func _placements_clear(specifications: Array, ignore_existing := false) -> bool:
	var existing_count := 0 if ignore_existing else units.size()
	var existing_alive := 0 if ignore_existing else _alive_count()
	if specifications.is_empty() or specifications.size()+existing_count > TOTAL_CAP or specifications.size()+existing_alive > CAP:
		return false
	var proposed: Array = []
	for spec in specifications:
		if not spec is Dictionary or not Unit.STATS.has(spec.get("role", "")) or spec.get("team", "") not in ["sun","moon"] or not _number(spec.get("lane")) or not _number(spec.get("progress")) or not _number(spec.get("lateral")):
			return false
		var lane_id := int(spec.lane)
		if lane_id < 0 or lane_id >= lanes.size() or float(lane_id) != float(spec.lane) or spec.progress < 0 or spec.progress > lanes[lane_id].length:
			return false
		var radius: float = Unit.STATS[spec.role].radius
		var point: Vector3 = route_sample(lane_id,spec.progress,spec.team,spec.lateral).position
		if _blocked_with(point,boxes,actor_bounds,radius):return false
		if spec.role in Unit.VEHICLE_ROLES and not _vehicle_route_clear(lane_id,radius):return false
		if not ignore_existing:
			for existing in units:
				if existing.alive and point.distance_squared_to(existing.position) < pow(radius+existing.radius,2):return false
		for prior in proposed:
			if point.distance_squared_to(prior.position) < pow(radius+prior.radius,2):return false
		proposed.append({"position":point,"radius":radius})
	return true

func _spawn_specifications(specifications: Array) -> bool:
	if not _placements_clear(specifications):return false
	for spec in specifications:
		var unit = Unit.new()
		unit.setup(self,next_id,spec.team,spec.role,int(spec.lane))
		next_id += 1
		unit.render_art = visual_enabled
		unit.progress = spec.progress
		unit.lateral = spec.lateral
		var sampled := route_sample(unit.lane_id,unit.progress,unit.team,unit.lateral)
		unit.position = sampled.position
		unit.heading = sampled.yaw
		unit.previous_yaw = unit.heading
		unit.defeated.connect(_on_defeated)
		add_child(unit)
		units.append(unit)
	return true

func _on_defeated(unit: Node3D, by_player: bool) -> void:
	_cancel_source_attacks(unit.get_instance_id())
	# Only the last damaging player hit grants confirmed currency, exactly once.
	kills_by_lane[unit.lane_id] += 1
	# Retire older corpses, never the unit whose damage callback is on the stack.
	var dead: Array = []
	for existing in units:
		if not existing.alive:dead.append(existing)
	while dead.size()>CORPSE_CAP:
		var retired = dead.pop_front()
		if retired == unit:
			dead.append(retired)
			continue
		_invalid_damage_retired += retired.invalid_damage
		units.erase(retired)
		retired.free()
	_record_limits()
	if by_player and unit.team == "moon":
		gold += int(Unit.STATS[unit.role].gold)
		kills += 1
		gold_changed.emit(gold)
	changed.emit()

func _cleanup() -> void:
	var corpses := 0
	var retained: Array = []
	for unit in units:
		var remove := false
		if not unit.alive:
			corpses += 1
			remove = unit.dead_age >= 1.20 or corpses > CORPSE_CAP
		if remove:
			_invalid_damage_retired += unit.invalid_damage
			unit.free()
		else:
			retained.append(unit)
	units = retained

func _cell(point: Vector3) -> Vector2i:
	return Vector2i(floori(point.x/1.0),floori(point.z/1.0))

func _grid_add(unit: Node3D) -> void:
	var key := _cell(unit.position)
	if not _grid.has(key):_grid[key] = []
	_grid[key].append(unit)

func _grid_remove(unit: Node3D) -> void:
	var key := _cell(unit.position)
	if _grid.has(key):_grid[key].erase(unit)

func _rebuild_buckets() -> void:
	_grid.clear()
	_lane_buckets.clear()
	for lane_id in range(3):
		_lane_buckets[str(lane_id)+"sun"] = []
		_lane_buckets[str(lane_id)+"moon"] = []
	for unit in units:
		if unit.alive:
			_grid_add(unit)
			_lane_buckets[str(unit.lane_id)+unit.team].append(unit)

func _occupied(point: Vector3, unit: Node3D) -> bool:
	var key := _cell(point)
	var reach := ceili(unit.radius+MAX_UNIT_RADIUS)
	for x in range(-reach,reach+1):
		for z in range(-reach,reach+1):
			for other in _grid.get(key+Vector2i(x,z),[]):
				if other != unit and other.alive and point.distance_squared_to(other.position) < pow(unit.radius+other.radius,2):
					return true
	return false

func _acquire_targets() -> void:
	for unit in units:
		if not unit.alive:continue
		unit.target = null
		var reach := maxf(16.0,float(Unit.STATS[unit.role].range))
		var nearest := reach*reach
		var enemy := "moon" if unit.team == "sun" else "sun"
		for other in _lane_buckets.get(str(unit.lane_id)+enemy,[]):
			var distance: float = unit.position.distance_squared_to(other.position)
			if distance < nearest and line_clear(unit.position,other.position):
				nearest = distance
				unit.target = other

func _blocked_with(point: Vector3, obstacles: Array, bounds: Array, margin: float) -> bool:
	if point.x < bounds[0]+margin or point.x > bounds[1]-margin or point.z < bounds[2]+margin or point.z > bounds[3]-margin:
		return true
	for box in obstacles:
		if absf(point.x-box.position.x) <= box.size.x*.5+margin and absf(point.z-box.position.z) <= box.size.z*.5+margin:
			return true
	return false

func line_clear(from_point: Vector3, to_point: Vector3, margin := 0.0) -> bool:
	if not from_point.is_finite() or not to_point.is_finite() or not is_finite(margin) or margin < 0:return false
	# Exact planar segment/AABB slab test, not a ray that can skip thin walls.
	for box in boxes:
		var minimum: Vector3 = box.position-box.size*.5-Vector3(margin,0,margin)
		var maximum: Vector3 = box.position+box.size*.5+Vector3(margin,0,margin)
		var t_min := 0.0
		var t_max := 1.0
		var intersects := true
		for axis in [0,2]:
			var direction: float = to_point[axis]-from_point[axis]
			if absf(direction)<1e-8:
				if from_point[axis]<minimum[axis] or from_point[axis]>maximum[axis]:intersects = false
			else:
				var near_value: float = (minimum[axis]-from_point[axis])/direction
				var far_value: float = (maximum[axis]-from_point[axis])/direction
				t_min = maxf(t_min,minf(near_value,far_value))
				t_max = minf(t_max,maxf(near_value,far_value))
				if t_min>t_max:intersects = false
		if intersects:return false
	return true

func pulse(origin: Vector3, radius: float, damage) -> int:
	if not origin.is_finite() or not is_finite(radius) or radius <= 0 or radius > 40 or not _number(damage) or float(damage) <= 0 or float(damage)>1000:
		invalid_pulses += 1
		return 0
	if not winner.is_empty():return 0
	var hits := 0
	for unit in units.duplicate():
		if is_instance_valid(unit) and unit.alive and unit.team == "moon" and (unit.position+Vector3.UP).distance_to(origin) <= radius and line_clear(origin,unit.position):
			if unit.take_hit(damage):hits += 1
	return hits

func _alive_count() -> int:
	var count := 0
	for unit in units:
		if unit.alive:count += 1
	return count

func _record_limits() -> void:
	var alive := _alive_count()
	max_alive_seen = maxi(max_alive_seen,alive)
	max_nodes_seen = maxi(max_nodes_seen,units.size())
	max_corpses_seen = maxi(max_corpses_seen,units.size()-alive)
	max_attacks_seen = maxi(max_attacks_seen,_attacks.size())

func minimap_units() -> Array:
	var result: Array = []
	for unit in units:
		if unit.alive:result.append({"position":unit.position,"team":unit.team,"role":unit.role,"radius":unit.radius})
	return result

func report() -> Dictionary:
	var invalid := _invalid_damage_retired
	var finite := true
	var alive_by_lane := [0,0,0]
	var roles_alive := {}
	for role in Unit.STATS:roles_alive[role] = 0
	for unit in units:
		invalid += unit.invalid_damage
		finite = finite and unit.articulation_finite()
		if unit.alive:
			alive_by_lane[unit.lane_id] += 1
			roles_alive[unit.role] += 1
	var alive := _alive_count()
	return {"configured":configured,"alive":alive,"cap":CAP,"unit_nodes":units.size(),"total_cap":TOTAL_CAP,
		"pending_cleanup":units.size()-alive,"corpse_cap":CORPSE_CAP,"queued_for_deletion":0,"queued_attacks":_attacks.size(),
		"max_alive_seen":max_alive_seen,"max_nodes_seen":max_nodes_seen,"max_corpses_seen":max_corpses_seen,"max_attacks_seen":max_attacks_seen,
		"waves":waves,"wave_events":wave_events,"next_wave_seconds":maxf(0,_next_wave-elapsed),"rejected_wave_pairs":rejected_waves,
		"elapsed":elapsed,"gold":gold,"kills":kills,"cores":cores.duplicate(),"winner":winner,
		"invalid_damage":invalid,"invalid_steps":invalid_steps,"invalid_pulses":invalid_pulses,
		"route_blocked_moves":route_blocked_moves,"separation_waits":separation_waits,"alive_by_lane":alive_by_lane,
		"kills_by_lane":kills_by_lane.duplicate(),"core_arrivals":core_arrivals.duplicate(),"finite":finite,
		"siege_drill":siege_drill,"roles_alive":roles_alive,
		"siege":{"windups":siege_windups,"impacts":siege_impacts,"cancelled":siege_cancelled,"hits":siege_hits,
			"spawned_pairs":siege_spawned_pairs,"rejected_pairs":siege_rejected_pairs,"pending":_pending_siege_count(),"pending_cap":SIEGE_ATTACK_CAP,"next_attack_id":_next_siege_id},
		"scope":"Offline deterministic original lane armies; no live network or commercial-game reconstruction."}
