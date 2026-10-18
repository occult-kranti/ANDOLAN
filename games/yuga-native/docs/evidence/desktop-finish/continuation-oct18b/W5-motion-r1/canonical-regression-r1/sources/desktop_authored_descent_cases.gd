extends "res://tests/graphics_g2_support_cases.gd"
## Maintained imported-skin regression; prescribed roots, not a raster/feel test.
const BASELINE := "res://docs/evidence/desktop-finish/continuation-oct18b/W5-motion-r1/canonical-rama_motion.gd"
const MOTION := "res://scripts/rama_motion.gd"
const LIBRARY := "res://assets/animations/rama_hero_motion.tres"
const HERO := "res://assets/heroes/rama-hero.glb"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
	call_deferred("run")

func signature(value:Variant) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256)
	context.update(var_to_bytes(value));return context.finish().hex_encode()

func leg(name_:String) -> bool:
	return name_.begins_with("upperleg") or name_.begins_with("lowerleg") or name_.begins_with("foot") or name_.begins_with("toe")

func source_records() -> Dictionary:
	var result:={}
	for path in [get_script().resource_path,"res://tests/graphics_g2_support_cases.gd",BASELINE,MOTION,LIBRARY,HERO,HERO+".import"]:
		result[path]=FileAccess.get_sha256(path)
	var config:=ConfigFile.new()
	if config.load(HERO+".import")==OK:
		for path in config.get_value("deps","dest_files",[]):result[path]=FileAccess.get_sha256(path)
	return result

func missing_land() -> void:
	# The cached library is changed only inside this test process and restored
	# before any descent case. The old implementation is the negative control.
	var library:AnimationLibrary=load(LIBRARY)
	var saved:Animation=library.get_animation("land")
	library.remove_animation("land")
	var admitted:=[]
	for path in [BASELINE,MOTION]:
		var model:Node3D=load(HERO).instantiate();root.add_child(model)
		var motion=load(path).new()
		var accepted:bool=motion.configure(model,find_kind(model,"AnimationPlayer"))
		admitted.append(accepted)
		if not accepted:motion.free()
		model.free()
	library.add_animation("land",saved)
	check("missing land rejects admission while complete library is restored",admitted==[true,false] and library.get_animation("land")==saved,{"old_accepted":admitted[0],"current_accepted":admitted[1],"restored":library.get_animation("land")==saved})

func sample(motion:Node,actor:Node3D,selected:Array,tick:int) -> Dictionary:
	var nonleg:=[];var knees:=[]
	for index in motion.rig.get_bone_count():
		var name_:String=motion.rig.get_bone_name(index)
		if not leg(name_):nonleg.append([motion.rig.get_bone_pose(index),motion.last_globals[index]])
		elif name_.begins_with("lowerleg01"):
			knees.append(motion.rig.get_bone_pose_rotation(index))
	var row:={"tick":tick,"root":actor.transform,"grounded":motion.grounded,"velocity":motion.world_velocity,"locomotion":motion.locomotion,"clocks":[motion.phase,motion.locomotion_age,motion.transition_age,motion.transition_duration,motion.action_elapsed,motion.release_count,motion.cancel_count],"nonleg":signature(nonleg),"locks":motion.foot_locks.duplicate(),"targets":motion.foot_targets.duplicate(),"knees":knees,"finite":motion.finite}
	if actor.position.y<.25:
		var skin:=measure(motion,selected,0.0);skin.erase("positions");row["skin"]=skin
	return row

