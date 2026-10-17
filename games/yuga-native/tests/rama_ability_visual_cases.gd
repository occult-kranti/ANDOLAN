extends SceneTree
## Real accepted-event presentation checks; these do not approve rendered art.
const Army = preload("res://scripts/lane_army.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
var army
var kit
var fx
var events: Array=[]
var checks: Array=[]
var budgets: Dictionary={}

func _initialize() -> void:call_deferred("run")
func check(label: String, passed: bool, evidence: Dictionary={}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	if not passed:push_error("RAMA ABILITY VISUAL FAILED: "+label)
func fresh() -> void:
	army.reset();events.clear();fx.set_suspended(false)
	fx.set_options({"reduced_effects":false,"reduced_motion":false})
func advance(seconds: float) -> void:
	var remaining:=seconds
	while remaining>1e-8:
		var delta:=minf(.025,remaining)
		army.step_simulation(delta);fx.step(delta);remaining-=delta
func cast(id: String) -> bool:
	return kit.request_ability(id,Vector3.ZERO,Vector3.BACK,Vector3(0,0,4)).accepted
func current() -> Dictionary:return fx._casts.values()[0]
func points(mesh: Mesh) -> PackedVector3Array:
	return mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] if mesh.get_surface_count()>0 else PackedVector3Array()
func geometry_finite(node: Node) -> bool:
	if node is MeshInstance3D and node.mesh:
		for point in points(node.mesh):
			if not point.is_finite() or point.length()>50.0:return false
	for child in node.get_children():
		if not geometry_finite(child):return false
	return true
func front_area(mesh: Mesh) -> float:
	if mesh.get_surface_count()==0:return 0.0
	var arrays:=mesh.surface_get_arrays(0)
	var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
	var area:=0.0
	for index in range(0,indices.size(),3):
		var a: Vector3=vertices[indices[index]]
		var b: Vector3=vertices[indices[index+1]]
		var c: Vector3=vertices[indices[index+2]]
		area+=absf((b-a).cross(c-a).z)*.5
	return area
func run() -> void:
	army=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	check("real_army_configures",army.configure(manifest,null))
	kit=Kit.new();root.add_child(kit)
	fx=Effects.new();root.add_child(fx);fx.set_process(false)
	check("real_kit_configures",kit.configure(army))
	kit.ability_event.connect(func(event):events.append(event.duplicate(true));fx.consume_event(event))
	kit.set_movement_receiver(func(_start,destination,_duration):return {"accepted":true,"destination":destination})
	for id in Effects.IDS:
		fresh();check(id+"_accepted",cast(id));advance(.075 if id=="measured_step" else minf(float(current().timing.windup_s)*.8,.65))
		var state:=current()
		var normal: Dictionary=fx.report()
		budgets[id]={"windup_triangles":normal.triangles,"meshes":normal.meshes}
		check(id+"_finite_and_under4096_triangle_budget",normal.finite and geometry_finite(state.root) and normal.triangles<=4096,normal)
		check(id+"_warning_uses_essential_boundary_material",state.warning.material_override.shader==(Effects.BoundaryShader if id=="guardian_circle" else Effects.RibbonShader) and state.main.shader==Effects.CalligraphyShader)
		var boundary: Mesh=state.warning.mesh
		fx.set_options({"reduced_effects":true})
		check(id+"_reduced_effects_leave_boundary_exact",state.warning.mesh==boundary and state.accent.mesh.get_surface_count()==0)
		fx.set_options({"reduced_effects":false})
		if id in ["kodanda","piercing_dawn","dawn_volley"]:
			var area:=front_area(state.motif.mesh)
			check(id+"_solar_strokes_have_front_facing_area",area>.01,{"projected_local_xy_area":area})
		kit.cancel_active("visual_case_end")
		check(id+"_cancel_removes_every_owned_node",fx.report().active==0 and fx.get_child_count()==0)
	fresh();cast("guardian_circle");advance(.6)
	var ward:=current()
	var radius: float=ward.geometry.radius_m
	var furthest:=0.0
	for node in [ward.motif,ward.accent]:
		for vertex in points(node.mesh):furthest=maxf(furthest,Vector2(vertex.x,vertex.z).length())
	check("lotus_petals_stay_inside_actual_boundary",furthest<radius-.20,{"decorative_radius":furthest,"gameplay_radius":radius})
	var boundary_mesh: Mesh=ward.warning.mesh
	var boundary_material: ShaderMaterial=ward.warning.material_override
	check("essential_boundary_renders_after_ornament",boundary_material.render_priority>ward.main.render_priority and boundary_material.render_priority>ward.detail.render_priority)
	for test_radius in [.05,5.0,6.0]:
		var geometry: Dictionary=ward.geometry.duplicate(true);geometry.radius_m=test_radius
		var width: float=fx._warning_width(geometry)
		var mesh: Mesh=fx._ribbon(fx._warning(geometry),width)
		var minimum_radius:=INF
		var maximum_radius:=0.0
		for vertex in points(mesh):
			var radial:=Vector2(vertex.x,vertex.z).length()
			minimum_radius=minf(minimum_radius,radial);maximum_radius=maxf(maximum_radius,radial)
		check("boundary_stroke_stays_inward_radius_"+str(test_radius),minimum_radius>=test_radius-width-.00001 and maximum_radius<=test_radius+.00001 and maximum_radius>=test_radius-.00001 and width<=test_radius*.20+.00001,{"radius":test_radius,"width":width,"minimum":minimum_radius,"maximum":maximum_radius})
	for reduced_motion in [false,true]:
		for reduced_effects in [false,true]:
			fx.set_options({"reduced_motion":reduced_motion,"reduced_effects":reduced_effects})
			check("essential_boundary_persists_options_%s_%s"%[reduced_motion,reduced_effects],ward.warning.visible and ward.warning.mesh==boundary_mesh and ward.warning.material_override==boundary_material and boundary_material.get_shader_parameter("opacity")==.92)
	fx.set_options({"reduced_motion":false,"reduced_effects":false})
	var boundary_transform: Transform3D=ward.warning.global_transform
	fx.set_suspended(true);fx.step(.3)
	check("boundary_pause_has_no_fade_or_transform_change",ward.warning.visible and ward.warning.mesh==boundary_mesh and ward.warning.global_transform==boundary_transform and boundary_material.get_shader_parameter("opacity")==.92)
	fx.set_suspended(false)
	var full_ward_triangles: int=fx.report().triangles
	fx.set_options({"reduced_effects":true,"reduced_motion":true})
	check("reduced_lotus_reduces_allocated_geometry",fx.report().triangles<full_ward_triangles and ward.warning.visible,{"full":full_ward_triangles,"reduced":fx.report().triangles})
	var stationary_a: Dictionary=fx._shapes(ward,1.0,.1)
	ward.age+=.12
	check("reduced_lotus_has_no_idle_breathing",stationary_a==fx._shapes(ward,1.0,.1))
	advance(4.45)
	check("essential_boundary_retires_at_authoritative_expiry",not ward.warning.visible and ward.authority_age>=5.05 and ward.warning.mesh==boundary_mesh)
	fresh();cast("measured_step");advance(.225)
	var step_state:=current()
	var normal_echo_vertices:=points(step_state.accent.mesh).size()
	fx.set_options({"reduced_motion":true})
	check("reduced_motion_omits_stationary_step_echoes",points(step_state.accent.mesh).size()<normal_echo_vertices and points(step_state.motif.mesh).size()>0,{"full_accent_vertices":normal_echo_vertices,"reduced_accent_vertices":points(step_state.accent.mesh).size()})
	fresh();cast("dawn_volley");advance(.95)
	check("volley_first_projectile_only_at_release",fx.report().live_arrows==1 and events.filter(func(event):return event.kind=="release").size()==1)
	advance(.1);check("volley_second_projectile_uses_accepted_delay",fx.report().live_arrows==2)
	advance(.1);check("volley_third_projectile_uses_accepted_delay",fx.report().live_arrows==3)
	var volley:=current()
	fx.set_options({"reduced_effects":true})
	check("reduced_volley_keeps_shaft_and_omits_wake_allocation",volley.arrows.all(func(arrow):return arrow.root.visible and arrow.shaft.mesh.get_surface_count()==1 and arrow.feather.mesh.get_surface_count()==0))
	fresh()
	fx._impact(Vector3(1,2,3),Color("e8c373"),true,Vector3.RIGHT)
	var impact: Dictionary=fx._impacts[0]
	check("contact_ornament_faces_incoming_direction",impact.root.global_basis.z.normalized().is_equal_approx(Vector3.RIGHT) and impact.root.global_position==Vector3(1,2,3))
	check("impact_under312_triangle_budget",fx.report().impact_triangles<=312 and fx.report().impact_triangles>80,fx.report())
	fx.step(.1)
	var frozen_age: float=impact.age
	var frozen_phase: float=impact.material.get_shader_parameter("phase")
	var frozen_transform: Transform3D=impact.root.global_transform
	fx.set_suspended(true);fx.step(.2)
	check("suspension_freezes_impact_phase_transform_and_age",impact.age==frozen_age and impact.material.get_shader_parameter("phase")==frozen_phase and impact.root.global_transform==frozen_transform)
	fx.set_suspended(false)
	fx.set_options({"reduced_effects":true,"reduced_motion":true})
	check("live_option_change_rebuilds_simple_contact",fx.report().impact_triangles==80 and impact.material.get_shader_parameter("reduced_motion")==true and impact.root.scale.is_equal_approx(Vector3.ONE*.65))
	var reduced_mesh: Mesh=impact.root.get_child(0).mesh
	fx.set_options({"reduced_motion":false,"reduced_effects":true})
	check("motion_only_toggle_reuses_impact_geometry",impact.root.get_child(0).mesh==reduced_mesh and impact.material.get_shader_parameter("reduced_motion")==false)
	fx.step(.43)
	check("expired_impact_is_hidden_and_pooled",fx.report().impacts==0 and fx.report().pooled_impacts==1 and not impact.root.visible)
	fx.set_options({"reduced_effects":false})
	fx._impact(Vector3(-2,1,4),Color("77b8df"),false,Vector3.BACK)
	var recycled: Dictionary=fx._impacts[0]
	check("pooled_impact_resets_age_hit_tint_orientation",recycled.root==impact.root and recycled.age==0.0 and not recycled.hit and recycled.material.get_shader_parameter("tint")==Color("77b8df") and recycled.root.global_basis.z.normalized().is_equal_approx(Vector3.BACK))
	fx.reset()
	for index in range(200):fx._impact(Vector3(index%8,1,index%6),Color("e8c373"),true)
	check("contact_saturation_has_eighteen_nodes_and_5616_triangles",fx.report().allocated_impacts==18 and fx.get_child_count()==18 and fx.report().impact_triangles<=5616 and geometry_finite(fx),fx.report())
	fx.reset();check("reset_frees_all_cast_and_pool_nodes",fx.get_child_count()==0 and fx.report().allocated_impacts==0)
	fresh();cast("guardian_circle")
	var template: Dictionary=events[0].duplicate(true)
	fx.reset()
	var generation: int=template.generation+1
	for index in range(12):
		var event:=template.duplicate(true);event.generation=generation;event.cast_id=index+1;event.event_seq=index+1
		check("saturated_cast_accept_"+str(index),fx.consume_event(event))
	var overflow:=template.duplicate(true);overflow.generation=generation;overflow.cast_id=13;overflow.event_seq=13
	check("thirteenth_cast_refused_without_nodes",not fx.consume_event(overflow) and fx.report().active==12 and fx.get_child_count()==12)
	check("twelve_wards_under49152_triangle_budget",fx.report().triangles<=49152 and geometry_finite(fx),fx.report())
	fx.reset()
	check("saturation_reset_clears_every_owned_node",fx.get_child_count()==0 and fx.report().total_triangles==0)
	var sources: Dictionary={}
	for path in ["res://scripts/rama_ability_effects.gd","res://scripts/rama_ability_kit.gd","res://shaders/rama_ability_calligraphy.gdshader","res://shaders/rama_ability_boundary.gdshader","res://shaders/rama_ribbon.gdshader",get_script().resource_path]:sources[path]=FileAccess.get_sha256(path)
	var passed:=checks.all(func(item):return item.passed)
	var report:={"schema":1,"suite":"rama_ability_visual_cases","passed":passed,"checks":checks,"source_sha256":sources,"sample_budgets":budgets,"scope":"Actual offline accepted kit events, geometry and resource lifecycle. Headless assertions do not establish rendered beauty, frame rate, AAA quality or online authority."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path:=argument.trim_prefix("--report=");DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("Rama ability visual checks: %d/%d"%[checks.filter(func(item):return item.passed).size(),checks.size()])
	kit.free();fx.free();army.free();quit(0 if passed else 1)
