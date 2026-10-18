extends SceneTree
## Run only in capture owner's isolated project, after serialized import with mips enabled.
const TEXTURE := "res://art/visual-rounds/cloth/textures/woven-roughness-r3.png"
var checks: Array[Dictionary] = []

func check(label: String, passed: bool, observed: Variant = null) -> void:
	checks.append({"check":label,"passed":passed,"observed":observed})

func _initialize() -> void:
	var config := ConfigFile.new()
	check("import configuration exists", config.load(TEXTURE + ".import") == OK)
	check("actual import requests mipmaps", config.get_value("params","mipmaps/generate",false) == true)
	check("roughness is not treated as normal", int(config.get_value("params","compress/normal_map",0)) == 0)
	check("red channel identity", int(config.get_value("params","process/channel_remap/red",0)) == 0)
	var texture := load(TEXTURE) as Texture2D
	check("actual imported texture loads", texture != null)
	if texture != null:
		check("actual dimensions", texture.get_width() == 1024 and texture.get_height() == 1024, [texture.get_width(),texture.get_height()])
		var image := texture.get_image()
		check("actual mip payload present", image != null and image.has_mipmaps())
		if image != null:
			if image.is_compressed(): image.decompress()
			check("actual mip count", image.get_mipmap_count() == 10, image.get_mipmap_count())
			var source := Image.load_from_file(TEXTURE)
			var maximum_error := 0.0
			for pixel in [Vector2i(0,0),Vector2i(77,151),Vector2i(512,512),Vector2i(1023,1023)]:
				maximum_error = maxf(maximum_error, absf(image.get_pixelv(pixel).r - source.get_pixelv(pixel).r))
			check("import preserves linear scalar samples", maximum_error <= 1.0/255.0, maximum_error)
	var shader := load("res://shaders/rama_secondary_cloth.gdshader") as Shader
	check("roughness sampler has mip filtering without source_color", shader != null and "rough_texture : hint_default_white, filter_linear_mipmap" in shader.code)
	var material := ShaderMaterial.new()
	material.shader = shader
	material.set_shader_parameter("rough_texture",texture)
	material.set_shader_parameter("rough_channel",Vector4(1,0,0,0))
	material.set_shader_parameter("roughness_value",1.0)
	material.set_shader_parameter("use_rough_texture",true)
	check("actual ShaderMaterial scalar binding", material.get_shader_parameter("rough_texture") == texture and material.get_shader_parameter("rough_channel") == Vector4(1,0,0,0) and material.get_shader_parameter("roughness_value") == 1.0)
	var failed := 0
	for item in checks:
		if not item.passed: failed += 1
	var report := {"task":"R3-01","tests":checks.size(),"failed":failed,"passed":failed == 0,"checks":checks,"scope":"Actual standalone import and shader input binding. Integrated all-LOD ownership and matched pixels remain separate gates."}
	var output := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file != null: file.store_string(JSON.stringify(report,"\t") + "\n")
	print(JSON.stringify(report))
	quit(0 if failed == 0 else 1)
