extends Node
## Optional reviewed mesh levels, driven by ONE existing Skeleton3D.
## Imported LOD skeletons/animators/face nodes never enter the live scene tree.
## Configure before surface/secondary calibration so every level receives it.
const Selector = preload("res://scripts/rama_visual_lod.gd")
const REQUIRED_BONES := 164
const MAX_CANDIDATES := 2
const MESH_NAMES := ["RamaHero", "RamaBow"]
const REST_EPSILON := 0.0001
const MASK_MATERIALS := ["Cobalt handwoven silk", "Cobalt lotus brocade", "Worked warm gold", "Swept black hair"]

var configured := false
var level := 0
var _visual: Node3D
var _skeleton: Skeleton3D
var _selector = Selector.new()
var _near: Dictionary = {}
var _near_visibility: Dictionary = {}
var _levels: Array[Array] = []
var _owned: Array[MeshInstance3D] = []
var _named_skins: Dictionary = {}
var _errors: Array[String] = []
var _paths: Array[String] = []
var _bounds := AABB()
var _ignored_faces := 0
var _switches := 0
var _last_reason := "unconfigured"

func _error(message: String) -> void:
	if _errors.size() < 8: _errors.append(message)

func _collect(node: Node, meshes: Array[MeshInstance3D], rigs: Array[Skeleton3D]) -> void:
	if node is MeshInstance3D and node.mesh != null: meshes.append(node)
	if node is Skeleton3D: rigs.append(node)
	for child in node.get_children(): _collect(child, meshes, rigs)

func _relative(node: Node3D, ancestor: Node) -> Transform3D:
	if node == ancestor: return Transform3D.IDENTITY
	var result := node.transform
	var parent := node.get_parent()
	while parent != null and parent != ancestor:
		if parent is Node3D: result = parent.transform * result
		parent = parent.get_parent()
	return result

func _transform_matches(a: Transform3D, b: Transform3D) -> bool:
	return a.origin.distance_to(b.origin) <= REST_EPSILON and a.basis.x.distance_to(b.basis.x) <= REST_EPSILON and a.basis.y.distance_to(b.basis.y) <= REST_EPSILON and a.basis.z.distance_to(b.basis.z) <= REST_EPSILON

func _finite_transform(value: Transform3D) -> bool:
	return value.origin.is_finite() and value.basis.is_finite() and absf(value.basis.determinant()) > 0.000001

func _rig_matches(candidate: Skeleton3D) -> bool:
	if candidate.get_bone_count() != _skeleton.get_bone_count(): return false
	for i in _skeleton.get_bone_count():
		if candidate.get_bone_name(i) != _skeleton.get_bone_name(i) or candidate.get_bone_parent(i) != _skeleton.get_bone_parent(i): return false
		if not _transform_matches(candidate.get_bone_rest(i), _skeleton.get_bone_rest(i)): return false
	return true

func _skin_records(skin: Skin, rig: Skeleton3D) -> Dictionary:
	var records := {}
	if skin == null or skin.get_bind_count() != rig.get_bone_count(): return records
	for i in skin.get_bind_count():
		var bone_name := String(skin.get_bind_name(i))
		if bone_name.is_empty():
			var bone := skin.get_bind_bone(i)
			if bone < 0 or bone >= rig.get_bone_count(): return {}
			bone_name = String(rig.get_bone_name(bone))
		if rig.find_bone(bone_name) < 0 or records.has(bone_name) or not _finite_transform(skin.get_bind_pose(i)): return {}
		records[bone_name] = skin.get_bind_pose(i)
	return records

func _compatible_skin(source: Skin, candidate: Skin, candidate_rig: Skeleton3D) -> bool:
	var original := _skin_records(source, _skeleton)
	var other := _skin_records(candidate, candidate_rig)
	if original.size() != REQUIRED_BONES or other.size() != original.size(): return false
	for i in source.get_bind_count():
		var source_name := String(source.get_bind_name(i))
		var candidate_name := String(candidate.get_bind_name(i))
		if source_name.is_empty(): source_name = String(_skeleton.get_bone_name(source.get_bind_bone(i)))
		if candidate_name.is_empty(): candidate_name = String(candidate_rig.get_bone_name(candidate.get_bind_bone(i)))
		if source_name != candidate_name: return false
	for bone_name in original:
		if not other.has(bone_name) or not _transform_matches(original[bone_name], other[bone_name]): return false
	return true

