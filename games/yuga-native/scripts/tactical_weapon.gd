extends Node3D
## Original procedural Surya weapon family. Ammunition and recovery own each shot.
const PROFILES := {
	"pistol": {"name":"ARKA / solar sidearm", "magazine":12, "reserve":36, "damage":28.0, "interval":.28, "reload":1.55, "spread":.009},
	"carbine": {"name":"SURYA / mythic carbine", "magazine":24, "reserve":72, "damage":34.0, "interval":.12, "reload":2.1, "spread":.013}
}
var weapon_id := "pistol"
var ammo := 12
var reserve := 36
var recovery := 0.0
var reload_remaining := 0.0
var recoil := 0.0
var ads := false
var reduced_motion := false
var moving := 0.0
var clock := 0.0
var model: Node3D
var magazine: Node3D
var muzzle: MeshInstance3D
var support_hand:Node3D
var base_position := Vector3(.24,-.22,-.58)
var _materials := {}

func _ready() -> void:
	_build()

func equip(id: String, refill := true) -> void:
	if id not in PROFILES: return
	var changed := weapon_id != id
	weapon_id = id
	if refill:
		ammo = int(PROFILES[id].magazine); reserve = int(PROFILES[id].reserve)
		reload_remaining = 0.0; recovery = 0.0
	if changed and is_inside_tree(): _build()

func step(delta: float) -> void:
	clock += delta
	recovery = maxf(0, recovery-delta)
	recoil = move_toward(recoil, 0, delta*4)
	if reload_remaining > 0:
		reload_remaining = maxf(0, reload_remaining-delta)
		if reload_remaining == 0:
			var amount := mini(int(PROFILES[weapon_id].magazine)-ammo,reserve)
			ammo += amount; reserve -= amount
	if not is_instance_valid(model): return
	var amount := 0.0 if reduced_motion else minf(moving/6.0,1.0)
	var target := Vector3(0,-.112,-.40) if ads else base_position
	position = position.lerp(target + Vector3(sin(clock*10)*.008,absf(cos(clock*10))*.008,0)*amount, minf(1,delta*14))
	var progress := reload_progress()
	model.rotation = Vector3(recoil*.10,0,recoil*-.04)
	model.position = Vector3(0,0,recoil*.045)
	if reload_remaining > 0:
		model.rotation.z -= sin(progress*PI)*.65
		model.position.y -= sin(progress*PI)*.15
	if is_instance_valid(magazine): magazine.position.y = -.1 - sin(progress*PI)*.25 if reload_remaining>0 else -.1
	if is_instance_valid(support_hand):
		var reach:=sin(progress*PI) if reload_remaining>0 else 0.0
		support_hand.position=Vector3(-.02,-.075,-.30).lerp(Vector3(-.04,-.20,-.14),reach)
		support_hand.position.y-=reach*.18
		support_hand.rotation.z=-.7+reach*.45
	if is_instance_valid(muzzle): muzzle.visible = recovery > float(PROFILES[weapon_id].interval)-.045

func fire() -> bool:
	if ammo <= 0 or recovery>0 or reload_remaining>0: return false
	ammo -= 1; recovery = float(PROFILES[weapon_id].interval); recoil = minf(1.8,recoil+.8)
	return true

func reload() -> bool:
	if reload_remaining>0 or ammo>=int(PROFILES[weapon_id].magazine) or reserve<=0: return false
	reload_remaining = float(PROFILES[weapon_id].reload)
	return true

func reload_progress() -> float:
	return 1.0-reload_remaining/float(PROFILES[weapon_id].reload) if reload_remaining>0 else 0.0

func _mat(id: String, color: Color, metal := 0.0, emission := 0.0) -> StandardMaterial3D:
	if _materials.has(id): return _materials[id]
	var m := StandardMaterial3D.new(); m.albedo_color=color; m.metallic=metal; m.roughness=.35 if metal>.5 else .7
	if emission>0: m.emission_enabled=true; m.emission=color; m.emission_energy_multiplier=emission
	_materials[id]=m
	return m

