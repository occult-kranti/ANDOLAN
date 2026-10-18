extends SceneTree
## Multi-surface ownership adversaries; actual imported groom checked separately.
const SECONDARY := preload("res://scripts/rama_secondary_motion.gd")
var checks: Array[Dictionary] = []
var output := "/tmp/rama-secondary-lifecycle.json"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)
func create(margin := .03) -> Dictionary:
	var visual := Node3D.new()
	var mesh := ArrayMesh.new()
	for material_name in ["Cobalt handwoven silk","Swept black hair"]:
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3.ZERO,Vector3.RIGHT,Vector3.UP])
		arrays[Mesh.ARRAY_COLOR] = PackedColorArray([Color(1,1,1,0),Color(1,1,1,.5),Color.WHITE])
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var material := StandardMaterial3D.new()
		material.resource_name = material_name
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		mesh.surface_set_material(mesh.get_surface_count()-1,material)
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.extra_cull_margin = margin
	visual.add_child(node)
	root.add_child(visual)
	var original: float = node.extra_cull_margin
	var owner := SECONDARY.new()
	visual.add_child(owner)
	assert(owner.configure(visual))
	return {"visual":visual,"mesh":node,"owner":owner,"original":original,"applied":node.extra_cull_margin}
func restored(f: Dictionary) -> bool:
	return f.mesh.get_surface_override_material(0) == null and f.mesh.get_surface_override_material(1) == null
func run() -> void:
	var f := create()
	check("one cull-margin record for a two-surface mesh",f.owner._bindings.size()==2 and f.owner._cull_margins.size()==1)
	check("bounded margin installed",is_equal_approx(f.applied,.08))
	f.owner.restore_materials()
	check("unchanged owned margin and both surfaces restore",f.mesh.extra_cull_margin==f.original and restored(f))
	f.mesh.extra_cull_margin = .5
	f.owner.restore_materials()
	check("repeated restore cannot clobber later margin",f.mesh.extra_cull_margin==.5 and restored(f))
	f.visual.free()
	for value in [.5,.04]:
		f = create()
		f.mesh.extra_cull_margin = value
		var exact: float = f.mesh.extra_cull_margin
		f.owner.restore_materials()
		check("external margin %s survives with owned materials restored"%value,f.mesh.extra_cull_margin==exact and restored(f))
		f.visual.free()
	f = create(.5)
	f.owner.restore_materials()
	check("preexisting large margin retained",f.mesh.extra_cull_margin==f.original and restored(f))
	f.visual.free()
	f = create()
	var foreign := StandardMaterial3D.new()
	f.mesh.set_surface_override_material(0,foreign)
	f.owner.restore_materials()
	check("foreign surface and its conservative mesh margin survive",f.mesh.get_surface_override_material(0)==foreign and f.mesh.get_surface_override_material(1)==null and f.mesh.extra_cull_margin==f.applied)
	f.visual.free()
	f = create()
	var replacement := BoxMesh.new()
	f.mesh.mesh = replacement
	f.mesh.set_surface_override_material(0,foreign)
	f.owner.restore_materials()
	check("replacement mesh with fewer surfaces survives",f.mesh.mesh==replacement and f.mesh.get_surface_override_material(0)==foreign and f.mesh.extra_cull_margin==f.applied)
	f.visual.free()
	for changed in [false,true]:
		f = create()
		if changed: f.mesh.extra_cull_margin = .5
		f.owner.free()
		check("owner disposal restores only owned margin; external=%s"%changed,f.mesh.extra_cull_margin==(.5 if changed else f.original) and restored(f))
		f.visual.free()
	f = create()
	f.mesh.free()
	f.owner.restore_materials()
	check("destroyed mesh teardown clears state safely",not f.owner.configured and f.owner._bindings.is_empty() and f.owner._cull_margins.is_empty())
	f.visual.free()
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_sha256":FileAccess.get_sha256("res://scripts/rama_secondary_motion.gd"),"scope":"Synthetic multi-surface lifecycle ownership adversaries. No rendering, import or response tuning."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if result.passed else 1)
