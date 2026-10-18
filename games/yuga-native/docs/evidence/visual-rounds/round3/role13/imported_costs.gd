extends SceneTree
const HERO := "res://assets/heroes/rama-hero.glb"
const LOD := preload("res://scripts/rama_lod_binding.gd")
const SURFACE := preload("res://scripts/rama_surface_materials.gd")
const SECONDARY := preload("res://scripts/rama_secondary_motion.gd")
const FINISH := preload("res://scripts/rama_surface_finish.gd")
var checks: Array[Dictionary] = []
var output := "/tmp/r3-imported-costs.json"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func find_rig(node:Node) -> Skeleton3D:
	if node is Skeleton3D:return node
	for child in node.get_children():
		var found:=find_rig(child)
		if found:return found
	return null
func collect(node:Node,result:Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh:result.append(node)
	for child in node.get_children():collect(child,result)
func check(label:String,ok:bool,detail:Dictionary={}) -> void:
	checks.append({"name":label,"passed":ok,"detail":detail});print("PASS " if ok else "FAIL ",label)
func triangle_count(mesh:MeshInstance3D) -> int:
	var total:=0
	for surface in mesh.mesh.get_surface_count():
		var arrays:=mesh.mesh.surface_get_arrays(surface)
		var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX]!=null else PackedInt32Array()
		total+=(indices.size() if not indices.is_empty() else arrays[Mesh.ARRAY_VERTEX].size())/3
	return total
func run() -> void:
	var visual:Node3D=load(HERO).instantiate();root.add_child(visual)
	var rig:=find_rig(visual);var lod:=LOD.new();visual.add_child(lod)
	check("three candidate levels bind one imported rig",lod.configure(visual,rig,["res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb"]),lod.report())
	for script in [SURFACE,SECONDARY,FINISH]:
		var owner=script.new();visual.add_child(owner)
		check("material owner configures "+script.resource_path,owner.configure(visual))
	var meshes:Array[MeshInstance3D]=[];collect(visual,meshes)
	var rows:=[];var materials:={};var textures:={};var hair:={};var face_count:=0
	for mesh in meshes:
		if mesh.name=="RamaFace":face_count+=1
		var row:={"mesh":String(mesh.name),"surfaces":mesh.mesh.get_surface_count(),"triangles":triangle_count(mesh),"vertices":0,"array_payload_bytes":0}
		for surface in mesh.mesh.get_surface_count():
			var arrays:=mesh.mesh.surface_get_arrays(surface)
			row.vertices+=arrays[Mesh.ARRAY_VERTEX].size()
			for array in arrays:
				if array!=null:row.array_payload_bytes+=array.to_byte_array().size()
			var material:=mesh.get_active_material(surface);materials[material.get_instance_id()]=true
			if material is ShaderMaterial:
				if material.resource_name.begins_with("Swept black hair"):
					var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX];hair[String(mesh.name)]=indices.size()/3
				for parameter in ["base_texture","rough_texture","metal_texture","normal_texture"]:
					var texture=material.get_shader_parameter(parameter)
					if texture is Texture2D:textures[texture.get_instance_id()]=texture
			elif material is StandardMaterial3D:
				for texture in [material.albedo_texture,material.roughness_texture,material.metallic_texture,material.normal_texture]:
					if texture is Texture2D:textures[texture.get_instance_id()]=texture
		rows.append(row)
	check("seven live meshes retain one face and one rig",meshes.size()==7 and face_count==1 and lod.report().live_rigs==1 and rig.get_bone_count()==164,{"meshes":meshes.size(),"faces":face_count,"rig":lod.report()})
	check("actual active groom triangle counts match source",hair.get("RamaHero")==29448 and hair.get("RamaHeroLOD1")==13450 and hair.get("RamaHeroLOD2")==6444,hair)
	var levels:=[]
	for level in [0,1,2,1,0]:
		lod._apply_level(level)
		var total:=0;var visible:=[]
		for mesh in meshes:
			if mesh.visible:total+=triangle_count(mesh);visible.append(String(mesh.name))
		levels.append({"level":level,"visible_meshes":visible,"triangles":total})
		check("only one body/bow level and one near face at level %s"%level,visible.size()==3 and "RamaFace" in visible and lod.report().visible_levels==[level],levels[-1])
	var texture_rows:=[];var texture_bytes:=0
	for texture in textures.values():
		var image:Image=texture.get_image();texture_bytes+=image.get_data_size()
		texture_rows.append({"path":texture.resource_path,"width":image.get_width(),"height":image.get_height(),"format":image.get_format(),"mipmaps":image.get_mipmap_count(),"cpu_image_payload_bytes":image.get_data_size()})
	lod.reset();check("reset restores near visibility without duplicate rig",lod.level==0 and lod.report().live_rigs==1 and lod.report().visible_levels==[0])
	var source_pins:={}
	for path in [HERO,"res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb","res://scripts/rama_lod_binding.gd","res://scripts/rama_secondary_motion.gd","res://scripts/rama_surface_finish.gd"]:source_pins[path]=FileAccess.get_sha256(path)
	var result:={"task":"R3-13","passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"meshes":rows,"levels":levels,"unique_materials":materials.size(),"unique_textures":textures.size(),"textures":texture_rows,"cpu_image_payload_bytes":texture_bytes,"source_pins":source_pins,"scope":"Actual imported headless scene ownership and exposed CPU array/image payload. Seven meshes loaded, three visible. No import, rendering, GPU allocation, measured FPS or draw-call claim. Mesh blendshape payload is not included in array byte sum."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	visual.free();quit(0 if result.passed else 1)
