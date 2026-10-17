extends RefCounted
## Only the known flat ground receives shadows without casting onto itself.
## No material, collision, visibility, light or raised-platform mutation.

const COURTYARD_NAMES := ["COL_Limestone_mortar", "FLOOR_BEVEL_Courtyard_stone_0",
	"FLOOR_BEVEL_Courtyard_stone_1", "FLOOR_BEVEL_Courtyard_stone_2", "FLOOR_BEVEL_Courtyard_stone_3"]
const WORLD_NAMES := ["FlatCityPaving", "NoncollidingTerrainApron"]

static func apply_courtyard(world: Node3D) -> int:
	if not is_instance_valid(world): return 0
	var count := 0
	for name_ in COURTYARD_NAMES:
		var mesh := world.get_node_or_null("AuthoredLankaCourtyard/" + name_) as MeshInstance3D
		var top := -0.002 if name_ == "COL_Limestone_mortar" else 0.0
		if _flat_receiver(mesh, world, top, 0.41):
			mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			count += 1
	return count

static func apply_world(world: Node3D) -> int:
	if not is_instance_valid(world): return 0
	var count := 0
	for name_ in WORLD_NAMES:
		var mesh := world.get_node_or_null(name_) as MeshInstance3D
		var top := -0.18 if name_ == "NoncollidingTerrainApron" else 0.0
		if _flat_receiver(mesh, world, top, 0.001):
			mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			count += 1
	return count

static func _flat_receiver(mesh: MeshInstance3D, world: Node3D, top: float, max_depth: float) -> bool:
	if not is_instance_valid(mesh) or mesh.mesh == null: return false
	# Names alone cannot identify a ground surface: reject raised/lookalike meshes
	# and unexpectedly changed imports. Bounds are measured in the world's space.
	var relative := world.global_transform.affine_inverse() * mesh.global_transform
	if not relative.is_finite(): return false
	var bounds: AABB = relative * mesh.get_aabb()
	return bounds.position.is_finite() and bounds.size.is_finite() \
		and bounds.size.x >= 30.0 and bounds.size.z >= 30.0 \
		and bounds.size.y <= max_depth \
		and absf(bounds.end.y - top) <= 0.001
