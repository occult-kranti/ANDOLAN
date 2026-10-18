extends SceneTree
const MOTION:=preload("res://scripts/rama_motion.gd")
const HERO:="res://assets/heroes/rama-hero.glb"
var output:=""
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")
func find_kind(node:Node,kind:String)->Node:
	if node.is_class(kind):return node
	for child in node.get_children():
		var found:=find_kind(child,kind)
		if found:return found
	return null
func matrix(t:Transform3D)->Array:
	return [[t.basis.x.x,t.basis.y.x,t.basis.z.x,t.origin.x],[t.basis.x.y,t.basis.y.y,t.basis.z.y,t.origin.y],[t.basis.x.z,t.basis.y.z,t.basis.z.z,t.origin.z],[0,0,0,1]]
func run()->void:
	var rows:Array[Dictionary]=[];var rests:={};var checks:Array[Dictionary]=[]
	for hz in [30.0,60.0,120.0]:
		var model:Node3D=load(HERO).instantiate();root.add_child(model)
		var motion=MOTION.new();var configured:bool=motion.configure(model,find_kind(model,"AnimationPlayer"));checks.append({"name":"configure "+str(hz),"passed":configured})
		for index in motion.rig.get_bone_count():rests[motion.rig.get_bone_name(index)]=matrix(motion.rig.get_bone_global_rest(index))
		var tape:=[{"id":"walk","velocity":Vector3(0,0,2)},{"id":"run","velocity":Vector3(0,0,6)},{"id":"backpedal","velocity":Vector3(0,0,-6),"aiming":true},{"id":"strafe","velocity":Vector3(4,0,0),"aiming":true},{"id":"stop","velocity":Vector3.ZERO},{"id":"aim_down","aiming":true,"aim_pitch":-.85,"aim_yaw":-.7},{"id":"draw","aiming":true,"aim_pitch":.65,"aim_yaw":.7},{"id":"release","velocity":Vector3(0,0,6),"aiming":true},{"id":"cancel","velocity":Vector3(0,0,6)},{"id":"jump","velocity":Vector3(0,5,6),"grounded":false},{"id":"fall","velocity":Vector3(0,-5,6),"grounded":false},{"id":"land","velocity":Vector3.ZERO},{"id":"reset","velocity":Vector3.ZERO}]
		for state in tape:
			if state.id=="draw":motion.request_action("kodanda",.18,.22)
			if state.id=="release":motion.release_action("kodanda")
			if state.id=="cancel":motion.request_action("piercing_dawn",.18,.22);motion.cancel_action("independent cancel")
			if state.id=="reset":motion.cancel("independent reset");model.position=Vector3.ZERO
			for frame in int(hz*.3):
				model.position+=Vector3(state.get("velocity",Vector3.ZERO))/hz
				motion.update_motion(1.0/hz,state);motion.evaluate_pose()
			var poses:={}
			for index in motion.rig.get_bone_count():poses[motion.rig.get_bone_name(index)]=matrix(motion.rig.get_bone_global_pose(index))
			rows.append({"id":str(hz)+"Hz_"+state.id,"bone_global_poses":poses,"motion":motion.diagnostics(),"root_position":model.position,"input":state})
		model.free()
	var result:={"task":"R3-10","checks":checks,"passed":checks.all(func(x):return x.passed),"samples":rows,"bone_global_rests":rests,"source_pins":{HERO:FileAccess.get_sha256(HERO),"res://scripts/rama_motion.gd":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"res://assets/animations/rama_hero_motion.tres":FileAccess.get_sha256("res://assets/animations/rama_hero_motion.tres")},"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"New actual imported groom skeletal tape at30/60/120Hz; accepted controller unchanged. Source skin/collision evaluation separate; no rendered or gameplay authority claim."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n");quit(0 if result.passed else 1)
