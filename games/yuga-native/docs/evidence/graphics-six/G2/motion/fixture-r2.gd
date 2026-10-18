extends SceneTree
## Imported skinned sole comparison on real courtyard collision geometry.
var report_path := "/tmp/graphics-g2-support.json"
var baseline_path := "/workspace/ANDOLAN/scratch/graphics-six/G2/motion/rama_motion.baseline.gd"
var candidate_path := "res://scripts/rama_motion.gd"
var checks: Array=[]
var trials: Array=[]
var scene: Node3D
var source_pins: Dictionary={}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
		elif arg.begins_with("--candidate-script="):candidate_path=arg.trim_prefix("--candidate-script=")
	call_deferred("run")

func find_kind(node: Node, kind: String) -> Node:
	if node.is_class(kind):return node
	for child in node.get_children():
		var found:=find_kind(child,kind)
		if found:return found
	return null

func vec(v: Vector3) -> Array:return [v.x,v.y,v.z]
func check(name_: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":name_,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",name_)

func pins() -> Dictionary:
	var result:={}
	for path in [baseline_path,candidate_path,"res://tests/graphics_g2_support_cases.gd","res://scripts/player.gd","res://scripts/courtyard.gd","res://assets/animations/rama_hero_motion.tres","res://assets/environment/lanka_courtyard.glb","res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb"]:
		result[path]=FileAccess.get_sha256(path)
		if path.ends_with(".glb"):
			result[path+".import"]=FileAccess.get_sha256(path+".import")
			var config:=ConfigFile.new()
			if config.load(path+".import")==OK:
				for dest in config.get_value("deps","dest_files",[]):result[dest]=FileAccess.get_sha256(dest)
	return result

