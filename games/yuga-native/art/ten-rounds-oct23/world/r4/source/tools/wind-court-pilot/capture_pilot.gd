extends SceneTree
## Matched, callback-held art comparison in the actual canonical full world.
## The only live art substitution is the opt-in sun-lift-west pilot. This is not
## a normal-input journey, performance benchmark, or multiplayer qualification.
const Builder=preload("res://scripts/traversal_landmarks.gd")
const HISTORICAL_CAMERA:=Transform3D(Basis(Vector3(-1,0,-8.74227765734759e-8),Vector3(-8.72771455107113e-9,.995004177093506,.0998334214091301),Vector3(8.69860272700862e-8,.0998334214091301,-.995004177093506)),Vector3(-.649999678134918,1.85025632381439,-115.482513427734))
var output:=""
var scene:Node3D
var camera:Camera3D
var checks:Array[Dictionary]=[]
var shots:Array[Dictionary]=[]
var before:Dictionary={}
var source_hashes:Dictionary={}
var pilot_report:Dictionary={}
var held:Dictionary={}
var old_court:Node3D
var old_body:StaticBody3D
var candidate:Node3D
var water_clock_controls:Array[Dictionary]=[]
var replacement_counts:Dictionary={}
var preflight:=false
var hold_controls:Array[Dictionary]=[]

