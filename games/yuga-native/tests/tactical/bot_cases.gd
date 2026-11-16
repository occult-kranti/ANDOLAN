extends SceneTree
const Rules = preload("res://scripts/tactical_round_rules.gd")
const Bots = preload("res://scripts/tactical_bots.gd")
var checks: Array[Dictionary]=[]

class MapFixture extends Node3D:
	var sites: Dictionary={"A":Vector3(-5,0,0),"B":Vector3(5,0,0)}
	var site_radius:=5.0
	func spawn(team: String,index: int,attack_team: String) -> Vector3:
		return Vector3(float(index-2)*1.3,0,-10 if team==attack_team else 10)
	func route(team: String,index: int,attack_team: String,target_site: String) -> Array[Vector3]:
		var start:=spawn(team,index,attack_team)
		return [start,Vector3(sites[target_site].x,0,start.z*.5),sites[target_site]]
	func is_buy_zone(pos: Vector3,team: String,attack_team: String) -> bool:
		return absf(pos.z-(-10.0 if team==attack_team else 10.0))<3 and absf(pos.x)<10

class HostFixture extends Node:
	var rules=Rules.new()
	var map=MapFixture.new()
	var actor_nodes: Dictionary={}
	var shots: Array[Dictionary]=[]
	var moves: Array[Dictionary]=[]
	var allow_los:=false
	func _init() -> void:
		rules.start_match()
		add_child(map)
		for actor in rules.actors:
			var body:=Node3D.new()
			add_child(body)
			actor_nodes[actor.id]=body
		reset_positions()
	func reset_positions() -> void:
		for actor in rules.actors:actor_nodes[actor.id].position=map.spawn(actor.team,actor.id%5,rules.attack_team)
	func actor_position(id: int) -> Vector3:return actor_nodes[id].position
	func line_of_sight(_from_id: int,_to_id: int) -> bool:return allow_los
	func bot_move(id: int,target: Vector3,delta: float) -> void:
		moves.append({"id":id,"target":target})
		actor_nodes[id].position=actor_nodes[id].position.move_toward(target,5*delta)
	func bot_fire(id: int,target_id: int) -> void:
		shots.append({"id":id,"target":target_id,"elapsed":rules.elapsed,"phase":rules.phase})
		rules.damage(target_id,35 if rules.actors[id].weapon=="carbine" else 22,id)

func check(label: String,condition: bool,detail: Dictionary={}) -> void:
	checks.append({"case":label,"passed":condition,"detail":detail})

func advance(host,bots,seconds: float) -> void:
	var remaining:=seconds
	while remaining>0.000001:
		var delta:=minf(.1,remaining)
		var before: int=host.rules.generation
		host.rules.tick(delta)
		if before!=host.rules.generation:host.reset_positions()
		bots.step(delta)
		remaining-=delta