func _named_skin(source: Skin) -> Skin:
	var records := _skin_records(source, _skeleton)
	if records.size() != REQUIRED_BONES: return null
	var skin := Skin.new()
	# Preserve the original bind ORDER: vertex joint values index this array.
	# Named resolution chooses the existing skeleton's bones without rewriting
	# source JOINTS/WEIGHTS or assuming the bind order equals bone order.
	for i in source.get_bind_count():
		var bone_name := source.get_bind_name(i)
		if String(bone_name).is_empty(): bone_name = _skeleton.get_bone_name(source.get_bind_bone(i))
		skin.add_named_bind(bone_name, source.get_bind_pose(i))
	return skin

func _material_matches(source: MeshInstance3D, candidate: MeshInstance3D) -> bool:
	if source.mesh.get_surface_count() != candidate.mesh.get_surface_count(): return false
	for i in source.mesh.get_surface_count():
		var a := source.mesh.surface_get_material(i)
		var b := candidate.mesh.surface_get_material(i)
		if a == null or b == null or a.resource_name != b.resource_name: return false
	return true

func _valid_masks(candidate: MeshInstance3D) -> bool:
	for surface in candidate.mesh.get_surface_count():
		var material := candidate.mesh.surface_get_material(surface)
		if material == null or not MASK_MATERIALS.has(material.resource_name): continue
		var arrays := candidate.mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var colors: PackedColorArray = arrays[Mesh.ARRAY_COLOR] if arrays[Mesh.ARRAY_COLOR] != null else PackedColorArray()
		if vertices.is_empty() or colors.size() != vertices.size(): return false
		for color in colors:
			if not is_finite(color.r) or not is_finite(color.g) or not is_finite(color.b) or not is_finite(color.a) or absf(color.r-1)>0.001 or absf(color.g-1)>0.001 or absf(color.b-1)>0.001 or color.a<0 or color.a>1: return false
	return true

