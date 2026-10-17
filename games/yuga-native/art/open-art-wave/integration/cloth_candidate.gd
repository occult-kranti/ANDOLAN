extends Node
## Explicit review-fixture binding only. Does not install itself in either game.
## The existing secondary-motion owner keeps its ShaderMaterial and offset writer.
const CLOTH_SHADER := preload("res://shaders/rama_secondary_cloth.gdshader")
const SOURCE_NAME := "Cobalt handwoven silk"
const TARGET_NAME := SOURCE_NAME + " · bounded secondary"
const CANDIDATE_PATH := "res://art/open-art-wave/materials/indigo-woven-cloth.tres"
const ALLOWED_PROPERTIES := ["resource_name", "resource_local_to_scene", "albedo_color", "albedo_texture", "roughness", "roughness_texture", "roughness_texture_channel", "metallic", "metallic_texture", "metallic_texture_channel", "metallic_specular", "normal_enabled", "normal_texture", "normal_scale", "cull_mode", "texture_filter"]
const SCOPE := "Optional review-only woven-map conversion on existing secondary-owned cloth materials. No mesh, skin, mask, face, shader, LOD, offset, input or default game-flow writes."

var _bindings: Array[Dictionary] = []
var _visual: Node3D
var _values := {}
var _candidate_path := ""
var _candidate_sha256 := ""
var _candidate_filter := -1
var _preserve_albedo := false
var _last_reason := "not bound"
var _last_unbind := {}
var _surface_slots := 0

