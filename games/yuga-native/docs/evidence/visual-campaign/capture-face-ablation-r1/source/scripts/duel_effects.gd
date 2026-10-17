extends Node3D
## Original choreography VFX. Fixed meshes; absolute time; no particles or tweens.
## The director supplies an identity world root and samples after actor poses.

const ENERGY := preload("res://scripts/duel_energy.gdshader")
const MAX_CUES := 32
const MAX_MESHES := 128
const TYPES := ["telegraph", "projectile", "guard", "impact", "trail"]

var _manifest: Dictionary = {}
var _socket_at_time := Callable()
var _entries: Array[Dictionary] = []
var _errors: Array[String] = []
var _configured := false
var _time := 0.0
var _mesh_count := 0
var _reduced_flash := true
var _reduced_motion := false

func configure(manifest: Dictionary, socket_at_time: Callable = Callable()) -> bool:
	_clear()
	_manifest = manifest.duplicate(true)
	_socket_at_time = socket_at_time
	_validate(manifest)
	if not _errors.is_empty():
		return false
	for cue in manifest.get("cues", []):
		var holder := Node3D.new()
		holder.name = String(cue.id).validate_node_name()
		add_child(holder)
		var entry := {"cue": cue.duplicate(true), "holder": holder, "meshes": []}
		_build(entry)
		_entries.append(entry)
	_configured = true
	sample(0.0)
	return true

func set_accessibility(reduced_flash: bool, reduced_motion: bool) -> void:
	_reduced_flash = reduced_flash
	_reduced_motion = reduced_motion

func sample_time(time: float, reduced_effects: bool = false) -> void:
	set_accessibility(reduced_effects, reduced_effects)
	sample(time)

func sample(time: float, manifest: Dictionary = {}) -> void:
	if not manifest.is_empty() and manifest != _manifest:
		configure(manifest, _socket_at_time)
	if not _configured:
		return
	_time = clampf(time, 0.0, float(_manifest.get("duration_seconds", 24.0))) if is_finite(time) else 0.0
	for entry in _entries:
		var cue: Dictionary = entry.cue
		var age := _time - float(cue.t_seconds)
		var duration := float(cue.duration_seconds)
		var active := _time >= float(cue.t_seconds) and _time < float(cue.t_seconds) + duration
		entry.holder.visible = active
		for mesh in entry.meshes:
			mesh.transform = Transform3D.IDENTITY
			mesh.visible = false
			mesh.material_override.set_shader_parameter("opacity", 0.0)
			mesh.material_override.set_shader_parameter("progress", 0.0)
		if not active:
			continue
		var u := clampf(age / duration, 0.0, 1.0)
		match String(cue.type):
			"telegraph": _telegraph(entry, u)
			"guard": _guard(entry, u)
			"projectile": _projectile(entry, u)
			"impact": _impact(entry, u)
			"trail": _trail(entry, u)

func diagnostics() -> Dictionary:
	var state: Array[Dictionary] = []
	var active_ids: Array[String] = []
	for entry in _entries:
		if entry.holder.visible:
			active_ids.append(String(entry.cue.id))
		var parts: Array[Dictionary] = []
		for mesh in entry.meshes:
			parts.append({"visible": mesh.visible, "transform": _transform_array(mesh.transform),
				"opacity": mesh.material_override.get_shader_parameter("opacity"),
				"progress": mesh.material_override.get_shader_parameter("progress")})
		state.append({"id": entry.cue.id, "visible": entry.holder.visible, "parts": parts})
	return {"configured": _configured, "errors": _errors.duplicate(), "time": _time,
		"cue_count": _entries.size(), "max_cues": MAX_CUES, "mesh_count": _mesh_count,
		"max_meshes": MAX_MESHES, "active_ids": active_ids, "state": state,
		"reduced_flash": _reduced_flash, "reduced_motion": _reduced_motion,
		"scope": "Deterministic choreography VFX, not authority hit or damage validation."}

