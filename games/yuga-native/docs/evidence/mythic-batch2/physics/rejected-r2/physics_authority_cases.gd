extends SceneTree
## Actual Godot direct-space counterpart to tools/physics/reference.ts.
## Fixture-only: no imported world, player controller or online clients.
const FIXTURE_PATH := "res://assets/contracts/physics-fixture-v1.json"
var checks: Array[Dictionary] = []
var world: Node3D
var fixture: Dictionary
var space: PhysicsDirectSpaceState3D
var output := "/tmp/yuga-physics-godot.json"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func check(ok: bool, label: String, detail: Variant = null) -> void:
	checks.append({"id":label,"passed":ok,"detail":detail})
	if not ok: push_error(label)

func v(value: Array) -> Vector3:
	return Vector3(float(value[0]), float(value[1]), float(value[2]))

func wire(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func aim_direction(yaw: float, pitch: float) -> Vector3:
	return Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))

func _run() -> void:
	fixture = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	check(fixture.schema_version == 1 and fixture.fixture_id == "yuga-stacked-physics-v1", "fixture identity")
	check(fixture.coordinates.units == "metres" and fixture.coordinates.up == "+Y" and fixture.coordinates.position == "feet_origin", "metres feet-origin up contract")
	check(fixture.layers.world == 1 and fixture.layers.actor == 2 and fixture.layers.target == 4, "layers match native contract")
	world = Node3D.new()
	root.add_child(world)
	for collider in fixture.colliders:
		if collider.visual_only: continue
		var body := StaticBody3D.new()
		body.name = collider.id
		body.set_meta("fixture_id", collider.id)
		body.collision_layer = int(collider.layer)
		body.collision_mask = 0
		var shape_node := CollisionShape3D.new()
		if collider.shape == "box":
			var shape := BoxShape3D.new()
			shape.size = v(collider.size)
			shape_node.shape = shape
			body.position = v(collider.center)
		else:
			var shape := ConvexPolygonShape3D.new()
			var points := PackedVector3Array()
			for point in collider.vertices: points.append(v(point))
			shape.points = points
			shape_node.shape = shape
		body.add_child(shape_node)
		world.add_child(body)
	await physics_frame
	await physics_frame
	space = world.get_world_3d().direct_space_state
	var queries: Array[Dictionary] = []
	var by_id: Dictionary = {}
	for query in fixture.queries:
		var result := _query(query)
		queries.append({"id":query.id,"actor":query.actor,"kind":query.kind,"result":result})
		by_id[query.id] = result
	check(by_id["bridge-road-support"].collider == "road" and by_id["bridge-deck-support"].collider == "bridge", "bridge and underpass retain distinct support at same xz")
	check(by_id["stack-road-support"].collider == "road" and by_id["stack-lower-support"].collider == "deck-lower" and by_id["stack-upper-support"].collider == "deck-upper", "three supports share same xz without flattening")
	check(by_id["ramp-support"].collider == "ramp" and absf(by_id["ramp-support"].position[1] - 2.0) < 0.005, "actual convex ramp height")
	check(by_id["underpass-clear"].fraction == 1.0 and by_id["bridge-walk-clear"].fraction == 1.0, "paired route bodies fit below and above bridge")
	check(by_id["stairs-do-not-invent-step"].fraction < 1.0 and by_id["ramp-rising-block"].fraction < 1.0, "query-only experiment does not invent step-up or sliding")
	check(by_id["ceiling-up-block"].fraction > 0.08 and by_id["ceiling-up-block"].fraction < 0.11, "low ceiling blocks upward body movement")
	check("low-ceiling" in by_id["ceiling-initial-overlap"].colliders, "initial overlap detected separately from sweep")
	check(by_id["ceiling-overlap-sweep-policy"].fraction == 1.0, "cast_motion ignores preexisting overlap and cannot serve as recovery")
	check(by_id["visual-canopy-does-not-block"].collider == "target-low", "visual-only canopy excluded")
	check(not by_id["mask-world-ignores-target"].hit, "world layer excludes target")
	check(by_id["actor-layer-low"].collider == "actor-a" and by_id["actor-layer-high"].collider == "actor-b", "actor layer preserves elevation")
	check(by_id["remote-pitch-up"].collider == "target-high" and by_id["remote-pitch-down"].collider == "target-low", "remote pitch changes actual hit target")
	check(by_id["bridge-occludes-vertical-aim"].collider == "bridge", "bridge occludes vertical aim")
	check(by_id["wall-highspeed-no-tunnel"].fraction < 1.0, "swept box catches high speed barrier")
	var stream: Array[Dictionary] = []
	var spec: Dictionary = fixture.paired_stream
	var actors: Array = spec.actors.duplicate(true)
	var started := Time.get_ticks_usec()
	for tick in range(int(spec.ticks)):
		for actor in actors:
			var motion := v(actor.velocity) / float(spec.tick_hz)
			var movement := _query({"kind":"sweep","feet":actor.feet,"size":fixture.query_contract.actor_size,"motion":wire(motion),"mask":spec.mask})
			actor.feet = wire(v(actor.feet) + motion * float(movement.fraction))
			var support := _query({"kind":"ray","from":wire(v(actor.feet) + Vector3.UP * 0.1),"to":wire(v(actor.feet) - Vector3.UP * float(spec.support_drop_m)),"mask":spec.mask})
			stream.append({"tick":tick,"actor":actor.id,"feet":actor.feet.duplicate(),"fraction":movement.fraction,"support":support})
	var elapsed := float(Time.get_ticks_usec() - started) / 1000.0
	check(stream.size() == 480, "two logical actors sampled for 240 ticks")
	check(stream[100].support.collider == "road" and stream[101].support.collider == "bridge", "paired stream preserves same-xz layered support")
	check(stream[-1].support.collider == "road", "upper stream detects bridge edge drop without invented gravity")
	check(world.get_child_count() == fixture.colliders.size() - 1, "visual-only body never entered physics")
	var failures := checks.filter(func(c:Dictionary)->bool:return not c.passed).size()
	var result := {"format":1,"implementation":"godot-direct-space-query-v1","engine":Engine.get_version_info().string,"physics_engine":ProjectSettings.get_setting("physics/3d/physics_engine", "GodotPhysics3D"),"fixture_sha256":FileAccess.get_sha256(FIXTURE_PATH),"source_sha256":FileAccess.get_sha256("res://tests/physics_authority_cases.gd"),"queries":queries,"stream":stream,"checks":checks,"failed":failures,"passed":failures == 0,"profile":{"stream_queries":stream.size()*2,"stream_query_elapsed_ms":elapsed,"scope":"single headless process query wall time; no online, rendering, controller or real-time server capacity claim"}}
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file == null: push_error("cannot write report"); quit(2); return
	file.store_string(JSON.stringify(result, "  ") + "\n")
	print(JSON.stringify({"checks":checks.size(),"failed":failures,"queries":queries.size(),"stream":stream.size(),"report":output}))
	world.free()
	quit(1 if failures else 0)

