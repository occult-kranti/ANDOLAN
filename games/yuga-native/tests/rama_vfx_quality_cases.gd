extends SceneTree
## Presentation counterexamples over the real offline army and accepted kit events.
## Finite geometry, ownership and stage checks cannot certify the visible art target.
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
	if not passed:push_error("RAMA VFX QUALITY FAILED: "+label)
func fresh() -> void:
	army.reset();events.clear();fx.set_suspended(false)
	fx.set_options({"reduced_motion":false,"reduced_effects":false})
func advance(seconds: float) -> void:
	var remaining:=seconds
	while remaining>1e-8:
		var dt:=minf(.05,remaining)
		army.step_simulation(dt);fx.step(dt);remaining-=dt
func cast(id: String) -> bool:
	return kit.request_ability(id,Vector3.ZERO,Vector3(0,0,1),Vector3(0,0,4)).accepted
func live() -> Dictionary:return fx._casts.values()[0]
func vertices(mesh: Mesh) -> PackedVector3Array:
	if mesh.get_surface_count()==0:return PackedVector3Array()
	return mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
func geometry_valid(node: Node) -> bool:
	if node is MeshInstance3D and node.mesh:
		for v in vertices(node.mesh):
			if not v.is_finite() or v.length()>50:return false
	for child in node.get_children():
		if not geometry_valid(child):return false
	return true
func count_lights(node: Node) -> int:
	var result:=1 if node is Light3D else 0
	for child in node.get_children():result+=count_lights(child)
	return result
func run() -> void:
	army=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	check("real_army_configures",army.configure(manifest,null))
	kit=Kit.new();root.add_child(kit)
	fx=Effects.new();root.add_child(fx);fx.set_process(false)
	check("real_kit_configures",kit.configure(army))
	kit.ability_event.connect(func(event):events.append(event.duplicate(true));fx.consume_event(event))
	for id in ["piercing_dawn","dawn_volley"]:
		fresh();check(id+"_accepted",cast(id))
		var current:=live()
		var early_opacity: float=current.main.get_shader_parameter("opacity")
		var mesh_count: int=fx.report().meshes
		var windup: float=current.timing.windup_s
		advance(windup-.05)
		check(id+"_charge_grows_without_phantom_arrows",float(current.main.get_shader_parameter("opacity"))>early_opacity*2 and fx.report().live_arrows==0 and current.warning.visible and not events.any(func(e):return e.kind=="release"),{"early_opacity":early_opacity,"late_opacity":current.main.get_shader_parameter("opacity")})
		check(id+"_charge_has_finite_open_geometry",geometry_valid(current.root) and current.motif.mesh.get_surface_count()==1 and current.accent.mesh.get_surface_count()==1)
		check(id+"_same_owned_mesh_nodes_at_charge",fx.report().meshes==mesh_count,{"meshes":mesh_count})
		advance(.05)
		check(id+"_one_real_release_starts_first_arrow",events.filter(func(e):return e.kind=="release").size()==1 and fx.report().live_arrows==1 and not current.warning.visible)
		check(id+"_fine_solar_core_is_explicit",float(current.main.get_shader_parameter("core_strength"))>=.5)
		fx.set_options({"reduced_motion":true,"reduced_effects":true})
		check(id+"_reduced_effects_keep_projectile_remove_wake",current.arrows[0].root.visible and current.arrows[0].shaft.visible and not current.arrows[0].feather.visible and not current.accent.visible)
		var age: float=current.age
		var phase: float=current.main.get_shader_parameter("phase")
		fx.set_suspended(true);fx.step(.3)
		check(id+"_pause_freezes_phase_and_age",current.age==age and float(current.main.get_shader_parameter("phase"))==phase)
		fx.set_suspended(false);fx.set_options({"reduced_motion":false,"reduced_effects":false})
		# Stable geometry within the same 30 Hz sample: high-Hz presentation
		# updates may move an arrow, but must not allocate another wake mesh.
		var wake_mesh: Mesh=current.arrows[0].feather.mesh
		var motif_mesh: Mesh=current.motif.mesh
		var geometry_frame: int=current.last_geometry_frame
		fx.step(.00001)
		check(id+"_subframe_reuses_mesh_resources",current.last_geometry_frame==geometry_frame and current.arrows[0].feather.mesh==wake_mesh and current.motif.mesh==motif_mesh)
		advance(.20)
		check(id+"_paced_live_arrows_match_accepted_geometry",fx.report().live_arrows==(3 if id=="dawn_volley" else 1) and geometry_valid(current.root))
		advance(1.5)
		check(id+"_normal_end_retires_all_owned_cast_geometry",fx.report().active==0 and events.any(func(e):return e.kind=="end"))
	for id in ["piercing_dawn","dawn_volley"]:
		fresh();cast(id);advance(.20)
		var current:=live()
		fx.set_options({"reduced_motion":true})
		var still_a: Dictionary=fx._shapes(current,1.0,0.0)
		current.age+=.08
		var still_b: Dictionary=fx._shapes(current,1.0,0.0)
		check(id+"_reduced_motion_freezes_decorative_orbit",still_a==still_b)
		kit.cancel_active("quality_cancel")
		check(id+"_cancel_removes_all_charge_geometry",fx.report().active==0 and fx.report().live_arrows==0)
	fresh();cast("guardian_circle");advance(5.0)
	var field:=live()
	fx.set_options({"reduced_motion":true,"reduced_effects":true});fx.step(.05)
	check("guardian_live_boundary_survives_interpolation_and_reduced_mode",field.warning.visible and field.authority_age<5.05)
	advance(.05)
	check("guardian_authority_expiry_removes_all_recipient_and_decorative_energy",not field.warning.visible and float(field.main.get_shader_parameter("opacity"))==0 and field.motif.mesh.get_surface_count()==0 and field.recipients.mesh.get_surface_count()==0)
	fresh()
	for i in range(100):
		fx._impact(Vector3(i%7,1,i%5),Color("ffd18b"),i%2==0)
		if i%3==0:fx.step(.43)
	check("contact_pool_remains_eighteen_allocations",fx.report().allocated_impacts<=18 and fx.report().finite,{"allocated":fx.report().allocated_impacts})
	check("no_dynamic_lights_or_particle_nodes",count_lights(fx)==0 and fx.report().lights==0 and fx.report().particles==0)
	fx.reset()
	check("reset_clears_pool_and_casts",fx.report().allocated_impacts==0 and fx.report().active==0)
	var sources: Dictionary={}
	for path in ["res://scripts/rama_ability_effects.gd","res://shaders/rama_ribbon.gdshader","res://scripts/rama_ability_kit.gd","res://tests/rama_vfx_quality_cases.gd"]:sources[path]=FileAccess.get_sha256(path)
	var passed:=checks.all(func(c):return c.passed)
	var report:={"schema":1,"suite":"rama_vfx_quality_cases","passed":passed,"checks":checks,"source_sha256":sources,"scope":"Real offline kit events with structural presentation counterexamples. No rendered art, GPU performance, multiplayer, readability or AAA-quality acceptance."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path:=argument.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("Rama VFX quality checks: %d/%d"%[checks.filter(func(c):return c.passed).size(),checks.size()])
	kit.free();fx.free();army.free();quit(0 if passed else 1)
