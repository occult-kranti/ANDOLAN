extends SceneTree
## Independent actual-world admission and lifecycle checks for the quality slice.
## No visual, physical-cloth, listening, GPU, Windows or online quality claim.
const ORIGIN := Vector3(-40, .05, -10)
const DT := 1.0 / 60.0
const FACE_SHAPES := ["rama_blink_left", "rama_blink_right", "rama_blink_half_left", "rama_blink_half_right"]
const SECONDARY_NAMES := ["Cobalt handwoven silk", "Cobalt lotus brocade", "Worked warm gold", "Swept black hair"]
const PROFILE_NAMES := ["Rama warm skin", "Natural lips", "Warm sclera", "Deep brown iris", "Polished sapphire", "Recessed antique gold"]
const SECONDARY_SHADER := preload("res://shaders/rama_secondary_cloth.gdshader")
const SOURCE_PATHS := [
	"res://tests/rama_quality_integration_cases.gd", "res://scenes/confluence_world.tscn",
	"res://scripts/confluence_world.gd", "res://scripts/player.gd",
	"res://scripts/rama_motion.gd", "res://assets/animations/rama_hero_motion.tres",
	"res://scripts/rama_surface_materials.gd", "res://scripts/rama_secondary_motion.gd",
	"res://shaders/rama_secondary_cloth.gdshader", "res://scripts/rama_facial_performance.gd",
	"res://scripts/rama_hero_runtime.gd", "res://scripts/rama_ability_kit.gd",
	"res://scripts/rama_vitals.gd", "res://scripts/rama_action_buffer.gd",
	"res://scripts/rama_action_audio.gd", "res://assets/audio/rama-quality/manifest.json",
	"res://scripts/rama_lod_binding.gd", "res://scripts/rama_visual_lod.gd"
]
var checks: Array[Dictionary] = []
var sources := {}
var imports := {}
var output := "/tmp/rama-quality-integration.json"
var scene: Node3D
var player: CharacterBody3D
var face: Node
var secondary: Node
var surface: Node
var face_mesh: MeshInstance3D
var rig: Skeleton3D
var started_usec := 0
var initial_nodes := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, value: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":value,"details":detail})
	print("PASS " if value else "FAIL ",label," ",JSON.stringify(detail))

func frames(count := 3) -> void:
	for unused in count: await process_frame

func collect(node: Node, kind: String, result: Array) -> void:
	if node.is_class(kind): result.append(node)
	for child in node.get_children(): collect(child,kind,result)

func controller_count(node: Node, source: String) -> int:
	var count := 1 if node.get_script()!=null and node.get_script().resource_path==source else 0
	for child in node.get_children(): count += controller_count(child,source)
	return count

func meshes() -> Array:
	var result := []
	collect(player.visual,"MeshInstance3D",result)
	return result

func morph_values() -> Dictionary:
	var result := {}
	if is_instance_valid(face_mesh):
		for index in face_mesh.mesh.get_blend_shape_count():
			result[String(face_mesh.mesh.get_blend_shape_name(index))] = face_mesh.get_blend_shape_value(index)
	return result

func uniforms() -> Dictionary:
	var result := {}
	for mesh in meshes():
		for index in mesh.mesh.get_surface_count():
			var material: Material = mesh.get_active_material(index)
			if material is ShaderMaterial and String(material.resource_name).ends_with("bounded secondary"):
				result[String(mesh.get_path())+":"+str(index)] = material.get_shader_parameter("secondary_offset")
	return result

func resource_identity() -> Dictionary:
	var result := {}
	for mesh in meshes():
		var materials := []
		for index in mesh.mesh.get_surface_count():
			var material: Material = mesh.get_active_material(index)
			materials.append(material.get_instance_id() if material else 0)
		result[String(mesh.get_path())] = {"mesh":mesh.mesh.get_instance_id(),"skin":mesh.skin.get_instance_id() if mesh.skin else 0,"materials":materials,"skeleton":String(mesh.skeleton)}
	return result

