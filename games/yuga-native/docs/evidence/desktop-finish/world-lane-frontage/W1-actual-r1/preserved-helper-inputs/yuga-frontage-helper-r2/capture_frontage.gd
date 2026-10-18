extends "res://tools/graphics-six/capture_compact_screens.gd"
## Private three-view frontage review; identical helper in both sibling branches.
## No canonical runtime/authority/pose/time/lighting edits.
const Frontage = preload("res://art/world-finish/lane-frontage-r1/candidate.gd")
const SELECTION := "res://tools/visual-rounds/frontage-review.json"
var branch := ""
var review_camera: Camera3D
var frontage_result: Dictionary = {}
var serialization_errors: Array[String] = []
var resource_rows: Dictionary = {}
var material_ids: Dictionary = {}
var route_checks: Dictionary = {}
var final_pose: Dictionary = {}
var final_pose_signals := 0
var completed_post_draws := 0

func frames(count: int) -> void:
	# Identical inherited frame schedule; this counter observes actual completed draws.
	for unused in count:
		await process_frame
		if not preflight:
			await RenderingServer.frame_post_draw
			completed_post_draws += 1


func observe_final_pose() -> void:
	# Observe while completed RamaMotion transforms exist, before Skeleton3D restores them.
	var scene: Node3D = current_scene
	var rig: Skeleton3D = scene.player.rama_motion.rig
	var names: Array = []
	var poses: Array = []
	for index in rig.get_bone_count():
		names.append(String(rig.get_bone_name(index)))
		poses.append(encode_value(rig.get_bone_global_pose(index)))
	var active_modifiers: Array = []
	for child in rig.get_children():
		if child is SkeletonModifier3D and child.active and child.influence>0.0: active_modifiers.append(String(child.name))
	final_pose_signals += 1
	final_pose = {"bone_names":names,"bone_global_poses":poses,"rig_transform":transform_values(rig.global_transform),"hero_transform":transform_values(scene.player.global_transform),"active_modifiers":active_modifiers,"observer_modifier":String(scene.player.rama_motion.name),"signals":final_pose_signals,"completed_post_draws":completed_post_draws,"process_frame":Engine.get_process_frames(),"physics_frame":Engine.get_physics_frames(),"drawn_frame":Engine.get_frames_drawn()}


func transform_values(value: Transform3D) -> Array:
	return [vector(value.basis.x),vector(value.basis.y),vector(value.basis.z),vector(value.origin)]

func surface_vertex_counts(mesh: Mesh) -> Array:
	var result: Array = []
	for index in mesh.get_surface_count(): result.append(mesh.surface_get_arrays(index)[Mesh.ARRAY_VERTEX].size())
	return result

func metadata_values(node: Node) -> Dictionary:
	var result: Dictionary = {}
	var names: Array = node.get_meta_list(); names.sort()
	for name in names: result[String(name)] = encode_value(node.get_meta(name))
	return result

