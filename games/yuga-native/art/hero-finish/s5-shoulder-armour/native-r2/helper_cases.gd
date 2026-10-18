extends SceneTree
## Reads the authored GLB buffers into ArrayMesh without invoking an importer.
## Existing cached Rama supplies the actual Skeleton3D and accepted materials.
var checks: Array[Dictionary]=[]
var directory:=OS.get_environment("YUGA_SHOULDER_SOURCE")
var report_path:=OS.get_environment("YUGA_SHOULDER_REPORT")
var helper_script: Script

func check(label: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)

func raw_accessor(doc: Dictionary, binary: PackedByteArray, index: int) -> PackedByteArray:
	var accessor: Dictionary=doc.accessors[index]
	var view: Dictionary=doc.bufferViews[accessor.bufferView]
	assert(not view.has("byteStride"))
	var widths: Dictionary={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}
	assert(accessor.componentType in [5126,5125])
	var start: int=int(view.get("byteOffset",0))+int(accessor.get("byteOffset",0))
	return binary.slice(start,start+int(accessor.count)*int(widths[accessor.type])*4)

func read_mesh(path: String) -> ArrayMesh:
	var data:=FileAccess.get_file_as_bytes(path)
	assert(data.decode_u32(0)==0x46546c67 and data.decode_u32(4)==2)
	var json_size:=data.decode_u32(12)
	var doc: Dictionary=JSON.parse_string(data.slice(20,20+json_size).get_string_from_utf8())
	var binary:=data.slice(28+json_size)
	var mesh:=ArrayMesh.new()
	for primitive: Dictionary in doc.meshes[0].primitives:
		var arrays:=[]; arrays.resize(Mesh.ARRAY_MAX)
		for attribute in ["POSITION","NORMAL","TANGENT","TEXCOORD_0","COLOR_0"]:
			var floats:=raw_accessor(doc,binary,int(primitive.attributes[attribute])).to_float32_array()
			if attribute in ["POSITION","NORMAL"]:
				var vectors:=PackedVector3Array()
				for i in range(0,floats.size(),3): vectors.append(Vector3(floats[i],floats[i+1],floats[i+2]))
				arrays[Mesh.ARRAY_VERTEX if attribute=="POSITION" else Mesh.ARRAY_NORMAL]=vectors
			elif attribute=="TANGENT": arrays[Mesh.ARRAY_TANGENT]=floats
			elif attribute=="TEXCOORD_0":
				var vectors:=PackedVector2Array()
				for i in range(0,floats.size(),2): vectors.append(Vector2(floats[i],floats[i+1]))
				arrays[Mesh.ARRAY_TEX_UV]=vectors
			else:
				var colors:=PackedColorArray()
				for i in range(0,floats.size(),4): colors.append(Color(floats[i],floats[i+1],floats[i+2],floats[i+3]))
				arrays[Mesh.ARRAY_COLOR]=colors
		arrays[Mesh.ARRAY_INDEX]=raw_accessor(doc,binary,int(primitive.indices)).to_int32_array()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var material:=StandardMaterial3D.new()
		material.resource_name=doc.materials[int(primitive.material)].name
		mesh.surface_set_material(mesh.get_surface_count()-1,material)
	return mesh

func poses(rig: Skeleton3D) -> Array:
	var rows:=[]
	for i in rig.get_bone_count(): rows.append([rig.get_bone_pose(i),rig.get_bone_rest(i),rig.get_bone_parent(i),rig.get_bone_name(i)])
	return rows

func stored(material: Material) -> Dictionary:
	var result: Dictionary={}
	for property in material.get_property_list():
		if int(property.usage)&PROPERTY_USAGE_STORAGE: result[property.name]=material.get(property.name)
	return result

func _initialize() -> void: call_deferred("run")