func one_skin_owner() -> bool:
	if not is_instance_valid(rig): return false
	for mesh in meshes():
		if mesh.skin and mesh.get_node_or_null(mesh.skeleton)!=rig: return false
	return true

func unowned_secondary_surfaces() -> Array:
	var result:=[]
	for mesh in meshes():
		for index in mesh.mesh.get_surface_count():
			var original: Material=mesh.mesh.surface_get_material(index)
			var active: Material=mesh.get_active_material(index)
			var name_: String=String(original.resource_name) if original else ""
			if active is ShaderMaterial and active.shader==SECONDARY_SHADER and not SECONDARY_NAMES.has(name_):
				result.append({"mesh":String(mesh.get_path()),"surface":index,"source_material":name_,"offset":active.get_shader_parameter("secondary_offset")})
	return result

func fresh_import(path: String) -> bool:
	var config := ConfigFile.new()
	if config.load(path+".import")!=OK: return false
	var imported: String = config.get_value("remap","path","")
	var stamp := imported.get_basename()+".md5"
	if imported.is_empty() or not FileAccess.file_exists(imported) or not FileAccess.file_exists(stamp): return false
	var text := FileAccess.get_file_as_string(stamp)
	var regex := RegEx.new()
	for entry in [["source_md5",path],["dest_md5",imported]]:
		regex.compile(String(entry[0])+'="([a-f0-9]+)"')
		var matched := regex.search(text)
		if matched==null or matched.get_string(1)!=FileAccess.get_md5(entry[1]): return false
	for source in [path,path+".import",imported,stamp]: sources[source]=FileAccess.get_sha256(source)
	imports[path]={"imported":imported,"sha256":sources[imported],"stamp_sha256":sources[stamp]}
	return true