func encode_value(value: Variant, depth: int = 0) -> Variant:
	if depth > 16:
		serialization_errors.append("resource/property depth exceeds16")
		return null
	match typeof(value):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING: return value
		TYPE_STRING_NAME, TYPE_NODE_PATH: return String(value)
		TYPE_FLOAT:
			if not is_finite(value): serialization_errors.append("nonfinite scalar")
			return value if is_finite(value) else null
		TYPE_VECTOR2, TYPE_VECTOR2I: return encode_value([value.x,value.y],depth+1)
		TYPE_VECTOR3, TYPE_VECTOR3I: return encode_value([value.x,value.y,value.z],depth+1)
		TYPE_VECTOR4, TYPE_VECTOR4I, TYPE_QUATERNION: return encode_value([value.x,value.y,value.z,value.w],depth+1)
		TYPE_COLOR: return encode_value([value.r,value.g,value.b,value.a],depth+1)
		TYPE_RECT2, TYPE_RECT2I: return encode_value([value.position,value.size],depth+1)
		TYPE_AABB: return encode_value([value.position,value.size],depth+1)
		TYPE_PLANE: return encode_value([value.normal,value.d],depth+1)
		TYPE_BASIS: return encode_value([value.x,value.y,value.z],depth+1)
		TYPE_TRANSFORM3D: return encode_value(transform_values(value),depth+1)
		TYPE_TRANSFORM2D: return encode_value([value.x,value.y,value.origin],depth+1)
		TYPE_PROJECTION: return encode_value([value.x,value.y,value.z,value.w],depth+1)
		TYPE_DICTIONARY:
			var result: Dictionary = {}
			for key in value:
				if typeof(key) not in [TYPE_STRING,TYPE_STRING_NAME]:
					serialization_errors.append("non-string dictionary key")
					continue
				result[String(key)] = encode_value(value[key],depth+1)
			return result
		TYPE_OBJECT:
			if value == null: return null
			if value is Resource: return resource_value(value,depth+1)
			if value is Node: return {"node_path":String(current_scene.get_path_to(value))}
			serialization_errors.append("unsupported object "+value.get_class())
			return null
		TYPE_RID:
			serialization_errors.append("opaque RID in stored property")
			return null
	if value is Array or typeof(value) >= TYPE_PACKED_BYTE_ARRAY:
		var result: Array = []
		for item in value: result.append(encode_value(item,depth+1))
		return result
	serialization_errors.append("unsupported variant "+str(typeof(value)))
	return null

func stored_properties(object: Object, depth: int = 0) -> Dictionary:
	var result: Dictionary = {}
	var names: Array[String] = []
	for property in object.get_property_list():
		var name := String(property.name)
		# Script bytes and imported/raw closure are already pinned separately.
		# Instance IDs, ResourceUIDs and inspector categories are not controls.
		if property.usage & PROPERTY_USAGE_STORAGE and name not in ["script","resource_path","resource_scene_unique_id"]:
			names.append(name)
	names.sort()
	for name in names: result[name] = encode_value(object.get(name),depth+1)
	return result

func resource_value(resource: Resource, depth: int) -> Dictionary:
	var path := resource.resource_path
	var origin := path.get_slice("::",0)
	var row := {"class":resource.get_class(),"path":path}
	if origin.begins_with("res://") and FileAccess.file_exists(origin): row.source_sha256 = FileAccess.get_sha256(origin)
	# External/embedded textures are identified by exact raw source and import
	# closure, never by GPU instance IDs or a readback that changes timing.
	if resource is Texture2D and not path.is_empty(): return row
	if resource is Shader:
		row.code = resource.code
		return row
	row.properties = stored_properties(resource,depth+1)
	if resource is ShaderMaterial and resource.shader:
		row.shader_uniforms = {}
		for uniform in resource.shader.get_shader_uniform_list():
			row.shader_uniforms[String(uniform.name)] = encode_value(resource.get_shader_parameter(uniform.name),depth+1)
	return row

func material_id(material: Material) -> String:
	if not material: return "none"
	var instance := material.get_instance_id()
	if material_ids.has(instance): return material_ids[instance]
	var row := resource_value(material,0)
	var key := JSON.stringify(row).sha256_text()
	resource_rows[key] = row
	material_ids[instance] = key
	return key

func collect_scene_controls(node: Node, lights: Array, meshes: Array) -> void:
	if node is Light3D:
		lights.append({"path":String(current_scene.get_path_to(node)),"class":node.get_class(),"global_transform":encode_value(node.global_transform),"visible":node.is_visible_in_tree(),"properties":stored_properties(node)})
	if node is MeshInstance3D and node.mesh:
		var surfaces: Array = []
		for index in node.mesh.get_surface_count(): surfaces.append(material_id(node.get_active_material(index)))
		meshes.append({"path":String(current_scene.get_path_to(node)),"mesh_path":node.mesh.resource_path,"aabb":encode_value(node.mesh.get_aabb()),"surface_vertices":surface_vertex_counts(node.mesh),"global_transform":encode_value(node.global_transform),"visible":node.is_visible_in_tree(),"layers":node.layers,"cast_shadow":node.cast_shadow,"transparency":node.transparency,"material_override":material_id(node.material_override),"material_overlay":material_id(node.material_overlay),"surfaces":surfaces})
	for child in node.get_children(): collect_scene_controls(child,lights,meshes)

