extends Node3D
## Absolute-time original-film posing; no physics, accumulated tween or root motion.
var actor_id := ""
var model: Node3D
var skeleton: Skeleton3D
var animator: AnimationPlayer
var animation_namespace := "film"
var clip_id := "ready"
var clip_phase := 0.0
var pose_finite := true
var pose_digest := ""
var material_overrides := 0
var errors: Array[String] = []

func _find(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var result:=_find(child,kind)
		if result: return result
	return null

func configure(spec: Dictionary) -> Array[String]:
	actor_id=spec.id
	animation_namespace=spec.get("animation_namespace","film")
	if not ResourceLoader.exists(spec.model_path) or not ResourceLoader.exists(spec.animation_library_path):
		errors.append(actor_id+": required actor model or film library is missing")
		return errors
	var packed=load(spec.model_path)
	var source_library=load(spec.animation_library_path)
	if not packed is PackedScene or not source_library is AnimationLibrary:
		errors.append(actor_id+": invalid model/library resource type")
		return errors
	model=packed.instantiate()
	model.name="ActorModel"
	add_child(model)
	_prepare_film_materials(model)
	skeleton=_find(model,"Skeleton3D")
	animator=_find(model,"AnimationPlayer")
	if skeleton==null:
		errors.append(actor_id+": actor has no Skeleton3D")
		return errors
	if animator==null:
		animator=AnimationPlayer.new()
		animator.name="AnimationPlayer"
		animator.root_node=NodePath("..")
		model.add_child(animator)
	animator.root_node=animator.get_path_to(model)
	animator.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var library: AnimationLibrary=source_library.duplicate(true)
	for name_ in library.get_animation_list():
		var clip:=library.get_animation(name_)
		clip.loop_mode=Animation.LOOP_NONE
		for track in clip.get_track_count():
			var path:=clip.track_get_path(track)
			var root_: Node=animator.get_node(animator.root_node)
			if path.get_subname_count()!=1 or root_.get_node_or_null(NodePath(path.get_concatenated_names()))!=skeleton or skeleton.find_bone(path.get_subname(0))<0:
				errors.append(actor_id+": unresolved animation track "+str(path))
	animator.add_animation_library(animation_namespace,library)
	return errors

func _prepare_film_materials(node: Node) -> void:
	if node is MeshInstance3D:
		for surface in node.mesh.get_surface_count():
			var original: Material=node.get_active_material(surface)
			if not original is StandardMaterial3D: continue
			var name_:=String(original.resource_name).to_lower()
			var kind:="skin" if name_.contains("skin") else "cloth" if name_.contains("silk") or name_.contains("cloth") else "hair" if name_.contains("hair") else "gold" if name_.contains("gold") else "armor" if name_.contains("bronze") or name_.contains("armour") or name_.contains("armor") else ""
			if kind.is_empty(): continue
			var material: StandardMaterial3D=original.duplicate()
			material.roughness_texture=null
			match kind:
				"skin":
					material.roughness=.82
					material.metallic=0
					material.metallic_specular=.20
					material.normal_scale=.18
				"cloth":
					material.roughness=.90
					material.metallic=0
					material.metallic_specular=.18
					material.normal_scale=.22
				"hair":
					material.roughness=.70
					material.metallic_specular=.25
				"gold":
					material.roughness=.43
					material.metallic=.75
				"armor":
					material.roughness=.58
					material.metallic=.55
			node.set_surface_override_material(surface,material)
			material_overrides+=1
	for child in node.get_children(): _prepare_film_materials(child)

func has_clip(name_: String) -> bool:
	return animator!=null and animator.has_animation(animation_namespace+"/"+name_)

func _pose(name_: String, normalized: float) -> Array[Transform3D]:
	animator.stop()
	skeleton.reset_bone_poses()
	var full:=animation_namespace+"/"+name_
	var clip:=animator.get_animation(full)
	animator.play(full,0)
	animator.seek(clampf(normalized,0,1)*clip.length,true)
	animator.advance(0)
	skeleton.force_update_all_bone_transforms()
	var result: Array[Transform3D]=[]
	for bone in skeleton.get_bone_count(): result.append(skeleton.get_bone_pose(bone))
	return result

func sample(name_: String, normalized: float, prior: String="", prior_phase: float=1.0, blend: float=1.0) -> void:
	clip_id=name_
	clip_phase=clampf(normalized,0,1)
	var current:=_pose(name_,clip_phase)
	if not prior.is_empty() and blend<1:
		var before:=_pose(prior,prior_phase)
		for bone in current.size():
			var a:=before[bone]
			var b:=current[bone]
			var rotation:=a.basis.get_rotation_quaternion().slerp(b.basis.get_rotation_quaternion(),blend)
			var scale_:=a.basis.get_scale().lerp(b.basis.get_scale(),blend)
			skeleton.set_bone_pose_position(bone,a.origin.lerp(b.origin,blend))
			skeleton.set_bone_pose_rotation(bone,rotation)
			skeleton.set_bone_pose_scale(bone,scale_)
	else:
		for bone in current.size(): skeleton.set_bone_pose(bone,current[bone])
	skeleton.force_update_all_bone_transforms()
	pose_finite=true
	var values:=PackedFloat32Array()
	for bone in skeleton.get_bone_count():
		var pose:=skeleton.get_bone_global_pose(bone)
		pose_finite=pose_finite and pose.is_finite()
		values.append_array([pose.origin.x,pose.origin.y,pose.origin.z])
		for axis in 3: values.append_array([pose.basis[axis].x,pose.basis[axis].y,pose.basis[axis].z])
	var context:=HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(values.to_byte_array())
	pose_digest=context.finish().hex_encode()

func socket(name_: String) -> Vector3:
	var bone_name:="wrist.R" if name_=="bow" else "spine01" if name_=="chest" else "root"
	var bone:=skeleton.find_bone(bone_name)
	return skeleton.global_transform*skeleton.get_bone_global_pose(bone).origin if bone>=0 else global_position

func snapshot(detailed: bool=false) -> Dictionary:
	var result:={"actor_id":actor_id,"position":[position.x,position.y,position.z],"yaw":rotation.y,"clip":clip_id,"phase":clip_phase,"finite":pose_finite,"pose_sha256":pose_digest,"bones":skeleton.get_bone_count() if skeleton else 0,"film_material_overrides":material_overrides}
	if detailed and skeleton:
		var bones:={}
		for bone in skeleton.get_bone_count():
			var transform_:=skeleton.get_bone_global_pose(bone)
			bones[skeleton.get_bone_name(bone)]={"position":[transform_.origin.x,transform_.origin.y,transform_.origin.z],"rotation":str(transform_.basis.get_rotation_quaternion())}
		result.bone_poses=bones
	return result
