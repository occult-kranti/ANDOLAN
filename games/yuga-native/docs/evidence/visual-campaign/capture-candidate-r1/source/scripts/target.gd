extends StaticBody3D

signal struck(target: Node3D, defeated: bool)

var max_health := 3
var health := 3
var reset_after := 4.0
var reset_remaining := 0.0
var number := 1
var body: Node3D
var ring: MeshInstance3D
var label: Label3D
var collision: CollisionShape3D
var ring_material: StandardMaterial3D
var impact_timer := 0.0

func _ready() -> void:
	collision_layer = 4
	collision_mask = 0
	body = Node3D.new()
	add_child(body)
	var bronze := StandardMaterial3D.new()
	bronze.albedo_color = Color("675344")
	bronze.metallic = 0.65
	bronze.roughness = 0.35
	var plinth := MeshInstance3D.new()
	var base := CylinderMesh.new()
	base.top_radius = 0.45
	base.bottom_radius = 0.58
	base.height = 0.22
	plinth.mesh = base
	plinth.position.y = 0.11
	plinth.material_override = bronze
	body.add_child(plinth)
	var stem := MeshInstance3D.new()
	var pole := CylinderMesh.new()
	pole.top_radius = 0.055
	pole.bottom_radius = 0.11
	pole.height = 1.35
	stem.mesh = pole
	stem.position.y = 0.8
	stem.material_override = bronze
	body.add_child(stem)
	ring = MeshInstance3D.new()
	var disc := CylinderMesh.new()
	disc.top_radius = 0.52
	disc.bottom_radius = 0.52
	disc.height = 0.13
	disc.radial_segments = 32
	ring.mesh = disc
	ring.position.y = 1.65
	ring.rotation.x = PI / 2
	ring_material = StandardMaterial3D.new()
	ring_material.albedo_color = Color("37c9c5")
	ring_material.metallic = 0.35
	ring_material.roughness = 0.28
	ring_material.emission_enabled = true
	ring_material.emission = Color("146e75")
	ring_material.emission_energy_multiplier = 0.45
	ring.material_override = ring_material
	body.add_child(ring)
	var center := MeshInstance3D.new()
	var bull := SphereMesh.new()
	bull.radius = 0.16
	bull.height = 0.32
	center.mesh = bull
	center.position = Vector3(0, 1.65, 0.10)
	var gold := StandardMaterial3D.new()
	gold.albedo_color = Color("ffdc87")
	gold.metallic = 0.5
	gold.emission_enabled = true
	gold.emission = Color("eab461")
	gold.emission_energy_multiplier = 0.5
	center.material_override = gold
	body.add_child(center)
	collision = CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1.12, 1.5, 0.45)
	collision.shape = box
	collision.position.y = 1.2
	add_child(collision)
	label = Label3D.new()
	label.position.y = 2.45
	label.font_size = 36
	label.pixel_size = 0.008
	label.modulate = Color("f4e8c9")
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.outline_size = 8
	add_child(label)
	_update_label()

func _physics_process(delta: float) -> void:
	if reset_remaining > 0:
		reset_remaining = maxf(0, reset_remaining - delta)
		if reset_remaining == 0:
			reset_target()
		else:
			label.text = "RETURNING  %.1f" % reset_remaining
	if impact_timer > 0:
		impact_timer = maxf(0, impact_timer - delta)
		ring.scale = Vector3.ONE * (1.0 + impact_timer * 0.5)
		ring_material.emission_energy_multiplier = 0.45 + impact_timer * 6

func take_hit(damage: int = 1) -> bool:
	if health <= 0:
		return false
	health = maxi(0, health - damage)
	impact_timer = 0.18
	var defeated := health == 0
	if defeated:
		reset_remaining = reset_after
		body.visible = false
		collision.set_deferred("disabled", true)
	else:
		_update_label()
	struck.emit(self, defeated)
	return true

func reset_target() -> void:
	health = max_health
	reset_remaining = 0
	impact_timer = 0
	body.visible = true
	ring.scale = Vector3.ONE
	ring_material.emission_energy_multiplier = 0.45
	collision.set_deferred("disabled", false)
	_update_label()

func _update_label() -> void:
	label.text = "0%d   %s" % [number, "◆".repeat(health) + "◇".repeat(max_health - health)]