func soles(model: Node, rig: Skeleton3D) -> Array:
	var result:=[]
	for node in model.find_children("*","MeshInstance3D",true,false):
		if not node.mesh or not node.skin or not node.is_visible_in_tree():continue
		var binds:=[]
		for index in node.skin.get_bind_count():
			var bone: int=rig.find_bone(String(node.skin.get_bind_name(index)))
			if bone<0:bone=node.skin.get_bind_bone(index)
			binds.append({"bone":bone,"inverse":node.skin.get_bind_pose(index)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array=node.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var bones: Variant=arrays[Mesh.ARRAY_BONES];var weights: Variant=arrays[Mesh.ARRAY_WEIGHTS]
			if bones==null or weights==null:continue
			var slots: int=bones.size()/vertices.size()
			for index in vertices.size():
				if vertices[index].y>=.30:continue
				var sums:={"L":0.0,"R":0.0};var influences:=[]
				for slot in slots:
					var weight: float=weights[index*slots+slot]
					if weight<=0:continue
					var bind: Dictionary=binds[bones[index*slots+slot]]
					var name_: String=rig.get_bone_name(bind.bone)
					if name_.begins_with("foot") or name_.begins_with("toe"):
						for side in ["L","R"]:
							if name_.ends_with("."+side):sums[side]+=weight
					influences.append({"bone":bind.bone,"point":bind.inverse*vertices[index],"weight":weight})
				var side: String="L" if sums.L>.5 else "R" if sums.R>.5 else ""
				if not side.is_empty():result.append({"side":side,"node":String(node.name),"surface":surface,"vertex":index,"influences":influences})
	return result

func measure(motion: Node, selected: Array, plane_y: float) -> Dictionary:
	var result:={}
	var positions:=[]
	for side in ["L","R"]:result[side]={"minimum_m":INF,"maximum_m":-INF,"below_minus_5mm":0,"vertices":0}
	for vertex in selected:
		var local:=Vector3.ZERO
		for influence in vertex.influences:local+=(motion.last_globals[influence.bone]*influence.point)*influence.weight
		var world: Vector3=motion.rig.global_transform*local
		positions.append(world)
		var item: Dictionary=result[vertex.side];var distance:=world.y-plane_y
		if distance<item.minimum_m:
			item.minimum_m=distance;item.witness={"node":vertex.node,"surface":vertex.surface,"vertex":vertex.vertex,"world":vec(world)}
		item.maximum_m=maxf(item.maximum_m,distance)
		item.below_minus_5mm+=int(distance<-.005);item.vertices+=1
	result["positions"]=positions
	return result

func execute(script: Script, asset: String, name_: String, hz: int) -> Dictionary:
	var body:=CharacterBody3D.new();body.collision_layer=2;body.collision_mask=1
	root.add_child(body)
	body.position=Vector3(0,.05,12)
	if name_=="elevated":body.position=Vector3(19,.49,-1)
	elif name_=="out_of_range":body.position.y=.30
	elif name_=="no_ground":body.position=Vector3(1000,.05,1000)
	var model: Node3D=load(asset).instantiate();body.add_child(model)
	var motion=script.new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")))
	motion.active=false # Manual evaluation has exactly one writer for this diagnostic.
	var selected:=soles(model,motion.rig)
	var state:={"grounded":name_!="airborne","floor_y":body.position.y,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"flight" if name_=="flight" else "grapple" if name_=="grapple" else "ground"}
	if name_=="walk":state.velocity=Vector3(0,0,2);state.local_velocity=state.velocity
	var plane_y:=.44 if name_=="elevated" else 0.0
	var body_before:=body.transform
	var rows:=[];var anchors:={};var drift:=0.0;var maximum_error:=0.0
	var original_skin:=[];var skin_drift:=0.0
	await physics_frame
	var query_phase:=Engine.is_in_physics_frame()
	for frame in int(hz*.4):
		if name_=="reset_teleport" and frame==int(hz*.2):
			motion.cancel("G2 teleport reset")
			body.position=Vector3(19,.49,-1);body_before=body.transform
			state.floor_y=body.position.y;plane_y=.44;anchors.clear();original_skin.clear()
		motion.update_motion(1.0/hz,state);motion.evaluate_pose()
		for side in ["L","R"]:
			if motion.foot_locks[side]:
				if not anchors.has(side):anchors[side]=motion.foot_targets[side]
				drift=maxf(drift,Vector3(anchors[side]).distance_to(motion.foot_targets[side]))
		if frame in [0,int(round(hz*.133333))-1,int(hz*.4)-1]:
			var skin:=measure(motion,selected,plane_y)
			if original_skin.is_empty():original_skin=skin.positions
			for index in original_skin.size():skin_drift=maxf(skin_drift,Vector3(original_skin[index]).distance_to(skin.positions[index]))
			skin.erase("positions")
			rows.append({"frame":frame,"age":motion.locomotion_age,"soles":skin,"locks":motion.foot_locks.duplicate(),"targets":{"L":vec(motion.foot_targets.L),"R":vec(motion.foot_targets.R)}})
		maximum_error=maxf(maximum_error,motion.max_contact_error)
	var clock:={"phase":motion.phase,"age":motion.locomotion_age,"stage":motion.action_stage,"release_count":motion.release_count}
	var final:=[]
	for transform in motion.last_globals:final.append(transform.origin)
	var result:={"name":name_,"asset":asset,"hz":hz,"rows":rows,"root_unchanged":body.transform==body_before,"anchor_drift_m":drift,"maximum_sampled_skin_drift_m":skin_drift,"max_endpoint_error_m":maximum_error,"clock":clock,"final_points":final,"selected_vertices":selected.size(),"query_in_physics_frame":query_phase}
	body.free();return result

func detached_probe(script: Script) -> bool:
	var model: Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();root.add_child(model)
	var motion=script.new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")))
	motion.active=false;motion.floor_y=.05
	# This helper must be safe both outside physics and with no tree/world.
	motion._update_idle_support()
	var outside_ok: bool=motion.idle_support_y.L==.05 and motion.idle_support_y.R==.05
	root.remove_child(model)
	await physics_frame
	motion._update_idle_support()
	var detached_ok: bool=motion.idle_support_y.L==.05 and motion.idle_support_y.R==.05
	model.free();return outside_ok and detached_ok

func run() -> void:
	source_pins=pins()
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene)
	for frame in 12:await physics_frame;await process_frame
	var player: CharacterBody3D=scene.player
	player.set_physics_process(false)
	var ray:=scene.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(player.global_position+Vector3.UP,player.global_position-Vector3.UP,1,[player.get_rid()]))
	var native:={"root":vec(player.global_position),"physically_grounded":player.is_on_floor(),"motion":player.rama_motion.diagnostics(),"floor_input":player.rama_motion.floor_y,"ray_point":vec(ray.position) if not ray.is_empty() else [],"ray_normal":vec(ray.normal) if not ray.is_empty() else []}
	var native_skin:=measure(player.rama_motion,soles(player.visual,player.rama_motion.rig),0)
	native_skin.erase("positions");native["skinned_soles"]=native_skin
	check("actual title root lies50mm above actual courtyard support plane",not ray.is_empty() and absf(player.global_position.y-ray.position.y-.05)<.00001,native)
	var baseline: Script=load(baseline_path);var candidate: Script=load(candidate_path)
	var improved:=true;var safe:=true;var unchanged:=true;var clocks:=true;var roots:=true;var drift:=true;var skin_stable:=true;var physics_queries:=true
	for hz in [30,60,120]:
		for asset in ["res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb"]:
			if hz!=60 and asset!="res://assets/heroes/rama-hero.glb":continue
			for name_ in ["idle","elevated","reset_teleport","out_of_range","no_ground","airborne","flight","grapple","walk"]:
				if (hz!=60 or asset!="res://assets/heroes/rama-hero.glb") and name_!="idle":continue
				var a: Dictionary=await execute(baseline,asset,name_,hz);var b: Dictionary=await execute(candidate,asset,name_,hz)
				if name_ in ["idle","elevated","reset_teleport"]:
					for side in ["L","R"]:
						var av: Dictionary=a.rows[-1].soles[side];var bv: Dictionary=b.rows[-1].soles[side]
						improved=improved and av.minimum_m>.045 and bv.minimum_m<.005 and bv.minimum_m>=0
						for row in b.rows:safe=safe and row.soles[side].below_minus_5mm==0 and row.soles[side].minimum_m>=0
					if name_!="reset_teleport":skin_stable=skin_stable and b.maximum_sampled_skin_drift_m<=a.maximum_sampled_skin_drift_m+.00001
				else:
					for bone in a.final_points.size():unchanged=unchanged and Vector3(a.final_points[bone]).distance_to(b.final_points[bone])<.00001
				clocks=clocks and a.clock==b.clock;roots=roots and b.root_unchanged;drift=drift and b.anchor_drift_m<.000001
				physics_queries=physics_queries and b.query_in_physics_frame
				a.erase("final_points");b.erase("final_points");trials.append({"baseline":a,"candidate":b})
	check("idle actual skinned soles approach floor on near/mid/far and30/60/120",improved)
	check("sampled idle/elevated skinned soles do not penetrate plane",safe)
	check("out-of-range absent-plane airborne flight grapple walk remain baseline-equal",unchanged)
	check("root transform and presentation clocks unchanged",roots and clocks)
	check("acquired world anchors remain fixed",drift)
	check("sampled support skin drift does not exceed baseline",skin_stable)
	check("candidate acquisition comparisons run inside physics frame",physics_queries)
	await process_frame
	check("off-physics and detached no-world probes preserve fallback without querying",await detached_probe(candidate))
	check("source and actual imports remain unchanged",pins()==source_pins)
	var passed:=checks.all(func(x):return x.passed)
	var file:=FileAccess.open(report_path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"native_title":native,"trials":trials,"source_sha256":source_pins,"scope":"Actual imported sole vertices and real courtyard collision geometry; same-state manual pose comparison. No rendered/static/continuous acceptance; native callback screenshots remain separate."},"\t")+"\n");file.close()
	quit(0 if passed else 1)
