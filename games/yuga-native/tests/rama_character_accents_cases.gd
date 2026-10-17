extends SceneTree
const Accents := preload("res://scripts/rama_character_accents.gd")
const Secondary := preload("res://scripts/rama_secondary_motion.gd")
var checks: Array[Dictionary] = []
var output := ""
var resources := false

func check(label: String, okay: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":okay,"details":detail})
	print("PASS " if okay else "FAIL ", label)

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
		if argument == "--resources": resources = true
	call_deferred("run")

func fixture() -> Dictionary:
	var visual := Node3D.new()
	root.add_child(visual)
	var rig := Skeleton3D.new()
	visual.add_child(rig)
	for index in Accents.REQUIRED_BONES: rig.add_bone("head" if index == 0 else "fixture_"+str(index))
	rig.set_bone_rest(0, Transform3D(Basis.IDENTITY, Accents.EXPECTED_HEAD_ORIGIN))
	rig.reset_bone_pose(0)
	var original := StandardMaterial3D.new()
	original.resource_name = "Swept black hair"
	var material := ShaderMaterial.new()
	material.shader = Accents.HAIR_SHADER
	material.resource_name = "Swept black hair · bounded secondary"
	material.set_shader_parameter("secondary_offset", Vector3(.01, .006, -.005))
	var mesh := MeshInstance3D.new()
	var geometry := ArrayMesh.new()
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3.ZERO, Vector3.RIGHT, Vector3.UP])
	geometry.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	geometry.surface_set_material(0, original)
	mesh.mesh = geometry
	mesh.set_surface_override_material(0, material)
	rig.add_child(mesh)
	var accent := Accents.new()
	visual.add_child(accent)
	return {"visual":visual,"rig":rig,"mesh":mesh,"original":original,"material":material,"accent":accent}

