extends SceneTree
## Explicit opt-in three-surface LOD/palette checks, separate from legacy oracle.
const Builder=preload("res://scripts/traversal_landmarks.gd")
var checks: Array=[]
func _initialize()->void:call_deferred("run")
func check(label: String, passed: bool, details: Variant=null)->void:
	checks.append({"name":label,"passed":passed,"details":details})
func lod(parent: Node3D,detail: String)->MeshInstance3D:
	return parent.get_node("TraversalRelics/sun-lift-west/WindCourt"+detail)
func palette_shared(near_: MeshInstance3D,mid_: MeshInstance3D)->bool:
	if near_.material_override!=null or mid_.material_override!=null or near_.mesh.get_surface_count()!=3 or mid_.mesh.get_surface_count()!=3:return false
	for slot in range(3):
		if near_.mesh.surface_get_material(slot)==null or near_.mesh.surface_get_material(slot)!=mid_.mesh.surface_get_material(slot):return false
	return true
func material_ids(parent: Node3D)->Dictionary:
	var ids: Dictionary={}
	for mesh in parent.find_children("*","MeshInstance3D",true,false):
		if mesh.material_override:ids[mesh.material_override.get_instance_id()]=true
		for slot in mesh.mesh.get_surface_count():
			var material: Material=mesh.mesh.surface_get_material(slot)
			if material:ids[material.get_instance_id()]=true
	return ids
func mesh_ids(parent: Node3D)->Dictionary:
	var ids: Dictionary={}
	for mesh in parent.find_children("*","MeshInstance3D",true,false):ids[mesh.mesh.get_instance_id()]=true
	return ids
func disjoint(a: Dictionary,b: Dictionary)->bool:
	for key in a:
		if b.has(key):return false
	return true
func material_state(material: Material)->Array:
	if material is ShaderMaterial:return ["shader",material.shader.resource_path,material.get_shader_parameter("deck_height"),material.get_shader_parameter("deck_width")]
	return ["standard",material.albedo_color,material.roughness,material.emission_enabled,material.emission,material.emission_energy_multiplier]
func palette_state(parent: Node3D)->Array:
	var result: Array=[]
	for detail in ["Near","Mid"]:
		var visual:=lod(parent,detail)
		var row: Array=[]
		for slot in visual.mesh.get_surface_count():row.append(material_state(visual.mesh.surface_get_material(slot)))
		result.append(row)
	return result
func run()->void:
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json")).traversal
	var before:={"builder":FileAccess.get_sha256("res://scripts/traversal_landmarks.gd"),"pool":FileAccess.get_sha256("res://scripts/world_render_resources.gd"),"manifest":FileAccess.get_sha256("res://assets/world/confluence-map.json")}
	var first:=Node3D.new();var second:=Node3D.new();var third:=Node3D.new()
	root.add_child(first);root.add_child(second);root.add_child(third)
	var builder=Builder.new();var other=Builder.new()
	var a: Dictionary=builder.build(first,data,{"wind_court_pilot":true})
	var b: Dictionary=other.build(second,data,{"wind_court_pilot":true})
	var near_a:=lod(first,"Near");var mid_a:=lod(first,"Mid");var near_b:=lod(second,"Near");var mid_b:=lod(second,"Mid")
	check("pilot retains exact near588 mid444 and three-surface budgets",a.wind_court_pilot.near_triangles==588 and a.wind_court_pilot.mid_triangles==444 and a.wind_court_pilot.architecture_surfaces_per_lod==3 and a.mesh_instances==221)
	check("near and mid use distinct merged meshes with exact shared three-material palette",near_a.mesh!=mid_a.mesh and palette_shared(near_a,mid_a))
	check("independent pilot build also owns an exact three-surface palette",palette_shared(near_b,mid_b) and a==b)
	check("pilot materials and geometry are disjoint across builders",disjoint(material_ids(first),material_ids(second)) and disjoint(mesh_ids(first),mesh_ids(second)))
	var initial:=palette_state(first);var other_initial:=palette_state(second)
	check("pilot surface values are deterministic across independent builds",initial==other_initial)
	var stone:=near_a.mesh.surface_get_material(0) as ShaderMaterial
	var original_width: Variant=stone.get_shader_parameter("deck_width")
	stone.set_shader_parameter("deck_width",99.0)
	check("one build embedded palette mutation reaches its own LOD but not another build",palette_state(first)!=initial and palette_state(second)==other_initial and mid_a.mesh.surface_get_material(0).get_shader_parameter("deck_width")==99.0)
	stone.set_shader_parameter("deck_width",original_width)
	check("restoring embedded palette mutation restores exact values",palette_state(first)==initial)
	var original_warm: Material=mid_a.mesh.surface_get_material(1)
	mid_a.mesh.surface_set_material(1,original_warm.duplicate())
	check("negative same-value duplicate material breaks within-build sharing",not palette_shared(near_a,mid_a) and palette_state(first)==initial)
	mid_a.mesh.surface_set_material(1,original_warm)
	var original_b: Material=near_b.mesh.surface_get_material(0)
	near_b.mesh.surface_set_material(0,stone);mid_b.mesh.surface_set_material(0,stone)
	check("negative cross-build embedded alias is detected",not disjoint(material_ids(first),material_ids(second)))
	near_b.mesh.surface_set_material(0,original_b);mid_b.mesh.surface_set_material(0,original_b)
	check("restoring alias preserves own palette and independent ownership",palette_shared(near_a,mid_a) and palette_shared(near_b,mid_b) and disjoint(material_ids(first),material_ids(second)) and palette_state(second)==other_initial)
	var c: Dictionary=builder.build(third,data,{"wind_court_pilot":true})
	check("reusing builder creates fresh pilot geometry and embedded materials",c==a and disjoint(mesh_ids(first),mesh_ids(third)) and disjoint(material_ids(first),material_ids(third)) and palette_state(third)==initial)
	var mesh_weak: WeakRef=weakref(near_a.mesh);var material_weak: WeakRef=weakref(stone)
	stone=null;original_warm=null;original_b=null;near_a=null;mid_a=null
	first.free();await process_frame
	check("freed pilot releases merged mesh and embedded palette without global retention",mesh_weak.get_ref()==null and material_weak.get_ref()==null)
	check("surviving pilot remains exact after peer teardown",palette_state(second)==other_initial and palette_shared(near_b,mid_b))
	second.free();third.free();builder=null;other=null
	var after:={"builder":FileAccess.get_sha256("res://scripts/traversal_landmarks.gd"),"pool":FileAccess.get_sha256("res://scripts/world_render_resources.gd"),"manifest":FileAccess.get_sha256("res://assets/world/confluence-map.json")}
	check("all product sources remain unchanged",before==after)
	var passed:=checks.all(func(row):return row.passed)
	var report:={"passed":passed,"cases":checks.size(),"checks":checks,"source_before":before,"source_after":after,"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Independent opt-in pilot resource-identity/lifetime checks. Legacy238/13 oracle assertions are not relaxed. No rendering, physics, FPS or whole-map quality acceptance."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file:=FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			if file==null:quit(2);return
			file.store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"cases":checks.size()}));quit(0 if passed else 1)
