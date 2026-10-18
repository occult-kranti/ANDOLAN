extends "res://tools/visual-rounds/capture_groom.gd"
## Two explicitly staged component comparisons; no runtime/material mutation.

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg=="--case=gold-pair": pass
		else: finish("Unknown gold comparison argument "+arg);return
	mode="groom-stills";expected=2
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh absolute output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus":finish("X11 Forward+ required");return
	contract=JSON.parse_string(FileAccess.get_file_as_string("res://tools/visual-rounds/groom_contract.json"))
	contract.stills=contract.stills.filter(func(f):return f.id in ["light-front","dark-profile"])
	if contract.stills.size()!=2:finish("Exact two gold fixtures missing");return
	seed(741031)
	root.size=SIZE;root.content_scale_size=SIZE;root.msaa_3d=Viewport.MSAA_2X;root.show()
	sources=source_hashes()
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene);current_scene=scene
	print("GOLD_COMPARE_STAGE before_initial_draw6")
	await draw(6)
	print("GOLD_COMPARE_STAGE after_initial_draw6")
	player=scene.player
	if not player.model_ready or not scene.environment_ready:finish("Actual hero/world missing");return
	review_camera=Camera3D.new();scene.add_child(review_camera);review_camera.near=.05;review_camera.far=180.0
	player.rama_motion.modification_processed.connect(observe_final_pose)
	scene.start_training();scene.title_light.hide();await draw(8)
	paused=true;Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	scene.ui.hide();freeze_background_time();set_light(false);cache_geometry()
	sequence_controls.append({"kind":"gold_component_comparison","fixture_ids":["light-front","dark-profile"],"upper_hair_added":false,"title_fill":false,"dark_means":"background, not night","scope":"Unchanged groom station/pose/light controls on diagnostic environment; component comparison only."})
	await groom_stills()
	if not done:finish("")

func groom_frame(id: String, required: String) -> void:
	if root.get_camera_3d()!=review_camera:finish("Actual camera differs from declared camera");return
	super.groom_frame(id,required)
	if done:return
	var materials:=[]
	for part in geometry:
		if not "Worked warm gold" in part.name:continue
		var material: ShaderMaterial=part.material
		var texture: Texture2D=material.get_shader_parameter("rough_texture")
		materials.append({"node":String(part.node.name),"surface":part.surface,"visible":part.node.is_visible_in_tree(),"texture":texture.resource_path,"roughness":material.get_shader_parameter("roughness_value"),"metallic":material.get_shader_parameter("metallic_value"),"specular":material.get_shader_parameter("specular_value")})
	if materials.is_empty():finish("No actual worked-gold materials observed");return
	shots[-1]["actual_camera_identity"]={"matches_requested":true,"path":str(review_camera.get_path())}
	shots[-1]["gold_materials"]=materials
	shots[-1]["scope"]="S1 gold component pair; actual imported materials, source-pinned staged camera/light/pose, diagnostic environment. Not production environment or title-interface acceptance."

func source_hashes() -> Dictionary:
	var result:=super.source_hashes()
	for path in ["res://tools/graphics-six/capture_gold.gd","res://.graphics-six-snapshot.json","res://scripts/rama_surface_finish.gd"]:
		result[path]=FileAccess.get_sha256(path)
	return result
