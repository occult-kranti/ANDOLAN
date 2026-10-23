extends SceneTree
## Actual immutable primitive reuse against the retained pre-change builder.
## No imported scenes, renderer, audio, physics authority or performance claim.
const Builder = preload("res://scripts/traversal_landmarks.gd")
const Pool = preload("res://scripts/world_render_resources.gd")
const MAP := "res://assets/world/confluence-map.json"
const ORACLE := "res://docs/evidence/desktop-finish/continuation-oct18/W4-world-r1/baseline-traversal_landmarks.gd.txt"
const ORACLE_SHA256 := "ee070b0a4b1c0bb07ac645681e6ef3dcf0311adb88afe07ece3ecc75b4ab971b"
var checks: Array[Dictionary] = []
var report_path := ""
var baseline := false

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
		if arg == "--baseline": baseline = true
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name": label, "passed": passed, "details": detail})
	print("PASS " if passed else "FAIL ",label)

func hash_value(value: Variant) -> String:
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	h.update(var_to_bytes(value))
	return h.finish().hex_encode()

func material_state(material: Material) -> Dictionary:
	if material is ShaderMaterial:
		return {"class":"ShaderMaterial", "shader":material.shader.resource_path,
			"height":material.get_shader_parameter("deck_height"), "width":material.get_shader_parameter("deck_width")}
	var m := material as StandardMaterial3D
	return {"class":"StandardMaterial3D", "color":m.albedo_color, "roughness":m.roughness,
		"emission_enabled":m.emission_enabled, "emission":m.emission, "energy":m.emission_energy_multiplier}

func mesh_state(mesh: Mesh) -> Dictionary:
	var surfaces: Array = []
	for index in mesh.get_surface_count():
		surfaces.append({"arrays":hash_value(mesh.surface_get_arrays(index))})
	return {"class":mesh.get_class(), "aabb":mesh.get_aabb(), "surfaces":surfaces}

func ordered_path(node: Node, parent: Node) -> Array:
	var indices: Array = []
	while node != parent:
		indices.push_front(node.get_index())
		node = node.get_parent()
	return indices

func scene_state(parent: Node3D) -> Array:
	var rows: Array = []
	for n in parent.find_children("*", "Node3D", true, false):
		var row := {"path":ordered_path(n,parent), "name":n.get_class() if String(n.name).begins_with("@") else String(n.name), "class":n.get_class(), "transform":n.transform,
			"visible":n.visible, "metadata":{}}
		for key in n.get_meta_list(): row.metadata[key] = n.get_meta(key)
		if n is MeshInstance3D:
			row.mesh = mesh_state(n.mesh)
			row.material = material_state(n.material_override)
			row.cast_shadow = n.cast_shadow
		rows.append(row)
	return rows

func mesh_ids(parent: Node3D) -> Dictionary:
	var ids: Dictionary = {}
	for n in parent.find_children("*", "MeshInstance3D", true, false): ids[n.mesh.get_instance_id()] = true
	return ids

func material_ids(parent: Node3D) -> Dictionary:
	var ids: Dictionary = {}
	for n in parent.find_children("*", "MeshInstance3D", true, false): ids[n.material_override.get_instance_id()] = true
	return ids

func disjoint(a: Dictionary, b: Dictionary) -> bool:
	for key in a:
		if b.has(key): return false
	return true

func no_embedded_materials(parent: Node3D) -> bool:
	for n in parent.find_children("*", "MeshInstance3D", true, false):
		for index in n.mesh.get_surface_count():
			if n.mesh.surface_get_material(index) != null: return false
	return true

func matches_retained_report(report: Dictionary, retained: Dictionary) -> bool:
	# The default builder still produces the exact retained geometry and report
	# fields. Its only reviewed schema addition explicitly disables the opt-in
	# court. Compare the entire expected dictionary: no key/value is discarded.
	var expected: Dictionary = retained.duplicate(true)
	if not baseline:
		var marker: Variant = report.get("wind_court_pilot")
		if not marker is Dictionary or marker.size() != 1 or not marker.has("enabled"): return false
		if typeof(marker.enabled) != TYPE_BOOL or marker.enabled: return false
		expected["wind_court_pilot"] = {"enabled":false}
	return report == expected

# The accepted pilot owns merged ArrayMeshes with embedded palette bindings.
# Its explicit opt-in contract is separate from the unchanged legacy primitive
# rule above: cached/published legacy meshes still must have no materials.
func pilot_lod(parent: Node3D, detail: String) -> MeshInstance3D:
	return parent.get_node("TraversalRelics/sun-lift-west/WindCourt"+detail)

