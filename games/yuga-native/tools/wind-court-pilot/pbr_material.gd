extends RefCounted
## Optional study adapter for the already audited CC0 material. No shader code,
## downloaded asset, imported resource mutation, or copied texture is involved.
const KIT:="res://art/source-kits/production-reuse-oct23/sandstone-blocks-05/"

func build(output:String)->Dictionary:
	var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(KIT+"manifest.json"))
	var text:=FileAccess.get_file_as_string(KIT+"sandstone.tres")
	# Preserve the vendor resource's native scalar settings. Its relative image
	# bindings require editor imports, so remove only those external bindings and
	# bind the same verified source PNGs through ImageTexture below.
	var scalar_lines:PackedStringArray=[]
	for line in text.split("\n"):
		if line.begins_with("[ext_resource ") or line.contains("ExtResource("):continue
		scalar_lines.append(line.replace("load_steps=4 ",""))
	var scalar_path:=output.path_join("source-native-scalars.tres")
	FileAccess.open(scalar_path,FileAccess.WRITE).store_string("\n".join(scalar_lines))
	var source:StandardMaterial3D=ResourceLoader.load(scalar_path,"StandardMaterial3D",ResourceLoader.CACHE_MODE_IGNORE)
	if source==null:return {"ok":false,"reason":"native scalar resource did not load"}
	var material:=source.duplicate() as StandardMaterial3D
	var rows:Array[Dictionary]=[]
	var decoded:=0
	for entry in manifest.files:
		var path:String=KIT+String(entry.file)
		if FileAccess.get_sha256(path)!=entry.sha256:return {"ok":false,"reason":"source hash mismatch: "+path}
		var image:=Image.load_from_file(ProjectSettings.globalize_path(path))
		if image==null or image.is_empty() or image.get_width()!=1024 or image.get_height()!=1024:return {"ok":false,"reason":"expected actual 1K source image"}
		var source_format:=image.get_format()
		# Bound the study upload. Preserve original PNG bytes; roughness is sampled
		# as native red-channel R8 after in-memory conversion from its 16-bit PNG.
		image.convert(Image.FORMAT_L8 if entry.role=="Rough" else Image.FORMAT_RGB8)
		if image.generate_mipmaps(entry.role=="nor_gl")!=OK:return {"ok":false,"reason":"mipmap generation failed"}
		var texture:=ImageTexture.create_from_image(image)
		if texture==null:return {"ok":false,"reason":"native image texture upload failed"}
		match String(entry.role):
			"Diffuse":material.albedo_texture=texture
			"nor_gl":material.normal_texture=texture
			"Rough":material.roughness_texture=texture
			_:return {"ok":false,"reason":"unrecognized source texture role"}
		decoded+=image.get_data_size()
		rows.append({"role":entry.role,"path":path,"sha256":entry.sha256,"source_bytes":entry.bytes,"source_decoded_format":source_format,"upload_format":image.get_format(),"width":image.get_width(),"height":image.get_height(),"mipmap_count":image.get_mipmap_count(),"decoded_with_mips_bytes":image.get_data_size()})
	# Reuse hero_district_detail.gd's existing StandardMaterial3D world-triplanar
	# pattern; the source manifest specifies a three-metre physical tile.
	material.resource_name="Optional CC0 Vayu court sandstone study"
	material.albedo_color=Color.WHITE
	material.uv1_triplanar=true
	material.uv1_world_triplanar=true
	material.uv1_scale=Vector3.ONE/3.0
	material.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	material.normal_scale=.55
	return {"ok":true,"material":material,"report":{"source_manifest_sha256":FileAccess.get_sha256(KIT+"manifest.json"),"source_tres_sha256":FileAccess.get_sha256(KIT+"sandstone.tres"),"cc0_sha256":FileAccess.get_sha256(KIT+"LICENSES/CC0-1.0.txt"),"provider":manifest.provider,"author":manifest.author,"license":manifest.asset_license,"source_url":manifest.source_url,"textures":rows,"source_disk_bytes":6220633,"copied_texture_bytes":0,"decoded_with_mips_bytes":decoded,"gpu_texture_budget_bytes":16777216,"gpu_budget_is_estimate":true,"texture_samplers":3,"estimated_triplanar_texture_fetches":9,"new_shader_files":0,"extra_meshes":0,"extra_lights":0,"scalars":{"metallic":material.metallic,"roughness":material.roughness,"roughness_channel":material.roughness_texture_channel,"normal_enabled":material.normal_enabled,"source_normal_scale":source.normal_scale,"study_normal_scale":material.normal_scale,"world_triplanar":true,"tile_period_m":3.0,"albedo_tint":[1,1,1,1]},"scope":"Native StandardMaterial3D adapter to existing CC0 maps. Original resource/PNG bytes stay unchanged; roughness is quantized to R8 only in memory. No canonical material promotion or shader file."}}
