extends Node3D
## Active native Casual: real local round authority, physical cover, one human + nine bots.
const Rules=preload("res://scripts/tactical_round_rules.gd")
const Map=preload("res://scripts/tactical_map.gd")
const Bots=preload("res://scripts/tactical_bots.gd")
const Player=preload("res://scripts/tactical_player.gd")
const Actor=preload("res://scripts/tactical_actor.gd")
const Effects=preload("res://scripts/tactical_effects.gd")
const UI=preload("res://scripts/tactical_ui.gd")
const TacticalTheme=preload("res://scripts/tactical_theme.gd")
const Weapon=preload("res://scripts/tactical_weapon.gd")
var rules=Rules.new()
var map:Node3D
var bots:Node
var player:CharacterBody3D
var effects:Node3D
var ui:CanvasLayer
var actor_nodes:Dictionary={}
var settings:Dictionary={}
var bot_weapons:Dictionary={}
var feed:Array=[]
var _paused:=false
var _shop_open:=false
var _generation:=-1
var _hint:=""
var _hint_life:=0.0
var _hit_marker:=0.0
var _damage_flash:=0.0
var _ultimate:Array[float]=[]
var _ultimate_age:=0.0
var _relic:Node3D
var _clock:=0.0
var _rng:=RandomNumberGenerator.new()
var _audio_streams:Dictionary={}
var _voices:Array[AudioStreamPlayer3D]=[]
var _voice_index:=0
var _spectate_id:=-1
var _last_objective_beep:=-1
var _ready_complete:=false
var event_receipts:Array[Dictionary]=[]

func _ready()->void:
	_register_input()
	_rng.seed=731013
	settings=TacticalTheme.load_settings()
	map=Map.new();map.name="SangamTacticalMap";add_child(map)
	effects=Effects.new();add_child(effects)
	player=Player.new();player.name="RamaFirstPerson";player.host=self;add_child(player);actor_nodes[0]=player
	for id in range(1,10):
		var actor:=Actor.new();actor.actor_id=id;actor.team="sun" if id<5 else "moon";actor.name="Warden%d"%id;add_child(actor);actor_nodes[id]=actor
	bots=Bots.new();add_child(bots);bots.configure(self)
	ui=UI.new();add_child(ui);ui.configure(self)
	_build_audio();_build_relic();apply_settings(settings)
	rules.start_match();_sync_round();_consume_events()
	_ready_complete=true
	Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	print("YUGA_TACTICAL_READY "+JSON.stringify({"mode":"Casual","authority":"offline bots","first_to":13,"teams":"5v5","map":map.report()}))

func _register_input()->void:
	var keys:={"tac_forward":KEY_W,"tac_back":KEY_S,"tac_left":KEY_A,"tac_right":KEY_D,"tac_walk":KEY_SHIFT,"tac_jump":KEY_SPACE,"tac_reload":KEY_R,"tac_q":KEY_Q,"tac_e":KEY_E,"tac_c":KEY_C,"tac_x":KEY_X,"tac_interact":KEY_F,"tac_shop":KEY_B,"tac_score":KEY_TAB,"tac_pause":KEY_ESCAPE,"tac_guide":KEY_F1}
	for action:String in keys:
		if InputMap.has_action(action):continue
		InputMap.add_action(action);var key:=InputEventKey.new();key.physical_keycode=keys[action];InputMap.action_add_event(action,key)
	for entry in [["tac_fire",MOUSE_BUTTON_LEFT],["tac_ads",MOUSE_BUTTON_RIGHT]]:
		if InputMap.has_action(entry[0]):continue
		InputMap.add_action(entry[0]);var button:=InputEventMouseButton.new();button.button_index=entry[1];InputMap.action_add_event(entry[0],button)