func admission() -> bool:
	var first_check:=checks.size()
	var rigs := []
	collect(player.visual,"Skeleton3D",rigs)
	check("Actual hero owns exactly one 164-bone skeleton",rigs.size()==1 and rigs[0].get_bone_count()==164,{"skeletons":rigs.size()})
	if rigs.size()==1: rig=rigs[0]
	check("One Rama motion modifier and no retained competing pose owner",controller_count(player.visual,"res://scripts/rama_motion.gd")==1 and player.hero_pose==null and player.traversal_pose==null)
	face=player.get("rama_face"); secondary=player.get("rama_secondary"); surface=player.get("rama_surface")
	var all_configured: bool = is_instance_valid(face) and is_instance_valid(secondary) and is_instance_valid(surface) and face.configured and secondary.configured and surface.configured
	check("Actual imported hero admits facial, secondary and material controllers",all_configured,{"face":face.report() if is_instance_valid(face) else {},"secondary":secondary.report() if is_instance_valid(secondary) else {},"materials":surface.diagnostics() if is_instance_valid(surface) else {}})
	var faces := []
	var linked := true
	for mesh in meshes():
		if mesh.skin: linked=linked and mesh.get_node_or_null(mesh.skeleton)==rig
		if not mesh.mesh is ArrayMesh: continue
		var names := []
		for index in mesh.mesh.get_blend_shape_count(): names.append(String(mesh.mesh.get_blend_shape_name(index)))
		if FACE_SHAPES.any(func(shape):return names.has(shape)): faces.append({"mesh":mesh,"names":names})
	check("Every actual skinned mesh binds to the same live skeleton",is_instance_valid(rig) and linked)
	var unique_face: bool = faces.size()==1 and faces[0].names.size()==4 and FACE_SHAPES.all(func(shape):return faces[0].names.has(shape))
	check("One unique face has the four authored full and half blink morphs",unique_face,{"matching_meshes":faces.size(),"names":faces[0].names if faces.size()==1 else []})
	if unique_face:
		face_mesh=faces[0].mesh
		var vertices := 0
		for index in face_mesh.mesh.get_surface_count(): vertices+=face_mesh.mesh.surface_get_arrays(index)[Mesh.ARRAY_VERTEX].size()
		check("Facial morphs remain a small skinned partition",vertices>0 and vertices<=8000 and face_mesh.skin!=null,{"vertices":vertices,"skin_bind_count":face_mesh.skin.get_bind_count() if face_mesh.skin else 0})
	var lod: Node=player.get("rama_lod")
	var lod_report: Dictionary=lod.report() if is_instance_valid(lod) else {}
	var clones:=0
	for mesh in meshes():
		if String(mesh.name) in ["RamaHeroLOD1","RamaBowLOD1","RamaHeroLOD2","RamaBowLOD2"]: clones+=1
	check("Actual asset LOD binding has three levels, four clones and one original rig and face",lod_report.get("configured",false) and lod_report.get("levels",0)==3 and lod_report.get("owned_mesh_instances",0)==4 and lod_report.get("owned_skins",0)==2 and lod_report.get("live_rigs",0)==1 and lod_report.get("live_bones",0)==164 and lod_report.get("paths",[]).size()==2 and clones==4 and unique_face and one_skin_owner(),{"binding":lod_report,"actual_clone_meshes":clones,"actual_face_meshes":faces.size()})
	var semantic := {}
	var masks_valid := true
	var unused_alpha_positive := 0
	var bow_free_weights := 0
	var ordinary_pbr := {}
	var bound_surfaces := 0
	for mesh in meshes():
		for index in mesh.mesh.get_surface_count():
			var original: Material = mesh.mesh.surface_get_material(index)
			var name_: String = String(original.resource_name) if original else ""
			var is_semantic: bool=SECONDARY_NAMES.has(name_)
			var active: Material=mesh.get_active_material(index)
			if not is_semantic and active is StandardMaterial3D:
				ordinary_pbr[String(mesh.get_path())+":"+str(index)]={"source_material":name_,"vertex_color_use_as_albedo":active.vertex_color_use_as_albedo,"transparency":active.transparency}
			var arrays: Array = mesh.mesh.surface_get_arrays(index)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var colors: PackedColorArray = arrays[Mesh.ARRAY_COLOR] if arrays[Mesh.ARRAY_COLOR]!=null else PackedColorArray()
			if colors.size()!=vertices.size():
				if is_semantic: masks_valid=false
				continue
			if is_semantic:
				if not semantic.has(name_): semantic[name_]={"anchors":0,"moving":0}
				if active is ShaderMaterial and active.shader==SECONDARY_SHADER and String(active.resource_name).ends_with("bounded secondary"): bound_surfaces+=1
				else: masks_valid=false
			for color in colors:
				if is_semantic:
					masks_valid=masks_valid and is_finite(color.r) and is_finite(color.g) and is_finite(color.b) and is_finite(color.a) and absf(color.r-1)<.001 and absf(color.g-1)<.001 and absf(color.b-1)<.001 and color.a>=0 and color.a<=1
					semantic[name_]["moving" if color.a>.001 else "anchors"]+=1
				elif color.a>.001: unused_alpha_positive+=1
				if String(mesh.name).begins_with("RamaBow") and active is ShaderMaterial and active.shader==SECONDARY_SHADER and color.a>.001: bow_free_weights+=1
	var all_semantic := SECONDARY_NAMES.all(func(name_):return semantic.has(name_) and semantic[name_].moving>0 and semantic[name_].anchors>0)
	var unowned_shaders:=unowned_secondary_surfaces()
	check("Actual moving masks bind all four domains while skin and bow remain outside displacement",masks_valid and all_semantic and unowned_shaders.is_empty() and bow_free_weights==0,{"domains":semantic,"unused_nonsecondary_alpha_positive_rows":unused_alpha_positive,"unowned_secondary_surfaces":unowned_shaders,"bow_nonzero_weights":bow_free_weights,"ordinary_pbr":ordinary_pbr,"bound_surfaces":bound_surfaces})
	if all_configured:
		var profiles: Dictionary=surface.diagnostics().profiles
		check("All six PBR profiles bind outside the four secondary domains",PROFILE_NAMES.all(func(name_):return profiles.has(name_) and int(profiles[name_])>0) and secondary.report().bindings==bound_surfaces,{"profiles":profiles,"secondary_bindings":secondary.report().bindings})
	var admitted:=true
	for index in range(first_check,checks.size()): admitted=admitted and bool(checks[index].passed)
	return admitted

