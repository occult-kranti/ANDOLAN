extends "res://tools/wind-court-pilot/capture_pilot.gd"
## Distinct optional PBR gate: accepted geometry/current stone versus same exact
## geometry/native CC0 sandstone material. Six images, not a game-quality claim.
const KitMaterial=preload("res://tools/wind-court-pilot/pbr_material.gd")
var material_report:Dictionary={}
var original_material:Material

func hashes()->Dictionary:
	var values:=super.hashes()
	for path in ["res://tools/wind-court-pilot/capture_material_study.gd","res://tools/wind-court-pilot/pbr_material.gd",KitMaterial.KIT+"manifest.json",KitMaterial.KIT+"sandstone.tres",KitMaterial.KIT+"LICENSES/CC0-1.0.txt"]:
		values[path]=FileAccess.get_sha256(path)
	return values
func views()->Array[Dictionary]:
	return [
		{"id":"close-day","phase":0.0,"at":Vector3(-12,2.2,-100),"target":Vector3(-20,3,-88)},
		{"id":"close-night","phase":1.0,"at":Vector3(-12,2.2,-100),"target":Vector3(-20,3,-88)},
		{"id":"rear-day","phase":0.0,"at":Vector3(-30,4,-77),"target":Vector3(-20,3.7,-88)}
	]
func geometry_stamp()->String:
	var rows:Array=[]
	collect_transforms(candidate,rows)
	for detail in ["WindCourtNear","WindCourtMid"]:
		var mesh:MeshInstance3D=candidate.get_node(detail)
		rows.append([detail,mesh.mesh.get_instance_id(),mesh.mesh.get_surface_count()])
	var body:StaticBody3D=candidate.get_node("WindCourtDetailedCollision")
	for shape in body.get_children():rows.append([shape.shape.get_instance_id(),shape.shape.size])
	return var_to_bytes(rows).hex_encode().sha256_text()
func install_candidate()->void:
	var stamp:=geometry_stamp()
	var result:Dictionary=KitMaterial.new().build(output)
	check("native CC0 material adapter ready",result.get("ok",false),result.get("reason"))
	if not result.get("ok",false):return
	material_report=result.report
	for detail in ["WindCourtNear","WindCourtMid"]:
		var mesh:MeshInstance3D=candidate.get_node(detail)
		mesh.set_surface_override_material(0,result.material)
	check("same geometry and colliders after material override",stamp==geometry_stamp())
	check("seven decks and anchors keep original instances",before==other_identity())
	check("three architecture surfaces remain at both detail levels",candidate.get_node("WindCourtNear").mesh.get_surface_count()==3 and candidate.get_node("WindCourtMid").mesh.get_surface_count()==3)
	check("exactly three verified existing maps within decoded budget",material_report.textures.size()==3 and material_report.decoded_with_mips_bytes<=16777216 and material_report.copied_texture_bytes==0,material_report)
	var space:PhysicsDirectSpaceState3D=scene.world.get_world_3d().direct_space_state
	var origin:Vector3=candidate.global_position
	var hit:Dictionary=space.intersect_ray(PhysicsRayQueryParameters3D.create(origin+Vector3(1.05,3,-6),origin+Vector3(1.05,3,0),1))
	check("actual closed bay collider remains at3.32m",not hit.is_empty() and absf(hit.position.z-(origin.z-3.32))<.001)
	hit=space.intersect_ray(PhysicsRayQueryParameters3D.create(origin+Vector3(0,12,0),origin+Vector3(0,7,0),1))
	check("actual roof remains y8",not hit.is_empty() and is_equal_approx(hit.position.y,8))
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):push_error("Fresh absolute output required");quit(1);return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()!="forward_plus"):push_error("Actual Forward+ display required");quit(1);return
	source_hashes=hashes()
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.msaa_3d=Viewport.MSAA_2X
	if not preflight:root.show()
	scene=load("res://scenes/confluence_world.tscn").instantiate();scene.set("wind_court_pilot_enabled",true);root.add_child(scene);current_scene=scene
	await draw_frames(8)
	check("actual accepted-geometry full world ready",scene.world_ready and scene.player.model_ready and scene.landmark_report.wind_court_pilot.enabled)
	if not checks[-1].passed:await finish();return
	candidate=scene.world.get_node("TraversalRelics/sun-lift-west")
	original_material=candidate.get_node("WindCourtNear").get_active_material(0)
	scene.set_overview(false);scene.set_paused(false);scene.set_review_phase(0)
	scene.set_process(false);scene.set_physics_process(false);hold_callbacks(scene.world)
	for water in scene.manifest.waters:
		var material:ShaderMaterial=scene.world.get_node(water.id).get_active_material(0)
		water_clock_controls.append({"id":water.id,"previous_animation_speed":material.get_shader_parameter("animation_speed"),"comparison_animation_speed":0.0});material.set_shader_parameter("animation_speed",0.0)
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	camera=Camera3D.new();camera.fov=65;camera.near=.08;camera.far=380;scene.add_child(camera);camera.current=true
	await draw_frames(2)
	held=freeze_state();before=other_identity()
	for view in views():await capture("geometry-stone",view)
	await install_candidate()
	for view in views():await capture("optional-cc0-pbr",view)
	check("six matched states produced",shots.size()==6)
	for index in 3:check("matched material-study camera "+String(views()[index].id),shots[index].camera==shots[index+3].camera and shots[index].phase==shots[index+3].phase)
	await finish()
func finish()->void:
	var after:=hashes()
	check("source kit and canonical source unchanged",source_hashes==after)
	var passed:=checks.all(func(row):return row.passed)
	var report:={"complete":passed,"preflight":preflight,"actual_image_count":0 if preflight else shots.size(),"shots":shots,"checks":checks,"material":material_report,"held_state":held,"hold_controls":hold_controls,"water_clock_controls":water_clock_controls,"source_sha256":source_hashes,"source_after_sha256":after,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"display":DisplayServer.get_name(),"engine":Engine.get_version_info(),"canonical_material_promoted":false,"scope":"Optional native PBR study on accepted one-court geometry. Three matched near day/night and rear day camera pairs, callbacks and actual bone/army poses held identically, physics retained. Existing CC0 sources read directly; one owned surface0 override perLOD, no shader file, geometry or collision change. No whole-game art, continuous motion, hardware performance or canonical material acceptance."}
	FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	if is_instance_valid(scene):scene.queue_free()
	for unused in 8:await process_frame
	print("WIND_COURT_MATERIAL_COMPLETE ",passed)
	quit(0 if passed else 1)
