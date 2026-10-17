extends SceneTree
## Load existing imported PackedScenes only; no editor or GLTF import here.
func _initialize() -> void:
	call_deferred("run")

func digest(value: Variant) -> String:
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(var_to_bytes(value))
	return hash.finish().hex_encode()

func run() -> void:
	var report_path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
	var lods := []
	for name in ["rama-hero","rama-hero-mid","rama-hero-far"]:
		var path: String = "res://assets/heroes/"+name+".glb"
		var packed: PackedScene = load(path)
		var instance: Node = packed.instantiate()
		var nodes := []
		for node in instance.find_children("*","",true,false):
			var item := {"path":String(instance.get_path_to(node)),"class":node.get_class()}
			if node is Node3D: item["transform_sha256"] = digest(node.transform)
			if node is MeshInstance3D and node.mesh:
				var surfaces := []
				for surface in node.mesh.get_surface_count():
					var material: Material = node.mesh.surface_get_material(surface)
					surfaces.append({"arrays":digest(node.mesh.surface_get_arrays(surface)),"morphs":digest(node.mesh.surface_get_blend_shape_arrays(surface)),"primitive":node.mesh.surface_get_primitive_type(surface),"format":node.mesh.surface_get_format(surface),"material_name":material.resource_name if material else "","material_class":material.get_class() if material else ""})
				item["surfaces"] = surfaces
				item["aabb_sha256"] = digest(node.mesh.get_aabb())
				item["blend_shape_mode"] = node.mesh.blend_shape_mode
				var shapes := []
				for index in node.mesh.get_blend_shape_count(): shapes.append(String(node.mesh.get_blend_shape_name(index)))
				item["blend_shape_names"] = shapes
				var binds := []
				if node.skin:
					for index in node.skin.get_bind_count(): binds.append([String(node.skin.get_bind_name(index)),node.skin.get_bind_bone(index),node.skin.get_bind_pose(index)])
				item["skin_binds_sha256"] = digest(binds)
			if node is Skeleton3D:
				var bones := []
				for index in node.get_bone_count(): bones.append([String(node.get_bone_name(index)),node.get_bone_parent(index),node.get_bone_rest(index),node.get_bone_pose(index)])
				item["bones_sha256"] = digest(bones)
				item["bone_count"] = node.get_bone_count()
			if node is AnimationPlayer:
				var animations := {}
				for key in node.get_animation_list():
					var animation: Animation = node.get_animation(key)
					var tracks := []
					for track in animation.get_track_count():
						var keys := []
						for index in animation.track_get_key_count(track): keys.append([animation.track_get_key_time(track,index),animation.track_get_key_transition(track,index),animation.track_get_key_value(track,index)])
						tracks.append([String(animation.track_get_path(track)),animation.track_get_type(track),animation.track_get_interpolation_type(track),animation.track_get_interpolation_loop_wrap(track),keys])
					animations[String(key)] = digest([animation.length,animation.loop_mode,tracks])
				item["animations"] = animations
			nodes.append(item)
		lods.append({"path":path,"source_sha256":FileAccess.get_sha256(path),"nodes":nodes,"payload_sha256":digest(nodes)})
		instance.free()
	var report := {"complete":lods.size()==3,"lods":lods,"scope":"Actual ResourceLoader imported mesh arrays, morph arrays, AABBs, material slots, skin binds, skeleton rests/poses, animations and node transforms. Source hashes deliberately remain separate from semantic payload hashes."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("IMPORTED_PAYLOADS ",lods.size())
	quit(0)
