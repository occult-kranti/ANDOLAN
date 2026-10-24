extends CharacterBody3D
## Input-driven extraction of native player.gd's bounded locomotion core.
## No hero rendering, traversal powers, local Input singleton or client position writes.
var intent:Dictionary={}
var previous_jump:=false
var input_tick:=-1000
var processed_seq:=-1
var pitch:=0.0
var yaw:=0.0
var config:Dictionary={}
var reset_epoch:=0
var last_shot:Dictionary={}
var fire_remaining:=0.0

func configure(contract:Dictionary)->void:
	config=contract
	collision_layer=2
	collision_mask=1
	floor_snap_length=.3
	safe_margin=.001
	var capsule:=CapsuleShape3D.new()
	capsule.radius=float(config.capsuleRadius)
	capsule.height=float(config.capsuleHeight)
	var holder:=CollisionShape3D.new()
	holder.shape=capsule
	holder.position.y=capsule.height*.5
	add_child(holder)

func server_reset(feet:Vector3,epoch:int)->void:
	position=feet
	velocity=Vector3.ZERO
	intent={}
	previous_jump=false
	input_tick=-1000
	reset_epoch=epoch
	last_shot={}

func receive_input(value:Dictionary,tick:int)->void:
	if int(value.seq)<=processed_seq:return
	intent=value.duplicate(true)
	processed_seq=int(value.seq)
	input_tick=tick
	yaw=float(value.yaw)
	pitch=float(value.pitch)

func authority_step(delta:float,tick:int)->void:
	var current:Dictionary=intent if tick-input_tick<=21 else {}
	var move:=Vector2(float(current.get("moveX",0)),float(current.get("moveZ",0))).limit_length(1.0)
	# Protocol-2 movement is already world XZ, unlike local player camera-relative Input.
	var accel:=38.0 if is_on_floor() else 12.0
	velocity.x=move_toward(velocity.x,move.x*float(config.speed),accel*delta)
	velocity.z=move_toward(velocity.z,move.y*float(config.speed),accel*delta)
	var jumping:bool=current.get("jump",false)
	if is_on_floor():
		if jumping and not previous_jump:velocity.y=float(config.jumpSpeed)
	else:velocity.y-=float(config.gravity)*delta
	previous_jump=jumping
	move_and_slide()
	fire_remaining=maxf(0,fire_remaining-delta)
	if current.get("fire",false) and fire_remaining<=0:
		fire_remaining=.2
		var origin:=global_position+Vector3.UP
		var direction:=Vector3(sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch))
		var hit:=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(origin,origin+direction*20,5))
		last_shot={"nativeTick":tick,"target":String(hit.collider.get_meta("fixture_id","")) if not hit.is_empty() else "","pitch":pitch,"origin":[origin.x,origin.y,origin.z]}

func wire(tick:int)->Dictionary:
	var support:=get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(global_position+Vector3.UP*.1,global_position-Vector3.UP*.35,1))
	return {"x":position.x,"y":position.y,"z":position.z,"yaw":yaw,"pitch":pitch,"grounded":is_on_floor(),"velocity":[velocity.x,velocity.y,velocity.z],"bridgeAckSeq":processed_seq,"bridgeInputTick":input_tick,"bridgeEpoch":reset_epoch,"nativeTick":tick,"support":String(support.collider.get_meta("fixture_id","")) if not support.is_empty() else "","shot":last_shot}
