extends "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W5-motion-r1/rama_motion.gd"
## Read-only boundary observer; all original operations execute once.
var contact_observations:Array=[]
var observer_selected:Array=[]
func pose_snapshot() -> Dictionary:
	var globals:Array=[];var nonleg:Array=[];var legs:Dictionary={}
	for index in rig.get_bone_count():
		var name_:String=rig.get_bone_name(index)
		var g:Transform3D=rig.get_bone_global_pose(index);globals.append(g)
		if name_.begins_with("upperleg") or name_.begins_with("lowerleg") or name_.begins_with("foot") or name_.begins_with("toe"):
			var q:Quaternion=rig.get_bone_pose_rotation(index);var gq:Quaternion=g.basis.get_rotation_quaternion()
			legs[name_]={"local":[q.x,q.y,q.z,q.w],"global":[gq.x,gq.y,gq.z,gq.w]}
		else:nonleg.append([rig.get_bone_pose(index),g])
	var hash_:=HashingContext.new();hash_.start(HashingContext.HASH_SHA256);hash_.update(var_to_bytes(nonleg))
	var skin:={"L":INF,"R":INF}
	for vertex in observer_selected:
		var local:=Vector3.ZERO
		for influence in vertex.influences:local+=(globals[influence.bone]*influence.point)*influence.weight
		var world:Vector3=rig.global_transform*local
		skin[vertex.side]=minf(skin[vertex.side],world.y)
	return {"legs":legs,"skin_min_world_y":skin,"nonleg_sha256":hash_.finish().hex_encode(),"locks":foot_locks.duplicate()}
func _protect_transition_floor() -> void:
	var before:=pose_snapshot() if grounded and locomotion=="land" and locomotion_age<=.10000001 else {}
	super._protect_transition_floor()
	if not before.is_empty():
		contact_observations.append({"age":locomotion_age,"transition_age":transition_age,"before_clearance":before,"after_clearance":pose_snapshot()})
func _apply_contact() -> void:
	var count:=contact_observations.size()
	super._apply_contact()
	if contact_observations.size()>count:contact_observations[-1]["after_contact"]=pose_snapshot()
