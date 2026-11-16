extends Node3D
## Effects have bounded lifetimes on the same paused match clock as the authority.
const VeilShader=preload("res://shaders/tactical_veil.gdshader")
const WardShader=preload("res://shaders/tactical_ward.gdshader")
const PulseShader=preload("res://shaders/tactical_pulse.gdshader")
var effects:Array[Dictionary]=[]
var smoke:Array[Dictionary]=[]
var materials:Dictionary={}

func mat(key:String,color:Color,emission:=0.0,alpha:=false)->StandardMaterial3D:
	if materials.has(key):return materials[key]
	var m:=StandardMaterial3D.new();m.albedo_color=color;m.roughness=.7
	if emission>0:m.emission_enabled=true;m.emission=color;m.emission_energy_multiplier=emission
	if alpha:m.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;m.cull_mode=BaseMaterial3D.CULL_DISABLED
	materials[key]=m;return m

func mesh(parent:Node3D,geometry:Mesh,material:Material,at:Vector3)->MeshInstance3D:
	var node:=MeshInstance3D.new();node.mesh=geometry;node.material_override=material;node.position=at;parent.add_child(node);return node

func trace(from:Vector3,to:Vector3,solar:=false,enemy:=false)->void:
	var distance:=from.distance_to(to)
	if distance<.01:return
	var geometry:=CylinderMesh.new();geometry.top_radius=.025 if solar else .008;geometry.bottom_radius=geometry.top_radius;geometry.height=distance;geometry.radial_segments=6
	var color:=Color("ffb3a1") if enemy else Color("ffe1a0")
	var node:=mesh(self,geometry,mat("solar" if solar else ("hostile" if enemy else "trace"),color,2.1),(from+to)*.5)
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Distinct solar releases remain visible but do not join into one persistent beam.
	node.quaternion=Quaternion(Vector3.UP,(to-from).normalized());effects.append({"node":node,"life":.16 if solar else .10,"duration":.16 if solar else .10,"kind":"trace"})
	var impact:=SphereMesh.new();impact.radius=.07 if solar else .025;impact.height=impact.radius*2;impact.radial_segments=8;impact.rings=4
	var spark:=mesh(self,impact,mat("spark",Color("ffe7b2"),3),to);effects.append({"node":spark,"life":.15,"duration":.15,"kind":"spark"})

func veil(at:Vector3)->void:
	var root:=Node3D.new();root.position=at;add_child(root)
	var sphere:=SphereMesh.new();sphere.radius=4.2;sphere.height=8.4;sphere.radial_segments=32;sphere.rings=16
	var material:=ShaderMaterial.new();material.shader=VeilShader
	mesh(root,sphere,material,Vector3(0,1.0,0))
	for i in 3:
		var ring:=TorusMesh.new();ring.inner_radius=4.15;ring.outer_radius=4.22;ring.rings=32;ring.ring_segments=8
		var node:=mesh(root,ring,mat("veil_ring",Color("e3c58a"),.4),Vector3(0,float(i)-.1,0));node.rotation.x=i*.35
	var entry:={"node":root,"life":12.0,"duration":12.0,"kind":"smoke","center":at+Vector3.UP,"radius":4.2,"material":material}
	effects.append(entry);smoke.append(entry)

func throw_veil(from:Vector3,to:Vector3)->void:
	var seed:=SphereMesh.new();seed.radius=.10;seed.height=.20;seed.radial_segments=16;seed.rings=8
	var node:=mesh(self,seed,mat("seed",Color("ffcf7a"),2),from)
	effects.append({"node":node,"life":.55,"duration":.55,"kind":"veil_seed","from":from,"to":to})

func ward(at:Vector3,yaw:float)->void:
	var body:=StaticBody3D.new();body.position=at;body.rotation.y=yaw;body.collision_layer=1;body.collision_mask=0;body.set_meta("ward_health",180.0);add_child(body)
	var geometry:=BoxMesh.new();geometry.size=Vector3(6,2.65,.32)
	var material:=ShaderMaterial.new();material.shader=WardShader
	mesh(body,geometry,material,Vector3(0,1.325,0))
	var collision:=CollisionShape3D.new();var shape:=BoxShape3D.new();shape.size=geometry.size;collision.shape=shape;collision.position.y=1.325;body.add_child(collision)
	for x in [-3,-1.5,0,1.5,3]:
		var pillar:=BoxMesh.new();pillar.size=Vector3(.06,2.8,.40);mesh(body,pillar,mat("ward_gold",Color("e4bf70"),1),Vector3(x,1.4,0))
	effects.append({"node":body,"life":10.0,"duration":10.0,"kind":"ward","material":material})

func burst(at:Vector3,color:=Color("edc27d"))->void:
	var ring:=TorusMesh.new();ring.inner_radius=.36;ring.outer_radius=.368;ring.rings=64;ring.ring_segments=8
	var material:=ShaderMaterial.new();material.shader=PulseShader;material.set_shader_parameter("tint",color)
	var n:=mesh(self,ring,material,at+Vector3(0,.045,0));n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.append({"node":n,"life":.65,"duration":.65,"kind":"burst","material":material})

func step(delta:float)->void:
	var blooms:Array[Vector3]=[]
	for entry in effects:
		entry.life-=delta
		if not is_instance_valid(entry.node):continue
		if entry.has("material"):entry.material.set_shader_parameter("age",entry.duration-entry.life)
		if entry.kind=="ward" and float(entry.node.get_meta("ward_health",0))<=0:entry.life=0
		if entry.kind=="burst":
			var progress:float=clampf(1.0-entry.life/entry.duration,0.0,1.0)
			entry.node.scale=Vector3.ONE*(1.0+sqrt(progress)*7.0)
		if entry.kind=="veil_seed":
			var progress:=clampf(1.0-entry.life/entry.duration,0,1)
			entry.node.position=entry.from.lerp(entry.to,progress)+Vector3(0,sin(progress*PI)*1.7,0)
			if entry.life<=0:blooms.append(entry.to)
		if entry.life<=0:remove_child(entry.node);entry.node.queue_free()
	effects=effects.filter(func(e):return e.life>0 and is_instance_valid(e.node))
	smoke=smoke.filter(func(e):return e.life>0 and is_instance_valid(e.node))
	for at in blooms:veil(at);burst(at)

func obscured(from:Vector3,to:Vector3)->bool:
	var segment:=to-from;var length:=segment.length_squared()
	for entry in smoke:
		var t:=clampf((entry.center-from).dot(segment)/maxf(.001,length),0,1)
		if (from+segment*t).distance_to(entry.center)<entry.radius:return true
	return false

func clear()->void:
	for entry in effects:
		if is_instance_valid(entry.node):remove_child(entry.node);entry.node.queue_free()
	effects.clear();smoke.clear()