func run() -> void:
	helper_script=load(directory+"/shoulder_review.gd")
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(directory+"/candidate-r4/source-manifest.json"))
	var meshes: Array[Mesh]=[]
	for level in ["near","mid","far"]:
		var path: String=directory+"/candidate-r4/shoulder-armour-"+level+".glb"
		check(level+" raw candidate pin",FileAccess.get_sha256(path)==manifest.levels[level].sha256)
		meshes.append(read_mesh(path))
	var visual: Node3D=load("res://assets/heroes/rama-hero.glb").instantiate()
	root.add_child(visual)
	var calibration=load("res://scripts/rama_surface_materials.gd").new()
	var secondary=load("res://scripts/rama_secondary_motion.gd").new()
	var finish=load("res://scripts/rama_surface_finish.gd").new()
	visual.add_child(calibration); visual.add_child(secondary); visual.add_child(finish)
	check("actual cached hero material owners",calibration.configure(visual) and secondary.configure(visual) and finish.configure(visual))
	var rig: Skeleton3D=visual.find_children("*","Skeleton3D",true,false)[0]
	var before:=poses(rig)
	var prior_children:=rig.get_child_count()
	var helper=helper_script.new(); root.add_child(helper)
	check("no default activation",not helper.configure(visual,meshes) and rig.get_child_count()==prior_children)
	var bad_mesh:=ArrayMesh.new()
	for surface in 3:
		var arrays:=meshes[0].surface_get_arrays(surface)
		if surface==0:
			var colors: PackedColorArray=arrays[Mesh.ARRAY_COLOR]
			colors[0]=Color(1,1,1,.5); arrays[Mesh.ARRAY_COLOR]=colors
		bad_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		bad_mesh.surface_set_material(surface,meshes[0].surface_get_material(surface))
	var malformed: Array[Mesh]=[bad_mesh,meshes[1],meshes[2]]
	check("secondary-moving armour vertex rejected before allocation",not helper.configure(visual,malformed,helper.ACKNOWLEDGEMENT) and rig.get_child_count()==prior_children)
	check("determinant-one anisotropic scale rejected",not helper._unit_transform(Transform3D(Basis.from_scale(Vector3(2,.5,1)),Vector3.ZERO)))
	check("determinant-one shear rejected",not helper._unit_transform(Transform3D(Basis(Vector3.RIGHT,Vector3(.2,1,0),Vector3.BACK),Vector3.ZERO)))
	check("actual cached bone50 and accepted borrowed materials admitted",helper.configure(visual,meshes,helper.ACKNOWLEDGEMENT),helper.report())
	if helper.configured:
		var shared:=true
		for instance: MeshInstance3D in helper._instances:
			for surface in 3: shared=shared and instance.get_active_material(surface)==helper._materials[surface]
		check("three LODs share exactly three borrowed material objects",shared and helper._materials.size()==3)
		check("one existing-bone attachment and no source pose/rest writes",rig.get_child_count()==prior_children+1 and poses(rig)==before and not helper._attachment.override_pose and helper._attachment.get_bone_idx()==50)
		var lod_ok:=true
		for level in 3:
			lod_ok=lod_ok and helper.use_existing_lod(level)
			for index in 3: lod_ok=lod_ok and helper._instances[index].visible==(index==level)
		check("only caller-selected LOD is visible",lod_ok and not helper.use_existing_lod(-1) and not helper.use_existing_lod(3))
		var duplicate=helper_script.new(); root.add_child(duplicate)
		check("second owner refused without allocating",not duplicate.configure(visual,meshes,helper.ACKNOWLEDGEMENT) and rig.get_child_count()==prior_children+1)
		duplicate.free()
		var borrowed: Array=helper._materials.duplicate()
		var snapshots:=[]
		for material: Material in borrowed: snapshots.append(stored(material))
		helper.release(); helper.release()
		check("repeated release removes only owned geometry and preserves rig",rig.get_child_count()==prior_children and not visual.has_meta(helper.OWNER_META) and poses(rig)==before)
		var still_valid:=true
		for i in borrowed.size(): still_valid=still_valid and is_instance_valid(borrowed[i]) and stored(borrowed[i])==snapshots[i]
		check("borrowed material stored properties remain exact for original hero",still_valid and finish.configure(visual))
		check("same resources can be reattached",helper.configure(visual,meshes,helper.ACKNOWLEDGEMENT))
		root.remove_child(visual)
		check("detached visual releases external helper and borrowed references",not helper.configured and helper._materials.is_empty() and helper._instances.is_empty() and rig.get_child_count()==prior_children)
		root.add_child(visual)
	helper.free(); visual.free(); meshes.clear()
	var result: Dictionary={"passed":checks.all(func(row):return row.passed),"checks":checks,"engine":Engine.get_version_info().string,"source_hero_sha256":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb"),"helper_sha256":FileAccess.get_sha256(directory+"/shoulder_review.gd"),"fixture_sha256":FileAccess.get_sha256(directory+"/helper_cases.gd"),"scope":"Existing cached imported hero rig/materials plus manual ArrayMesh decoding of new GLB buffers. No new GLB import, renderer, action-clearance or art acceptance."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result,"\t")+"\n")
	quit(0 if result.passed else 1)