func _unhandled_input(event:InputEvent)->void:
	if not _ready_complete:return
	if event.is_action_pressed("tac_pause"):
		if _paused or ui.has_modal():request_resume()
		else:_pause()
		get_viewport().set_input_as_handled();return
	if event.is_action_pressed("tac_guide"):
		_pause();ui.show_guide();get_viewport().set_input_as_handled();return
	if event.is_action_pressed("tac_shop"):
		if _shop_open:request_resume()
		elif _buy_allowed():_shop_open=true;_pause()
		else:_message("Buy during preparation, inside your spawn.")
		get_viewport().set_input_as_handled();return
	if _paused or ui.has_modal():return
	if event is InputEventMouseMotion and Input.mouse_mode==Input.MOUSE_MODE_CAPTURED:player.aim(event.relative)
	if event.is_action_pressed("tac_reload") and rules.actors[0].alive:
		if player.weapon.reload():play_cue("reload",player.global_position,.7)
	for slot in ["q","e","c","x"]:
		if event.is_action_pressed("tac_"+slot):_ability(slot)
	if not rules.actors[0].alive and event.is_action_pressed("tac_fire"):_cycle_spectator()

func _physics_process(delta:float)->void:
	if not _ready_complete:return
	var stopped:bool=_paused or ui.has_modal()
	player.enabled=not stopped and bool(rules.actors[0].alive) and rules.phase not in ["round_end","match_end"]
	if stopped:return
	_clock+=delta
	rules.tick(delta)
	if rules.generation!=_generation:_sync_round()
	player.enabled=bool(rules.actors[0].alive) and rules.phase not in ["round_end","match_end"]
	map.set_buy_barriers(rules.phase=="buy")
	if player.enabled:
		player.weapon.ads=Input.is_action_pressed("tac_ads") and Input.mouse_mode==Input.MOUSE_MODE_CAPTURED
		player.simulate(delta)
		if Input.is_action_pressed("tac_fire") and rules.phase in ["live","planted"] and _ultimate.is_empty():_fire_player()
		_objective_input(delta)
	else:rules.cancel_interaction(0)
	for id:int in bot_weapons:
		bot_weapons[id].cooldown=maxf(0,bot_weapons[id].cooldown-delta)
		if bot_weapons[id].reload>0:
			bot_weapons[id].reload=maxf(0,bot_weapons[id].reload-delta)
			if bot_weapons[id].reload==0:bot_weapons[id].ammo=int(Weapon.PROFILES[bot_weapons[id].weapon].magazine)
	bots.step(delta)
	for id in range(1,10):
		if not rules.actors[id].alive and actor_nodes[id].alive:actor_nodes[id].die()
		actor_nodes[id].step(delta)
	if not rules.actors[0].alive:
		player.weapon.visible=false;player.collision_layer=0;_ultimate.clear();_spectate(delta)
	_step_ultimate(delta);effects.step(delta);_step_relic(delta);_consume_events()
	_hint_life=maxf(0,_hint_life-delta);_hit_marker=maxf(0,_hit_marker-delta);_damage_flash=maxf(0,_damage_flash-delta)
	for entry in feed:entry.life-=delta
	feed=feed.filter(func(e):return e.life>0)

func _process(_delta:float)->void:
	if not _ready_complete:return
	var view:Dictionary=rules.snapshot()
	var hint:String=_hint if _hint_life>0 else _objective_hint()
	if rules.phase in ["round_end","match_end"]:hint=""
	view.merge({"local_id":0,"ammo":player.weapon.ammo,"reserve":player.weapon.reserve,"reload_progress":player.weapon.reload_progress(),"ads":player.weapon.ads,"callout":map.callout(player.global_position),"hint":hint,"crosshair_spread":3+player.weapon.recoil*7+player.moved,"paused":_paused,"shop_open":_shop_open,"scoreboard_open":Input.is_action_pressed("tac_score"),"hit_marker":_hit_marker>0,"damage_flash":_damage_flash,"weapon_name":Weapon.PROFILES[player.weapon.weapon_id].name,"feed":feed,"ability_hint":"Rama · Solar guardian" if rules.phase not in ["round_end","match_end"] else "","spectating":_spectate_name(),"buy_allowed":_buy_allowed(),"player_position":player.global_position,"actor_positions":_positions(),"sites":map.sites,"map_bounds":map.bounds},true)
	ui.update_view(view)

