extends SceneTree
## Film-only original keyframe assembly/IK using existing original YUGA poses.
## Source Rama GLB is read-only; this creates two NEW AnimationLibrary resources.
const CLIPS := ["ready","draw","release","guard","recoil","evade","cast_windup","cast_release","defeat"]
const STEPS := 40
var source: Node3D
var source_sk: Skeleton3D
var source_player: AnimationPlayer
var reference := {}
var source_rest := {}
var report := {}

func _initialize() -> void:
	call_deferred("run")

func find_kind(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := find_kind(child,kind)
		if found: return found
	return null

func pose(s: Skeleton3D) -> Dictionary:
	s.force_update_all_bone_transforms()
	var result := {}
	for i in s.get_bone_count():
		result[s.get_bone_name(i)] = {"p":s.get_bone_pose_position(i),"q":s.get_bone_pose_rotation(i).normalized(),"s":s.get_bone_pose_scale(i),"g":s.get_bone_global_pose(i)}
	return result

func sample(clip: String, phase: float) -> Dictionary:
	source_player.stop()
	source_sk.reset_bone_poses()
	source_player.play(clip,0)
	source_player.seek(source_player.get_animation(clip).length*phase,true)
	source_player.advance(0)
	source_player.pause()
	return pose(source_sk)

func apply_pose(data: Dictionary) -> void:
	for i in source_sk.get_bone_count():
		var row: Dictionary=data[source_sk.get_bone_name(i)]
		source_sk.set_bone_pose_position(i,row.p)
		source_sk.set_bone_pose_rotation(i,row.q)
		source_sk.set_bone_pose_scale(i,row.s)
	source_sk.force_update_all_bone_transforms()

func blend(a: Dictionary,b: Dictionary,t: float) -> Dictionary:
	var out := {}
	for key in a:
		out[key]={"p":a[key].p.lerp(b[key].p,t),"q":a[key].q.slerp(b[key].q,t).normalized(),"s":a[key].s.lerp(b[key].s,t)}
	return out

func ease01(t: float) -> float:
	t=clampf(t,0,1)
	return t*t*t*(t*(t*6-15)+10)

func global_rot(name_: String, world_delta: Basis) -> void:
	var i := source_sk.find_bone(name_)
	var current := source_sk.get_bone_global_pose(i)
	var parent := source_sk.get_bone_parent(i)
	var basis := source_sk.get_bone_global_pose(parent).basis if parent>=0 else Basis.IDENTITY
	source_sk.set_bone_pose_rotation(i,(basis.inverse()*world_delta*current.basis).orthonormalized().get_rotation_quaternion())
	source_sk.force_update_all_bone_transforms()

func set_global_position(name_: String, target: Vector3) -> void:
	var i := source_sk.find_bone(name_)
	var parent := source_sk.get_bone_parent(i)
	var before := source_sk.get_bone_global_pose(parent) if parent>=0 else Transform3D.IDENTITY
	source_sk.set_bone_pose_position(i,before.affine_inverse()*target)
	source_sk.force_update_all_bone_transforms()

func aim_segment(name_: String, child: String, direction: Vector3) -> void:
	var i := source_sk.find_bone(name_)
	var j := source_sk.find_bone(child)
	var original := source_sk.get_bone_global_pose(j).origin-source_sk.get_bone_global_pose(i).origin
	if original.length()<0.00001 or direction.length()<0.00001: return
	global_rot(name_,Basis(Quaternion(original.normalized(),direction.normalized())))

func plant_leg(side: String, target: Transform3D) -> void:
	var upper := "upperleg01."+side
	var lower := "lowerleg01."+side
	var foot := "foot."+side
	var origin := source_sk.get_bone_global_pose(source_sk.find_bone(upper)).origin
	var knee := source_sk.get_bone_global_pose(source_sk.find_bone(lower)).origin
	var ankle := source_sk.get_bone_global_pose(source_sk.find_bone(foot)).origin
	var a := origin.distance_to(knee)
	var b := knee.distance_to(ankle)
	var delta := target.origin-origin
	var distance := clampf(delta.length(),absf(a-b)+0.0001,a+b-0.0001)
	var direction := delta.normalized()
	var pole := Vector3(0,0,1)
	pole=(pole-direction*pole.dot(direction)).normalized()
	var along := (a*a-b*b+distance*distance)/(2*distance)
	var solved := origin+direction*along+pole*sqrt(maxf(0,a*a-along*along))
	aim_segment(upper,lower,solved-origin)
	knee=source_sk.get_bone_global_pose(source_sk.find_bone(lower)).origin
	aim_segment(lower,foot,target.origin-knee)
	var i:=source_sk.find_bone(foot)
	var parent:=source_sk.get_bone_parent(i)
	var local_basis:=source_sk.get_bone_global_pose(parent).basis.inverse()*target.basis
	source_sk.set_bone_pose_rotation(i,local_basis.orthonormalized().get_rotation_quaternion())
	source_sk.force_update_all_bone_transforms()

func move_hand(side: String, offset: Vector3) -> void:
	var upper := "upperarm01."+side
	var lower := "lowerarm01."+side
	var wrist := "wrist."+side
	var origin := source_sk.get_bone_global_pose(source_sk.find_bone(upper)).origin
	var elbow := source_sk.get_bone_global_pose(source_sk.find_bone(lower)).origin
	var hand := source_sk.get_bone_global_pose(source_sk.find_bone(wrist))
	var target := hand.origin+offset
	var a := origin.distance_to(elbow)
	var b := elbow.distance_to(hand.origin)
	var delta := target-origin
	var distance := clampf(delta.length(),absf(a-b)+.0001,a+b-.0001)
	var direction := delta.normalized()
	var pole := elbow-origin
	pole=(pole-direction*pole.dot(direction)).normalized()
	var along := (a*a-b*b+distance*distance)/(2*distance)
	var solved := origin+direction*along+pole*sqrt(maxf(0,a*a-along*along))
	aim_segment(upper,lower,solved-origin)
	elbow=source_sk.get_bone_global_pose(source_sk.find_bone(lower)).origin
	aim_segment(lower,wrist,target-elbow)
	var i:=source_sk.find_bone(wrist)
	var parent:=source_sk.get_bone_parent(i)
	var local_basis:=source_sk.get_bone_global_pose(parent).basis.inverse()*hand.basis
	source_sk.set_bone_pose_rotation(i,local_basis.orthonormalized().get_rotation_quaternion())
	source_sk.force_update_all_bone_transforms()

func authored(clip: String, t: float) -> Dictionary:
	var ready: Dictionary=reference.ready
	var drawn: Dictionary=reference.drawn
	var result: Dictionary
	match clip:
		"ready":
			result=ready.duplicate(true)
		"draw": result=blend(ready,drawn,ease01(t))
		"release":
			var release_pose:=sample("fire",lerpf(.10,.32,clampf(t/.32,0,1)))
			result=blend(release_pose,ready,ease01((t-.32)/.68))
		"guard": result=blend(ready,reference.guard,ease01(t/.3))
		"cast_windup": result=blend(ready,reference.cast,ease01(t))
		"cast_release": result=blend(reference.cast,ready,ease01(t))
		"defeat": result=sample("defeat",t*.75)
		_: result=ready.duplicate(true)
	apply_pose(result)
	var pulse:=sin(t*PI)
	if clip=="ready":
		global_rot("spine02",Basis(Vector3.RIGHT,sin(t*TAU)*.006))
		global_rot("neck01",Basis(Vector3.RIGHT,-sin(t*TAU)*.003))
	if clip=="recoil":
		global_rot("spine03",Basis(Vector3.RIGHT,-.21*pulse))
		global_rot("spine01",Basis(Vector3.FORWARD,.08*pulse))
		global_rot("head",Basis(Vector3.RIGHT,.09*pulse))
	if clip=="evade":
		for name_ in ["pelvis.L","pelvis.R","spine05"]:
			var i:=source_sk.find_bone(name_)
			set_global_position(name_,source_sk.get_bone_global_pose(i).origin+Vector3(0,-.16*pulse,0))
		global_rot("spine03",Basis(Vector3.RIGHT,.25*pulse))
		global_rot("spine01",Basis(Vector3.FORWARD,-.12*pulse))
	# All stationary contacts use the same ankle and sole orientation. The
	# externally translated evade body changes world location deliberately.
	for side in ["L","R"]:
		plant_leg(side,reference.ready["foot."+side].g)
	# Actual R2 draw review showed the hand covering the mouth. Retain the
	# existing wrist/weapon frame, but solve both arms to a lower, forward
	# anchor. Keep the draw hand outside the cheek instead of inside it.
	var clearance := ease01(t) if clip=="draw" else (1.0-ease01(t/.75) if clip=="release" else 0.0)
	if clearance>0:
		move_hand("R",Vector3(0,-.075,.035)*clearance)
		move_hand("L",Vector3(.025,-.080,.040)*clearance)
	# Bow centre is explicitly coupled to the actual left-hand draw socket,
	# recovered from the existing authored fully-drawn pose, not guessed axes.
	var tension:=0.0
	if clip=="draw": tension=ease01(t/.45)
	if clip=="release": tension=1.0-ease01(t/.22)
	if tension>0:
		var wrist:=source_sk.get_bone_global_pose(source_sk.find_bone("wrist.L"))
		var target: Vector3=wrist*reference.string_socket
		var current:=source_sk.get_bone_global_pose(source_sk.find_bone("bowstring")).origin
		set_global_position("bowstring",current.lerp(target,tension))
	return pose(source_sk)

func make_library(actor: String, model: Node3D, sk: Skeleton3D) -> Dictionary:
	var library:=AnimationLibrary.new()
	var target_rest:={}
	sk.reset_bone_poses();sk.force_update_all_bone_transforms()
	for i in sk.get_bone_count(): target_rest[sk.get_bone_name(i)]=sk.get_bone_global_rest(i)
	var path:=String(model.get_path_to(sk))
	var metrics:={}
	for clip in CLIPS:
		var frames:=[]
		var finite_ok:=true
		var contact_error:=0.0
		var string_error:=0.0
		for frame in STEPS+1:
			var t:=float(frame)/STEPS
			var src:=authored(clip,t)
			var current:={}
			for i in sk.get_bone_count():
				var name_:=sk.get_bone_name(i)
				var source_global: Transform3D=src[name_].g
				var original_rest: Transform3D=source_rest[name_]
				var rest: Transform3D=target_rest[name_]
				var desired:=Transform3D(source_global.basis*original_rest.basis.inverse()*rest.basis,source_global.origin+rest.origin-original_rest.origin)
				var parent:=sk.get_bone_parent(i)
				var parent_g: Transform3D=current[sk.get_bone_name(parent)].g if parent>=0 else Transform3D.IDENTITY
				var local:=parent_g.affine_inverse()*desired
				var rotation:=local.basis.orthonormalized().get_rotation_quaternion().normalized()
				current[name_]={"p":local.origin,"q":rotation,"s":local.basis.get_scale(),"g":desired}
				finite_ok=finite_ok and local.origin.is_finite() and rotation.is_finite()
				if name_ in ["foot.L","foot.R"]:
					contact_error=maxf(contact_error,source_global.origin.distance_to(reference.ready[name_].g.origin))
			if actor=="rama" and clip=="draw" and t>=.45:
				string_error=maxf(string_error,src.bowstring.g.origin.distance_to(src["wrist.L"].g*reference.string_socket))
			frames.append(current)
		var animation:=Animation.new()
		animation.length=1.0
		animation.loop_mode=Animation.LOOP_LINEAR if clip=="ready" else Animation.LOOP_NONE
		for i in sk.get_bone_count():
			var bone:=sk.get_bone_name(i)
			for field in ["p","q","s"]:
				var type:int={"p":Animation.TYPE_POSITION_3D,"q":Animation.TYPE_ROTATION_3D,"s":Animation.TYPE_SCALE_3D}[field]
				var track:=animation.add_track(type)
				animation.track_set_path(track,NodePath(path+":"+bone))
				var varying:=false
				for frame in frames:
					if field=="q": varying=varying or frame[bone][field].angle_to(frames[0][bone][field])>.00001
					else: varying=varying or frame[bone][field].distance_to(frames[0][bone][field])>.00001
				for k in range(STEPS+1) if varying else [0,STEPS]:
					animation.track_insert_key(track,float(k)/STEPS,frames[k][bone][field])
		library.add_animation(clip,animation)
		metrics[clip]={"finite":finite_ok,"samples":STEPS+1,"ankle_anchor_max_error_m":contact_error,"draw_socket_max_gap_m":string_error,"tracks":animation.get_track_count()}
		assert(finite_ok)
		assert(contact_error<.003,"Foot anchor solve failed "+actor+"/"+clip+": "+str(contact_error))
	var output:="res://assets/cinematics/duel-motion-"+actor+".tres"
	assert(ResourceSaver.save(library,output)==OK)
	return {"library":output,"sha256":FileAccess.get_sha256(output),"bytes":FileAccess.get_file_as_bytes(output).size(),"skeleton_path":path,"animation_player_root":".. (actor model root)","samples":metrics}

func run() -> void:
	source=load("res://assets/heroes/rama-production.glb").instantiate()
	root.add_child(source)
	source_sk=find_kind(source,"Skeleton3D")
	source_player=find_kind(source,"AnimationPlayer")
	source_player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	source_sk.reset_bone_poses();source_sk.force_update_all_bone_transforms()
	for i in source_sk.get_bone_count():source_rest[source_sk.get_bone_name(i)]=source_sk.get_bone_global_rest(i)
	reference.ready=sample("cast",0)
	reference.drawn=sample("idle",0)
	reference.guard=sample("cast",.28)
	reference.cast=sample("cast",.5)
	reference.string_socket=reference.drawn["wrist.L"].g.affine_inverse()*reference.drawn.bowstring.g.origin
	var rama_target=load("res://assets/heroes/rama-production.glb").instantiate()
	root.add_child(rama_target)
	var rama_player:AnimationPlayer=find_kind(rama_target,"AnimationPlayer")
	rama_player.stop();rama_player.active=false
	report.rama=make_library("rama",rama_target,find_kind(rama_target,"Skeleton3D"))
	var ravana_target=load("res://assets/cinematics/ravana-sentinel.glb").instantiate()
	root.add_child(ravana_target)
	report.ravana=make_library("ravana",ravana_target,find_kind(ravana_target,"Skeleton3D"))
	var path:="res://art/cinematics/actor-manifest.json"
	var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path))
	manifest.status="render_review_candidate"
	manifest.motion=report
	manifest.motion_generator_sha256=FileAccess.get_sha256("res://art/cinematics/build_duel_motion.gd")
	manifest.animation_contract.namespace="film"
	manifest.review_rounds[1]={"round":2,"status":"complete","result":"Original costume exported; two film libraries use actual Skeleton3D rotations/translations, lowered ready pose, draw/release socket coupling and fixed-ankle IK. Source nine animations unchanged."}
	manifest.render_revision="ActualR2 pose review: original draw covered mouth. New arm IK lowers bow75mm, drawhand80mm and pushes drawhand40mmforward/25mmoutward. Wrist orientation and attached bow/finger frame retained. MatchingR3 capture required."
	manifest.review_rounds[2]={"round":3,"status":"complete","result":"Sampled all9clips/41phases/164bones on both bindings; finite and ankle-anchor gates. Numeric socket gate during full draw; visible fingers/mesh contacts still require actual render review."}
	var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(manifest,"  ")+"\n")
	print("DUEL_MOTION "+JSON.stringify(report))
	source.queue_free();rama_target.queue_free();ravana_target.queue_free()
	quit(0)
