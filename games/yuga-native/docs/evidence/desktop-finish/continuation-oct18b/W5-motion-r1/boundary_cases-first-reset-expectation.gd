extends "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W5-motion-r1/component_authored_descent.gd"
var details:Dictionary={}

func setup(path:String) -> Dictionary:
	var support:=StaticBody3D.new();support.collision_layer=1
	var shape_node:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(4,.2,4);shape_node.shape=box
	support.add_child(shape_node);root.add_child(support);support.position.y=-.1
	var actor:=CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor)
	var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();actor.add_child(model)
	var motion=load(path).new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	var selected:=soles(model,motion.rig);actor.position.y=.0008394047617912292
	await physics_frame
	for tick in 20:motion.update_motion(1.0/60,{"grounded":true,"floor_y":actor.position.y});motion.evaluate_pose()
	return {"support":support,"shape_node":shape_node,"shape":box,"actor":actor,"model":model,"motion":motion,"selected":selected}

func release(item:Dictionary) -> void:
	item.actor.free();item.support.free()

func locals(motion:Node) -> Array:
	var result:Array=[]
	for index in motion.rig.get_bone_count():result.append(motion.rig.get_bone_pose(index))
	return result

func neutral_fall(item:Dictionary,height:float=.06) -> void:
	item.actor.position.y=height
	for tick in 20:
		item.motion.update_motion(1.0/60,{"grounded":false,"floor_y":height,"velocity":Vector3(0,-2,0),"traversal":"ground"});item.motion.evaluate_pose()

func support_mutation(kind:String) -> Dictionary:
	var item:=await setup(OWNER+"rama_motion.gd");neutral_fall(item,-.02)
	var motion:Node=item.motion
	motion.update_motion(1.0/60,{"grounded":false,"floor_y":-.02,"velocity":Vector3(0,-2,0),"traversal":"ground"})
	var hit_count:int=motion.descent_support_y.size()
	var saved:Dictionary=motion.descent_support_y.duplicate()
	motion.descent_support_y.clear();motion.evaluate_pose();var uncorrected:=locals(motion)
	var uncorrected_skin:=measure(motion,item.selected,0);uncorrected_skin.erase("positions")
	motion.descent_support_y=saved;motion.evaluate_pose();var corrected:=locals(motion)
	if kind=="layer":item.support.collision_layer=2
	elif kind=="disabled":item.shape_node.disabled=true
	elif kind=="shape_geometry":item.shape.size=Vector3(4,.3,4)
	elif kind=="shape_resource":item.shape_node.shape=BoxShape3D.new()
	elif kind=="shape_transform":item.shape_node.position.x=.2
	elif kind=="owner_transform":item.support.position.x=.2
	elif kind=="owner_disposal":item.support.queue_free()
	elif kind=="rig_transform":item.actor.position.x=.3
	motion.evaluate_pose()
	var after:=locals(motion)
	var result:={"hits":hit_count,"control_correction_nonzero":uncorrected!=corrected,"invalidated_pose_equals_no_support":after==uncorrected,"air_locks":motion.foot_locks.duplicate(),"uncorrected_skin":uncorrected_skin}
	check("fresh support invalidation "+kind,hit_count==2 and uncorrected!=corrected and after==uncorrected and not motion.foot_locks.L and not motion.foot_locks.R,result)
	# queued deletion is retained until ordinary disposal; no second free.
	item.actor.free()
	if kind!="owner_disposal":item.support.free()
	await process_frame
	return result

func action_case(path:String,kind:String) -> Array:
	var item:=await setup(path);neutral_fall(item,.3)
	var motion:Node=item.motion;var rows:Array=[]
	motion.request_action(kind,.18,.22)
	for tick in 18:
		var state:={"grounded":false,"floor_y":.3,"velocity":Vector3(0,-2,0),"traversal":"ground","aiming":kind=="kodanda","aim_pitch":.2,"aim_yaw":-.1}
		motion.update_motion(1.0/60,state)
		if tick==12 and kind=="kodanda":motion.release_action(kind)
		if tick==15 and kind=="kodanda":motion.cancel_action("interrupted component")
		motion.evaluate_pose()
		var r:=record(motion,item.actor,item.selected,0,tick,1.0/60);r["all_pose_sha256"]=signature(locals(motion));rows.append(r)
	release(item);await process_frame
	return rows

func missing_land() -> void:
	var library:AnimationLibrary=load("res://assets/animations/rama_hero_motion.tres")
	var saved:Animation=library.get_animation("land")
	library.remove_animation("land")
	var results:Dictionary={}
	for pair in [["baseline","canonical-rama_motion.gd"],["candidate","rama_motion.gd"]]:
		var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();root.add_child(model)
		var motion=load(OWNER+pair[1]).new();var accepted:bool=motion.configure(model,find_kind(model,"AnimationPlayer"));results[pair[0]]=accepted
		if not accepted:motion.free()
		model.free()
	library.add_animation("land",saved)
	check("missing newly required land animation rejected before sample",results.baseline and not results.candidate and library.has_animation("land"),results)

