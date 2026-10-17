extends SceneTree
## Small real-engine Mesh/Skin/Skeleton fixture; no imported hero/GPU claim.
const Binding = preload("res://scripts/rama_lod_binding.gd")
var checks: Array[Dictionary] = []
var output := ""

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label, "passed":passed, "details":details})
	print("PASS " if passed else "FAIL ", label)

func _arrays() -> Array:
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-.2,0,0),Vector3(.2,0,0),Vector3(.2,1.9,0),Vector3(-.2,1.9,0)])
	arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.FORWARD,Vector3.FORWARD,Vector3.FORWARD,Vector3.FORWARD])
	arrays[Mesh.ARRAY_COLOR] = PackedColorArray([Color(1,1,1,0),Color(1,1,1,0),Color(1,1,1,.7),Color.WHITE])
	arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2.ZERO,Vector2.RIGHT,Vector2.ONE,Vector2.DOWN])
	arrays[Mesh.ARRAY_BONES] = PackedInt32Array([2,0,0,0,2,0,0,0,2,0,0,0,2,0,0,0])
	arrays[Mesh.ARRAY_WEIGHTS] = PackedFloat32Array([1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0])
	arrays[Mesh.ARRAY_INDEX] = PackedInt32Array([0,1,2,0,2,3])
	return arrays

func _mesh(label: String, material_name: String) -> MeshInstance3D:
	var material := StandardMaterial3D.new()
	material.resource_name = material_name
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, _arrays())
	mesh.surface_set_material(0, material)
	var instance := MeshInstance3D.new()
	instance.name = label
	instance.mesh = mesh
	return instance

func _skin(rig: Skeleton3D, reverse := false) -> Skin:
	var skin := Skin.new()
	for count in rig.get_bone_count():
		var index := 163-count if reverse else count
		skin.add_bind(index, rig.get_bone_global_rest(index).affine_inverse())
	return skin

func _model() -> Node3D:
	var model := Node3D.new()
	model.name = "Model"
	model.transform = Transform3D(Basis(Vector3.UP,.2),Vector3(.1,.2,.3))
	var rig := Skeleton3D.new()
	rig.name = "Skeleton3D"
	rig.position = Vector3(.2,.05,.1)
	model.add_child(rig)
	for index in range(164):
		rig.add_bone("root" if index == 0 else ("wrist.R" if index == 2 else "bone"+str(index)))
		if index > 0: rig.set_bone_parent(index,0)
		rig.set_bone_rest(index,Transform3D(Basis.IDENTITY,Vector3(0,float(index)*.001,0)))
	for entry in [["RamaHero","Cobalt handwoven silk"],["RamaBow","Worked warm gold"],["RamaFace","Rama warm skin"]]:
		var instance := _mesh(entry[0],entry[1])
		instance.transform = rig.transform * Transform3D(Basis.IDENTITY,Vector3(.05,.1,0))
		instance.skin = _skin(rig)
		model.add_child(instance)
		instance.skeleton = NodePath("../Skeleton3D")
	return model

func _own(node: Node, owner: Node) -> void:
	for child in node.get_children():
		child.owner = owner
		_own(child,owner)

func _scene(change := "") -> PackedScene:
	var model := _model()
	var rig: Skeleton3D = model.get_node("Skeleton3D")
	var body: MeshInstance3D = model.get_node("RamaHero")
	if change == "transform": body.position.x += .02
	if change == "rest": rig.set_bone_rest(3,Transform3D(Basis.IDENTITY,Vector3(.1,0,0)))
	if change == "joint_order": body.skin = _skin(rig,true)
	if change == "bind_pose": body.skin.set_bind_pose(0,Transform3D(Basis.IDENTITY,Vector3(.1,0,0)))
	if change == "mask" or change == "missing_mask":
		var arrays := _arrays()
		if change == "mask": arrays[Mesh.ARRAY_COLOR][0] = Color(.2,1,1,.5)
		else: arrays[Mesh.ARRAY_COLOR] = null
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		mesh.surface_set_material(0,body.mesh.surface_get_material(0))
		body.mesh = mesh
	if change == "material": body.mesh.surface_get_material(0).resource_name = "Wrong material"
	if change == "extra_rig": model.add_child(Skeleton3D.new())
	if change == "missing_bow": model.get_node("RamaBow").free()
	_own(model,model)
	var scene := PackedScene.new()
	var error := scene.pack(model)
	if error != OK: push_error("Fixture pack failed")
	model.free()
	return scene

