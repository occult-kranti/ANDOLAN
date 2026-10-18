extends SceneTree
## Executes the current component on shared physical-time tapes. No render claim.
var secondary_source := "res://scripts/rama_secondary_motion.gd"
var output := "/tmp/visual-round-secondary.json"
# baseline runs live-component checks; candidate-math adds CPU transport oracles.
# Neither mode executes the experimental shader or claims rendered acceptance.
var mode := "baseline"
var checks: Array[Dictionary] = []
var examples := {}
var fixtures: Array[Node] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
		if arg.begins_with("--source="): secondary_source = arg.trim_prefix("--source=")
		if arg.begins_with("--mode="): mode = arg.trim_prefix("--mode=")
	call_deferred("run")

func check(label: String, passed: bool, details := {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func component() -> Node:
	var visual := Node3D.new()
	var node := MeshInstance3D.new()
	var mesh := ArrayMesh.new()
	for material_name in ["Cobalt handwoven silk","Swept black hair"]:
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3.ZERO,Vector3.RIGHT,Vector3.UP])
		arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.BACK,Vector3.BACK,Vector3.BACK])
		arrays[Mesh.ARRAY_COLOR] = PackedColorArray([Color(1,1,1,0),Color(1,1,1,.5),Color.WHITE])
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var material := StandardMaterial3D.new()
		material.resource_name = material_name
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		mesh.surface_set_material(mesh.get_surface_count()-1,material)
	node.mesh = mesh
	visual.add_child(node)
	root.add_child(visual)
	var source: Script = load(secondary_source)
	var secondary: Node = source.new()
	visual.add_child(secondary)
	assert(secondary.configure(visual))
	fixtures.append(visual)
	return secondary

func vector(value: Vector3) -> Array:
	return [value.x,value.y,value.z]

func snapshot(secondary: Node) -> Dictionary:
	return {"cloth_offset_m":vector(secondary.cloth_offset),"hair_offset_m":vector(secondary.hair_offset),"cloth_velocity_mps":vector(secondary.cloth_velocity),"hair_velocity_mps":vector(secondary.hair_velocity),"elapsed_s":secondary.elapsed,"reset_count":secondary.reset_count,"reason":secondary.last_reason}

func transported(value: Vector3, before_x: Vector3, before_y: Vector3, after_x: Vector3, after_y: Vector3) -> Vector3:
	# CPU mathematical oracle for the staged experiment; GPU code is unexecuted.
	var before_cross := before_x.cross(before_y)
	var after_cross := after_x.cross(after_y)
	var before_area := before_cross.length_squared()
	var after_area := after_cross.length_squared()
	if before_area<=maxf(1e-20,before_x.length_squared()*before_y.length_squared()*1e-6) or after_area<=maxf(1e-20,after_x.length_squared()*after_y.length_squared()*1e-6): return value
	var first := before_cross.normalized()
	var last := after_cross.normalized()
	var cosine := clampf(first.dot(last),-1,1)
	if cosine<=-.99: return value
	var axis := first.cross(last)
	return value+axis.cross(value)+axis.cross(axis.cross(value))/(1+cosine)