func landing_probe() -> void:
	var item:=await setup(OWNER+"contact_observer.gd");item.motion.observer_selected=item.selected
	var speed:=7.2;var airborne:=true;var grounded_ticks:=0;var rows:Array=[]
	for tick in 36:
		if airborne:
			speed-=18.0/30
			var next_y:float=item.actor.position.y+speed/30
			airborne=next_y>.0008394047617912292
			item.actor.position.y=maxf(.0008394047617912292,next_y)
		item.motion.update_motion(1.0/30,{"grounded":not airborne,"floor_y":item.actor.position.y,"velocity":Vector3(0,speed if airborne else 0,0),"traversal":"ground"});item.motion.evaluate_pose()
		rows.append(record(item.motion,item.actor,item.selected,0,tick,1.0/30))
		if not airborne:
			grounded_ticks+=1
			if grounded_ticks==3:break
	details["first_contact_stages"]={"rows":rows,"observations":item.motion.contact_observations.duplicate(true)}
	var safe:=true
	for obs in item.motion.contact_observations:
		safe=safe and obs.before_clearance.nonleg_sha256==obs.after_clearance.nonleg_sha256 and obs.before_clearance.nonleg_sha256==obs.after_contact.nonleg_sha256
	check("contact diagnostic preserves nonleg at each internal stage",safe and item.motion.contact_observations.size()==3,{"observations":item.motion.contact_observations.size()})
	release(item);await process_frame

func run() -> void:
	missing_land()
	for kind in ["layer","disabled","shape_geometry","shape_resource","shape_transform","owner_transform","owner_disposal","rig_transform"]:await support_mutation(kind)
	var item:=await setup(OWNER+"rama_motion.gd");neutral_fall(item,-.02)
	item.actor.position.x=1.95
	item.motion.update_motion(1.0/60,{"grounded":false,"floor_y":-.02,"velocity":Vector3(0,-2,0)});item.motion.evaluate_pose()
	var edge_skin:=measure(item.motion,item.selected,0);edge_skin.erase("positions")
	check("narrow edge admits only actually supported footprint",item.motion.descent_support_y.has("R") and not item.motion.descent_support_y.has("L") and edge_skin.R.minimum_m>=-.005 and edge_skin.L.minimum_m<-.01 and not item.motion.foot_locks.L and not item.motion.foot_locks.R,{"hits":item.motion.descent_support_y.duplicate(),"skin":edge_skin,"scope":"Counterfactual root below plane; left foot is fully outside the finite box, so its signed distance to the infinite plane is not terrain penetration."})
	release(item);await process_frame
	item=await setup(OWNER+"rama_motion.gd");neutral_fall(item,.3)
	var held:=locals(item.motion);var clocks:=[item.motion.phase,item.motion.locomotion_age,item.motion.transition_age]
	for tick in 8:item.motion.evaluate_pose()
	check("paused pose evaluation adds no elapsed motion",held==locals(item.motion) and clocks==[item.motion.phase,item.motion.locomotion_age,item.motion.transition_age])
	item.motion.cancel("reset in fall");item.actor.position.y=.0008394047617912292
	item.motion.update_motion(1.0/60,{"grounded":true,"floor_y":item.actor.position.y});item.motion.evaluate_pose()
	check("reset returns to idle and clears air support",item.motion.locomotion=="idle" and item.motion.descent_support_y.is_empty() and item.motion.action_stage=="none")
	release(item);await process_frame
	for kind in ["kodanda","hit"]:
		var a:Array=await action_case(OWNER+"canonical-rama_motion.gd",kind)
		var b:Array=await action_case(OWNER+"rama_motion.gd",kind)
		var same:=true;var fullbody:=true
		for i in a.size():
			same=same and a[i].nonleg_sha256==b[i].nonleg_sha256 and a[i].clocks==b[i].clocks and a[i].locks==b[i].locks
			if kind=="hit" and i>=6:fullbody=fullbody and a[i].all_pose_sha256==b[i].all_pose_sha256
		check("airborne "+kind+" preserves nonleg clocks and later fullbody precedence",same and fullbody,{"nonleg_clocks_locks":same,"fullbody_after_entry":fullbody,"baseline":a,"candidate":b})
	await landing_probe()
	var spec:={"name":"elevated","support":.7,"height":0.0,"speed":7.2,"gravity":18.0}
	var a:Array=await trial(OWNER+"canonical-rama_motion.gd",spec,60);var b:Array=await trial(OWNER+"rama_motion.gd",spec,60)
	var first:=-1;var controls:=true
	for i in b.size():
		if i>0 and first<0 and b[i].grounded:first=i
		controls=controls and a[i].root==b[i].root and a[i].clocks==b[i].clocks and a[i].nonleg_sha256==b[i].nonleg_sha256 and a[i].locks==b[i].locks
	check("elevated support first soles within5mm with exact controls",controls and first>=0 and b[first].skin.L.minimum_m>=-.005 and b[first].skin.R.minimum_m>=-.005 and b[first].skin.L.minimum_m<=.005 and b[first].skin.R.minimum_m<=.005,{"first":first,"gaps":[b[first].skin.L.minimum_m,b[first].skin.R.minimum_m],"controls":controls})
	details["elevated"]={"baseline":a,"candidate":b}
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"details":details,"source":{"candidate":FileAccess.get_sha256(OWNER+"rama_motion.gd"),"fixture":FileAccess.get_sha256(get_script().resource_path),"observer":FileAccess.get_sha256(OWNER+"contact_observer.gd")},"scope":"Actual imported-rig component and physics-query guards; manually prescribed root/input timing. No raster/native collision-authority claim. Invalid-support controls deliberately place the root below a plane to exercise existing upward-only clearance."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	quit(0 if result.passed else 1)
