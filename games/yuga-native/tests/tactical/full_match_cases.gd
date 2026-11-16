extends SceneTree
## One natural actual-scene match. No actor positions, damage, scores or wins injected.
class Observer extends Node:
	var owner_tree: SceneTree
	func _physics_process(delta: float) -> void:
		owner_tree.observe(delta)

var world: Node3D
var observer: Observer
var finishing:=false
var last_seq:=0
var elapsed:=0.0
var sampled_frames:=0
var max_step:=0.0
var source_before: Dictionary={}
var counts: Dictionary={}
var round_results: Array[Dictionary]=[]
var violations: Array[String]=[]
var previous_generation:=-1
var dead_ids: Array[int]=[]
var max_travel:=0.0
var origins: Dictionary={}

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	for path in ["scripts/tactical_world.gd","scripts/tactical_player.gd","scripts/tactical_actor.gd","scripts/tactical_weapon.gd","scripts/tactical_effects.gd","scripts/tactical_map.gd","scripts/tactical_bots.gd","scripts/tactical_round_rules.gd","assets/tactical/rules.json","assets/tactical/map.json","tests/tactical/full_match_cases.gd"]:
		source_before[path]=FileAccess.get_sha256("res://"+path)
	root.size=Vector2i(1280,720)
	Engine.time_scale=10
	Engine.max_physics_steps_per_frame=32
	world=load("res://scenes/tactical_world.tscn").instantiate()
	root.add_child(world)
	await process_frame
	observer=Observer.new()
	observer.owner_tree=self
	observer.process_physics_priority=1000
	root.add_child(observer)
	for id in world.actor_nodes:origins[id]=world.actor_position(id)
	print("TACTICAL_NATURAL_MATCH_STARTED")

func observe(delta: float) -> void:
	if finishing:return
	sampled_frames+=1
	max_step=maxf(max_step,delta)
	elapsed=float(world.rules.elapsed)
	if world.rules.generation!=previous_generation:
		dead_ids.clear()
		previous_generation=world.rules.generation
	for actor in world.rules.actors:
		var id: int=actor.id
		if not actor.alive and id not in dead_ids:dead_ids.append(id)
		elif actor.alive and id in dead_ids:_violation("Actor resurrected within generation "+str(id))
		var position: Vector3=world.actor_position(id)
		if not position.is_finite():_violation("Nonfinite actor position")
		if id>0:max_travel=maxf(max_travel,position.distance_to(origins[id]))
	for event in world.event_receipts:
		if int(event.seq)<=last_seq:continue
		last_seq=event.seq
		var kind: String=event.kind
		counts[kind]=int(counts.get(kind,0))+1
		if kind in ["damage","elimination"] and event.phase not in ["live","planted"]:_violation("Combat outside live phase")
		if kind=="round_end":round_results.append({"round":event.round_number,"winner":event.winner,"reason":event.reason,"time_s":event.time_s,"scores":event.scores})
	if sampled_frames%1200==0:print("TACTICAL_NATURAL_MATCH_PROGRESS "+JSON.stringify({"elapsed":elapsed,"scores":world.rules.scores,"round":world.rules.round_number,"phase":world.rules.phase}))
	if world.rules.phase=="match_end" or elapsed>=2000 or sampled_frames>=15000:
		finishing=true
		call_deferred("finish")

func _violation(message: String) -> void:
	if message not in violations:violations.append(message)

func finish() -> void:
	var final: Dictionary=world.rules.snapshot()
	var unchanged:=true
	for path in source_before:unchanged=unchanged and source_before[path]==FileAccess.get_sha256("res://"+path)
	var checks: Array[Dictionary]=[
		{"case":"actual scene natural first13 match completes","passed":final.phase=="match_end" and maxi(final.scores.sun,final.scores.moon)==13},
		{"case":"real bots travel and damage through host physics","passed":max_travel>20 and int(counts.get("damage",0))>0 and int(counts.get("elimination",0))>0},
		{"case":"actual round event count matches final score","passed":round_results.size()==int(final.scores.sun)+int(final.scores.moon)},
		{"case":"halftime and one life remain correct","passed":int(counts.get("side_swap",0))==1 and violations.is_empty()},
		{"case":"bounded simulation step remains eligible","passed":max_step<=.25},
		{"case":"reviewed sources unchanged","passed":unchanged}
	]
	var passed: bool=checks.all(func(row):return row.passed)
	var report: Dictionary={"task_id":"YUGA-TACTICAL-CASUAL-13","passed":passed,"count":checks.size(),"checks":checks,"elapsed_simulation_s":elapsed,"physics_samples":sampled_frames,"maximum_step_s":max_step,"maximum_bot_displacement_m":max_travel,"event_counts":counts,"round_results":round_results,"violations":violations,"final":final,"sources":source_before,"scope":"One actual instantiated world match with idle human and nine local bots, real movement/collision/rays/weapon/effects and unchanged authority. Engine time scale10 speeds deterministic execution; no forced score/death/win/position, no OSinput/render/humanbalance or hardwareperformance claim."}
	observer.set_physics_process(false)
	world.set_physics_process(false)
	for node in world.find_children("*","AudioStreamPlayer3D",true,false):node.stop()
	world.queue_free()
	await process_frame
	await process_frame
	OS.delay_msec(100)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file:=FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			file.store_string(JSON.stringify(report,"  ")+"\n")
	print("TACTICAL_NATURAL_MATCH_RESULT "+JSON.stringify({"passed":passed,"checks":checks,"scores":final.scores,"elapsed":elapsed,"events":counts}))
	quit(0 if passed else 1)