func pilot_palette_shared(near_: MeshInstance3D, mid_: MeshInstance3D) -> bool:
	if near_.material_override != null or mid_.material_override != null or near_.mesh.get_surface_count() != 3 or mid_.mesh.get_surface_count() != 3: return false
	for slot in range(3):
		if near_.get_surface_override_material(slot) != null or mid_.get_surface_override_material(slot) != null: return false
		if near_.mesh.surface_get_material(slot) == null or near_.mesh.surface_get_material(slot) != mid_.mesh.surface_get_material(slot): return false
	return true

func pilot_material_ids(parent: Node3D) -> Dictionary:
	var ids: Dictionary = {}
	for visual in parent.find_children("*", "MeshInstance3D", true, false):
		if visual.material_override != null: ids[visual.material_override.get_instance_id()] = true
		for slot in visual.mesh.get_surface_count():
			var material: Material = visual.mesh.surface_get_material(slot)
			if material != null: ids[material.get_instance_id()] = true
	return ids

func pilot_palette_state(parent: Node3D) -> Array:
	var result: Array = []
	for detail in ["Near","Mid"]:
		var visual := pilot_lod(parent,detail)
		var row: Array = []
		for slot in visual.mesh.get_surface_count(): row.append(material_state(visual.mesh.surface_get_material(slot)))
		result.append(row)
	return result

func check_pilot_resources(data: Dictionary) -> void:
	# Equivalent to the independent 14-case pilot resource probe; the main
	# source-before/after check below covers its final source-identity predicate.
	var first := Node3D.new()
	var second := Node3D.new()
	var third := Node3D.new()
	root.add_child(first)
	root.add_child(second)
	root.add_child(third)
	var builder = Builder.new()
	var other = Builder.new()
	var a: Dictionary = builder.build(first,data,{"wind_court_pilot":true})
	var b: Dictionary = other.build(second,data,{"wind_court_pilot":true})
	var near_a := pilot_lod(first,"Near")
	var mid_a := pilot_lod(first,"Mid")
	var near_b := pilot_lod(second,"Near")
	var mid_b := pilot_lod(second,"Mid")
	check("pilot retains exact near588 mid444 and three-surface budgets", a.wind_court_pilot.near_triangles == 588 and a.wind_court_pilot.mid_triangles == 444 and a.wind_court_pilot.architecture_surfaces_per_lod == 3 and a.mesh_instances == 221)
	check("pilot LODs use distinct merged meshes with exact shared three-material palette", near_a.mesh != mid_a.mesh and pilot_palette_shared(near_a,mid_a))
	check("independent pilot owns exact three-surface palette and report", pilot_palette_shared(near_b,mid_b) and a == b)
	check("pilot materials and geometry are disjoint across builders", disjoint(pilot_material_ids(first),pilot_material_ids(second)) and disjoint(mesh_ids(first),mesh_ids(second)))
	var initial := pilot_palette_state(first)
	var other_initial := pilot_palette_state(second)
	check("pilot surface values are deterministic across independent builds", initial == other_initial)
	var stone := near_a.mesh.surface_get_material(0) as ShaderMaterial
	var original_width: Variant = stone.get_shader_parameter("deck_width")
	stone.set_shader_parameter("deck_width",99.0)
	check("embedded palette mutation reaches own LOD without bleeding into another build", pilot_palette_state(first) != initial and pilot_palette_state(second) == other_initial and mid_a.mesh.surface_get_material(0).get_shader_parameter("deck_width") == 99.0)
	stone.set_shader_parameter("deck_width",original_width)
	check("restoring embedded palette mutation restores exact values", pilot_palette_state(first) == initial)
	var original_warm: Material = mid_a.mesh.surface_get_material(1)
	mid_a.mesh.surface_set_material(1,original_warm.duplicate())
	check("negative same-value duplicate breaks within-build palette sharing", not pilot_palette_shared(near_a,mid_a) and pilot_palette_state(first) == initial)
	mid_a.mesh.surface_set_material(1,original_warm)
	var original_b: Material = near_b.mesh.surface_get_material(0)
	near_b.mesh.surface_set_material(0,stone)
	mid_b.mesh.surface_set_material(0,stone)
	check("negative cross-build embedded alias is detected", not disjoint(pilot_material_ids(first),pilot_material_ids(second)))
	near_b.mesh.surface_set_material(0,original_b)
	mid_b.mesh.surface_set_material(0,original_b)
	check("restoring alias preserves exact own palette and independent ownership", pilot_palette_shared(near_a,mid_a) and pilot_palette_shared(near_b,mid_b) and disjoint(pilot_material_ids(first),pilot_material_ids(second)) and pilot_palette_state(second) == other_initial)
	var c: Dictionary = builder.build(third,data,{"wind_court_pilot":true})
	check("reused builder creates fresh pilot geometry and embedded materials", c == a and disjoint(mesh_ids(first),mesh_ids(third)) and disjoint(pilot_material_ids(first),pilot_material_ids(third)) and pilot_palette_state(third) == initial)
	var mesh_weak: WeakRef = weakref(near_a.mesh)
	var material_weak: WeakRef = weakref(stone)
	stone = null
	original_warm = null
	original_b = null
	near_a = null
	mid_a = null
	first.free()
	await process_frame
	check("freed pilot releases merged mesh and embedded palette without global retention", mesh_weak.get_ref() == null and material_weak.get_ref() == null)
	check("surviving pilot remains exact after peer teardown", pilot_palette_state(second) == other_initial and pilot_palette_shared(near_b,mid_b))
	second.free()
	third.free()
	builder = null
	other = null

