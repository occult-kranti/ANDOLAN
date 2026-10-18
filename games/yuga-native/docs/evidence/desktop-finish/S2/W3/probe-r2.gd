extends SceneTree
## Actual scene lifecycle, observed at Player.ready before the parent scene finishes.
## Headless inspection proves material state, not the first rasterized framebuffer.
const Finish = preload("res://scripts/rama_surface_finish.gd")
const EXPECTED_PROFILES := {
	"Rama warm skin":4, "Ivory silk":6, "Recessed antique gold":3,
	"Polished sapphire":6, "Natural lips":3, "Warm sclera":3,
	"Deep brown iris":3, "Pupil":3, "Cobalt handwoven silk":3,
	"Cobalt lotus brocade":3, "Worked warm gold":6, "Swept black hair":3,
}
const PROFILE_MAP := {
	"Rama warm skin":"skin", "Ivory silk":"ivory", "Cobalt handwoven silk":"woven",
	"Cobalt lotus brocade":"woven", "Worked warm gold":"gold", "Swept black hair":"hair",
}
var output := "/tmp/desktop-s2-material-lifecycle.json"
var checks: Array[Dictionary] = []
var observations: Array[Dictionary] = []
var ready_receipts: Array[Dictionary] = []
var owned_refs := {}
var borrowed_refs := {}
var source_paths: Array[String] = []
var source_before := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	node_added.connect(_node_added)
	call_deferred("run")