func _box(parent: Node3D, size: Vector3, at: Vector3, material: Material) -> MeshInstance3D:
	var n:=MeshInstance3D.new(); n.mesh=_beveled_box(size); n.material_override=material; n.position=at; parent.add_child(n); return n

func _beveled_box(size:Vector3)->ArrayMesh:
	# Six faces, twelve bevel strips and eight corners; actual geometry catches light.
	var h:=size*.5;var bevel:=minf(.007,minf(size.x,minf(size.y,size.z))*.18)
	var surface:=SurfaceTool.new();surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for axis in 3:
		var u:=(axis+1)%3;var v:=(axis+2)%3
		for sign_value in [-1.0,1.0]:
			var points:Array[Vector3]=[]
			for pair in [Vector2(-1,-1),Vector2(1,-1),Vector2(1,1),Vector2(-1,1)]:
				var p:=Vector3.ZERO;p[axis]=h[axis]*sign_value;p[u]=(h[u]-bevel)*pair.x;p[v]=(h[v]-bevel)*pair.y;points.append(p)
			_face(surface,points)
	for axis in 3:
		var u:=(axis+1)%3;var v:=(axis+2)%3
		for su in [-1.0,1.0]:
			for sv in [-1.0,1.0]:
				var points:Array[Vector3]=[]
				for pair in [Vector2(-1,0),Vector2(1,0),Vector2(1,1),Vector2(-1,1)]:
					var p:=Vector3.ZERO;p[axis]=(h[axis]-bevel)*pair.x;p[u]=(h[u]-(bevel if pair.y==0 else 0))*su;p[v]=(h[v]-(0 if pair.y==0 else bevel))*sv;points.append(p)
				_face(surface,points)
	for x in [-1.0,1.0]:
		for y in [-1.0,1.0]:
			for z in [-1.0,1.0]:
				var points:Array[Vector3]=[]
				for axis in 3:
					var p:=(h-Vector3.ONE*bevel)*Vector3(x,y,z);p[axis]=h[axis]*[x,y,z][axis];points.append(p)
				_face(surface,points)
	surface.generate_normals();surface.index();return surface.commit()

func _face(surface:SurfaceTool,points:Array[Vector3])->void:
	var center:=Vector3.ZERO
	for p in points:center+=p
	center/=points.size()
	# Godot clockwise front faces; retain outward normals on all bevels.
	if (points[1]-points[0]).cross(points[2]-points[0]).dot(center)>0:points.reverse()
	for i in range(1,points.size()-1):
		for p in [points[0],points[i],points[i+1]]:surface.add_vertex(p)

func _cylinder(parent:Node3D, radius:float, length:float, at:Vector3, material:Material, axis_z:=false) -> MeshInstance3D:
	var n:=MeshInstance3D.new(); var mesh:=CylinderMesh.new(); mesh.top_radius=radius; mesh.bottom_radius=radius; mesh.height=length; mesh.radial_segments=16; n.mesh=mesh; n.material_override=material; n.position=at
	if axis_z: n.rotation.x=PI/2
	parent.add_child(n); return n