func trial(path:String,hz:int) -> Array:
	var floor_body:=StaticBody3D.new();floor_body.collision_layer=1
	var floor_shape:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(4,.2,4);floor_shape.shape=box
	floor_body.add_child(floor_shape);root.add_child(floor_body);floor_body.position.y=-.1
	var actor:=CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor)
	var model:Node3D=load(HERO).instantiate();actor.add_child(model)
	var motion=load(path).new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	var selected:=soles(model,motion.rig)
	var dt:=1.0/hz;var base_y:=.0008394047617912292;actor.position.y=base_y
	var state:={"grounded":true,"floor_y":base_y,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"ground"}
	await physics_frame
	for tick in int(hz*.3):motion.update_motion(dt,state);motion.evaluate_pose()
	var rows:Array=[];var speed:=7.2;var airborne:=true;var landed_age:=0.0
	for tick in int(hz*1.2):
		if airborne:
			speed-=18.0*dt
			var next_y:float=actor.position.y+speed*dt
			airborne=next_y>base_y;actor.position.y=maxf(base_y,next_y)
		state.grounded=not airborne;state.floor_y=actor.position.y
		state.velocity=Vector3(0,speed if airborne else 0,0);state.local_velocity=state.velocity
		var root_before:=actor.transform
		motion.update_motion(dt,state);motion.evaluate_pose()
		var row:=sample(motion,actor,selected,tick);row["root_unwritten"]=actor.transform==root_before;rows.append(row)
		if not airborne:
			landed_age+=dt
			if landed_age>=.3:break
	actor.free();floor_body.free();await process_frame
	return rows

func compare(hz:int,a:Array,b:Array) -> Dictionary:
	var first:=-1;var exact:=a.size()==b.size();var safe:=true;var have_jump:=false;var have_fall:=false
	var baseline_min:=INF;var current_min:=INF;var peak_knee:=0.0;var compact:=[]
	for i in b.size():
		var row:Dictionary=b[i]
		if first<0 and row.grounded:first=i
		have_jump=have_jump or row.locomotion=="jump";have_fall=have_fall or row.locomotion=="fall"
		for key in ["tick","root","grounded","velocity","locomotion","clocks","nonleg","locks","targets"]:exact=exact and a[i][key]==row[key]
		exact=exact and row.root_unwritten
		safe=safe and row.finite and (row.grounded or (not row.locks.L and not row.locks.R))
		if i>0:
			for j in row.knees.size():peak_knee=maxf(peak_knee,rad_to_deg(Quaternion(row.knees[j]).angle_to(b[i-1].knees[j])))
		if row.has("skin"):
			for side in ["L","R"]:
				baseline_min=minf(baseline_min,a[i].skin[side].minimum_m);current_min=minf(current_min,row.skin[side].minimum_m)
			if first<0 or i-first<=4:
				compact.append({"tick":i,"grounded":row.grounded,"land_age":row.clocks[1],"transition_age":row.clocks[2],"gaps_m":[row.skin.L.minimum_m,row.skin.R.minimum_m],"locks":row.locks})
	var first_skin:Dictionary=b[first].skin if first>=0 else {}
	var contact:=first>=0 and have_jump and have_fall and not first_skin.is_empty()
	if contact:
		for side in ["L","R"]:contact=contact and first_skin[side].vertices>0 and absf(first_skin[side].minimum_m)<=.005
	check(str(hz)+"Hz first grounded imported soles within5mm after jump and fall",contact,{"first_tick":first,"baseline_gaps_m":[a[first].skin.L.minimum_m,a[first].skin.R.minimum_m] if first>=0 else [],"current_skin":first_skin})
	check(str(hz)+"Hz root nonleg clocks and anchor state remain exact",exact)
	check(str(hz)+"Hz no airborne anchor or deeper sole penetration",safe and current_min>=-.005 and minf(current_min,0.0)>=minf(baseline_min,0.0),{"baseline_min_m":baseline_min,"current_min_m":current_min})
	return {"hz":hz,"steps":b.size(),"baseline_digest":signature(a),"current_digest":signature(b),"peak_local_knee_step_degrees":peak_knee,"contact_window":compact,"scope":"Every prescribed timestep evaluated. Peak angle is reported, not an aesthetic threshold; actual acceptance remains separate."}

func run() -> void:
	var before:=source_records();missing_land();var cases:=[]
	for hz in [30,60,120]:
		var baseline:Array=await trial(BASELINE,hz)
		var current:Array=await trial(MOTION,hz)
		cases.append(compare(hz,baseline,current))
	check("fixture runtime library and imported sources unchanged",source_records()==before)
	var passed:=checks.all(func(row):return row.passed)
	var result:={"passed":passed,"count":checks.size(),"checks":checks,"cases":cases,"source_sha256":before,"scope":"Imported actual skinned soles on a real box floor, prescribed jump/fall roots at30/60/120Hz. Component regression only; not native collision movement, raster, human feel or hardware performance."}
	var file:=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(result)+"\n");file.close()
	quit(0 if passed else 1)