func _initialize()->void:call_deferred("run")
func check(label:String,value:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":value,"detail":detail})
func vector(v:Vector3)->Array:return [v.x,v.y,v.z]
func transform(t:Transform3D)->Array:return [vector(t.basis.x),vector(t.basis.y),vector(t.basis.z),vector(t.origin)]
func hashes()->Dictionary:
	var result:Dictionary={}
	for path in ["res://scripts/traversal_landmarks.gd","res://scripts/traversal_stone.gdshader","res://scripts/world_render_resources.gd","res://scripts/confluence_world.gd","res://scripts/world_lane_frontage.gd","res://scripts/world_roof_loggia.gd","res://scripts/world_water.gdshader","res://scripts/world_ground.gdshader","res://scripts/world_lighting.gd","res://scripts/rama_motion.gd","res://scripts/rama_hero_hud.gd","res://assets/world/confluence-map.json","res://tools/wind-court-pilot/capture_pilot.gd"]:
		if FileAccess.file_exists(path):result[path]=FileAccess.get_sha256(path)
	return result
func draw_frames(count:int)->void:
	for unused in count:
		await process_frame
		if not preflight:await RenderingServer.frame_post_draw
func hold_callbacks(node:Node)->void:
	# Process-mode DISABLED is unsafe here: it can remove CollisionObject3D
	# from physics while explicit PAUSABLE children keep running. Hold actual
	# callbacks and animation writers, leaving every physics body participating.
	node.set_process(false);node.set_physics_process(false)
	if node is AnimationMixer:
		node.active=false
		hold_controls.append({"node":str(node.get_path()),"kind":"AnimationMixer.active=false"})
	if node is SkeletonModifier3D:
		node.active=false
		hold_controls.append({"node":str(node.get_path()),"kind":"SkeletonModifier3D.active=false"})
	for child in node.get_children():hold_callbacks(child)
func state_differences(actual:Dictionary)->Array[Dictionary]:
	var differences:Array[Dictionary]=[]
	for field in held:
		if actual.get(field)!=held[field]:differences.append({"field":field,"expected":held[field],"actual":actual.get(field)})
	return differences
func freeze_state()->Dictionary:
	var bones:Array=[]
	var skeleton:Skeleton3D=scene.player.rama_motion.get_skeleton()
	for index in skeleton.get_bone_count():bones.append(skeleton.get_bone_global_pose(index))
	var army_pose:Array=[]
	collect_transforms(scene.army,army_pose)
	return {"hero_transform":transform(scene.player.global_transform),"hero_velocity":vector(scene.player.velocity),"army_elapsed":scene.army.elapsed,"army_report":scene.army.report(),"kit_elapsed":scene.rama_kit.elapsed,"hero_pose_sha256":var_to_bytes(bones).hex_encode().sha256_text(),"hero_bones":bones.size(),"army_transform_sha256":var_to_bytes(army_pose).hex_encode().sha256_text(),"army_transform_count":army_pose.size(),"scope":"Callbacks held after actual full-world load; actual skeletal bone poses and all army Node3D transforms are compared, alongside simulation clocks."}
func collect_transforms(node:Node,rows:Array)->void:
	if node is Node3D:rows.append([str(node.get_path()),node.transform])
	for child in node.get_children():collect_transforms(child,rows)
func other_identity()->Dictionary:
	var result:Dictionary={}
	var relics:Node3D=scene.world.get_node("TraversalRelics")
	for entry in scene.manifest.traversal.landmarks:
		if entry.id!=Builder.WIND_COURT_ID:result[entry.id]=relics.get_node(entry.id).get_instance_id()
	for anchor in scene.manifest.traversal.anchors:result[anchor.id]=relics.get_node(anchor.id).get_instance_id()
	return result
func install_candidate()->void:
	var relics:Node3D=scene.world.get_node("TraversalRelics")
	old_court=relics.get_node(Builder.WIND_COURT_ID)
	old_body=scene.world.get_node(Builder.WIND_COURT_COLLISION_ID)
	# Reuse these exact immutable material resources from the old node, including
	# its stone shader: no added material, shader, texture, or light resource.
	var stone:Material=old_court.get_node("SolidLandingDeck").get_active_material(0)
	var warm:Material=old_court.get_node("CorniceFace").get_active_material(0)
	var shade:Material=old_court.get_node("ClearLandingMedallion").get_active_material(0)
	replacement_counts={"baseline_mesh_instances":old_court.get_children().filter(func(child):return child is MeshInstance3D).size(),"baseline_opaque_architecture_instances":19,"old_collider_shapes":old_body.get_child_count()}
	candidate=Node3D.new();candidate.name=Builder.WIND_COURT_ID
	candidate.position=old_court.position
	relics.remove_child(old_court)
	relics.add_child(candidate)
	var builder=Builder.new()
	pilot_report=builder._wind_court(candidate,stone,warm,shade,true)
	var mesh:ArrayMesh=candidate.get_node("WindCourtNear").mesh
	check("exact existing immutable materials reused",mesh.surface_get_material(0)==stone and mesh.surface_get_material(1)==warm and mesh.surface_get_material(2)==shade)
	# Preserve exact original landing signals as instances, not reconstructed copies.
	for child in old_court.get_children():
		if child is MeshInstance3D and (child.name=="ClearLandingMedallion" or child.mesh is SphereMesh and child.position.y>8):
			old_court.remove_child(child);candidate.add_child(child)
	replacement_counts.pilot_mesh_instances=candidate.get_children().filter(func(child):return child is MeshInstance3D).size()
	replacement_counts.pilot_architecture_lod_instances=2
	replacement_counts.pilot_active_architecture_surfaces=3
	replacement_counts.pilot_collider_shapes=36
	scene.native_platform_bodies.erase(old_body)
	scene.world.remove_child(old_body)
	var detailed:StaticBody3D=candidate.get_node("WindCourtDetailedCollision")
	detailed.set_meta("native_only",true)
	detailed.add_to_group("confluence_native_platform")
	scene.native_platform_bodies.append(detailed)
	check("only exact old manifest box removed",not scene.world.has_node(Builder.WIND_COURT_COLLISION_ID) and detailed.get_child_count()==36)
	check("seven decks and all anchors preserve instance identity",before==other_identity())
	check("gold anchor unchanged and present",relics.has_node("sun-lift-west-ring"))
	await physics_frame;await physics_frame
	var space:PhysicsDirectSpaceState3D=scene.world.get_world_3d().direct_space_state
	var origin:=candidate.global_position
	var hit:Dictionary=space.intersect_ray(PhysicsRayQueryParameters3D.create(origin+Vector3(1.05,3,-6),origin+Vector3(1.05,3,0),1))
	check("full-world ray sees recessed closed bay and no flat blocker",not hit.is_empty() and absf(hit.position.z-(origin.z-3.32))<.001,{"hit":not hit.is_empty(),"position":vector(hit.position) if not hit.is_empty() else null})
	hit=space.intersect_ray(PhysicsRayQueryParameters3D.create(origin+Vector3(0,12,0),origin+Vector3(0,7,0),1))
	check("full-world roof remains y8",not hit.is_empty() and is_equal_approx(hit.position.y,8),{"hit":not hit.is_empty(),"position":vector(hit.position) if not hit.is_empty() else null})
func views()->Array[Dictionary]:
	return [
		{"id":"ordinary-day","phase":0.0,"ordinary":true},
		{"id":"ordinary-night","phase":1.0,"ordinary":true},
		{"id":"close-day","phase":0.0,"at":Vector3(-12,2.2,-100),"target":Vector3(-20,3,-88)},
		{"id":"close-night","phase":1.0,"at":Vector3(-12,2.2,-100),"target":Vector3(-20,3,-88)},
		{"id":"landing-day","phase":0.0,"at":Vector3(-9,16,-101),"target":Vector3(-20,7,-88)},
		{"id":"rear-day","phase":0.0,"at":Vector3(-30,4,-77),"target":Vector3(-20,3.7,-88)},
		{"id":"lateral-00","phase":0.0,"at":Vector3(-11.3,2.2,-100),"target":Vector3(-20,3,-88)},
		{"id":"lateral-02","phase":0.0,"at":Vector3(-12.7,2.2,-100),"target":Vector3(-20,3,-88)}
	]
func capture(kind:String,view:Dictionary)->void:
	scene.set_review_phase(float(view.phase))
	if view.get("ordinary",false):
		camera.global_transform=HISTORICAL_CAMERA
	else:
		camera.global_position=view.at;camera.look_at(view.target)
	camera.reset_physics_interpolation()
	await draw_frames(2)
	var actual:=freeze_state()
	var differences:=state_differences(actual)
	if preflight:
		shots.append({"view":view.id,"variant":kind,"phase":view.phase,"camera":transform(camera.global_transform),"state_unchanged":actual==held,"state_differences":differences})
		check("held hero/army/kit state "+kind+"-"+String(view.id),actual==held,differences)
		return
	var image:=root.get_texture().get_image()
	var name:=kind+"-"+String(view.id)+".png"
	var saved:=not image.is_empty() and image.save_png(output.path_join(name))==OK
	check("actual image "+name,saved and image.get_width()==960 and image.get_height()==540)
	var objects:=RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)
	var primitives:=RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
	check("real rendering "+name,objects>0 and primitives>0)
	shots.append({"file":name,"sha256":FileAccess.get_sha256(output.path_join(name)),"view":view.id,"variant":kind,"phase":view.phase,"camera":transform(camera.global_transform),"fov":camera.fov,"near":camera.near,"far":camera.far,"width":image.get_width(),"height":image.get_height(),"drawn_frame":Engine.get_frames_drawn(),"objects":objects,"primitives":primitives,"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"state_unchanged":actual==held,"state_differences":differences})
	check("held hero/army/kit state "+name,actual==held,differences)
	print("WIND_COURT_IMAGE ",name)
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):push_error("Fresh absolute output directory required");quit(1);return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()!="forward_plus"):push_error("Actual Forward+ X11/Vulkan required");quit(1);return
	source_hashes=hashes()
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.msaa_3d=Viewport.MSAA_2X;root.title="YUGA — single court matched art review"
	if not preflight:root.show()
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene
	await draw_frames(8)
	check("actual full world ready",scene.world_ready and scene.player.model_ready and scene.player.traversal_report().enabled)
	if not checks[-1].passed:await finish();return
	scene.set_overview(false);scene.set_paused(false);scene.set_review_phase(0)
	await draw_frames(2)
	# Freeze all product callbacks before comparing. Keep actual existing HUD,
	# lights, characters and props. This staging is recorded explicitly.
	scene.set_process(false);scene.set_physics_process(false)
	hold_callbacks(scene.world)
	# World water is the only time-dependent shader in this scene. Use its
	# existing animation-speed uniform identically for both variants, at clock0.
	for water in scene.manifest.waters:
		var material:ShaderMaterial=scene.world.get_node(water.id).get_active_material(0)
		water_clock_controls.append({"id":water.id,"previous_animation_speed":material.get_shader_parameter("animation_speed"),"comparison_animation_speed":0.0})
		material.set_shader_parameter("animation_speed",0.0)
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	camera=Camera3D.new();camera.name="MatchedCourtReviewCamera";camera.fov=65;camera.near=.08;camera.far=380;scene.add_child(camera);camera.current=true
	# Allow final skeletal modifier invalidation and pending queue cleanup to
	# settle before pinning any expected state, not after the first screenshot.
	await draw_frames(2)
	held=freeze_state();before=other_identity()
	for view in views():await capture("baseline",view)
	await install_candidate()
	for view in views():await capture("pilot",view)
	check("all sixteen matched states produced",shots.size()==16)
	for index in 8:check("matched camera and phase "+String(views()[index].id),shots[index].camera==shots[index+8].camera and shots[index].phase==shots[index+8].phase)
	await finish()