func frame_cases() -> void:
	var ex := Vector3.RIGHT
	var ey := Vector3.UP
	var geometric := Vector3.BACK
	var authored := Vector3(.3,.2,1).normalized()
	check("Transport identity retains authored smooth normal exactly",transported(authored,ex,ey,ex,ey)==authored)
	var translation := Vector3(.02,-.01,.075)
	var points := [Vector3.ZERO,ex,ey]
	var moved := [points[0]+translation,points[1]+translation,points[2]+translation]
	check("Uniform translation retains authored frame",transported(authored,ex,ey,moved[1]-moved[0],moved[2]-moved[0]).distance_to(authored)<.000001)
	# Two fixed zero-mask points and a displaced free corner produce atan(.075).
	var bent_y := ey+Vector3(0,0,.075)
	var expected_face := Vector3(0,-.075,1).normalized()
	var corrected_face := transported(geometric,ex,ey,ex,bent_y)
	var corrected_authored := transported(authored,ex,ey,ex,bent_y)
	var expected_angle := atan(.075)
	check("Known alpha displacement exposes unchanged-normal baseline error",absf(geometric.angle_to(expected_face)-expected_angle)<.000001,{"baseline_normal_error_degrees":rad_to_deg(geometric.angle_to(expected_face)),"source_fixed_vertices":2,"free_vertex_displacement_m":.075})
	check("Transport aligns geometric normal without flattening authored smoothing",corrected_face.distance_to(expected_face)<.000001 and absf(corrected_authored.dot(expected_face)-authored.dot(geometric))<.000001 and corrected_authored.distance_to(expected_face)>.1)
	var tangent := authored.cross(Vector3.UP).normalized()
	for handedness in [-1,1]:
		var binormal: Vector3 = authored.cross(tangent)*handedness
		var moved_t := transported(tangent,ex,ey,ex,bent_y)
		var moved_b := transported(binormal,ex,ey,ex,bent_y)
		check("Transport preserves %d tangent handedness and frame angles"%handedness,absf(corrected_authored.cross(moved_t).dot(moved_b)-handedness)<.000001 and absf(moved_t.length()-1)<.000001 and absf(moved_b.length()-1)<.000001 and absf(corrected_authored.dot(moved_t))<.000001)
	check("Collapsed differential retains finite authored normal",transported(authored,ex,ex,ex,bent_y)==authored and transported(authored,ex,ey,ex,ex)==authored)
	check("Nearly collinear differential refuses unstable frame",transported(authored,ex,Vector3(1,.000001,0),ex,bent_y)==authored)
	check("Near-opposite and opposite geometric normals retain authored frame",transported(authored,ex,ey,ex,Vector3(0,-1,.01))==authored and transported(authored,ex,ey,ex,-ey)==authored)
	var view := Basis(Vector3(.2,.6,.4).normalized(),.8)
	var in_view := transported(view*authored,view*ex,view*ey,view*ex,view*bent_y)
	check("Frame transport commutes with a rigid view transform",in_view.distance_to(view*corrected_authored)<.000001)
	examples["frame_counterexample"] = {"authored_normal":vector(authored),"deformed_face_normal":vector(expected_face),"transported_authored_normal":vector(corrected_authored),"scope":"CPU geometric construction, not GPU or actual hero acceptance"}

func tape(time: float) -> Dictionary:
	# Smooth start, reverse, landing and finite yaw wrap, with 0.5 s aligned stops.
	var moving := time >= .5 and time < 4.5
	var velocity := Vector3(5*sin(time*2.1), .8*sin(time*3.0), 8*sin((time-.5)*1.2)) if moving else Vector3.ZERO
	return {"local_velocity":velocity,"position":Vector3(time,0,0),"yaw":wrapf(2.8+time*1.8+sin(time*2.2)*.4,-PI,PI),"grounded":time<2.0 or time>=3.0}

func simulate(hz: int) -> Dictionary:
	var secondary := component()
	secondary.update_secondary(1.0/hz,tape(0))
	var samples: Array = []
	var finite := true
	var maximum_cloth := 0.0
	var maximum_hair := 0.0
	for index in hz*6:
		var time := float(index)/hz
		var accepted: bool = secondary.update_secondary(1.0/hz,tape(time))
		finite = finite and accepted and secondary.report().finite
		maximum_cloth = maxf(maximum_cloth,secondary.cloth_offset.length())
		maximum_hair = maxf(maximum_hair,secondary.hair_offset.length())
		if (index+1)%(hz/30) == 0:
			samples.append({"time_s":float(index+1)/hz,"cloth":secondary.cloth_offset,"hair":secondary.hair_offset})
		if (index+1)%(hz/2) == 0:
			examples["%dHz/%.1fs"%[hz,float(index+1)/hz]] = snapshot(secondary)
	check("Shared tape finite and bounded at %d Hz"%hz,finite and maximum_cloth<=.075001 and maximum_hair<=.018001,{"samples":hz*6,"maximum_cloth_m":maximum_cloth,"maximum_hair_m":maximum_hair})
	return {"samples":samples,"node":secondary}

