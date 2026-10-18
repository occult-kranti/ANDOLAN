extends SceneTree
## Imported rig component checks. Pose evaluation is an explicit test fixture.
const Fletching = preload("res://scripts/rama_arrow_fletching.gd")
const Player = preload("res://scripts/player.gd")
var output := "/tmp/desktop-s3-arrow.json"
var checks: Array[Dictionary] = []
var samples: Array[Dictionary] = []
var source_paths: Array[String] = []
var before_pins := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, okay: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":okay,"details":details})
	print("PASS " if okay else "FAIL ",label)

func vec(value: Vector3) -> Array: return [value.x,value.y,value.z]

func matrix(value: Transform3D) -> Array:
	return [[value.basis.x.x,value.basis.y.x,value.basis.z.x,value.origin.x],
		[value.basis.x.y,value.basis.y.y,value.basis.z.y,value.origin.y],
		[value.basis.x.z,value.basis.y.z,value.basis.z.z,value.origin.z],[0,0,0,1]]

func stored(resource: Resource) -> Dictionary:
	var result:={}
	for property in resource.get_property_list():
		if int(property.usage)&PROPERTY_USAGE_STORAGE: result[property.name]=resource.get(property.name)
	return result

func poses(rig: Skeleton3D) -> Array:
	var result:=[]
	for bone in rig.get_bone_count(): result.append(rig.get_bone_pose(bone))
	return result

func pins() -> Dictionary:
	var result:={}
	for path in source_paths: result[path]=FileAccess.get_sha256(path)
	return result

func add_import(path: String) -> void:
	for item in [path,path+".import"]:
		if not source_paths.has(item): source_paths.append(item)
	var config:=ConfigFile.new()
	if config.load(path+".import")==OK:
		for target in config.get_value("deps","dest_files",[]):
			if not source_paths.has(target): source_paths.append(target)

func ivory_material(visual: Node) -> StandardMaterial3D:
	for node in visual.find_children("*","MeshInstance3D",true,false):
		if node.mesh==null: continue
		for surface in node.mesh.get_surface_count():
			var material: Material=node.get_active_material(surface)
			if material is StandardMaterial3D and material.resource_name=="Ivory silk · Rama finish v2": return material
	return null

func hand_mesh(player: Node) -> Dictionary:
	var rig: Skeleton3D=player.rama_motion.rig
	var mesh: MeshInstance3D=player.visual.find_child("RamaHero",true,false)
	var bindings:=[]
	for index in mesh.skin.get_bind_count():
		var bone:=rig.find_bone(String(mesh.skin.get_bind_name(index)))
		if bone<0: bone=mesh.skin.get_bind_bone(index)
		bindings.append({"bone":bone,"inverse":mesh.skin.get_bind_pose(index)})
	var result:={"vertices":[],"triangles":[],"source_vertices":[],"max_rest_reconstruction_error_m":0.0}
	for surface in mesh.mesh.get_surface_count():
		var source: Material=mesh.mesh.surface_get_material(surface)
		if source.resource_name!="Rama warm skin": continue
		var arrays: Array=mesh.mesh.surface_get_arrays(surface)
		var points: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var bones: PackedInt32Array=arrays[Mesh.ARRAY_BONES]
		var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
		var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
		var slots: int=bones.size()/points.size()
		var selected:={}
		for vertex in points.size():
			var hand_weight:=0.0
			for slot in slots:
				var bind: Dictionary=bindings[bones[vertex*slots+slot]]
				var label: String=rig.get_bone_name(bind.bone)
				if label.begins_with("wrist.") or label.begins_with("finger"):
					hand_weight+=weights[vertex*slots+slot]
			if hand_weight>.2: selected[vertex]=true
		var used:={}
		var triangles:=[]
		for offset in range(0,indices.size(),3):
			var a:=indices[offset];var b:=indices[offset+1];var c:=indices[offset+2]
			if selected.has(a) or selected.has(b) or selected.has(c):
				triangles.append([a,b,c]);used[a]=true;used[b]=true;used[c]=true
		var remap:={}
		for vertex in used:
			var influences:=[]
			var rest:=Vector3.ZERO
			for slot in slots:
				var weight: float=weights[vertex*slots+slot]
				if weight<=0: continue
				var bind: Dictionary=bindings[bones[vertex*slots+slot]]
				var point: Vector3=bind.inverse*points[vertex]
				influences.append({"bone":bind.bone,"point":vec(point),"weight":weight})
				rest+=(rig.get_bone_global_rest(bind.bone)*point)*weight
			var expected: Vector3=mesh.global_transform*points[vertex]
			var observed: Vector3=rig.global_transform*rest
			result.max_rest_reconstruction_error_m=maxf(result.max_rest_reconstruction_error_m,observed.distance_to(expected))
			remap[vertex]=result.vertices.size();result.vertices.append(influences)
			result.source_vertices.append({"surface":surface,"vertex":vertex})
		for triangle in triangles: result.triangles.append([remap[triangle[0]],remap[triangle[1]],remap[triangle[2]]])
	return result

