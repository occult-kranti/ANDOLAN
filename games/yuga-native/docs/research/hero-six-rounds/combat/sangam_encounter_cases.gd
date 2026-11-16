extends SceneTree
## Independent imported-world physics and actual offline combat checks.
## Run after lead's serialized import/integration; never imports or edits assets.
const District = preload("res://scripts/sangam_district.gd")
const Army = preload("res://scripts/lane_army.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Unit = preload("res://scripts/lane_minion.gd")
var checks: Array = []
var scene: Node3D
var army
var kit
var events: Array = []
var source_before: Dictionary = {}
var output := "/tmp/sangam-encounter-independent.json"

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):output=argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"case":label,"passed":passed,"detail":detail})
	if not passed:push_error("SANGAM ENCOUNTER: "+label)

func hashes() -> Dictionary:
	var result := {}
	for path in [get_script().resource_path,"res://scripts/confluence_world.gd","res://scripts/sangam_district.gd","res://assets/world/sangam-district.glb","res://assets/world/sangam-district.json","res://assets/world/confluence-map.json","res://scripts/lane_army.gd","res://scripts/rama_ability_kit.gd","res://scripts/relay_art.gd","res://scripts/relay_session.gd","res://scripts/world_ground.gdshader","res://scripts/world_ground_common.gdshaderinc","res://scripts/world_water.gdshader"]:
		result[path]=FileAccess.get_sha256(path)
	return result

func vec(value: Array) -> Vector3:return Vector3(value[0],value[1],value[2])

func ray(a: Vector3, b: Vector3) -> Dictionary:
	return scene.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1,[scene.player.get_rid()]))

func sweep(shape: Shape3D, a: Vector3, b: Vector3) -> float:
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape=shape;query.transform=Transform3D(Basis.IDENTITY,a);query.motion=b-a
	query.collision_mask=1;query.margin=.001;query.exclude=[scene.player.get_rid()]
	var result := scene.get_world_3d().direct_space_state.cast_motion(query)
	return result[0] if result.size()==2 else -1.0

func advance(seconds: float) -> void:
	for index in int(ceil(seconds/.05)):army.step_simulation(.05)

func clear_units() -> void:
	kit.reset("independent_fixture")
	for unit in army.units.duplicate():army.units.erase(unit);unit.free()
	army._rebuild_buckets();events.clear()

func enemy_at(point: Vector3):
	var unit=Unit.new();unit.render_art=false;unit.setup(army,army.next_id,"moon","commander",1)
	army.next_id+=1;unit.position=point;unit.attack_time=1000;unit.attack_cooldown=1000
	unit.defeated.connect(army._on_defeated);army.add_child(unit);army.units.append(unit)
	return unit

