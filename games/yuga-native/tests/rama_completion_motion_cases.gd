extends SceneTree
## Actual imported skeleton/skin defeat and return contract. No render/feel claim.
const Motion = preload("res://scripts/rama_motion.gd")
const Contacts = preload("res://tools/hero-family-reuse/motion_skin_contacts.gd")
const HERO := "res://assets/heroes/rama-hero.glb"
const BASELINE := "res://art/hero-completion/motion/baseline/rama_motion.gd"
var output := ""
var checks: Array[Dictionary] = []
var trials: Array[Dictionary] = []
var skin := {}
var bow_points: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")
func check(label: String, passed: bool, details: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)
func find(node: Node,kind: String) -> Node:
	if node.is_class(kind):return node
	for child in node.get_children():
		var found:=find(child,kind)
		if found:return found
	return null
func collect_bow(node: Node,rig: Skeleton3D) -> void:
	if node is MeshInstance3D and node.name=="RamaBow":
		var binds:=[]
		for i in node.skin.get_bind_count():
			var bone_name:=String(node.skin.get_bind_name(i))
			binds.append({"bone":rig.find_bone(bone_name) if not bone_name.is_empty() else node.skin.get_bind_bone(i),"inverse":node.skin.get_bind_pose(i)})
		for surface in node.mesh.get_surface_count():
			var arrays:Array=node.mesh.surface_get_arrays(surface)
			var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var joints:PackedInt32Array=arrays[Mesh.ARRAY_BONES]
			var weights:PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			var stride:int=joints.size()/vertices.size()
			for vi in vertices.size():
				var influences:=[]
				for slot in stride:
					var weight:float=weights[vi*stride+slot]
					if weight<=0:continue
					var bind:Dictionary=binds[joints[vi*stride+slot]]
					influences.append({"bone":bind.bone,"point":bind.inverse*vertices[vi],"weight":weight})
				bow_points.append({"influences":influences})
	for child in node.get_children():collect_bow(child,rig)
func point(motion: Node,bone: String) -> Vector3:
	return motion.last_globals[motion.rig.find_bone(bone)].origin
func tick(motion: Node,dt: float,state: Dictionary={}) -> void:
	motion.update_motion(dt,state);motion.evaluate_pose()
func create(script: Script) -> Array:
	var actor:Node3D=load(HERO).instantiate();root.add_child(actor)
	var motion=script.new();var ok:bool=motion.configure(actor,find(actor,"AnimationPlayer"))
	return [actor,motion,ok]
func grip_gap(motion: Node) -> Dictionary:
	var inverse:Transform3D=motion.last_globals[motion.rig.find_bone("wrist.R")].affine_inverse()
	var smallest:=INF;var penetration:=0.0
	for p in Contacts.skin(skin.grip_fingers,motion):
		var local:Vector3=inverse*p-Motion.GRIP_CENTER
		var radial:=Vector2(local.y,local.z).length()-Motion.GRIP_RADIUS
		var axial:=absf(local.x)-Motion.GRIP_HALF_LENGTH
		var signed_distance:=Vector2(maxf(radial,0),maxf(axial,0)).length()+minf(maxf(radial,axial),0)
		smallest=minf(smallest,absf(signed_distance));penetration=maxf(penetration,-signed_distance)
	return {"nearest_m":smallest,"penetration_m":penetration}
func bounds(points: PackedVector3Array) -> Dictionary:
	var low:=Vector3(INF,INF,INF);var high:=Vector3(-INF,-INF,-INF)
	for p in points: low=low.min(p);high=high.max(p)
	return {"low":[low.x,low.y,low.z],"high":[high.x,high.y,high.z],"min_y":low.y,"max_y":high.y}
