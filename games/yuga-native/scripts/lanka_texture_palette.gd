extends RefCounted
## Exact, immutable source-image sharing for the two verified Lanka caches.
## Material/channel settings and serialized assets are never changed here.
const CHANNELS := [&"albedo_texture", &"normal_texture", &"roughness_texture", &"metallic_texture"]
static var _textures: Dictionary = {}

static func _image_key(texture: Texture2D) -> String:
	# These caches embed ImageTextures. Other texture implementations can have
	# different sampling/lifetime semantics; leave them and empty images alone.
	if not texture is ImageTexture or texture.get_width() <= 0 or texture.get_height() <= 0:
		return ""
	var image := texture.get_image()
	if image == null or image.is_empty(): return ""
	var bytes := image.get_data()
	if bytes.is_empty(): return ""
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(bytes)
	return "%s:%s:%s:%s:%s:%s:%s:%s" % [texture.get_width(), texture.get_height(), image.get_width(), image.get_height(), image.get_format(), image.has_mipmaps(), image.get_mipmap_count(), hash.finish().hex_encode()]

static func share(node: Node3D) -> Dictionary:
	if not is_instance_valid(node): return {"eligible": 0, "replaced": 0, "skipped": 0}
	var materials: Dictionary = {}
	for visual in node.find_children("*", "MeshInstance3D", true, false):
		if visual.mesh == null: continue
		for index in visual.mesh.get_surface_count():
			var material := visual.mesh.surface_get_material(index) as StandardMaterial3D
			if material != null: materials[material.get_instance_id()] = material
	var eligible := 0
	var replaced := 0
	var skipped := 0
	for material: StandardMaterial3D in materials.values():
		for channel: StringName in CHANNELS:
			var texture := material.get(channel) as Texture2D
			if texture == null: continue
			var key := _image_key(texture)
			if key.is_empty():
				skipped += 1
				continue
			eligible += 1
			# Guard against a future consumer updating a supposedly immutable
			# canonical image. Never alias its changed pixels under an old key.
			if _textures.has(key) and _image_key(_textures[key]) != key: _textures.erase(key)
			if not _textures.has(key): _textures[key] = texture
			elif _textures[key] != texture:
				material.set(channel, _textures[key])
				replaced += 1
	return {"eligible": eligible, "replaced": replaced, "skipped": skipped}

static func cache_report() -> Dictionary:
	return {"images": _textures.size(), "policy": "Exact ImageTexture pixel bytes, dimensions, format and mipmap identity; immutable process-lifetime palette. Not a GPU allocation measurement."}
