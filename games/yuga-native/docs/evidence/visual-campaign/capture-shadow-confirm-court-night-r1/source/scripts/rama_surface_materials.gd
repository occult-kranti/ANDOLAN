extends Node
## Optional, reversible dielectric/metal calibration for the Rama quality slice.
## Native Godot PBR remains in charge: no replacement skin shader or added light.
## The authored maps, normal strength, UVs and mesh data are never rewritten.
const PROFILE_VERSION := 1
const PROFILES := {
	"Rama warm skin": {"metallic_specular":0.42},
	"Natural lips": {"metallic_specular":0.42,"roughness":0.50},
	"Warm sclera": {"metallic_specular":0.395,"roughness":0.20},
	"Deep brown iris": {"metallic_specular":0.395,"roughness":0.22},
	"Polished sapphire": {"metallic":0.0,"metallic_specular":0.68},
	"Recessed antique gold": {"metallic":0.90},
}
# These surfaces carry the separate owner's semantic vertex-alpha motion mask.
const SECONDARY_OWNED := ["Cobalt handwoven silk","Cobalt lotus brocade","Worked warm gold","Swept black hair"]
var configured := false
var _visual: Node3D
var _bindings: Array[Dictionary] = []

func _collect_meshes(node: Node, result: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh: result.append(node)
	for child in node.get_children(): _collect_meshes(child, result)

func _finite_surface(source: StandardMaterial3D) -> bool:
	for value in [source.roughness,source.metallic,source.metallic_specular,source.normal_scale]:
		if not is_finite(value): return false
	var color := source.albedo_color
	return is_finite(color.r) and is_finite(color.g) and is_finite(color.b) and is_finite(color.a)

func configure(visual: Node3D) -> bool:
	if not is_instance_valid(visual): return false
	# Repeated entry/settings calls do not allocate or replace materials again.
	if configured: return visual == _visual and is_instance_valid(_visual)
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(visual,meshes)
	var staged: Array[Dictionary] = []
	for mesh in meshes:
		# A global override deliberately wins over per-surface appearance.
		if mesh.material_override != null: continue
		for surface in mesh.mesh.get_surface_count():
			var source := mesh.get_active_material(surface)
			if not source is StandardMaterial3D: continue
			if SECONDARY_OWNED.has(source.resource_name) or not PROFILES.has(source.resource_name): continue
			# Reject atomically rather than propagating invalid material uniforms.
			if not _finite_surface(source): return false
			var target := source.duplicate(false) as StandardMaterial3D
			target.resource_name = source.resource_name + " · Rama calibration v" + str(PROFILE_VERSION)
			target.resource_local_to_scene = true
			for property in PROFILES[source.resource_name]: target.set(property,PROFILES[source.resource_name][property])
			staged.append({"mesh":mesh,"surface":surface,"original":mesh.get_surface_override_material(surface),"material":target,"profile":source.resource_name})
	if staged.is_empty(): return false
	for binding in staged: binding.mesh.set_surface_override_material(binding.surface,binding.material)
	_bindings = staged
	_visual = visual
	configured = true
	name = "RamaSurfaceMaterials"
	return true

func restore_materials() -> void:
	for binding in _bindings:
		if is_instance_valid(binding.mesh) and binding.mesh.mesh != null and binding.surface < binding.mesh.mesh.get_surface_count() and binding.mesh.get_surface_override_material(binding.surface) == binding.material:
			binding.mesh.set_surface_override_material(binding.surface,binding.original)
	_bindings.clear()
	_visual = null
	configured = false

func diagnostics() -> Dictionary:
	var profiles := {}
	for binding in _bindings: profiles[binding.profile] = int(profiles.get(binding.profile,0)) + 1
	return {"configured":configured,"profile_version":PROFILE_VERSION,"owned_materials":_bindings.size(),"profiles":profiles,"native_pbr":true,"additional_lights":0}

func _exit_tree() -> void:
	restore_materials()