func _visual() -> Node3D:
	var visual := Node3D.new()
	visual.name = "HeroVisual"
	visual.transform = Transform3D(Basis(Vector3.UP,.6).scaled(Vector3.ONE*1.25),Vector3(3,2,4))
	visual.add_child(_model())
	root.add_child(visual)
	return visual

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _run() -> void:
	root.size = Vector2i(1280,720)
	var visual := _visual()
	var rig: Skeleton3D = visual.get_node("Model/Skeleton3D")
	var near: MeshInstance3D = visual.get_node("Model/RamaHero")
	var original_transform := near.global_transform
	var rest := rig.get_bone_rest(2)
	var pose := rig.get_bone_pose_position(2)
	var original_mesh := near.mesh
	var shared_override := ShaderMaterial.new()
	shared_override.resource_name = "Shared secondary override"
	near.set_surface_override_material(0,shared_override)
	var lod = Binding.new()
	visual.add_child(lod)
	var candidate := _scene()
	check("Two real164-bone skin candidates configure",lod.configure(visual,rig,[candidate,candidate]),lod.report())
	check("Exactly one live skeleton and164bones",lod.report().live_rigs == 1 and lod.report().live_bones == 164)
	check("Only four body/bow clones, two shared named skins",lod.report().owned_mesh_instances == 4 and lod.report().owned_skins == 2)
	check("Candidate faces omitted; one original face retained",lod.report().ignored_candidate_faces == 2 and visual.find_children("RamaFace","MeshInstance3D",true,false).size() == 1)
	var transformed := true
	var skin_order := true
	var bound := true
	var shared_material := true
	for instance in lod._owned:
		bound = bound and instance.get_node(instance.skeleton) == rig
		if String(instance.name).begins_with("RamaHero"):
			transformed = transformed and instance.global_transform.is_equal_approx(original_transform)
			shared_material = shared_material and instance.mesh.surface_get_material(0) == shared_override
		for i in instance.skin.get_bind_count():
			skin_order = skin_order and instance.skin.get_bind_name(i) == rig.get_bone_name(i) and instance.skin.get_bind_pose(i).is_equal_approx(rig.get_bone_global_rest(i).affine_inverse())
	check("Nested rotation/translation/scale preserved in world coordinates",transformed)
	check("All clones point at existing live rig",bound)
	check("Named skin bind order and inverse binds preserved",skin_order)
	check("Candidate materials remap to original override resource",shared_material)
	check("Near arrays and imported candidate material stay immutable",near.mesh == original_mesh and _candidate_material_name(candidate) == "Cobalt handwoven silk")
	check("Configure is idempotent with fixed owned resources",lod.configure(visual,rig,[candidate,candidate]) and lod.report().owned_mesh_instances == 4 and lod.report().owned_skins == 2)
	var camera := Camera3D.new()
	root.add_child(camera)
	camera.keep_aspect = Camera3D.KEEP_HEIGHT
	var center: Vector3 = rig.global_transform * lod._bounds.get_center()
	camera.global_position = center + Vector3(0,0,100)
	check("Actual camera selects far",lod.update(camera,.2) and lod.report().level == 2 and lod.report().visible_levels == [2])
	check("Face remains visible while body level changes",visual.get_node("Model/RamaFace").visible)
	rig.set_bone_pose_position(2,pose+Vector3(.1,0,0))
	check("Existing live pose changes without rest/skeleton mutation",rig.get_bone_pose_position(2) != pose and rig.get_bone_rest(2).is_equal_approx(rest) and lod.report().live_rigs == 1)
	lod.reset("death")
	check("Death reset returns to near without removing face",lod.report().level == 0 and lod.report().visible_levels == [0] and visual.get_node("Model/RamaFace").visible)
	check("Invalid camera falls back near explicitly",lod.update(null,.2) and lod.report().level == 0 and lod.report().visible_levels == [0])
	var stable := true
	for i in range(100): stable = stable and lod.update(camera,.016) and lod.report().owned_mesh_instances == 4 and lod.report().live_rigs == 1
	check("100 updates keep bounded mesh/skin/rig resources",stable)
	lod.dispose()
	check("Dispose restores source visibility and removes owned meshes",near.visible and lod.report().owned_mesh_instances == 0 and not lod.configured and visual.find_children("RamaFace","MeshInstance3D",true,false).size() == 1)
	visual.free()
	for defect in ["transform","rest","joint_order","bind_pose","mask","missing_mask","material","extra_rig","missing_bow"]:
		var v := _visual()
		var r: Skeleton3D = v.get_node("Model/Skeleton3D")
		var component = Binding.new(); v.add_child(component)
		check("Rejected candidate: " + defect,not component.configure(v,r,[_scene(defect)]) and component.report().owned_mesh_instances == 0 and component.report().levels == 1 and not component.report().errors.is_empty(),component.report())
		v.free()
	var v := _visual()
	var r: Skeleton3D = v.get_node("Model/Skeleton3D")
	var transaction = Binding.new();v.add_child(transaction)
	check("Rejected second candidate rolls back first atomically",not transaction.configure(v,r,[_scene(),_scene("mask")]) and transaction.report().owned_mesh_instances == 0 and transaction.report().live_rigs == 1 and v.get_node("Model/RamaHero").visible)
	transaction.dispose()
	check("No candidate reports explicit near-only result",not transaction.configure(v,r,[]) and transaction.report().levels == 1 and transaction.report().last_reason.contains("no reviewed LODs"))
	transaction.dispose()
	check("Missing candidate path reports rejection",not transaction.configure(v,r,["res://does-not-exist.glb"]) and transaction.report().owned_mesh_instances == 0 and not transaction.report().errors.is_empty())
	transaction.dispose()
	check("More than two levels rejected before allocation",not transaction.configure(v,r,[_scene(),_scene(),_scene()]) and transaction.report().owned_mesh_instances == 0)
	transaction.dispose()
	for i in range(100): transaction.configure(null,null,[])
	check("Repeated rejected configure has bounded error history",transaction.report().errors.size() <= 8)
	v.free()
	for missing in ["rig","near"]:
		var actor := _visual()
		var existing: Skeleton3D = actor.get_node("Model/Skeleton3D")
		var component = Binding.new();actor.add_child(component)
		component.configure(actor,existing,[_scene(),_scene()])
		if missing == "rig": existing.free()
		else: actor.get_node("Model/RamaHero").free()
		check("Freed " + missing + " disposes owned levels safely",not component.update(camera,.1) and not component.configured and component.report().owned_mesh_instances == 0)
		actor.free()
	# Actual-world teardown exposed a missing lifecycle case: the visual
	# parent removes the helper before its later-added sibling LOD meshes.
	# Active parent teardown must not free those siblings during that traversal.
	for whole_visual in [true,false]:
		var actor := _visual()
		var existing: Skeleton3D = actor.get_node("Model/Skeleton3D")
		var component = Binding.new();actor.add_child(component)
		component.configure(actor,existing,[_scene(),_scene()])
		var clone_refs: Array[WeakRef] = []
		var resource_refs: Array[WeakRef] = []
		for instance in component._owned:
			clone_refs.append(weakref(instance))
			resource_refs.append(weakref(instance.mesh))
		for skin in component._named_skins.values(): resource_refs.append(weakref(skin))
		if whole_visual: actor.free()
		else: component.queue_free()
		await process_frame
		await process_frame
		var clones_released := true
		var resources_released := true
		for reference in clone_refs: clones_released = clones_released and reference.get_ref() == null
		for reference in resource_refs: resources_released = resources_released and reference.get_ref() == null
		var label := "Whole visual parent teardown" if whole_visual else "Helper-only queued teardown"
		check(label + " releases every owned clone",clones_released)
		check(label + " releases owned meshes and named skins",resources_released)
		if not whole_visual:
			check("Helper-only teardown restores near and retains original face/rig",actor.get_node("Model/RamaHero").visible and actor.get_node("Model/RamaFace").visible and actor.get_node("Model/Skeleton3D") == existing)
			actor.free()
	camera.free()
	var passed := true
	for result in checks: passed = passed and result.passed
	var report := {"passed":passed,"total":checks.size(),"checks":checks,"limits":["Actual engine objects and skin paths are tested; no final hero LOD was imported or visually accepted.","Dummy headless rendering does not establish pose pixels, VRAM residency or GPU performance."]}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify(report))
	quit(0 if passed else 1)

func _candidate_material_name(scene: PackedScene) -> String:
	var instance := scene.instantiate()
	var label: String = instance.get_node("RamaHero").mesh.surface_get_material(0).resource_name
	instance.free()
	return label