func _positions()->Dictionary:
	var result:={}
	for id:int in actor_nodes:result[id]=actor_position(id)
	return result

func _sync_round()->void:
	_generation=rules.generation;_ultimate.clear();effects.clear();feed.clear();_spectate_id=-1;_last_objective_beep=-1
	_release_actions()
	for id in range(10):
		var actor:Dictionary=rules.actors[id];var at:Vector3=map.spawn(actor.team,id%5,rules.attack_team)
		if id==0:player.reset_at(at,PI if actor.team==rules.attack_team else 0,actor.weapon)
		else:actor_nodes[id].reset_at(at)
		bot_weapons[id]={"weapon":actor.weapon,"ammo":int(Weapon.PROFILES[actor.weapon].magazine),"cooldown":0.0,"reload":0.0}
	map.set_buy_barriers(true)
	_message("Prepare your loadout · B to buy",4)

func _buy_allowed()->bool:
	return not rules.actors.is_empty() and rules.phase=="buy" and rules.actors[0].alive and map.is_buy_zone(player.global_position,"sun",rules.attack_team)

func request_purchase(item:String)->void:
	if not _buy_allowed():_message("Return to your spawn during preparation.");return
	if rules.purchase(0,item):
		if item=="carbine" or item=="pistol":player.weapon.equip(rules.actors[0].weapon,true)
		play_cue("buy",player.global_position,.6)
	else:_message("Unavailable: check your credits and inventory.")

func _pause()->void:
	_paused=true;player.stop_input();rules.cancel_interaction(0);_release_actions();Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	for voice in _voices:voice.stream_paused=true

func _release_actions()->void:
	for action:StringName in InputMap.get_actions():
		if String(action).begins_with("tac_"):Input.action_release(action)

func request_resume()->void:
	ui.close_modal(false);_paused=false;_shop_open=false
	_release_actions()
	for voice in _voices:voice.stream_paused=false
	Input.mouse_mode=Input.MOUSE_MODE_CAPTURED if rules.phase!="match_end" else Input.MOUSE_MODE_VISIBLE

func request_shop_close()->void:request_resume()
func request_settings()->void:_pause();ui.show_settings()
func request_restart()->void:
	ui.close_modal(false);_paused=false;_shop_open=false;rules.start_match();_sync_round();Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
func request_menu()->void:
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	get_tree().change_scene_to_file("res://scenes/tactical_frontend.tscn")

func apply_settings(values:Dictionary)->void:
	settings=TacticalTheme.sanitize_settings(values)
	if is_instance_valid(player):
		player.sensitivity=float(settings.sensitivity);player.base_fov=float(settings.fov);player.weapon.reduced_motion=bool(settings.reduced_motion)
	AudioServer.set_bus_volume_db(0,linear_to_db(maxf(.0001,float(settings.master_volume))))
	AudioServer.set_bus_mute(0,float(settings.master_volume)<=0)

func _notification(what:int)->void:
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT and _ready_complete:_pause()

func _exit_tree()->void:
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	for voice in _voices:
		if is_instance_valid(voice):voice.stop();voice.stream=null
	_audio_streams.clear()

func actor_position(id:int)->Vector3:
	return actor_nodes[id].global_position if actor_nodes.has(id) else Vector3.ZERO

func bot_move(id:int,target:Vector3,delta:float)->void:
	if id<=0 or id>=10 or not rules.actors[id].alive:return
	actor_nodes[id].move_towards(target,delta)

func line_of_sight(from_id:int,to_id:int)->bool:
	if not actor_nodes.has(from_id) or not actor_nodes.has(to_id):return false
	var from:=actor_position(from_id)+Vector3(0,1.45,0);var to:=actor_position(to_id)+Vector3(0,1.20,0)
	if effects.obscured(from,to):return false
	return get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from,to,1)).is_empty()

