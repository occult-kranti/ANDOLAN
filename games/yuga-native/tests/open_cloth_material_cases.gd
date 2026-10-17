extends SceneTree
## Actual ShaderMaterial lifecycle counterexamples on a synthetic masked mesh.
const CANDIDATE := preload("res://art/open-art-wave/integration/cloth_candidate.gd")
const SECONDARY := preload("res://scripts/rama_secondary_motion.gd")
var checks: Array[Dictionary] = []
var fixtures: Array[Node] = []
var output := "/tmp/open-cloth-material-cases.json"
var verify_candidate_resource := false

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
		if argument == "--candidate-resource": verify_candidate_resource = true
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func texture(color: Color) -> ImageTexture:
	var image := Image.create(2,2,false,Image.FORMAT_RGBA8)
	image.fill(color)
	return ImageTexture.create_from_image(image)

func candidate() -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.resource_name = "Synthetic review cloth"
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.roughness = .87
	material.metallic = 0
	material.metallic_specular = .42
	material.albedo_color = Color(.15,.25,.75,1)
	material.albedo_texture = texture(Color(.7,.7,.9,1))
	material.roughness_texture = texture(Color(.8,.2,.1,1))
	material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	material.normal_enabled = true
	material.normal_scale = .6
	material.normal_texture = texture(Color(.5,.5,1,1))
	return material

func fixture(share_lods := true) -> Dictionary:
	var visual := Node3D.new()
	root.add_child(visual)
	fixtures.append(visual)
	var mesh := ArrayMesh.new()
	for label in ["Cobalt handwoven silk","Cobalt lotus brocade","Worked warm gold","Swept black hair","Natural lips"]:
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(0,1.5,0),Vector3(.2,.7,-.2),Vector3(-.2,.3,-.3)])
		arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.FORWARD,Vector3.FORWARD,Vector3.FORWARD])
		arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2.ZERO,Vector2.RIGHT,Vector2.ONE])
		arrays[Mesh.ARRAY_COLOR] = PackedColorArray([Color(1,1,1,0),Color(1,1,1,.5),Color.WHITE])
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
		var material := StandardMaterial3D.new()
		material.resource_name = label
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		material.albedo_color = Color(.2,.3,.5,1)
		material.roughness = .35
		material.normal_enabled = true
		material.normal_scale = .25
		material.normal_texture = texture(Color(.5,.5,1,1))
		mesh.surface_set_material(mesh.get_surface_count()-1,material)
	var near := MeshInstance3D.new()
	near.mesh = mesh
	visual.add_child(near)
	var secondary := SECONDARY.new()
	visual.add_child(secondary)
	var configured: bool = secondary.configure(visual)
	var meshes := [near]
	if share_lods:
		for unused in 2:
			var lod := MeshInstance3D.new()
			lod.mesh = mesh
			for surface in mesh.get_surface_count(): lod.set_surface_override_material(surface,near.get_surface_override_material(surface))
			visual.add_child(lod)
			meshes.append(lod)
	var binder := CANDIDATE.new()
	visual.add_child(binder)
	return {"visual":visual,"mesh":mesh,"meshes":meshes,"near":near,"secondary":secondary,"binder":binder,"configured":configured,"material":near.get_active_material(0)}

func snapshot(material: ShaderMaterial) -> Dictionary:
	var values := {}
	for property in material.shader.get_shader_uniform_list(): values[property.name] = material.get_shader_parameter(property.name)
	return values

