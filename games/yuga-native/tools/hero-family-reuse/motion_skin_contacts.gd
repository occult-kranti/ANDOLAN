extends RefCounted
## Actual imported skin sampling, adapted from tests/rama_motion_cases.gd.
## Samples the accepted mesh/bind arrays; no procedural replacement geometry.
static func collect(model: Node,rig: Skeleton3D) -> Dictionary:
	var result:={"string":[],"draw_fingers":[],"grip_fingers":[]}
	_collect(model,rig,result)
	return result

static func _collect(node: Node,rig: Skeleton3D,result: Dictionary) -> void:
	if node is MeshInstance3D and node.skin:
		var binds:=[]
		for index in node.skin.get_bind_count():
			var name_:=str(node.skin.get_bind_name(index))
			var bone: int=rig.find_bone(name_) if not name_.is_empty() else node.skin.get_bind_bone(index)
			binds.append({"bone":bone,"inverse":node.skin.get_bind_pose(index)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array=node.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var joints: PackedInt32Array=arrays[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			if vertices.is_empty() or joints.is_empty():continue
			var stride: int=joints.size()/vertices.size()
			for vi in vertices.size():
				var influences:=[];var dominant:=-1;var largest:=0.;var string_weight:=0.
				for slot in stride:
					var weight: float=weights[vi*stride+slot]
					if weight<=0:continue
					var bind: Dictionary=binds[joints[vi*stride+slot]]
					influences.append({"bone":bind.bone,"point":bind.inverse*vertices[vi],"weight":weight})
					if str(rig.get_bone_name(bind.bone))=="bowstring":string_weight+=weight
					if weight>largest:largest=weight;dominant=bind.bone
				var name_:=str(rig.get_bone_name(dominant)) if dominant>=0 else ""
				var point:={"mesh":str(node.name),"surface":surface,"vertex":vi,"influences":influences}
				if string_weight>0:result.string.append(point)
				if name_.begins_with("finger") and name_.ends_with("-3.L"):result.draw_fingers.append(point)
				if name_.begins_with("finger") and name_.ends_with("-3.R"):result.grip_fingers.append(point)
	for child in node.get_children():_collect(child,rig,result)

static func skin(points: Array,motion: Node) -> PackedVector3Array:
	var result:=PackedVector3Array()
	for vertex in points:
		var point:=Vector3.ZERO
		for influence in vertex.influences:point+=(motion.last_globals[influence.bone]*influence.point)*influence.weight
		result.append(point)
	return result

static func max_step(before: PackedVector3Array,after: PackedVector3Array) -> Dictionary:
	var worst:=-1;var largest:=0.
	for i in mini(before.size(),after.size()):
		var delta:=before[i].distance_to(after[i])
		if delta>largest:largest=delta;worst=i
	return {"maximum_m":largest,"sample_index":worst}

static func minimum_gap(points: PackedVector3Array,target: Vector3) -> float:
	var gap:=INF
	for point in points:gap=minf(gap,point.distance_to(target))
	return gap