func bot_fire(id:int,target_id:int)->void:
	if id<=0 or id>=10 or target_id<0 or target_id>=10 or rules.phase not in ["live","planted"]:return
	if not rules.actors[id].alive or not rules.actors[target_id].alive or rules.actors[id].team==rules.actors[target_id].team:return
	if not line_of_sight(id,target_id):return
	var data:Dictionary=bot_weapons[id]
	if data.weapon!=rules.actors[id].weapon:
		data.weapon=rules.actors[id].weapon;data.ammo=int(Weapon.PROFILES[data.weapon].magazine)
	if data.cooldown>0 or data.reload>0:return
	if data.ammo<=0:data.reload=float(Weapon.PROFILES[data.weapon].reload);return
	data.ammo-=1;data.cooldown=.32 if data.weapon=="carbine" else .62
	var from:=actor_position(id)+Vector3(0,1.40,0);var to:=actor_position(target_id)+Vector3(0,1.15,0)
	var distance:=from.distance_to(to);var error:=.12+distance*.018
	to+=Vector3(_rng.randf_range(-error,error),_rng.randf_range(-.25,.25),_rng.randf_range(-error,error))
	actor_nodes[id].face(to);actor_nodes[id].shot_time=.12
	_fire_ray(id,from,(to-from).normalized(),float(Weapon.PROFILES[data.weapon].damage),false)
	play_cue(data.weapon,from,.35)

func _fire_player()->void:
	if not player.weapon.fire():
		if player.weapon.ammo==0 and player.weapon.reload_remaining==0:_message("Magazine empty · R to reload",1)
		return
	var camera:Camera3D=player.camera
	var spread:float=Weapon.PROFILES[player.weapon.weapon_id].spread
	spread*=.24 if player.weapon.ads else 1.0
	spread*=1.0+player.moved*.22
	var direction:=(-camera.global_basis.z+camera.global_basis.x*_rng.randf_range(-spread,spread)+camera.global_basis.y*_rng.randf_range(-spread,spread)).normalized()
	_fire_ray(0,camera.global_position,direction,float(Weapon.PROFILES[player.weapon.weapon_id].damage),false)
	if not player.weapon.reduced_motion:player.pitch=minf(1.42,player.pitch+.006);player.camera.rotation.x=player.pitch
	play_cue(player.weapon.weapon_id,player.global_position,.7)

func _fire_ray(id:int,origin:Vector3,direction:Vector3,damage:float,solar:bool)->void:
	var excluded:Array[RID]=[actor_nodes[id].get_rid()]
	var from:=origin;var final:=origin+direction*110
	for count in (3 if solar else 1):
		var hit:=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from,origin+direction*110,1|2,excluded))
		if hit.is_empty():break
		final=hit.position
		var collider:Node=hit.collider
		if collider.has_meta("ward_health"):
			collider.set_meta("ward_health",float(collider.get_meta("ward_health"))-damage);break
		var target:=int(collider.get_meta("actor_id",-1))
		if target<0:break
		var multiplier:=3.0 if hit.position.y-actor_position(target).y>1.45 else 1.0
		if rules.damage(target,damage*multiplier,id) and id==0:_hit_marker=.18;play_cue("hit",player.global_position,.45)
		if not solar:break
		excluded.append(collider.get_rid());from=hit.position+direction*.02
	var muzzle:=origin+direction*.5
	if id==0:muzzle=player.camera.global_transform*Vector3(.22,-.18,-.55)
	effects.trace(muzzle,final,solar,rules.actors[id].team!="sun")

