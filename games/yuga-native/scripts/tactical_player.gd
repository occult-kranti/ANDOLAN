extends CharacterBody3D
## First-person movement for Casual. No automatic resurrection or legacy flight.
const Weapon = preload("res://scripts/tactical_weapon.gd")
var camera:Camera3D
var weapon:Node3D
var host:Node
var yaw:=0.0
var pitch:=0.0
var sensitivity:=.0025
var base_fov:=90.0
var enabled:=true
var dash_time:=0.0
var dash_direction:=Vector3.ZERO
var moved:=0.0
var _step_distance:=0.0

func _ready()->void:
	collision_layer=2; collision_mask=1; floor_snap_length=.25
	set_meta("actor_id",0)
	var shape:=CollisionShape3D.new(); var capsule:=CapsuleShape3D.new(); capsule.radius=.30; capsule.height=1.8; shape.shape=capsule; shape.position.y=.9; add_child(shape)
	camera=Camera3D.new(); camera.position.y=1.62; camera.near=.04; camera.far=220; camera.fov=base_fov; camera.current=true; add_child(camera)
	weapon=Weapon.new(); camera.add_child(weapon)

func aim(relative:Vector2)->void:
	if not enabled:return
	yaw-=relative.x*sensitivity; pitch=clampf(pitch-relative.y*sensitivity,-1.42,1.42)
	rotation.y=yaw; camera.rotation.x=pitch

func simulate(delta:float)->void:
	if not enabled:return
	var input:=Input.get_vector("tac_left","tac_right","tac_forward","tac_back")
	var direction:=global_basis*Vector3(input.x,0,input.y)
	var speed:=3.1 if Input.is_action_pressed("tac_walk") else 6.5
	if weapon.ads:speed*=.65
	if dash_time>0:
		dash_time=maxf(0,dash_time-delta); direction=dash_direction; speed=20.0
	velocity.x=move_toward(velocity.x,direction.x*speed,delta*45)
	velocity.z=move_toward(velocity.z,direction.z*speed,delta*45)
	if is_on_floor():
		velocity.y=-.1
		if Input.is_action_just_pressed("tac_jump"):velocity.y=6.4
	else:velocity.y-=18*delta
	var before:=position
	move_and_slide()
	moved=Vector2(velocity.x,velocity.z).length()
	_step_distance+=position.distance_to(before)
	if _step_distance>2.2 and is_on_floor():
		_step_distance=0
		if is_instance_valid(host):host.play_cue("step",global_position,.20 if speed<4 else .45)
	weapon.moving=moved
	weapon.step(delta)
	camera.fov=lerpf(camera.fov,base_fov*.72 if weapon.ads else base_fov,minf(1,delta*13))

func reset_at(at:Vector3,facing:float,weapon_id:String)->void:
	global_position=at+Vector3(0,.05,0); yaw=facing; pitch=0; rotation.y=yaw; camera.rotation=Vector3.ZERO; camera.position=Vector3(0,1.62,0)
	velocity=Vector3.ZERO; dash_time=0; moved=0; _step_distance=0
	weapon.equip(weapon_id,true); weapon.ads=false; weapon.visible=true; collision_layer=2

func dash()->bool:
	if not enabled or not is_on_floor():return false
	var input:=Input.get_vector("tac_left","tac_right","tac_forward","tac_back")
	dash_direction=(global_basis*Vector3(input.x,0,input.y)).normalized() if input.length()>.1 else -global_basis.z
	dash_time=.30
	return true

func stop_input()->void:
	weapon.ads=false; velocity.x=0; velocity.z=0; dash_time=0
