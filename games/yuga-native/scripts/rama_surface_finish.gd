extends Node
## Reversible material finish after the LOD/calibration/secondary owners bind.
## Authored albedo, normals, UVs and geometry remain intact. No frame callback.
const SECONDARY_SHADER := preload("res://shaders/rama_secondary_cloth.gdshader")
const VERSION := 2
const OWNER_META := &"yuga_surface_finish_owner"
const SUFFIX := " · Rama finish v2"
const ROOT := "res://assets/materials/rama-finish/"
const DETAIL_ROOT := "res://assets/hero-finish/"
const MAP_PATHS := {
	"skin":ROOT+"skin-roughness.png", "gold":DETAIL_ROOT+"s1-hammered-gold-roughness.png",
	"ivory":ROOT+"ivory-roughness.png", "hair":DETAIL_ROOT+"hair-bundle-roughness.png",
	"woven":ROOT+"woven-roughness.png",
}
const STANDARD_PROFILES := {
	"Rama warm skin":{"map":"skin","values":{"metallic_specular":.34,"subsurf_scatter_enabled":true,"subsurf_scatter_strength":.08,"subsurf_scatter_skin_mode":true}},
	"Ivory silk":{"map":"ivory","values":{"metallic_specular":.32}},
	"Recessed antique gold":{"values":{"metallic":.92,"roughness":.43}},
	"Polished sapphire":{"values":{"metallic":0.0,"roughness":.19,"metallic_specular":.62}},
	"Natural lips":{"values":{"roughness":.49,"metallic_specular":.39}},
	"Warm sclera":{"values":{"roughness":.22,"metallic_specular":.46}},
	"Deep brown iris":{"values":{"roughness":.16,"metallic_specular":.49}},
	"Pupil":{"values":{"roughness":.18,"metallic_specular":.42}},
}
const SECONDARY_PROFILES := {
	"Cobalt handwoven silk":{"map":"woven","values":{"specular_value":.38}},
	"Cobalt lotus brocade":{"map":"woven","values":{"specular_value":.38}},
	"Worked warm gold":{"map":"gold","values":{"metallic_value":.88,"specular_value":.48}},
	"Swept black hair":{"map":"hair","values":{"specular_value":.29}},
}
var configured := false
var _visual: Node3D
var _standard: Array[Dictionary] = []
var _secondary: Array[Dictionary] = []
var _last_reason := "unconfigured"
var _last_release := {}

