extends SceneTree

const Visibility = preload("res://scripts/friendly_camera_visibility.gd")
const Unit = preload("res://scripts/lane_minion.gd")
var checks: Array = []
var output := ""

func check_(label: String, pass_: bool, details = {}) -> void:
	checks.append({"name":label,"passed":pass_,"details":details})

func mesh_list(node: Node) -> Array:
	var out: Array = []
	if node is GeometryInstance3D: out.append(node)
	for child in node.get_children(): out.append_array(mesh_list(child))
	return out

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func run() -> void:
	var world := Node3D.new(); root.add_child(world)
	var camera := Camera3D.new(); world.add_child(camera); camera.position = Vector3(0,1.4,0); camera.current = true
	var hero := Node3D.new(); world.add_child(hero); hero.position = Vector3(0,0,-3)
	var ally := Unit.new(); ally.setup(null,1,"sun","spearman",0); world.add_child(ally); ally.position = Vector3(0,0,-1.5)
	var other := Unit.new(); other.setup(null,2,"sun","spearman",0); world.add_child(other); other.position = Vector3(5,0,-1.5)
	var enemy := Unit.new(); enemy.setup(null,3,"moon","spearman",0); world.add_child(enemy); enemy.position = Vector3(0,0,-1.5)
	var meshes := mesh_list(ally)
	var body_meshes := mesh_list(ally.visual)
	var other_meshes := mesh_list(other.visual)
	var initial: Array = []; for mesh in meshes: initial.append(mesh.transparency)
	var physics_before := {"layer":ally.collision_layer,"mask":ally.collision_mask,"health":ally.health,"alive":ally.alive,"position":ally.position,"state":ally.state,"shape":ally.shape.shape.get_instance_id()}
	check_("actual_spearman_meshes_share_source_resources",body_meshes[0].mesh == other_meshes[0].mesh)
	var visibility := Visibility.new()
	visibility.update(camera,hero,[ally,other,enemy],1.0/60.0)
	check_("near_friendly_occluder_enters_smoothly",visibility.report().faded_units == 1 and visibility.report().maximum_fade > 0 and visibility.report().maximum_fade < .2,visibility.report())
	for index in range(20): visibility.update(camera,hero,[ally,other,enemy],1.0/60.0)
	check_("bounded_fade_never_hides_friendly_unit",is_equal_approx(visibility.report().maximum_fade,Visibility.MAX_FADE) and body_meshes[0].transparency < 1.0)
	check_("same_shared_mesh_instance_elsewhere_is_opaque",other_meshes[0].transparency == 0.0)
	check_("enemy_parts_remain_opaque",mesh_list(enemy).all(func(mesh):return mesh.transparency == 0.0))
	check_("authority_and_body_transform_unchanged",physics_before == {"layer":ally.collision_layer,"mask":ally.collision_mask,"health":ally.health,"alive":ally.alive,"position":ally.position,"state":ally.state,"shape":ally.shape.shape.get_instance_id()})
	ally.position.x = 4
	visibility.update(camera,hero,[ally,other,enemy],1.0/60.0)
	check_("clear_segment_restores_smoothly",visibility.report().maximum_fade > 0.0 and visibility.report().maximum_fade < Visibility.MAX_FADE)
	for index in range(20): visibility.update(camera,hero,[ally,other,enemy],1.0/60.0)
	check_("clear_segment_returns_exact_initial_values",meshes.all(func(mesh):return mesh.transparency == 0.0))
	ally.position = Vector3(0,0,1.5)
	for index in range(20): visibility.update(camera,hero,[ally],1.0/60.0)
	check_("unit_behind_camera_does_not_fade",visibility.report().faded_units == 0)
	ally.position = Vector3(0,0,-5)
	for index in range(20): visibility.update(camera,hero,[ally],1.0/60.0)
	check_("unit_beyond_hero_does_not_fade",visibility.report().faded_units == 0)
	ally.position = Vector3(0,0,-1.5); visibility.reset()
	meshes[0].transparency = .3
	for index in range(20): visibility.update(camera,hero,[ally],1.0/60.0)
	check_("existing_transparency_multiplies_without_material_edit",is_equal_approx(meshes[0].transparency,1.0-.7*(1.0-Visibility.MAX_FADE)))
	visibility.update(camera,hero,[ally],1.0/60.0,false)
	check_("overview_disable_restores_existing_transparency",is_equal_approx(meshes[0].transparency,.3) and visibility.report().cached_units == 0)
	visibility.update(camera,hero,[ally],1.0/60.0); visibility.update(camera,hero,[],1.0/60.0)
	check_("removed_unit_restores_and_releases_cache",is_equal_approx(meshes[0].transparency,.3) and visibility.report().cached_units == 0)
	visibility.update(camera,hero,[ally],1.0/60.0); var before: Dictionary = visibility.report()
	visibility.update(camera,hero,[ally],NAN)
	check_("nonfinite_delta_rejected_without_corrupting_state",visibility.report().rejected_updates == 1 and visibility.report().maximum_fade == before.maximum_fade)
	visibility.reset()
	visibility.update(camera,hero,[ally],9999.0)
	check_("hitch_step_bounded_to_point_one_seconds",visibility.report().maximum_fade <= .600001)
	visibility.reset()
	var rates: Array = []
	for hz in [30,60,120]:
		for index in range(hz): visibility.update(camera,hero,[ally],1.0/float(hz))
		rates.append(visibility.report().maximum_fade)
		visibility.reset()
	check_("thirty_sixty_one_twenty_reach_same_bound",rates.all(func(value):return is_equal_approx(value,Visibility.MAX_FADE)),rates)
	visibility.update(camera,hero,[ally],.05); ally.free(); visibility.update(camera,hero,[],.05)
	check_("freed_unit_releases_weak_cache_safely",visibility.report().cached_units == 0)
	var report := {"passed":checks.all(func(value):return value.passed),"checks":checks,"scope":"Actual existing unit meshes; headless geometric/per-instance property checks, no rendered acceptance"}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE); file.store_string(JSON.stringify(report,"\t")+"\n"); file.close()
	print(JSON.stringify({"passed":report.passed,"checks":checks.size(),"failures":checks.filter(func(value):return not value.passed)}))
	visibility.reset(); world.free()
	quit(0 if report.passed else 1)
