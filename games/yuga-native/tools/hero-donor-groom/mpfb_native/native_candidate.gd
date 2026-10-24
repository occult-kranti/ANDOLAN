extends RefCounted
## Isolated attachment adapter: same production skeleton/motion, no extra owner.
## The original body's exact nine-nape mask comes from masked_glb.py.

static func first(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := first(child, kind)
		if found: return found
	return null

static func load_glb(path: String) -> Node3D:
	var document := GLTFDocument.new()
	var state := GLTFState.new()
	if document.append_from_file(path, state) != OK: return null
	return document.generate_scene(state) as Node3D

static func attach(model: Node3D, hair_path: String) -> Dictionary:
	var rig := first(model, "Skeleton3D") as Skeleton3D
	var hair := load_glb(hair_path)
	if not rig or not hair: return {"ok": false, "reason": "Missing model or hair rig"}
	model.get_tree().root.add_child(hair)
	# Imported hair shares the model's authored coordinates. Place its carrier
	# in the model's current world frame BEFORE transferring the mesh, so a
	# hero spawned away from origin receives the same local nape attachment.
	hair.global_transform = model.global_transform
	var carrier := first(hair, "Skeleton3D") as Skeleton3D
	var mesh := first(hair, "MeshInstance3D") as MeshInstance3D
	if not carrier or not mesh or not mesh.skin:
		hair.free()
		return {"ok": false, "reason": "Missing hair skin carrier"}
	var rest_error := 0.0
	var basis_error := 0.0
	var all_names := rig.get_bone_count() == 164 and carrier.get_bone_count() == 164
	for index in carrier.get_bone_count():
		var name_ := carrier.get_bone_name(index)
		var bone := rig.find_bone(name_)
		if bone < 0:
			all_names = false
			continue
		var a := carrier.get_bone_global_rest(index)
		var b := rig.get_bone_global_rest(bone)
		rest_error = maxf(rest_error, a.origin.distance_to(b.origin))
		for axis in 3: basis_error = maxf(basis_error, a.basis[axis].distance_to(b.basis[axis]))
	# Carrier float32 round-trip error is measured, not called exact. It is
	# discarded below: all native inverse binds come from the canonical rig.
	# 164 chained float32 transforms have an explicit 0.1mm/1e-4 budget.
	if not all_names or rest_error > .0001 or basis_error > .0001:
		hair.free()
		return {"ok": false, "reason": "Carrier rest differs from exact Rama rig", "rest_error_m": rest_error, "basis_error": basis_error, "all_names": all_names}
	var skin := Skin.new()
	for index in mesh.skin.get_bind_count():
		var name_ := mesh.skin.get_bind_name(index)
		if str(name_).is_empty(): name_ = carrier.get_bone_name(mesh.skin.get_bind_bone(index))
		if rig.find_bone(name_) < 0:
			hair.free()
			return {"ok": false, "reason": "Unknown skin bind"}
		var native_bone := rig.find_bone(name_)
		var mesh_to_rig := rig.global_transform.affine_inverse() * mesh.global_transform
		skin.add_named_bind(name_, rig.get_bone_global_rest(native_bone).affine_inverse() * mesh_to_rig)
	mesh.reparent(rig, true)
	mesh.skin = skin
	mesh.skeleton = mesh.get_path_to(rig)
	mesh.name = "MPFB donor cards isolated candidate"
	# R1 alpha-hash produced visible stippling without TAA. This single material
	# correction uses scissor + the fixture's 2xMSAA coverage; geometry is fixed.
	var material := mesh.mesh.surface_get_material(0).duplicate() as StandardMaterial3D
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	material.alpha_scissor_threshold = .3
	material.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE
	material.alpha_antialiasing_edge = .3
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.set_surface_override_material(0, material)
	var result := {"ok": true, "mesh": mesh, "rest_error_m": rest_error, "basis_error": basis_error,
		"bones": rig.get_bone_count(), "binds": skin.get_bind_count(), "separate_animation_owner": false,
		"inverse_bind_source": "Canonical native bone global rest; exported carrier binds discarded",
		"local_material": "Alpha scissor .3, MSAA alpha-to-coverage .3, double sided, same atlas"}
	# The transferred mesh survives; the duplicate skeleton is never animated.
	hair.free()
	return result

static func points(mesh: MeshInstance3D, rig: Skeleton3D) -> Array:
	var result: Array = []
	for surface in mesh.mesh.get_surface_count():
		var arrays := mesh.mesh.surface_get_arrays(surface)
		var positions: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var joints: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
		var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
		var stride := joints.size() / positions.size()
		for index in positions.size():
			var influences: Array = []
			for slot in stride:
				var weight: float = weights[index * stride + slot]
				if weight <= 0: continue
				var binding: int = joints[index * stride + slot]
				influences.append({"bone": rig.find_bone(mesh.skin.get_bind_name(binding)),
					"point": mesh.skin.get_bind_pose(binding) * positions[index], "weight": weight})
			result.append({"influences": influences})
	return result
