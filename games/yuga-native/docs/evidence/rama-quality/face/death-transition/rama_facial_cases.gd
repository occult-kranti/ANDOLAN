extends SceneTree
## Small synthetic geometry verifies behavior. Actual lids need visual acceptance.
const FACE := preload("res://scripts/rama_facial_performance.gd")
var checks: Array[Dictionary] = []
var fixtures: Array[Node] = []
var output := "/tmp/rama-facial-cases.json"
var hero_asset := ""

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
		elif argument.begins_with("--asset="): hero_asset = argument.trim_prefix("--asset=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func fixture(shapes := true, large := false, half_count := 0) -> Array:
	var visual := Node3D.new()
	var rig := Skeleton3D.new()
	rig.add_bone("head")
	rig.set_bone_rest(0,Transform3D(Basis.IDENTITY,Vector3(0,1.7,0)))
	visual.add_child(rig)
	var face := MeshInstance3D.new()
	face.name = "RamaFace"
	var mesh := ArrayMesh.new()
	mesh.blend_shape_mode = Mesh.BLEND_SHAPE_MODE_RELATIVE
	if shapes:
		for shape in FACE.REQUIRED_SHAPES: mesh.add_blend_shape(shape)
		for index in half_count: mesh.add_blend_shape(FACE.HALF_SHAPES[index])
	var vertices := PackedVector3Array([Vector3(-.01,0,0),Vector3(.01,0,0),Vector3(0,.02,0)])
	if large:
		vertices.clear()
		for index in 8004: vertices.append(Vector3(float(index%3)*.01,float(index/3)*.001,0))
	var normals := PackedVector3Array()
	var colors := PackedColorArray()
	for unused in vertices.size():
		normals.append(Vector3.FORWARD)
		colors.append(Color(1,1,1,0))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_COLOR] = colors
	var morphs: Array[Array] = []
	if shapes:
		for unused in 2+half_count:
			var morph := []
			morph.resize(Mesh.ARRAY_MAX)
			var positions := PackedVector3Array()
			var normal_deltas := PackedVector3Array()
			for index in vertices.size():
				positions.append(Vector3(0,-.002,0))
				normal_deltas.append(Vector3.ZERO)
			morph[Mesh.ARRAY_VERTEX] = positions
			morph[Mesh.ARRAY_NORMAL] = normal_deltas
			morphs.append(morph)
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays,morphs)
	var material := StandardMaterial3D.new()
	material.resource_name = "Rama warm skin"
	mesh.surface_set_material(0,material)
	face.mesh = mesh
	rig.add_child(face)
	root.add_child(visual)
	var driver := FACE.new()
	visual.add_child(driver)
	fixtures.append(visual)
	return [visual,face,driver,rig]

func advance(driver: Node, seconds: float, hz := 120, state := {}) -> void:
	var steps := roundi(seconds*hz)
	for unused in steps: driver.update_facial(1.0/hz,state)

func trajectory(hz: int) -> Array:
	var f := fixture()
	var driver: Node = f[2]
	driver.configure(f[0])
	var samples := []
	for index in hz*17:
		var time := float(index+1)/hz
		# Input changes align with every tested clock; all matched times are 30 Hz.
		var effort := 1.0 if time>.5 and time<=1.5 else 0.0
		driver.update_facial(1.0/hz,{"effort":effort})
		if (index+1)%(hz/30)==0: samples.append(driver.report().weights.rama_blink_left)
	return samples

func collect_skeletons(node: Node, result: Array[Skeleton3D]) -> void:
	if node is Skeleton3D: result.append(node)
	for child in node.get_children(): collect_skeletons(child,result)

