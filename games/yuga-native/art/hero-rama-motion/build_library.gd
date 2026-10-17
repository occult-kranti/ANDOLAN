extends SceneTree
## Original Rama trajectories. Uses only the project's CC0-compatible rest rig and
## its previously authored finger closure; no third-party motion is sampled.
const TARGET := "res://assets/heroes/rama-production.glb"
const OUTPUT := "res://assets/animations/rama_hero_motion.tres"
const CLIPS := {
	"idle": [2.4,true], "walk": [1.0,true], "run": [1.0,true], "sprint": [1.0,true],
	"aim": [1.8,true], "draw": [.18,false], "ready_draw": [.18,false], "release": [.22,false],
	"piercing_draw": [.65,false], "piercing_release": [.30,false],
	"circle_draw": [.55,false], "circle_release": [.30,false],
	"volley_draw": [.95,false], "volley_release": [.55,false],
	"jump": [.32,false], "fall": [.8,true], "land": [.22,false],
	"dash": [.30,false], "flight": [1.6,true], "grapple": [1.2,true],
	"hit": [.3,false], "death": [.9,false], "respawn": [.8,false],
}
var skeleton: Skeleton3D
var animator: AnimationPlayer
var rests: Array[Transform3D] = []
var globals: Array[Transform3D] = []
var grips := {}
var names: Array[String] = []
var report_path := "/tmp/rama-motion-library-build.json"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path=arg.trim_prefix("--report=")
	call_deferred("run")
