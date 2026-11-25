extends MeshInstance3D
## Single feathered footprint under Hanuman on the trial's flat limestone.

const Shade = preload("res://shaders/hanuman_contact_shadow.gdshader")
const MAX_LIFT_M := 0.66
const DEPTH_OFFSET_M := 0.009
const SUN_CONTACT_OPACITY := 0.22
const FALLBACK_CONTACT_OPACITY := 0.46

var _actor: CharacterBody3D
var _facing: Node3D
var _floor: StaticBody3D
var _paving: MeshInstance3D
var _sun: DirectionalLight3D
var _ray := PhysicsRayQueryParameters3D.new()
var _material: ShaderMaterial

func configure(actor: CharacterBody3D, facing: Node3D, floor_body: StaticBody3D,
		paving: MeshInstance3D, sun: DirectionalLight3D) -> void:
	_actor = actor
	_facing = facing
	_floor = floor_body
	_paving = paving
	_sun = sun
	_ray.collision_mask = floor_body.collision_layer
	_ray.exclude = [actor.get_rid()]

func _ready() -> void:
	visible = false
	process_physics_priority = 20
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var plane := PlaneMesh.new()
	plane.size = Vector2(2, 2)
	mesh = plane
	_material = ShaderMaterial.new()
	_material.shader = Shade
	_material.render_priority = -4
	material_override = _material

func _physics_process(_delta: float) -> void:
	if not is_instance_valid(_actor) or not is_instance_valid(_floor) \
			or not is_instance_valid(_paving) or _paving.mesh == null or not _paving.is_visible_in_tree():
		visible = false
		return

	var foot := _actor.global_position
	_ray.from = foot + Vector3.UP * 0.12
	_ray.to = foot - Vector3.UP * MAX_LIFT_M
	var hit := get_world_3d().direct_space_state.intersect_ray(_ray)
	if hit.is_empty() or hit.collider != _floor:
		visible = false
		return

	var ground: Vector3 = hit.position
	var upward: Vector3 = hit.normal
	var bounds := _paving.global_transform * _paving.get_aabb()
	if upward.y < 0.99 or absf(bounds.end.y - ground.y) > 0.02 or bounds.size.y > 0.41:
		visible = false
		return

	var edge := minf(minf(ground.x - bounds.position.x, bounds.end.x - ground.x),
			minf(ground.z - bounds.position.z, bounds.end.z - ground.z))
	var gap := maxf(0.0, foot.y - ground.y)
	if edge <= 0.03 or gap >= MAX_LIFT_M:
		visible = false
		return

	var lift := smoothstep(0.08, MAX_LIFT_M, gap)
	var has_sun_shadow := is_instance_valid(_sun) and _sun.visible and _sun.shadow_enabled
	# Preserve the sun silhouette. With it present, restrict this to soft
	# occlusion near the feet. With it disabled, the footprint carries grounding.
	var radius := Vector2(0.75, 0.54) if has_sun_shadow else Vector2(0.81, 0.62)
	radius *= lerpf(1.0, 1.16, lift)
	var edge_scale := minf(1.0, (edge - 0.02) / maxf(radius.x, radius.y))
	var strength := SUN_CONTACT_OPACITY if has_sun_shadow else FALLBACK_CONTACT_OPACITY
	strength *= (1.0 - lift) * smoothstep(0.03, 0.24, edge)
	global_position = ground + Vector3.UP * DEPTH_OFFSET_M
	if is_instance_valid(_facing):
		global_rotation = Vector3(0, _facing.global_rotation.y, 0)
	scale = Vector3(radius.x * edge_scale, 1.0, radius.y * edge_scale)
	_material.set_shader_parameter("opacity", strength)
	visible = true
