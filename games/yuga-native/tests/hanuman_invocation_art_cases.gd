extends SceneTree
## Read actual cue geometry, UV atlas assignments and pooled resource lifetimes.

const Effects := preload("res://scripts/hanuman_trial_effects.gd")
const ORIGIN := Vector3(1.0, 0, 2.0)
const SECTOR := {"kind": "sector", "origin": ORIGIN, "center": ORIGIN, "forward": Vector3.RIGHT,
	"range_m": 5.0, "half_angle_cos": .55}
const MOVE := {"kind": "movement", "origin": ORIGIN, "center": ORIGIN + Vector3.FORWARD * 6.0, "forward": Vector3.FORWARD}
const DISK := {"kind": "disk", "origin": ORIGIN, "center": ORIGIN + Vector3.FORWARD * 6.0, "forward": Vector3.FORWARD, "radius_m": 7.0}
const CASES := [
	["vajra_gada", SECTOR, "GadaSolarArc", 2],
	["vajra_kavacha", SECTOR, "WardCanopy", 2],
	["maruti_udayana", MOVE, "VaultFeatherTrail", 3],
	["lanka_dahan", SECTOR, "EmberField", 2],
	["mountain_pulse", DISK, "MountainPayload", 4],
]

var _effects: Node3D
var _checks: Array[Dictionary] = []
var _cast_id := 0
var _sequence := 0
var _generation := 1
var _shared_mesh: Mesh
var _shared_texture: Texture2D
var _phase_materials: Dictionary = {}
var _release_geometry: Dictionary = {}


func _initialize() -> void:
	call_deferred("_run")


func _assert(label: String, passed: bool) -> void:
	_checks.append({"name": label, "passed": passed})
	if not passed:
		printerr("FAIL ", label)


func _emit(kind: String, case: Array, cast_id: int, receipts: Array = []) -> bool:
	_sequence += 1
	return _effects.consume_event({"schema": 1, "hero_id": "hanuman", "kind": kind, "generation": _generation,
		"event_seq": _sequence, "cast_id": cast_id, "ability_id": case[0], "geometry": case[1], "receipts": receipts,
		"timing": {"windup_s": .40, "travel_s": .0 if case[1] == SECTOR else .45, "recovery_s": .5,
			"active_s": 2.0 if case[0] == "lanka_dahan" else 0.0}})


func _begin(case: Array) -> Node3D:
	_cast_id += 1
	if not _emit("begin", case, _cast_id):
		return null
	return _effects.get_node_or_null("Cue%d" % _cast_id)


func _stamp_valid(stamp: MeshInstance3D, case: Array, column: int, row: int) -> bool:
	if stamp == null or not stamp.visible or stamp.get_meta("art_phase", -1) != column:
		return false
	var material := stamp.material_override as ShaderMaterial
	if material == null or material.get_shader_parameter("atlas_cell") != Vector2(column, row):
		return false
	if _shared_mesh == null:
		_shared_mesh = stamp.mesh
		_shared_texture = material.get_shader_parameter("painted_masks")
	_phase_materials[Vector2i(column, row)] = material
	return stamp.mesh == _shared_mesh and _shared_texture != null and material.get_shader_parameter("painted_masks") == _shared_texture


func _within_shape(stamp: MeshInstance3D, geometry: Dictionary) -> bool:
	if stamp == null:
		return false
	if geometry.kind == "movement":
		var offset: Vector3 = geometry.center - geometry.origin
		var from: Vector3 = stamp.global_position - geometry.origin
		var axis := Vector2(offset.x, offset.z).normalized()
		var traveled := Vector2(from.x, from.z).dot(axis)
		return (traveled - stamp.scale.z >= 0.0 and traveled + stamp.scale.z <= offset.length())
	for corner in [Vector3(-1, 0, -1), Vector3(-1, 0, 1), Vector3(1, 0, -1), Vector3(1, 0, 1)]:
		var point: Vector3 = stamp.transform * corner
		var radius_vector := Vector2(point.x, point.z)
		if geometry.kind == "disk":
			if radius_vector.length() >= geometry.radius_m:
				return false
		elif radius_vector.length() >= geometry.range_m or radius_vector.normalized().y < geometry.half_angle_cos:
			return false
	return true


func _visible_mesh_count(group: Node3D) -> int:
	var count := 0
	for child in group.get_children(true):
		if child is MeshInstance3D and child.is_visible_in_tree():
			count += 1
		elif child is Node3D:
			count += _visible_mesh_count(child)
	return count


