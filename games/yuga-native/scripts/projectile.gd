extends Node3D
## Swept collision each physics tick prevents fast projectiles tunnelling.

signal impacted(position: Vector3, target: Node)

var direction := Vector3.FORWARD
var speed := 54.0
var life := 2.2
var ignore: Array[RID] = []
var damage := 1

func _ready() -> void:
	var mesh := MeshInstance3D.new()
	var shape := CapsuleMesh.new()
	shape.radius = 0.035
	shape.height = 0.65
	shape.radial_segments = 8
	shape.rings = 2
	mesh.mesh = shape
	mesh.rotation.x = PI / 2
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("ffe5a3")
	material.emission_enabled = true
	material.emission = Color("ffc764")
	material.emission_energy_multiplier = 4
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mesh.material_override = material
	add_child(mesh)
	if direction.length_squared() > 0.001:
		look_at(global_position + direction)

func _physics_process(delta: float) -> void:
	life -= delta
	if life <= 0:
		queue_free()
		return
	var next := global_position + direction * speed * delta
	var query := PhysicsRayQueryParameters3D.create(global_position, next, 1 | 4, ignore)
	var result := get_world_3d().direct_space_state.intersect_ray(query)
	if not result.is_empty():
		if result.collider.has_method("take_hit"):
			result.collider.take_hit(damage)
		impacted.emit(result.position, result.collider)
		queue_free()
	else:
		global_position = next
