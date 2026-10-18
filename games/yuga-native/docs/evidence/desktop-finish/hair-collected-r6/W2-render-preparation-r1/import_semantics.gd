extends SceneTree
## Loads already imported resources only. No editor, GLTF import or scene tick.
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	call_deferred("run")

func digest(value: Variant) -> String:
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(var_to_bytes(value))
	return hash.finish().hex_encode()

func mat_record(material: Material) -> Dictionary:
	var values := {}
	for property in material.get_property_list():
		if (int(property.usage) & PROPERTY_USAGE_STORAGE) == 0: continue
		var key: String = property.name
		if key in ["resource_path","resource_scene_unique_id"]: continue
		var value: Variant = material.get(key)
		if value is Texture2D:
			var image: Image = value.get_image()
			values[key] = {"class":value.get_class(),"path":value.resource_path,
				"width":image.get_width(),"height":image.get_height(),"format":image.get_format(),
				"mipmaps":image.get_mipmap_count(),"pixels":digest(image.get_data())}
		else: values[key] = digest(value)
	return {"class":material.get_class(),"name":material.resource_name,"properties":values}

func run() -> void:
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): quit(2); return
	DirAccess.make_dir_recursive_absolute(output)
	var result := {"scope":"Actual imported resource payload only; no runtime controller, rendering or import.","engine":Engine.get_version_info(),"lods":[]}
	for label in ["rama-hero","rama-hero-mid","rama-hero-far"]:
		var path: String = "res://assets/heroes/" + label + ".glb"
		var packed: PackedScene = load(path)
		if packed == null: quit(3); return
		var instance: Node = packed.instantiate()
		var entry := {"path":path,"raw_sha256":FileAccess.get_sha256(path),"descriptor_sha256":FileAccess.get_sha256(path+".import"),"nodes":[]}
		var config := ConfigFile.new()
		if config.load(path+".import") != OK: quit(4); return
		entry["imported_path"] = config.get_value("remap","path","")
		entry["imported_sha256"] = FileAccess.get_sha256(entry.imported_path)
		var all_nodes := [instance]
		all_nodes.append_array(instance.find_children("*","",true,false))
		for node_index in all_nodes.size():
			var node: Node = all_nodes[node_index]
			var item := {"path":String(instance.get_path_to(node)),"class":node.get_class()}
			if node is Node3D: item["transform"] = digest(node.transform)
			if node is Skeleton3D:
				var order := []
				var rests := []
				for index in node.get_bone_count():
					order.append({"index":index,"name":String(node.get_bone_name(index)),"parent":node.get_bone_parent(index)})
					rests.append([node.get_bone_rest(index),node.get_bone_pose(index)])
				item["bone_order"] = order
				item["rests_and_poses"] = digest(rests)
			if node is MeshInstance3D and node.mesh:
				var surfaces := []
				for surface in node.mesh.get_surface_count():
					var arrays: Array = node.mesh.surface_get_arrays(surface)
					var material: Material = node.mesh.surface_get_material(surface)
					var array_info := []
					for index in arrays.size():
						var array: Variant = arrays[index]
						var info := {"index":index,"type":type_string(typeof(array)),"digest":digest(array)}
						if array != null:
							var raw: PackedByteArray = array if array is PackedByteArray else array.to_byte_array()
							var file: String = label+"-node"+str(node_index)+"-surface"+str(surface)+"-array"+str(index)+".bin"
							FileAccess.open(output.path_join(file),FileAccess.WRITE).store_buffer(raw)
							info["file"] = file; info["bytes"] = raw.size(); info["count"] = array.size()
						array_info.append(info)
					var morph_arrays: Array = node.mesh.surface_get_blend_shape_arrays(surface)
					var morph_info := []
					for shape_index in morph_arrays.size():
						var channels := []
						var shape: Array = morph_arrays[shape_index]
						for channel in shape.size():
							var value: Variant = shape[channel]
							var info := {"index":channel,"type":type_string(typeof(value)),"digest":digest(value)}
							if value != null:
								var raw: PackedByteArray = value if value is PackedByteArray else value.to_byte_array()
								var file: String = label+"-node"+str(node_index)+"-surface"+str(surface)+"-shape"+str(shape_index)+"-array"+str(channel)+".bin"
								FileAccess.open(output.path_join(file),FileAccess.WRITE).store_buffer(raw)
								info["file"] = file; info["bytes"] = raw.size(); info["count"] = value.size()
							channels.append(info)
						morph_info.append(channels)
					surfaces.append({"morph_arrays":morph_info,"arrays":array_info,"material":mat_record(material),"primitive":node.mesh.surface_get_primitive_type(surface),"format":node.mesh.surface_get_format(surface),"morphs":digest(node.mesh.surface_get_blend_shape_arrays(surface))})
				item["surfaces"] = surfaces; item["aabb"] = digest(node.mesh.get_aabb())
				var binds := []
				if node.skin:
					for index in node.skin.get_bind_count(): binds.append([String(node.skin.get_bind_name(index)),node.skin.get_bind_bone(index),node.skin.get_bind_pose(index)])
				item["bind_names_and_matrices"] = digest(binds)
				item["bind_names"] = []
				for bind in binds: item.bind_names.append([bind[0],bind[1]])
				var shapes := []
				for index in node.mesh.get_blend_shape_count(): shapes.append(String(node.mesh.get_blend_shape_name(index)))
				item["morph_names"] = shapes
				item["morph_mode"] = node.mesh.blend_shape_mode
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
			entry.nodes.append(item)
		result.lods.append(entry)
		instance.free()
	result["complete"] = result.lods.size() == 3
	FileAccess.open(output.path_join("semantics.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"  ",true,true)+"\n")
	print("IMPORTED_SEMANTICS ",result.lods.size())
	quit(0)
