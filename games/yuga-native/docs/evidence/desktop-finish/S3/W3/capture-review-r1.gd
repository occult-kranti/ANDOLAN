extends "res://tools/visual-rounds/capture_groom.gd"
## Review-only ablation. Invoke with --mode=groom-actions. Same source both runs;
## only YUGA_FLETCHING_REVIEW=off/on changes optional geometry admission.
const Fletching = preload("res://scripts/rama_arrow_fletching.gd")
var optional_helper: Node

func existing_ivory() -> StandardMaterial3D:
	for node in player.visual.find_children("*","MeshInstance3D",true,false):
		if node.mesh==null: continue
		for surface in node.mesh.get_surface_count():
			var material: Material=node.get_active_material(surface)
			if material is StandardMaterial3D and material.resource_name=="Ivory silk · Rama finish v2": return material
	return null

func source_hashes() -> Dictionary:
	var result:=super.source_hashes()
	for path in ["res://art/hero-finish/s3-arrow-fletching/capture_review.gd",Fletching.DATA_PATH]:
		result[path]=FileAccess.get_sha256(path)
	return result

func candidate_projection() -> Dictionary:
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(Fletching.DATA_PATH))
	var low:=Vector2(INF,INF);var high:=Vector2(-INF,-INF);var behind:=0
	for point in data.vertices:
		var world: Vector3=player.rama_motion.nocked_arrow.global_transform*Vector3(point[0],point[1],point[2])
		var pixel:=review_camera.unproject_position(world)
		low=low.min(pixel);high=high.max(pixel)
		if review_camera.is_position_behind(world): behind+=1
	return {"min":normal(low),"max":normal(high),"behind":behind,
		"passed":behind==0 and low.x>=24 and low.y>=24 and high.x<=SIZE.x-24 and high.y<=SIZE.y-24,
		"scope":"Same candidate vertex projection in both branches; no pixel occlusion or size acceptance."}

func groom_actions() -> void:
	expected=2
	var toggle:=OS.get_environment("YUGA_FLETCHING_REVIEW")
	if toggle not in ["off","on"]: finish("Explicit YUGA_FLETCHING_REVIEW=off/on required");return
	var enabled:=toggle=="on"
	if player.visual.has_meta(&"rama_upper_hair_layers_owner") or player.visual.find_child("SevenSweptUpperHairLayers",true,false)!=null:
		finish("Optional upper-hair helper must remain off");return
	var ivory:=existing_ivory()
	if ivory==null: finish("Current finished ivory missing");return
	if enabled:
		optional_helper=Fletching.new();player.visual.add_child(optional_helper)
		if not optional_helper.configure(player.rama_motion.nocked_arrow,ivory): finish("Optional fletching refused");return
	sequence_controls.append({"kind":"optional_fletching_only","enabled":enabled,
		"geometry_sha256":FileAccess.get_sha256(Fletching.DATA_PATH),"material_name":ivory.resource_name,
		"material_roughness":ivory.roughness,"roughness_texture":ivory.roughness_texture.resource_path,
		"default_activation":false,"upper_hair_enabled":false})
	paused=false
	scene.reset_training();scene.start_training();scene.ui.hide();scene.title_light.hide()
	for action in ["move_left","move_right","move_forward","move_back","fire"]: Input.action_release(action)
	player.global_position=Vector3(-.65,.0001,0);player.velocity=Vector3.ZERO
	player.yaw=0;player.pitch=0;player._update_camera();player.visual.rotation.y=PI
	player.reset_physics_interpolation();player.visual.reset_physics_interpolation()
	set_light(false)
	player.camera.make_current()
	await draw(8)
	if not player.is_on_floor(): finish("Actor lacks actual floor contact");return
	var origin: Vector3=player.camera.project_ray_origin(Vector2(SIZE)*.5)
	var direction: Vector3=player.camera.project_ray_normal(Vector2(SIZE)*.5)
	var hit: Dictionary=scene.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(origin,origin+direction*80,1|4,[player.get_rid()]))
	if hit.is_empty() or String(hit.collider.name)!="Target03": finish("Actual player aim misses Target03");return
	scene.rama_runtime.combat_event.connect(record_event)
	var cast: Dictionary=scene.rama_runtime.cast_ability("piercing_dawn")
	if not cast.get("accepted",false): finish("Actual Piercing Dawn refused");return
	var begin_time: float=scene.rama_runtime.kit.elapsed
	var age:=0.0;var frames:=0
	while age+.000001<.30 and frames<30:
		await draw(1);frames+=1
		age=scene.rama_runtime.kit.elapsed-begin_time
	paused=true
	if age>.325 or player.rama_motion.action_stage!="windup" or not player.rama_motion.nocked_arrow.visible:
		finish("Required live nocked windup missing");return
	sequence_controls.append({"kind":"real_public_cast","cast":normal(cast),"authority_age_s":age,
		"advanced_render_frames":frames,"aim_hit":normal(hit.position),"collider":String(hit.collider.name)})
	for view in ["normal-camera","hand-close"]:
		var arrow: Node3D=player.rama_motion.nocked_arrow
		if view=="normal-camera":
			review_camera.global_transform=player.camera.global_transform
			review_camera.fov=player.camera.fov
		else:
			var center: Vector3=arrow.global_transform*Vector3(0,.10,0)
			review_camera.global_position=center+arrow.global_basis.x*.60+arrow.global_basis.z*.65+Vector3.UP*.25
			review_camera.look_at(center);review_camera.fov=35
		review_camera.near=.05;review_camera.make_current();review_camera.reset_physics_interpolation()
		player.rama_lod.reset("S3 fletching camera");player.rama_lod.update(review_camera,1.0/30)
		await draw(4)
		var projection:=candidate_projection()
		if not projection.passed or posed_globals.size()!=164: finish("Fletching framing/final modifier snapshot missing");return
		if preflight:
			shots.append({"id":view,"camera":normal(review_camera.global_transform),"fov":review_camera.fov})
		else:
			write_frame(view,review_camera,"S3 optional fletching ablation; paused real Piercing Dawn windup. Normal player camera or explicit hand close-up; no motion-quality claim.")
			if done:return
		shots[-1]["fletching_enabled"]=enabled
		shots[-1]["candidate_projection"]=projection
		shots[-1]["arrow_global"]=normal(arrow.global_transform)
		shots[-1]["rendered_pose_globals"]=normal(posed_globals)
		shots[-1]["rendered_pose_pin"]=JSON.stringify(normal(posed_globals),"",true,true).sha256_text()
		shots[-1]["secondary"]=normal(player.rama_secondary.report())
		shots[-1]["nocked_visible"]=arrow.is_visible_in_tree()
		shots[-1]["scope"]="Geometry projection is not visibility. Compare original off/on images and exact non-toggle controls before any art decision."