func collision_inventory(node: Node, result: Array) -> void:
	if node is CollisionObject3D:
		var row:={"path":String(node.get_path()),"class":node.get_class(),"layer":node.collision_layer,"mask":node.collision_mask,"transform":transform_values(node.global_transform),"metadata":metadata_values(node),"shapes":[]}
		for child in node.get_children():
			if child is not CollisionShape3D: continue
			var shape:Shape3D=child.shape
			var item:={"path":String(child.get_path()),"class":shape.get_class(),"disabled":child.disabled,"transform":transform_values(child.transform)}
			if shape is BoxShape3D: item.size=vector(shape.size)
			elif shape is CapsuleShape3D: item.height=shape.height;item.radius=shape.radius
			elif shape is ConcavePolygonShape3D:
				var values:Array=[]
				for point in shape.get_faces(): values.append(vector(point))
				item.faces=values.size()/3;item.faces_sha256=JSON.stringify(values).sha256_text();item.backface_collision=shape.backface_collision
			row.shapes.append(item)
		result.append(row)
	for child in node.get_children(): collision_inventory(child,result)

func existing_materials(old: Node3D) -> Array:
	var result: Array = []
	var meshes: Array = old.find_children("*","MeshInstance3D",true,false)
	if old is MeshInstance3D: meshes.push_front(old)
	for name in Frontage.MATERIAL_NAMES:
		var found: Material
		for node in meshes:
			if node.mesh == null: continue
			for index in node.mesh.get_surface_count():
				var imported: Material = node.mesh.surface_get_material(index)
				if imported != null and imported.resource_name == name: found = node.get_active_material(index)
		result.append(found)
	return result