func _validate(manifest: Dictionary) -> void:
	if not _number(manifest.get("duration_seconds"), 0.1, 60.0):
		_errors.append("duration_seconds must be finite and in [0.1,60]")
	var cues: Variant = manifest.get("cues")
	if not cues is Array or cues.size() > MAX_CUES:
		_errors.append("cues must be an array with at most 32 entries")
		return
	var ids := {}
	var total := 0
	for cue in cues:
		if not cue is Dictionary:
			_errors.append("cue must be an object")
			continue
		var id := str(cue.get("id", ""))
		if not cue.get("id") is String or id.is_empty() or ids.has(id):
			_errors.append("cue IDs must be nonempty and unique")
		ids[id] = true
		if not cue.get("type") is String or not str(cue.get("type", "")) in TYPES:
			_errors.append("unknown cue type: " + id)
		if not _number(cue.get("t_seconds"), 0.0, 60.0) or not _number(cue.get("duration_seconds"), 0.001, 30.0):
			_errors.append("invalid cue time: " + id)
		elif _number(manifest.get("duration_seconds"), 0.1, 60.0) and float(cue.t_seconds) + float(cue.duration_seconds) > float(manifest.duration_seconds) + 0.000001:
			_errors.append("cue exceeds film duration: " + id)
		for field in ["position", "from_position", "to_position", "locked_target_position"]:
			if cue.has(field) and not _position_valid(cue[field]):
				_errors.append("invalid world position: " + id + "/" + field)
		var needs_pair: bool = str(cue.get("type", "")) in ["projectile", "trail"] or cue.get("style", "") == "danger_corridor"
		if needs_pair:
			if not (cue.has("from_position") and cue.has("to_position")) and not (_socket_at_time.is_valid() and cue.has("actor_id") and cue.has("target_id")):
				_errors.append("cue requires endpoints or an actor/target socket resolver: " + id)
		elif not cue.has("position") and not (_socket_at_time.is_valid() and cue.has("actor_id")):
			_errors.append("cue requires a position or actor socket resolver: " + id)
		if cue.has("radius") and not _number(cue.radius, 0.05, 8.0):
			_errors.append("invalid radius: " + id)
		total += _cost(cue)
	if total > MAX_MESHES:
		_errors.append("VFX mesh budget exceeds 128")

func _cost(cue: Dictionary) -> int:
	match str(cue.get("type", "")):
		"telegraph", "guard": return 2
		"projectile": return 15 if cue.get("style", "") == "spectral_fan" else 3
		"impact": return 11
		"trail": return 6
	return 0

func _build(entry: Dictionary) -> void:
	var cue: Dictionary = entry.cue
	var tint := Color("ad94ff") if cue.get("color_role", "solar") == "spectral" else Color("ffd16d")
	match String(cue.type):
		"telegraph":
			_add(entry, _plane(), tint, 1 if cue.get("style", "") == "danger_corridor" else 0)
			_add(entry, _plane() if cue.get("style", "") == "danger_corridor" else _sphere(), tint, 0 if cue.get("style", "") == "danger_corridor" else 4)
		"guard":
			_add(entry, _quad(), tint, 2)
			_add(entry, _quad(), tint, 0)
		"projectile":
			for _i in range(5 if cue.get("style", "") == "spectral_fan" else 1):
				_add(entry, _cylinder(false), tint, 4)
				_add(entry, _cylinder(true), tint, 4)
				_add(entry, _sphere(), tint, 4)
		"impact":
			_add(entry, _quad(), tint, 0)
			_add(entry, _plane(), tint, 0)
			for _i in range(6): _add(entry, _cylinder(true), tint, 4)
			for _i in range(3): _add(entry, _sphere(), Color("a3967e"), 4)
		"trail":
			for _i in range(3): _add(entry, _plane(), tint, 3)
			for _i in range(3): _add(entry, _sphere(), Color("a3967e"), 4)

func _add(entry: Dictionary, mesh: Mesh, tint: Color, pattern: int) -> void:
	var instance := MeshInstance3D.new()
	instance.name = "Part%02d" % entry.meshes.size()
	instance.mesh = mesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := ShaderMaterial.new()
	material.shader = ENERGY
	material.set_shader_parameter("tint", tint)
	material.set_shader_parameter("pattern", pattern)
	material.set_shader_parameter("energy", 1.05)
	instance.material_override = material
	entry.holder.add_child(instance)
	entry.meshes.append(instance)
	_mesh_count += 1

func _telegraph(entry: Dictionary, u: float) -> void:
	var cue: Dictionary = entry.cue
	var opacity := _envelope(u, 0.12, 0.12) * 0.72
	if cue.get("style", "") == "danger_corridor":
		var a := _point(cue, "from_position")
		var b := _point(cue, "to_position")
		var direction := (b-a).normalized()
		var radius := float(cue.get("radius", 1.6))
		_put(entry.meshes[0], (a+b)*0.5, Vector3(radius*2.0,1.0,maxf(a.distance_to(b),0.01)), opacity, u)
		entry.meshes[0].rotation.y = atan2(direction.x,direction.z)
		_put(entry.meshes[1], b+Vector3.UP*0.004, Vector3.ONE*radius*2.2, opacity*0.75, u)
	else:
		var p := _point(cue, "position")
		_put(entry.meshes[0], Vector3(p.x,0.032,p.z), Vector3(2.5,1.0,2.5), opacity*0.72, u)
		var charge_size := lerpf(0.09,0.23,u)
		_put(entry.meshes[1], p, Vector3.ONE*charge_size, opacity*0.7, u)