func sample(label: String, player: Node, candidate: Node) -> void:
	var motion=player.rama_motion
	var globals:=[]
	for transform in motion.last_globals: globals.append(matrix(transform))
	var size:=root.get_visible_rect().size
	var low:=Vector2(INF,INF)
	var high:=Vector2(-INF,-INF)
	var arrays: Array=candidate._instance.mesh.surface_get_arrays(0)
	for vertex in arrays[Mesh.ARRAY_VERTEX]:
		var pixel: Vector2=player.camera.unproject_position(candidate._instance.global_transform*vertex)
		low=low.min(pixel);high=high.max(pixel)
	samples.append({"id":label,"bone_globals":globals,"rig_global":matrix(motion.rig.global_transform),
		"arrow_global":matrix(motion.nocked_arrow.global_transform),"helper_global":matrix(candidate._instance.global_transform),
		"nock_global":matrix(motion.socket_global("string_nock")),"grip_global":matrix(motion.socket_global("bow_grip")),
		"motion":motion.diagnostics(),"visible":candidate._instance.is_visible_in_tree(),
		"projection":{"viewport":[size.x,size.y],"camera_fov":player.camera.fov,"bounds_min":[low.x,low.y],"bounds_max":[high.x,high.y],
			"scope":"Explicit default-distance camera fixture:3.5m spring length, fixed camera, source65-degree FOV. Vertex projection only; no native camera-update, occlusion or rasterized visibility claim."}})