func _build() -> void:
	if is_instance_valid(model): remove_child(model); model.queue_free()
	support_hand=null
	model=Node3D.new(); model.name="SuryaOriginalWeapon"; add_child(model)
	var brass:=_mat("brass",Color("b89750"),.8)
	var edge:=_mat("edge",Color("eed198"),.7)
	var indigo:=_mat("indigo",Color("162a43"),.35)
	var dark:=_mat("dark",Color("121a22"),.4)
	var crystal:=_mat("crystal",Color("ffc66c"),.2,1.1)
	var skin:=_mat("skin",Color("965e3d"))
	var cloth:=_mat("cloth",Color("25365d"))
	var long_gun:=weapon_id=="carbine"
	_box(model,Vector3(.105,.13,.29 if long_gun else .20),Vector3(0,0,-.12),indigo)
	_box(model,Vector3(.115,.012,.25),Vector3(0,.073,-.11),brass)
	_box(model,Vector3(.065,.11,.17),Vector3(0,-.075,.02),dark).rotation.x=-.28
	_cylinder(model,.026,.36 if long_gun else .15,Vector3(0,.018,-.36 if long_gun else -.22),dark,true)
	_cylinder(model,.032,.05,Vector3(0,.018,-.55 if long_gun else -.31),brass,true)
	for i in (6 if long_gun else 3):
		_box(model,Vector3(.125,.025,.012),Vector3(0,.025,-.12-float(i)*.035),brass)
	_box(model,Vector3(.025,.018,.045),Vector3(0,.105,-.21),edge)
	_box(model,Vector3(.012,.028,.018),Vector3(-.036,.09,-.02),brass)
	_box(model,Vector3(.012,.028,.018),Vector3(.036,.09,-.02),brass)
	_box(model,Vector3(.007,.012,.01),Vector3(0,.113,-.21),crystal)
	_cylinder(model,.046,.112,Vector3(0,-.005,-.04),crystal,true)
	for z in [-.005,-.075]: _cylinder(model,.052,.014,Vector3(0,-.005,z),brass,true)
	for x in [-1,1]:
		_box(model,Vector3(.009,.078,.105),Vector3(x*.055,.0,-.045),brass)
		_box(model,Vector3(.011,.060,.085),Vector3(x*.058,.0,-.045),crystal)
		for slope in [-1,1]:
			var brace:=_box(model,Vector3(.012,.008,.102),Vector3(x*.065,0,-.045),brass);brace.rotation.x=slope*.55
		for z in [-.19,-.14,-.085,.02]:
			var bolt:=_cylinder(model,.007,.005,Vector3(x*.057,-.045,z),edge);bolt.rotation.z=PI/2
		for i in 4:
			var inset:=_box(model,Vector3(.004,.018,.022),Vector3(x*.055,.015,-.09-i*.027),edge); inset.rotation.x=.5
	magazine=Node3D.new(); magazine.position=Vector3(0,-.1,-.14); model.add_child(magazine)
	_box(magazine,Vector3(.067,.14 if long_gun else .06,.08),Vector3(0,-.04,0),indigo)
	_box(magazine,Vector3(.078,.024,.089),Vector3(0,-.11 if long_gun else -.07,0),brass)
	# Hands are original articulated geometry with wrapped bracers and individual fingers.
	_hand(model,Vector3(.028,-.105,.025),skin,cloth,brass,false)
	if long_gun:
		support_hand=_hand(model,Vector3(-.02,-.075,-.30),skin,cloth,brass,true)
		_box(model,Vector3(.055,.08,.12),Vector3(0,-.012,.095),indigo)
		_box(model,Vector3(.08,.13,.025),Vector3(0,-.03,.16),brass)
	muzzle=_cylinder(model,.055,.16,Vector3(0,.018,-.64 if long_gun else -.40),_mat("flash",Color("ffe5a3"),0,4),true)
	muzzle.visible=false
	position=base_position

func _hand(parent:Node3D, at:Vector3, skin:Material, cloth:Material, brass:Material, support:bool)->Node3D:
	var hand:=Node3D.new(); hand.position=at; parent.add_child(hand)
	if support: hand.rotation.z=-.7
	_box(hand,Vector3(.072,.10,.05),Vector3.ZERO,skin)
	for i in 4:
		var finger:=_cylinder(hand,.010,.040,Vector3(-.028+i*.018,.030,-.024),skin)
		finger.rotation.x=1.15
		var tip:=_cylinder(hand,.009,.027,Vector3(-.028+i*.018,.023,-.047),skin);tip.rotation.x=2.2
		var knuckle:=SphereMesh.new();knuckle.radius=.011;knuckle.height=.024;knuckle.radial_segments=10;knuckle.rings=5
		var joint:=MeshInstance3D.new();joint.mesh=knuckle;joint.material_override=skin;joint.position=Vector3(-.028+i*.018,.030,-.040);hand.add_child(joint)
	_cylinder(hand,.014,.055,Vector3(.04,.018,-.015),skin).rotation.z=-.55
	_cylinder(hand,.045,.23,Vector3(.018,-.15,.018),cloth).rotation.z=.12
	for y in [-.07,-.12,-.20]: _cylinder(hand,.047,.018,Vector3(.01,y,.01),brass)
	return hand