func _ability(slot:String)->void:
	if rules.phase not in ["live","planted"] or not rules.actors[0].alive or not _ultimate.is_empty():return
	if slot=="e" and not player.is_on_floor():_message("Measured step needs solid ground.");return
	if slot=="c":
		var shape:=BoxShape3D.new();shape.size=Vector3(6,2.5,.35)
		var query:=PhysicsShapeQueryParameters3D.new();query.shape=shape;query.collision_mask=1
		query.transform=Transform3D(Basis(Vector3.UP,player.yaw),player.global_position-player.global_basis.z*3.8+Vector3(0,1.4,0))
		if not get_world_3d().direct_space_state.intersect_shape(query,1).is_empty():_message("Ward needs a clear placement ahead.");return
		if not get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(player.camera.global_position,query.transform.origin,1)).is_empty():_message("Ward cannot pass through cover.");return
	if not rules.use_ability(0,slot):_message("Utility unavailable · buy charges or earn your ultimate.");return
	rules.cancel_interaction(0)
	var origin:Vector3=player.camera.global_position;var direction:Vector3=-player.camera.global_basis.z
	var hit:=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(origin,origin+direction*18,1))
	var at:Vector3=hit.position-direction*.4 if not hit.is_empty() else origin+direction*14
	at.y=.1
	match slot:
		"q":effects.throw_veil(player.camera.global_position+direction*.5,at);play_cue("veil",at,.65)
		"e":player.dash();effects.burst(player.global_position);play_cue("dash",player.global_position,.6)
		"c":
			var forward:Vector3=-player.global_basis.z
			at=player.global_position+forward*3.8;at.y=.02
			effects.ward(at,player.yaw);play_cue("ward",at,.65)
		"x":_ultimate=[.55,.79,1.03];_ultimate_age=0;_message("DAWN VOLLEY · keep your aim on target",1.1);play_cue("ultimate",player.global_position,.8)

func _step_ultimate(delta:float)->void:
	if _ultimate.is_empty() or not rules.actors[0].alive or rules.phase not in ["live","planted"]:_ultimate.clear();return
	_ultimate_age+=delta
	while not _ultimate.is_empty() and _ultimate_age>=_ultimate[0]:
		_ultimate.pop_front();_fire_ray(0,player.camera.global_position,-player.camera.global_basis.z,95,true);player.weapon.recoil=1.5;play_cue("solar",player.global_position,.8)

func _objective_input(delta:float)->void:
	if not Input.is_action_pressed("tac_interact") or rules.phase not in ["live","planted"] or Input.is_action_pressed("tac_fire") or player.weapon.reload_remaining>0 or player.moved>.5 or not _ultimate.is_empty():rules.cancel_interaction(0);return
	var found:=false
	for site_name:String in map.sites:
		var at:Vector3=map.sites[site_name]
		if Vector2(player.global_position.x-at.x,player.global_position.z-at.z).length()<=float(map.site_radius) and absf(player.global_position.y-at.y)<1.5 and player.is_on_floor():
			if rules.phase=="planted" and site_name!=rules.site:continue
			rules.interact(0,site_name,delta);found=true;break
	if not found:rules.cancel_interaction(0)

func _objective_hint()->String:
	if rules.actors.is_empty():return ""
	if rules.phase in ["round_end","match_end"]:return ""
	if not rules.actors[0].alive:return "One life per round · LMB to change teammate"
	if rules.phase=="buy":return "B  Buy equipment · prepare before barriers fall"
	for site_name:String in map.sites:
		if player.global_position.distance_to(map.sites[site_name])<float(map.site_radius)+.1:
			if rules.phase=="live" and rules.attack_team=="sun":return "Hold F · attune the Astra at site "+site_name
			if rules.phase=="planted" and rules.attack_team!="sun" and rules.site==site_name:return "Hold F · sever the Astra"
	if rules.phase=="planted":return "Defend the attuned Astra · site "+rules.site if rules.attack_team=="sun" else "Retake site "+rules.site+" · hold F to sever the Astra"
	return "Attune at A or B · clear the approach" if rules.attack_team=="sun" else "Defend A and B · prevent the attunement"

func _consume_events()->void:
	for event:Dictionary in rules.drain_events():
		event_receipts.append(event.duplicate(true))
		if event_receipts.size()>500:event_receipts.pop_front()
		var kind:String=event.get("kind","")
		if kind=="damage" and int(event.get("target_id",event.get("target",-1)))==0:_damage_flash=.3
		if kind=="elimination":
			var attacker:=int(event.get("attacker_id",event.get("attacker",-1)));var target:=int(event.get("target_id",event.get("target",-1)))
			if attacker>=0 and target>=0:
				feed.push_front({"attacker":rules.actors[attacker].name,"target":rules.actors[target].name,"weapon":"SURYA" if rules.actors[attacker].weapon=="carbine" else "ARKA","life":6.0})
		if kind in ["plant","defuse","round_end","match_end","buy_end"]:play_cue("objective",player.global_position,.7)
		if kind=="buy_end":_hint_life=0
		if kind=="match_end":Input.mouse_mode=Input.MOUSE_MODE_VISIBLE

