extends RefCounted
## Offline authority. Presentation, animation and frame capture never advance it.
const RULES_PATH := "res://assets/tactical/rules.json"
const TEAMS := ["sun", "moon"]
const SHOP := {
	"pistol":{"label":"ARKA sidearm","cost":0,"kind":"weapon","max":1},
	"carbine":{"label":"SURYA carbine","cost":2900,"kind":"weapon","max":1},
	"armor":{"label":"Kavacha armor","cost":1000,"kind":"armor","max":50},
	"q":{"label":"Solar veil","cost":200,"kind":"utility","max":2},
	"e":{"label":"Measured step","cost":100,"kind":"utility","max":1},
	"c":{"label":"Ward wall","cost":300,"kind":"utility","max":1}}
var config: Dictionary = {}
var configured := false
var actors: Array[Dictionary] = []
var phase := "match_end"
var round_number := 1
var scores := {"sun":0,"moon":0}
var attack_team := "sun"
var time_left := 0.0
var site := ""
var winner := ""
var reason := ""
var events: Array[Dictionary] = []
var generation := 0
var elapsed := 0.0
var event_sequence := 0
var interaction_actor := -1
var interaction_progress := 0.0
var _interaction_site := ""
var _interaction_seconds := 0.0
var _interaction_tick := -1
var _tick_id := 0
var _tick_delta := 0.0

func _init() -> void:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(RULES_PATH))
	if not parsed is Dictionary: return
	config = parsed
	configured = config.get("schema_version") == 1 and config.get("players_per_team") == 5 and config.get("rounds_to_win") == 13 and _catalog_valid(config.get("catalog"))
	for key in ["buy_seconds","live_seconds","planted_seconds","plant_seconds","defuse_seconds","result_seconds","start_credits","credit_cap","win_credits","loss_credits","kill_credits","max_health","max_armor","ult_cost","swap_after_round"]:
		var value = config.get(key)
		if not typeof(value) in [TYPE_INT,TYPE_FLOAT] or not is_finite(float(value)) or float(value) <= 0: configured = false

func _catalog_valid(value: Variant) -> bool:
	if not value is Dictionary or value.size()!=SHOP.size(): return false
	for id in SHOP:
		if not value.get(id) is Dictionary or value[id].size()!=SHOP[id].size(): return false
		for key in SHOP[id]:
			# JSON numbers load as floats; compare validated numeric value, not
			# Dictionary's stricter int/float Variant identity.
			if key in ["cost","max"]:
				var amount = value[id].get(key)
				if not typeof(amount) in [TYPE_INT,TYPE_FLOAT] or not is_finite(float(amount)) or float(amount)!=float(SHOP[id][key]): return false
			elif value[id].get(key)!=SHOP[id][key]: return false
	return true

func _emit(kind: String, data: Dictionary = {}) -> void:
	event_sequence += 1
	var event := data.duplicate(true)
	event.merge({"kind":kind,"seq":event_sequence,"generation":generation,"round_number":round_number,"phase":phase,"time_s":elapsed},true)
	events.append(event)
	if events.size() > 512: events.pop_front()

func start_match() -> void:
	if not configured:
		_emit("configuration_error",{"reason":"Invalid tactical rules"})
		return
	actors.clear()
	events.clear()
	generation += 1
	elapsed = 0
	_tick_id = 0
	_tick_delta = 0
	scores = {"sun":0,"moon":0}
	round_number = 1
	attack_team = "sun"
	var names := ["Rama · You","Tara","Kabir","Mira","Arun","Varun","Nila","Dev","Asha","Ravi"]
	for id in range(10):
		actors.append({"id":id,"team":"sun" if id<5 else "moon","name":names[id],"alive":true,"health":100,"armor":0,"credits":int(config.start_credits),"weapon":"pistol","charges":{"q":0,"e":1,"c":0},"ult":0,"kills":0,"deaths":0})
	phase = "buy"
	time_left = float(config.buy_seconds)
	site = ""
	winner = ""
	reason = "Equip at your spawn"
	_clear_interaction()
	_emit("match_start")
	_emit("round_start",{"attack_team":attack_team})