func execute(hz: float,warm: bool) -> void:
	var fixture:=create(Motion);var actor:Node3D=fixture[0];var motion=fixture[1]
	var tag:="%dHz_%s"%[int(hz),"aimed" if warm else "idle"]
	check(tag+" imports actual unchanged rig",fixture[2])
	if skin.is_empty(): skin=Contacts.collect(actor,motion.rig);collect_bow(actor,motion.rig)
	var state:={"grounded":true,"aiming":warm,"aim_pitch":.4 if warm else 0.0,"aim_yaw":.3 if warm else 0.0,"velocity":Vector3.ZERO}
	for unused in int(hz):tick(motion,1.0/hz,state)
	var actor_before:Transform3D=actor.transform
	var ready_hip:float=point(motion,"spine05").y
	var old_wrists:=[point(motion,"wrist.L"),point(motion,"wrist.R")]
	var accepted:bool=motion.request_action("death",.12,.8)
	state.aiming=false
	var maximum_wrist_step:=0.0;var maximum_wrist_frame:=0;var minimum_bow_y:=INF;var early_hip:=0.0;var marker_held:=false
	var sample_rows:=[]
	for frame in int(hz*1.25):
		tick(motion,1.0/hz,state)
		var now:=[point(motion,"wrist.L"),point(motion,"wrist.R")]
		for i in 2:
			var change:float=now[i].distance_to(old_wrists[i])
			if change>maximum_wrist_step:maximum_wrist_step=change;maximum_wrist_frame=frame
		old_wrists=now
		if frame==int(hz*.20)-1:early_hip=point(motion,"spine05").y
		if frame==int(ceil(hz*.15))-1:marker_held=motion.action_stage=="hold"
		if frame%maxi(1,int(hz/10))==0:
			var bow:Dictionary=bounds(Contacts.skin(bow_points,motion));minimum_bow_y=minf(minimum_bow_y,bow.min_y)
			sample_rows.append({"time_s":(frame+1)/hz,"head":str(point(motion,"head")),"left":str(now[0]),"right":str(now[1]),"bow":bow})
	var head:=point(motion,"head")
	var left:=point(motion,"wrist.L");var right:=point(motion,"wrist.R")
	var settled:Dictionary=bounds(Contacts.skin(bow_points,motion))
	check(tag+" keeps combat marker while visual kneel continues",accepted and marker_held and is_equal_approx(motion.windup,.12) and is_equal_approx(motion.recovery,.8) and early_hip>ready_hip-.30,{"hip_at_200ms":early_hip,"ready_hip":ready_hip})
	check(tag+" lowers both hands below head in stable defeated silhouette",left.y<head.y-.35 and right.y<head.y-.35 and right.y>.4 and right.y<.6,{"left":str(left),"right":str(right),"head":str(head),"bow":settled})
	check(tag+" settles gradually without large wrist discontinuities",maximum_wrist_step<4.0/hz,{"maximum_wrist_step_m":maximum_wrist_step,"at_frame":maximum_wrist_frame,"at_seconds":(maximum_wrist_frame+1)/hz,"limit_m":4.0/hz})
	check(tag+" keeps actual bow geometry clear of the flat floor",minimum_bow_y>-.01,{"minimum_bow_y":minimum_bow_y,"settled_bow":settled})
	var grip:=grip_gap(motion)
	check(tag+" preserves calibrated gripping finger contact",grip.nearest_m<.002 and grip.penetration_m<.002,grip)
	var held:Array=motion.last_positions.duplicate();var held_rot:Array=motion.last_rotations.duplicate()
	for unused in int(hz*.5):tick(motion,1.0/hz,state)
	var still:=true
	for i in held.size(): still=still and held[i].distance_to(motion.last_positions[i])<.00001 and held_rot[i].angle_to(motion.last_rotations[i])<.001
	check(tag+" holds defeated pose without movement or combat release",still and actor.transform==actor_before and motion.release_count==0 and not motion.nocked and not motion.request_action("kodanda",.18,.22) and motion.finite)
	# Runtime reset first cancels presentation, then begins/releases its return.
	motion.cancel("respawn reset")
	check(tag+" reset retires death state and arrow",motion.action.is_empty() and motion.action_stage=="none" and not motion.nocked)
	var returned:bool=motion.request_action("respawn",.1,.7) and motion.release_action("respawn")
	var max_return:=0.0;var old:Vector3=point(motion,"wrist.R")
	for unused in int(hz):
		tick(motion,1.0/hz,{"grounded":true,"velocity":Vector3.ZERO})
		var current:=point(motion,"wrist.R");max_return=maxf(max_return,current.distance_to(old));old=current
	check(tag+" returns to ready stance and unchanged actor transform",returned and motion.action_stage=="none" and point(motion,"spine05").y>ready_hip-.04 and actor.transform==actor_before and motion.finite,{"maximum_return_wrist_step_m":max_return})
	trials.append({"mode":tag,"maximum_wrist_step_m":maximum_wrist_step,"minimum_bow_y":minimum_bow_y,"settled_bow":settled,"max_return_wrist_step_m":max_return,"samples":sample_rows})
	actor.free()
func baseline_counterexample() -> void:
	var fixture:=create(load(BASELINE));var actor:Node3D=fixture[0];var motion=fixture[1]
	for unused in 60:tick(motion,1.0/60)
	motion.request_action("death",.12,.8)
	for unused in 30:tick(motion,1.0/60)
	var head:=point(motion,"head");var wrist:=point(motion,"wrist.R")
	check("Preserved baseline reproduces raised bow hand above defeated head",wrist.y>head.y,{"head":str(head),"right_wrist":str(wrist)})
	actor.free()
func run() -> void:
	var paths:=[get_script().resource_path,Motion.LIBRARY_PATH,HERO,"res://scripts/rama_motion.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_vitals.gd","res://scripts/player.gd","res://scripts/rama_hero_runtime.gd",BASELINE]
	var before:={}
	for p in paths:before[p]=FileAccess.get_sha256(p)
	for hz in [30.0,60.0,120.0]:
		for warm in [false,true]:execute(hz,warm)
	baseline_counterexample()
	var after:={}
	for p in paths:after[p]=FileAccess.get_sha256(p)
	check("All source, canonical hero and simulation owners stable during run",before==after)
	var report:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"trials":trials,"source_before":before,"source_after":after,"bow_vertices":bow_points.size(),"scope":"Actual imported164bone/sampled skin and presentation at30/60/120Hz. No visual, audio, human feel, simulation timing or hardware acceptance claim."}
	if not output.is_empty():
		DirAccess.make_dir_recursive_absolute(output.get_base_dir());FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	quit(0 if report.passed else 1)
