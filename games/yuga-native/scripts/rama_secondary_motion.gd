extends Node
## Bounded procedural mantle/hair response, not a cloth or hair physics solver.
## One caller supplies actual movement state; no gameplay or skeleton is written.
const CLOTH_SHADER := preload("res://shaders/rama_secondary_cloth.gdshader")
const CLOTH_LIMIT := .075
const HAIR_LIMIT := .018
const CLOTH_FREQUENCY := 12.0
const HAIR_FREQUENCY := 18.0
const MAX_DELTA := .1
const TELEPORT_DISTANCE := 3.0
const MATERIAL_KINDS := {"Cobalt handwoven silk":"cloth", "Cobalt lotus brocade":"cloth", "Worked warm gold":"cloth", "Swept black hair":"hair"}

var configured := false
var cloth_offset := Vector3.ZERO
var cloth_velocity := Vector3.ZERO
var hair_offset := Vector3.ZERO
var hair_velocity := Vector3.ZERO
var elapsed := 0.0
var rejected_states := 0
var reset_count := 0
var last_reason := ""
var _bindings: Array[Dictionary] = []
var _cull_margins: Array[Dictionary] = []
var _visual: Node3D
var _last_position := Vector3.ZERO
var _last_yaw := 0.0
var _have_sample := false
var _last_alive := true
var _masked_vertices := {"cloth":0, "hair":0}
var _anchored_vertices := {"cloth":0, "hair":0}

