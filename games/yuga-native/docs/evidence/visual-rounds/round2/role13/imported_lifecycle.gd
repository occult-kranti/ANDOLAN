extends SceneTree
## Loads pre-imported PackedScenes only. No editor or GLTF runtime import.
const LOD = preload("res://scripts/rama_lod_binding.gd")
const FACE = preload("res://scripts/rama_facial_performance.gd")
const SURFACE = preload("res://scripts/rama_surface_materials.gd")
const SECONDARY = preload("res://scripts/rama_secondary_motion.gd")
const FINISH = preload("res://scripts/rama_surface_finish.gd")
const HERO = "res://assets/heroes/rama-hero.glb"
const LEVELS = ["res://assets/heroes/rama-hero-mid.glb", "res://assets/heroes/rama-hero-far.glb"]
var checks: Array[Dictionary] = []
var samples: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ", label)

func rig_nodes(node: Node, result: Array[Skeleton3D]) -> void:
	if node is Skeleton3D: result.append(node)
	for child in node.get_children(): rig_nodes(child,result)

func mesh_nodes(node: Node, result: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D: result.append(node)
	for child in node.get_children(): mesh_nodes(child,result)

func material_ids(visual: Node3D) -> Dictionary:
	var result := {}
	var meshes: Array[MeshInstance3D] = []
	mesh_nodes(visual,meshes)
	for instance in meshes:
		for surface in instance.mesh.get_surface_count():
			var material := instance.get_active_material(surface)
			result[str(visual.get_path_to(instance))+":"+str(surface)] = material.get_instance_id() if material else 0
	return result

func run() -> void:
	root.size = Vector2i(1280,720)
	var packed := load(HERO) as PackedScene
	check("Already imported near PackedScene loads",packed != null)
	if packed == null:
		finish()
		return
	var spectator := packed.instantiate() as Node3D
	root.add_child(spectator)
	var spectator_materials := material_ids(spectator)
	var camera := Camera3D.new()
	camera.fov = 75.0
	root.add_child(camera)
	var first_counts := {}
	for cycle in range(4):
		var visual := packed.instantiate() as Node3D
		root.add_child(visual)
		var original_materials := material_ids(visual)
		var rigs: Array[Skeleton3D] = []
		rig_nodes(visual,rigs)
		check("Cycle%d actual source has one164-bone rig" % cycle,rigs.size()==1 and rigs[0].get_bone_count()==164)
		if rigs.size()!=1:
			visual.free()
			continue
		var rig := rigs[0]
		var poses := []
		for index in rig.get_bone_count(): poses.append(rig.get_bone_pose(index))
		var lod = LOD.new(); visual.add_child(lod)
		check("Cycle%d actual two LODs bind" % cycle,lod.configure(visual,rig,LEVELS),lod.report())
		var surface = SURFACE.new(); visual.add_child(surface)
		check("Cycle%d material calibration binds" % cycle,surface.configure(visual))
		var secondary = SECONDARY.new(); visual.add_child(secondary)
		check("Cycle%d secondary materials bind" % cycle,secondary.configure(visual))
		var finish_owner = FINISH.new(); visual.add_child(finish_owner)
		check("Cycle%d finish binds" % cycle,finish_owner.configure(visual),finish_owner.report())
		var face = FACE.new(); visual.add_child(face)
		check("Cycle%d one actual face writer binds" % cycle,face.configure(visual),face.report())
		var competing = FACE.new(); visual.add_child(competing)
		check("Cycle%d competing actual face writer rejected" % cycle,not competing.configure(visual))
		competing.free()
		var identities := material_ids(visual)
		var counts := {"lod":lod.report().owned_mesh_instances,"skins":lod.report().owned_skins,"calibration":surface.diagnostics().owned_materials,"finish_standard":finish_owner.report().standard_materials,"finish_secondary":finish_owner.report().secondary_materials,"face_writers":face.report().owned_meshes}
		if cycle==0: first_counts=counts.duplicate()
		check("Cycle%d ownership counts match first load" % cycle,counts==first_counts,counts)
		var center: Vector3 = rig.global_transform*lod._bounds.get_center()
		var height: float = (rig.global_basis*Vector3.UP).length()*maxf(.01,lod._bounds.size.y+.16)
		var projected_at_4m: float = absf(camera.get_camera_projection().y.y)*camera.get_viewport().get_visible_rect().size.y*height*.5/4.0
		check("Cycle%d measured4m target lies inside mid hysteresis from both directions" % cycle,projected_at_4m>160.0*1.15 and projected_at_4m<420.0*.85,{"camera_fov":camera.fov,"viewport_height":camera.get_viewport().get_visible_rect().size.y,"hero_height_m":height,"projected_height_4m":projected_at_4m,"projected_height_failed8m":projected_at_4m*.5,"mid_reentry_min":160.0*1.15,"near_exit_max":420.0*.85})
		var transition_ok := true
		for distance in [2.0,4.0,100.0,4.0,2.0]:
			camera.global_position=center+Vector3(0,0,distance)
			for sample in range(3): lod.update(camera,.25)
			var state: Dictionary = lod.report()
			transition_ok = transition_ok and state.live_rigs==1 and state.live_bones==164 and state.owned_mesh_instances==4 and state.visible_levels.size()==1
			check("Cycle%d distance%.0f LOD identity" % [cycle,distance],state.level== (0 if distance==2.0 else (2 if distance==100.0 else 1)),state)
			for sample in range(40): face.update_facial(1.0/120.0,{"effort":.7})
		check("Cycle%d LOD transitions retain one rig and bounded clones" % cycle,transition_ok)
		var stable := true
		for sample in range(20):
			stable = stable and surface.configure(visual) and finish_owner.configure(visual)
			lod.reset("review reset")
			face.reset("review reset")
		stable = stable and identities==material_ids(visual) and face.report().owned_meshes==1
		check("Cycle%d repeated reset/configure retains material identities and one writer" % cycle,stable)
		var poses_unchanged := true
		for index in rig.get_bone_count(): poses_unchanged = poses_unchanged and poses[index]==rig.get_bone_pose(index)
		check("Cycle%d face/LOD updates preserve all bone poses" % cycle,poses_unchanged)
		check("Cycle%d shared second hero materials remain exact" % cycle,spectator_materials==material_ids(spectator))
		var owned_refs: Array[WeakRef] = []
		for mesh in lod._owned:
			owned_refs.append(weakref(mesh)); owned_refs.append(weakref(mesh.mesh))
		for binding in surface._bindings: owned_refs.append(weakref(binding.material))
		samples.append({"cycle":cycle,"counts":counts,"lod":lod.report(),"finish":finish_owner.report(),"face":face.report()})
		face.release(); finish_owner.release(); secondary.restore_materials(); surface.restore_materials(); lod.dispose()
		check("Cycle%d release restores exact original material identity" % cycle,original_materials==material_ids(visual))
		visual.free()
		await process_frame
		var released := true
		for reference in owned_refs: released = released and reference.get_ref()==null
		check("Cycle%d retained weakrefs show owned clones and calibration materials released" % cycle,released)
	spectator.free(); camera.free()
	finish()

func finish() -> void:
	var passed := checks.all(func(row):return row.passed)
	var pins := {}
	for path in [HERO,LEVELS[0],LEVELS[1]]: pins[path]=FileAccess.get_sha256(path)
	var report := {"passed":passed,"checks":checks,"cycles":samples,"asset_sha256":pins,"engine":Engine.get_version_info().string,"scope":"Four pre-imported candidate load/reset/LOD/material-isolation/release cycles. No renderer, importer, physical GPU timing, general leak-freedom or visual acceptance claim."}
	var file := FileAccess.open(output,FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(report,"\t")+"\n")
	quit(0 if passed else 1)
