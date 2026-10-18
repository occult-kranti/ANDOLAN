extends SceneTree
## G2 actual unit/mesh sampling around the unchanged committed bow timing.
## Manual presentation samples supplement the existing fixed-step army regression.
const Unit = preload("res://scripts/lane_minion.gd")
const Art = preload("res://scripts/lane_infantry_art.gd")
var checks: Array = []

func _initialize() -> void: call_deferred("run")
func check_case(label: String, passed: bool, evidence = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})

func sample(unit, remaining: float) -> Dictionary:
	unit.attack_time = remaining
	unit.update_pose(7,1)
	return {"remaining":remaining,"nock_visible":unit.joints.nock.visible,"tracer_visible":unit.arrow.visible,"tracer_position":unit.arrow.global_position,"tracer_basis":unit.arrow.global_basis,"nock_center":unit.joints.nock.global_transform*Vector3(0,0,.32)}

func run() -> void:
	var source := {}
	for path in ["res://scripts/lane_infantry_art.gd","res://scripts/lane_minion.gd",get_script().resource_path]: source[path]=FileAccess.get_sha256(path)
	var unit = Unit.new()
	unit.setup(null,9,"moon","bow_guard",0)
	root.add_child(unit)
	unit.position = Vector3(3,0,5)
	unit.previous_position = unit.position
	unit.heading = .7
	unit.previous_yaw = unit.heading
	var target := Vector3(6,0,12)
	var windup: float = unit.start_attack(target)
	check_case("real_receiver_still_commits_exact_point26_windup",windup==.26 and unit.attack_time==.52 and unit.attack_cooldown==1.50)
	var snapshots: Array = []
	var exclusive := true
	var correct_phases := true
	for remaining in [.52,.50,.45,.400001,.40,.399999,.35,.30,.260001,.26,.259999,.20,.05,0.0]:
		var state := sample(unit,remaining)
		snapshots.append(state)
		exclusive = exclusive and not (state.nock_visible and state.tracer_visible)
		correct_phases = correct_phases and state.nock_visible==(remaining>.40) and state.tracer_visible==(remaining<=.40 and remaining>.26)
	check_case("draw_release_travel_impact_never_show_duplicate_arrows",exclusive and correct_phases,snapshots)
	var before := sample(unit,.400001)
	var release := sample(unit,.40)
	check_case("release_starts_at_actual_nocked_shaft_center",before.nock_center.distance_to(release.tracer_position)<.00002,{"distance":before.nock_center.distance_to(release.tracer_position)})
	var near_impact := sample(unit,.260001)
	check_case("cosmetic_arrow_reaches_committed_point_at_point26",near_impact.tracer_position.distance_to(target+Vector3.UP)<.0001,{"distance":near_impact.tracer_position.distance_to(target+Vector3.UP)})
	var impact := sample(unit,.26)
	check_case("impact_has_no_lingering_nock_or_tracer",not impact.nock_visible and not impact.tracer_visible)
	var midpoint := sample(unit,.33)
	check_case("travel_is_between_exact_release_and_impact_endpoints",midpoint.tracer_position.distance_to(release.tracer_position.lerp(target+Vector3.UP,.5))<.00001)
	var authority := [unit.health,unit.attack_time,unit.attack_cooldown,unit.state,unit.position,unit.heading,unit.collision_layer,unit.shape.transform]
	for tick in range(120): unit.update_pose(7,1)
	var held := sample(unit,.33)
	check_case("same_army_clock_and_remaining_freeze_arrow_exactly",held==midpoint and authority==[unit.health,unit.attack_time,unit.attack_cooldown,unit.state,unit.position,unit.heading,unit.collision_layer,unit.shape.transform])
	unit.receive_damage(1000,"army")
	var dead := sample(unit,.33)
	check_case("real_death_receiver_hides_both_arrows",not dead.nock_visible and not dead.tracer_visible and not unit.alive and unit.collision_layer==0)
	unit.free()
	var repeats := true
	for attempt in range(8):
		unit = Unit.new()
		unit.setup(null,attempt,"sun" if attempt%2==0 else "moon","bow_guard",0)
		root.add_child(unit)
		repeats = repeats and not unit.arrow.visible and not unit.joints.nock.visible
		for attack in range(3):
			repeats = repeats and unit.start_attack(target)==.26
			var draw := sample(unit,.48)
			var flying := sample(unit,.36)
			var done := sample(unit,0)
			repeats = repeats and draw.nock_visible and not draw.tracer_visible and not flying.nock_visible and flying.tracer_visible and not done.nock_visible and not done.tracer_visible
		unit.free()
	check_case("eight_recreations_and24_attacks_have_no_stale_arrow_state",repeats)
	var art: Dictionary = Art.build("sun","spearman")
	root.add_child(art.root)
	var materials := {}
	for material in Art.material_cache.values(): materials[material.get_instance_id()]={"roughness":material.roughness,"metallic":material.metallic}
	check_case("cloth_leather_skin_and_metal_have_distinct_surface_finish",Art.material_cache.suncloth.roughness>.9 and Art.material_cache.leather.roughness<.8 and Art.material_cache.skin.roughness<.85 and Art.material_cache.sunarmour.metallic>.5 and Art.material_cache.sunarmour.roughness<.6,materials)
	art.root.free()
	var unchanged := true
	for path in source: unchanged=unchanged and source[path]==FileAccess.get_sha256(path)
	check_case("scoped_sources_unchanged_during_test",unchanged)
	var passed: bool = checks.all(func(row):return row.passed)
	var report := {"passed":passed,"passed_count":checks.filter(func(row):return row.passed).size(),"count":checks.size(),"checks":checks,"source_sha256":source,"scope":"Real unit receiver plus explicit presentation samples; unchanged committed0.26s hit,0.12s visual draw/0.14s travel. No new combat clock or rendered-motion acceptance."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var file := FileAccess.open(argument.trim_prefix("--report="),FileAccess.WRITE)
			file.store_string(JSON.stringify(report,"  ")+"\n")
	print("G2_INFANTRY_TIMING "+JSON.stringify({"passed":passed,"passed_count":report.passed_count,"count":checks.size()}))
	for row in checks:
		if not row.passed: print(JSON.stringify(row))
	quit(0 if passed else 1)
