extends SceneTree
const HERO:="res://assets/heroes/rama-hero.glb"
const LOD:=preload("res://scripts/rama_lod_binding.gd")
const SECONDARY:=preload("/workspace/ANDOLAN/games/yuga-native/scripts/rama_secondary_motion.gd")
const SURFACE:=preload("res://scripts/rama_surface_materials.gd")
const FINISH:=preload("res://scripts/rama_surface_finish.gd")
var checks: Array[Dictionary]=[]
var report_path:=""
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path=arg.trim_prefix("--report=")
	call_deferred("run")
func find_kind(node: Node,kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found:=find_kind(child,kind)
		if found:return found
	return null
func collect(node: Node,result: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:result.append(node)
	for child in node.get_children():collect(child,result)
func check(label: String,ok: bool,detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":ok,"detail":detail});print("PASS " if ok else "FAIL ",label)
func run() -> void:
	var visual:Node3D=load(HERO).instantiate();root.add_child(visual)
	var rig:Skeleton3D=find_kind(visual,"Skeleton3D")
	var lod=LOD.new();visual.add_child(lod)
	check("actual groom candidate has three levels and one existing rig",lod.configure(visual,rig,["res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb"]) and lod.report().live_rigs==1,lod.report())
	var surface=SURFACE.new();visual.add_child(surface);check("surface calibration binds",surface.configure(visual))
	var secondary=SECONDARY.new();visual.add_child(secondary);check("secondary binds actual masks",secondary.configure(visual),secondary.report())
	var finish=FINISH.new();visual.add_child(finish);check("finish binds actual candidate",finish.configure(visual),finish.report())
	var meshes:Array[MeshInstance3D]=[];collect(visual,meshes)
	var textile:Array[Dictionary]=[];var hair:Array[Dictionary]=[];var textures:={};var imported:Array[Dictionary]=[]
	for mesh in meshes:
		for index in mesh.mesh.get_surface_count():
			var material:=mesh.get_active_material(index)
			if not material is ShaderMaterial:continue
			if material.resource_name.begins_with("Cobalt"):
				var texture:Texture2D=material.get_shader_parameter("rough_texture")
				textures[texture.get_instance_id()]=true
				var image:=texture.get_image()
				textile.append({"mesh":mesh,"surface":index,"material":material})
				imported.append({"mesh":mesh.name,"surface":index,"texture_path":texture.resource_path,"width":image.get_width(),"height":image.get_height(),"format":image.get_format(),"mipmaps":image.get_mipmap_count(),"payload_bytes":image.get_data_size()})
				check("cloth RED linear map "+str(mesh.name)+":"+str(index),material.get_shader_parameter("rough_channel")==Vector4(1,0,0,0) and material.get_shader_parameter("roughness_value")==1.0 and image.has_mipmaps())
			if material.resource_name.begins_with("Swept black hair"):hair.append({"mesh":mesh,"surface":index,"material":material})
	check("all six cloth LOD surfaces share one imported rough texture",textile.size()==6 and textures.size()==1,{"surfaces":textile.size(),"unique_textures":textures.size()})
	check("three actual hair LOD surfaces retain opaque shader",hair.size()==3 and not FINISH.SECONDARY_SHADER.code.contains("ALPHA ="))
	var ids:=[]
	for row in textile:ids.append(row.material.get_instance_id())
	check("second configure is idempotent",finish.configure(visual))
	for index in textile.size():check("material identity survives configure "+str(index),ids[index]==textile[index].material.get_instance_id())
	# Concrete competing-writer adversary: a changed owned uniform must refuse
	# rebinding and remain untouched, rather than be silently reset to RED.
	var edited:ShaderMaterial=textile[0].material
	edited.set_shader_parameter("rough_channel",Vector4(0,1,0,0))
	check("competing channel edit is refused without overwrite",not finish.configure(visual) and edited.get_shader_parameter("rough_channel")==Vector4(0,1,0,0))
	edited.set_shader_parameter("rough_channel",Vector4(1,0,0,0))
	# Slot replacement must also survive release; never write into a new owner.
	var foreign:=StandardMaterial3D.new();var slot:Dictionary=textile[0]
	slot.mesh.set_surface_override_material(slot.surface,foreign)
	var released:Dictionary=finish.release()
	check("foreign material survives finish release",slot.mesh.get_surface_override_material(slot.surface)==foreign and (not released.conflicts.is_empty() or released.invalidated>0),released)
	# Independent margin adversary: another system grows a still-owned mesh's
	# culling margin after configure. Record whether teardown destroys that edit.
	var margin_mesh:MeshInstance3D=hair[0].mesh
	margin_mesh.extra_cull_margin=.5
	secondary.restore_materials()
	var external_margin_preserved:bool=is_equal_approx(margin_mesh.extra_cull_margin,.5)
	var adversary:={"name":"external culling-margin edit survives secondary teardown","passed":external_margin_preserved,"expected":.5,"actual":margin_mesh.extra_cull_margin,"classification":"focused corrected owner teardown; frozen imported assets unchanged"}
	check("external culling-margin edit survives secondary teardown",external_margin_preserved,adversary)
	var result:={"passed":checks.all(func(x):return x.passed),"checks":checks,"count":checks.size(),"adversaries":[adversary],"imported_textures":imported,"candidate_sha256":FileAccess.get_sha256(HERO),"woven_sha256":FileAccess.get_sha256("res://assets/materials/rama-finish/woven-roughness.png"),"corrected_secondary_sha256":FileAccess.get_sha256("/workspace/ANDOLAN/games/yuga-native/scripts/rama_secondary_motion.gd"),"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Headless actual imported groom lifecycle/channel/resource audit. No import or renderer run. Independent foreign-owner counterexamples separate from candidate regression checks."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	visual.free();quit(0 if result.passed else 1)