func disable_steps() -> void:
	scene.set_process(false);scene.set_physics_process(false)
	scene.army.set_physics_process(false);player.set_physics_process(false)
	scene.rama_effects.set_process(false)
	scene.army._attacks.clear();scene.army._decision_clock=100000.0;scene.army._next_wave=100000.0

func prepare() -> void:
	scene.set_paused(false);scene.set_overview(false)
	scene._restart_army()
	disable_steps()
	scene.teleport_to(ORIGIN,0)
	player.set_physics_process(true)
	for unused in 8: await physics_frame
	player.set_physics_process(false)
	scene.teleport_to(ORIGIN,0)
	disable_steps()

func player_steps(count: int) -> void:
	for unused in count:
		player._physics_process(DT)
		player.rama_motion.evaluate_pose()

func shader_ownership_counterexample() -> void:
	# COLOR alpha on an ordinary opaque PBR skin is unused by secondary motion.
	# Deliberately attaching the moving shader to that SAME actual skin must fail.
	var victim: MeshInstance3D
	var victim_surface:=-1
	for mesh in meshes():
		if not String(mesh.name).begins_with("RamaHero"): continue
		for index in mesh.mesh.get_surface_count():
			var original: Material=mesh.mesh.surface_get_material(index)
			if original and original.resource_name=="Rama warm skin":
				victim=mesh;victim_surface=index;break
		if victim: break
	if victim==null:
		check("Actual skin-bound moving-shader counterexample has a real skin surface",false)
		return
	var resources:=resource_identity()
	var original_override: Material=victim.get_surface_override_material(victim_surface)
	var wrong:=ShaderMaterial.new()
	wrong.shader=SECONDARY_SHADER
	wrong.resource_name="QA deliberately misplaced secondary shader"
	wrong.set_shader_parameter("secondary_offset",Vector3(.03,0,0))
	victim.set_surface_override_material(victim_surface,wrong)
	var rejected:=not unowned_secondary_surfaces().is_empty()
	victim.set_surface_override_material(victim_surface,original_override)
	check("Actual moving-shader-on-skin counterexample rejects and restores original resources",rejected and unowned_secondary_surfaces().is_empty() and resource_identity()==resources)

func lod_camera_cases() -> void:
	# An actual viewport Camera3D drives the real player's LOD hook. This checks
	# ownership/selection only; occlusion, silhouette and pop need rendered review.
	disable_steps()
	var binding: Node=player.get("rama_lod")
	var old_camera: Camera3D=root.get_camera_3d()
	var camera:=Camera3D.new()
	scene.add_child(camera)
	camera.fov=50
	var center: Vector3=player.global_position+Vector3.UP
	camera.global_position=center+Vector3(0,0,2)
	camera.look_at(center)
	camera.make_current()
	player.velocity=Vector3.ZERO
	var original_resources:=resource_identity()
	var original_face:=face_mesh.get_instance_id()
	binding.reset("QA actual near camera")
	player._update_rama_motion(DT)
	var selected: Dictionary=binding.report()
	check("Actual viewport near camera selects only near body and bow with the original face",selected.level==0 and selected.visible_levels==[0] and face_mesh.visible and face_mesh.get_instance_id()==original_face and one_skin_owner(),{"binding":selected})
	camera.global_position=center+Vector3(0,0,50)
	camera.look_at(center)
	for unused in 24: player._update_rama_motion(DT)
	selected=binding.report()
	check("Actual player camera hook reaches only far body and bow without replacing face or skins",selected.level==2 and selected.visible_levels==[2] and face_mesh.visible and face_mesh.get_instance_id()==original_face and one_skin_owner() and resource_identity()==original_resources,{"binding":selected})
	camera.global_position=center+Vector3(0,0,2)
	camera.look_at(center)
	for unused in 24: player._update_rama_motion(DT)
	selected=binding.report()
	check("Actual viewport approach returns to near with the same admitted resources",selected.level==0 and selected.visible_levels==[0] and resource_identity()==original_resources and one_skin_owner(),{"binding":selected})
	player.reset()
	selected=binding.report()
	check("Actual player reset restores only near visibility and preserves one original face and rig",selected.level==0 and selected.visible_levels==[0] and selected.live_rigs==1 and selected.live_bones==164 and selected.owned_mesh_instances==4 and face_mesh.visible and face_mesh.get_instance_id()==original_face and one_skin_owner() and resource_identity()==original_resources,{"binding":selected})
	if is_instance_valid(old_camera): old_camera.make_current()
	camera.queue_free()
	await frames(2)

