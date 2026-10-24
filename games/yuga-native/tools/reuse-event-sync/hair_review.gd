extends SceneTree
## Independent W5 numerical skin/placement review. No asset fixes or rendering.
const Adapter = preload("res://tools/hero-donor-groom/mpfb_native/native_candidate.gd")
const Motion = preload("res://scripts/rama_motion.gd")
var base := ""
var hair := ""
var wrong_hair := ""
var output := ""
var checks: Array = []
var clip_rows: Array = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--base="): base=arg.trim_prefix("--base=")
		elif arg.begins_with("--hair="): hair=arg.trim_prefix("--hair=")
		elif arg.begins_with("--wrong-hair="): wrong_hair=arg.trim_prefix("--wrong-hair=")
		elif arg.begins_with("--output="): output=arg.trim_prefix("--output=")
	call_deferred("run")

func check(name_: String, passed: bool, details: Variant = null) -> void:
	checks.append({"name":name_,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",name_)

func load_model(path: String) -> Node3D:
	var document := GLTFDocument.new()
	var state := GLTFState.new()
	if document.append_from_file(path,state)!=OK:return null
	return document.generate_scene(state) as Node3D

func first(node: Node, kind: String) -> Node:
	if node.is_class(kind):return node
	for child in node.get_children():
		var found := first(child,kind)
		if found:return found
	return null

func setup(path: String, transform_: Transform3D = Transform3D.IDENTITY) -> Dictionary:
	var model := load_model(base)
	root.add_child(model)
	model.global_transform=transform_
	var motion := Motion.new()
	if not motion.configure(model,first(model,"AnimationPlayer")):return {"ok":false,"model":model}
	motion.active=false
	var attached := Adapter.attach(model,path)
	if not attached.ok:return {"ok":false,"model":model,"attached":attached}
	return {"ok":true,"model":model,"motion":motion,"rig":motion.rig,"mesh":attached.mesh,"attached":attached}

func vertices(fixture: Dictionary) -> Dictionary:
	# Read actual imported mesh/skin arrays independently of Adapter.points and
	# Contacts.skin. Include the rig's world transform explicitly.
	var mesh: MeshInstance3D=fixture.mesh
	var rig: Skeleton3D=fixture.rig
	var result:=PackedVector3Array()
	var head_only:=true
	var weight_error:=0.0
	var invalid:=0
	for surface in mesh.mesh.get_surface_count():
		var arrays:=mesh.mesh.surface_get_arrays(surface)
		var positions:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var joints:PackedInt32Array=arrays[Mesh.ARRAY_BONES]
		var weights:PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
		var stride:int=joints.size()/positions.size()
		for vertex in positions.size():
			var value:=Vector3.ZERO
			var total:=0.0
			for slot in stride:
				var weight:float=weights[vertex*stride+slot]
				if weight<=0:continue
				var bind:int=joints[vertex*stride+slot]
				var name_:=mesh.skin.get_bind_name(bind)
				var bone:=rig.find_bone(name_) if not str(name_).is_empty() else mesh.skin.get_bind_bone(bind)
				if bone<0 or bone>=rig.get_bone_count():invalid+=1;continue
				head_only=head_only and rig.get_bone_name(bone)==&"head"
				value+=(rig.get_bone_global_pose(bone)*mesh.skin.get_bind_pose(bind)*positions[vertex])*weight
				total+=weight
			weight_error=maxf(weight_error,absf(1-total))
			result.append(rig.global_transform*value)
	return {"points":result,"head_only":head_only,"weight_error":weight_error,"invalid":invalid}

func max_distance(a: PackedVector3Array,b: PackedVector3Array, transform_: Transform3D=Transform3D.IDENTITY) -> float:
	if a.size()!=b.size():return INF
	var result:=0.0
	for index in a.size():result=maxf(result,(transform_*a[index]).distance_to(b[index]))
	return result

func run() -> void:
	if not base.is_absolute_path() or not hair.is_absolute_path() or not wrong_hair.is_absolute_path() or not output.is_absolute_path() or FileAccess.file_exists(output):quit(2);return
	var identity := setup(hair)
	check("positive isolated candidate attaches",identity.ok)
	if not identity.ok:identity.model.free();finish();return
	identity.rig.reset_bone_poses()
	var rest:=vertices(identity)
	check("independent actual arrays contain2304head-onlyunitweightedvertices",rest.points.size()==2304 and rest.head_only and rest.invalid==0 and rest.weight_error<.000001,{"count":rest.points.size(),"weight_error":rest.weight_error})
	check("only canonical164bone owner drives transferredskin",identity.rig.get_bone_count()==164 and identity.mesh.get_node(identity.mesh.skeleton)==identity.rig)
	var placement:=Transform3D(Basis(Vector3.UP,.6),Vector3(7,3,-5))
	identity.model.global_transform=placement
	var moved:=vertices(identity)
	var move_error:=max_distance(rest.points,moved.points,placement)
	check("attach-before-placement world covariance",move_error<.00001,{"maximum_error_m":move_error})
	var preplaced := setup(hair,placement)
	check("preplaced model candidate attaches",preplaced.ok)
	if preplaced.ok:
		preplaced.rig.reset_bone_poses()
		var sampled:=vertices(preplaced)
		var error:=max_distance(rest.points,sampled.points,placement)
		check("attach-after-placement aligns with same moved hero",error<.00001,{"maximum_error_m":error,"expected_world_translation":[7,3,-5]})
	preplaced.model.free()
	identity.model.global_transform=Transform3D.IDENTITY
	var head:int=identity.rig.find_bone("head")
	var reference_head:Transform3D=identity.rig.get_bone_global_pose(head)
	for clip in identity.motion.library.get_animation_list():
		var distinct:=[]
		for normalized in [0.0,.25,.5,.75,1.0]:
			var pose:Dictionary=identity.motion._sample(clip,normalized)
			for bone in identity.rig.get_bone_count():
				identity.rig.set_bone_pose_position(bone,pose.positions[bone])
				identity.rig.set_bone_pose_rotation(bone,pose.rotations[bone])
			var current:=vertices(identity)
			var head_transform:Transform3D=identity.rig.get_bone_global_pose(head)*reference_head.affine_inverse()
			var deviation:=max_distance(rest.points,current.points,head_transform)
			var finite:=true
			for point in current.points:finite=finite and point.is_finite()
			var signature:=str(identity.rig.get_bone_global_pose(head))
			if not signature in distinct:distinct.append(signature)
			clip_rows.append({"clip":clip,"normalized":normalized,"finite":finite,"head_rigid_error_m":deviation,"head_global_pose":signature})
		check("%s fiveactualskinposes follow observedhead" % str(clip),clip_rows.slice(clip_rows.size()-5).all(func(row):return row.finite and row.head_rigid_error_m<.00001),{"distinct_head_poses":distinct.size()})
	check("exact23externalclips115sampledposes",identity.motion.library.get_animation_list().size()==23 and clip_rows.size()==115)
	var wrong:=setup(wrong_hair)
	check("wrong-head negative remains importable",wrong.ok)
	if wrong.ok:
		var sampled:=vertices(wrong)
		check("independenteligibilityrejectswrong-headweights",not sampled.head_only and sampled.points.size()==2304 and sampled.invalid==0,{"head_only":sampled.head_only,"invalid":sampled.invalid})
	wrong.model.free();identity.model.free();finish()

func finish() -> void:
	var passed:=checks.all(func(row):return row.passed)
	var report:={"schema":1,"passed":passed,"checks":checks,"clip_rows":clip_rows,"source_pins":{"base":FileAccess.get_sha256(base),"hair":FileAccess.get_sha256(hair),"negative_hair":FileAccess.get_sha256(wrong_hair),"adapter":FileAccess.get_sha256("res://tools/hero-donor-groom/mpfb_native/native_candidate.gd"),"motion":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"probe":FileAccess.get_sha256(get_script().resource_path)},"scope":"Independent head-only skin and transform eligibility, no rendered/contact/secondarymotion/LOD/hardware acceptance"}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	quit(0 if passed else 1)