func _collect_meshes(node: Node, result: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh: result.append(node)
	for child in node.get_children(): _collect_meshes(child, result)

func _channel(index: int) -> Vector4:
	if index == BaseMaterial3D.TEXTURE_CHANNEL_GREEN: return Vector4(0,1,0,0)
	if index == BaseMaterial3D.TEXTURE_CHANNEL_BLUE: return Vector4(0,0,1,0)
	if index == BaseMaterial3D.TEXTURE_CHANNEL_ALPHA: return Vector4(0,0,0,1)
	if index == BaseMaterial3D.TEXTURE_CHANNEL_GRAYSCALE: return Vector4(1.0/3.0,1.0/3.0,1.0/3.0,0)
	return Vector4(1,0,0,0)

func _material(source: StandardMaterial3D) -> ShaderMaterial:
	var target := ShaderMaterial.new()
	target.shader = CLOTH_SHADER
	target.resource_name = source.resource_name + " · bounded secondary"
	target.render_priority = source.render_priority
	target.set_shader_parameter("base_color", source.albedo_color)
	target.set_shader_parameter("roughness_value", source.roughness)
	target.set_shader_parameter("metallic_value", source.metallic)
	target.set_shader_parameter("normal_strength", source.normal_scale)
	target.set_shader_parameter("specular_value", source.metallic_specular)
	target.set_shader_parameter("rough_channel", _channel(source.roughness_texture_channel))
	target.set_shader_parameter("metal_channel", _channel(source.metallic_texture_channel))
	for entry in [["base",source.albedo_texture],["rough",source.roughness_texture],["metal",source.metallic_texture],["normal",source.normal_texture]]:
		var exists: bool = entry[1] != null
		target.set_shader_parameter("use_" + entry[0] + "_texture", exists and (entry[0] != "normal" or source.normal_enabled))
		if exists: target.set_shader_parameter(entry[0] + "_texture", entry[1])
	return target

func configure(visual: Node3D) -> bool:
	if configured or visual == null: return false
	if not visual.global_basis.is_finite() or absf(visual.global_basis.determinant())<.000001: return false
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(visual, meshes)
	var staged: Array[Dictionary] = []
	var masked := {"cloth":0, "hair":0}
	var anchored := {"cloth":0, "hair":0}
	for mesh in meshes:
		if not mesh.global_basis.is_finite() or absf(mesh.global_basis.determinant())<.000001: return false
		for surface in mesh.mesh.get_surface_count():
			var source := mesh.get_active_material(surface)
			if not source is StandardMaterial3D or not MATERIAL_KINDS.has(source.resource_name): continue
			# Preserve unsupported material features rather than silently flatten them.
			if source.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED or source.shading_mode != BaseMaterial3D.SHADING_MODE_PER_PIXEL or source.emission_enabled or source.clearcoat_enabled or source.rim_enabled or source.anisotropy_enabled or source.subsurf_scatter_enabled or source.heightmap_enabled or source.ao_enabled or source.detail_enabled: return false
			if source.diffuse_mode != BaseMaterial3D.DIFFUSE_BURLEY or source.specular_mode != BaseMaterial3D.SPECULAR_SCHLICK_GGX: return false
			if source.cull_mode != BaseMaterial3D.CULL_DISABLED or source.billboard_mode != BaseMaterial3D.BILLBOARD_DISABLED or source.uv1_scale != Vector3.ONE or source.uv1_offset != Vector3.ZERO or source.uv2_scale != Vector3.ONE or source.uv2_offset != Vector3.ZERO or source.uv1_triplanar or source.uv2_triplanar or source.texture_filter != BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS or not source.texture_repeat: return false
			var arrays: Array = mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var colors: PackedColorArray = arrays[Mesh.ARRAY_COLOR] if arrays[Mesh.ARRAY_COLOR] != null else PackedColorArray()
			if colors.size() != vertices.size(): return false
			var kind: String = MATERIAL_KINDS[source.resource_name]
			for color in colors:
				if not is_finite(color.r) or not is_finite(color.g) or not is_finite(color.b) or not is_finite(color.a) or absf(color.r-1)>.001 or absf(color.g-1)>.001 or absf(color.b-1)>.001 or color.a<0 or color.a>1: return false
				if color.a>.001: masked[kind] += 1
				else: anchored[kind] += 1
			staged.append({"mesh":mesh,"mesh_id":mesh.mesh.get_instance_id(),"surface":surface,"original":mesh.get_surface_override_material(surface),"original_cull_margin":mesh.extra_cull_margin,"material":_material(source),"kind":kind})
	if staged.is_empty() or masked.cloth == 0 or masked.hair == 0 or anchored.cloth == 0 or anchored.hair == 0: return false
	# No mesh arrays, LODs, skeleton state or shared imported materials are changed.
	_bindings = staged
	_visual = visual
	_masked_vertices = masked
	_anchored_vertices = anchored
	var bounded_meshes := {}
	for binding in _bindings:
		binding.mesh.set_surface_override_material(binding.surface,binding.material)
		var id: int = binding.mesh.get_instance_id()
		if not bounded_meshes.has(id):
			binding.mesh.extra_cull_margin = maxf(binding.original_cull_margin,CLOTH_LIMIT+.005)
			# Read back the property's stored precision for exact ownership checks.
			_cull_margins.append({"mesh":binding.mesh,"original":binding.original_cull_margin,"applied":binding.mesh.extra_cull_margin})
			bounded_meshes[id] = true
	configured = true
	name = "RamaSecondaryMotion"
	return true

func restore_materials() -> void:
	var owned_meshes := {}
	for binding in _bindings:
		if not is_instance_valid(binding.mesh): continue
		var id: int = binding.mesh.get_instance_id()
		var owns_slot: bool = binding.mesh.mesh != null and binding.mesh.mesh.get_instance_id() == binding.mesh_id and binding.surface < binding.mesh.mesh.get_surface_count() and binding.mesh.get_surface_override_material(binding.surface) == binding.material
		owned_meshes[id] = bool(owned_meshes.get(id,true)) and owns_slot
		if owns_slot:
			binding.mesh.set_surface_override_material(binding.surface,binding.original)
	for margin in _cull_margins:
		if not is_instance_valid(margin.mesh): continue
		# A margin belongs to the mesh, not each surface. Preserve later edits
		# and replacements, including another owner's material on one surface.
		if bool(owned_meshes.get(margin.mesh.get_instance_id(),false)) and margin.mesh.extra_cull_margin == margin.applied:
			margin.mesh.extra_cull_margin = margin.original
	_bindings.clear()
	_cull_margins.clear()
	_visual = null
	configured = false

func _exit_tree() -> void:
	restore_materials()

func _spring(position: Vector3, velocity: Vector3, target: Vector3, omega: float, delta: float) -> Array[Vector3]:
	# Exact critically damped constant-target solution. No unstable Euler steps.
	var offset := position - target
	var coefficient := velocity + offset * omega
	var decay := exp(-omega * delta)
	return [(target + (offset + coefficient * delta) * decay), (velocity - coefficient * omega * delta) * decay]

func reset(reason := "reset") -> void:
	cloth_offset = Vector3.ZERO; cloth_velocity = Vector3.ZERO
	hair_offset = Vector3.ZERO; hair_velocity = Vector3.ZERO
	_have_sample = false
	_last_alive = true
	elapsed = 0
	reset_count += 1
	last_reason = reason
	_publish()

func _publish() -> void:
	for binding in _bindings:
		if is_instance_valid(binding.mesh) and is_instance_valid(_visual):
			if not binding.mesh.global_basis.is_finite() or absf(binding.mesh.global_basis.determinant())<.000001 or not _visual.global_basis.is_finite():
				binding.material.set_shader_parameter("secondary_offset",Vector3.ZERO)
				continue
			var offset: Vector3 = hair_offset if binding.kind == "hair" else cloth_offset
			binding.material.set_shader_parameter("secondary_offset",binding.mesh.global_basis.inverse()*_visual.global_basis*offset)

func update_secondary(delta: float, state: Dictionary) -> bool:
	if not configured: return false
	# Pause is an explicit hold: no integration, decay, clock or baseline mutation.
	if bool(state.get("paused",false)): return true
	if not is_finite(delta) or delta <= 0 or delta > MAX_DELTA:
		rejected_states += 1
		reset("invalid delta; no catch-up")
		return false
	if not state.get("local_velocity",Vector3.ZERO) is Vector3 or not state.get("position",Vector3.ZERO) is Vector3 or not (state.get("yaw",0.0) is float or state.get("yaw",0.0) is int):
		rejected_states += 1
		reset("invalid motion input type")
		return false
	var velocity: Vector3 = state.get("local_velocity",Vector3.ZERO)
	var position: Vector3 = state.get("position",Vector3.ZERO)
	var yaw: float = state.get("yaw",0.0)
	if not velocity.is_finite() or not position.is_finite() or not is_finite(yaw):
		rejected_states += 1
		reset("non-finite motion input")
		return false
	# Normalize each finite angle before subtracting: opposite huge finite inputs
	# must not overflow into an infinite angular velocity or material uniform.
	yaw = wrapf(yaw,-PI,PI)
	var alive: bool = state.get("alive",true)
	var generation_reset: bool = state.get("reset",false)
	var teleported := _have_sample and position.distance_to(_last_position) > maxf(TELEPORT_DISTANCE,velocity.length()*delta*2+.5)
	if not alive and not _last_alive and not generation_reset and not teleported:
		_last_position = position; _last_yaw = yaw
		return true
	if generation_reset or teleported or not alive or alive != _last_alive:
		reset("reset" if generation_reset else ("teleport" if teleported else "death/respawn"))
		_last_position = position; _last_yaw = yaw; _have_sample = true; _last_alive = alive
		return true
	var turn := clampf(wrapf(yaw-_last_yaw,-PI,PI)/delta,-5,5) if _have_sample else 0.0
	_last_position = position; _last_yaw = yaw; _have_sample = true; _last_alive = alive
	velocity = velocity.limit_length(24.0)
	var speed := Vector2(velocity.x,velocity.z).length()
	var lift := minf(.021,speed*.0014) + clampf(-velocity.y*.001,-.012,.012)
	var cloth_target := Vector3(-velocity.x*.0038-turn*.003, lift, -velocity.z*.0038).limit_length(CLOTH_LIMIT)
	var hair_target := Vector3(-velocity.x*.0009-turn*.0012, lift*.16, -velocity.z*.0009).limit_length(HAIR_LIMIT)
	if not bool(state.get("grounded",true)):
		cloth_target = (cloth_target * 1.14).limit_length(CLOTH_LIMIT)
		hair_target = (hair_target * 1.08).limit_length(HAIR_LIMIT)
	if bool(state.get("reduced_motion",false)):
		cloth_target = Vector3.ZERO
		hair_target = Vector3.ZERO
	var cloth := _spring(cloth_offset,cloth_velocity,cloth_target,CLOTH_FREQUENCY,delta)
	var hair := _spring(hair_offset,hair_velocity,hair_target,HAIR_FREQUENCY,delta)
	cloth_offset = cloth[0].limit_length(CLOTH_LIMIT); cloth_velocity = cloth[1].limit_length(1.5)
	hair_offset = hair[0].limit_length(HAIR_LIMIT); hair_velocity = hair[1].limit_length(.6)
	elapsed += delta
	_publish()
	return true

func rest_displacement(mask: float, kind := "cloth") -> Vector3:
	if not is_finite(mask): return Vector3.ZERO
	var weight := clampf(mask,0,1)
	return (hair_offset if kind == "hair" else cloth_offset) * weight * weight

func report() -> Dictionary:
	return {"configured":configured,"bindings":_bindings.size(),"masked_vertices":_masked_vertices.duplicate(),"anchored_vertices":_anchored_vertices.duplicate(),"cloth_offset":cloth_offset,"cloth_velocity":cloth_velocity,"hair_offset":hair_offset,"hair_velocity":hair_velocity,"elapsed":elapsed,"cloth_limit_m":CLOTH_LIMIT,"hair_limit_m":HAIR_LIMIT,"finite":cloth_offset.is_finite() and cloth_velocity.is_finite() and hair_offset.is_finite() and hair_velocity.is_finite(),"rejected_states":rejected_states,"reset_count":reset_count,"last_reason":last_reason,"scope":"Bounded analytic spring response through authored rest-space masks. No cloth collision, strands, gameplay or skeleton writes."}