func _collect(node: Node, meshes: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh: meshes.append(node)
	for child in node.get_children(): _collect(child, meshes)

func _channel(index: int) -> Vector4:
	if index == BaseMaterial3D.TEXTURE_CHANNEL_GREEN: return Vector4(0,1,0,0)
	if index == BaseMaterial3D.TEXTURE_CHANNEL_BLUE: return Vector4(0,0,1,0)
	if index == BaseMaterial3D.TEXTURE_CHANNEL_ALPHA: return Vector4(0,0,0,1)
	if index == BaseMaterial3D.TEXTURE_CHANNEL_GRAYSCALE: return Vector4(1.0/3.0,1.0/3.0,1.0/3.0,0)
	return Vector4(1,0,0,0)

func _candidate_values(candidate: StandardMaterial3D) -> Dictionary:
	if not is_instance_valid(candidate):
		_last_reason = "candidate is not a StandardMaterial3D"
		return {}
	# Compare every stored material property against the engine's default, rather
	# than silently ignoring new/less common features outside the fixed shader.
	var defaults := StandardMaterial3D.new()
	for property in candidate.get_property_list():
		var key: String = property.name
		if not (int(property.usage) & PROPERTY_USAGE_STORAGE) or key in ALLOWED_PROPERTIES: continue
		if candidate.get(key) != defaults.get(key):
			_last_reason = "unsupported candidate property: " + key
			return {}
	if candidate.cull_mode != BaseMaterial3D.CULL_DISABLED:
		_last_reason = "candidate must be two sided"
		return {}
	if candidate.texture_filter not in [BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS, BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC]:
		_last_reason = "unsupported candidate texture filter"
		return {}
	var color := candidate.albedo_color
	if not is_finite(color.r) or not is_finite(color.g) or not is_finite(color.b) or not is_finite(color.a) or color.a != 1.0 or minf(color.r,minf(color.g,color.b)) < 0 or maxf(color.r,maxf(color.g,color.b)) > 1:
		_last_reason = "candidate base color must be finite, opaque and normalized"
		return {}
	for value in [candidate.roughness, candidate.metallic, candidate.metallic_specular]:
		if not is_finite(value) or value < 0 or value > 1:
			_last_reason = "candidate PBR scalars must be finite and normalized"
			return {}
	if not is_finite(candidate.normal_scale) or candidate.normal_scale < 0 or candidate.normal_scale > 2:
		_last_reason = "candidate normal strength is outside the bounded review range"
		return {}
	for channel in [candidate.roughness_texture_channel,candidate.metallic_texture_channel]:
		if channel < BaseMaterial3D.TEXTURE_CHANNEL_RED or channel > BaseMaterial3D.TEXTURE_CHANNEL_GRAYSCALE:
			_last_reason = "unsupported candidate packed-map channel"
			return {}
	for texture in [candidate.albedo_texture,candidate.roughness_texture,candidate.metallic_texture,candidate.normal_texture]:
		if texture != null and (texture.get_width() <= 0 or texture.get_height() <= 0 or texture.get_width() > 8192 or texture.get_height() > 8192):
			_last_reason = "candidate texture dimensions are invalid or exceed the review bound"
			return {}
	if candidate.normal_enabled and candidate.normal_texture == null:
		_last_reason = "enabled candidate normal map is missing"
		return {}
	return {"base_color":candidate.albedo_color,"roughness_value":candidate.roughness,"metallic_value":candidate.metallic,"normal_strength":candidate.normal_scale,"specular_value":candidate.metallic_specular,"rough_channel":_channel(candidate.roughness_texture_channel),"metal_channel":_channel(candidate.metallic_texture_channel),"base_texture":candidate.albedo_texture,"rough_texture":candidate.roughness_texture,"metal_texture":candidate.metallic_texture,"normal_texture":candidate.normal_texture,"use_base_texture":candidate.albedo_texture != null,"use_rough_texture":candidate.roughness_texture != null,"use_metal_texture":candidate.metallic_texture != null,"use_normal_texture":candidate.normal_enabled and candidate.normal_texture != null}

func bind(visual: Node3D, candidate: StandardMaterial3D = null, preserve_albedo: bool = false) -> bool:
	if not is_instance_valid(visual) or not visual.is_inside_tree():
		_last_reason = "visual must be a live tree node"
		return false
	if candidate == null:
		if not ResourceLoader.exists(CANDIDATE_PATH):
			_last_reason = "review candidate is unavailable"
			return false
		candidate = load(CANDIDATE_PATH) as StandardMaterial3D
	var values := _candidate_values(candidate)
	if values.is_empty(): return false
	if preserve_albedo:
		# This review profile retains the authored indigo/gold motif exactly.
		# These keys are absent from ownership, snapshots and rollback alike.
		for key in ["base_color","base_texture","use_base_texture"]: values.erase(key)
	if not _bindings.is_empty():
		if visual != _visual or values != _values or preserve_albedo != _preserve_albedo:
			_last_reason = "already bound to a different visual, candidate or appearance policy"
			return false
		for binding in _bindings:
			if binding.material.shader != CLOTH_SHADER or not _has_live_slot(binding):
				_last_reason = "bound material shader or live owner slot was replaced"
				return false
			for key in _values:
				if binding.material.get_shader_parameter(key) != _values[key]:
					_last_reason = "bound uniform changed externally: " + key
					return false
		_last_reason = "already bound; no writes"
		return true
	var meshes: Array[MeshInstance3D] = []
	_collect(visual,meshes)
	var staged: Array[Dictionary] = []
	var by_id := {}
	var slots := 0
	for mesh in meshes:
		for surface in mesh.mesh.get_surface_count():
			var material := mesh.get_active_material(surface)
			if material == null or material.resource_name not in [SOURCE_NAME,TARGET_NAME]: continue
			if mesh.material_override != null or not material is ShaderMaterial or material.resource_name != TARGET_NAME or material.shader != CLOTH_SHADER:
				_last_reason = "target cloth is not under the recognized secondary shader owner"
				return false
			var id := material.get_instance_id()
			if not by_id.has(id):
				var before := {}
				for key in values: before[key] = material.get_shader_parameter(key)
				staged.append({"material":material,"id":id,"before":before,"slots":[]})
				by_id[id] = staged.size()-1
			staged[by_id[id]].slots.append({"mesh":weakref(mesh),"mesh_id":mesh.mesh.get_instance_id(),"surface":surface})
			slots += 1
	if staged.is_empty():
		_last_reason = "no secondary-owned target cloth found"
		return false
	# All material/resource/ownership validation precedes the first write.
	for binding in staged:
		for key in values: binding.material.set_shader_parameter(key,values[key])
	_bindings = staged
	_visual = visual
	_values = values
	_candidate_path = candidate.resource_path
	_candidate_sha256 = FileAccess.get_sha256(_candidate_path) if not _candidate_path.is_empty() and FileAccess.file_exists(_candidate_path) else ""
	_candidate_filter = candidate.texture_filter
	_preserve_albedo = preserve_albedo
	_surface_slots = slots
	visual.tree_exiting.connect(_on_visual_exiting)
	_last_reason = "bound explicitly for review"
	return true

func _has_live_slot(binding: Dictionary) -> bool:
	for slot in binding.slots:
		var mesh = slot.mesh.get_ref()
		if is_instance_valid(mesh) and mesh.is_inside_tree() and is_instance_valid(_visual) and (mesh == _visual or _visual.is_ancestor_of(mesh)) and mesh.mesh != null and mesh.mesh.get_instance_id() == slot.mesh_id and slot.surface < mesh.mesh.get_surface_count() and mesh.get_active_material(slot.surface) == binding.material:
			return true
	return false

func unbind() -> Dictionary:
	var result := {"restored_fields":0,"conflicts":[],"invalidated_materials":[],"materials":_bindings.size(),"already_unbound":_bindings.is_empty(),"appearance_policy":_appearance_policy()}
	for binding in _bindings:
		if binding.material.shader != CLOTH_SHADER or not _has_live_slot(binding):
			result.invalidated_materials.append(binding.id)
			continue
		# Each uniform has conditional ownership; a foreign write is preserved.
		# secondary_offset is deliberately absent from both snapshots and writes.
		for key in _values:
			if binding.material.get_shader_parameter(key) == _values[key]:
				binding.material.set_shader_parameter(key,binding.before[key])
				result.restored_fields += 1
			else: result.conflicts.append({"material_id":binding.id,"uniform":key})
	if is_instance_valid(_visual) and _visual.tree_exiting.is_connected(_on_visual_exiting): _visual.tree_exiting.disconnect(_on_visual_exiting)
	_bindings.clear()
	_values.clear()
	_visual = null
	_preserve_albedo = false
	_last_unbind = result.duplicate(true)
	_last_reason = "unbound with preserved conflicts or invalidation" if not result.conflicts.is_empty() or not result.invalidated_materials.is_empty() else "unbound"
	return result

func report() -> Dictionary:
	var ids := []
	for binding in _bindings: ids.append(binding.id)
	return {"bound":not _bindings.is_empty(),"unique_materials":_bindings.size(),"surface_slots":_surface_slots if not _bindings.is_empty() else 0,"material_ids":ids,"touched_fields":_values.keys(),"appearance_policy":_appearance_policy(),"preserve_albedo":_preserve_albedo,"candidate_path":_candidate_path,"candidate_sha256":_candidate_sha256,"candidate_filter":_candidate_filter,"shader_filter":"linear with mipmaps, repeat","filter_conversion":_candidate_filter == BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC,"last_reason":_last_reason,"last_unbind":_last_unbind.duplicate(true),"scope":SCOPE}

func _appearance_policy() -> String:
	if _bindings.is_empty(): return "unbound"
	return "preserve-authored-albedo-surface-only" if _preserve_albedo else "candidate-albedo-and-surface"

func _on_visual_exiting() -> void:
	unbind()

func _exit_tree() -> void:
	unbind()
