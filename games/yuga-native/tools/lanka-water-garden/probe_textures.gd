extends SceneTree
## Inventory exact source-image overlap; no GPU memory/performance inference.
func _initialize() -> void: call_deferred("run")
func scan(path: String) -> Dictionary:
	var node: Node3D = load(path).instantiate()
	var resources: Dictionary = {}
	var contents: Dictionary = {}
	for visual in node.find_children("*", "MeshInstance3D", true, false):
		for surface in visual.mesh.get_surface_count():
			var material := visual.mesh.surface_get_material(surface) as StandardMaterial3D
			if material == null: continue
			for texture: Texture2D in [material.albedo_texture, material.normal_texture, material.roughness_texture, material.metallic_texture]:
				if texture == null: continue
				var image := texture.get_image()
				if image == null: continue
				var hash := HashingContext.new()
				hash.start(HashingContext.HASH_SHA256)
				hash.update(image.get_data())
				var key := "%s:%s:%s:%s" % [image.get_width(), image.get_height(), image.get_format(), hash.finish().hex_encode()]
				resources[texture.get_instance_id()] = key
				contents[key] = {"width": image.get_width(), "height": image.get_height(), "format": image.get_format(), "decoded_bytes_including_mips": image.get_data_size(), "mipmaps": image.get_mipmap_count()}
	var result := {"asset_sha256": FileAccess.get_sha256(path), "resource_count": resources.size(), "content_count": contents.size(), "contents": contents}
	node.free()
	return result
func run() -> void:
	var output := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	if not output.is_absolute_path() or FileAccess.file_exists(output): push_error("fresh absolute report required"); quit(1); return
	var gate := scan("res://assets/world/lanka-lane-gate.scn")
	var garden := scan("res://assets/world/lanka-water-garden-candidate.scn")
	var duplicate_keys: Array = []
	var duplicate_bytes := 0
	for key in garden.contents:
		if gate.contents.has(key):
			duplicate_keys.append(key)
			duplicate_bytes += int(garden.contents[key].decoded_bytes_including_mips)
	var report := {"schema": 1, "gate": gate, "garden": garden, "shared_source_image_contents": duplicate_keys.size(), "duplicated_decoded_image_bytes": duplicate_bytes, "scope": "Exact decoded source-image content census across two self-contained native caches; repeats within each cache deduplicated by image content. Decoded image storage is not measured GPU allocation or frame time. Canonical runtime/assets unchanged."}
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(report, "  ") + "\n")
	print(JSON.stringify({"gate_resources": gate.resource_count, "garden_resources": garden.resource_count, "duplicate_contents": duplicate_keys.size(), "duplicate_decoded_bytes": duplicate_bytes}))
	quit()