func tick(delta: float) -> void:
	# Bound host steps; pause is represented by no ticks, never wall-clock time.
	if not configured or actors.size()!=10 or not is_finite(delta) or delta<=0 or delta>.25 or phase=="match_end": return
	_tick_id += 1
	_tick_delta = delta
	elapsed += delta
	if interaction_actor>=0 and _interaction_tick < _tick_id-1: _clear_interaction()
	time_left = maxf(0,time_left-delta)
	if time_left>0.0000001: return
	match phase:
		"buy":
			phase="live"
			time_left=float(config.live_seconds)
			reason="Attune or defend the sanctums"
			_clear_interaction()
			_emit("buy_end")
		"live": _finish_round(other_team(attack_team),"Time expired")
		"planted": _finish_round(attack_team,"Astra detonated")
		"round_end": _next_round()

func other_team(team: String) -> String:
	return "moon" if team=="sun" else "sun"

func _valid_actor(id: int) -> bool:
	return id>=0 and id<actors.size() and int(actors[id].id)==id

func damage(target_id: int, amount: float, attacker_id: int) -> bool:
	if phase not in ["live","planted"] or not _valid_actor(target_id) or not actors[target_id].alive or not is_finite(amount) or amount<=0 or amount>1000: return false
	if attacker_id!=-1 and (not _valid_actor(attacker_id) or not actors[attacker_id].alive or actors[attacker_id].team==actors[target_id].team): return false
	var target: Dictionary=actors[target_id]
	var absorbed := minf(float(target.armor),amount)
	target.armor -= absorbed
	var health_damage := maxf(0,amount-float(absorbed))
	target.health = maxf(0,float(target.health)-health_damage)
	_emit("damage",{"target_id":target_id,"attacker_id":attacker_id,"amount":amount,"armor_damage":absorbed,"health":target.health})
	if target.health<=0:
		target.alive=false
		target.deaths+=1
		cancel_interaction(target_id)
		if _valid_actor(attacker_id):
			actors[attacker_id].kills+=1
			_credit(attacker_id,int(config.kill_credits))
			actors[attacker_id].ult=mini(int(config.ult_cost),int(actors[attacker_id].ult)+1)
		_emit("elimination",{"target_id":target_id,"attacker_id":attacker_id})
		_check_elimination()
	return true

func _check_elimination() -> void:
	if phase not in ["live","planted"]: return
	var living := {"sun":0,"moon":0}
	for actor in actors:
		if actor.alive: living[actor.team]+=1
	if living[other_team(attack_team)]==0: _finish_round(attack_team,"Defenders eliminated")
	elif phase=="live" and living[attack_team]==0: _finish_round(other_team(attack_team),"Attackers eliminated")

func purchase(actor_id: int, item: String) -> bool:
	if phase!="buy" or not _valid_actor(actor_id) or not actors[actor_id].alive or not SHOP.has(item): return false
	var actor: Dictionary=actors[actor_id]
	var offer: Dictionary=SHOP[item]
	if int(actor.credits)<int(offer.cost): return false
	match str(offer.kind):
		"weapon":
			if actor.weapon==item: return false
			# A free pistol cannot replace a bought carbine and discard its value.
			if item=="pistol": return false
			actor.weapon=item
		"armor":
			if int(actor.armor)>=int(offer.max): return false
			actor.armor=int(offer.max)
		"utility":
			if int(actor.charges.get(item,0))>=int(offer.max): return false
			actor.charges[item]=int(actor.charges.get(item,0))+1
	actor.credits-=int(offer.cost)
	_emit("purchase",{"actor_id":actor_id,"item":item,"cost":offer.cost,"credits":actor.credits})
	return true

func use_ability(actor_id: int, slot: String) -> bool:
	if phase not in ["live","planted"] or not _valid_actor(actor_id) or not actors[actor_id].alive: return false
	var actor: Dictionary=actors[actor_id]
	if slot=="x":
		if int(actor.ult)<int(config.ult_cost): return false
		actor.ult-=int(config.ult_cost)
	elif slot in ["q","e","c"]:
		if int(actor.charges.get(slot,0))<=0: return false
		actor.charges[slot]-=1
	else: return false
	cancel_interaction(actor_id)
	_emit("ability",{"actor_id":actor_id,"slot":slot})
	return true

