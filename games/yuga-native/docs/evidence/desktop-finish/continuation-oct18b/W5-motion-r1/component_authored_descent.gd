extends "/workspace/ANDOLAN/games/yuga-native/tests/graphics_g2_support_cases.gd"
## Prescribed-root imported-rig component. Every declared timestep is evaluated.
const OWNER := "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W5-motion-r1/"

func signature(value: Variant) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256);context.update(var_to_bytes(value))
	return context.finish().hex_encode()

func is_leg(name_:String) -> bool:
	return name_.begins_with("upperleg") or name_.begins_with("lowerleg") or name_.begins_with("foot") or name_.begins_with("toe")

func record(motion:Node, actor:Node3D, selected:Array, plane_y:float, tick:int, dt:float) -> Dictionary:
	var nonleg:Array=[];var legs:Dictionary={};var feet:Dictionary={}
	for index in motion.rig.get_bone_count():
		var name_:String=motion.rig.get_bone_name(index)
		if is_leg(name_):
			var q:Quaternion=motion.rig.get_bone_pose_rotation(index)
			var g:Quaternion=motion.last_globals[index].basis.get_rotation_quaternion()
			legs[name_]={"local":[q.x,q.y,q.z,q.w],"global":[g.x,g.y,g.z,g.w]}
		else:nonleg.append([motion.rig.get_bone_pose(index),motion.last_globals[index]])
	for side in ["L","R"]:
		var v:Vector3=motion.rig.global_transform*motion.last_globals[motion.rig.find_bone("foot."+side)].origin
		feet[side]={"world":vec(v),"relative_root":vec(v-actor.global_position)}
	var row:={"tick":tick,"time_s":(tick+1)*dt,"root":vec(actor.position),"grounded":motion.grounded,"velocity":vec(motion.world_velocity),"locomotion":motion.locomotion,"clocks":[motion.phase,motion.locomotion_age,motion.transition_age,motion.transition_duration,motion.action_elapsed,motion.release_count,motion.cancel_count],"nonleg_sha256":signature(nonleg),"legs":legs,"feet":feet,"locks":motion.foot_locks.duplicate(),"targets":{"L":vec(motion.foot_targets.L),"R":vec(motion.foot_targets.R)}}
	if actor.position.y-plane_y<.25:
		var skin:=measure(motion,selected,plane_y);skin.erase("positions");row["skin"]=skin
	return row

func trial(path:String, spec:Dictionary, hz:int) -> Array:
	var support:=StaticBody3D.new();support.collision_layer=1
	var shape_node:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(4,.2,4);shape_node.shape=box
	support.add_child(shape_node);root.add_child(support);support.position.y=spec.support-.1
	var actor:=CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor)
	var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();actor.add_child(model)
	var motion=load(path).new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	var selected:=soles(model,motion.rig)
	var dt:=1.0/hz;var base_y:float=spec.support+.0008394047617912292
	actor.position.y=base_y
	var state:={"grounded":true,"floor_y":base_y,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"ground"}
	await physics_frame
	for tick in int(hz*.3):motion.update_motion(dt,state);motion.evaluate_pose()
	var rows:Array=[record(motion,actor,selected,spec.support,-1,dt)]
	actor.position.y=base_y+spec.height
	var speed:float=spec.speed;var airborne:=true;var landed_age:=0.0
	for tick in int(hz*1.6):
		if airborne:
			speed-=float(spec.gravity)*dt
			var next_y:float=actor.position.y+speed*dt
			airborne=next_y>base_y
			actor.position.y=maxf(base_y,next_y)
		state.grounded=not airborne
		state.floor_y=actor.position.y
		state.velocity=Vector3(0,speed if airborne else 0,0);state.local_velocity=state.velocity
		motion.update_motion(dt,state);motion.evaluate_pose()
		rows.append(record(motion,actor,selected,spec.support,tick,dt))
		if not airborne:
			landed_age+=dt
			if landed_age>=.3:break
	actor.free();support.free();await process_frame
	return rows

func run() -> void:
	var specs:=[{"name":"jump","support":0.0,"height":0.0,"speed":7.2,"gravity":18.0},{"name":"drop","support":0.0,"height":1.5,"speed":-2.0,"gravity":18.0},{"name":"fast_drop","support":0.0,"height":1.5,"speed":-20.0,"gravity":18.0},{"name":"low_drop","support":0.0,"height":.12,"speed":-1.0,"gravity":18.0},{"name":"slow_low","support":0.0,"height":.03,"speed":-.1,"gravity":0.0}]
	var cases_rows:Array=[]
	for spec in specs:
		for hz in [30,60,120]:
			var a:Array=await trial(OWNER+"canonical-rama_motion.gd",spec,hz)
			var b:Array=await trial(OWNER+"rama_motion.gd",spec,hz)
			var first:=-1;var authority:=a.size()==b.size();var nonleg:=true;var locks:=true;var amin:=INF;var bmin:=INF
			for i in b.size():
				if i>0 and first<0 and b[i].grounded:first=i
				for key in ["tick","root","grounded","velocity","locomotion","clocks"]:authority=authority and a[i][key]==b[i][key]
				nonleg=nonleg and a[i].nonleg_sha256==b[i].nonleg_sha256
				locks=locks and a[i].locks==b[i].locks
				if b[i].has("skin"):
					for side in ["L","R"]:amin=minf(amin,a[i].skin[side].minimum_m);bmin=minf(bmin,b[i].skin[side].minimum_m)
			var prefix:String=spec.name+"/"+str(hz)
			check(prefix+" first grounded soles within 5mm",first>=0 and b[first].skin.L.minimum_m>=-.005 and b[first].skin.R.minimum_m>=-.005 and b[first].skin.L.minimum_m<=.005 and b[first].skin.R.minimum_m<=.005,{"first":first,"baseline":[a[first].skin.L.minimum_m,a[first].skin.R.minimum_m],"candidate":[b[first].skin.L.minimum_m,b[first].skin.R.minimum_m]})
			check(prefix+" root clocks nonleg and anchor timing exact",authority and nonleg and locks,{"authority":authority,"nonleg":nonleg,"anchor_timing":locks})
			check(prefix+" sole floor remains within 5mm and no deeper penetration",bmin>=-.005 and minf(bmin,0.0)>=minf(amin,0.0),{"baseline_min_m":amin,"candidate_min_m":bmin})
			cases_rows.append({"spec":spec,"hz":hz,"baseline":a,"candidate":b})
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"cases":cases_rows,"sources":{"baseline":FileAccess.get_sha256(OWNER+"canonical-rama_motion.gd"),"candidate":FileAccess.get_sha256(OWNER+"rama_motion.gd"),"fixture":FileAccess.get_sha256(get_script().resource_path),"inherited_geometry":FileAccess.get_sha256("/workspace/ANDOLAN/games/yuga-native/tests/graphics_g2_support_cases.gd"),"hero":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb"),"library":FileAccess.get_sha256("res://assets/animations/rama_hero_motion.tres")},"scope":"Imported near-rig actual skinned geometry, prescribed identical roots at every declared30/60/120Hz update and pose evaluation. No native CharacterBody collision simulation, raster or human temporal acceptance. Per-step full leg quaternions, ankle positions and all nonleg local/global hashes retained; near-ground actual full skin minima retained."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	quit(0 if result.passed else 1)