func run() -> void:
	if mode not in ["baseline","candidate-math"]:
		push_error("Expected --mode=baseline or --mode=candidate-math")
		quit(2)
		return
	if mode=="candidate-math": frame_cases()
	var reference := simulate(120)
	for hz in [30,60]:
		var result := simulate(hz)
		var cloth_error := 0.0
		var hair_error := 0.0
		var worst_time := 0.0
		for index in result.samples.size():
			var error: float = result.samples[index].cloth.distance_to(reference.samples[index].cloth)
			if error>cloth_error: worst_time = result.samples[index].time_s
			cloth_error = maxf(cloth_error,error)
			hair_error = maxf(hair_error,result.samples[index].hair.distance_to(reference.samples[index].hair))
		check("Common-time tape agreement at %d/120 Hz"%hz,cloth_error<.003 and hair_error<.0015,{"maximum_cloth_error_m":cloth_error,"maximum_hair_error_m":hair_error,"worst_cloth_time_s":worst_time,"cloth_tolerance_m":.003,"hair_tolerance_m":.0015,"comparison_samples":result.samples.size()})
	var secondary := component()
	for unused in 60: secondary.update_secondary(1.0/60,{"local_velocity":Vector3(3,0,8)})
	var before: Dictionary = secondary.report()
	for unused in 15: secondary.update_secondary(.1,{"paused":true,"position":Vector3(20,0,0),"yaw":2.4})
	check("Pause holds complete report and sampling history",before==secondary.report())
	var paused_twin := component()
	for unused in 60: paused_twin.update_secondary(1.0/60,{"local_velocity":Vector3(3,0,8)})
	var resumed_state := {"local_velocity":Vector3(3,0,8),"yaw":.03}
	secondary.update_secondary(1.0/60,resumed_state)
	paused_twin.update_secondary(1.0/60,resumed_state)
	check("Resume equals a twin that received no paused calls",secondary.report()==paused_twin.report())
	examples["resume"] = snapshot(secondary)
	secondary.update_secondary(1.0/60,{"position":Vector3(20,0,0),"yaw":2.4,"local_velocity":Vector3(0,0,8)})
	check("Teleport clears position and velocity inertia",secondary.cloth_offset==Vector3.ZERO and secondary.cloth_velocity==Vector3.ZERO and secondary.hair_offset==Vector3.ZERO and secondary.hair_velocity==Vector3.ZERO and secondary.last_reason=="teleport")
	examples["teleport"] = snapshot(secondary)
	secondary.update_secondary(1.0/60,{"reset":true,"position":Vector3(20,0,0)})
	check("Explicit generation reset clears inertia",secondary.cloth_offset==Vector3.ZERO and secondary.hair_offset==Vector3.ZERO and secondary.elapsed==0)
	secondary.update_secondary(1.0/60,{"alive":false,"position":Vector3(20,0,0)})
	var death_count: int = secondary.reset_count
	for unused in 15: secondary.update_secondary(1.0/60,{"alive":false,"position":Vector3(20,0,0)})
	check("Death holds rest without repeating generation reset",secondary.reset_count==death_count and secondary.cloth_offset==Vector3.ZERO and secondary.hair_offset==Vector3.ZERO)
	secondary.update_secondary(1.0/60,{"alive":true,"position":Vector3(20,0,0)})
	check("Respawn discards dead history",secondary.cloth_offset==Vector3.ZERO and secondary.hair_offset==Vector3.ZERO and secondary.last_reason=="death/respawn")
	# One bounded 100 ms step and twelve 120 Hz steps integrate the same target.
	var big_step := component()
	var split_step := component()
	var constant := {"local_velocity":Vector3(4,-2,12)}
	big_step.update_secondary(.1,constant)
	for unused in 12: split_step.update_secondary(1.0/120,constant)
	check("Bounded hitch partitions exactly for a constant target",big_step.cloth_offset.distance_to(split_step.cloth_offset)<.000001 and big_step.hair_offset.distance_to(split_step.hair_offset)<.000001,{"cloth_error_m":big_step.cloth_offset.distance_to(split_step.cloth_offset),"hair_error_m":big_step.hair_offset.distance_to(split_step.hair_offset)})
	examples["bounded_hitch_100ms"] = snapshot(big_step)
	check("Over-limit hitch refuses catch-up and resets",not big_step.update_secondary(.10001,constant) and big_step.cloth_offset==Vector3.ZERO and big_step.hair_offset==Vector3.ZERO)
	check("Zero-alpha anchors remain exact through live motion",split_step.rest_displacement(0)==Vector3.ZERO and split_step.rest_displacement(0,"hair")==Vector3.ZERO and split_step.rest_displacement(1)==split_step.cloth_offset)
	var passed := true
	for entry in checks: passed = passed and entry.passed
	var file := FileAccess.open(output,FileAccess.WRITE)
	if file: file.store_string(JSON.stringify({"passed":passed,"mode":mode,"checks":checks,"state_examples":examples,"sources":{secondary_source:FileAccess.get_sha256(secondary_source),get_script().resource_path:FileAccess.get_sha256(get_script().resource_path)},"scope":"Actual current component integration on synthetic sampled movement tapes and material fixture. candidate-math mode additionally checks a CPU transport oracle; it does not execute the staged shader. No actual player input, skinning, collision, GPU or visual acceptance."},"\t")+"\n")
	else: passed = false
	for fixture in fixtures: fixture.free()
	quit(0 if passed else 1)