func interact(actor_id: int, site_name: String, delta: float) -> bool:
	# Caller verifies physical proximity. Only this authority clock may accrue a
	# hold: repeated calls, invalid deltas and a missing frame cannot accelerate it.
	if not is_finite(delta) or delta<=0 or delta>.25 or _tick_delta<=0 or not _valid_actor(actor_id) or not actors[actor_id].alive or site_name not in ["A","B"]: return false
	var planting: bool = phase=="live" and actors[actor_id].team==attack_team
	var defusing: bool = phase=="planted" and actors[actor_id].team!=attack_team and site_name==site
	if not planting and not defusing:
		cancel_interaction(actor_id)
		return false
	if interaction_actor>=0 and interaction_actor!=actor_id: return false
	if interaction_actor==actor_id and _interaction_tick==_tick_id: return false
	if interaction_actor!=actor_id or _interaction_site!=site_name or _interaction_tick!=_tick_id-1:
		_clear_interaction()
		interaction_actor=actor_id
		_interaction_site=site_name
	_interaction_tick=_tick_id
	_interaction_seconds+=minf(delta,_tick_delta)
	var required := float(config.plant_seconds if planting else config.defuse_seconds)
	interaction_progress=clampf(_interaction_seconds/required,0,1)
	if _interaction_seconds+0.0000001<required: return true
	actors[actor_id].ult=mini(int(config.ult_cost),int(actors[actor_id].ult)+1)
	if planting:
		site=site_name
		phase="planted"
		time_left=float(config.planted_seconds)
		reason="Astra attuned at "+site
		_clear_interaction()
		_emit("plant",{"actor_id":actor_id,"site":site})
	else:
		_emit("defuse",{"actor_id":actor_id,"site":site})
		_finish_round(other_team(attack_team),"Astra severed")
	return true

func cancel_interaction(actor_id: int) -> void:
	if interaction_actor==actor_id: _clear_interaction()

func _clear_interaction() -> void:
	interaction_actor=-1
	interaction_progress=0
	_interaction_seconds=0
	_interaction_site=""
	_interaction_tick=-1

func _credit(actor_id: int, amount: int) -> void:
	actors[actor_id].credits=clampi(int(actors[actor_id].credits)+amount,0,int(config.credit_cap))

func _finish_round(team: String, result: String) -> void:
	if phase not in ["live","planted"]: return
	winner=team
	reason=result
	scores[team]+=1
	_clear_interaction()
	for actor in actors:
		_credit(int(actor.id),int(config.win_credits if actor.team==team else config.loss_credits))
	phase="round_end"
	time_left=float(config.result_seconds)
	_emit("round_end",{"winner":winner,"reason":reason,"scores":scores.duplicate()})
	if int(scores[team])>=int(config.rounds_to_win):
		phase="match_end"
		time_left=0
		_emit("match_end",{"winner":winner,"reason":reason,"scores":scores.duplicate()})

func _next_round() -> void:
	if round_number==int(config.swap_after_round):
		attack_team=other_team(attack_team)
		_emit("side_swap",{"attack_team":attack_team})
	round_number+=1
	generation+=1
	for actor in actors:
		if not actor.alive:
			actor.weapon="pistol"
			actor.armor=0
			actor.charges={"q":0,"e":1,"c":0}
		actor.charges.e=1
		actor.health=int(config.max_health)
		actor.alive=true
	phase="buy"
	time_left=float(config.buy_seconds)
	site=""
	winner=""
	reason="Equip at your spawn"
	_clear_interaction()
	_emit("round_start",{"attack_team":attack_team})

func drain_events() -> Array[Dictionary]:
	var result: Array[Dictionary]=events.duplicate(true)
	events.clear()
	return result

func snapshot() -> Dictionary:
	return {"configured":configured,"mode":"Casual · offline 5v5","actors":actors.duplicate(true),"phase":phase,"round_number":round_number,"scores":scores.duplicate(),"attack_team":attack_team,"time_left":time_left,"site":site,"winner":winner,"reason":reason,"interaction_progress":interaction_progress,"interaction_actor":interaction_actor,"interaction_site":_interaction_site,"generation":generation,"elapsed":elapsed,"catalog":SHOP.duplicate(true),"target_score":int(config.get("rounds_to_win",13)),"ult_cost":int(config.get("ult_cost",6))}