func _guard(entry: Dictionary, u: float) -> void:
	var cue: Dictionary = entry.cue
	var center := _point(cue, "position")
	var normal := _incoming_direction(cue)
	var opacity := _envelope(u,0.15,0.15)*0.68
	_put(entry.meshes[0],center,Vector3.ONE*3.0,opacity,u)
	_face(entry.meshes[0],normal)
	_put(entry.meshes[1],center+normal*0.012,Vector3.ONE*3.20,opacity*0.48,u)
	_face(entry.meshes[1],normal)

func _projectile(entry: Dictionary, u: float) -> void:
	var cue: Dictionary = entry.cue
	var a := _point(cue,"from_position")
	var b := _point(cue,"to_position")
	var direction := (b-a).normalized()
	if direction.length_squared()<0.1: direction=Vector3.FORWARD
	var sideways := Vector3.UP.cross(direction).normalized()
	if sideways.length_squared()<0.1: sideways=Vector3.RIGHT
	var count := 5 if cue.get("style", "") == "spectral_fan" else 1
	var opacity := _envelope(u,0.04,0.04)*0.88
	for i in range(count):
		var spread := (float(i)-2.0)*0.62 if count==5 else 0.0
		var end := b+sideways*spread
		var travel := (end-a).normalized()
		var p := a.lerp(end,u)
		var tail := 1.15 if count==5 else 1.75
		if _reduced_motion: tail*=0.45
		_put(entry.meshes[i*3],p-travel*tail*0.5,Vector3(0.032,tail,0.032),opacity*0.65,u)
		_align_y(entry.meshes[i*3],travel)
		_put(entry.meshes[i*3+1],p,Vector3(0.13,0.36,0.13),opacity,u)
		_align_y(entry.meshes[i*3+1],travel)
		_put(entry.meshes[i*3+2],p,Vector3.ONE*0.075,opacity*0.45,u)

func _impact(entry: Dictionary, u: float) -> void:
	var cue: Dictionary = entry.cue
	var center := _point(cue,"position")
	var normal := _incoming_direction(cue)
	var decay := pow(1.0-u,1.6)
	var radius := lerpf(0.5,2.5 if not _reduced_motion else 1.1,u)
	_put(entry.meshes[0],center,Vector3.ONE*radius,decay*0.72,u)
	_face(entry.meshes[0],normal)
	_put(entry.meshes[1],Vector3(center.x,0.04,center.z),Vector3.ONE*radius*1.3,decay*0.38,u)
	for i in range(6):
		var angle := float(i)*TAU/6.0+0.27
		var direction := Vector3(cos(angle),0.35+float(i%3)*0.22,sin(angle)).normalized()
		var travel := u*(1.5 if not _reduced_motion else 0.45)
		var p := center+direction*travel+Vector3.DOWN*u*u*0.3
		_put(entry.meshes[i+2],p,Vector3(0.045,0.22,0.045)*(1.0-u*0.55),decay*0.55,u)
		_align_y(entry.meshes[i+2],direction)
	for i in range(3):
		var angle := float(i)*TAU/3.0+0.5
		var p := Vector3(center.x,0.1+u*0.18,center.z)+Vector3(cos(angle),0,sin(angle))*u*0.8
		_put(entry.meshes[i+8],p,Vector3(0.55,0.22,0.55)*(0.4+u),decay*0.12,u)

func _trail(entry: Dictionary, u: float) -> void:
	var cue: Dictionary = entry.cue
	var a := _point(cue,"from_position")
	var b := _point(cue,"to_position")
	var direction := (b-a).normalized()
	var current := a.lerp(b,u)
	var opacity := _envelope(u,0.12,0.2)*0.55
	for i in range(3):
		var start := a.lerp(current,float(i)*0.1)
		var p := (start+current)*0.5+Vector3.UP*(0.12+float(i)*0.38)
		_put(entry.meshes[i],p,Vector3(0.17,1,maxf(start.distance_to(current),0.01)),opacity*(0.25 if _reduced_motion else 1.0),u)
		entry.meshes[i].rotation.y=atan2(direction.x,direction.z)
	for i in range(3):
		var p := a.lerp(current,float(i)/3.0)+Vector3.UP*0.06
		_put(entry.meshes[i+3],p,Vector3(0.28,0.11,0.28),opacity*0.16,u)

