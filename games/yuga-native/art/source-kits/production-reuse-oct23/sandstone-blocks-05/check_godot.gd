extends SceneTree

func _initialize() -> void:
	var material = load("res://sandstone.tres")
	if not material is StandardMaterial3D:
		push_error("Source material did not instantiate as StandardMaterial3D")
		quit(1)
		return
	for texture in [material.albedo_texture, material.normal_texture, material.roughness_texture]:
		if not texture is Texture2D or texture.get_width() != 1024 or texture.get_height() != 1024:
			push_error("Expected three imported 1024 x 1024 textures")
			quit(1)
			return
	if not material.normal_enabled or material.metallic != 0.0 or material.roughness_texture_channel != 0:
		push_error("Expected OpenGL normal and nonmetal red-channel roughness bindings")
		quit(1)
		return
	print(JSON.stringify({"status":"PASS", "engine":Engine.get_version_info().string, "material":"StandardMaterial3D", "textures":3, "dimensions":[1024,1024], "rendered":false}))
	quit(0)
