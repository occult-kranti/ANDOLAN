extends CharacterBody3D
## Tactical wardens reuse YUGA's original articulated infantry, with firearm poses.
const Art=preload("res://scripts/lane_infantry_art.gd")
var actor_id:=1
var team:="sun"
var alive:=true
var art:Dictionary
var clock:=0.0
var shot_time:=0.0
var body_visual:Node3D
var rifle:Node3D
var last_position:=Vector3.ZERO

func _ready()->void:
	collision_layer=2;collision_mask=1;floor_snap_length=.3;set_meta("actor_id",actor_id)
	var collision:=CollisionShape3D.new();var shape:=CapsuleShape3D.new();shape.radius=.34;shape.height=1.82;collision.shape=shape;collision.position.y=.91;add_child(collision)
	art=Art.build(team,"spearman");body_visual=art.root;add_child(body_visual)
	art.joints.weapon.hide();art.joints.shield.hide()
	rifle=Node3D.new();art.joints.torso.add_child(rifle);rifle.position=Vector3(.04,.18,.26)
	var material:=StandardMaterial3D.new();material.albedo_color=Color("192b43");material.metallic=.45;material.roughness=.4
	var brass:=StandardMaterial3D.new();brass.albedo_color=Color("c9aa67");brass.metallic=.75
	for spec in [[Vector3(.10,.12,.36),Vector3.ZERO,material],[Vector3(.12,.022,.38),Vector3(0,.07,0),brass],[Vector3(.06,.16,.09),Vector3(0,-.10,.02),material],[Vector3(.05,.05,.28),Vector3(0,.02,.28),brass]]:
		var node:=MeshInstance3D.new();var mesh:=BoxMesh.new();mesh.size=spec[0];node.mesh=mesh;node.position=spec[1];node.material_override=spec[2];rifle.add_child(node)
	var marker:=Label3D.new();marker.text="WARDEN %02d"%actor_id;marker.font_size=32;marker.pixel_size=.007;marker.position.y=2.1;marker.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	marker.modulate=Color("b9ead8") if team=="sun" else Color("f3a18e");marker.no_depth_test=false;add_child(marker)

func step(delta:float)->void:
	clock+=delta;shot_time=maxf(0,shot_time-delta)
	var actual_speed:=global_position.distance_to(last_position)/maxf(.001,delta);last_position=global_position
	Art.pose(art,clock,actual_speed*.03,0,shot_time,alive,actor_id)
	if alive:
		Art._arm(art.joints,"left",Vector3(-.02,.14,.47))
		Art._arm(art.joints,"right",Vector3(.09,.10,.22))
		rifle.position.z=.26-shot_time*.12
		body_visual.rotation.z=0
	else:body_visual.rotation.z=lerp_angle(body_visual.rotation.z,PI/2,minf(1,delta*8))

func move_towards(target:Vector3,delta:float)->void:
	if not alive:return
	var flat:=target-global_position;flat.y=0
	var direction:=flat.normalized() if flat.length()>.25 else Vector3.ZERO
	velocity.x=direction.x*4.8;velocity.z=direction.z*4.8
	velocity.y=-.1 if is_on_floor() else velocity.y-18*delta
	move_and_slide()
	if direction.length()>.1:rotation.y=lerp_angle(rotation.y,atan2(direction.x,direction.z),minf(1,delta*10))

func face(target:Vector3)->void:
	var d:=target-global_position
	if Vector2(d.x,d.z).length()>.1:rotation.y=atan2(d.x,d.z)

func reset_at(at:Vector3)->void:
	global_position=at+Vector3(0,.06,0);last_position=global_position;velocity=Vector3.ZERO;alive=true;collision_layer=2;body_visual.rotation.z=0;shot_time=0

func die()->void:
	alive=false;collision_layer=0;velocity=Vector3.ZERO