func _put(mesh: MeshInstance3D, position_: Vector3, scale_: Vector3, opacity: float, u: float) -> void:
	mesh.position=position_
	mesh.scale=scale_
	mesh.visible=opacity>0.001
	mesh.material_override.set_shader_parameter("opacity",clampf(opacity*(0.65 if _reduced_flash else 1.0),0,0.9))
	mesh.material_override.set_shader_parameter("progress",u)

func _face(mesh: MeshInstance3D, normal: Vector3) -> void:
	var z := normal.normalized()
	if z.length_squared()<0.1: z=Vector3.BACK
	var x := Vector3.UP.cross(z).normalized()
	if x.length_squared()<0.1: x=Vector3.RIGHT
	var size := mesh.scale
	mesh.basis=Basis(x*size.x,z.cross(x).normalized()*size.y,z*size.z)

func _align_y(mesh: MeshInstance3D, direction: Vector3) -> void:
	var y := direction.normalized()
	if y.length_squared()<0.1: y=Vector3.UP
	var x := Vector3.UP.cross(y).normalized()
	if x.length_squared()<0.1: x=Vector3.RIGHT
	var size := mesh.scale
	mesh.basis=Basis(x*size.x,y*size.y,x.cross(y).normalized()*size.z)

func _incoming_direction(cue: Dictionary) -> Vector3:
	for other in _manifest.get("cues",[]):
		if other.get("type", "") == "projectile" and (other.get("receipt_id", "missing") == cue.get("receipt_id", "none") or other.get("target_id", "") == cue.get("actor_id", "none")):
			return (_point(other,"from_position")-_point(other,"to_position")).normalized()
	return Vector3(0,0,-1)

func _point(cue: Dictionary, field: String) -> Vector3:
	# The director caches release sockets while building the film. This lookup
	# never resamples or moves the currently displayed actor pose.
	if field == "from_position" and cue.get("type", "") == "projectile" and cue.get("style", "") == "solar_arrow" and _socket_at_time.is_valid():
		var release: Variant = _socket_at_time.call(str(cue.get("actor_id", "")), "bow", float(cue.t_seconds))
		if release is Vector3 and release.is_finite():
			return release
	if cue.has(field):
		var p: Array=cue[field]
		return Vector3(float(p[0]),float(p[1]),float(p[2]))
	if _socket_at_time.is_valid():
		var socket := "bow" if field=="from_position" else "chest"
		var actor := str(cue.get("target_id", "")) if field=="to_position" else str(cue.get("actor_id", ""))
		var result: Variant=_socket_at_time.call(actor,socket,float(cue.get("t_seconds",_time)))
		if result is Vector3 and result.is_finite(): return result
	return Vector3.ZERO

func _envelope(u: float, attack: float, release: float) -> float:
	return smoothstep(0.0,attack,u)*(1.0-smoothstep(1.0-release,1.0,u))

func _clear() -> void:
	for child in get_children():
		remove_child(child)
		child.free()
	_entries.clear()
	_errors.clear()
	_mesh_count=0
	_configured=false
	_time=0.0

static func _number(value: Variant, minimum: float, maximum: float) -> bool:
	return (value is float or value is int) and is_finite(float(value)) and float(value)>=minimum and float(value)<=maximum

static func _position_valid(value: Variant) -> bool:
	if not value is Array or value.size()!=3: return false
	for component in value:
		if not _number(component,-10000.0,10000.0): return false
	return true

static func _plane() -> PlaneMesh:
	var mesh:=PlaneMesh.new()
	mesh.size=Vector2.ONE
	return mesh

static func _quad() -> QuadMesh:
	var mesh:=QuadMesh.new()
	mesh.size=Vector2.ONE
	return mesh

static func _sphere() -> SphereMesh:
	var mesh:=SphereMesh.new()
	mesh.radius=1.0
	mesh.height=2.0
	mesh.radial_segments=10
	mesh.rings=5
	return mesh

static func _cylinder(cone: bool) -> CylinderMesh:
	var mesh:=CylinderMesh.new()
	mesh.bottom_radius=1.0
	mesh.top_radius=0.0 if cone else 1.0
	mesh.height=1.0
	mesh.radial_segments=8
	return mesh

static func _transform_array(value: Transform3D) -> Array:
	return [value.origin.x,value.origin.y,value.origin.z,
		value.basis.x.x,value.basis.x.y,value.basis.x.z,
		value.basis.y.x,value.basis.y.y,value.basis.y.z,
		value.basis.z.x,value.basis.z.y,value.basis.z.z]