func seed_quality_state() -> bool:
	Input.action_press("move_forward")
	player_steps(24)
	Input.action_release("move_forward")
	var accepted: Dictionary=scene.cast_rama_ability("piercing_dawn")
	player_steps(10)
	return accepted.get("accepted",false) and secondary.report().cloth_offset.length()>.0001 and face.report().weights.rama_blink_left>.01

func lifecycle() -> void:
	await prepare()
	check("Real player movement and accepted draw seed nonneutral visible quality state",seed_quality_state(),{"secondary":secondary.report(),"face":face.report()})
	var before_face: Dictionary=face.report()
	var before_secondary: Dictionary=secondary.report()
	var before_morphs:=morph_values()
	var before_uniforms:=uniforms()
	var resources:=resource_identity()
	scene.set_paused(true)
	await frames(5)
	check("Actual world pause holds facial clock and partial blink exactly",face.report()==before_face and morph_values()==before_morphs)
	check("Actual world pause holds secondary inertia and shader offsets exactly",secondary.report()==before_secondary and uniforms()==before_uniforms)
	player._on_focus_lost()
	check("Focus-loss callback clears input without snapping paused quality state",face.report()==before_face and secondary.report()==before_secondary and morph_values()==before_morphs and uniforms()==before_uniforms)
	scene.set_paused(false)
	player_steps(1)
	check("Resume advances one ordinary presentation tick without reset or catch-up",absf(float(face.report().elapsed)-float(before_face.elapsed)-DT)<.000001 and absf(float(secondary.report().elapsed)-float(before_secondary.elapsed)-DT)<.000001 and face.report().reset_count==before_face.reset_count and secondary.report().reset_count==before_secondary.reset_count)
	scene.teleport_to(ORIGIN+Vector3(8,0,0),0)
	var reset_morphs:=true
	for weight in morph_values().values(): reset_morphs=reset_morphs and absf(float(weight))<.000001
	check("Actual teleport clears inertia and every full/half morph before another update",secondary.report().cloth_offset==Vector3.ZERO and secondary.report().hair_offset==Vector3.ZERO and face.report().elapsed==0 and reset_morphs)
	await prepare()
	check("Second real draw fixture is admitted after ordinary world reset",seed_quality_state())
	var receipt: Dictionary=scene.rama_runtime.vitals.receive_damage(300.0,"quality_lifecycle",scene.rama_runtime.vitals.generation,0)
	var audio: Dictionary=scene.rama_runtime.action_audio.report()
	check("Lethal actual receiver receipt reaches audio lifecycle before the alive guard",receipt.get("accepted",false) and not scene.rama_runtime.vitals.alive and not audio.alive and audio.playing==0 and audio.receiver_generation==scene.rama_runtime.vitals.generation,{"receipt":receipt,"audio_alive":audio.alive,"playing":audio.playing})
	player_steps(18)
	var dead_morphs:=morph_values()
	check("Actual death update rests hair/cloth and closes the authored eyelid morphs",secondary.report().cloth_offset==Vector3.ZERO and secondary.report().hair_offset==Vector3.ZERO and dead_morphs.rama_blink_left>.999 and dead_morphs.rama_blink_right>.999 and absf(float(dead_morphs.rama_blink_half_left))<.001 and absf(float(dead_morphs.rama_blink_half_right))<.001,{"morphs":dead_morphs})
	for unused in 62:
		scene.army.step_simulation(.05)
		player_steps(3)
	check("Authority respawn returns the same bound face and materials without corpse state",scene.rama_runtime.vitals.alive and player.active and face.configured and secondary.configured and face.report().weights.rama_blink_left<.05 and face.report().weights.rama_blink_right<.05 and resource_identity()==resources,{"face":face.report(),"secondary":secondary.report()})
	var stable:=true
	for unused in 100:
		player.reset()
		stable=stable and resource_identity()==resources and face.configured and secondary.configured and surface.configured and controller_count(player.visual,"res://scripts/rama_motion.gd")==1
	check("100 actual player resets retain the same rig, face, skins and owned material resources",stable)