func run() -> void:
	source_before=hashes()
	scene=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	check("actual_integrated_world_is_ready",scene.world_ready)
	var district: Node3D=scene.world.get_node_or_null("SangamDistrict")
	check("actual_default_world_installs_authored_district",district!=null)
	if not scene.world_ready or district==null:finish();return
	scene.set_paused(false);scene.set_physics_process(false)
	scene.player.active=false;scene.player.set_physics_process(false);scene.army.set_physics_process(false)
	await physics_frame;await process_frame;await physics_frame;await process_frame
	var before := JSON.stringify(scene.manifest)
	var derived: Dictionary=scene.manifest
	for row in [["LankaLaneGate","res://scripts/lanka_lane_gate.gd"],["LankaWaterGarden","res://scripts/lanka_water_garden.gd"],["SangamDistrict","res://scripts/sangam_district.gd"]]:
		var node=scene.world.get_node_or_null(row[0])
		check("integrated_"+row[0]+"_present",node!=null)
		if node==null:finish();return
		var preparation: Dictionary=load(row[1]).prepare_army_manifest(derived,node)
		check("derived_"+row[0]+"_manifest_valid",preparation.get("ok",false))
		if not preparation.get("ok",false):finish();return
		derived=preparation.manifest
	check("canonical_manifest_unmutated",before==JSON.stringify(scene.manifest))
	army=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	check("effective_three_adapter_army_configures",army.configure(derived,null))
	# Existing relay_session appends nine plinth shapes after army.configure.
	# Derive them from actual instantiated physics shapes, not the army array.
	var relay_shapes:=0
	for body in get_nodes_in_group("relay_plinth"):
		for holder in body.get_children():
			if holder is CollisionShape3D and holder.shape is BoxShape3D:
				var bounds: AABB=holder.global_transform*AABB(-holder.shape.size*.5,holder.shape.size)
				army.boxes.append({"position":Vector3(bounds.get_center().x,bounds.position.y,bounds.get_center().z),"size":bounds.size})
				relay_shapes+=1
	check("nine_existing_relay_physics_shapes_retained",relay_shapes==9)
	check("actual_integrated_army_uses_effective_collision",army.boxes==scene.army.boxes,{"box_count":army.boxes.size(),"world_box_count":scene.army.boxes.size(),"expected":str(army.boxes),"actual":str(scene.army.boxes)})
	kit=Kit.new();root.add_child(kit);check("real_kit_configures",kit.configure(army))
	kit.ability_event.connect(func(event):events.append(event.duplicate(true)))
	clear_units()
	var capsule:=CapsuleShape3D.new();capsule.radius=float(scene.manifest.bounds.hero_radius);capsule.height=1.8
	var failures: Array=[];var segments:=0
	for route in scene.manifest.lanes+scene.manifest.rotations:
		var points: Array=route.points.duplicate(true)
		if route.get("closed",false):points.append(points[0])
		for index in range(points.size()-1):
			for direction in [false,true]:
				var a:=vec(points[index])+Vector3.UP*.95;var b:=vec(points[index+1])+Vector3.UP*.95
				var fraction:=sweep(capsule,b if direction else a,a if direction else b);segments+=1
				if fraction<.9999:failures.append({"route":route.id,"segment":index,"reverse":direction,"safe_fraction":fraction})
	check("actual_capsule_all_lane_and_rotation_segments_both_directions",failures.is_empty(),{"segments":segments,"radius":capsule.radius,"failures":failures})
	var camera_shape:=SphereShape3D.new();camera_shape.radius=.18
	for z in [-28.0,28.0]:
		var low:=Vector3(0,7,z);var high:=Vector3(0,9,z);var hit:=ray(low,high)
		check("connector_%s_has_exact_visible_underside"%z,not hit.is_empty() and absf(hit.position.y-8.0)<.005,{"hit":str(hit.get("position",Vector3.ZERO))})
		check("connector_%s_ground_army_and_camera_pass"%z,army.line_clear(Vector3(0,0,z-5),Vector3(0,0,z+5),.65) and sweep(camera_shape,Vector3(0,2.8,z-5),Vector3(0,2.8,z+5))>.9999)
	for x in [-8.0,8.0]:
		for z in [-60.0,60.0]:
			var tag:="cover_%s_%s"%[x,z]
			for height in [1.0,1.9,2.6]:
				var a:=Vector3(x-4,height,z);var b:=Vector3(x+4,height,z);var hit:=ray(a,b)
				check(tag+"_native_and_planar_height_%s"%height,not hit.is_empty() and absf(hit.position.x-(x-1.5))<.005 and not army.line_clear(a,b,.22),{"hit":str(hit.get("position",Vector3.ZERO))})
			check(tag+"_capsule_parallel_retreat_open",sweep(capsule,Vector3(x-2.3,.95,z-5),Vector3(x-2.3,.95,z+5))>.9999)
			check(tag+"_capsule_crossing_blocked",sweep(capsule,Vector3(x-4,.95,z),Vector3(x+4,.95,z))<.5)
			var origin:=Vector3(x-4,0,z);var target:=Vector3(x+4,0,z)
			for ability in ["kodanda","piercing_dawn","dawn_volley"]:
				clear_units();var enemy=enemy_at(target)
				var accepted: Dictionary=kit.request_ability(ability,origin,Vector3.RIGHT,target)
				advance(1.8)
				var wall_events: Array=events.filter(func(event):return event.kind=="impact" and event.get("reason","")=="wall")
				check(tag+"_real_"+ability+"_stops_before_receiver",accepted.accepted and enemy.health==150 and wall_events.size()==(3 if ability=="dawn_volley" else 1),{"wall_receipts":wall_events.size(),"receiver_health":enemy.health})
			clear_units()
			var ward: Dictionary=kit.request_ability("guardian_circle",origin,Vector3.RIGHT,target)
			check(tag+"_guardian_rejects_cross_cover",not ward.accepted and ward.reason=="Guardian Circle cannot cross cover")
			kit.set_movement_receiver(func(_from,destination,_duration):return {"accepted":true,"destination":destination})
			var step: Dictionary=kit.request_ability("measured_step",origin,Vector3.RIGHT,target)
			var begin_events: Array=events.filter(func(event):return event.kind=="begin" and event.ability_id=="measured_step")
			check(tag+"_step_target_stays_before_cover",step.accepted and begin_events.size()==1 and begin_events[0].target.x<x-1.5 and army.line_clear(origin,begin_events[0].target,.48),{"scope":"Authority planned target; independent player movement suite owns actual receipt/capsule movement."})
	clear_units()
	var raised: Dictionary=kit.request_ability("piercing_dawn",Vector3(0,8.56,-28),Vector3.FORWARD,Vector3(0,0,-40))
	check("raised_gallery_does_not_claim_elevated_combat",not raised.accepted and raised.reason=="Land before using Rama's kit")
	finish()

func finish() -> void:
	var after:=hashes();check("reviewed_sources_did_not_change",after==source_before)
	var passed: bool=checks.all(func(row):return row.passed)
	var report:={"task_id":"YUGA-HERO-6R","round":5,"passed":passed,"count":checks.size(),"checks":checks,"source_sha256":source_before,"source_after_sha256":after,"scope":"Independent default-world imported physics, all lane/rotation segment capsule sweeps, native gallery/cover probes, actual kit and staged receiver tests with private effective army. No renderer, OS input, human balance or GPU performance claim. Camera probes are a bounded .18m sphere sweep, not full spring-arm/camera visual acceptance."}
	DirAccess.make_dir_recursive_absolute(output.get_base_dir());FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("Sangam independent encounters: %d/%d"%[checks.filter(func(row):return row.passed).size(),checks.size()])
	if is_instance_valid(kit):kit.free()
	if is_instance_valid(army):army.free()
	if is_instance_valid(scene):
		# This physics fixture is silent. Stop the default world's music before
		# teardown so an audio mixing reference cannot outlive the short test.
		for player in scene.find_children("*", "Node", true, false):
			if player is AudioStreamPlayer or player is AudioStreamPlayer2D or player is AudioStreamPlayer3D:
				player.stop()
				player.stream=null
		scene.free()
	await process_frame
	await process_frame
	await create_timer(.12).timeout
	quit(0 if passed else 1)