func finish()->void:
	var after:=hashes()
	check("canonical sources unchanged during capture",source_hashes==after)
	var passed:=checks.all(func(row):return row.passed)
	var result:={"complete":passed,"preflight":preflight,"actual_image_count":0 if preflight else shots.size(),"checks":checks,"shots":shots,"pilot":pilot_report,"replacement_counts":replacement_counts,"held_state":held,"hold_controls":hold_controls,"water_clock_controls":water_clock_controls,"source_sha256":source_hashes,"source_after_sha256":after,"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"engine":Engine.get_version_info(),"canonical_enabled":false,"scope":"Actual canonical full-world load, then each process/physics callback held, animation mixers and skeletal modifiers deactivated, settled two frames before state pin. Physics bodies retain participation. Eight matched staged art views for baseline and isolated pilot; exact historical ordinary camera transform. Same original materials, roof signals, seven other deck and anchor instances. Existing water animation-speed uniform set0 identically. Existing lighting manually set per named phase. Three lateral views are sparse lateral-00, close-day, lateral-02 samples; no continuous/LOD-threshold proof. Headless preflight creates zero images. No normal-input, multiplayer, hardware FPS, current-source pixel identity to historical capture, or commercial visual-parity claim."}
	FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	if is_instance_valid(old_court):old_court.free()
	if is_instance_valid(old_body):old_body.free()
	if is_instance_valid(scene):scene.queue_free()
	for unused in 8:await process_frame
	print("WIND_COURT_CAPTURE_COMPLETE ",passed)
	quit(0 if passed else 1)