func run() -> void:
	started_usec=Time.get_ticks_usec()
	initial_nodes=int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	for path in SOURCE_PATHS:
		if FileAccess.file_exists(path): sources[path]=FileAccess.get_sha256(path)
	var audio_directory:=DirAccess.open("res://assets/audio/rama-quality")
	if audio_directory:
		for name_ in audio_directory.get_files():
			if name_.ends_with(".wav"):
				var path:="res://assets/audio/rama-quality/"+name_
				sources[path]=FileAccess.get_sha256(path)
	root.size=Vector2i(1280,720)
	scene=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	await frames(5)
	player=scene.get("player")
	var ready: bool=scene.world_ready and is_instance_valid(player) and is_instance_valid(scene.rama_runtime) and scene.rama_runtime.configured
	check("Actual Confluence world and current Rama runtime configure",ready)
	if not ready:
		await finish();return
	var asset: String=player.get_script().get_script_constant_map().get("HERO_PATH","")
	var imports_ready: bool=not asset.is_empty() and fresh_import(asset)
	check("Actual hero source and imported scene have matching current stamps",imports_ready,{"asset":asset,"imports":imports})
	# Optional LOD candidates remain a separate visual promotion gate. If present,
	# their exact imported bytes still belong to this actual-world test identity.
	for path in player.get_script().get_script_constant_map().get("HERO_LODS",[]):
		if FileAccess.file_exists(path):
			var current: bool=fresh_import(path)
			check("Present LOD candidate import is current: "+String(path),current)
			imports_ready=imports_ready and current
	if admission() and imports_ready:
		shader_ownership_counterexample()
		await lod_camera_cases()
		await lifecycle()
	await finish()

func finish() -> void:
	Input.action_release("move_forward")
	paused=false
	if is_instance_valid(scene):
		scene.queue_free()
		await frames(5)
		check("World teardown releases all quality component nodes",int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==initial_nodes,{"starting_nodes":initial_nodes,"remaining_nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))})
	var stable:=true
	for path in sources: stable=stable and FileAccess.get_sha256(path)==sources[path]
	check("All tested source and imported bytes stay frozen",stable)
	var passed:=not checks.is_empty()
	for item in checks: passed=passed and item.passed
	var report:={"passed":passed,"checks":checks,"source_sha256":sources,"imports":imports,"engine":Engine.get_version_info().string,"wall_seconds":(Time.get_ticks_usec()-started_usec)/1000000.0,"scope":"Actual Confluence imported hero admission, one-rig ownership, three-level LOD binding and actual viewport camera selection, semantic masks/material isolation, real player update and pause/focus/reset/teleport/death/respawn glue. Headless source-bound regression only; no rendered LOD silhouette/pop, visual closure, cloth collision, hand-contact, listening, OS input, physical-GPU, Windows, online or commercial-quality acceptance."}
	var file:=FileAccess.open(output,FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(report,"\t")+"\n")
	else: passed=false
	print("RAMA_QUALITY_INTEGRATION ",JSON.stringify({"passed":passed,"checks":checks.size(),"report":output}))
	quit(0 if passed else 1)
