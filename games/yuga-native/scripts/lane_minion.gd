extends StaticBody3D
## Offline lane unit. One collider plus shared original articulated part meshes.

signal defeated(unit: Node3D, by_player: bool)

const Art = preload("res://scripts/lane_infantry_art.gd")
const VehicleArt = preload("res://scripts/lane_vehicle_art.gd")
const VEHICLE_ROLES := ["cannon_cart", "royal_chariot"]
const STATS := {
	"spearman":{"health":75.0,"damage":10.0,"range":2.15,"cooldown":1.10,"speed":3.8,"gold":18,"radius":.39,"height":1.9,"core_damage":7.0},
	"bow_guard":{"health":55.0,"damage":8.0,"range":11.0,"cooldown":1.50,"speed":3.6,"gold":24,"radius":.39,"height":1.9,"core_damage":7.0},
	"commander":{"health":150.0,"damage":13.0,"range":2.55,"cooldown":1.40,"speed":3.45,"gold":45,"radius":.39,"height":2.13,"core_damage":12.0},
	"cannon_cart":{"health":220.0,"damage":24.0,"range":18.0,"cooldown":4.0,"speed":2.8,"gold":70,"radius":.82,"height":1.8,"core_damage":20.0,"windup":.80,"attack_duration":1.20,"blast_radius":3.0},
	"royal_chariot":{"health":340.0,"damage":22.0,"range":5.5,"cooldown":2.6,"speed":3.1,"gold":110,"radius":.88,"height":2.4,"core_damage":25.0,"windup":.55,"attack_duration":1.0,"blast_radius":2.4}
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
var radius := .39
var vehicle_art: Dictionary = {}
var infantry_art: Dictionary = {}
# Invocation practice statuses use the army clock, never render time.
var shield := 0.0
var shield_until := 0.0
var slow_multiplier := 1.0
var slow_until := 0.0
var practice_summon := false
var summon_expires_at := 0.0
var summon_attack_damage := 0.0
var shield_fill: MeshInstance3D
var invalid_status := 0

func setup(owner_army: Node3D, identity: int, team_value: String, role_value: String, lane_value: int) -> void:
	army = owner_army
	unit_id = identity
	team = team_value
	role = role_value
	lane_id = lane_value
	max_health = float(STATS[role].health)
	radius = float(STATS[role].radius)
	health = max_health
	name = "%s_%s_%d" % [team,role,unit_id]

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	collision_layer = 4 if team == "moon" else 0
	collision_mask = 0
	add_to_group("lane_enemy" if team == "moon" else "lane_ally")
	shape = CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = radius
	capsule.height = float(STATS[role].height)
	shape.shape = capsule
	shape.position.y = capsule.height*.5
	add_child(shape)
	if render_art:
		var result: Dictionary = VehicleArt.build(team,role) if role in VEHICLE_ROLES else Art.build(team,role)
		if role in VEHICLE_ROLES:
			vehicle_art = result
		else:
			infantry_art = result
		visual = result.root
		joints = result.joints
		add_child(visual)
		var bar := Node3D.new()
		bar.position.y = 3.05 if role in VEHICLE_ROLES or role == "commander" else 2.10
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
		shield_fill = MeshInstance3D.new()
		var shield_mesh := BoxMesh.new()
		shield_mesh.size = Vector3(.78,.022,.07)
		shield_fill.mesh = shield_mesh
		var shield_color := StandardMaterial3D.new()
		shield_color.albedo_color = Color("b8ecfa")
		shield_color.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		shield_fill.material_override = shield_color
		shield_fill.position.y = .065
		shield_fill.visible = false
		bar.add_child(shield_fill)
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
	if is_instance_valid(army) and not army.winner.is_empty():
		return false
	var absorbed := minf(shield,float(amount))
	shield -= absorbed
	health = maxf(0.0,health-(float(amount)-absorbed))
	hit_time = .18
	if health <= 0:
		alive = false
		state = "fall"
		clear_statuses()
		collision_layer = 0
		target = null
		if not reward_emitted:
			reward_emitted = true
			if is_instance_valid(army):army._receiver_depth += 1
			defeated.emit(self,source == "player")
			if is_instance_valid(army):army._receiver_depth -= 1
	return true

func arrive() -> void:
	clear_statuses()
	alive = false
	state = "arrived"
	collision_layer = 0
	dead_age = 1.21
	target = null

func _status_number(value, lower: float, upper: float) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and float(value)>=lower and float(value)<=upper

func _status_available() -> bool:
	return alive and is_instance_valid(army) and army.winner.is_empty()

func receive_heal(amount) -> float:
	if not _status_number(amount,.000001,1000):invalid_status += 1;return 0.0
	if not _status_available():return 0.0
	var before := health
	health = minf(max_health,health+float(amount))
	_update_health_bar()
	return health-before

func apply_shield(amount, duration) -> bool:
	if not _status_number(amount,.000001,100) or not _status_number(duration,.000001,12):invalid_status += 1;return false
	if not _status_available():return false
	shield = maxf(shield,float(amount))
	shield_until = maxf(shield_until,float(army.elapsed)+float(duration))
	_update_health_bar()
	return true

func apply_slow(multiplier, duration) -> bool:
	if not _status_number(multiplier,.1,1) or not _status_number(duration,.000001,12):invalid_status += 1;return false
	if not _status_available():return false
	slow_multiplier = minf(slow_multiplier,float(multiplier))
	slow_until = maxf(slow_until,float(army.elapsed)+float(duration))
	return true

func step_statuses(now: float) -> void:
	if not is_finite(now) or now<0:return
	if not alive:clear_statuses();return
	if now+1e-8>=shield_until:shield = 0.0;shield_until = 0.0
	if now+1e-8>=slow_until:slow_multiplier = 1.0;slow_until = 0.0
	_update_health_bar()

func clear_statuses() -> void:
	shield = 0.0
	shield_until = 0.0
	slow_multiplier = 1.0
	slow_until = 0.0
	_update_health_bar()

func movement_multiplier() -> float:
	return slow_multiplier

func attack_damage() -> float:
	return summon_attack_damage if practice_summon else float(STATS[role].damage)

func core_damage() -> float:
	return 0.0 if practice_summon else float(STATS[role].core_damage)

func status_report() -> Dictionary:
	return {"shield":shield,"shield_until":shield_until,"speed_multiplier":slow_multiplier,"slow_until":slow_until,
		"temporary":practice_summon,"expires_at":summon_expires_at,"invalid_status":invalid_status}

func start_attack(point: Vector3) -> float:
	if not point.is_finite() or not alive:
		return 0.0
	attack_cooldown = float(STATS[role].cooldown)
	attack_time = float(STATS[role].get("attack_duration",.52))
	attack_target = point
	state = "siege_windup" if role in VEHICLE_ROLES else ("aim" if role == "bow_guard" else "swing")
	if role in VEHICLE_ROLES:
		return float(STATS[role].windup)
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
	if role in VEHICLE_ROLES:
		VehicleArt.pose(vehicle_art,role,time,moved,attack_time,hit_time,alive,dead_age)
		_update_health_bar()
		return
	Art.pose(infantry_art,time,moved,attack_time,hit_time,alive,unit_id)
	if not alive:
		visual.position.y -= minf(dead_age,1.0)*.22
		visual.rotation.z = minf(dead_age/.65,1.0)*1.48
	_update_health_bar()
	if arrow:
		Art.pose_arrow(infantry_art,arrow,attack_time,alive,attack_target)

func _update_health_bar() -> void:
	if is_instance_valid(shield_fill):
		shield_fill.visible = alive and shield>0
		shield_fill.scale.x = maxf(.001,shield/100.0)
		shield_fill.position.x = -(1.0-shield/100.0)*.39
	if health_fill:
		health_fill.scale.x = maxf(.001,health/max_health)
		health_fill.position.x = -(1.0-health/max_health)*.39

func _joint_finite(value) -> bool:
	if value is Node3D:
		return value.transform.is_finite()
	if value is Array:
		for child in value:
			if not _joint_finite(child):return false
		return true
	return false

func articulation_finite() -> bool:
	if not position.is_finite() or not is_finite(health) or not is_finite(heading) or not is_finite(shield) or not is_finite(slow_multiplier):
		return false
	for joint in joints.values():
		if not _joint_finite(joint):
			return false
	return true
