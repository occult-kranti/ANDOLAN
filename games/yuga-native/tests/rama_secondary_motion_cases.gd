extends SceneTree
## Component counterexamples; synthetic mask fixture. Actual asset/render remains separate.
const SECONDARY := preload("res://scripts/rama_secondary_motion.gd")
var checks: Array[Dictionary] = []
var output := "/tmp/rama-secondary-cases.json"
var fixtures: Array[Node] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func create(with_mask := true, bad_color := false, unsupported := false, lighting_fault := "") -> Array:
	var visual := Node3D.new()
	var mesh_node := MeshInstance3D.new()
	var mesh := ArrayMesh.new()
	for name_ in ["Cobalt handwoven silk","Worked warm gold","Swept black hair","Cobalt lotus brocade","Dark bow leather"]:
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(0,1.5,0),Vector3(.2,.7,-.2),Vector3(-.2,.3,-.3)])
		arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.FORWARD,Vector3.FORWARD,Vector3.FORWARD])
		arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2.ZERO,Vector2.RIGHT,Vector2.ONE])
		if with_mask:
			arrays[Mesh.ARRAY_COLOR] = PackedColorArray([Color(1,1,1,0),Color(.5 if bad_color else 1,1,1,.5),Color(1,1,1,1)])
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var material := StandardMaterial3D.new()
		material.resource_name = name_
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		material.albedo_color = Color(.18,.35,.56,1)
		material.metallic = .73 if name_ == "Worked warm gold" else .03
		material.roughness = .47
		material.metallic_specular = .31
		material.normal_enabled = true
		material.normal_scale = .42
		material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
		material.metallic_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_BLUE
		material.albedo_texture = GradientTexture2D.new()
		material.roughness_texture = GradientTexture2D.new()
		material.metallic_texture = material.roughness_texture
		material.normal_texture = GradientTexture2D.new()
		if unsupported: material.emission_enabled = true
		if lighting_fault == "diffuse": material.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
		if lighting_fault == "specular": material.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
		mesh.surface_set_material(mesh.get_surface_count()-1,material)
	mesh_node.mesh = mesh
	visual.add_child(mesh_node)
	root.add_child(visual)
	var secondary := SECONDARY.new()
	visual.add_child(secondary)
	var configured: bool = secondary.configure(visual)
	fixtures.append(visual)
	return [visual,mesh_node,secondary,configured]

func simulate(hz: int, turning := false) -> Node:
	var fixture := create()
	var secondary: Node = fixture[2]
	# Seed an unchanged neutral baseline so turn samples have a defined predecessor.
	secondary.update_secondary(.01,{})
	for index in hz*2:
		var time := float(index+1)/hz
		secondary.update_secondary(1.0/hz,{"local_velocity":Vector3(3,0,8),"position":Vector3(3,0,8)*time,"yaw":time*1.5 if turning else 0.0})
	return secondary

func varying(hz: int) -> Array[Vector3]:
	var secondary: Node = create()[2]
	secondary.update_secondary(.01,{})
	var samples: Array[Vector3] = []
	var position := Vector3.ZERO
	for index in hz*3:
		var time := float(index+1)/hz
		var velocity := Vector3(sin(time*1.7)*5,cos(time*.9)*.6,8+sin(time*1.3)*3)
		position += velocity/hz
		secondary.update_secondary(1.0/hz,{"local_velocity":velocity,"position":position,"yaw":sin(time*1.4)*.7})
		if (index+1)%(hz/30) == 0: samples.append(secondary.cloth_offset)
	return samples

