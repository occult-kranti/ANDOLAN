extends SceneTree
const Layers := preload("res://scripts/rama_upper_hair_layers.gd")
const Secondary := preload("res://scripts/rama_secondary_motion.gd")
const Finish := preload("res://scripts/rama_surface_finish.gd")
var checks: Array[Dictionary] = []
var output := ""
var geometry_output := ""

func check(label: String, okay: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":okay,"details":details})
	print("PASS " if okay else "FAIL ",label)

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
		if arg.begins_with("--geometry="): geometry_output = arg.trim_prefix("--geometry=")
	call_deferred("run")

func _pose_list(rig: Skeleton3D) -> Array:
	var result := []
	for bone in rig.get_bone_count(): result.append(rig.get_bone_pose(bone))
	return result

func _poses_approx(rig: Skeleton3D, poses: Array) -> bool:
	for bone in rig.get_bone_count():
		if not rig.get_bone_pose(bone).is_equal_approx(poses[bone]): return false
	return true

func _stored(resource: Resource) -> Dictionary:
	var result := {}
	for property in resource.get_property_list():
		if int(property.usage)&PROPERTY_USAGE_STORAGE: result[property.name] = resource.get(property.name)
	return result

func run() -> void:
	var visual := load("res://assets/heroes/rama-hero.glb").instantiate() as Node3D
	root.add_child(visual)
	var secondary := Secondary.new(); visual.add_child(secondary)
	var finish := Finish.new(); visual.add_child(finish)
	check("actual imported secondary owner binds",secondary.configure(visual))
	check("actual imported G1 finish and maps bind",finish.configure(visual))
	var candidate := Layers.new(); visual.add_child(candidate)
	var rigs: Array[Skeleton3D] = []; var meshes: Array[MeshInstance3D] = []
	candidate._collect(visual,rigs,meshes)
	check("one actual 164-bone rig",rigs.size() == 1 and rigs[0].get_bone_count() == 164)
	var rig := rigs[0]; var head := rig.find_bone("head")
	var rest := rig.get_bone_global_rest(head)
	var before := _pose_list(rig)
	var source_meshes := []; var source_materials := []; var source_records := []
	for mesh in meshes:
		source_meshes.append(mesh.mesh)
		var materials := []
		for surface in mesh.mesh.get_surface_count():
			var material := mesh.get_active_material(surface)
			materials.append(material); source_records.append([material,_stored(material)])
		source_materials.append(materials)
	var child_count := rig.get_child_count()
	check("reject missing visual before allocation",not candidate.configure(null))
	check("actual rig admits separate seven-layer helper",candidate.configure(visual))
	await process_frame
	check("helper writes no actual bone poses",_pose_list(rig) == before)
	check("one attachment and one mesh only",rig.get_child_count() == child_count+1 and candidate._attachment.get_child_count() == 1)
	check("no skeleton override or frame callbacks",not candidate._attachment.override_pose and not candidate.is_processing() and not candidate.is_physics_processing())
	check("exact bounded geometry",candidate.report().triangles == 1904 and candidate.report().vertices == 1085 and candidate.report().extra_materials == 0,candidate.report())
	var geometry: Array = candidate._mesh.mesh.surface_get_arrays(0)
	var finite := true; var frames := true; var mask := true; var uv_ok := true
	var max_frame_dot := 0.0
	var vertices := []; var normals := []; var uv := []; var tangent_data := []
	var low := Vector3(INF,INF,INF); var high := Vector3(-INF,-INF,-INF)
	for i in geometry[Mesh.ARRAY_VERTEX].size():
		var p: Vector3 = geometry[Mesh.ARRAY_VERTEX][i]
		var n: Vector3 = geometry[Mesh.ARRAY_NORMAL][i]
		var u: Vector2 = geometry[Mesh.ARRAY_TEX_UV][i]
		var t := Vector3(geometry[Mesh.ARRAY_TANGENT][4*i],geometry[Mesh.ARRAY_TANGENT][4*i+1],geometry[Mesh.ARRAY_TANGENT][4*i+2])
		var sign_value: float = geometry[Mesh.ARRAY_TANGENT][4*i+3]
		finite = finite and p.is_finite() and n.is_finite() and u.is_finite() and t.is_finite() and is_finite(sign_value)
		# ArrayMesh octahedral packing quantizes normal and tangent independently.
		# Bound the returned frame to .001 (~.057 degrees), not bitwise equality.
		max_frame_dot = maxf(max_frame_dot,absf(n.dot(t)))
		frames = frames and absf(n.length()-1.0) < .0001 and absf(t.length()-1.0) < .0001 and absf(n.dot(t)) < .001 and absf(sign_value) == 1.0
		mask = mask and geometry[Mesh.ARRAY_COLOR][i] == Color(1,1,1,0)
		uv_ok = uv_ok and u.x >= 0 and u.x <= 1 and u.y >= 0 and u.y <= 1
		var model := rest*p; low = low.min(model); high = high.max(model)
		vertices.append([model.x,model.y,model.z]); normals.append([n.x,n.y,n.z]); uv.append([u.x,u.y]); tangent_data.append([t.x,t.y,t.z,sign_value])
	check("finite positions UV normals tangents",finite)
	check("unit orthogonal handed normal-map frames after ArrayMesh packing",frames,{"maximum_normal_tangent_dot":max_frame_dot,"dot_limit":.001})
	check("all new upper-hair vertices use anchored white RGB alpha0",mask)
	check("all source-compatible UVs bounded",uv_ok)
	check("new tier stays above low nape and behind face",low.y > 1.66 and high.y < 1.805 and high.z < .015 and low.x > -.16 and high.x < .16,{"min":[low.x,low.y,low.z],"max":[high.x,high.y,high.z]})
	var nondegenerate := true; var min_area := INF
	for i in range(0,geometry[Mesh.ARRAY_INDEX].size(),3):
		var a: Vector3 = geometry[Mesh.ARRAY_VERTEX][geometry[Mesh.ARRAY_INDEX][i]]
		var b: Vector3 = geometry[Mesh.ARRAY_VERTEX][geometry[Mesh.ARRAY_INDEX][i+1]]
		var c: Vector3 = geometry[Mesh.ARRAY_VERTEX][geometry[Mesh.ARRAY_INDEX][i+2]]
		var area := (b-a).cross(c-a).length()*.5
		min_area = minf(min_area,area); nondegenerate = nondegenerate and area > 1e-12
	check("every closed layer triangle has nonzero area",nondegenerate,{"minimum_area_m2":min_area})
	var preserved := true
	for i in meshes.size():
		preserved = preserved and meshes[i].mesh == source_meshes[i]
		for surface in meshes[i].mesh.get_surface_count(): preserved = preserved and meshes[i].get_active_material(surface) == source_materials[i][surface]
	for record in source_records: preserved = preserved and _stored(record[0]) == record[1]
	check("all existing mesh and material resources remain exact",preserved)
	check("finish and secondary owners remain admitted",finish.configure(visual) and secondary.configured)
	var mesh_id := candidate._mesh.get_instance_id(); var resource_id := candidate._mesh.mesh.get_instance_id()
	var stable := true
	for unused in 100: stable = stable and candidate.configure(visual) and candidate._mesh.get_instance_id() == mesh_id and candidate._mesh.mesh.get_instance_id() == resource_id
	check("100 repeated configurations allocate no new mesh or attachment",stable)
	var other := Layers.new(); visual.add_child(other)
	check("second layer owner cannot stack",not other.configure(visual)); other.free()
	var head_pose := rig.get_bone_pose(head)
	var follow := true
	for angle in [-.4,0.,.4]:
		rig.set_bone_pose_rotation(head,Quaternion(Vector3.UP,angle)*head_pose.basis.get_rotation_quaternion())
		rig.force_update_all_bone_transforms()
		await process_frame
		follow = follow and candidate._attachment.global_transform.is_equal_approx(rig.global_transform*rig.get_bone_global_pose(head))
	check("actual head yaw follows bone with no detached offset",follow)
	rig.set_bone_pose(head,head_pose); rig.force_update_all_bone_transforms(); await process_frame
	check("fixture restores every bone pose after quaternion roundtrip",_poses_approx(rig,before))
	var mesh_reference: WeakRef = weakref(candidate._mesh)
	candidate.release()
	check("release removes only owned attachment and mesh",rig.get_child_count() == child_count and mesh_reference.get_ref() == null and not visual.has_meta(Layers.OWNER_META))
	check("release leaves source poses and existing material owner intact",_poses_approx(rig,before) and finish.configure(visual))
	check("released helper can reconfigure",candidate.configure(visual))
	var transferred := candidate._attachment
	transferred.reparent(root)
	check("transferred attachment invalidates repeated configure",not candidate.configure(visual))
	candidate.release()
	check("release preserves attachment transferred to another owner",is_instance_valid(transferred) and transferred.get_parent() == root)
	transferred.free()
	finish.release(); secondary.restore_materials(); visual.free()
	if not geometry_output.is_empty():
		var file := FileAccess.open(geometry_output,FileAccess.WRITE)
		file.store_string(JSON.stringify({"source_glb_sha256":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb"),"helper_sha256":FileAccess.get_sha256("res://scripts/rama_upper_hair_layers.gd"),"guides_sha256":FileAccess.get_sha256(Layers.DATA_PATH),"rest_vertices":vertices,"indices":Array(geometry[Mesh.ARRAY_INDEX]),"normals":normals,"uv":uv,"tangents":tangent_data},"\t")+"\n")
	var passed := true
	for item in checks: passed = passed and item.passed
	var report := {"passed":passed,"checks":checks,"engine":Engine.get_version_info().string,"helper_sha256":FileAccess.get_sha256("res://scripts/rama_upper_hair_layers.gd"),"guides_sha256":FileAccess.get_sha256(Layers.DATA_PATH),"scope":"Actual imported rig, geometry/frame, material sharing and release checks; no rendered, whole-action contact or hardware claim."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE); file.store_string(JSON.stringify(report,"\t")+"\n")
	quit(0 if passed else 1)
