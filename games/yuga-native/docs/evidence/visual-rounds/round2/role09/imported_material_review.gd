extends SceneTree
## R2-09 independent checks against the actual imported hero and material owners.
const Finish = preload("res://scripts/rama_surface_finish.gd")
const Calibration = preload("res://scripts/rama_surface_materials.gd")
const Secondary = preload("res://scripts/rama_secondary_motion.gd")
var checks: Array[Dictionary] = []
var report_path := ""
var material_rows: Array[Dictionary] = []
func check(label: String, ok: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":ok,"details":details})
	print("PASS " if ok else "FAIL ", label)
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
	call_deferred("_run")
func slots(node: Node, out: Array) -> void:
	if node is MeshInstance3D and node.mesh:
		for s in node.mesh.get_surface_count(): out.append({"mesh":node,"surface":s,"material":node.get_active_material(s)})
	for child in node.get_children(): slots(child,out)
func stored(mat: Resource) -> Dictionary:
	var values := {}
	for p in mat.get_property_list():
		if int(p.usage) & PROPERTY_USAGE_STORAGE: values[p.name] = mat.get(p.name)
	return values
func _run() -> void:
	var scene: PackedScene = load("res://assets/heroes/rama-hero.glb")
	var visual: Node3D = scene.instantiate()
	var other: Node3D = scene.instantiate()
	root.add_child(visual); root.add_child(other)
	var source_slots := []; var other_slots := []
	slots(visual,source_slots); slots(other,other_slots)
	var originals := {}; var skin_slots := []
	for slot in source_slots:
		var mat: Material = slot.material
		originals[mat.get_instance_id()] = {"mat":mat,"stored":stored(mat)}
		if mat.resource_name == "Rama warm skin": skin_slots.append(slot)
	check("Actual near import has separate face and body skin slots",skin_slots.size() == 2,{"count":skin_slots.size()})
	var imported_skin: StandardMaterial3D = skin_slots[0].material
	var imported_image := imported_skin.roughness_texture.get_image()
	var sample := imported_image.get_pixel(256,256)
	check("Actual imported authored roughness selects GREEN",imported_skin.roughness_texture_channel == BaseMaterial3D.TEXTURE_CHANNEL_GREEN and sample.r > .99 and sample.g > .50 and sample.g < .56,{"channel":imported_skin.roughness_texture_channel,"rgba":str(sample),"mipmaps":imported_image.has_mipmaps()})
	var calibration = Calibration.new(); visual.add_child(calibration)
	var secondary = Secondary.new(); visual.add_child(secondary)
	var finish = Finish.new(); visual.add_child(finish)
	check("Actual imported calibration and secondary binding succeed",calibration.configure(visual) and secondary.configure(visual))
	var calibrated := []
	for slot in source_slots: calibrated.append(slot.mesh.get_active_material(slot.surface))
	check("Actual imported finish public API succeeds",finish.configure(visual),finish.report())
	var skin_ok := true
	for slot in skin_slots:
		var before: StandardMaterial3D = slot.material
		var active: StandardMaterial3D = slot.mesh.get_active_material(slot.surface)
		var img := active.roughness_texture.get_image()
		var row := {"mesh":str(slot.mesh.name),"channel":active.roughness_texture_channel,"roughness":active.roughness,"normal_scale":active.normal_scale,"mipmaps":img.has_mipmaps(),"mipmap_count":img.get_mipmap_count(),"texture":active.roughness_texture.resource_path,"sss":active.subsurf_scatter_enabled,"sss_strength":active.subsurf_scatter_strength,"specular":active.metallic_specular}
		material_rows.append(row)
		skin_ok = skin_ok and active.roughness_texture_channel == BaseMaterial3D.TEXTURE_CHANNEL_RED and active.roughness == 1.0 and active.albedo_texture == before.albedo_texture and active.albedo_color == before.albedo_color and active.normal_texture == before.normal_texture and active.normal_enabled == before.normal_enabled and active.normal_scale == before.normal_scale and active.uv1_scale == before.uv1_scale and active.uv1_offset == before.uv1_offset
	check("Actual face/body finish binds RED and preserves authored palette normal and UV",skin_ok)
	var source_same := true
	for record in originals.values(): source_same = source_same and stored(record.mat) == record.stored
	for slot in other_slots: source_same = source_same and slot.mesh.get_active_material(slot.surface) == slot.material and slot.mesh.get_surface_override_material(slot.surface) == null
	check("Both imported-source resources and second actual hero remain untouched",source_same)
	var competitor = Finish.new(); visual.add_child(competitor)
	check("Second owner cannot claim actual finished hero",not competitor.configure(visual))
	competitor.free()
	var active_slots := []; slots(visual,active_slots)
	var stable := true
	for unused in 3:
		stable = stable and finish.configure(visual)
		for slot in active_slots: stable = stable and slot.mesh.get_active_material(slot.surface) == slot.material
	check("Repeated actual configure keeps all imported active material identities",stable)
	var released: Dictionary = finish.release()
	var restored: bool = released.conflicts.is_empty()
	for i in source_slots.size(): restored = restored and source_slots[i].mesh.get_active_material(source_slots[i].surface) == calibrated[i]
	check("Release restores every actual pre-finish material by identity",restored,released)
	check("Repeated release clears ownership without further restores",finish.release().restored_slots == 0 and finish.report().standard_materials == 0 and finish.report().secondary_materials == 0)
	finish.configure(visual)
	var moved: MeshInstance3D = skin_slots[0].mesh
	var old_parent: Node = moved.get_parent()
	var finish_material: Material = moved.get_active_material(skin_slots[0].surface)
	moved.reparent(other)
	check("Moving actual face outside visual is detected",not finish.configure(visual))
	var transfer: Dictionary = finish.release()
	check("Release retains transferred actual face appearance",transfer.invalidated > 0 and moved.get_active_material(skin_slots[0].surface) == finish_material,transfer)
	moved.reparent(old_parent)
	for i in source_slots.size(): source_slots[i].mesh.set_surface_override_material(source_slots[i].surface,calibrated[i])
	finish.configure(visual)
	visual.remove_child(finish)
	var owner_exit_ok: bool = not finish.configured
	for i in source_slots.size(): owner_exit_ok = owner_exit_ok and source_slots[i].mesh.get_active_material(source_slots[i].surface) == calibrated[i]
	check("Owner teardown restores all actual material identities",owner_exit_ok)
	visual.add_child(finish); finish.configure(visual)
	root.remove_child(visual)
	check("Actual visual tree exit releases ownership",not finish.configured)
	visual.free(); other.free()
	var ok := true
	for c in checks: ok = ok and c.passed
	var report := {"task":"R2-09","passed":ok,"checks":checks,"material_rows":material_rows,"engine":Engine.get_version_info().string,"hero_sha256":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb"),"finish_sha256":FileAccess.get_sha256("res://scripts/rama_surface_finish.gd"),"script_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Actual imported hero channel, preservation, isolation and lifecycle checks; no renderer, image or performance acceptance"}
	if not report_path.is_empty():
		var f := FileAccess.open(report_path,FileAccess.WRITE)
		if f: f.store_string(JSON.stringify(report,"\t")+"\n")
		else: ok = false
	quit(0 if ok else 1)
