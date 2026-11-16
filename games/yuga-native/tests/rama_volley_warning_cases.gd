extends SceneTree
## Accepted-event warning lifetime, geometry and accessibility counterexamples.
## Headless checks do not certify rendered clarity or human combat feel.
const Army = preload("res://scripts/lane_army.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
var army
var kit
var fx
var events: Array=[]
var checks: Array=[]

func _initialize() -> void:call_deferred("run")
func check(label: String, passed: bool, evidence: Dictionary={}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	if not passed:push_error("RAMA VOLLEY WARNING: "+label)
func advance(seconds: float) -> void:
	var remaining:=seconds
	while remaining>1e-8:
		var delta:=minf(.025,remaining)
		army.step_simulation(delta);fx.step(delta);remaining-=delta
func current() -> Dictionary:return fx._casts.values()[0]
func warning_vertices(cast: Dictionary) -> PackedVector3Array:
	return cast.warning.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] if cast.warning.mesh.get_surface_count()>0 else PackedVector3Array()
func cast_ability(id: String) -> bool:
	army.reset();fx.set_suspended(false);events.clear()
	fx.set_options({"reduced_effects":false,"reduced_motion":false})
	return kit.request_ability(id,Vector3.ZERO,Vector3.BACK,Vector3(0,0,4)).accepted
func run() -> void:
	army=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	check("actual_army_configures",army.configure(JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json")),null))
	kit=Kit.new();root.add_child(kit);fx=Effects.new();root.add_child(fx);fx.set_process(false)
	check("actual_kit_configures",kit.configure(army))
	kit.ability_event.connect(func(event):events.append(event.duplicate(true));fx.consume_event(event))
	check("volley_accepted",cast_ability("dawn_volley"))
	var state:=current()
	check("three_complete_lanes_visible_at_acceptance",state.warning.visible and warning_vertices(state).size()==24 and fx.report().live_arrows==0)
	var initial_mesh: Mesh=state.warning.mesh
	var initial_readiness: float=state.warning_material.get_shader_parameter("readiness")
	fx.step(.5)
	check("presentation_without_authority_cannot_advance_warning",state.warning.mesh==initial_mesh and state.warning_material.get_shader_parameter("readiness")==initial_readiness and fx.report().live_arrows==0)
	advance(.95)
	check("first_authority_release_keeps_two_pending_lanes",state.released and state.warning.visible and warning_vertices(state).size()==16 and state.launched_arrows==1,{"authority_age":state.authority_age,"release_age":state.release_age_s})
	var first_mesh: Mesh=state.warning.mesh
	fx.step(.5)
	check("interpolation_cannot_retire_the_next_lane",state.warning.mesh==first_mesh and warning_vertices(state).size()==16 and state.launched_arrows==1)
	fx.set_suspended(true)
	var suspended_age: float=state.age
	fx.step(.2)
	check("suspension_freezes_pending_lanes",state.age==suspended_age and state.warning.mesh==first_mesh and state.warning.visible)
	fx.set_suspended(false)
	for reduced_motion in [false,true]:
		for reduced_effects in [false,true]:
			fx.set_options({"reduced_motion":reduced_motion,"reduced_effects":reduced_effects})
			check("two_pending_lanes_survive_options_%s_%s"%[reduced_motion,reduced_effects],state.warning.mesh==first_mesh and state.warning.visible and warning_vertices(state).size()==16)
	advance(.1)
	check("second_authority_release_keeps_final_pending_lane",state.warning.visible and warning_vertices(state).size()==8 and state.launched_arrows==2,{"authority_age":state.authority_age})
	advance(.1)
	check("third_authority_release_retires_final_warning",not state.warning.visible and warning_vertices(state).is_empty() and state.launched_arrows==3,{"authority_age":state.authority_age})
	var older: Dictionary={}
	for event in events:
		if event.kind=="release":older=event.duplicate(true);break
	check("stale_release_cannot_restore_retired_lanes",not fx.consume_event(older) and not state.warning.visible and warning_vertices(state).is_empty())
	kit.cancel_active("warning_cleanup")
	check("cancel_removes_owned_warning",fx.report().active==0)
	cast_ability("dawn_volley");advance(.95)
	kit.cancel_active("interrupted_between_pulses")
	check("between_pulse_cancellation_removes_pending_lanes",fx.report().active==0 and fx.get_child_count()==0)
	cast_ability("dawn_volley");advance(.95)
	army.reset()
	check("reset_clears_pending_lanes",fx.report().active==0 and fx.get_child_count()==0)
	for id in ["piercing_dawn","dawn_volley"]:
		cast_ability(id);state=current()
		var vertices:=warning_vertices(state)
		var exact:=true
		for index in state.geometry.projectiles.size():
			var direction: Vector3=state.geometry.projectiles[index].forward
			var right:=Vector3(direction.z,0,-direction.x)
			var extent:=0.0
			for vertex in vertices.slice(index*8,index*8+8):
				var lateral:=absf(vertex.dot(right))
				extent=maxf(extent,lateral)
				exact=exact and lateral<=float(state.geometry.radius_m)+.00001 and vertex.dot(direction)>=-.00001 and vertex.dot(direction)<=float(state.geometry.range_m)+.00001
			exact=exact and absf(extent-float(state.geometry.radius_m))<.00001
		check(id+"_stroke_outer_edge_equals_actual_sweep",exact,{"radius":state.geometry.radius_m,"width":fx._warning_width(state.geometry)})
		check(id+"_two_tone_material_is_essential",state.warning.material_override.shader==Effects.ProjectileWarningShader and state.warning.material_override.render_priority==2)
	cast_ability("piercing_dawn");advance(.65);state=current()
	check("single_piercing_warning_retires_at_own_release",state.released and not state.warning.visible)
	cast_ability("kodanda");state=current()
	check("ordinary_shot_has_no_ground_lane_clutter",not state.warning.visible)
	kit.cancel_active("finished")
	var source_sha256: Dictionary={}
	for path in [get_script().resource_path,"res://scripts/rama_ability_effects.gd","res://scripts/rama_ability_kit.gd","res://shaders/rama_projectile_warning.gdshader"]:source_sha256[path]=FileAccess.get_sha256(path)
	var passed:=checks.all(func(item):return item.passed)
	var report:={"schema":1,"suite":"rama_volley_warning_cases","passed":passed,"checks":checks,"source_sha256":source_sha256,"scope":"Actual offline kit event timing, pending lane geometry, accessibility, stale event and lifecycle checks. No rendered readability, human feel, online or hardware acceptance."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path:=argument.trim_prefix("--report=");DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("Rama volley warning checks: %d/%d"%[checks.filter(func(item):return item.passed).size(),checks.size()])
	kit.free();fx.free();army.free();quit(0 if passed else 1)