func imported_asset() -> void:
	if hero_asset.is_empty(): return
	var document := GLTFDocument.new()
	var state := GLTFState.new()
	var result := document.append_from_file(hero_asset,state)
	check("Requested actual GLB imports through the runtime importer",result==OK,{"asset_sha256":FileAccess.get_sha256(hero_asset)})
	if result!=OK: return
	var visual := document.generate_scene(state)
	root.add_child(visual)
	fixtures.append(visual)
	var skeletons: Array[Skeleton3D] = []
	collect_skeletons(visual,skeletons)
	var driver := FACE.new()
	visual.add_child(driver)
	var configured: bool = driver.configure(visual)
	check("Actual imported eyelid mesh binds alongside one 164-bone rig",configured and skeletons.size()==1 and skeletons[0].get_bone_count()==164)
	if not configured or skeletons.size()!=1: return
	var before := []
	for index in skeletons[0].get_bone_count(): before.append(skeletons[0].get_bone_pose(index))
	advance(driver,3.2166666667)
	var closed: Dictionary = driver.report()
	driver.reset("actual imported reset")
	var unchanged := true
	for index in skeletons[0].get_bone_count(): unchanged = unchanged and before[index]==skeletons[0].get_bone_pose(index)
	check("Actual imported morphs close/reset without modifying skeletal poses",closed.weights.rama_blink_left==1 and closed.weights.rama_blink_right==1 and driver.report().weights.rama_blink_left==0 and unchanged)