func _one(case: Array, row: int) -> void:
	var cue := _begin(case)
	var stamp: MeshInstance3D = cue.get_node_or_null("InvocationMark") if cue != null else null
	_assert(case[0] + " windup uses the correct painted mark within its footprint",
		_stamp_valid(stamp, case, 0, row) and _within_shape(stamp, case[1]))
	_assert(case[0] + " accepted release selects its own three-dimensional silhouette",
		_emit("release", case, _cast_id) and cue.has_node(case[2]) and cue.get_node(case[2]).get_child_count() == case[3] and
		_stamp_valid(stamp, case, 1, row) and _within_shape(stamp, case[1]))
	_release_geometry[case[0]] = _visible_mesh_count(cue)
	if case[0] == "mountain_pulse":
		var payload: Node3D = cue.get_node("MountainPayload")
		var stone: MeshInstance3D = payload.get_node_or_null("PaintedMountain")
		_assert("one opaque 24-triangle stone falls with the contour meshes",
			stone != null and stone.mesh.surface_get_array_len(0) == 72 and payload.visible)
		_effects._process(.45)
	var receipts: Array = [{"position": ORIGIN, "effects": ["shield"], "shield_after": 48.0}] if row == 1 else []
	_assert(case[0] + " accepts one impact and retains the shared art node", _emit("impact", case, _cast_id, receipts) and
		not _emit("impact", case, _cast_id, receipts) and cue.get_node("InvocationMark") == stamp)
	if case[0] == "maruti_udayana":
		_assert("movement acceptance does not produce a landing burst or ground timestamp",
			_effects.report().ground_field.active == 0 and not cue.has_node("MountainImpact"))
	if case[0] == "vajra_gada":
		_assert("one-frame combat resolution still leaves time to show the crescent", stamp.get_meta("art_phase") == 1)
	_effects._process(.105)
	_assert(case[0] + " resolves to its distinct painted impact frame", _stamp_valid(stamp, case, 2, row) and _within_shape(stamp, case[1]))
	_assert(case[0] + " cancel hides the whole cast in the same frame", _emit("cancel", case, _cast_id) and not cue.visible and _effects.report().ground_field.active == 0)


func _run() -> void:
	_effects = Effects.new()
	root.add_child(_effects)
	_effects.set_process(false)
	_effects.set_options({"volume": 0.0})
	for row in CASES.size():
		_one(CASES[row], row)
	_assert("one 384×640 packed texture with fifteen shared phase materials",
		_shared_texture != null and _shared_texture.get_size() == Vector2(384, 640) and _phase_materials.size() == 15)
	var first := _begin(CASES[0])
	var first_id := _cast_id
	var second := _begin(CASES[0])
	var second_id := _cast_id
	_assert("simultaneous casts share mark materials and mesh but retain private state",
		first.get_node("InvocationMark").material_override == second.get_node("InvocationMark").material_override and
		_emit("release", CASES[0], first_id) and
		first.get_node("InvocationMark").material_override != second.get_node("InvocationMark").material_override)
	_effects.set_options({"volume": 0.0, "reduced_effects": true})
	_effects._process(.1)
	_assert("reduced effects immediately keep exact boundary and suppress textured art",
		not first.get_node("InvocationMark").visible and first.get_child(0).visible and not first.get_node("GadaSolarArc").visible)
	_assert("cancelling one concurrent cast does not hide the other",
		_emit("cancel", CASES[0], first_id) and not first.visible and second.visible)
	_generation += 1
	_assert("reset retires all old marks and rejects stale impacts",
		_emit("reset", CASES[0], 0) and not second.visible and not _emit("impact", CASES[0], second_id))
	var reduced := _begin(CASES[4])
	_assert("reduced mountain still telegraphs and resolves without painted extras",
		reduced.get_node_or_null("InvocationMark") == null and _emit("release", CASES[4], _cast_id)
		and not reduced.has_node("MountainPayload") and _emit("impact", CASES[4], _cast_id)
		and not reduced.has_node("MountainImpact"))
	_assert("the five sampled releases use at most seven visible cue meshes each",
		_release_geometry.values().all(func(count): return count <= 7))
	var audio_paths: Dictionary = {}
	for case in CASES:
		var stream: AudioStream = _effects._style[case[0]].stream
		audio_paths[case[0]] = stream.resource_path if stream != null else ""
	var mountain_impact: AudioStream = _effects._style.mountain_pulse.impact_stream
	audio_paths["mountain_impact"] = mountain_impact.resource_path if mountain_impact != null else ""
	_assert("all six original trial WAVs load through the real presentation profile",
		audio_paths.keys().all(func(id): return audio_paths[id] == "res://assets/audio/hanuman-trial/%s.wav" % id))
	var passed := _checks.filter(func(check): return check.passed).size()
	var sources: Dictionary = {}
	for resource_path in [get_script().resource_path, "res://scripts/hanuman_trial_effects.gd", "res://scripts/hanuman_invocation_art.gd",
			"res://shaders/hanuman_invocation_mark.gdshader", "res://assets/design/hanuman-presentation.json",
			"res://assets/vfx/hanuman-invocation-masks.png"] + audio_paths.values():
		sources[resource_path] = FileAccess.get_sha256(resource_path)
	var result := {"passed": passed, "failed": _checks.size() - passed, "checks": _checks,
		"release_visible_meshes": _release_geometry, "audio_paths": audio_paths, "sources": sources}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var out := FileAccess.open(argument.trim_prefix("--report="), FileAccess.WRITE)
			if out != null:
				out.store_string(JSON.stringify(result, "  ") + "\n")
	print("YUGA_HANUMAN_INVOCATION_ART ", JSON.stringify(result))
	_effects.queue_free()
	await process_frame
	await process_frame
	_phase_materials.clear()
	_shared_mesh = null
	_shared_texture = null
	quit(0 if passed == _checks.size() else 1)
