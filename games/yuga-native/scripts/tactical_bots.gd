extends Node
## Deterministic local opponents/teammates. Movement/fire are host-owned physics.
## No clairvoyant shot: every attack requires current host line of sight.
var host: Node
var states: Dictionary = {}
var generation := -1
var configured := false
var counters := {"moves":0,"shots_requested":0,"holds":0,"buys":0}

func configure(value: Node) -> bool:
	if not is_instance_valid(value): return false
	for method in ["bot_move","bot_fire","line_of_sight","actor_position"]:
		if not value.has_method(method): return false
	if value.get("rules")==null or value.get("map")==null or not value.get("actor_nodes") is Dictionary: return false
	host=value
	states.clear()
	generation=-1
	configured=true
	return true

func _reset_states() -> void:
	states.clear()
	generation=int(host.rules.generation)
	for actor in host.rules.actors:
		var id: int=actor.id
		if id==0: continue
		states[id]={"site":"A" if id%2==0 else "B","route":[],"waypoint":0,"target":-1,"reaction":0.0,"fire_wait":0.0,"bought":false,"route_phase":""}

func step(delta: float) -> void:
	if not configured or not is_instance_valid(host) or not is_finite(delta) or delta<=0 or delta>.25: return
	if host.rules.generation!=generation: _reset_states()
	if host.rules.phase=="buy":
		for id in states: _buy(int(id))
		return
	if host.rules.phase not in ["live","planted"]: return
	for actor in host.rules.actors:
		if host.rules.phase not in ["live","planted"]: break
		var id: int=actor.id
		if id==0 or not states.has(id): continue
		if not actor.alive or not host.actor_nodes.has(id):
			host.rules.cancel_interaction(id)
			continue
		_act(id,delta)

func _buy(id: int) -> void:
	var state: Dictionary=states[id]
	if state.bought or not host.rules.actors[id].alive or not host.actor_nodes.has(id): return
	# The map's physical own-spawn rule also applies to bot purchases.
	if not host.map.is_buy_zone(host.actor_position(id),host.rules.actors[id].team,host.rules.attack_team): return
	if host.rules.purchase(id,"carbine"): counters.buys+=1
	if host.rules.purchase(id,"armor"): counters.buys+=1
	state.bought=true

func _enemy(id: int) -> int:
	var closest := -1
	var distance := 60.0
	var position: Vector3=host.actor_position(id)
	for actor in host.rules.actors:
		if not actor.alive or actor.team==host.rules.actors[id].team or not host.actor_nodes.has(actor.id): continue
		var target_position: Vector3=host.actor_position(actor.id)
		if not target_position.is_finite(): continue
		var candidate := position.distance_to(target_position)
		if candidate<distance and host.line_of_sight(id,actor.id):
			distance=candidate
			closest=actor.id
	return closest

func _route_to(id: int, site_name: String) -> void:
	var actor: Dictionary=host.rules.actors[id]
	var state: Dictionary=states[id]
	var route: Array[Vector3]=host.map.route(actor.team,id%5,host.rules.attack_team,site_name)
	if state.site!=site_name and not state.route.is_empty():
		# Retrace known clear route segments before taking the other site route.
		# A direct nearest-waypoint shortcut could cut through real map cover.
		var retreat: Array[Vector3]=[]
		for index in range(maxi(0,int(state.waypoint)-1),-1,-1): retreat.append(state.route[index])
		for point in route:
			if retreat.is_empty() or retreat.back().distance_to(point)>.1: retreat.append(point)
		route=retreat
	state.route=route
	state.waypoint=0
	state.site=site_name
	state.route_phase=host.rules.phase
	# Spawn is part of the map API route. New rounds start there; retakes use
	# the explicit reverse prefix above rather than teleporting route progress.

func _move_route(id: int, delta: float) -> void:
	var state: Dictionary=states[id]
	var route: Array=state.route
	if route.is_empty(): return
	var position: Vector3=host.actor_position(id)
	while int(state.waypoint)<route.size()-1 and position.distance_to(route[int(state.waypoint)])<1.4:
		state.waypoint+=1
	var target: Vector3=route[int(state.waypoint)]
	if position.distance_to(target)>.6:
		host.bot_move(id,target,delta)
		counters.moves+=1

func _act(id: int, delta: float) -> void:
	var actor: Dictionary=host.rules.actors[id]
	var state: Dictionary=states[id]
	var position: Vector3=host.actor_position(id)
	if not position.is_finite():
		host.rules.cancel_interaction(id)
		return
	state.fire_wait=maxf(0,float(state.fire_wait)-delta)
	var target := _enemy(id)
	if target!=int(state.target):
		state.target=target
		state.reaction=.30+float(id%5)*.045
	if target>=0:
		host.rules.cancel_interaction(id)
		state.reaction=maxf(0,float(state.reaction)-delta)
		if state.reaction<=0 and state.fire_wait<=0 and host.line_of_sight(id,target):
			host.bot_fire(id,target)
			counters.shots_requested+=1
			state.fire_wait=.22 if actor.weapon=="carbine" else .48
		return
	state.reaction=0
	var site_name: String=host.rules.site if host.rules.phase=="planted" else state.site
	if not host.map.sites.has(site_name):
		host.rules.cancel_interaction(id)
		return
	if state.route.is_empty() or state.site!=site_name: _route_to(id,site_name)
	else: state.route_phase=host.rules.phase
	var center: Vector3=host.map.sites[site_name]
	var in_site := Vector2(position.x-center.x,position.z-center.z).length()<=minf(float(host.map.site_radius),2.8) and absf(position.y-center.y)<1.5
	var may_plant: bool=host.rules.phase=="live" and actor.team==host.rules.attack_team
	var may_defuse: bool=host.rules.phase=="planted" and actor.team!=host.rules.attack_team
	if in_site and (may_plant or may_defuse):
		if host.rules.interact(id,site_name,delta): counters.holds+=1
		return
	host.rules.cancel_interaction(id)
	# Attackers hold their armed site. Defenders rotate and actually defuse.
	if host.rules.phase=="planted" and actor.team==host.rules.attack_team and in_site: return
	_move_route(id,delta)

func report() -> Dictionary:
	return {"configured":configured,"generation":generation,"states":states.duplicate(true),"counts":counters.duplicate(),"scope":"Nine deterministic local bots; host physics/line of sight/fire authority; no online or human skill claim."}
