extends SceneTree
const Hero := "res://assets/heroes/rama-hero.glb"
var names := ["root","spine05","spine03","spine01","head","upperarm01.L","upperarm01.R","lowerarm01.L","lowerarm01.R","wrist.L","wrist.R","upperleg01.L","upperleg01.R","foot.L","foot.R"]
func _initialize() -> void: call_deferred("run")
func find_kind(node: Node,kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found:=find_kind(child,kind)
		if found: return found
	return null
func sample(motion: Node) -> Dictionary:
	var row := {}
	for name in names:
		var point:Vector3=motion.rig.get_bone_global_pose(motion.rig.find_bone(name)).origin
		row[name]=[point.x,point.y,point.z]
	row.grip = str(motion.socket_global("bow_grip").origin)
	return row
func run() -> void:
	var model = load(Hero).instantiate()
	root.add_child(model)
	var script = load("res://scripts/rama_motion.gd")
	var motion = script.new()
	assert(motion.configure(model,find_kind(model,"AnimationPlayer")))
	for unused in 60: motion.update_motion(1.0/60,{}); motion.evaluate_pose()
	var rows := [{"time":0,"state":"idle","bones":sample(motion)}]
	motion.request_action("death",.12,.8)
	for frame in 180:
		motion.update_motion(1.0/60,{});motion.evaluate_pose()
		if frame in [0,5,11,23,41,59,119,179]:rows.append({"time":(frame+1)/60.0,"state":motion.action_stage,"bones":sample(motion)})
	print(JSON.stringify(rows,"\t"))
	model.free();quit()