func _candidate_scene(entry: Variant) -> PackedScene:
	if entry is PackedScene: return entry
	if not entry is String and not entry is StringName: return null
	var path := String(entry)
	if not path.begins_with("res://") or not ResourceLoader.exists(path, "PackedScene"): return null
	# A temporary imported scene must not remain a cache owner of duplicate
	# material image resources after its meshes are extracted/remapped.
	return ResourceLoader.load(path, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene

func _make_candidate(scene: PackedScene, label: String) -> Array[MeshInstance3D]:
	var result: Array[MeshInstance3D] = []
	var root := scene.instantiate()
	if not root is Node3D:
		if root: root.free()
		_error(label + ": root is not Node3D")
		return result
	var meshes: Array[MeshInstance3D] = []
	var rigs: Array[Skeleton3D] = []
	_collect(root, meshes, rigs)
	if rigs.size() != 1 or not _rig_matches(rigs[0]):
		_error(label + ": expected one matching164-bone rest hierarchy")
		root.free()
		return result
	var rig_transform := _relative(rigs[0], root)
	if not _finite_transform(rig_transform):
		_error(label + ": invalid candidate rig transform")
		root.free()
		return result
	var by_name := {}
	for candidate in meshes:
		if candidate.name == "RamaFace":
			_ignored_faces += 1
			continue
		if not MESH_NAMES.has(String(candidate.name)):
			_error(label + ": unexpected candidate mesh " + String(candidate.name))
			root.free()
			return result
		if by_name.has(String(candidate.name)):
			_error(label + ": duplicate named hero mesh")
			root.free()
			return result
		by_name[String(candidate.name)] = candidate
	if by_name.size() != MESH_NAMES.size():
		_error(label + ": required body/bow mesh missing")
		root.free()
		return result
	for mesh_name in MESH_NAMES:
		var candidate: MeshInstance3D = by_name[mesh_name]
		var original: MeshInstance3D = _near[mesh_name]
		var relation := rig_transform.affine_inverse() * _relative(candidate, root)
		var existing_relation := _skeleton.global_transform.affine_inverse() * original.global_transform
		if not candidate.mesh is ArrayMesh or not _finite_transform(relation) or not _transform_matches(relation, existing_relation) or not _material_matches(original, candidate) or not _valid_masks(candidate) or not _compatible_skin(original.skin, candidate.skin, rigs[0]):
			_error(label + ": mesh transform/material/mask/skin mismatch for " + mesh_name)
			for staged in result: staged.free()
			result.clear()
			root.free()
			return result
		var instance := MeshInstance3D.new()
		instance.name = mesh_name + "LOD" + label
		# Duplicate the mesh resource before replacing its material references.
		# This leaves the imported candidate/source resource immutable and lets
		# its unused duplicate textures go when the temporary scene is freed.
		var mesh := candidate.mesh.duplicate(false) as ArrayMesh
		for surface in mesh.get_surface_count(): mesh.surface_set_material(surface, original.get_active_material(surface))
		instance.mesh = mesh
		instance.skin = _named_skins[mesh_name]
		instance.transform = _visual.global_transform.affine_inverse() * _skeleton.global_transform * relation
		instance.cast_shadow = original.cast_shadow
		instance.layers = original.layers
		instance.extra_cull_margin = original.extra_cull_margin
		instance.lod_bias = original.lod_bias
		instance.material_override = original.material_override
		instance.material_overlay = original.material_overlay
		instance.visible = false
		result.append(instance)
	root.free()
	return result

func configure(visual: Node3D, skeleton: Skeleton3D, paths: Array = []) -> bool:
	if configured: return visual == _visual and skeleton == _skeleton and _levels.size() > 1
	_errors.clear()
	if not is_instance_valid(visual) or not is_instance_valid(skeleton) or not visual.is_inside_tree() or not visual.is_ancestor_of(skeleton) or skeleton.get_bone_count() != REQUIRED_BONES or not _finite_transform(visual.global_transform) or not _finite_transform(skeleton.global_transform):
		_error("configure: invalid visual/live164-bone skeleton")
		return false
	var meshes: Array[MeshInstance3D] = []
	var rigs: Array[Skeleton3D] = []
	_collect(visual, meshes, rigs)
	if rigs.size() != 1 or rigs[0] != skeleton:
		_error("configure: visual must contain only the supplied live rig")
		return false
	_visual = visual
	_skeleton = skeleton
	for instance in meshes:
		if MESH_NAMES.has(String(instance.name)):
			if _near.has(String(instance.name)):
				_error("configure: duplicate near mesh")
				_near.clear()
				return false
			_near[String(instance.name)] = instance
	if _near.size() != MESH_NAMES.size():
		_error("configure: expected named near body/bow meshes")
		_near.clear()
		return false
	var near_level: Array = []
	var first_bounds := true
	for mesh_name in MESH_NAMES:
		var instance: MeshInstance3D = _near[mesh_name]
		var named := _named_skin(instance.skin)
		if named == null:
			_error("configure: invalid near skin " + mesh_name)
			_near.clear(); _named_skins.clear()
			return false
		_named_skins[mesh_name] = named
		_near_visibility[mesh_name] = instance.visible
		near_level.append(instance)
		var relation := skeleton.global_transform.affine_inverse() * instance.global_transform
		var bounds := relation * instance.get_aabb()
		_bounds = bounds if first_bounds else _bounds.merge(bounds)
		first_bounds = false
	_levels.append(near_level)
	configured = true
	if paths.size() > MAX_CANDIDATES:
		_error("configure: at most two candidate levels")
		_last_reason = "near_only: candidate limit"
		return false
	var staged_levels: Array[Array] = []
	for index in paths.size():
		var scene := _candidate_scene(paths[index])
		if scene == null:
			_error("candidate " + str(index + 1) + ": missing/invalid PackedScene")
			break
		var candidate := _make_candidate(scene, str(index + 1))
		if candidate.size() != MESH_NAMES.size(): break
		staged_levels.append(candidate)
	if staged_levels.size() != paths.size():
		for row in staged_levels:
			for instance in row: instance.free()
		_last_reason = "near_only: rejected candidate transaction"
		return false
	for row in staged_levels:
		_levels.append(row)
		for instance in row:
			visual.add_child(instance)
			instance.skeleton = instance.get_path_to(skeleton)
			_owned.append(instance)
	for entry in paths: _paths.append(String(entry) if entry is String or entry is StringName else "in-memory fixture")
	_last_reason = "ready" if _levels.size() > 1 else "near_only: no reviewed LODs supplied"
	return _levels.size() > 1

func _apply_level(value: int) -> void:
	value = clampi(value, 0, _levels.size() - 1)
	if value != level: _switches += 1
	level = value
	for index in _levels.size():
		for mesh_index in _levels[index].size():
			var instance: MeshInstance3D = _levels[index][mesh_index]
			if is_instance_valid(instance): instance.visible = index == level and bool(_near_visibility[MESH_NAMES[mesh_index]])

func update(camera: Variant, delta: float = -1.0) -> bool:
	if not configured:
		_last_reason = "unavailable live visual/rig"
		return false
	if not is_instance_valid(_visual) or not is_instance_valid(_skeleton):
		dispose()
		_last_reason = "unavailable live visual/rig"
		return false
	for mesh_name in MESH_NAMES:
		if not is_instance_valid(_near.get(mesh_name)):
			dispose()
			_last_reason = "unavailable near source mesh"
			return false
	if delta == -1.0: delta = get_process_delta_time()
	var center := _skeleton.global_transform * _bounds.get_center()
	var height := (_skeleton.global_basis * Vector3.UP).length() * maxf(.01, _bounds.size.y + .16)
	_apply_level(_selector.choose_camera(camera, center, height, delta))
	return _levels.size() > 1

func reset(reason: String = "reset") -> void:
	_selector.reset()
	if configured: _apply_level(0)
	_last_reason = reason

func report() -> Dictionary:
	var rigs: Array[Skeleton3D] = []
	var meshes: Array[MeshInstance3D] = []
	if is_instance_valid(_visual): _collect(_visual, meshes, rigs)
	var visible_levels: Array[int] = []
	for index in _levels.size():
		for instance in _levels[index]:
			if is_instance_valid(instance) and instance.visible:
				visible_levels.append(index)
				break
	return {"configured":configured, "mode":"lod_ready" if _levels.size()>1 else "near_only", "level":level, "levels":_levels.size(), "owned_mesh_instances":_owned.size(), "owned_skins":_named_skins.size(), "live_rigs":rigs.size(), "live_bones":_skeleton.get_bone_count() if is_instance_valid(_skeleton) else 0, "ignored_candidate_faces":_ignored_faces, "visible_levels":visible_levels, "switches":_switches, "paths":_paths.duplicate(), "errors":_errors.duplicate(), "last_reason":_last_reason, "scope":"One existing rig; body/bow visibility only; source face/morph writer remains unique; actual posed LOD acceptance and GPU profiling are separate."}

func dispose() -> void:
	for mesh_name in _near:
		if is_instance_valid(_near[mesh_name]): _near[mesh_name].visible = bool(_near_visibility.get(mesh_name, true))
	for instance in _owned:
		if is_instance_valid(instance): instance.free()
	_owned.clear(); _levels.clear(); _near.clear(); _near_visibility.clear(); _named_skins.clear(); _paths.clear()
	_visual = null; _skeleton = null; configured = false; level = 0
	_bounds = AABB(); _ignored_faces = 0; _switches = 0; _errors.clear()
	_selector.reset()
	_last_reason = "disposed"

func _exit_tree() -> void:
	dispose()