func run() -> void:
	root.size=Vector2i(1280,720)
	for path in [get_script().resource_path,"res://scripts/rama_arrow_fletching.gd",Fletching.DATA_PATH,"res://scripts/player.gd","res://scripts/rama_motion.gd","res://scripts/rama_surface_finish.gd","res://scripts/rama_secondary_motion.gd","res://scripts/rama_lod_binding.gd","res://assets/animations/rama_hero_motion.tres","res://assets/design/rama-ability-kit.json"]: source_paths.append(path)
	for filename in DirAccess.get_files_at("res://assets/heroes"):
		if filename.begins_with("rama-hero") and filename.ends_with(".import"): add_import("res://assets/heroes/"+filename.trim_suffix(".import"))
	for path in preload("res://scripts/rama_surface_finish.gd").MAP_PATHS.values(): add_import(path)
	before_pins=pins()
	var player:=Player.new()
	player.process_mode=Node.PROCESS_MODE_DISABLED
	root.add_child(player)
	# The disabled actor does not tick SpringArm3D; explicitly stage its
	# ordinary camera distance for bounded projection estimates only.
	player.camera.position.z=player.spring.spring_length
	var motion=player.rama_motion
	motion.active=false # Explicit component sampling; no competing modifier clock.
	var arrow: Node3D=motion.nocked_arrow
	var ivory:=ivory_material(player.visual)
	var material_before:=stored(ivory)
	var before_poses:=poses(motion.rig)
	var arrow_before:=arrow.transform
	var original_children:=arrow.get_children()
	var candidate:=Fletching.new();player.visual.add_child(candidate)
	check("Unconfigured current actor has no optional fletching",arrow.get_child_count()==2 and not arrow.has_meta(Fletching.OWNER_META))
	check("Reject missing parent before creating geometry",not candidate.configure(null,ivory))
	check("Actual imported164-bone arrow and finished ivory admit helper",candidate.configure(arrow,ivory))
	check("Configure changes no bone, arrow transform, visibility or borrowed material",poses(motion.rig)==before_poses and arrow.transform==arrow_before and not arrow.visible and stored(ivory)==material_before)
	check("One shared60-triangle mesh, no material or per-frame owner",candidate.report().triangles==60 and candidate.report().vertices==180 and candidate.report().new_materials==0 and not candidate.is_processing() and not candidate.is_physics_processing(),candidate.report())
	check("One instance borrows exact existing ivory without writing shared geometry material",candidate._instance.material_override==ivory and candidate._instance.mesh.surface_get_material(0)==null)
	var mesh_id: int=candidate._instance.mesh.get_instance_id()
	var instance_id: int=candidate._instance.get_instance_id()
	var stable:=true
	for unused in 100: stable=stable and candidate.configure(arrow,ivory) and candidate._instance.mesh.get_instance_id()==mesh_id and candidate._instance.get_instance_id()==instance_id
	check("Repeated configure preserves geometry and node identity",stable)
	var competitor:=Fletching.new();player.visual.add_child(competitor)
	check("Second owner cannot stack vanes on the same arrow",not competitor.configure(arrow,ivory));competitor.free()
	var hands:=hand_mesh(player)
	check("Actual imported hand subset is nonempty and bind reconstruction agrees",hands.vertices.size()>100 and hands.triangles.size()>100 and hands.max_rest_reconstruction_error_m<.00002,{"vertices":hands.vertices.size(),"triangles":hands.triangles.size(),"max_rest_error_m":hands.max_rest_reconstruction_error_m})
	var kit: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/design/rama-ability-kit.json"))
	var actions:=[]
	for ability in kit.abilities:
		if ability.id in ["kodanda","piercing_dawn","dawn_volley"]: actions.append(ability)
	var attachment_ok:=true
	var visibility_ok:=true
	for ability in actions:
		for pitch in [-.3,0.0,.3]:
			motion.cancel("S3 declared pose fixture")
			var state:={"velocity":Vector3.ZERO,"grounded":true,"aiming":true,"aim_pitch":pitch}
			for unused in 30: motion.update_motion(1.0/60,state);motion.evaluate_pose()
			var accepted: bool=motion.request_action(ability.id,ability.windup_s,ability.recovery_s)
			var elapsed:=0.0
			for fraction in [.1,.5,1.05]:
				var target: float=ability.windup_s*fraction
				while elapsed<target:
					var dt:=minf(1.0/60,target-elapsed)
					motion.update_motion(dt,state);motion.evaluate_pose();elapsed+=dt
				attachment_ok=attachment_ok and candidate._instance.global_transform.is_equal_approx(arrow.global_transform) and arrow.global_position.distance_to(motion.socket_global("string_nock").origin)<.00001
				visibility_ok=visibility_ok and accepted and arrow.visible and candidate._instance.is_visible_in_tree()
				sample(ability.id+"-pitch"+str(pitch)+"-fraction"+str(fraction),player,candidate)
			motion.release_action(ability.id)
			visibility_ok=visibility_ok and not arrow.visible and not candidate._instance.is_visible_in_tree()
			motion.cancel("S3 cancellation fixture")
			motion.request_action(ability.id,ability.windup_s,ability.recovery_s)
			motion.update_motion(1.0/60,state);motion.evaluate_pose()
			motion.cancel_action("S3 actual controller cancellation")
			visibility_ok=visibility_ok and not arrow.visible and not candidate._instance.is_visible_in_tree()
	check("All27 draw samples inherit exact existing arrow frame and nock",attachment_ok)
	check("Draw visibility and all9 release/cancel pairs inherit existing owner",visibility_ok)
	check("Current shaft/tip nodes and borrowed ivory remain unchanged",arrow.get_child(0)==original_children[0] and arrow.get_child(1)==original_children[1] and stored(ivory)==material_before)
	var finite_frames:=true
	var arrays: Array=candidate._instance.mesh.surface_get_arrays(0)
	var max_dot:=0.0
	for i in arrays[Mesh.ARRAY_VERTEX].size():
		var p: Vector3=arrays[Mesh.ARRAY_VERTEX][i];var n: Vector3=arrays[Mesh.ARRAY_NORMAL][i];var uv: Vector2=arrays[Mesh.ARRAY_TEX_UV][i]
		var t:=Vector3(arrays[Mesh.ARRAY_TANGENT][4*i],arrays[Mesh.ARRAY_TANGENT][4*i+1],arrays[Mesh.ARRAY_TANGENT][4*i+2])
		max_dot=maxf(max_dot,absf(n.dot(t)))
		finite_frames=finite_frames and p.is_finite() and uv.is_finite() and n.is_finite() and t.is_finite() and absf(n.length()-1)<.0001 and absf(t.length()-1)<.0001 and absf(n.dot(t))<.001
	check("Native packed positions UV normals and tangents remain finite and orthogonal",finite_frames,{"max_dot":max_dot})
	var reference:=weakref(candidate._instance)
	candidate.release()
	await process_frame;await process_frame
	check("Release removes only the owned instance and leaves both existing arrow children",reference.get_ref()==null and arrow.get_child_count()==2 and not arrow.has_meta(Fletching.OWNER_META) and stored(ivory)==material_before)
	check("Reconfiguration reuses the one cached geometry resource",candidate.configure(arrow,ivory) and candidate._instance.mesh.get_instance_id()==mesh_id)
	var transferred: MeshInstance3D=candidate._instance
	transferred.reparent(root)
	check("Transferred instance invalidates configure",not candidate.configure(arrow,ivory))
	candidate.release()
	check("Release preserves geometry explicitly transferred to another owner",is_instance_valid(transferred) and transferred.get_parent()==root)
	transferred.free();candidate.free();player.free()
	await process_frame
	check("Relevant runtime raw and actual import pins unchanged during probe",pins()==before_pins)
	var result:={"passed":checks.all(func(row):return row.passed),"checks":checks,"samples":samples,"hand_geometry":hands,"source_before":before_pins,"source_after":pins(),"engine":Engine.get_version_info(),
		"scope":"Actual imported Player and RamaMotion API with declared direct pose evaluations and kit timings; helper lifecycle, transform, visibility and frame checks. Hand geometry is exported for full-triangle clearance. No actual render/native modifier continuity or general motion acceptance."}
	var file:=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(result,"\t")+"\n");file.close()
	quit(0 if result.passed else 1)
