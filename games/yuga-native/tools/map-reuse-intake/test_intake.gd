extends SceneTree
const Loader=preload("res://map_loader.gd")
const PBR=preload("res://pbr_material.gd")
var checks:Array[Dictionary]=[]
func _initialize()->void:call_deferred("run")
func check(label:String,ok:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":ok,"detail":detail})
func container(document:Dictionary)->PackedByteArray:
	var data:=JSON.stringify(document).to_utf8_buffer()
	while data.size()%4:data.append(32)
	var bytes:=PackedByteArray()
	bytes.resize(28+data.size()+4)
	bytes.encode_u32(0,0x46546c67);bytes.encode_u32(4,2);bytes.encode_u32(8,bytes.size())
	bytes.encode_u32(12,data.size());bytes.encode_u32(16,0x4e4f534a)
	for index in data.size():bytes[20+index]=data[index]
	bytes.encode_u32(20+data.size(),4);bytes.encode_u32(24+data.size(),0x004e4942)
	return bytes
func run()->void:
	var source:="res://assets/courtyard.glb"
	var original_hash:=FileAccess.get_sha256(source)
	var placement:=Transform3D(Basis(Vector3.UP,PI*.5),Vector3(3,2,-5))
	var loaded:Dictionary=Loader.load_element(source,Loader.EXPECTED_SOURCE,Loader.ELEMENT,placement)
	check("actual pinned CC0 structural source loads",loaded.ok)
	if not loaded.ok:
		print(JSON.stringify(loaded));quit(1);return
	root.add_child(loaded.root)
	check("one existing structural mesh with 1296 source triangles",loaded.triangles==1296 and loaded.visual.mesh.get_surface_count()==1,loaded.triangles)
	check("triangle collision matches all transformed source vertices",loaded.shape.get_faces()==loaded.faces)
	var inverse:=placement.affine_inverse()
	var error:=0.0
	var source_bounds:=AABB(loaded.source_faces[0],Vector3.ZERO)
	for index in loaded.faces.size():
		error=maxf(error,(inverse*loaded.faces[index]-loaded.source_faces[index]).length())
		source_bounds=source_bounds.expand(loaded.source_faces[index])
	check("rigid Y-up metre transform has no double axis conversion",error<.00001,error)
	var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://source-manifest.json"))
	var raw_min:Array=manifest.element_accessor_bounds.min
	var raw_max:Array=manifest.element_accessor_bounds.max
	var expected_bounds:=AABB(Vector3(raw_min[0],raw_min[1],raw_min[2]),Vector3(raw_max[0]-raw_min[0],raw_max[1]-raw_min[1],raw_max[2]-raw_min[2]))
	check("native Y-up metre bounds equal independent raw accessor bounds",source_bounds.is_equal_approx(expected_bounds),{"native":source_bounds,"raw":expected_bounds})
	var material_result:Dictionary=PBR.new().build(ProjectSettings.globalize_path("res://"))
	check("existing verified CC0 material adapter loads without new image downloads",material_result.ok)
	if material_result.ok:
		loaded.visual.material_override=material_result.material
		check("source material tile remains three metres",material_result.material.uv1_world_triplanar and material_result.material.uv1_scale.is_equal_approx(Vector3.ONE/3.0),material_result.report.scalars)
	await physics_frame
	await physics_frame
	var space:PhysicsDirectSpaceState3D=loaded.root.get_world_3d().direct_space_state
	var samples:=0
	var hits:=0
	for index in range(0,loaded.faces.size(),maxi(3,int(loaded.faces.size()/36.0)/3*3)):
		if index+2>=loaded.faces.size():break
		var a:Vector3=loaded.faces[index]
		var b:Vector3=loaded.faces[index+1]
		var c:Vector3=loaded.faces[index+2]
		var cross:Vector3=(b-a).cross(c-a)
		if cross.length()<.0001:continue
		var normal:=cross.normalized()
		var center:Vector3=(a+b+c)/3
		var result:=space.intersect_ray(PhysicsRayQueryParameters3D.create(center+normal*.05,center-normal*.05,1))
		samples+=1
		if not result.is_empty() and result.collider==loaded.body and result.position.distance_to(center)<.051:hits+=1
	check("actual transformed structural triangles answer physics rays",samples>=24 and hits==samples,{"tested":samples,"hits":hits})
	check("far empty space stays traversable",space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(100,10,100),Vector3(100,-10,100),1)).is_empty())
	for entry in [
		["unapproved decorative mesh refused",Loader.load_element(source,Loader.EXPECTED_SOURCE,"DECOR_Aged_brass"),"unapproved_element"],
		["source checksum mismatch refused",Loader.load_element(source,"0".repeat(64)),"source_hash"],
		["centimetre/nonuniform scale refused",Loader.load_element(source,Loader.EXPECTED_SOURCE,Loader.ELEMENT,Transform3D(Basis.IDENTITY.scaled(Vector3(.01,.01,.01)),Vector3.ZERO)),"rigid_metre_placement_required"],
		["reflection refused",Loader.load_element(source,Loader.EXPECTED_SOURCE,Loader.ELEMENT,Transform3D(Basis.IDENTITY.scaled(Vector3(-1,1,1)),Vector3.ZERO)),"rigid_metre_placement_required"],
		["external buffer refused by pure preflight before native parser",Loader.inspect(FileAccess.get_file_as_bytes("res://bad-uri.glb")),"external_resources"],
		["truncated container refused",Loader.inspect(PackedByteArray([1,2,3])),"bounded_complete_glb"]
	]:check(entry[0],not entry[1].ok and entry[1].reason==entry[2],entry[1])
	for entry in [
		["null asset rejected",{"asset":null,"buffers":[{"byteLength":4}]},"gltf_version"],
		["null animation list rejected",{"asset":{"version":"2.0"},"buffers":[{"byteLength":4}],"animations":null},"array_contract"],
		["string extension list rejected",{"asset":{"version":"2.0"},"buffers":[{"byteLength":4}],"extensionsUsed":"KHR_materials_emissive_strength"},"array_contract"],
		["unknown required extension rejected",{"asset":{"version":"2.0"},"buffers":[{"byteLength":4}],"extensionsRequired":["UNKNOWN_private"]},"unsupported_extension"],
		["undeclared required extension rejected",{"asset":{"version":"2.0"},"buffers":[{"byteLength":4}],"extensionsRequired":["KHR_materials_emissive_strength"]},"undeclared_extension"],
		["fractional buffer byte count rejected",{"asset":{"version":"2.0"},"buffers":[{"byteLength":3.5}]},"embedded_buffer_length"],
		["overflowing buffer byte count rejected",{"asset":{"version":"2.0"},"buffers":[{"byteLength":4000000}]},"embedded_buffer_length"]
	]:
		var inspected:Dictionary=Loader.inspect(container(entry[1]))
		check(entry[0],not inspected.ok and inspected.reason==entry[2],inspected)
	check("original map source bytes remain unchanged",FileAccess.get_sha256(source)==original_hash and original_hash==Loader.EXPECTED_SOURCE)
	var passed:=checks.all(func(item):return item.passed)
	var report:={"schema":1,"passed":passed,"checks":checks,"source_sha256":original_hash,"element":Loader.ELEMENT,"triangles":loaded.triangles,"coordinate_contract":loaded.units,"material":material_result.get("report",{}),"scope":"Real pinned source geometry, rigid coordinate, material and native physics intake. No full-map or visual quality acceptance.","canonical_enabled":false}
	FileAccess.open("res://intake-report.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size(),"triangles":loaded.triangles}))
	quit(0 if passed else 1)