func _collect(node: Node, meshes: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh != null: meshes.append(node)
	for child in node.get_children(): _collect(child,meshes)

func _standard_name(material: StandardMaterial3D) -> String:
	var label := material.resource_name
	if label.ends_with(" · Rama calibration v1"): label = label.trim_suffix(" · Rama calibration v1")
	return label if STANDARD_PROFILES.has(label) else ""

func _valid_standard(material: StandardMaterial3D) -> bool:
	for value in [material.roughness,material.metallic,material.metallic_specular,material.normal_scale]:
		if not is_finite(value): return false
	var color := material.albedo_color
	return is_finite(color.r) and is_finite(color.g) and is_finite(color.b) and is_finite(color.a)

func _maps(supplied: Dictionary) -> Dictionary:
	var maps := {}
	for key in MAP_PATHS:
		var texture: Texture2D
		if supplied.has(key):
			if supplied[key] is Texture2D: texture = supplied[key]
		elif ResourceLoader.exists(MAP_PATHS[key]): texture = load(MAP_PATHS[key]) as Texture2D
		if texture == null or texture.get_width() < 1 or texture.get_height() < 1 or texture.get_width() > 4096 or texture.get_height() > 4096:
			_last_reason = "missing or invalid roughness map: " + key
			return {}
		maps[key] = texture
	return maps

func _all_slots_owned(binding: Dictionary, material: Material) -> bool:
	for slot in binding.slots:
		var mesh = slot.mesh.get_ref()
		if not is_instance_valid(mesh) or not is_instance_valid(_visual) or not (mesh == _visual or _visual.is_ancestor_of(mesh)) or mesh.mesh == null or mesh.mesh.get_instance_id() != slot.mesh_id or slot.surface >= mesh.mesh.get_surface_count() or mesh.get_active_material(slot.surface) != material: return false
	return not binding.slots.is_empty()

func _stored(resource: Resource) -> Dictionary:
	var result := {}
	for property in resource.get_property_list():
		if int(property.usage) & PROPERTY_USAGE_STORAGE: result[property.name] = resource.get(property.name)
	return result

func _matches_owned() -> bool:
	for binding in _standard:
		if not _all_slots_owned(binding,binding.material): return false
		for key in binding.values:
			if binding.material.get(key) != binding.values[key]: return false
	for binding in _secondary:
		if binding.material.shader != SECONDARY_SHADER or binding.material.get_meta(OWNER_META,0) != get_instance_id() or not _all_slots_owned(binding,binding.material): return false
		for key in binding.values:
			if binding.material.get_shader_parameter(key) != binding.values[key]: return false
	return true

func configure(visual: Node3D, supplied_maps: Dictionary = {}) -> bool:
	if not is_inside_tree() or not is_instance_valid(visual) or not visual.is_inside_tree():
		_last_reason = "finish owner and visual must be live tree nodes"
		return false
	if configured:
		var stable := visual == _visual and _matches_owned()
		_last_reason = "already configured; no writes" if stable else "owned material or visual changed"
		return stable
	var maps := _maps(supplied_maps)
	if maps.is_empty(): return false
	var meshes: Array[MeshInstance3D] = []
	_collect(visual,meshes)
	var standards: Array[Dictionary] = []
	var secondaries: Array[Dictionary] = []
	var standard_ids := {}
	var secondary_ids := {}
	for mesh in meshes:
		# A global override is an intentional competing appearance and wins.
		if mesh.material_override != null: continue
		for surface in mesh.mesh.get_surface_count():
			var material := mesh.get_active_material(surface)
			if material == null: continue
			if material.resource_name.ends_with(SUFFIX):
				_last_reason = "another finish already owns a surface"
				return false
			var slot := {"mesh":weakref(mesh),"mesh_id":mesh.mesh.get_instance_id(),"surface":surface,"original":mesh.get_surface_override_material(surface)}
			var id := material.get_instance_id()
			if material is StandardMaterial3D:
				var label := _standard_name(material)
				if label.is_empty(): continue
				if not _valid_standard(material):
					_last_reason = "nonfinite source material: " + label
					return false
				if not standard_ids.has(id):
					var profile: Dictionary = STANDARD_PROFILES[label]
					var values: Dictionary = profile.values.duplicate()
					if profile.has("map"):
						values.merge({"roughness":1.0,"roughness_texture":maps[profile.map],"roughness_texture_channel":BaseMaterial3D.TEXTURE_CHANNEL_RED})
					var target := material.duplicate(false) as StandardMaterial3D
					target.resource_name = material.resource_name + SUFFIX
					target.resource_local_to_scene = true
					for key in values:
						target.set(key,values[key])
						values[key] = target.get(key)
					standard_ids[id] = standards.size()
					standards.append({"source":material,"material":target,"label":label,"values":values,"stored":_stored(target),"slots":[]})
				standards[standard_ids[id]].slots.append(slot)
			elif material is ShaderMaterial:
				var label: String = material.resource_name.trim_suffix(" · bounded secondary")
				if not SECONDARY_PROFILES.has(label): continue
				if material.resource_name != label + " · bounded secondary" or material.shader != SECONDARY_SHADER or material.has_meta(OWNER_META):
					_last_reason = "secondary surface has an unrecognized or competing owner"
					return false
				if not secondary_ids.has(id):
					var profile: Dictionary = SECONDARY_PROFILES[label]
					var values: Dictionary = profile.values.duplicate()
					values.merge({"roughness_value":1.0,"rough_texture":maps[profile.map],"rough_channel":Vector4(1,0,0,0),"use_rough_texture":true})
					var before := {}
					for key in values:
						before[key] = material.get_shader_parameter(key)
						if before[key] is float and not is_finite(before[key]):
							_last_reason = "nonfinite source secondary uniform: " + key
							return false
					secondary_ids[id] = secondaries.size()
					secondaries.append({"material":material,"label":label,"values":values,"before":before,"slots":[]})
				secondaries[secondary_ids[id]].slots.append(slot)
	if standards.is_empty() and secondaries.is_empty():
		_last_reason = "no recognized Rama surfaces"
		return false
	# One atomic commit after every texture, source and ownership check passes.
	for binding in standards:
		for slot in binding.slots: slot.mesh.get_ref().set_surface_override_material(slot.surface,binding.material)
	for binding in secondaries:
		for key in binding.values: binding.material.set_shader_parameter(key,binding.values[key])
		binding.material.set_meta(OWNER_META,get_instance_id())
	_standard = standards; _secondary = secondaries; _visual = visual
	configured = true
	visual.tree_exiting.connect(_on_visual_exiting)
	_last_reason = "configured roughness and PBR finish"
	return true

func release() -> Dictionary:
	var result := {"restored_slots":0,"restored_uniforms":0,"conflicts":[],"invalidated":0}
	for binding in _standard:
		var material_changed: bool = _stored(binding.material) != binding.stored
		for slot in binding.slots:
			var mesh = slot.mesh.get_ref()
			if not is_instance_valid(mesh) or not is_instance_valid(_visual) or not (mesh == _visual or _visual.is_ancestor_of(mesh)) or mesh.mesh == null or mesh.mesh.get_instance_id() != slot.mesh_id or slot.surface >= mesh.mesh.get_surface_count():
				result.invalidated += 1
				continue
			if material_changed:
				# A later owner may have edited even an unrelated property on this
				# isolated material; replacing it would discard that newer state.
				result.conflicts.append(binding.label + ": material edited externally")
			elif mesh.get_surface_override_material(slot.surface) == binding.material:
				mesh.set_surface_override_material(slot.surface,slot.original)
				result.restored_slots += 1
			else: result.conflicts.append(binding.label + ": surface replaced")
	for binding in _secondary:
		if binding.material.get_meta(OWNER_META,0) != get_instance_id():
			result.conflicts.append(binding.label + ": owner replaced")
			continue
		# Uniforms affect every slot sharing this material. If even one slot was
		# transferred/replaced, do not mutate that other owner's appearance.
		if binding.material.shader == SECONDARY_SHADER and _all_slots_owned(binding,binding.material):
			for key in binding.values:
				if binding.material.get_shader_parameter(key) == binding.values[key]:
					binding.material.set_shader_parameter(key,binding.before[key])
					result.restored_uniforms += 1
				else: result.conflicts.append(binding.label + ": " + key)
		else: result.invalidated += 1
		binding.material.remove_meta(OWNER_META)
	if is_instance_valid(_visual) and _visual.tree_exiting.is_connected(_on_visual_exiting): _visual.tree_exiting.disconnect(_on_visual_exiting)
	_standard.clear(); _secondary.clear(); _visual = null; configured = false
	_last_release = result.duplicate(true)
	_last_reason = "released"
	return result

func report() -> Dictionary:
	var profiles := {}
	var slots := 0
	for binding in _standard + _secondary:
		profiles[binding.label] = binding.slots.size()
		slots += binding.slots.size()
	return {"configured":configured,"version":VERSION,"standard_materials":_standard.size(),"secondary_materials":_secondary.size(),"surface_slots":slots,"profiles":profiles,"last_reason":_last_reason,"last_release":_last_release.duplicate(true),"frame_callbacks":0,"scope":"Reversible PBR finish. Original albedo/UV/normal, geometry, rig and secondary offset retained; actual appearance and GPU timing require rendered review."}

func _on_visual_exiting() -> void:
	release()

func _exit_tree() -> void:
	release()