func find_node(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := find_node(child,kind)
		if found: return found
	return null
func smooth(v: float) -> float:
	v=clampf(v,0,1)
	return v*v*(3-2*v)
func b(name_: String) -> int: return skeleton.find_bone(name_)
func gp(name_: String) -> Transform3D: return skeleton.get_bone_global_pose(b(name_))
func orient(name_: String, world: Quaternion) -> void:
	var index := b(name_)
	var parent := skeleton.get_bone_parent(index)
	var p := skeleton.get_bone_global_pose(parent).basis.get_rotation_quaternion() if parent>=0 else Quaternion.IDENTITY
	skeleton.set_bone_pose_rotation(index,(p.inverse()*world).normalized())
func rotate_world(name_: String, angles: Vector3) -> void:
	var index := b(name_)
	var q := Basis.from_euler(angles).get_rotation_quaternion()
	orient(name_,(q*globals[index].basis.get_rotation_quaternion()).normalized())
func aim(name_: String, direction: Vector3) -> void:
	var rest := globals[b(name_)].basis.orthonormalized()
	var delta := Quaternion(rest.y.normalized(),direction.normalized())
	orient(name_,(delta*rest.get_rotation_quaternion()).normalized())
func chain(side: String, kind: String, target: Vector3, pole: Vector3) -> void:
	var n1 := "upper%s01.%s"%[kind,side]
	var n2 := "upper%s02.%s"%[kind,side]
	var n3 := "lower%s01.%s"%[kind,side]
	var n4 := "lower%s02.%s"%[kind,side]
	var end := ("wrist." if kind=="arm" else "foot.")+side
	var a := rests[b(n2)].origin.length()+rests[b(n3)].origin.length()
	var c := rests[b(n4)].origin.length()+rests[b(end)].origin.length()
	var origin := gp(n1).origin
	var offset := target-origin
	var d := clampf(offset.length(),absf(a-c)+.002,a+c-.004)
	var direction := offset.normalized()
	var bend := pole-origin
	bend-=direction*bend.dot(direction)
	if bend.length_squared()<.00001: bend=Vector3.FORWARD.cross(direction)
	bend=bend.normalized()
	var along := (a*a-c*c+d*d)/(2*d)
	var elbow := origin+direction*along+bend*sqrt(maxf(0,a*a-along*along))
	for name_ in [n1,n2]: aim(name_,elbow-origin)
	for name_ in [n3,n4]: aim(name_,origin+direction*d-elbow)
func hand(side: String, target: Vector3, pole: Vector3, forward := Vector3(0,-.12,1), axis := Vector3.UP) -> void:
	chain(side,"arm",target,pole)
	var y := forward.normalized()
	var x := (axis-y*axis.dot(y)).normalized()
	var z := x.cross(y).normalized()
	orient("wrist."+side,Basis(x,y,z).get_rotation_quaternion())
func foot(side: String, target: Vector3, pitch := 0.0) -> void:
	chain(side,"leg",target,Vector3(target.x,.6,.8))
	orient("foot."+side,(Quaternion(Vector3.RIGHT,pitch)*globals[b("foot."+side)].basis.get_rotation_quaternion()).normalized())
func hips(height: float, side := 0.0) -> void:
	for name_ in ["pelvis.L","pelvis.R","spine05"]:
		var index := b(name_)
		var parent := skeleton.get_bone_parent(index)
		var pos := rests[index].origin+skeleton.get_bone_global_pose(parent).basis.inverse()*Vector3(side,height,0)
		skeleton.set_bone_pose_position(index,pos)
func grip(left_weight := .45) -> void:
	for name_ in grips:
		var q: Quaternion=grips[name_]
		if name_.ends_with(".L"): q=rests[b(name_)].basis.get_rotation_quaternion().slerp(q,left_weight).normalized()
		skeleton.set_bone_pose_rotation(b(name_),q)
func draw_string(amount: float) -> void:
	var parent := gp("wrist.R")
	var neutral := parent*rests[b("bowstring")].origin
	var contact := gp("wrist.L")*Vector3(.012613,.114969,-.042728)
	var target := neutral.lerp(contact,amount)
	skeleton.set_bone_pose_position(b("bowstring"),parent.affine_inverse()*target)
func arms(raise_amount: float, draw_amount: float, phase := 0.0, release_amount := 0.0) -> void:
	var bow := Vector3(-.33,1.05,.27).lerp(Vector3(-.11,1.58,.47),raise_amount)
	var string_hand := Vector3(.30,1.08,.23).lerp(Vector3(-.042272,1.56827,.12576),raise_amount)
	string_hand.z-=draw_amount*.15
	string_hand+=Vector3(.10,.015,-.12)*release_amount
	bow.y+=sin(phase*TAU)*.004*(1-raise_amount)
	hand("R",bow,Vector3(-.65,1.15,.14))
	hand("L",string_hand,Vector3(.58,1.48,-.18),Vector3(0,-.12,1))
	grip(lerpf(.45,1,smooth(raise_amount*4))*(1-release_amount*.90))
	draw_string(draw_amount*(1-release_amount))
func pose(clip: String, p: float) -> void:
	skeleton.reset_bone_poses()
	var wave := sin(p*TAU)
	var lift := 0.0
	var lean := 0.0
	var side := 0.0
	var raise_amount := 0.0
	var draw_amount := 0.0
	var release_amount := 0.0
	var ankle_l := Vector3(.16,.076,.025)
	var ankle_r := Vector3(-.16,.076,.025)
	if clip in ["walk","run","sprint"]:
		var duty := .62 if clip=="walk" else .29
		var reach := .34 if clip=="walk" else (.47 if clip=="sprint" else .43)
		var clearance := .10 if clip=="walk" else .25
		lift=(-.065 if clip=="walk" else -.125)+sin(p*TAU*2)*(.012 if clip=="walk" else .018)
		lean=.07 if clip=="walk" else (.19 if clip=="sprint" else .13)
		side=wave*(.015 if clip=="walk" else .008)
		for sign_ in [1,-1]:
			var phase := fposmod(p+(0.5 if sign_<0 else 0),1)
			var point := Vector3(sign_*.15,.076,0)
			if phase<duty:
				point.z=lerpf(reach,-reach,phase/duty)
			else:
				var swing := (phase-duty)/(1-duty)
				point.z=lerpf(-reach,reach,smooth(swing))
				point.y+=sin(swing*PI)*clearance
			if sign_>0: ankle_l=point
			else: ankle_r=point
	elif clip=="idle": lift=wave*.003
	elif clip=="aim": raise_amount=1; draw_amount=.78
	elif clip.ends_with("draw"):
		var q := smooth(p)
		raise_amount=smooth(p/.95)
		draw_amount=smooth((p-.18)/.82)
		if clip=="ready_draw": raise_amount=1
		elif clip=="piercing_draw": lean=-.025*q; lift=-.035*q
		elif clip=="volley_draw": lean=-.06*q; lift=-.06*q
		elif clip=="circle_draw":
			raise_amount=.55*q; draw_amount=0; lift=-.065*sin(p*PI)
	elif clip.ends_with("release"):
		raise_amount=1-smooth((p-.5)/.5)*.16
		draw_amount=1
		release_amount=smooth(p/.18)
		lean=-sin(minf(p/.35,1)*PI)*.055
		if clip=="circle_release": raise_amount=.55*(1-p); draw_amount=0; release_amount=0
	elif clip in ["jump","fall","land","dash","flight","grapple"]:
		if clip=="jump": lift=-.08*(1-smooth(p)); ankle_l.y+=.18*p; ankle_r.y+=.12*p; lean=.12
		elif clip=="fall": ankle_l.y+=.12; ankle_r.y+=.08; lean=.06
		elif clip=="land": lift=-.14*sin(p*PI); lean=.10*sin(p*PI)
		elif clip=="dash": lift=-.12*sin(p*PI); lean=.30*sin(p*PI); ankle_l.z=.27; ankle_r.z=-.28
		elif clip=="flight": ankle_l+=Vector3(0,.22,-.2); ankle_r+=Vector3(0,.28,-.24); lean=.22; lift=wave*.01
		elif clip=="grapple": ankle_l+=Vector3(0,.3,-.12); ankle_r+=Vector3(0,.18,-.25); lean=.28
	elif clip=="hit": lean=-sin(p*PI)*.16; lift=-sin(p*PI)*.05
	elif clip=="death": lift=-.56*smooth(p); lean=.55*smooth(p); ankle_l.z=.18; ankle_r.z=-.16
	elif clip=="respawn": lift=-.34*(1-smooth(p)); lean=.3*(1-smooth(p))
	hips(lift,side)
	rotate_world("spine05",Vector3(lean*.55,0,0))
	rotate_world("spine03",Vector3(lean*.80,wave*.025 if clip in ["walk","run","sprint"] else 0,0))
	rotate_world("spine01",Vector3(lean,0,0))
	rotate_world("head",Vector3(-lean*.1,0,0))
	foot("L",ankle_l)
	foot("R",ankle_r)
	arms(raise_amount,draw_amount,p,release_amount)
	if clip=="grapple": hand("L",Vector3(.27,1.78,.35),Vector3(.57,1.55,.1))
	if clip=="circle_draw":
		hand("L",Vector3(.30,1.08,.23).lerp(Vector3(.42,1.42,.38),smooth(p)),Vector3(.6,1.2,.05),Vector3(0,1,.2),Vector3.RIGHT)
		grip(.10)
	if clip in ["walk","run","sprint"]:
		hand("L",Vector3(.30,1.08,.23+wave*.11),Vector3(.5,1.1,-.08))
		grip()
func run() -> void:
	var model = load(TARGET).instantiate()
	root.add_child(model)
	skeleton=find_node(model,"Skeleton3D")
	animator=find_node(model,"AnimationPlayer")
	for index in skeleton.get_bone_count():
		rests.append(skeleton.get_bone_rest(index)); globals.append(skeleton.get_bone_global_rest(index)); names.append(skeleton.get_bone_name(index))
	var fire: Animation=animator.get_animation("fire")
	for track in fire.get_track_count():
		var path:=fire.track_get_path(track)
		if fire.track_get_type(track)!=Animation.TYPE_ROTATION_3D or path.get_subname_count()!=1: continue
		var name_:=String(path.get_subname(0))
		if name_.begins_with("finger"):
			var authored:=fire.rotation_track_interpolate(track,fire.length*(.08 if name_.ends_with(".L") else .25)).normalized()
			if name_.ends_with(".R"):
				var closure: float=[.25,.90,1.0,.80,1.0][int(name_.substr(6,1))-1]
				authored=rests[b(name_)].basis.get_rotation_quaternion().slerp(authored,closure).normalized()
			grips[name_]=authored
	animator.stop()
	var library:=AnimationLibrary.new()
	library.set_meta("rama_rig_rest",rests)
	library.set_meta("rama_rig_names",names)
	var parents:=PackedInt32Array()
	for index in skeleton.get_bone_count(): parents.append(skeleton.get_bone_parent(index))
	library.set_meta("rama_rig_parents",parents)
	var rows:=[]
	for clip in CLIPS:
		var anim:=Animation.new()
		anim.resource_name=clip
		anim.length=CLIPS[clip][0]
		anim.loop_mode=Animation.LOOP_LINEAR if CLIPS[clip][1] else Animation.LOOP_NONE
		for name_ in names:
			for type_ in [Animation.TYPE_ROTATION_3D,Animation.TYPE_POSITION_3D]:
				var track:=anim.add_track(type_)
				anim.track_set_path(track,NodePath(String(animator.get_node(animator.root_node).get_path_to(skeleton))+":"+name_))
				anim.track_set_interpolation_type(track,Animation.INTERPOLATION_LINEAR)
		var samples:=48 if CLIPS[clip][1] else maxi(16,int(ceil(anim.length*60)))
		for frame in samples+1:
			var p:=float(frame)/samples
			pose(clip,p)
			for index in names.size():
				anim.rotation_track_insert_key(index*2,p*anim.length,skeleton.get_bone_pose_rotation(index).normalized())
				anim.position_track_insert_key(index*2+1,p*anim.length,skeleton.get_bone_pose_position(index))
		# Remove exact constant channels and collapse static posed channels.
		for track in range(anim.get_track_count()-1,-1,-1):
			var type_:=anim.track_get_type(track)
			var index:=b(String(anim.track_get_path(track).get_subname(0)))
			var first=anim.track_get_key_value(track,0)
			var constant:=true
			for key in anim.track_get_key_count(track):
				var v=anim.track_get_key_value(track,key)
				if type_==Animation.TYPE_ROTATION_3D and first.angle_to(v)>.00001: constant=false
				elif type_==Animation.TYPE_POSITION_3D and first.distance_to(v)>.000001: constant=false
			if constant:
				var baseline=rests[index].basis.get_rotation_quaternion().normalized() if type_==Animation.TYPE_ROTATION_3D else rests[index].origin
				var same: bool=first.angle_to(baseline)<.00001 if type_==Animation.TYPE_ROTATION_3D else first.distance_to(baseline)<.000001
				if same: anim.remove_track(track)
				else:
					for key in range(anim.track_get_key_count(track)-1,0,-1): anim.track_remove_key(track,key)
		library.add_animation(clip,anim)
		rows.append({"clip":clip,"length":anim.length,"samples":samples+1,"loop":CLIPS[clip][1]})
	var error:=ResourceSaver.save(library,OUTPUT)
	var report={"passed":error==OK,"generator":"Original contact/target-authored trajectories; existing project finger rotation calibration only.","target_sha256":FileAccess.get_sha256(TARGET),"output_sha256":FileAccess.get_sha256(OUTPUT),"bone_count":names.size(),"clips":rows}
	DirAccess.make_dir_recursive_absolute(report_path.get_base_dir())
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify(report))
	quit(0 if error==OK else 1)
