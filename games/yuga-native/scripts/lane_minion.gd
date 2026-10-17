extends StaticBody3D
## Offline lane unit. One collider plus shared original articulated part meshes.

signal defeated(unit: Node3D, by_player: bool)

const Art = preload("res://scripts/lane_unit_art.gd")
const STATS := {
	"spearman":{"health":75.0,"damage":10.0,"range":2.15,"cooldown":1.10,"speed":3.8,"gold":18},
	"bow_guard":{"health":55.0,"damage":8.0,"range":11.0,"cooldown":1.50,"speed":3.6,"gold":24},
	"commander":{"health":150.0,"damage":13.0,"range":2.55,"cooldown":1.40,"speed":3.45,"gold":45}
}

var army: Node3D
var unit_id := 0
var team := "sun"
var role := "spearman"
var lane_id := 0
var progress := 0.0
var lateral := 0.0
var max_health := 75.0
var health := 75.0
var alive := true
var state := "walk"
var attack_cooldown := 0.0
var attack_time := 0.0
var hit_time := 0.0
var dead_age := 0.0
var invalid_damage := 0
var target: Node3D
var visual: Node3D
var joints: Dictionary = {}
var previous_position := Vector3.ZERO
var previous_yaw := 0.0
var heading := 0.0
var moved := 0.0
var attack_target := Vector3.ZERO
var shape: CollisionShape3D
var health_fill: MeshInstance3D
var arrow: MeshInstance3D
var reward_emitted := false
var render_art := true

func setup(owner_army: Node3D, identity: int, team_value: String, role_value: String, lane_value: int) -> void:
	army = owner_army
	unit_id = identity
	team = team_value
	role = role_value
	lane_id = lane_value
	max_health = float(STATS[role].health)
	health = max_health
	name = "%s_%s_%d" % [team,role,unit_id]

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	collision_layer = 4 if team == "moon" else 0
	collision_mask = 0
	add_to_group("lane_enemy" if team == "moon" else "lane_ally")
	shape = CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = .39
	capsule.height = 1.9 if role != "commander" else 2.13
	shape.shape = capsule
	shape.position.y = capsule.height*.5
	add_child(shape)
	if render_art:
		var result := Art.build(team,role)
		visual = result.root
		joints = result.joints
		add_child(visual)
		var bar := Node3D.new()
		bar.position.y = 2.10 if role != "commander" else 3.02
		add_child(bar)
		var dark := StandardMaterial3D.new()
		dark.albedo_color = Color("1a2024")
		dark.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		var background := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(.82,.075,.055)
		background.mesh = box
		background.material_override = dark
		bar.add_child(background)
		health_fill = MeshInstance3D.new()
		var fill := BoxMesh.new()
		fill.size = Vector3(.78,.045,.065)
		health_fill.mesh = fill
		var color := StandardMaterial3D.new()
		color.albedo_color = Color("edb860") if team == "sun" else Color("70c7eb")
		color.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		health_fill.material_override = color
		bar.add_child(health_fill)
		if role == "bow_guard":
			arrow = MeshInstance3D.new()
			var shaft := CylinderMesh.new()
			shaft.top_radius = .018
			shaft.bottom_radius = .018
			shaft.height = .70
			shaft.radial_segments = 6
			arrow.mesh = shaft
			arrow.material_override = color
			arrow.visible = false
			add_child(arrow)
	previous_position = position

func take_hit(amount = 1) -> bool:
	return receive_damage(amount,"player")

func receive_damage(amount, source := "army") -> bool:
	if typeof(amount) not in [TYPE_INT,TYPE_FLOAT] or not is_finite(float(amount)) or float(amount) <= 0 or float(amount) > 1000:
		invalid_damage += 1
		return false
	if source not in ["army","player"] or not alive or (source == "player" and team == "sun"):
		return false
	health = maxf(0.0,health-float(amount))
	hit_time = .18
	if health <= 0:
		alive = false
		state = "fall"
		collision_layer = 0
		target = null
		if not reward_emitted:
			reward_emitted = true
			defeated.emit(self,source == "player")
	return true

func arrive() -> void:
	alive = false
	state = "arrived"
	collision_layer = 0
	dead_age = 1.21
	target = null

func start_attack(point: Vector3) -> float:
	attack_cooldown = float(STATS[role].cooldown)
	attack_time = .52
	attack_target = point
	state = "aim" if role == "bow_guard" else "swing"
	return .26 if role == "bow_guard" else .18

func _process(_delta: float) -> void:
	if visual and is_instance_valid(army):
		update_pose(float(army.elapsed)+float(army.interpolation_alpha())*.05,float(army.interpolation_alpha()))

func update_pose(time: float, alpha := 1.0) -> void:
	if not visual or not is_finite(time) or not is_finite(alpha):
		return
	alpha = clampf(alpha,0,1)
	visual.position = (previous_position-position)*(1-alpha)
	visual.rotation = Vector3(0,lerp_angle(previous_yaw,heading,alpha),0)
	var walk := sin(time*8.8+float(unit_id%5)*.12)*clampf(moved/.14,0,1)
	for side in ["left","right"]:
		var sign_value := 1.0 if side == "left" else -1.0
		joints[side+"_hip"].rotation.x = walk*.46*sign_value
		joints[side+"_knee"].rotation.x = maxf(0,-walk*sign_value)*.48
		joints[side+"_shoulder"].rotation = Vector3(-walk*.28*sign_value,0,-sign_value*.08)
		joints[side+"_elbow"].rotation.x = -.18
	joints.torso.rotation = Vector3(-hit_time*1.1,0,0)
	if role == "bow_guard":
		joints.left_shoulder.rotation.x = -1.30
		joints.right_shoulder.rotation = Vector3(-1.0,-.4,0)
		joints.right_elbow.rotation.x = -1.4 if attack_time > .18 else -.7
		joints.weapon.rotation.x = 1.30
	else:
		var swing := sin(clampf((.52-attack_time)/.52,0,1)*PI) if attack_time > 0 else 0.0
		joints.right_shoulder.rotation.x -= swing*1.30
		joints.right_elbow.rotation.x -= swing*.5
		joints.weapon.rotation.x = .38+swing*1.2
	if joints.has("banner"):
		joints.banner.rotation.y = sin(time*3.0)*.10
	if not alive:
		visual.position.y -= minf(dead_age,1.0)*.22
		visual.rotation.z = minf(dead_age/.65,1.0)*1.48
	if health_fill:
		health_fill.scale.x = maxf(.001,health/max_health)
		health_fill.position.x = -(1.0-health/max_health)*.39
	if arrow:
		var flight := (.52-attack_time)/.26
		arrow.visible = alive and attack_time > .26
		if arrow.visible:
			arrow.global_position = (global_position+Vector3.UP*1.4).lerp(attack_target+Vector3.UP,clampf(flight,0,1))
			var direction := attack_target+Vector3.UP-arrow.global_position
			if direction.length_squared() > .0001:
				arrow.quaternion = Quaternion(Vector3.UP,direction.normalized())

func articulation_finite() -> bool:
	if not position.is_finite() or not is_finite(health) or not is_finite(heading):
		return false
	for joint in joints.values():
		if not joint.transform.origin.is_finite() or not joint.rotation.is_finite():
			return false
	return true