func frontage_state(scene: Node3D) -> Dictionary:
	var old: Node3D = scene.world.get_node(Frontage.TARGET)
	var body: StaticBody3D = scene.world.get_node(Frontage.BODY)
	var holders: Array = []
	for child in body.get_children():
		if child is CollisionShape3D and not child.disabled: holders.append(child)
	var existing: Array = existing_materials(old)
	var result := {"branch":branch,"target_path":String(old.get_path()),"target_transform":transform_values(old.global_transform),"target_visible":old.visible,"body_path":String(body.get_path()),"body_transform":transform_values(body.global_transform),"body_metadata":metadata_values(body),"shape_owner_count":body.get_shape_owners().size(),"active_shape_count":holders.size(),"material_ids":existing.map(func(item): return material_id(item)),"data_sha256":FileAccess.get_sha256(Frontage.DATA),"replacement_present":scene.world.get_node_or_null(Frontage.ROOT) != null}
	if holders.size() != 1: return result
	var shape: Shape3D = holders[0].shape
	result.shape_class = shape.get_class()
	if shape is BoxShape3D: result.box_size = vector(shape.size)
	if branch == "candidate" and frontage_result.get("ok",false):
		var instance: MeshInstance3D = frontage_result.mesh
		if not shape is ConcavePolygonShape3D:
			serialization_errors.append("candidate shape is not ConcavePolygonShape3D")
			return result
		var concave := shape as ConcavePolygonShape3D
		var faces: PackedVector3Array = concave.get_faces()
		var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Frontage.DATA))
		var offset := 0
		var local_exact := true
		var body_local_exact := true
		var world_approx := true
		var max_world_error := 0.0
		for surface in instance.mesh.get_surface_count():
			var arrays: Array = instance.mesh.surface_get_arrays(surface)
			var points: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var local_index := 0
			for triangle in source.geometry.near.surfaces[surface].triangles:
				for raw in triangle:
					var expected := Vector3(raw[0],raw[1],raw[2])
					if local_index >= points.size() or offset >= faces.size(): local_exact=false;body_local_exact=false;world_approx=false;continue
					var point: Vector3 = points[local_index]
					local_exact = local_exact and point == expected
					var visual: Vector3 = instance.global_transform * point
					var physical: Vector3 = body.global_transform * faces[offset]
					body_local_exact = body_local_exact and faces[offset] == body.to_local(visual)
					world_approx = world_approx and visual.is_equal_approx(physical)
					max_world_error = maxf(max_world_error,visual.distance_to(physical))
					local_index += 1; offset += 1
		result.candidate_transform = transform_values(instance.global_transform)
		result.geometry = {"triangles":offset/3,"surfaces":instance.mesh.get_surface_count(),"local_vertices_exact_raw":local_exact,"body_local_vertices_exact":body_local_exact,"world_vertices_equal_approx":world_approx,"max_world_vertex_error_m":max_world_error,"vertex_count_matches":offset==faces.size(),"bounds":encode_value(instance.mesh.get_aabb()),"body_bounds":encode_value(concave.get_debug_mesh().get_aabb()),"backface_collision":concave.backface_collision}
		result.material_identity_reused = frontage_result.materials == existing
		result.surface_material_ids = []
		for index in instance.mesh.get_surface_count(): result.surface_material_ids.append(material_id(instance.get_active_material(index)))
		result.new_materials = frontage_result.new_materials
		result.new_textures = frontage_result.new_textures
		result.new_lights = frontage_result.new_lights
	return result

func snapshot(id: String) -> Dictionary:
	var state := super.snapshot(id)
	var scene: Node3D = current_scene
	resource_rows.clear(); material_ids.clear()
	state.product_camera = camera_state(scene.player.camera)
	state.camera_properties = stored_properties(root.get_camera_3d())
	state.hero_skeleton = final_pose.duplicate(true)
	# Raw counters remain available; comparator excludes ONLY these named absolute counters.
	state.pose_signal_counters = {}
	state.hero_skeleton.erase("completed_post_draws")
	for name in ["process_frame","physics_frame","drawn_frame"]:
		state.pose_signal_counters[name] = state.hero_skeleton.get(name,-1)
		state.hero_skeleton.erase(name)
	state.pose_correlation = {"source":"RamaMotion.modification_processed","preflight_no_draw":preflight,"process_age":Engine.get_process_frames()-int(final_pose.get("process_frame",-1)),"physics_age":Engine.get_physics_frames()-int(final_pose.get("physics_frame",-1)),"draw_age":Engine.get_frames_drawn()-int(final_pose.get("drawn_frame",-1)),"post_draw_age":completed_post_draws-int(final_pose.get("completed_post_draws",-1))}
	state.hero_global_transform = encode_value(scene.player.global_transform)
	state.hero_velocity = encode_value(scene.player.velocity)
	state.visual_transform = encode_value(scene.player.visual.global_transform)
	state.army_units = []
	for unit in scene.army.units:
		var joints := {}
		var names: Array = unit.joints.keys(); names.sort()
		for name in names:
			if unit.joints[name] is Node3D: joints[name] = transform_values(unit.joints[name].transform)
		state.army_units.append({"id":unit.unit_id,"team":unit.team,"role":unit.role,"health":unit.health,"alive":unit.alive,"state":unit.state,"transform":transform_values(unit.global_transform),"joints":joints})
	state.authority_report = encode_value(scene.army.report())
	state.nav_manifest_sha256 = JSON.stringify(scene.manifest).sha256_text()
	var environment: Environment = scene.world_environment.environment
	state.environment = stored_properties(environment)
	state.ao = {}
	for property in environment.get_property_list():
		if String(property.name).begins_with("ssao_"): state.ao[String(property.name)] = encode_value(environment.get(property.name))
	state.light_diagnostics = encode_value(scene.lighting.diagnostics())
	state.lights = []; state.meshes = []
	collect_scene_controls(scene,state.lights,state.meshes)
	state.frontage = frontage_state(scene)
	state.materials = resource_rows.duplicate(true)
	state.collision_objects = []
	collision_inventory(scene.world,state.collision_objects)
	var motion := {}
	for name in ["phase","locomotion_age","transition_age","action_elapsed","action","action_stage","locomotion","grounded","traversal"]: motion[name] = encode_value(scene.player.rama_motion.get(name))
	state.clocks = {"elapsed":scene.elapsed,"footstep_clock":scene.footstep_clock,"feedback_clock":scene.feedback_clock,"motion":motion,"kit":encode_value(scene.rama_runtime.kit.report()),"traversal":encode_value(scene.player.traversal.report())}
	state.render_settings = {}
	for name in ["rendering/anti_aliasing/quality/msaa_3d","rendering/anti_aliasing/quality/use_taa","rendering/textures/default_filters/anisotropic_filtering_level","rendering/textures/default_filters/use_nearest_mipmap_filter"]: state.render_settings[name] = encode_value(ProjectSettings.get_setting(name))
	state.viewport_msaa_3d = root.msaa_3d
	state.viewport_use_taa = root.use_taa
	state.serialization_errors = serialization_errors.duplicate()
	return state