func run() -> void:
	var unconfigured := CANDIDATE.new()
	check("Null visual rejects without allocation",not unconfigured.bind(null,candidate()) and not unconfigured.report().bound)
	var detached := Node3D.new()
	check("Detached visual rejects because lifecycle ownership is unavailable",not unconfigured.bind(detached,candidate()))
	detached.free()
	unconfigured.free()
	var base := fixture()
	var binder: Node = base.binder
	var material: ShaderMaterial = base.material
	var initial := snapshot(material)
	var masks: PackedByteArray = base.mesh.surface_get_arrays(0)[Mesh.ARRAY_COLOR].to_byte_array()
	var brocade := snapshot(base.near.get_active_material(1))
	var gold := snapshot(base.near.get_active_material(2))
	var hair := snapshot(base.near.get_active_material(3))
	var face: Material = base.near.get_active_material(4)
	var shader: Shader = material.shader
	var selected := candidate()
	check("Secondary fixture owns the intended material",base.configured and material.resource_name == CANDIDATE.TARGET_NAME)
	check("Shared three-LOD target binds one existing unique material",binder.bind(base.visual,selected) and binder.report().unique_materials == 1 and binder.report().surface_slots == 3,binder.report())
	check("Cloth PBR channels map into exact existing shader uniforms",material.get_shader_parameter("base_texture") == selected.albedo_texture and material.get_shader_parameter("rough_texture") == selected.roughness_texture and material.get_shader_parameter("normal_texture") == selected.normal_texture and material.get_shader_parameter("rough_channel") == Vector4(1,0,0,0) and material.get_shader_parameter("metallic_value") == 0.0 and material.get_shader_parameter("use_normal_texture") == true)
	check("Material identity shader masks mesh face and other cloth owners are preserved",base.near.get_active_material(0) == material and material.shader == shader and base.near.mesh == base.mesh and masks == base.mesh.surface_get_arrays(0)[Mesh.ARRAY_COLOR].to_byte_array() and snapshot(base.near.get_active_material(1)) == brocade and snapshot(base.near.get_active_material(2)) == gold and snapshot(base.near.get_active_material(3)) == hair and base.near.get_active_material(4) == face)
	var bound := snapshot(material)
	check("Same-candidate repeated binding is idempotent",binder.bind(base.visual,selected) and snapshot(material) == bound and binder.report().unique_materials == 1)
	var other := fixture(false)
	check("Bound component refuses a different visual without partial writes",not binder.bind(other.visual,selected) and snapshot(material) == bound)
	var different := candidate()
	different.roughness = .22
	check("Bound component refuses a changed candidate without partial writes",not binder.bind(base.visual,different) and snapshot(material) == bound)
	base.secondary.update_secondary(1.0/60,{"local_velocity":Vector3(4,0,12)})
	var offset: Vector3 = material.get_shader_parameter("secondary_offset")
	check("Secondary writer remains live while optional cloth maps are bound",offset.length() > 0 and material.get_shader_parameter("base_texture") == selected.albedo_texture)
	var restored: Dictionary = binder.unbind()
	var expected := initial.duplicate()
	expected.secondary_offset = offset
	check("Unbind restores every owned field and retains latest secondary offset",snapshot(material) == expected and restored.conflicts.is_empty() and restored.invalidated_materials.is_empty() and restored.restored_fields == bound.size()-1,restored)
	check("Repeated unbind performs no writes",binder.unbind().already_unbound and snapshot(material) == expected)
	check("Component can rebind after explicit rollback",binder.bind(base.visual,selected))
	material.set_shader_parameter("roughness_value",.8125)
	var external := snapshot(material)
	check("Foreign owned-field edit invalidates idempotent re-entry",not binder.bind(base.visual,selected) and snapshot(material) == external)
	var conflict: Dictionary = binder.unbind()
	check("Conditional rollback preserves foreign roughness and reports exact conflict",material.get_shader_parameter("roughness_value") == .8125 and material.get_shader_parameter("base_texture") == initial.base_texture and material.get_shader_parameter("secondary_offset") == offset and conflict.conflicts.size() == 1 and conflict.conflicts[0].uniform == "roughness_value",conflict)
	var invalid_candidates: Array[StandardMaterial3D] = []
	var unsupported := candidate(); unsupported.emission_enabled = true; invalid_candidates.append(unsupported)
	var uv_changed := candidate(); uv_changed.uv1_scale = Vector3(2,1,1); invalid_candidates.append(uv_changed)
	var bad_filter := candidate(); bad_filter.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST; invalid_candidates.append(bad_filter)
	var wrong_cull := candidate(); wrong_cull.cull_mode = BaseMaterial3D.CULL_BACK; invalid_candidates.append(wrong_cull)
	var missing_normal := candidate(); missing_normal.normal_texture = null; invalid_candidates.append(missing_normal)
	var bad_color := candidate(); bad_color.albedo_color = Color(NAN,1,1,1); invalid_candidates.append(bad_color)
	var alpha := candidate(); alpha.albedo_color = Color(1,1,1,.5); invalid_candidates.append(alpha)
	var custom_shader := candidate(); custom_shader.next_pass = StandardMaterial3D.new(); invalid_candidates.append(custom_shader)
	for index in invalid_candidates.size():
		var before := snapshot(material)
		check("Unsupported candidate %d rejects atomically"%index,not binder.bind(base.visual,invalid_candidates[index]) and snapshot(material) == before and not binder.report().bound,{"reason":binder.report().last_reason})
	var anisotropic := candidate()
	anisotropic.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	check("Anisotropic sampler request is an explicit reported linear conversion",binder.bind(base.visual,anisotropic) and binder.report().filter_conversion and material.shader == shader)
	binder.unbind()
	var atomic := fixture(false)
	var extra := MeshInstance3D.new()
	extra.mesh = atomic.mesh
	var wrong := ShaderMaterial.new()
	wrong.resource_name = CANDIDATE.TARGET_NAME
	wrong.shader = Shader.new()
	wrong.shader.code = "shader_type spatial; void fragment(){ALBEDO=vec3(1.0);}"
	extra.set_surface_override_material(0,wrong)
	atomic.visual.add_child(extra)
	var before_atomic := snapshot(atomic.material)
	check("Later unrecognized target shader rejects all earlier staged materials",not atomic.binder.bind(atomic.visual,selected) and snapshot(atomic.material) == before_atomic and extra.get_active_material(0) == wrong)
	var unswitched := fixture(false)
	unswitched.secondary.restore_materials()
	check("Authoring StandardMaterial target requires secondary ownership first",not unswitched.binder.bind(unswitched.visual,selected) and unswitched.near.get_surface_override_material(0) == null)
	var private_lod := fixture()
	var extra_private: ShaderMaterial = private_lod.material.duplicate(false)
	private_lod.meshes[1].set_surface_override_material(0,extra_private)
	check("Distinct LOD material instances bind once each",private_lod.binder.bind(private_lod.visual,selected) and private_lod.binder.report().unique_materials == 2 and private_lod.binder.report().surface_slots == 3)
	check("Every distinct LOD material rolls back",private_lod.binder.unbind().restored_fields == 30)
	var invalidated := fixture(false)
	invalidated.binder.bind(invalidated.visual,selected)
	var selected_values := snapshot(invalidated.material)
	invalidated.secondary.restore_materials()
	check("Withdrawn secondary owner cannot pass idempotent re-entry",not invalidated.binder.bind(invalidated.visual,selected) and snapshot(invalidated.material) == selected_values)
	var invalidation: Dictionary = invalidated.binder.unbind()
	check("Withdrawn secondary slot invalidates rollback without stale-material writes",invalidation.invalidated_materials.size() == 1 and snapshot(invalidated.material) == selected_values and invalidated.near.get_surface_override_material(0) == null,invalidation)
	var replaced_shader := fixture(false)
	replaced_shader.binder.bind(replaced_shader.visual,selected)
	replaced_shader.material.shader = wrong.shader
	var replaced_result: Dictionary = replaced_shader.binder.unbind()
	check("Foreign shader replacement is preserved and reported invalidated",replaced_result.invalidated_materials.size() == 1 and replaced_shader.material.shader == wrong.shader)
	var teardown := fixture(false)
	var teardown_before := snapshot(teardown.material)
	teardown.binder.bind(teardown.visual,selected)
	teardown.binder.free()
	check("Component exit disconnects and restores the secondary-owned material",snapshot(teardown.material) == teardown_before)
	teardown.visual.remove_child(teardown.near)
	teardown.near.free()
	fixtures.erase(teardown.visual)
	teardown.visual.free()
	var exiting := fixture(false)
	var exiting_before := snapshot(exiting.material)
	exiting.binder.bind(exiting.visual,selected)
	root.remove_child(exiting.visual)
	check("Visual tree exit disconnects and restores candidate fields",not exiting.binder.report().bound and snapshot(exiting.material) == exiting_before)
	# Removing the visual also exits its secondary owner, so explicitly release
	# remaining synthetic resources after checking the candidate's own callback.
	fixtures.erase(exiting.visual)
	exiting.visual.free()
	var preserved := fixture(false)
	var preserved_material: ShaderMaterial = preserved.material
	var authored_motif := texture(Color(.8,.55,.08,1))
	var authored_color := Color(.08,.15,.34,1)
	preserved_material.set_shader_parameter("base_texture",authored_motif)
	preserved_material.set_shader_parameter("base_color",authored_color)
	preserved_material.set_shader_parameter("use_base_texture",true)
	var preserved_before := snapshot(preserved_material)
	var preservation_bound: bool = preserved.binder.bind(preserved.visual,selected,true)
	var preservation_report: Dictionary = preserved.binder.report()
	check("Preserve-albedo profile owns twelve fields and retains authored indigo gold map exactly",preservation_bound and preservation_report.preserve_albedo and preservation_report.appearance_policy == "preserve-authored-albedo-surface-only" and preservation_report.touched_fields.size() == 12 and not preservation_report.touched_fields.has("base_color") and not preservation_report.touched_fields.has("base_texture") and not preservation_report.touched_fields.has("use_base_texture") and preserved_material.get_shader_parameter("base_color") == authored_color and preserved_material.get_shader_parameter("base_texture") == authored_motif and preserved_material.get_shader_parameter("use_base_texture") == true,preservation_report)
	var alias_candidate := selected.duplicate(false) as StandardMaterial3D
	alias_candidate.albedo_color = Color(.9,.1,.1,1)
	alias_candidate.albedo_texture = authored_motif
	var preserved_bound := snapshot(preserved_material)
	check("Aliased candidate maps and changed unused albedo are idempotent without candidate mutation",preserved.binder.bind(preserved.visual,alias_candidate,true) and snapshot(preserved_material) == preserved_bound and alias_candidate.roughness_texture == selected.roughness_texture and alias_candidate.normal_texture == selected.normal_texture and selected.albedo_color == Color(.15,.25,.75,1) and selected.albedo_texture != authored_motif)
	check("Profile replacement requires unbind even with the same candidate",not preserved.binder.bind(preserved.visual,selected,false) and snapshot(preserved_material) == preserved_bound and preserved.binder.report().preserve_albedo)
	preserved.secondary.update_secondary(1.0/60,{"local_velocity":Vector3(3,0,9)})
	var preserved_offset: Vector3 = preserved_material.get_shader_parameter("secondary_offset")
	var foreign_color := Color(.11,.22,.33,1)
	preserved_material.set_shader_parameter("base_color",foreign_color)
	preserved_material.set_shader_parameter("use_base_texture",false)
	preserved_material.set_shader_parameter("roughness_value",.9375)
	var preservation_rollback: Dictionary = preserved.binder.unbind()
	check("Preserved profile rollback keeps foreign albedo offset and owned-field conflict",preserved_offset.length() > 0 and preserved_material.get_shader_parameter("secondary_offset") == preserved_offset and preserved_material.get_shader_parameter("base_color") == foreign_color and preserved_material.get_shader_parameter("base_texture") == authored_motif and preserved_material.get_shader_parameter("use_base_texture") == false and preserved_material.get_shader_parameter("roughness_value") == .9375 and preserved_material.get_shader_parameter("normal_texture") == preserved_before.normal_texture and preservation_rollback.restored_fields == 11 and preservation_rollback.conflicts.size() == 1 and preservation_rollback.conflicts[0].uniform == "roughness_value" and preservation_rollback.appearance_policy == "preserve-authored-albedo-surface-only" and preserved.binder.report().appearance_policy == "unbound",preservation_rollback)
	var before_legacy_rebind := snapshot(preserved_material)
	var legacy_rebound: bool = preserved.binder.bind(preserved.visual,selected)
	var legacy_full_color: bool = preserved_material.get_shader_parameter("base_color") == selected.albedo_color and preserved_material.get_shader_parameter("base_texture") == selected.albedo_texture
	var reverse_profile_refused: bool = not preserved.binder.bind(preserved.visual,selected,true)
	var legacy_policy: String = preserved.binder.report().appearance_policy
	var legacy_rollback: Dictionary = preserved.binder.unbind()
	check("Explicit unbind permits legacy full-albedo rebind and exact subsequent restore",legacy_rebound and legacy_full_color and reverse_profile_refused and legacy_policy == "candidate-albedo-and-surface" and legacy_rollback.restored_fields == 15 and legacy_rollback.conflicts.is_empty() and snapshot(preserved_material) == before_legacy_rebind)
	if verify_candidate_resource:
		var shipped := load(CANDIDATE.CANDIDATE_PATH) as StandardMaterial3D
		var actual := fixture(false)
		check("Committed cloth candidate validates and records its exact source digest",is_instance_valid(shipped) and actual.binder.bind(actual.visual,shipped) and actual.binder.report().candidate_sha256 == FileAccess.get_sha256(CANDIDATE.CANDIDATE_PATH) and not actual.binder.report().candidate_sha256.is_empty(),actual.binder.report())
		actual.binder.unbind()
	var passed := true
	for entry in checks: passed = passed and entry.passed
	var sources := {}
	for path in [get_script().resource_path,"res://art/open-art-wave/integration/cloth_candidate.gd","res://scripts/rama_secondary_motion.gd","res://shaders/rama_secondary_cloth.gdshader"]: sources[path] = FileAccess.get_sha256(path)
	var file := FileAccess.open(output,FileAccess.WRITE)
	if file: file.store_string(JSON.stringify({"passed":passed,"checks":checks,"sources":sources,"scope":"Synthetic actual ShaderMaterial/ArrayMesh/secondary-motion lifecycle, rollback and counterexamples. Separate renderer evidence is required for the current hero maps and appearance. No art, human feel, GPU, real-time performance or production promotion claim."},"\t")+"\n")
	else: passed = false
	for visual in fixtures: visual.free()
	quit(0 if passed else 1)