func _query(query: Dictionary) -> Dictionary:
	if query.kind == "ray" or query.kind == "aim":
		var origin: Vector3
		var endpoint: Vector3
		var direction := Vector3.ZERO
		if query.kind == "aim":
			origin = v(query.origin)
			direction = aim_direction(float(query.yaw), float(query.pitch))
			endpoint = origin + direction * float(query.distance)
		else:
			origin = v(query.from)
			endpoint = v(query.to)
		var parameters := PhysicsRayQueryParameters3D.create(origin, endpoint, int(query.mask))
		parameters.hit_from_inside = false
		var found := space.intersect_ray(parameters)
		var result: Dictionary = {"hit":not found.is_empty()}
		if not found.is_empty():
			result.merge({"collider":found.collider.get_meta("fixture_id"),"position":wire(found.position),"normal":wire(found.normal),"fraction":origin.distance_to(found.position)/origin.distance_to(endpoint)})
		if query.kind == "aim": result.direction = wire(direction)
		return result
	var shape := BoxShape3D.new()
	shape.size = v(query.size)
	var parameters := PhysicsShapeQueryParameters3D.new()
	parameters.shape = shape
	parameters.transform = Transform3D(Basis.IDENTITY, v(query.feet) + Vector3.UP * shape.size.y / 2.0)
	parameters.collision_mask = int(query.mask)
	parameters.margin = 0.0
	if query.kind == "overlap":
		var colliders: Array[String] = []
		for result in space.intersect_shape(parameters, 128): colliders.append(result.collider.get_meta("fixture_id"))
		colliders.sort()
		return {"colliders":colliders}
	parameters.motion = v(query.motion)
	var fractions := space.cast_motion(parameters)
	return {"fraction":fractions[0],"unsafe_fraction":fractions[1]}