func take_frontage(id: String) -> bool:
	if not take(id): return false
	var item: Dictionary = shots.back()
	check(id+" full164final-modifier poses and finite supported controls",item.hero_skeleton.get("bone_names",[]).size()==164 and item.hero_skeleton.get("bone_global_poses",[]).size()==164 and item.hero_skeleton.get("signals",0)>0 and item.serialization_errors.is_empty())
	var mods: Array = item.hero_skeleton.get("active_modifiers",[])
	check(id+" observed modifier is last active skeleton modifier",not mods.is_empty() and mods.back()==item.hero_skeleton.get("observer_modifier",""))
	check(id+" final-modifier sample belongs to captured frame",item.pose_correlation.process_age==0 and item.pose_correlation.physics_age==0 and (item.pose_correlation.post_draw_age==0 if preflight else item.pose_correlation.post_draw_age==1))
	var f: Dictionary = item.frontage
	var common := f.active_shape_count==1 and f.shape_owner_count==1 and f.body_metadata.authority_id==Frontage.BODY and f.body_metadata.dimensions==[18.0,15.0,18.0] and f.body_metadata.position_base==[20.0,0.0,-28.0]
	if branch=="baseline":
		check(id+" declared original visible/sole18x15x18box",common and f.target_visible and not f.replacement_present and f.shape_class=="BoxShape3D" and f.box_size==[18.0,15.0,18.0])
	else:
		check(id+" declared original hidden/sole detailed closed shape",common and not f.target_visible and f.replacement_present and f.shape_class=="ConcavePolygonShape3D")
		check(id+" exact local geometry and reviewed world float transform",f.geometry.local_vertices_exact_raw and f.geometry.body_local_vertices_exact and f.geometry.world_vertices_equal_approx and f.geometry.vertex_count_matches and f.geometry.triangles==2816 and f.geometry.surfaces==3 and f.geometry.backface_collision)
		check(id+" existing effective material identities only",f.material_identity_reused and f.surface_material_ids==f.material_ids and f.new_materials==0 and f.new_textures==0 and f.new_lights==0)
	if checks.any(func(row): return not row.passed): finish("Frontage shot contract failed");return false
	return true

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg=="--preflight": preflight=true
		elif arg=="--case=scene-anchors": pass
		else: finish("Unknown argument: "+arg);return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"): finish("X11 Forward+ required");return
	var selection: Variant = JSON.parse_string(FileAccess.get_file_as_string(SELECTION))
	if not selection is Dictionary or selection.keys().size()!=1 or selection.get("branch","") not in ["baseline","candidate"]: finish("Explicit one-field branch JSON required");return
	branch=selection.branch
	source_start=hashes()
	if source_start.is_empty(): finish("Immutable source manifest required");return
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
	if not preflight: root.show()
	checkpoint("actual_boot_main_scene")
	if change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))!=OK: finish("Main scene failed");return
	if not await wait_scene("res://scenes/courtyard.tscn"): finish("Boot did not reach title");return
	await frames(SETTLE_FRAMES)
	var court: Node3D = current_scene
	for scale in SCALES: root.content_scale_factor=scale;await frames(SETTLE_FRAMES)
	root.content_scale_factor=1.0;await frames(SETTLE_FRAMES)
	court.main_panel.primary_button.grab_focus();await key(KEY_ENTER)
	if not await wait_scene("res://scenes/confluence_world.tscn"): finish("Primary action did not reach world");return
	await frames(SETTLE_FRAMES)
	var scene: Node3D = current_scene
	if not scene.world_ready or not scene.player.model_ready: finish("World/hero missing");return
	var body: StaticBody3D = scene.world.get_node(Frontage.BODY)
	var old_identity := body.get_instance_id()
	var original_manifest := JSON.stringify(scene.manifest).sha256_text()
	scene.player.rama_motion.modification_processed.connect(observe_final_pose)
	if branch=="candidate":
		frontage_result=Frontage.configure(scene.world,"near")
		if not frontage_result.get("ok",false): finish("Candidate admission rejected: "+str(frontage_result));return
	await frames(SETTLE_FRAMES)
	check("same native body identity/nav retained after optional configure",body.get_instance_id()==old_identity and JSON.stringify(scene.manifest).sha256_text()==original_manifest)
	check("first view uses current live product camera",root.get_camera_3d()==scene.player.camera and scene.player.active and not scene.overview and not paused)
	if not take_frontage("00-world-product"): return
	review_camera=Camera3D.new();review_camera.name="ReviewFrontageContactCamera"
	review_camera.fov=58.0;review_camera.near=.08;review_camera.far=380.0
	scene.world.add_child(review_camera)
	review_camera.global_position=Vector3(16,1.65,-44)
	review_camera.look_at(Vector3(20,1.9,-36.35),Vector3.UP)
	review_camera.make_current();await frames(SETTLE_FRAMES)
	check("declared supplemental player-height camera with live world",root.get_camera_3d()==review_camera and scene.player.active and not scene.overview and not paused)
	if not take_frontage("01-frontage-contact"): return
	scene.player.camera.make_current()
	# Existing overview action owns suspension, camera framing and return.
	await key(KEY_F1);await frames(SETTLE_FRAMES)
	check("genuine overview ownership",scene.overview and not paused and not scene.player.active and scene.player.presentation_suspended and scene.rama_runtime.suspended and root.get_camera_3d()==scene.review_camera and scene.atlas_guide.is_visible_in_tree())
	var held_army: float = scene.army.elapsed
	var held_kit: float = scene.rama_runtime.kit.elapsed
	var held_position: Vector3 = scene.player.global_position
	var product_camera_before := camera_state(scene.player.camera)
	await frames(SETTLE_FRAMES)
	check("genuine overview holds army/kit/hero position",scene.army.elapsed==held_army and scene.rama_runtime.kit.elapsed==held_kit and scene.player.global_position==held_position)
	if not take_frontage("02-overview-context"): return
	await key(KEY_F1)
	check("native overview return restores live owner",not scene.overview and not paused and scene.player.active and not scene.player.presentation_suspended and not scene.rama_runtime.suspended and root.get_camera_3d()==scene.player.camera and not scene.atlas_guide.is_visible_in_tree())
	# Parent/position/projection exact; only SpringArm basis uses Godot's known float comparison.
	var product_camera_after := camera_state(scene.player.camera)
	var before_basis := Basis(Vector3(product_camera_before.transform[0][0],product_camera_before.transform[0][1],product_camera_before.transform[0][2]),Vector3(product_camera_before.transform[1][0],product_camera_before.transform[1][1],product_camera_before.transform[1][2]),Vector3(product_camera_before.transform[2][0],product_camera_before.transform[2][1],product_camera_before.transform[2][2]))
	route_checks={"before":product_camera_before,"after":product_camera_after,"hero_position_held":scene.player.global_position==held_position,"army_resumed":scene.army.elapsed>held_army,"kit_resumed":scene.rama_runtime.kit.elapsed>held_kit}
	check("native return preserves camera origin/projection and known float basis",product_camera_before.path==product_camera_after.path and product_camera_before.transform[3]==product_camera_after.transform[3] and before_basis.is_equal_approx(scene.player.camera.global_basis) and product_camera_before.fov==product_camera_after.fov and product_camera_before.near==product_camera_after.near and product_camera_before.far==product_camera_after.far)
	check("native return resumes held world clocks",route_checks.army_resumed and route_checks.kit_resumed and route_checks.hero_position_held)
	check("live contact view advances world clocks",shots[1].army_elapsed>shots[0].army_elapsed and shots[1].kit_elapsed>shots[0].kit_elapsed)
	finish("")
