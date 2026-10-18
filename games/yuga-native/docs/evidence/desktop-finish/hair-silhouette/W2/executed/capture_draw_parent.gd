extends SceneTree
## Hair contact tape, sampling procedure derived from desktop_s3_arrow_fletching_cases.
## No optional fletching helper; actual shaft/tip/socket, kit and bind checks remain.
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
	var result:={"vertices":[],"triangles":[],"source_vertices":[],"max_rest_reconstruction_error_m":0.0,
		"max_unweighted_rest_error_m":0.0,"max_imported_weight_sum_error":0.0}
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
			var weight_sum:=0.0
			for slot in slots:
				var weight: float=weights[vertex*slots+slot]
				if weight<=0: continue
				weight_sum+=weight
				var bind: Dictionary=bindings[bones[vertex*slots+slot]]
				var point: Vector3=bind.inverse*points[vertex]
				influences.append({"bone":bind.bone,"point":vec(point),"weight":weight})
				rest+=(rig.get_bone_global_rest(bind.bone)*point)*weight
			# Imported quantized weights need not sum exactly to one. The skin
			# shader applies those weights directly; do not silently normalize.
			var expected: Vector3=rig.global_transform*(rig.global_transform.affine_inverse()*(mesh.global_transform*points[vertex])*weight_sum)
			var observed: Vector3=rig.global_transform*rest
			result.max_rest_reconstruction_error_m=maxf(result.max_rest_reconstruction_error_m,observed.distance_to(expected))
			result.max_unweighted_rest_error_m=maxf(result.max_unweighted_rest_error_m,observed.distance_to(mesh.global_transform*points[vertex]))
			result.max_imported_weight_sum_error=maxf(result.max_imported_weight_sum_error,absf(weight_sum-1.0))
			remap[vertex]=result.vertices.size();result.vertices.append(influences)
			result.source_vertices.append({"surface":surface,"vertex":vertex})
		for triangle in triangles: result.triangles.append([remap[triangle[0]],remap[triangle[1]],remap[triangle[2]]])
	return result

func sample(id: String, player: Node, elapsed: float) -> void:
	var motion = player.rama_motion
	var bones := []
	for index in motion.rig.get_bone_count(): bones.append(matrix(motion.rig.get_bone_global_pose(index)))
	samples.append({"id":id,"declared_elapsed_s":elapsed,"bone_globals":bones,
		"rig_global":matrix(motion.rig.global_transform),"arrow_global":matrix(motion.nocked_arrow.global_transform),
		"nock_global":matrix(motion.socket_global("string_nock")),"grip_global":matrix(motion.socket_global("bow_grip")),
		"motion":motion.diagnostics(),"visible":motion.nocked_arrow.visible})

func run() -> void:
	for path in [get_script().resource_path,"res://scripts/player.gd","res://scripts/rama_motion.gd","res://scripts/rama_surface_finish.gd","res://scripts/rama_secondary_motion.gd","res://scripts/rama_lod_binding.gd","res://assets/animations/rama_hero_motion.tres","res://assets/design/rama-ability-kit.json"]: source_paths.append(path)
	for filename in DirAccess.get_files_at("res://assets/heroes"):
		if filename.begins_with("rama-hero") and filename.ends_with(".import"): add_import("res://assets/heroes/"+filename.trim_suffix(".import"))
	for path in preload("res://scripts/rama_surface_finish.gd").MAP_PATHS.values(): add_import(path)
	before_pins=pins()
	var player:=Player.new()
	player.process_mode=Node.PROCESS_MODE_DISABLED
	root.add_child(player)
	var motion=player.rama_motion
	motion.active=false # Explicit component sampling, no competing modifier clock.
	var arrow: Node3D=motion.nocked_arrow
	check("actual imported parent has one164-bone rig and only ordinary shaft/tip",motion.rig.get_bone_count()==164 and arrow.get_child_count()==2)
	var hands:=hand_mesh(player)
	check("actual imported hands and weighted binds reconstruct",hands.vertices.size()>100 and hands.triangles.size()>100 and hands.max_rest_reconstruction_error_m<.00002 and hands.max_imported_weight_sum_error<.0001)
	var kit: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/design/rama-ability-kit.json"))
	var actions:=[]
	for ability in kit.abilities:
		if ability.id in ["kodanda","piercing_dawn","dawn_volley"]: actions.append(ability)
	check("exact three actual kit draw actions",actions.size()==3)
	var attachment_ok:=true
	var visibility_ok:=true
	for ability in actions:
		for pitch in [-.3,0.0,.3]:
			motion.cancel("Hair declared pose fixture")
			var state:={"velocity":Vector3.ZERO,"grounded":true,"aiming":true,"aim_pitch":pitch}
			for unused in 30: motion.update_motion(1.0/60,state);motion.evaluate_pose()
			var accepted: bool=motion.request_action(ability.id,ability.windup_s,ability.recovery_s)
			var elapsed:=0.0
			var step:=0
			for fraction in [.1,.5,1.05]:
				var target: float=ability.windup_s*fraction
				while elapsed<target:
					var dt:=minf(1.0/60,target-elapsed)
					motion.update_motion(dt,state);motion.evaluate_pose();elapsed+=dt
					attachment_ok=attachment_ok and arrow.global_position.distance_to(motion.socket_global("string_nock").origin)<.00001
					visibility_ok=visibility_ok and accepted and arrow.visible
					sample(ability.id+"-pitch"+str(pitch)+"-step"+str(step),player,elapsed)
					step+=1
			motion.release_action(ability.id)
			visibility_ok=visibility_ok and not arrow.visible
			motion.cancel("Hair cancellation fixture")
			motion.request_action(ability.id,ability.windup_s,ability.recovery_s)
			motion.update_motion(1.0/60,state);motion.evaluate_pose()
			motion.cancel_action("Hair actual controller cancellation")
			visibility_ok=visibility_ok and not arrow.visible
	check("all348 declared draw samples retain actual arrow/socket attachment",attachment_ok and samples.size()==348,{"sample_count":samples.size(),"maximum_declared_step_s":1.0/60})
	check("all nine draws plus release/cancel pairs keep actual visibility truth",visibility_ok)
	player.free()
	await process_frame
	check("runtime raw and actual import pins unchanged during probe",pins()==before_pins)
	var result:={"passed":checks.all(func(row):return row.passed),"checks":checks,"samples":samples,"hand_geometry":hands,"source_before":before_pins,"source_after":pins(),"engine":Engine.get_version_info(),"sample_mode":"348-fixed-step-direct-api",
		"scope":"Actual accepted-parent imported Player/RamaMotion, three actual kit draw windups at three pitches with348 direct pose evaluations at declared steps<=1/60s. No optional fletching dependency or candidate hair import. Not continuous native gameplay or rendered clearance."}
	var file:=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(result,"\t")+"\n");file.close()
	quit(0 if result.passed else 1)