func check(label: String, ok: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":ok,"details":details})
	print("PASS " if ok else "FAIL ",label)

func _node_added(node: Node) -> void:
	var script = node.get_script()
	if script != null and script.resource_path == "res://scripts/player.gd":
		node.ready.connect(_player_ready.bind(node),CONNECT_ONE_SHOT)

func _player_ready(player: Node) -> void:
	var receipt := inspect("player-ready-"+str(ready_receipts.size()+1),player,true)
	ready_receipts.append(receipt)
	check(receipt.stage+": all expected material profiles already bound",receipt.valid,receipt)

func collect(node: Node, meshes: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh != null: meshes.append(node)
	for child in node.get_children(): collect(child,meshes)

func fingerprint(material: Material) -> String:
	var values := {}
	for property in material.get_property_list():
		if int(property.usage) & PROPERTY_USAGE_STORAGE:
			var value = material.get(property.name)
			values[property.name] = value.resource_path if value is Resource else str(value)
	return JSON.stringify(values).sha256_text()

func inspect(stage: String, player: Node, retain_weak_refs := false) -> Dictionary:
	var profiles := {}
	var material_ids := {}
	var texture_ids := {}
	var issues: Array[String] = []
	var meshes: Array[MeshInstance3D] = []
	var own_refs: Array[WeakRef] = []
	collect(player.visual,meshes)
	for mesh in meshes:
		for surface in mesh.mesh.get_surface_count():
			var source = mesh.mesh.surface_get_material(surface)
			var material := mesh.get_active_material(surface)
			if source == null or material == null: continue
			var key := str(player.visual.get_path_to(mesh))+":"+str(surface)
			material_ids[key] = material.get_instance_id()
			if retain_weak_refs:
				borrowed_refs[source.get_instance_id()]={"ref":weakref(source),"before":fingerprint(source),"name":source.resource_name}
				if material != source: own_refs.append(weakref(material))
			var label := material.resource_name.trim_suffix(Finish.SUFFIX).trim_suffix(" · Rama calibration v1").trim_suffix(" · bounded secondary")
			if not EXPECTED_PROFILES.has(label):
				if material != source: issues.append(key+": unexpected unrecognized override")
				continue
			profiles[label]=int(profiles.get(label,0))+1
			if material is StandardMaterial3D:
				if not material.resource_name.ends_with(Finish.SUFFIX): issues.append(key+": unfinished standard")
				if material.albedo_texture != source.albedo_texture or material.normal_texture != source.normal_texture:
					issues.append(key+": borrowed source texture replaced")
			elif material is ShaderMaterial:
				if material.shader != Finish.SECONDARY_SHADER or material.get_meta(Finish.OWNER_META,0) != player.rama_finish.get_instance_id():
					issues.append(key+": missing finish shader ownership")
				if material.get_shader_parameter("base_texture") != source.albedo_texture or material.get_shader_parameter("normal_texture") != source.normal_texture:
					issues.append(key+": borrowed shader source texture replaced")
			if PROFILE_MAP.has(label):
				var map_name: String = PROFILE_MAP[label]
				var texture: Texture2D = material.roughness_texture if material is StandardMaterial3D else material.get_shader_parameter("rough_texture")
				var scalar: float = material.roughness if material is StandardMaterial3D else material.get_shader_parameter("roughness_value")
				if texture == null or texture.resource_path != Finish.MAP_PATHS[map_name] or scalar != 1.0:
					issues.append(key+": missing or wrong roughness map")
				else:
					if texture_ids.has(map_name) and texture_ids[map_name] != texture.get_instance_id(): issues.append(key+": duplicate texture resource")
					texture_ids[map_name]=texture.get_instance_id()
	if retain_weak_refs: owned_refs[player.get_instance_id()]=own_refs
	var ready: bool = is_instance_valid(player.rama_finish) and player.rama_finish.configured
	var unique_materials := {}
	for id in material_ids.values(): unique_materials[id]=true
	var result := {"stage":stage,"player_id":player.get_instance_id(),"finish_ready":ready,
		"profiles":profiles,"material_ids":material_ids,"texture_ids":texture_ids,"issues":issues,
		"material_slots":material_ids.size(),"unique_active_materials":unique_materials.size(),
		"valid":ready and profiles==EXPECTED_PROFILES and texture_ids.size()==5 and issues.is_empty(),
		"finish":player.rama_finish.report(),"lod":player.rama_lod.report()}
	observations.append(result)
	return result

func borrowed_unchanged() -> bool:
	for entry in borrowed_refs.values():
		var material = entry.ref.get_ref()
		if material != null and fingerprint(material) != entry.before: return false
	return true

func retired(player_id: int) -> Dictionary:
	var live := 0
	for reference in owned_refs[player_id]:
		if reference.get_ref() != null: live+=1
	return {"tracked":owned_refs[player_id].size(),"still_live":live}

func frames(number := 3) -> void:
	for unused in number: await process_frame

func wait_scene(path: String, old_player: Node = null) -> bool:
	var deadline := Time.get_ticks_msec()+60000
	var seen := {}
	while Time.get_ticks_msec()<deadline:
		await process_frame
		var loader := root.get_node_or_null("YugaSceneTransitionLayer/SceneTransition")
		if is_instance_valid(loader) and loader.phase==&"error": return false
		if is_instance_valid(old_player) and is_instance_valid(loader) and not seen.has(loader.phase):
			seen[loader.phase]=true
			var receipt := inspect("loading-"+str(loader.phase),old_player)
			check(receipt.stage+": existing hero retains complete finish",receipt.valid)
		if is_instance_valid(current_scene) and current_scene.scene_file_path==path and (not is_instance_valid(loader) or loader.phase==&"done"):
			await frames()
			return true
	return false

func pin_sources() -> Dictionary:
	var result := {}
	for path in source_paths: result[path]=FileAccess.get_sha256(path)
	return result

func pin_import(path: String) -> void:
	for value in [path,path+".import"]:
		if not source_paths.has(value): source_paths.append(value)
	var config:=ConfigFile.new()
	if config.load(path+".import")!=OK:
		check("Import descriptor can be read: "+path,false)
		return
	var target: String=config.get_value("remap","path","")
	if target.is_empty() or not FileAccess.file_exists(target):
		check("Actual imported payload exists: "+path,false)
		return
	if not source_paths.has(target): source_paths.append(target)

func run() -> void:
	root.size=Vector2i(960,600)
	for path in [get_script().resource_path,"res://scripts/player.gd","res://scripts/rama_surface_materials.gd","res://scripts/rama_secondary_motion.gd","res://scripts/rama_surface_finish.gd","res://scripts/rama_lod_binding.gd","res://scripts/boot.gd","res://scripts/scene_transition.gd","res://scripts/loading_presentation.gd","res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://shaders/rama_secondary_cloth.gdshader","res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb"]:
		source_paths.append(path)
	for path in Finish.MAP_PATHS.values():
		pin_import(path)
	# Pin the actual scene/texture imports used by the three hero levels, not
	# only their raw GLBs. This performs no import or cache rewrite.
	for filename in DirAccess.get_files_at("res://assets/heroes"):
		if filename.begins_with("rama-hero") and filename.ends_with(".import"):
			pin_import("res://assets/heroes/"+filename.trim_suffix(".import"))
	source_before=pin_sources()
	change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
	var arrived := await wait_scene("res://scenes/courtyard.tscn")
	check("Actual boot loader reaches courtyard",arrived)
	if not arrived: await finish();return
	var court: Node=current_scene
	var before := inspect("courtyard-mounted",court.player)
	check("Mounted courtyard has complete finish",before.valid)
	court.start_training();court.reset_training();court.return_to_menu()
	var after := inspect("training-reset-title",court.player)
	check("Training reset and title return preserve exact material and texture identities",after.valid and before.material_ids==after.material_ids and before.texture_ids==after.texture_ids)
	check("Borrowed imported materials remain exact after reset",borrowed_unchanged())
	var court_id: int=court.player.get_instance_id()
	var old_player: Node=court.player
	court.enter_confluence()
	arrived=await wait_scene("res://scenes/confluence_world.tscn",old_player)
	check("Actual threaded route reaches world",arrived)
	if not arrived: await finish();return
	var released := retired(court_id)
	check("Retired courtyard owned material resources release",released.still_live==0,released)
	var world: Node=current_scene
	before=inspect("world-mounted",world.player)
	world._restart_army()
	after=inspect("world-restarted",world.player)
	check("World restart preserves exact material and texture identities",after.valid and before.material_ids==after.material_ids and before.texture_ids==after.texture_ids)
	check("Borrowed imported materials remain exact in second scene",borrowed_unchanged())
	var world_id: int=world.player.get_instance_id()
	old_player=world.player
	world.return_to_courtyard()
	arrived=await wait_scene("res://scenes/courtyard.tscn",old_player)
	check("Actual threaded return reaches courtyard",arrived)
	if not arrived: await finish();return
	released=retired(world_id)
	check("Retired world owned material resources release",released.still_live==0,released)
	var final := inspect("courtyard-returned",current_scene.player)
	check("All three Player.ready observations contained the complete finish",ready_receipts.size()==3 and ready_receipts.all(func(row):return row.valid))
	check("Returned courtyard has complete profiles and five shared maps",final.valid)
	check("Borrowed imported material state survives full route",borrowed_unchanged())
	check("Reported per-profile counts equal actual finished slots in every observed state",
		observations.all(func(row):return row.finish.profiles==row.profiles),
		{"actual":final.profiles,"reported":final.finish.profiles,"total_finished_slots":final.finish.surface_slots})
	var last_id: int=current_scene.player.get_instance_id()
	current_scene.queue_free()
	var layer:=root.get_node_or_null("YugaSceneTransitionLayer")
	if layer != null: layer.queue_free()
	await frames(5)
	released=retired(last_id)
	check("Final scene disposal releases owned materials",released.still_live==0,released)
	await finish()

func finish() -> void:
	check("Runtime, imported-source descriptors and probe unchanged during execution",pin_sources()==source_before)
	var result := {"passed":checks.all(func(row):return row.passed),"checks":checks,"observations":observations,"source_before":source_before,"source_after":pin_sources(),"engine":Engine.get_version_info(),
		"expected_profile_basis":"Raw near GLB material-use counts, body and bow repeated across three runtime LODs; one near face. All12 recognized labels total46 slots. Six dark-bow-leather slots intentionally retain their original material.",
		"scope":"Actual boot/courtyard/world/return in headless Godot; Player.ready observations, exact within-lifetime material/texture identities, five shared imported finish maps and weak-reference disposal. No rendered first frame, shader warmup, pixel quality, pose acceptance, arbitrary scene stress or memory/FPS threshold."}
	var file:=FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify(result,"\t")+"\n");file.close()
	if is_instance_valid(current_scene): current_scene.queue_free()
	var layer:=root.get_node_or_null("YugaSceneTransitionLayer")
	if layer != null: layer.queue_free()
	await frames()
	quit(0 if result.passed else 1)