func run() -> void:
	var unconfigured := SECONDARY.new()
	check("Unconfigured component cannot affect presentation",not unconfigured.update_secondary(1.0/60,{}))
	unconfigured.free()
	var no_mask := create(false)
	check("Missing semantic masks rejected without material overrides",not no_mask[3] and no_mask[1].get_surface_override_material(0) == null)
	var bad_mask := create(true,true)
	check("Non-white color masks rejected to preserve PBR albedo",not bad_mask[3] and bad_mask[1].get_surface_override_material(0) == null)
	var unsupported := create(true,false,true)
	check("Unsupported material features preserved by rejecting binding",not unsupported[3] and unsupported[1].get_surface_override_material(0) == null)
	for kind in ["diffuse","specular"]:
		var changed := create(true,false,false,kind)
		check("Nonstandard %s lighting rejects conversion without overriding PBR"%kind,not changed[3] and changed[1].get_surface_override_material(0) == null)
	var fixture := create()
	var mesh_node: MeshInstance3D = fixture[1]
	var secondary: Node = fixture[2]
	var original_mesh: Mesh = mesh_node.mesh
	check("Authored anchors and free tips bind four target surfaces",fixture[3] and secondary.report().bindings == 4 and secondary.report().masked_vertices.cloth == 6 and secondary.report().anchored_vertices.hair == 1)
	check("Duplicate configuration rejected",not secondary.configure(fixture[0]))
	check("Shared mesh, LOD resource and bow leather remain unchanged",mesh_node.mesh == original_mesh and mesh_node.get_surface_override_material(4) == null)
	var material: ShaderMaterial = mesh_node.get_surface_override_material(1)
	var original: StandardMaterial3D = mesh_node.mesh.surface_get_material(1)
	check("PBR textures, scalars and channel selectors preserved",material.get_shader_parameter("base_texture") == original.albedo_texture and material.get_shader_parameter("rough_texture") == original.roughness_texture and material.get_shader_parameter("normal_texture") == original.normal_texture and is_equal_approx(material.get_shader_parameter("roughness_value"),.47) and is_equal_approx(material.get_shader_parameter("metallic_value"),.73) and is_equal_approx(material.get_shader_parameter("normal_strength"),.42) and material.get_shader_parameter("rough_channel") == Vector4(0,1,0,0) and material.get_shader_parameter("metal_channel") == Vector4(0,0,1,0))
	var base := simulate(30)
	check("Steady travel drags free tips against motion with small lift",base.cloth_offset.x<-.01 and base.cloth_offset.z<-.025 and base.cloth_offset.y>0 and base.hair_offset.length()>.005 and base.hair_offset.length()<base.cloth_offset.length(),{"cloth_offset":base.cloth_offset,"hair_offset":base.hair_offset})
	for hz in [60,120]:
		var other := simulate(hz)
		check("Constant velocity response agrees at 30/%d Hz"%hz,base.cloth_offset.distance_to(other.cloth_offset)<.000001 and base.hair_offset.distance_to(other.hair_offset)<.000001,{"cloth_difference_m":base.cloth_offset.distance_to(other.cloth_offset),"hair_difference_m":base.hair_offset.distance_to(other.hair_offset)})
	var turning := simulate(30,true)
	for hz in [60,120]:
		var other := simulate(hz,true)
		check("Constant turn response agrees at 30/%d Hz"%hz,turning.cloth_offset.distance_to(other.cloth_offset)<.000001 and turning.hair_offset.distance_to(other.hair_offset)<.000001,{"cloth_difference_m":turning.cloth_offset.distance_to(other.cloth_offset)})
	var reference := varying(120)
	for hz in [30,60]:
		var sampled := varying(hz)
		var maximum := 0.0
		for index in sampled.size(): maximum = maxf(maximum,sampled[index].distance_to(reference[index]))
		check("Smooth varying input stays within 2 mm at %d/120 Hz"%hz,maximum<.002,{"matched_time_samples":sampled.size(),"maximum_cloth_difference_m":maximum,"tolerance_m":.002,"input":"3 s sinusoidal direction, speed, vertical speed and yaw; identical 30 Hz comparison times"})
	secondary.update_secondary(1.0/60,{"local_velocity":Vector3(8,0,12)})
	check("Every zero-mask anchor remains exactly fixed",secondary.rest_displacement(0)==Vector3.ZERO and secondary.rest_displacement(0,"hair")==Vector3.ZERO)
	check("Hem, brocade border and cloth use the same displacement field",mesh_node.get_surface_override_material(0).get_shader_parameter("secondary_offset") == material.get_shader_parameter("secondary_offset") and mesh_node.get_surface_override_material(3).get_shader_parameter("secondary_offset") == material.get_shader_parameter("secondary_offset"))
	mesh_node.rotation.y = PI/2
	secondary.update_secondary(1.0/60,{"local_velocity":Vector3(0,0,8)})
	var local_offset: Vector3 = material.get_shader_parameter("secondary_offset")
	check("Hero-local response converts into each mesh's coordinate basis",(mesh_node.global_basis*local_offset).distance_to(secondary.cloth_offset)<.000001)
	mesh_node.rotation.y = 0
	check("Mask field is continuous, clamped and finite",secondary.rest_displacement(-1)==Vector3.ZERO and secondary.rest_displacement(2)==secondary.cloth_offset and secondary.rest_displacement(NAN)==Vector3.ZERO and secondary.rest_displacement(.50001).distance_to(secondary.rest_displacement(.5))<.00001)
	var before: Dictionary = secondary.report()
	for unused in 30: secondary.update_secondary(.1,{"paused":true,"local_velocity":Vector3(50,50,50),"position":Vector3(100,0,0),"yaw":PI})
	check("Pause preserves positions, velocities, elapsed time and baseline",secondary.report() == before)
	secondary.update_secondary(1.0/60,{"local_velocity":Vector3(8,0,12)})
	check("Pause resume does not produce a catch-up reset",secondary.reset_count == before.reset_count and secondary.cloth_offset.distance_to(before.cloth_offset)<.01)
	var maximum_cloth := 0.0
	var maximum_hair := 0.0
	var finite := true
	for index in 2400:
		var delta: float = 1.0/[30.0,60.0,120.0][index%3]
		secondary.update_secondary(delta,{"local_velocity":Vector3(100 if index%2 else -100,90,-100),"yaw":float(index)*1.7,"grounded":index%3 == 0})
		maximum_cloth = maxf(maximum_cloth,secondary.cloth_offset.length())
		maximum_hair = maxf(maximum_hair,secondary.hair_offset.length())
		finite = finite and secondary.report().finite
	check("Adversarial turn, flight and oversized speed remain finite and capped",finite and maximum_cloth<=SECONDARY.CLOTH_LIMIT+.000001 and maximum_hair<=SECONDARY.HAIR_LIMIT+.000001,{"samples":2400,"maximum_cloth_m":maximum_cloth,"maximum_hair_m":maximum_hair})
	secondary.update_secondary(1.0/60,{"yaw":1e308})
	secondary.update_secondary(1.0/60,{"yaw":-1e308})
	var uniform: Vector3 = material.get_shader_parameter("secondary_offset")
	check("Opposite huge finite yaw inputs cannot overflow the spring or published uniform",secondary.report().finite and uniform.is_finite() and secondary.cloth_offset.length()<=SECONDARY.CLOTH_LIMIT+.000001)
	secondary.update_secondary(1.0/60,{"position":Vector3(100,0,0)})
	check("Teleport clears inherited inertia before rendering",secondary.cloth_offset == Vector3.ZERO and secondary.hair_offset == Vector3.ZERO and secondary.last_reason == "teleport")
	secondary.update_secondary(1.0/60,{"local_velocity":Vector3(0,0,8),"position":Vector3(100,0,0)})
	secondary.update_secondary(1.0/60,{"alive":false,"position":Vector3(100,0,0)})
	var dead_count: int = secondary.reset_count
	for unused in 30: secondary.update_secondary(1.0/60,{"alive":false,"position":Vector3(100,0,0)})
	check("Death rests cloth/hair and holds without repeated resets",secondary.cloth_offset == Vector3.ZERO and secondary.hair_offset == Vector3.ZERO and secondary.reset_count == dead_count)
	secondary.update_secondary(1.0/60,{"position":Vector3(100,0,0)})
	check("Respawn seeds a fresh stationary baseline",secondary.cloth_offset == Vector3.ZERO and secondary.hair_offset == Vector3.ZERO and secondary.last_reason == "death/respawn")
	for delta in [0.0,-.01,.10001,INF,NAN]:
		secondary.update_secondary(1.0/60,{"local_velocity":Vector3(0,0,8)})
		check("Invalid delta %s resets without catch-up"%str(delta),not secondary.update_secondary(delta,{}) and secondary.cloth_offset == Vector3.ZERO and secondary.hair_offset == Vector3.ZERO)
	for state in [{"local_velocity":Vector3(NAN,0,0)},{"position":Vector3(INF,0,0)},{"yaw":NAN},{"local_velocity":"bad"},{"yaw":Vector3.ZERO}]:
		check("Invalid input %s is rejected and finite"%str(state),not secondary.update_secondary(1.0/60,state) and secondary.report().finite)
	secondary.reset("ordinary practice reset")
	check("Explicit reset clears springs and the baseline",secondary.cloth_offset==Vector3.ZERO and secondary.hair_offset==Vector3.ZERO and secondary.elapsed==0 and secondary.last_reason=="ordinary practice reset")
	for unused in 60: secondary.update_secondary(1.0/60,{"local_velocity":Vector3(0,0,12)})
	var active_offset: float = secondary.cloth_offset.length()
	for unused in 240: secondary.update_secondary(1.0/60,{"local_velocity":Vector3(0,0,12),"reduced_motion":true})
	check("Reduced motion returns smoothly to neutral despite ongoing locomotion",active_offset>.01 and secondary.cloth_offset.length()<.000001 and secondary.hair_offset.length()<.000001)
	secondary.reset()
	for unused in 60: secondary.update_secondary(1.0/60,{"local_velocity":Vector3(0,0,8)})
	for unused in 240: secondary.update_secondary(1.0/60,{})
	check("Ordinary stop settles to rest without autonomous flutter",secondary.cloth_offset.length()<.000001 and secondary.hair_offset.length()<.000001)
	secondary.restore_materials()
	check("Unbind restores only this component's overrides",not secondary.configured and mesh_node.get_surface_override_material(0)==null and mesh_node.get_surface_override_material(1)==null and mesh_node.get_surface_override_material(2)==null and mesh_node.get_surface_override_material(3)==null)
	var passed := true
	for entry in checks: passed = passed and entry.passed
	var sources := {}
	for path in [get_script().resource_path,"res://scripts/rama_secondary_motion.gd","res://shaders/rama_secondary_cloth.gdshader"]: sources[path] = FileAccess.get_sha256(path)
	var file := FileAccess.open(output,FileAccess.WRITE)
	if file: file.store_string(JSON.stringify({"passed":passed,"checks":checks,"sources":sources,"scope":"Synthetic semantic-mask/material fixture and deterministic movement counterexamples. No actual hero deformation, rendering, GPU, physical cloth, hand contact or gameplay acceptance claim."},"\t")+"\n")
	else: passed = false
	for visual in fixtures: visual.free()
	quit(0 if passed else 1)
