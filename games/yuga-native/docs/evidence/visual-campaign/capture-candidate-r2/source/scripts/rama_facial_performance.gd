extends Node
## Presentation-only performance for authored small eyelid meshes.
## Never scales an eye, warps a face in a shader, or writes the Skeleton3D.
const REQUIRED_SHAPES := ["rama_blink_left", "rama_blink_right"]
const HALF_SHAPES := ["rama_blink_half_left", "rama_blink_half_right"]
const MAX_FACE_VERTICES := 8000
const MAX_DELTA := .1
const BLINK_INTERVALS := [3.15, 4.20, 3.60, 5.10, 3.85]
const BLINK_CLOSE := .055
const BLINK_HOLD := .025
const BLINK_OPEN := .110
const OWNER_META := &"rama_facial_performance_owner"

var configured := false
var elapsed := 0.0
var blink_index := 0
var blink_clock := 0.0
var effort := 0.0
var defeat_age := 0.0
var rejected_states := 0
var reset_count := 0
var last_reason := ""
var _alive := true
var _defeat_start := Vector2.ZERO
var _mesh: MeshInstance3D
var _indices := {}
var _weights := {"rama_blink_left":0.0,"rama_blink_right":0.0}
var _have_half := false

func _collect(node: Node, result: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh: result.append(node)
	for child in node.get_children(): _collect(child,result)

func configure(visual: Node3D) -> bool:
	if configured or not is_instance_valid(visual): return false
	var meshes: Array[MeshInstance3D] = []
	_collect(visual,meshes)
	var candidates: Array[MeshInstance3D] = []
	for candidate in meshes:
		if not candidate.mesh is ArrayMesh: continue
		var names := []
		for index in candidate.mesh.get_blend_shape_count(): names.append(String(candidate.mesh.get_blend_shape_name(index)))
		if REQUIRED_SHAPES.all(func(shape): return names.has(shape)): candidates.append(candidate)
	# Ambiguous duplicate faces and a body-wide morph are explicit authoring errors.
	if candidates.size()!=1: return false
	var candidate: MeshInstance3D = candidates[0]
	if candidate.has_meta(OWNER_META): return false
	var vertices := 0
	for surface in candidate.mesh.get_surface_count():
		var arrays: Array = candidate.mesh.surface_get_arrays(surface)
		vertices += arrays[Mesh.ARRAY_VERTEX].size()
	if vertices<=0 or vertices>MAX_FACE_VERTICES: return false
	var staged := {}
	var half_count := 0
	for index in candidate.mesh.get_blend_shape_count():
		var shape := String(candidate.mesh.get_blend_shape_name(index))
		if not REQUIRED_SHAPES.has(shape) and not HALF_SHAPES.has(shape): continue
		var weight: float = candidate.get_blend_shape_value(index)
		if not is_finite(weight) or absf(weight)>.000001: return false
		staged[shape] = index
		if HALF_SHAPES.has(shape): half_count += 1
	if half_count!=0 and half_count!=2: return false
	_mesh = candidate
	_indices = staged
	_have_half = half_count==2
	_mesh.set_meta(OWNER_META,get_instance_id())
	configured = true
	name = "RamaFacialPerformance"
	reset("configure")
	return true

func _ease(value: float) -> float:
	var t := clampf(value,0,1)
	return t*t*(3-2*t)

func _blink_value(clock: float) -> float:
	var start: float = BLINK_INTERVALS[blink_index]
	var age := clock-start
	if age<0: return 0.0
	if age<BLINK_CLOSE: return _ease(age/BLINK_CLOSE)
	if age<BLINK_CLOSE+BLINK_HOLD: return 1.0
	return 1.0-_ease((age-BLINK_CLOSE-BLINK_HOLD)/BLINK_OPEN)

func _publish(left: float, right: float) -> bool:
	if not is_instance_valid(_mesh) or _mesh.get_meta(OWNER_META,0)!=get_instance_id():
		configured = false
		last_reason = "face removed or ownership changed"
		return false
	_weights.rama_blink_left = clampf(left,0,1)
	_weights.rama_blink_right = clampf(right,0,1)
	for index in 2:
		var shape: String = REQUIRED_SHAPES[index]
		var weight: float = _weights[shape]
		_mesh.set_blend_shape_value(_indices[shape],maxf(0,2*weight-1) if _have_half else weight)
		if _have_half: _mesh.set_blend_shape_value(_indices[HALF_SHAPES[index]],1-absf(2*weight-1))
	return true

func reset(reason := "reset") -> void:
	elapsed = 0
	blink_index = 0
	blink_clock = 0
	effort = 0
	defeat_age = 0
	_defeat_start = Vector2.ZERO
	_alive = true
	reset_count += 1
	last_reason = reason
	if configured: _publish(0,0)

func release() -> void:
	if is_instance_valid(_mesh) and _mesh.get_meta(OWNER_META,0)==get_instance_id():
		for shape in _indices: _mesh.set_blend_shape_value(_indices[shape],0)
		_mesh.remove_meta(OWNER_META)
	_mesh = null
	_indices.clear()
	_have_half = false
	configured = false
	_weights = {"rama_blink_left":0.0,"rama_blink_right":0.0}

func _exit_tree() -> void: release()

func update_facial(delta: float, state: Dictionary) -> bool:
	if not configured: return false
	# Pausing holds all clocks and actual values, including a partly closed lid.
	if bool(state.get("paused",false)): return true
	if not is_finite(delta) or delta<=0 or delta>MAX_DELTA:
		rejected_states += 1
		reset("invalid delta; no catch-up")
		return false
	var requested = state.get("effort",0.0)
	if not (requested is float or requested is int) or not is_finite(float(requested)):
		rejected_states += 1
		reset("invalid effort input")
		return false
	if bool(state.get("reset",false)) or bool(state.get("teleported",false)):
		reset("reset" if bool(state.get("reset",false)) else "teleport")
		return true
	var alive: bool = state.get("alive",true)
	if alive and not _alive:
		reset("respawn")
		return true
	var began_defeat := not alive and _alive
	_alive = alive
	elapsed += delta
	if not alive:
		if began_defeat:
			_defeat_start = Vector2(_weights.rama_blink_left,_weights.rama_blink_right)
			defeat_age = 0
		defeat_age += delta
		# Proper closed eyelids, not a new jaw or an invented facial death sculpt.
		var progress := _ease(defeat_age/.28)
		return _publish(lerpf(_defeat_start.x,1,progress),lerpf(_defeat_start.y,1,progress))
	effort = lerpf(effort,clampf(float(requested),0,1),1-exp(-12*delta))
	blink_clock += delta
	var cycle: float = BLINK_INTERVALS[blink_index]+BLINK_CLOSE+BLINK_HOLD+BLINK_OPEN
	if blink_clock>=cycle:
		blink_clock -= cycle
		blink_index = (blink_index+1)%BLINK_INTERVALS.size()
	var blink := _blink_value(blink_clock) if bool(state.get("blink_enabled",true)) else 0.0
	# A small authored partial closure gives effort/recovery readability.
	# Expression/eye-gaze/jaw morphs require separate sculpted assets.
	var weight := maxf(blink,effort*.14)
	return _publish(weight,weight)

func report() -> Dictionary:
	return {"configured":configured,"elapsed":elapsed,"blink_index":blink_index,"blink_clock":blink_clock,"effort":effort,"defeat_age":defeat_age,"weights":_weights.duplicate(),"half_correctives":_have_half,"rejected_states":rejected_states,"reset_count":reset_count,"last_reason":last_reason,"owned_meshes":1 if configured else 0,"scope":"Authored eyelid morph performance only, optional authored half-blink arc correctives. No eye scaling, facial shader warp, skeleton modification, gaze or jaw expression."}