func run() -> void:
	var unbound := FACE.new()
	check("Unbound driver cannot write a hero",not unbound.update_facial(1.0/60,{}))
	unbound.free()
	var no_shapes := fixture(false)
	check("Released no-morph mesh fails closed without ownership",not no_shapes[2].configure(no_shapes[0]) and not no_shapes[1].has_meta(FACE.OWNER_META))
	var huge := fixture(true,true)
	check("Body-wide morph payload is rejected",not huge[2].configure(huge[0]) and not huge[1].has_meta(FACE.OWNER_META))
	var half_missing := fixture(true,false,1)
	check("Incomplete half-blink corrective pair fails closed",not half_missing[2].configure(half_missing[0]) and not half_missing[1].has_meta(FACE.OWNER_META))
	var corrected := fixture(true,false,2)
	corrected[2].configure(corrected[0])
	advance(corrected[2],3.175)
	var corrected_weight: float = corrected[2].report().weights.rama_blink_left
	check("Closing arc uses authored half shape instead of a direct full-shape chord",corrected[2].report().half_correctives and corrected[1].get_blend_shape_value(0)==0 and absf(corrected[1].get_blend_shape_value(2)-corrected_weight*2)<.000001)
	advance(corrected[2],.0416666667)
	check("Full closure retires half correctives without double deformation",corrected[1].get_blend_shape_value(0)==1 and corrected[1].get_blend_shape_value(1)==1 and corrected[1].get_blend_shape_value(2)==0 and corrected[1].get_blend_shape_value(3)==0)
	var f := fixture()
	var visual: Node3D = f[0]
	var mesh: MeshInstance3D = f[1]
	var driver: Node = f[2]
	var rig: Skeleton3D = f[3]
	var source_mesh: Mesh = mesh.mesh
	var source_material: Material = mesh.mesh.surface_get_material(0)
	var source_arrays: Array = mesh.mesh.surface_get_arrays(0)
	var rest: Transform3D = rig.get_bone_rest(0)
	check("Small authored two-lid mesh binds at neutral",driver.configure(visual) and driver.report().owned_meshes==1 and mesh.get_blend_shape_value(0)==0)
	check("Same driver cannot bind twice",not driver.configure(visual))
	var duplicate := FACE.new()
	visual.add_child(duplicate)
	check("Second driver cannot steal a bound mesh",not duplicate.configure(visual))
	advance(driver,3.175)
	var partial: Dictionary = driver.report()
	check("Authored blink has an intermediate closing sample",partial.weights.rama_blink_left>.1 and partial.weights.rama_blink_left<.95 and partial.weights.rama_blink_left==partial.weights.rama_blink_right,partial)
	var held: Dictionary = driver.report()
	for unused in 50: driver.update_facial(.1,{"paused":true,"effort":1.0,"alive":false})
	check("Pause freezes actual partial eyelid and all clocks",driver.report()==held)
	advance(driver,.0416666667)
	check("Closed blink reaches both authored endpoints",is_equal_approx(mesh.get_blend_shape_value(0),1) and is_equal_approx(mesh.get_blend_shape_value(1),1),driver.report())
	advance(driver,.2)
	check("Blink returns to neutral instead of accumulating closure",is_zero_approx(mesh.get_blend_shape_value(0)) and is_zero_approx(mesh.get_blend_shape_value(1)),driver.report())
	driver.reset("effort test")
	advance(driver,.6,120,{"effort":1.0,"blink_enabled":false})
	check("Effort uses bounded subtle authored partial closure",mesh.get_blend_shape_value(0)>.139 and mesh.get_blend_shape_value(0)<=.14,driver.report())
	advance(driver,1.0,120,{"blink_enabled":false})
	check("Recovery smoothly returns effort toward neutral",mesh.get_blend_shape_value(0)<.00001,driver.report())
	driver.reset("clock parity")
	var reference := trajectory(120)
	for hz in [30,60]:
		var samples := trajectory(hz)
		var maximum := 0.0
		for index in samples.size(): maximum = maxf(maximum,absf(samples[index]-reference[index]))
		check("Matched 17-second blink and effort path agrees at %d/120 Hz"%hz,maximum<.00001,{"samples":samples.size(),"maximum_weight_difference":maximum,"tolerance":.00001})
	for bad in [NAN,INF,-.01,0.0,.101]:
		check("Invalid delta %s clears stored expression without catch-up"%str(bad),not driver.update_facial(bad,{}) and driver.report().elapsed==0 and mesh.get_blend_shape_value(0)==0)
	for bad in ["strong",Vector3.ONE,NAN,INF]:
		check("Invalid effort %s is rejected before writing morphs"%str(bad),not driver.update_facial(1.0/60,{"effort":bad}) and mesh.get_blend_shape_value(0)==0)
	advance(driver,.15,120,{"alive":false})
	var defeat_mid: float = mesh.get_blend_shape_value(0)
	advance(driver,.2,120,{"alive":false})
	check("Death closes proper lids over time without jaw or eye warp",defeat_mid>.4 and defeat_mid<.9 and mesh.get_blend_shape_value(0)==1,driver.report())
	driver.update_facial(1.0/60,{"alive":true})
	check("Respawn clears stale corpse closure and blink clock",mesh.get_blend_shape_value(0)==0 and driver.report().elapsed==0 and driver.report().last_reason=="respawn")
	advance(driver,.4,120,{"effort":1.0})
	driver.update_facial(1.0/60,{"teleported":true})
	check("Teleport explicitly clears stored expression",mesh.get_blend_shape_value(0)==0 and driver.report().elapsed==0)
	for index in 100:
		advance(driver,.05,120,{"effort":1.0})
		driver.update_facial(1.0/60,{"reset":true})
	check("One hundred reset cycles retain one owner and fixed two-shape state",driver.report().owned_meshes==1 and driver.report().weights.size()==2 and mesh.get_blend_shape_value(0)==0 and mesh.get_meta(FACE.OWNER_META)==driver.get_instance_id())
	var final_arrays: Array = mesh.mesh.surface_get_arrays(0)
	check("Mesh arrays, mask, material and skeleton rest remain unchanged",mesh.mesh==source_mesh and mesh.mesh.surface_get_material(0)==source_material and source_arrays[Mesh.ARRAY_VERTEX]==final_arrays[Mesh.ARRAY_VERTEX] and source_arrays[Mesh.ARRAY_NORMAL]==final_arrays[Mesh.ARRAY_NORMAL] and source_arrays[Mesh.ARRAY_COLOR]==final_arrays[Mesh.ARRAY_COLOR] and rig.get_bone_rest(0)==rest and rig.get_bone_pose_scale(0)==Vector3.ONE)
	driver.release()
	check("Release removes only owned state and restores neutral",not mesh.has_meta(FACE.OWNER_META) and not driver.configured and mesh.get_blend_shape_value(0)==0)
	check("Released mesh can bind to a new owner",duplicate.configure(visual))
	mesh.free()
	check("Freed face fails safely without accumulating replacement nodes",not duplicate.update_facial(1.0/60,{}) and not duplicate.configured)
	var ambiguous := fixture()
	var copied := (ambiguous[1] as MeshInstance3D).duplicate()
	ambiguous[0].add_child(copied)
	check("Duplicate authored face nodes are rejected without partial ownership",not ambiguous[2].configure(ambiguous[0]) and not ambiguous[1].has_meta(FACE.OWNER_META) and not copied.has_meta(FACE.OWNER_META))
	var nonneutral := fixture()
	nonneutral[1].set_blend_shape_value(0,.2)
	check("Existing artist expression is preserved by rejecting nonneutral binding",not nonneutral[2].configure(nonneutral[0]) and is_equal_approx(nonneutral[1].get_blend_shape_value(0),.2))
	var partial_death := fixture(true,false,2)
	partial_death[2].configure(partial_death[0])
	advance(partial_death[2],3.175)
	var partial_start: Dictionary = partial_death[2].report().weights
	var previous_left: float = partial_start.rama_blink_left
	var previous_right: float = partial_start.rama_blink_right
	var monotonic := true
	var partial_samples := []
	for unused in 18:
		partial_death[2].update_facial(1.0/60,{"alive":false})
		var weights: Dictionary = partial_death[2].report().weights
		monotonic = monotonic and weights.rama_blink_left>=previous_left and weights.rama_blink_right>=previous_right
		previous_left=weights.rama_blink_left;previous_right=weights.rama_blink_right
		partial_samples.append([previous_left,previous_right])
	check("Death from partial blink continues monotonically to closed",monotonic and previous_left==1 and previous_right==1,{"start":partial_start,"consecutive_60hz_samples":partial_samples})
	var full_death := fixture(true,false,2)
	full_death[2].configure(full_death[0])
	advance(full_death[2],3.2166666667)
	var full_start: Dictionary = full_death[2].report().weights
	var stays_closed := true
	var full_samples := []
	for unused in 18:
		full_death[2].update_facial(1.0/60,{"alive":false})
		var weights: Dictionary = full_death[2].report().weights
		stays_closed = stays_closed and weights.rama_blink_left==1 and weights.rama_blink_right==1
		full_samples.append([weights.rama_blink_left,weights.rama_blink_right])
	check("Death from full blink never reopens authored lids",stays_closed,{"start":full_start,"consecutive_60hz_samples":full_samples})
	imported_asset()
	var passed := true
	for entry in checks: passed = passed and entry.passed
	var scope := "Synthetic small authored-morph fixture only. Does not accept actual Rama eyelids, facial art, imported geometry, rendering, physical GPU performance or commercial parity."
	if not hero_asset.is_empty(): scope = "Synthetic component cases plus requested actual GLB runtime import/binding/close-reset/unchanged-pose checks. No rendered art acceptance, gameplay integration, physical GPU performance or commercial parity."
	var report := {"passed":passed,"count":checks.size(),"checks":checks,"source_sha256":FileAccess.get_sha256("res://scripts/rama_facial_performance.gd"),"test_sha256":FileAccess.get_sha256(get_script().resource_path),"actual_asset_sha256":FileAccess.get_sha256(hero_asset) if not hero_asset.is_empty() else "","scope":scope}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	for item in fixtures: if is_instance_valid(item): item.queue_free()
	await process_frame
	quit(0 if passed else 1)