func _message(text:String,duration:=2.5)->void:_hint=text;_hint_life=duration

func _cycle_spectator()->void:
	for offset in range(1,6):
		var next:=posmod(_spectate_id+offset,5)
		if next>0 and rules.actors[next].alive:_spectate_id=next;return
	_spectate_id=-1

func _spectate(delta:float)->void:
	if _spectate_id<1 or not rules.actors[_spectate_id].alive:_cycle_spectator()
	if _spectate_id>0:
		var actor:Node3D=actor_nodes[_spectate_id]
		var target:=actor.global_position+Vector3(0,2.5,0)-actor.global_basis.z*3.5
		var obstruction:=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(actor.global_position+Vector3(0,1.6,0),target,1))
		if not obstruction.is_empty():target=obstruction.position+obstruction.normal*.25
		player.camera.global_position=player.camera.global_position.lerp(target,minf(1,delta*7))
		player.camera.look_at(actor.global_position+Vector3(0,1.35,0)+actor.global_basis.z*4,Vector3.UP)

func _spectate_name()->String:
	return str(rules.actors[_spectate_id].name) if _spectate_id>0 and not rules.actors[0].alive else ""

func _build_relic()->void:
	_relic=Node3D.new();add_child(_relic)
	var crystal:=PrismMesh.new();crystal.size=Vector3(.55,1.4,.55)
	effects.mesh(_relic,crystal,effects.mat("relic",Color("ffe1a0"),2),Vector3(0,1.2,0))
	for i in 3:
		var torus:=TorusMesh.new();torus.inner_radius=.62+i*.12;torus.outer_radius=.66+i*.12;torus.rings=32;torus.ring_segments=8
		var ring:MeshInstance3D=effects.mesh(_relic,torus,effects.mat("relic_gold",Color("cca661"),.8),Vector3(0,1.2,0));ring.rotation=Vector3(i*.7,0,i*.8)
	_relic.visible=false

func _step_relic(delta:float)->void:
	_relic.visible=rules.phase=="planted"
	if not _relic.visible:return
	_relic.position=map.sites.get(rules.site,Vector3.ZERO);_relic.rotation.y+=delta*.8
	var beat:=int(rules.time_left*(2 if rules.time_left<10 else 1))
	if beat!=_last_objective_beep:_last_objective_beep=beat;play_cue("beep",_relic.global_position,.6)

func _build_audio()->void:
	for cue in ["pistol","carbine","reload","step","buy","hit","veil","dash","ward","ultimate","solar","objective","beep"]:
		var path:String="res://assets/tactical/audio/"+cue+".wav"
		if ResourceLoader.exists(path):_audio_streams[cue]=load(path)
	for i in 12:
		var voice:=AudioStreamPlayer3D.new();voice.max_distance=65;voice.unit_size=6;voice.max_db=-5;add_child(voice);_voices.append(voice)

func play_cue(cue:String,at:Vector3,gain:=.5)->void:
	if not _audio_streams.has(cue) or _voices.is_empty():return
	var voice:=_voices[_voice_index];_voice_index=(_voice_index+1)%_voices.size()
	voice.stop();voice.stream=_audio_streams[cue];voice.global_position=at;voice.volume_db=linear_to_db(maxf(.001,gain))-10;voice.play()

func report()->Dictionary:
	return {"rules":rules.snapshot(),"map":map.report(),"actors":actor_nodes.size(),"position":str(player.global_position),"weapon":player.weapon.weapon_id,"ammo":player.weapon.ammo,"paused":_paused,"events":event_receipts.size(),"effects":effects.effects.size(),"audio_streams":_audio_streams.size()}
