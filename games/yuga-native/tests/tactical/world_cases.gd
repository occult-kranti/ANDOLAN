extends SceneTree
var world:Node3D
var passed:=0
var failed:Array[String]=[]
func _initialize()->void:call_deferred("run")
func check(value:bool,label:String)->void:
	if value:passed+=1
	else:failed.append(label);push_error(label)
func run()->void:
	world=load("res://scenes/tactical_world.tscn").instantiate();root.add_child(world);current_scene=world
	await process_frame
	world.set_physics_process(false);world.set_process(false)
	check(world._ready_complete,"World ready")
	check(world.actor_nodes.size()==10,"Physical 5v5 roster")
	check(world.rules.configured,"Valid round contract")
	check(world.map.report().ready,"Map built")
	check(world._audio_streams.size()==13,"All original cues load")
	check(world.player.camera.current,"First person camera")
	check(world.player.weapon.ammo==12,"Pistol start")
	var before:int=world.rules.actors[0].credits
	world.request_purchase("q")
	check(world.rules.actors[0].credits==before-200,"Spawn purchase spends real credits")
	world.player.position=Vector3(-29,0,8)
	before=world.rules.actors[0].credits;world.request_purchase("q")
	check(world.rules.actors[0].credits==before,"Site purchase rejected")
	while world.rules.phase=="buy":world.rules.tick(.1)
	world.map.set_buy_barriers(false)
	for id in range(1,10):world.actor_nodes[id].position=Vector3(38+id*.5,0,-58)
	world.player.reset_at(Vector3(-29,0,-53),PI,"pistol")
	world.actor_nodes[5].position=Vector3(-29,0,-48)
	await physics_frame;await physics_frame
	check(world.line_of_sight(0,5),"Open physical line of sight")
	before=world.rules.actors[5].health
	world._fire_ray(0,Vector3(-29,1.1,-53),Vector3.BACK,28,false)
	check(world.rules.actors[5].health==before-28,"Bullet hits physical actor")
	world.actor_nodes[5].position=Vector3(-29,0,-40);world.map.set_buy_barriers(true)
	await physics_frame;await physics_frame
	before=world.rules.actors[5].health
	world._fire_ray(0,Vector3(-29,1.1,-53),Vector3.BACK,28,false)
	check(world.rules.actors[5].health==before,"Barrier blocks physical bullet")
	check(not world.line_of_sight(0,5),"Barrier blocks bot sight")
	world.map.set_buy_barriers(false);world.effects.veil(Vector3(-29,0,-47))
	await physics_frame;await physics_frame
	check(not world.line_of_sight(0,5),"Solar veil blocks bot sight")
	world.effects.clear()
	check(world.player.weapon.fire(),"Weapon consumes a shot")
	check(world.player.weapon.ammo==11,"Ammo truthful")
	check(not world.player.weapon.fire(),"Fire-rate lock")
	check(world.player.weapon.reload(),"Reload begins")
	var remaining:float=world.player.weapon.reload_remaining
	world._pause();world._physics_process(.1)
	check(world.player.weapon.reload_remaining==remaining,"Pause freezes reload")
	world.request_resume();world.player.weapon.step(2)
	check(world.player.weapon.ammo==12 and world.player.weapon.reserve==35,"Reload transfers finite ammunition")
	world.player.weapon.fire();world.player.weapon.reload()
	for i in 120:world.player.weapon.step(1.0/60.0)
	check(absf(world.player.weapon.model.position.y)<.001,"Frame-sampled reload returns weapon to origin")
	world.rules.damage(0,200,5)
	world._physics_process(.1)
	check(not world.rules.actors[0].alive and world.player.collision_layer==0,"Death removes living collider")
	check(not world.player.weapon.visible,"Death hides local weapon")
	for i in 60:world.rules.tick(.1)
	check(not world.rules.actors[0].alive,"No within-round automatic resurrection")
	world.request_restart()
	check(world.rules.phase=="buy" and world.rules.actors[0].alive and world.player.collision_layer==2,"Restart restores all round state")
	check(world.effects.effects.is_empty(),"Restart clears transient cover/veil")
	check(world.player.weapon.ammo==12 and world.rules.actors[0].credits==800,"Fresh match resets inventory/economy")
	world.queue_free();await process_frame;await process_frame;OS.delay_msec(100)
	print(JSON.stringify({"suite":"tactical_world","passed":passed,"failed":failed,"scope":"Actual native headless scene and physical ray tests; no visual/human/hardware claim"}))
	quit(0 if failed.is_empty() else 1)