func run() -> void:
	var f := fixture()
	var a = f.accent
	var source_arrays: Array = f.mesh.mesh.surface_get_arrays(0).duplicate(true)
	check("reject missing visual", not a.configure(null))
	check("configure valid bounded candidate", a.configure(f.visual))
	check("idempotent configure allocates no second attachment", a.configure(f.visual) and f.rig.get_child_count() == 2)
	var second := Accents.new()
	f.visual.add_child(second)
	check("reject competing accent owner", not second.configure(f.visual))
	second.free()
	check("exact finite geometry budget", a.report().triangles == 800 and a.report().vertices == 476 and a.report().triangles <= 1536)
	var data: Array = a._mesh.mesh.surface_get_arrays(0)
	var finite := true
	var normal_valid := true
	var anchored := true
	var tangent_valid := true
	var bounds := AABB(Vector3(-.14, 1.65, .01), Vector3(.28, .185, .125))
	var all_inside := true
	for index in data[Mesh.ARRAY_VERTEX].size():
		var point: Vector3 = data[Mesh.ARRAY_VERTEX][index]
		var normal: Vector3 = data[Mesh.ARRAY_NORMAL][index]
		var uv: Vector2 = data[Mesh.ARRAY_TEX_UV][index]
		var tangent := Vector3(data[Mesh.ARRAY_TANGENT][index*4], data[Mesh.ARRAY_TANGENT][index*4+1], data[Mesh.ARRAY_TANGENT][index*4+2])
		finite = finite and point.is_finite() and normal.is_finite() and uv.is_finite() and tangent.is_finite()
		normal_valid = normal_valid and absf(normal.length()-1.0)<.001
		tangent_valid = tangent_valid and absf(tangent.length()-1.0)<.001 and absf(tangent.dot(normal))<.001
		anchored = anchored and data[Mesh.ARRAY_COLOR][index] == Color(1, 1, 1, 0)
		all_inside = all_inside and bounds.has_point(f.rig.get_bone_global_rest(0)*point)
	check("all generated channels finite", finite)
	check("unit normals and orthogonal unit tangents", normal_valid and tangent_valid)
	check("all hair masks anchored; secondary offset cannot displace them", anchored)
	check("geometry remains in measured temple envelope", all_inside)
	var nondegenerate := true
	for index in range(0, data[Mesh.ARRAY_INDEX].size(), 3):
		var p: Vector3 = data[Mesh.ARRAY_VERTEX][data[Mesh.ARRAY_INDEX][index]]
		var q: Vector3 = data[Mesh.ARRAY_VERTEX][data[Mesh.ARRAY_INDEX][index+1]]
		var r: Vector3 = data[Mesh.ARRAY_VERTEX][data[Mesh.ARRAY_INDEX][index+2]]
		nondegenerate = nondegenerate and (q-p).cross(r-p).length_squared() > 1e-20
	check("every emitted triangle has nonzero area", nondegenerate)
	var seam_closed := true
	for strand in Accents.WISPS:
		for ring in Accents.SEGMENTS+1:
			var first := strand*(Accents.SEGMENTS+1)*Accents.RING_VERTICES + ring*Accents.RING_VERTICES
			seam_closed = seam_closed and data[Mesh.ARRAY_VERTEX][first].is_equal_approx(data[Mesh.ARRAY_VERTEX][first+Accents.SIDES]) and data[Mesh.ARRAY_TEX_UV][first].x == 0.0 and data[Mesh.ARRAY_TEX_UV][first+Accents.SIDES].x == 1.0
	check("circumferential UV seam duplicates exact positions", seam_closed)
	check("native bounded distance and hysteresis; no frame callbacks", a._mesh.visibility_range_end == 8.0 and a._mesh.visibility_range_end_margin == 1.0 and not a.is_processing() and not a.is_physics_processing())
	check("shared current hair material without material writes", a._mesh.get_active_material(0) == f.material and a._mesh.mesh.surface_get_material(0) == f.original and f.material.get_shader_parameter("secondary_offset") == Vector3(.01, .006, -.005))
	check("source body arrays untouched", source_arrays == f.mesh.mesh.surface_get_arrays(0))
	check("attachment cannot override any bone pose", not a._attachment.override_pose and a._attachment.bone_name == "head" and a._mesh.skin == null)
	f.visual.transform = Transform3D(Basis.from_euler(Vector3(.2, -.4, .1)).scaled(Vector3(1.2, 1.2, 1.2)), Vector3(4, 2, -3))
	f.rig.transform = Transform3D(Basis.from_euler(Vector3(-.1, .3, .07)), Vector3(.2, .3, .4))
	var poses_preserved := true
	var follows := true
	for angles in [Vector3.ZERO, Vector3(.3, -.7, .2), Vector3(-.4, .8, -.25)]:
		var rotation := Quaternion.from_euler(angles)
		f.rig.set_bone_pose_rotation(0, rotation)
		f.rig.force_update_all_bone_transforms()
		await process_frame
		var expected: Transform3D = f.rig.global_transform*f.rig.get_bone_global_pose(0)
		follows = follows and a._attachment.global_transform.is_equal_approx(expected)
		poses_preserved = poses_preserved and f.rig.get_bone_pose_rotation(0).is_equal_approx(rotation)
	check("head follows real skeleton under rotated translated scaled parents", follows)
	check("head pose unchanged by accents across pose samples", poses_preserved)
	var material_id: int = f.material.get_instance_id()
	a.release()
	check("release removes exactly the owned attachment", not a.configured and f.rig.get_child_count() == 1 and not f.visual.has_meta(Accents.OWNER_META))
	check("release preserves body and material identity", f.mesh.get_active_material(0).get_instance_id() == material_id and f.rig.get_bone_count() == Accents.REQUIRED_BONES)
	a.release()
	check("repeated release is safe", not a.configured)
	f.rig.set_bone_rest(0, Transform3D(Basis.IDENTITY, Vector3.ZERO))
	check("reject unrelated head geometry", not a.configure(f.visual))
	f.rig.set_bone_rest(0, Transform3D(Basis.IDENTITY, Accents.EXPECTED_HEAD_ORIGIN))
	f.material.resource_name = "foreign material"
	check("reject unowned hair material", not a.configure(f.visual))
	f.material.resource_name = "Swept black hair · bounded secondary"
	var extra := Skeleton3D.new()
	f.visual.add_child(extra)
	check("reject multiple rigs", not a.configure(f.visual))
	extra.free()
	check("reconfigure after release retains ownership contract", a.configure(f.visual))
	f.visual.free()
	if resources: await actual_resource()
	var passed := checks.all(func(row): return row.passed)
	var report := {"passed":passed,"count":checks.size(),"checks":checks,"resources":resources,"scope":"Geometry, ownership, bounded LOD and actual bone following. Actual appearance requires matched render acceptance."}
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report, "\t")+"\n")
		else: push_error("Cannot write receipt"); quit(1); return
	print(JSON.stringify(report))
	quit(0 if passed else 1)

func actual_resource() -> void:
	var visual := load("res://assets/heroes/rama-hero.glb").instantiate() as Node3D
	root.add_child(visual)
	var secondary := Secondary.new()
	visual.add_child(secondary)
	check("actual authored secondary owner configures", secondary.configure(visual))
	var accent := Accents.new()
	visual.add_child(accent)
	var rigs: Array[Skeleton3D] = []
	var meshes: Array[MeshInstance3D] = []
	accent._collect(visual, rigs, meshes)
	var bones := []
	for index in rigs[0].get_bone_count(): bones.append(rigs[0].get_bone_pose(index))
	var masks_before: Dictionary = secondary.report().duplicate(true)
	check("actual imported hero accepts four-wisp optional candidate", accent.configure(visual))
	await process_frame
	var unchanged := true
	for index in rigs[0].get_bone_count(): unchanged = unchanged and rigs[0].get_bone_pose(index).is_equal_approx(bones[index])
	check("all actual 164 bone poses remain unchanged", unchanged)
	check("actual secondary masks and bindings remain unchanged", secondary.report() == masks_before)
	check("actual head attachment agrees with imported rest transform", accent._attachment.global_transform.is_equal_approx(rigs[0].global_transform*rigs[0].get_bone_global_pose(rigs[0].find_bone("head"))))
	accent.release()
	secondary.restore_materials()
	visual.free()
