from pathlib import Path
repo=Path('/workspace/ANDOLAN/games/yuga-native')
roof=(repo/'art/world-finish/roof-loggia-render-r2/capture_roof.gd').read_text()
ao=(repo/'art/world-finish/title-floor-ssao-plan-r1/capture_floor_ao.UNRUN.gd').read_text()
serial=ao[ao.index('func encode_value'):ao.index('func diagnostic_controls')]
serial=serial.replace('TYPE_OBJECT:\n','TYPE_OBJECT:\n\t\t\tif value == null: return null\n')
# Keep accepted serialization, add explicit mesh geometry dimensions/counts.
serial=serial.replace('"mesh_path":node.mesh.resource_path,','"mesh_path":node.mesh.resource_path,"aabb":encode_value(node.mesh.get_aabb()),"surface_vertices":surface_vertex_counts(node.mesh),')
collision=roof[roof.index('func collision_inventory'):roof.index('func snapshot')]
collision=collision.replace('"shapes":[]','"metadata":metadata_values(node),"shapes":[]')
collision=collision.replace('"class":shape.get_class(),','"path":String(child.get_path()),"class":shape.get_class(),')
header='''extends "res://tools/graphics-six/capture_compact_screens.gd"
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

func transform_values(value: Transform3D) -> Array:
\treturn [vector(value.basis.x),vector(value.basis.y),vector(value.basis.z),vector(value.origin)]

func surface_vertex_counts(mesh: Mesh) -> Array:
\tvar result: Array = []
\tfor index in mesh.get_surface_count(): result.append(mesh.surface_get_array_len(index))
\treturn result

func metadata_values(node: Node) -> Dictionary:
\tvar result: Dictionary = {}
\tvar names: Array = node.get_meta_list(); names.sort()
\tfor name in names: result[String(name)] = encode_value(node.get_meta(name))
\treturn result

'''
extra='''func existing_materials(old: Node3D) -> Array:
\tvar result: Array = []
\tvar meshes: Array = old.find_children("*","MeshInstance3D",true,false)
\tif old is MeshInstance3D: meshes.push_front(old)
\tfor name in Frontage.MATERIAL_NAMES:
\t\tvar found: Material
\t\tfor node in meshes:
\t\t\tif node.mesh == null: continue
\t\t\tfor index in node.mesh.get_surface_count():
\t\t\t\tvar imported: Material = node.mesh.surface_get_material(index)
\t\t\t\tif imported != null and imported.resource_name == name: found = node.get_active_material(index)
\t\tresult.append(found)
\treturn result

func frontage_state(scene: Node3D) -> Dictionary:
\tvar old: Node3D = scene.world.get_node(Frontage.TARGET)
\tvar body: StaticBody3D = scene.world.get_node(Frontage.BODY)
\tvar holders: Array = []
\tfor child in body.get_children():
\t\tif child is CollisionShape3D and not child.disabled: holders.append(child)
\tvar existing: Array = existing_materials(old)
\tvar result := {"branch":branch,"target_path":String(old.get_path()),"target_transform":transform_values(old.global_transform),"target_visible":old.visible,"body_path":String(body.get_path()),"body_transform":transform_values(body.global_transform),"body_metadata":metadata_values(body),"shape_owner_count":body.get_shape_owners().size(),"active_shape_count":holders.size(),"material_ids":existing.map(func(item): return material_id(item)),"data_sha256":FileAccess.get_sha256(Frontage.DATA),"replacement_present":scene.world.get_node_or_null(Frontage.ROOT) != null}
\tif holders.size() != 1: return result
\tvar shape: Shape3D = holders[0].shape
\tresult.shape_class = shape.get_class()
\tif shape is BoxShape3D: result.box_size = vector(shape.size)
\tif branch == "candidate" and frontage_result.get("ok",false):
\t\tvar instance: MeshInstance3D = frontage_result.mesh
\t\tvar faces: PackedVector3Array = shape.get_faces()
\t\tvar source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Frontage.DATA))
\t\tvar offset := 0
\t\tvar local_exact := true
\t\tvar body_local_exact := true
\t\tvar world_approx := true
\t\tvar max_world_error := 0.0
\t\tfor surface in instance.mesh.get_surface_count():
\t\t\tvar arrays: Array = instance.mesh.surface_get_arrays(surface)
\t\t\tvar points: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
\t\t\tvar local_index := 0
\t\t\tfor triangle in source.geometry.near.surfaces[surface].triangles:
\t\t\t\tfor raw in triangle:
\t\t\t\t\tvar expected := Vector3(raw[0],raw[1],raw[2])
\t\t\t\t\tif local_index >= points.size() or offset >= faces.size(): local_exact=false;body_local_exact=false;world_approx=false;continue
\t\t\t\t\tvar point: Vector3 = points[local_index]
\t\t\t\t\tlocal_exact = local_exact and point == expected
\t\t\t\t\tvar visual: Vector3 = instance.global_transform * point
\t\t\t\t\tvar physical: Vector3 = body.global_transform * faces[offset]
\t\t\t\t\tbody_local_exact = body_local_exact and faces[offset] == body.to_local(visual)
\t\t\t\t\tworld_approx = world_approx and visual.is_equal_approx(physical)
\t\t\t\t\tmax_world_error = maxf(max_world_error,visual.distance_to(physical))
\t\t\t\t\tlocal_index += 1; offset += 1
\t\tresult.geometry = {"triangles":offset/3,"surfaces":instance.mesh.get_surface_count(),"local_vertices_exact_raw":local_exact,"body_local_vertices_exact":body_local_exact,"world_vertices_equal_approx":world_approx,"max_world_vertex_error_m":max_world_error,"vertex_count_matches":offset==faces.size(),"bounds":encode_value(instance.mesh.get_aabb()),"body_bounds":encode_value(shape.get_debug_mesh().get_aabb()),"backface_collision":shape.backface_collision}
\t\tresult.material_identity_reused = frontage_result.materials == existing
\t\tresult.surface_material_ids = []
\t\tfor index in instance.mesh.get_surface_count(): result.surface_material_ids.append(material_id(instance.get_active_material(index)))
\t\tresult.new_materials = frontage_result.new_materials
\t\tresult.new_textures = frontage_result.new_textures
\t\tresult.new_lights = frontage_result.new_lights
\treturn result

func snapshot(id: String) -> Dictionary:
\tvar state := super.snapshot(id)
\tvar scene: Node3D = current_scene
\tresource_rows.clear(); material_ids.clear()
\tstate.product_camera = camera_state(scene.player.camera)
\tstate.camera_properties = stored_properties(root.get_camera_3d())
\tstate.hero_skeleton = {"bone_names":[],"bone_global_poses":[]}
\tvar rig: Skeleton3D = scene.player.rama_motion.rig
\tfor index in rig.get_bone_count():
\t\tstate.hero_skeleton.bone_names.append(String(rig.get_bone_name(index)))
\t\tstate.hero_skeleton.bone_global_poses.append(transform_values(rig.get_bone_global_pose(index)))
\tstate.hero_global_transform = encode_value(scene.player.global_transform)
\tstate.hero_velocity = encode_value(scene.player.velocity)
\tstate.visual_transform = encode_value(scene.player.visual.global_transform)
\tstate.army_units = []
\tfor unit in scene.army.units:
\t\tvar joints := {}
\t\tvar names: Array = unit.joints.keys(); names.sort()
\t\tfor name in names:
\t\t\tif unit.joints[name] is Node3D: joints[name] = transform_values(unit.joints[name].transform)
\t\tstate.army_units.append({"id":unit.unit_id,"team":unit.team,"role":unit.role,"health":unit.health,"alive":unit.alive,"state":unit.state,"transform":transform_values(unit.global_transform),"joints":joints})
\tstate.authority_report = encode_value(scene.army.report())
\tstate.nav_manifest_sha256 = JSON.stringify(scene.manifest).sha256_text()
\tvar environment: Environment = scene.world_environment.environment
\tstate.environment = stored_properties(environment)
\tstate.ao = {}
\tfor property in environment.get_property_list():
\t\tif String(property.name).begins_with("ssao_"): state.ao[String(property.name)] = encode_value(environment.get(property.name))
\tstate.light_diagnostics = encode_value(scene.lighting.diagnostics())
\tstate.lights = []; state.meshes = []
\tcollect_scene_controls(scene,state.lights,state.meshes)
\tstate.frontage = frontage_state(scene)
\tstate.materials = resource_rows.duplicate(true)
\tstate.collision_objects = []
\tcollision_inventory(scene.world,state.collision_objects)
\tvar motion := {}
\tfor name in ["phase","locomotion_age","transition_age","action_elapsed","action","action_stage","locomotion","grounded","traversal"]: motion[name] = encode_value(scene.player.rama_motion.get(name))
\tstate.clocks = {"elapsed":scene.elapsed,"footstep_clock":scene.footstep_clock,"feedback_clock":scene.feedback_clock,"motion":motion,"kit":encode_value(scene.rama_runtime.kit.report()),"traversal":encode_value(scene.player.traversal.report())}
\tstate.render_settings = {}
\tfor name in ["rendering/anti_aliasing/quality/msaa_3d","rendering/anti_aliasing/quality/use_taa","rendering/textures/default_filters/anisotropic_filtering_level","rendering/textures/default_filters/use_nearest_mipmap_filter"]: state.render_settings[name] = encode_value(ProjectSettings.get_setting(name))
\tstate.viewport_msaa_3d = root.msaa_3d
\tstate.viewport_use_taa = root.use_taa
\tstate.serialization_errors = serialization_errors.duplicate()
\treturn state

func take_frontage(id: String) -> bool:
\tif not take(id): return false
\tvar item: Dictionary = shots.back()
\tcheck(id+" full164poses and finite supported controls",item.hero_skeleton.bone_names.size()==164 and item.hero_skeleton.bone_global_poses.size()==164 and item.serialization_errors.is_empty())
\tvar f: Dictionary = item.frontage
\tvar common := f.active_shape_count==1 and f.shape_owner_count==1 and f.body_metadata.authority_id==Frontage.BODY and f.body_metadata.dimensions==[18.0,15.0,18.0] and f.body_metadata.position_base==[20.0,0.0,-28.0]
\tif branch=="baseline":
\t\tcheck(id+" declared original visible/sole18x15x18box",common and f.target_visible and not f.replacement_present and f.shape_class=="BoxShape3D" and f.box_size==[18.0,15.0,18.0])
\telse:
\t\tcheck(id+" declared original hidden/sole detailed closed shape",common and not f.target_visible and f.replacement_present and f.shape_class=="ConcavePolygonShape3D")
\t\tcheck(id+" exact local geometry and reviewed world float transform",f.geometry.local_vertices_exact_raw and f.geometry.body_local_vertices_exact and f.geometry.world_vertices_equal_approx and f.geometry.vertex_count_matches and f.geometry.triangles==2816 and f.geometry.surfaces==3 and f.geometry.backface_collision)
\t\tcheck(id+" existing effective material identities only",f.material_identity_reused and f.surface_material_ids==f.material_ids and f.new_materials==0 and f.new_textures==0 and f.new_lights==0)
\tif checks.any(func(row): return not row.passed): finish("Frontage shot contract failed");return false
\treturn true

func run() -> void:
\tfor arg in OS.get_cmdline_user_args():
\t\tif arg.begins_with("--output="): output=arg.trim_prefix("--output=")
\t\telif arg=="--preflight": preflight=true
\t\telif arg=="--case=scene-anchors": pass
\t\telse: finish("Unknown argument: "+arg);return
\tif not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required");return
\tDirAccess.make_dir_recursive_absolute(output)
\tif not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"): finish("X11 Forward+ required");return
\tvar selection: Variant = JSON.parse_string(FileAccess.get_file_as_string(SELECTION))
\tif not selection is Dictionary or selection.keys().size()!=1 or selection.get("branch","") not in ["baseline","candidate"]: finish("Explicit one-field branch JSON required");return
\tbranch=selection.branch
\tsource_start=hashes()
\tif source_start.is_empty(): finish("Immutable source manifest required");return
\troot.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
\tif not preflight: root.show()
\tcheckpoint("actual_boot_main_scene")
\tif change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))!=OK: finish("Main scene failed");return
\tif not await wait_scene("res://scenes/courtyard.tscn"): finish("Boot did not reach title");return
\tawait frames(SETTLE_FRAMES)
\tvar court: Node3D = current_scene
\tfor scale in SCALES: root.content_scale_factor=scale;await frames(SETTLE_FRAMES)
\troot.content_scale_factor=1.0;await frames(SETTLE_FRAMES)
\tcourt.main_panel.primary_button.grab_focus();await key(KEY_ENTER)
\tif not await wait_scene("res://scenes/confluence_world.tscn"): finish("Primary action did not reach world");return
\tawait frames(SETTLE_FRAMES)
\tvar scene: Node3D = current_scene
\tif not scene.world_ready or not scene.player.model_ready: finish("World/hero missing");return
\tvar body: StaticBody3D = scene.world.get_node(Frontage.BODY)
\tvar old_identity := body.get_instance_id()
\tvar original_manifest := JSON.stringify(scene.manifest).sha256_text()
\tif branch=="candidate":
\t\tfrontage_result=Frontage.configure(scene.world,"near")
\t\tif not frontage_result.get("ok",false): finish("Candidate admission rejected: "+str(frontage_result));return
\tawait frames(SETTLE_FRAMES)
\tcheck("same native body identity/nav retained after optional configure",body.get_instance_id()==old_identity and JSON.stringify(scene.manifest).sha256_text()==original_manifest)
\tcheck("first view uses current live product camera",root.get_camera_3d()==scene.player.camera and scene.player.active and not scene.overview and not paused)
\tif not take_frontage("00-world-product"): return
\treview_camera=Camera3D.new();review_camera.name="ReviewFrontageContactCamera"
\treview_camera.fov=58.0;review_camera.near=.08;review_camera.far=380.0
\tscene.world.add_child(review_camera)
\treview_camera.global_position=Vector3(16,1.65,-44)
\treview_camera.look_at(Vector3(20,1.9,-36.35),Vector3.UP)
\treview_camera.make_current();await frames(SETTLE_FRAMES)
\tcheck("declared supplemental player-height camera with live world",root.get_camera_3d()==review_camera and scene.player.active and not scene.overview and not paused)
\tif not take_frontage("01-frontage-contact"): return
\tscene.player.camera.make_current()
\t# Existing overview action owns suspension, camera framing and return.
\tawait key(KEY_F1);await frames(SETTLE_FRAMES)
\tcheck("genuine overview ownership",scene.overview and not paused and not scene.player.active and scene.player.presentation_suspended and scene.rama_runtime.suspended and root.get_camera_3d()==scene.review_camera and scene.atlas_guide.is_visible_in_tree())
\tvar held_army: float = scene.army.elapsed
\tvar held_kit: float = scene.rama_runtime.kit.elapsed
\tvar held_position: Vector3 = scene.player.global_position
\tvar product_camera_before := camera_state(scene.player.camera)
\tawait frames(SETTLE_FRAMES)
\tcheck("genuine overview holds army/kit/hero position",scene.army.elapsed==held_army and scene.rama_runtime.kit.elapsed==held_kit and scene.player.global_position==held_position)
\tif not take_frontage("02-overview-context"): return
\tawait key(KEY_F1)
\tcheck("native overview return restores live owner",not scene.overview and not paused and scene.player.active and not scene.player.presentation_suspended and not scene.rama_runtime.suspended and root.get_camera_3d()==scene.player.camera and not scene.atlas_guide.is_visible_in_tree())
\t# Parent/position/projection exact; only SpringArm basis uses Godot's known float comparison.
\tvar product_camera_after := camera_state(scene.player.camera)
\tvar before_basis := Basis(Vector3(product_camera_before.transform[0][0],product_camera_before.transform[0][1],product_camera_before.transform[0][2]),Vector3(product_camera_before.transform[1][0],product_camera_before.transform[1][1],product_camera_before.transform[1][2]),Vector3(product_camera_before.transform[2][0],product_camera_before.transform[2][1],product_camera_before.transform[2][2]))
\troute_checks={"before":product_camera_before,"after":product_camera_after,"hero_position_held":scene.player.global_position==held_position,"army_resumed":scene.army.elapsed>held_army,"kit_resumed":scene.rama_runtime.kit.elapsed>held_kit}
\tcheck("native return preserves camera origin/projection and known float basis",product_camera_before.path==product_camera_after.path and product_camera_before.transform[3]==product_camera_after.transform[3] and before_basis.is_equal_approx(scene.player.camera.global_basis) and product_camera_before.fov==product_camera_after.fov and product_camera_before.near==product_camera_after.near and product_camera_before.far==product_camera_after.far)
\tcheck("native return resumes held world clocks",route_checks.army_resumed and route_checks.kit_resumed and route_checks.hero_position_held)
\tcheck("live contact view advances world clocks",shots[1].army_elapsed>shots[0].army_elapsed and shots[1].kit_elapsed>shots[0].kit_elapsed)
\tfinish("")
'''
finish=roof[roof.index('func finish'):]
finish=finish.replace('two declared matched views','three declared matched views').replace('shots.size()==2','shots.size()==3').replace('"roof-loggia-review"','"lane-frontage-review"')
a=finish.index('"scope":"Two source-bound views:');b=finish.index('"}',a)
finish=finish[:a]+'"route_checks":route_checks,"branch":branch,"selection_sha256":FileAccess.get_sha256(SELECTION),"scope":"Three source-bound product/contact/native-overview views. Only named block2 visible mesh and existing sole local3D collider detail are declared differences; no art/performance/authority acceptance.'+finish[b:]
finish=finish.replace('paused=false\n','frontage_result.clear()\n\tpaused=false\n').replace('after both shots','after all three shots').replace('ROOF_LOGGIA_COMPLETE','LANE_FRONTAGE_COMPLETE')
Path('/workspace/scratch/yuga-frontage-helper-r1/capture_frontage.gd').write_text(header+serial+collision+extra+finish)