func finish(failure:String) -> void:
	if done:return
	done=true
	var after:=hashes() if not source_start.is_empty() else {}
	check("three declared matched views",shots.size()==3)
	check("source unchanged",not source_start.is_empty() and source_start==after)
	var passed:=failure.is_empty() and checks.all(func(item):return item.passed)
	var report:={"schema":1,"case":"lane-frontage-review","outer_transport_alias":"scene-anchors","complete":passed,"failure":failure,"preflight":preflight,"shots":shots,"checks":checks,"checkpoints":checkpoints,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"route_checks":route_checks,"branch":branch,"selection_sha256":FileAccess.get_sha256(SELECTION),"scope":"Three source-bound product/contact/native-overview views. Only named block2 visible mesh and existing sole local3D collider detail are declared differences; no art/performance/authority acceptance."}
	frontage_result.clear()
	paused=false
	if is_instance_valid(current_scene):current_scene.queue_free()
	for unused in 8:await process_frame
	# Dummy audio fades/releases on its real mixer thread, not fixed-fps scene time.
	# Observe two clock resets without assuming simulated frames span mixer ticks.
	var started:=Time.get_ticks_usec()
	var previous:=AudioServer.get_time_since_last_mix()
	var observed:=0
	var samples:Array[Dictionary]=[]
	while observed<2 and Time.get_ticks_usec()-started<250000:
		OS.delay_msec(1)
		var now:=AudioServer.get_time_since_last_mix()
		if now+.0002<previous: observed+=1
		samples.append({"wall_usec":Time.get_ticks_usec()-started,"since_mix_s":now,"ticks":observed})
		previous=now
	var wait_usec:=Time.get_ticks_usec()-started
	# AudioServer's main-thread list cleanup follows the mix-thread deletion.
	for unused in 8:await process_frame
	check("two real mixer ticks observed within250ms cleanup budget",observed==2 and wait_usec<=250000)
	report.audio_cleanup={"scope":"Capture shutdown only, after all three shots and scene free; no runtime audio change.","observed_mixer_ticks":observed,"wait_usec":wait_usec,"budget_usec":250000,"samples":samples,"main_cleanup_frames":8}
	report.complete=failure.is_empty() and checks.all(func(item):return item.passed)
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):write_json(output.path_join("preflight.json" if preflight else "capture.json"),report)
	print("LANE_FRONTAGE_COMPLETE ",report.complete," ",failure)
	quit(0 if report.complete else 1)