func _initialize() -> void:
	var host=HostFixture.new()
	var bots=Bots.new()
	check("complete host API configures",bots.configure(host))
	bots.step(.1)
	check("exactly nine bot states exclude human",bots.states.size()==9 and not bots.states.has(0))
	check("buyphase no movement shots or objective holds",host.moves.is_empty() and host.shots.is_empty() and host.rules.interaction_actor==-1)
	check("pistol round no unaffordable purchases",host.rules.actors.all(func(a):return a.weapon=="pistol" and a.credits==800))
	var before: Dictionary=bots.report()
	for bad in [NAN,INF,0.0,-1.0,.3]:bots.step(bad)
	check("invalid bot steps leave state unchanged",bots.report()==before)
	advance(host,bots,22)
	check("live bots actually traverse routes",not host.moves.is_empty() and host.moves.all(func(row):return row.id!=0 and row.target.is_finite()))
	check("no shots through missing line of sight",host.shots.is_empty())
	var planted:=false
	var defused:=false
	for unused in range(180):
		advance(host,bots,.1)
		planted=planted or host.rules.phase=="planted"
		if host.rules.phase=="round_end":
			defused=host.rules.reason.contains("severed")
			break
	check("attack bots plant using actual timed authority",planted and bots.counters.holds>=40)
	check("defender bots complete real sevensecond defuse",defused and host.rules.scores.moon==1,{"phase":host.rules.phase,"reason":host.rules.reason})
	check("objective does not consume human input or life",host.rules.actors[0].health==100 and host.actor_position(0)==host.map.spawn("sun",0,"sun"))
	host.free();bots.free()
	host=HostFixture.new();bots=Bots.new();bots.configure(host)
	for actor in host.rules.actors:actor.credits=5000
	bots.step(.1)
	check("bots buy weapon armor within ownspawn and budget",host.rules.actors.slice(1).all(func(a):return a.weapon=="carbine" and a.armor==50 and a.credits==1100) and host.rules.actors[0].credits==5000)
	host.free();bots.free()
	host=HostFixture.new();bots=Bots.new();bots.configure(host)
	host.rules.actors[1].credits=5000
	host.actor_nodes[1].position=Vector3.ZERO
	bots.step(.1)
	check("bot cannot buy away from ownspawn",host.rules.actors[1].weapon=="pistol" and host.rules.actors[1].credits==5000)
	advance(host,bots,20)
	host.allow_los=true
	host.shots.clear()
	bots.step(.1)
	check("new visual target has reaction delay",host.shots.is_empty())
	advance(host,bots,.4)
	check("visible enemies receive host fire requests",not host.shots.is_empty() and host.shots.all(func(row):return row.id!=0 and host.rules.actors[row.id].team!=host.rules.actors[row.target].team))
	var fired: int=host.shots.size()
	host.allow_los=false
	advance(host,bots,.5)
	check("lost line of sight stops shooting immediately",host.shots.size()==fired)
	host.rules.actors[1].alive=false
	host.moves.clear();host.shots.clear();host.allow_los=true
	advance(host,bots,.5)
	check("dead bots do not move or fire",host.moves.all(func(row):return row.id!=1) and host.shots.all(func(row):return row.id!=1))
	host.free();bots.free()
	host=HostFixture.new();bots=Bots.new();bots.configure(host)
	advance(host,bots,22.5)
	var state: Dictionary=bots.states[2]
	var old_route: Array=state.route.duplicate()
	var old_index: int=state.waypoint
	host.rules.phase="planted";host.rules.site="B";host.rules.time_left=40
	bots.step(.1)
	check("opposite site rotation retraces safe waypoints",state.route.size()>=old_route.size() and state.route[0]==old_route[maxi(0,old_index-1)])
	host.free();bots.free()
	# The fixture supplies deterministic movement/visibility and damage, while
	# actual bots/rules own buys, targeting, deaths, economy and match progression.
	host=HostFixture.new();bots=Bots.new();bots.configure(host);host.allow_los=true
	var generations:=0
	var last_generation: int=host.rules.generation
	for unused in range(16000):
		advance(host,bots,.1)
		if last_generation!=host.rules.generation:generations+=1;last_generation=host.rules.generation
		if host.rules.phase=="match_end":break
	check("autonomous bots finish first13 match through host shots",host.rules.phase=="match_end" and maxi(host.rules.scores.sun,host.rules.scores.moon)==13,{"scores":host.rules.scores,"round":host.rules.round_number,"time":host.rules.elapsed,"shots":host.shots.size()})
	check("bots reset correctly across rounds and side swap",generations>=12 and bots.generation==host.rules.generation and host.rules.attack_team=="moon")
	check("host receives no buy or result phase shot",host.shots.all(func(row):return row.phase in ["live","planted"]))
	check("terminal match causes no further bot requests",_terminal_quiet(host,bots))
	host.free();bots.free()
	finish()

func _terminal_quiet(host,bots) -> bool:
	var moves: int=host.moves.size()
	var shots: int=host.shots.size()
	advance(host,bots,2)
	return moves==host.moves.size() and shots==host.shots.size()

func finish() -> void:
	var passed: bool=checks.all(func(row):return row.passed)
	var report: Dictionary={"task_id":"YUGA-TACTICAL-CASUAL-13","passed":passed,"count":checks.size(),"checks":checks,"sources":{"bots":FileAccess.get_sha256("res://scripts/tactical_bots.gd"),"rules":FileAccess.get_sha256("res://scripts/tactical_round_rules.gd"),"test":FileAccess.get_sha256("res://tests/tactical/bot_cases.gd")},"scope":"Actual bot/rules execution against a transparent synthetic host. Real host collision, firearm cover, nav routes and visual/input acceptance require integrated root/map tests; this is not an online or human skill claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file:=FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			file.store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"count":checks.size(),"failures":checks.filter(func(row):return not row.passed)}))
	quit(0 if passed else 1)