func run() -> void:
	var inputs := ["res://scripts/traversal_landmarks.gd", "res://scripts/world_render_resources.gd", MAP, ORACLE, get_script().resource_path]
	var before: Dictionary = {}
	for path in inputs: before[path] = FileAccess.get_sha256(path)
	var old_script := GDScript.new()
	old_script.source_code = FileAccess.get_file_as_string(ORACLE)
	var old_ok := FileAccess.get_sha256(ORACLE) == ORACLE_SHA256 and old_script.reload() == OK
	check("retained original builder matches a7 Git source and parses", old_ok)
	if not old_ok: quit(1); return
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MAP)).traversal
	var old_parent := Node3D.new()
	var first := Node3D.new()
	var second := Node3D.new()
	root.add_child(old_parent)
	root.add_child(first)
	root.add_child(second)
	var original = old_script.new()
	var builder = old_script.new() if baseline else Builder.new()
	var other = old_script.new() if baseline else Builder.new()
	var old_report: Dictionary = original.build(old_parent, data)
	var first_report: Dictionary = builder.build(first, data)
	var second_report: Dictionary = other.build(second, data)
	var oracle_state := scene_state(old_parent)
	var first_state := scene_state(first)
	check("full manifest node topology geometry arrays transforms materials and metadata match retained original", first_state == oracle_state)
	check("independent builds produce deterministic full geometry and material state", scene_state(second) == first_state)
	check("public build report retains exact original fields plus explicit opt-in state", matches_retained_report(first_report,old_report) and matches_retained_report(second_report,old_report), {"report":first_report})
	var changed_count: Dictionary = first_report.duplicate(true)
	changed_count.mesh_instances += 1
	check("negative changed report count remains rejected", not matches_retained_report(changed_count,old_report))
	var changed_scope: Dictionary = first_report.duplicate(true)
	changed_scope.scope += " unreviewed scope"
	check("negative changed report scope remains rejected", not matches_retained_report(changed_scope,old_report))
	var extra_field: Dictionary = first_report.duplicate(true)
	extra_field["unreviewed_field"] = true
	check("negative unknown report field remains rejected", not matches_retained_report(extra_field,old_report))
	var wrong_pilots: Array[Dictionary] = []
	for marker in [{"enabled":true},{"enabled":0},{"enabled":"false"},{"enabled":null},{},{"enabled":false,"unreviewed":true},false,null]:
		var corrupted: Dictionary = first_report.duplicate(true)
		corrupted["wind_court_pilot"] = marker
		wrong_pilots.append(corrupted)
	if not baseline:
		var missing: Dictionary = first_report.duplicate(true)
		missing.erase("wind_court_pilot")
		wrong_pilots.append(missing)
	check("negative enabled missing or malformed pilot state remains rejected", wrong_pilots.all(func(report): return not matches_retained_report(report,old_report)))
	var count := first.find_children("*", "MeshInstance3D", true, false).size()
	check("all 238 visible landmark mesh instances retained", count == 238)
	check("238 formerly distinct primitive resources become exactly 13 shared resources", mesh_ids(old_parent).size() == 238 and mesh_ids(first).size() == 13, {"old_unique":mesh_ids(old_parent).size(), "current_unique":mesh_ids(first).size(), "instances":count})
	check("shared meshes never contain mutable material bindings", no_embedded_materials(first) and no_embedded_materials(second))
	check("independent builders do not share mutable materials or geometry", disjoint(material_ids(first),material_ids(second)) and disjoint(mesh_ids(first),mesh_ids(second)))
	check("builder adds no physics bodies colliders or lights", first.find_children("*", "CollisionObject3D", true, false).is_empty() and first.find_children("*", "CollisionShape3D", true, false).is_empty() and first.find_children("*", "Light3D", true, false).is_empty())
	var ember: MeshInstance3D = first.find_children("DiyaEmber", "MeshInstance3D", true, false)[0]
	var original_energy: float = ember.material_override.emission_energy_multiplier
	ember.material_override.emission_energy_multiplier = 99.0
	check("mutating one build material cannot bleed into another build", scene_state(second) == first_state and scene_state(first) != first_state)
	ember.material_override.emission_energy_multiplier = original_energy
	var old_transform := ember.transform
	ember.position.x += 1.0
	check("negative moved node is detected despite shared geometry", scene_state(first) != oracle_state and scene_state(second) == first_state)
	ember.transform = old_transform
	var old_mesh: Mesh = ember.mesh
	ember.mesh = old_mesh.duplicate()
	(ember.mesh as SphereMesh).radius += .01
	check("negative changed geometry resource is detected", scene_state(first) != oracle_state)
	ember.mesh = old_mesh
	old_mesh = null
	check("restoring negative controls restores exact geometry material and transform state", scene_state(first) == oracle_state)
	# Full parameter keys must distinguish subdivisions, orientation, caps and
	# very close floating values; none is rounded into a human-readable string.
	var pool := Pool.new()
	var box := pool.box(Vector3.ONE)
	check("equal complete parameters return actual same resource", pool.box(Vector3.ONE) == box)
	check("close dimensions cannot alias through rounded text keys", pool.box(Vector3(1.000001,1,1)) != box)
	check("box subdivision and flipped orientation are distinct", pool.box(Vector3.ONE,Vector3i(1,0,0)) != box and pool.box(Vector3.ONE,Vector3i.ZERO,true) != box)
	var disk := pool.cylinder(1,1,.1,24)
	check("cylinder caps height rings radii and segments participate in identity", pool.cylinder(1,1,.1,24,4,false) != disk and pool.cylinder(1,1,.1,24,5) != disk and pool.cylinder(.9,1,.1,24) != disk and pool.cylinder(1,1,.2,24) != disk and pool.cylinder(1,1,.1,25) != disk)
	var sphere := pool.sphere(.9,.9,12,6,true)
	check("sphere hemisphere rings radial segments height and orientation remain distinct", pool.sphere(.9,.9,12,6,false) != sphere and pool.sphere(.9,.9,12,7,true) != sphere and pool.sphere(.9,.9,13,6,true) != sphere and pool.sphere(.9,1,12,6,true) != sphere and pool.sphere(.9,.9,12,6,true,true) != sphere)
	var torus := pool.torus(.7,.92,24,6)
	check("torus radii rings segment count and orientation remain distinct", pool.torus(.71,.92,24,6) != torus and pool.torus(.7,.93,24,6) != torus and pool.torus(.7,.92,25,6) != torus and pool.torus(.7,.92,24,7) != torus and pool.torus(.7,.92,24,6,true) != torus)
	# A builder may be reused, but each new build must own mutable material state.
	var third := Node3D.new()
	root.add_child(third)
	var third_report: Dictionary = builder.build(third,data)
	check("reusing a builder starts a fresh per-build mesh and material pool", matches_retained_report(third_report,old_report) and disjoint(material_ids(first),material_ids(third)) and disjoint(mesh_ids(first),mesh_ids(third)) and scene_state(third) == oracle_state)
	var mesh_weak: WeakRef = weakref(ember.mesh)
	var material_weak: WeakRef = weakref(ember.material_override)
	ember = null
	first.free()
	await process_frame
	check("freed first world releases its resources without global retention", mesh_weak.get_ref() == null and material_weak.get_ref() == null)
	check("surviving independent world remains exact after peer teardown", scene_state(second) == first_state)
	old_parent.free()
	second.free()
	third.free()
	original = null
	builder = null
	other = null
	await process_frame
	await check_pilot_resources(data)
	var after: Dictionary = {}
	for path in inputs: after[path] = FileAccess.get_sha256(path)
	check("all input sources and manifest remain byte-identical during checks", before == after)
	var passed: bool = checks.all(func(row): return row.passed)
	var result := {"passed":passed,"baseline_original_builder":baseline,"count":checks.size(),"checks":checks,"source_before":before,"source_after":after,"scope":"Actual legacy full-manifest primitive/node/material equality against retained original builder, strict additive report schema, resource parameter separation, isolation, teardown and corruption controls. Separate opt-in pilot three-surface LOD palette ownership, exact budgets, mutation/alias controls, builder reuse and weak-reference teardown. No imports, 3D raster, physics-authority, draw-call/FPS, hardware or whole-map art acceptance."}
	if not report_path.is_empty(): FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result,"\t")+"\n")
	quit(0 if passed else 1)
