extends SceneTree
const Rules = preload("res://scripts/tactical_round_rules.gd")
var checks: Array[Dictionary]=[]

func check(label: String, condition: bool, detail: Dictionary={}) -> void:
	checks.append({"case":label,"passed":condition,"detail":detail})

func fresh():
	var value=Rules.new()
	value.start_match()
	return value

func advance(value, seconds: float) -> void:
	var remaining:=seconds
	while remaining>0.000001:
		var delta:=minf(.1,remaining)
		value.tick(delta)
		remaining-=delta

func hold(value,id: int,site: String,seconds: float) -> void:
	var remaining:=seconds
	while remaining>0.000001:
		var delta:=minf(.1,remaining)
		value.tick(delta)
		value.interact(id,site,delta)
		remaining-=delta

func win_by_elimination(value,team: String) -> void:
	var killer:=0 if team=="sun" else 5
	for id in range(10):
		if value.actors[id].team!=team and value.actors[id].alive: value.damage(id,1000,killer)

func _initialize() -> void:
	var r=fresh()
	check("valid source configuration",r.configured)
	if not r.configured: finish();return
	check("ten actors one human balanced teams",r.actors.size()==10 and r.actors[0].id==0 and r.actors.filter(func(a):return a.team=="sun").size()==5)
	check("starts buy first round800credits one free dash",r.phase=="buy" and r.round_number==1 and r.actors.all(func(a):return a.credits==800 and a.health==100 and a.charges.e==1 and a.charges.q==0))
	check("buy disables damage and utility",not r.damage(5,20,0) and not r.use_ability(0,"e"))
	check("expensive weapon rejected without debit",not r.purchase(0,"carbine") and r.actors[0].credits==800)
	check("buy smoke twice exact cap and debit",r.purchase(0,"q") and r.purchase(0,"q") and not r.purchase(0,"q") and r.actors[0].credits==400 and r.actors[0].charges.q==2)
	check("free starting dash cannot overbuy",not r.purchase(0,"e") and r.actors[0].charges.e==1)
	check("wall cost300 and unknown item rejected",r.purchase(0,"c") and r.actors[0].credits==100 and not r.purchase(0,"x") and not r.purchase(-1,"q"))
	var initial:=r.snapshot()
	initial.actors[0].credits=999999
	initial.catalog.q.cost=-10
	initial.scores.sun=12
	check("snapshot deep copy cannot rewrite authority",r.actors[0].credits==100 and r.scores.sun==0 and r.SHOP.q.cost==200)
	var before: float=r.time_left
	for bad in [NAN,INF,-1.0,0.0,.26]:r.tick(bad)
	check("invalid clock steps do not advance",r.time_left==before)
	advance(r,19.9)
	check("buy barrier phase lasts full20seconds",r.phase=="buy")
	advance(r,.1)
	check("live follows actual buy deadline",r.phase=="live" and is_equal_approx(r.time_left,100))
	check("purchase rejected after buy",not r.purchase(0,"q"))
	check("consume utility once per owned charge",r.use_ability(0,"e") and not r.use_ability(0,"e") and r.use_ability(0,"q") and r.actors[0].charges.q==1)
	check("ultimate cannot cast below6",not r.use_ability(0,"x"))
	r.actors[0].ult=6
	check("ultimate spends all6 without passive refill",r.use_ability(0,"x") and r.actors[0].ult==0)
	advance(r,1)
	check("time does not refill ultimate",r.actors[0].ult==0)
	check("friendly self invalid damage rejected",not r.damage(0,20,0) and not r.damage(1,20,0) and not r.damage(5,NAN,0) and not r.damage(5,-1,0) and not r.damage(99,20,0))
	r.actors[5].armor=50
	check("armor absorbs first50",r.damage(5,40,0) and r.actors[5].health==100 and r.actors[5].armor==10)
	check("damage spills exactly through armor",r.damage(5,25,0) and r.actors[5].health==85 and r.actors[5].armor==0)
	check("kill increments score credit ult once",r.damage(5,100,0) and r.actors[0].kills==1 and r.actors[0].credits==300 and r.actors[0].ult==1 and r.actors[5].deaths==1)
	check("duplicate kill and dead attacker rejected",not r.damage(5,100,0) and not r.damage(0,100,5) and r.actors[0].kills==1)
	advance(r,3)
	check("one life no timed midround respawn",not r.actors[5].alive)
	check("defender cannot plant unknownsite rejected",not r.interact(6,"A",.1) and not r.interact(0,"Z",.1))
	r.tick(.1)
	check("first valid hold accepted",r.interact(0,"A",.1))
	var progress: float=r.interaction_progress
	for unused in range(20):r.interact(0,"A",.1)
	check("same tick repeated hold cannot accelerate",r.interaction_progress==progress)
	check("one interactor prevents stolen progress",not r.interact(1,"A",.1) and r.interaction_actor==0)
	r.cancel_interaction(0)
	check("explicit release clears hold",r.interaction_actor==-1 and r.interaction_progress==0)
	hold(r,0,"A",1)
	r.tick(.1);r.tick(.1)
	check("missing input tick invalidates hold",r.interaction_actor==-1)
	hold(r,0,"A",1)
	r.tick(.1);r.interact(0,"B",.1)
	check("changing site restarts progress",r.interaction_progress<.03)
	r.cancel_interaction(0)
	hold(r,0,"A",3.9)
	check("plant requires all4seconds",r.phase=="live")
	hold(r,0,"A",.1)
	check("plant creates40second armed objective and ult",r.phase=="planted" and r.site=="A" and r.time_left==40 and r.actors[0].ult==2)
	for id in range(5):r.damage(id,1000,6)
	check("all attacker deaths do not end planted round",r.phase=="planted" and r.scores.moon==0)
	check("attacker and wrongsite cannot defuse",not r.interact(0,"A",.1) and not r.interact(6,"B",.1))
	hold(r,6,"A",6.9)
	check("defuse requires all7seconds",r.phase=="planted")
	hold(r,6,"A",.1)
	check("defuse awards defending team round",r.phase=="round_end" and r.winner=="moon" and r.scores.moon==1 and r.reason.contains("severed"))
	check("round economy win3000 loss1900 plus prior kills",r.actors[0].credits==2200 and r.actors[6].credits==4800)
	var old_generation: int=r.generation
	advance(r,5)
	check("next round resets dead equipment and health",r.phase=="buy" and r.round_number==2 and r.generation==old_generation+1 and r.actors[0].alive and r.actors[0].weapon=="pistol" and r.actors[0].armor==0 and r.actors[0].charges=={"q":0,"e":1,"c":0})
	r.actors[6].credits=9000
	check("rich actor buys carbine armor exact prices",r.purchase(6,"carbine") and r.purchase(6,"armor") and r.actors[6].credits==5100 and r.actors[6].armor==50)
	check("duplicate equipment purchase rejected",not r.purchase(6,"carbine") and not r.purchase(6,"armor") and not r.purchase(6,"pistol"))
	advance(r,20)
	win_by_elimination(r,"moon")
	check("unplanted attacker elimination wins immediately",r.phase=="round_end" and r.winner=="moon")
	advance(r,5)
	check("survivor retains purchased equipment",r.actors[6].weapon=="carbine" and r.actors[6].armor==50)
	r=fresh();advance(r,20);advance(r,99.9)
	r.interact(0,"A",.1);r.tick(.1)
	check("live deadline wins before incomplete plant",r.phase=="round_end" and r.winner=="moon" and r.interaction_actor==-1 and not r.interact(0,"A",.1))
	r=fresh();advance(r,20);hold(r,0,"B",4);advance(r,40)
	check("armed deadline wins attackers",r.phase=="round_end" and r.winner=="sun" and r.reason.contains("detonated"))
	r=fresh();advance(r,20);hold(r,0,"A",2);r.damage(0,1000,5)
	check("death cancels active plant",r.interaction_actor==-1 and r.phase=="live")
	r=fresh();advance(r,20);hold(r,0,"A",4);win_by_elimination(r,"sun")
	check("defender elimination ends planted round",r.phase=="round_end" and r.winner=="sun")
	r=fresh()
	for number in range(1,14):
		advance(r,20)
		win_by_elimination(r,"sun")
		if number==12:
			check("no early swap during12th result",r.attack_team=="sun" and r.round_number==12)
		if number<13:
			advance(r,5)
			if number==12:check("roles swap exactly for13thround",r.attack_team=="moon" and r.round_number==13)
	check("first13 wins match no overtime",r.phase=="match_end" and r.scores=={"sun":13,"moon":0} and r.winner=="sun")
	var final_snapshot: Dictionary=r.snapshot()
	advance(r,100)
	check("match end is terminal",r.snapshot()==final_snapshot and not r.damage(5,10,0) and not r.purchase(0,"q") and not r.use_ability(0,"e"))
	check("credits and ultimate capped",r.actors.all(func(a):return a.credits<=9000 and a.ult<=6) and r.actors[0].credits==9000 and r.actors[0].ult==6)
	var drained: Array=r.drain_events()
	var ordered:=true
	for index in range(1,drained.size()):ordered=ordered and drained[index].seq>drained[index-1].seq
	check("events drain once and ordered",ordered and not drained.is_empty() and r.drain_events().is_empty())
	var final_generation: int=r.generation
	r.start_match()
	check("restart fresh generation resets match",r.generation>final_generation and r.phase=="buy" and r.scores=={"sun":0,"moon":0} and r.actors[0].kills==0 and r.actors[0].credits==800)
	finish()

func finish() -> void:
	var passed: bool=checks.all(func(row):return row.passed)
	var report: Dictionary={"task_id":"YUGA-TACTICAL-CASUAL-13","passed":passed,"count":checks.size(),"checks":checks,"sources":{"rules":FileAccess.get_sha256("res://scripts/tactical_round_rules.gd"),"config":FileAccess.get_sha256("res://assets/tactical/rules.json"),"test":FileAccess.get_sha256("res://tests/tactical/round_rules_cases.gd")},"scope":"Actual offline authority and adverse temporal/economy/lifecycle cases; no renderer, real map collision, OS input, online or human balance claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file:=FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			file.store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"count":checks.size(),"failures":checks.filter(func(row):return not row.passed)}))
	quit(0 if passed else 1)
