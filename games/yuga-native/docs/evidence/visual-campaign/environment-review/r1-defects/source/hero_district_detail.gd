extends RefCounted
## Original coastal belvedere: a visual-only garden beyond the training boundary.
## Layered arches, lathed stone, floral relief and lanceolate planting are invented
## art direction, not a reconstruction of an historic site or another game's art.
## The optional maps below are the existing original CC0 courtyard textures;
## provenance: assets/environment/lanka_courtyard.metadata.json.

const ROOT_NAME := "HeroDistrictDetail"
const MAX_MESHES := 8
const MAX_TRIANGLES := 65000
const TERRACE_FRONT_Z := 24.99
const TERRACE_BACK_Z := 35.0
const TERRACE_HALF_WIDTH := 22.0
const TERRACE_TOP_Y := -0.006
const TEXTURE_ROOT := "res://assets/environment/lanka_courtyard_"
const PALETTE := {
	"stone": Color("d5c1a0"), "limestone": Color("ebe1c8"),
	"indigo": Color("395f71"), "brass": Color("b49c65"),
	"leaf": Color("57745c"), "leaf_light": Color("7e9770"),
	"earth": Color("493e32"), "wick": Color("ffcf86")
}
var _surfaces: Dictionary = {}
var _counts := {"arches": 0, "cupolas": 0, "urns": 0, "leaf_blades": 0, "diyas": 0, "rosettes": 0, "terrace_courses": 0}

static func configure(world: Node3D) -> Dictionary:
	if not is_instance_valid(world): return {"ok": false, "reason": "invalid_parent"}
	var existing := world.get_node_or_null(ROOT_NAME)
	if existing != null:
		if not existing.get_meta("hero_district_owned", false):
			return {"ok": false, "reason": "foreign_name_collision"}
		return diagnostics(world)
	var builder = new()
	builder._belvedere()
	builder._pier_relief()
	var district := Node3D.new()
	district.name = ROOT_NAME
	district.set_meta("hero_district_owned", true)
	district.set_meta("visual_only", true)
	district.set_meta("design", "Original coastal belvedere, not a historical reconstruction")
	district.set_meta("counts", builder._counts.duplicate(true))
	builder._finish(district)
	world.add_child(district)
	set_phase(world, 0.0)
	return diagnostics(world)

static func set_phase(world: Node3D, phase: float) -> void:
	if not is_instance_valid(world): return
	var district := world.get_node_or_null(ROOT_NAME)
	if district == null or not district.get_meta("hero_district_owned", false): return
	var safe_phase := clampf(phase, 0.0, 1.0) if is_finite(phase) else 0.0
	district.set_meta("phase", safe_phase)
	var wick := district.get_node_or_null("wick") as MeshInstance3D
	if wick != null:
		var material := wick.material_override as StandardMaterial3D
		if material != null: material.emission_energy_multiplier = lerpf(0.55, 1.6, safe_phase)

static func diagnostics(world: Node3D) -> Dictionary:
	var district := world.get_node_or_null(ROOT_NAME) if is_instance_valid(world) else null
	var result := {"ok": false, "meshes": 0, "triangles": 0, "lights": 0,
		"collision_objects": 0, "phase": 0.0, "mesh_budget": MAX_MESHES,
		"triangle_budget": MAX_TRIANGLES, "counts": {}, "per_frame_callbacks": false,
		"texture_source": "original courtyard CC0 textures", "play_area_changed": false,
		"terrace": {"front_z": TERRACE_FRONT_Z, "back_z": TERRACE_BACK_Z,
			"half_width": TERRACE_HALF_WIDTH, "top_y": TERRACE_TOP_Y}}
	if district == null or not district.get_meta("hero_district_owned", false): return result
	result.ok = true
	result.phase = district.get_meta("phase", 0.0)
	result.counts = district.get_meta("counts", {}).duplicate(true)
	for child in district.get_children():
		if child is MeshInstance3D:
			result.meshes += 1
			result.triangles += child.mesh.surface_get_array_len(0) / 3
		if child is Light3D: result.lights += 1
		if child is CollisionObject3D: result.collision_objects += 1
	return result

func _belvedere() -> void:
	_terrace()
	# Entire above-ground assembly is beyond the existing solid z=25.25 movement boundary.
	# Its open centre frames the real title hero without masking the practice lane.
	for side in [-1.0, 1.0]:
		for x_abs in [5.2, 10.4, 15.6]:
			var p := Vector3(side * x_abs, 0.0, 28.8)
			_column(p, 5.25, 0.44)
			_rosette(p + Vector3(0, 4.62, -0.63), 0.36)
		for x_abs in [7.8, 13.0]:
			var p := Vector3(side * x_abs, 3.25, 28.8)
			_arch("stone", p, 2.18, 0.39, 0.74, 48)
			_arch("limestone", p + Vector3(0, 0, -0.43), 2.15, 0.075, 0.10, 48)
			_arch("brass", p + Vector3(0, 0, -0.495), 2.28, 0.025, 0.035, 48)
			_counts.arches += 1
			# Tiny lotus medallions articulate the spandrels rather than flat panels.
			_rosette(p + Vector3(0, 2.8, -0.44), 0.33)
			_lintel(p + Vector3(0, 2.8, 0.0), 4.9, 0.36, 0.88, "stone")
			_lintel(p + Vector3(0, 3.02, -0.02), 5.12, 0.09, 1.04, "limestone")
			for offset in [-1.9, -0.95, 0.0, 0.95, 1.9]:
				_bead(Vector3(p.x + offset, 6.06, 28.24), 0.055, "brass")
		for z in [27.0, 30.5]:
			_urn(Vector3(side * 17.4, 0.0, z), 1.0, int(absf(z * 19.0) + side * 3))
		# Larger plants sit at the actual outboard border, never as false cover.
		_urn(Vector3(side * 8.4, 0.0, 26.6), 0.88, int(side + 12))
		_diya(Vector3(side * 4.1, 0.0, 26.8), 0.82)
		_diya(Vector3(side * 12.6, 0.0, 26.8), 0.82)
		_cupola(Vector3(side * 10.4, 6.22, 28.8), 1.95, 1.0)
	# Tall scalloped-profile outer arch, a finer inner order and a crowned canopy.
	_arch("stone", Vector3(0, 4.65, 28.8), 4.78, 0.58, 1.0, 72)
	_arch("limestone", Vector3(0, 4.65, 28.22), 4.75, 0.11, 0.13, 72)
	_arch("brass", Vector3(0, 4.65, 28.14), 4.91, 0.035, 0.042, 72)
	_counts.arches += 1
	_lintel(Vector3(0, 10.11, 28.8), 11.2, 0.31, 1.31, "stone")
	_lintel(Vector3(0, 10.33, 28.8), 11.55, 0.10, 1.50, "limestone")
	_cupola(Vector3(0, 10.43, 28.8), 1.30, 0.85)
	for x in [-4.7, -3.6, -2.5, 2.5, 3.6, 4.7]:
		_lathe("limestone", Vector3(x, 10.40, 28.8), [Vector2(0.20, 0), Vector2(0.24, 0.08), Vector2(0.14, 0.20), Vector2(0.085, 0.43), Vector2(0.02, 0.53)], 16)
	# Rear parapets read as depth behind the open front order; no thin backdrop card.
	for side in [-1.0, 1.0]:
		for x_abs in [7.8, 13.0]:
			_lintel(Vector3(side * x_abs, 0.62, 31.7), 4.5, 0.12, 0.36, "limestone")
			_lintel(Vector3(side * x_abs, 1.46, 31.7), 4.5, 0.13, 0.40, "limestone")
			for step in range(7):
				var x: float = side * x_abs - 1.8 + step * 0.6
				_lathe("stone", Vector3(x, 0.67, 31.7), [Vector2(0.11, 0), Vector2(0.14, 0.10), Vector2(0.055, 0.26), Vector2(0.11, 0.53), Vector2(0.08, 0.73)], 12)

func _terrace() -> void:
	# R1 actual title review exposed floating feet beyond the old z=25 paving.
	# The top overlaps that edge by 1 cm, but is 6 mm below it: no coplanar
	# faces, raised threshold or new movement/cover authority. The two lower
	# courses give the outboard garden a substantial visible coastal foundation.
	var centre_z := (TERRACE_FRONT_Z + TERRACE_BACK_Z) * 0.5
	var depth := TERRACE_BACK_Z - TERRACE_FRONT_Z
	_lintel(Vector3(0, TERRACE_TOP_Y - 0.08, centre_z), TERRACE_HALF_WIDTH * 2.0, 0.16, depth, "limestone")
	_lintel(Vector3(0, -0.53, centre_z + 0.08), TERRACE_HALF_WIDTH * 2.0 - 0.24, 0.80, depth - 0.08, "stone")
	_lintel(Vector3(0, -1.00, centre_z + 0.10), TERRACE_HALF_WIDTH * 2.0 + 0.20, 0.22, depth + 0.18, "limestone")
	_counts.terrace_courses = 3

func _pier_relief() -> void:
	# All north-facing decoration hugs existing occupied gate piers. It never
	# adds visual obstacles in the 24 x 28 metre clear central movement rectangle.
	for side in [-1.0, 1.0]:
		for y in [2.85, 7.68]:
			for offset in [-1.65, -0.83, 0.0, 0.83, 1.65]:
				_rosette(Vector3(side * 9.0 + offset, y, -20.49), 0.20, true)
		for offset in [-2.28, 2.28]:
			var start := Vector3(side * 9.0 + offset, 3.12, -20.45)
			for index in range(7):
				_rosette(start + Vector3(0, index * 0.64, 0), 0.105, true)

func _column(p: Vector3, height: float, radius: float) -> void:
	var profile: Array[Vector2] = [Vector2(radius * 1.55, 0.02), Vector2(radius * 1.62, 0.09),
		Vector2(radius * 1.62, 0.21), Vector2(radius * 1.48, 0.30), Vector2(radius * 1.12, 0.41),
		Vector2(radius * 1.0, 0.56), Vector2(radius * 0.86, height - 0.74),
		Vector2(radius * 1.07, height - 0.55), Vector2(radius * 1.45, height - 0.35),
		Vector2(radius * 1.52, height - 0.22), Vector2(radius * 1.52, height)]
	_lathe("stone", p, profile, 32, 0.055, 12)
	for y in [0.47, height - 0.52, height - 0.18]:
		_lathe("limestone", p + Vector3.UP * y, [Vector2(radius * 1.19, -0.06), Vector2(radius * 1.24, -0.025), Vector2(radius * 1.24, 0.025), Vector2(radius * 1.19, 0.06)], 32)

func _cupola(p: Vector3, radius: float, height_scale: float) -> void:
	var profile: Array[Vector2] = []
	for item in [Vector2(1, 0), Vector2(1.06, 0.10), Vector2(1.04, 0.22), Vector2(0.96, 0.39), Vector2(0.83, 0.63), Vector2(0.66, 0.89), Vector2(0.45, 1.13), Vector2(0.25, 1.31), Vector2(0.10, 1.41), Vector2(0.018, 1.48)]:
		profile.append(Vector2(item.x * radius, item.y * radius * height_scale))
	_lathe("indigo", p, profile, 48, 0.035, 12)
	_lathe("brass", p, [Vector2(radius * 1.035, 0.05), Vector2(radius * 1.07, 0.095), Vector2(radius * 1.07, 0.13), Vector2(radius * 1.035, 0.18)], 48)
	_lathe("brass", p + Vector3.UP * radius * height_scale * 1.43, [Vector2(0.10, 0.0), Vector2(0.17, 0.16), Vector2(0.095, 0.29), Vector2(0.055, 0.48), Vector2(0.012, 0.77)], 20)
	_counts.cupolas += 1

func _urn(p: Vector3, size: float, seed_value: int) -> void:
	var profile: Array[Vector2] = []
	for point in [Vector2(0.48, 0.0), Vector2(0.56, 0.07), Vector2(0.55, 0.16), Vector2(0.37, 0.23), Vector2(0.40, 0.34), Vector2(0.67, 0.59), Vector2(0.72, 0.87), Vector2(0.62, 1.11), Vector2(0.66, 1.17), Vector2(0.66, 1.25), Vector2(0.56, 1.28), Vector2(0.52, 1.18)]:
		profile.append(point * size)
	_lathe("stone", p, profile, 32, 0.026, 10)
	_lathe("earth", p + Vector3.UP * 1.18 * size, [Vector2(0.001, 0), Vector2(0.51 * size, 0)], 24)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	for i in range(24):
		var angle := i * 2.39996 + rng.randf_range(-0.12, 0.12)
		var length := rng.randf_range(1.15, 2.15) * size
		var outward := Vector3(cos(angle), 0, sin(angle))
		var base := p + Vector3.UP * size * 1.21 + outward * rng.randf_range(0.02, 0.22)
		_leaf(base, outward, length, rng.randf_range(0.12, 0.23) * size, "leaf_light" if i % 4 == 0 else "leaf", rng.randf_range(0.72, 1.15))
	_counts.urns += 1

func _leaf(base: Vector3, outward: Vector3, length: float, width: float, material: String, lift: float) -> void:
	var side := Vector3.UP.cross(outward).normalized()
	var colour := Color(0.90, 0.94, 0.88)
	for step in range(8):
		var t0 := float(step) / 8.0
		var t1 := float(step + 1) / 8.0
		var c0 := base + outward * length * t0 * 0.62 + Vector3.UP * length * (sin(t0 * 1.8) * lift)
		var c1 := base + outward * length * t1 * 0.62 + Vector3.UP * length * (sin(t1 * 1.8) * lift)
		var w0 := maxf(0.008, sin(t0 * PI) * width)
		var w1 := maxf(0.001, sin(t1 * PI) * width)
		var ridge0 := c0 + Vector3.UP * sin(t0 * PI) * width * 0.27
		var ridge1 := c1 + Vector3.UP * sin(t1 * PI) * width * 0.27
		_quad(material, c0 - side * w0, c1 - side * w1, ridge1, ridge0, colour)
		_quad(material, ridge0, ridge1, c1 + side * w1, c0 + side * w0, colour)
	_counts.leaf_blades += 1

func _diya(p: Vector3, size: float) -> void:
	var profile: Array[Vector2] = []
	for point in [Vector2(0.24, 0), Vector2(0.29, 0.08), Vector2(0.18, 0.19), Vector2(0.10, 0.34), Vector2(0.10, 1.12), Vector2(0.19, 1.21), Vector2(0.35, 1.28), Vector2(0.40, 1.39), Vector2(0.38, 1.44)]:
		profile.append(point * size)
	_lathe("brass", p, profile, 28)
	_lathe("wick", p + Vector3.UP * 1.43 * size, [Vector2(0.065 * size, 0), Vector2(0.085 * size, 0.10 * size), Vector2(0.045 * size, 0.22 * size), Vector2(0.003, 0.38 * size)], 12)
	_counts.diyas += 1

func _rosette(p: Vector3, radius: float, face_positive: bool = false) -> void:
	var depth := 0.045 * (1.0 if face_positive else -1.0)
	for petal in range(8):
		var angle := petal * TAU / 8.0
		var axis := Vector3(cos(angle), sin(angle), 0)
		var side := Vector3(-sin(angle), cos(angle), 0)
		var a := p + axis * radius * 0.12
		var b := p + axis * radius * 0.50 + side * radius * 0.19
		var c := p + axis * radius
		var d := p + axis * radius * 0.50 - side * radius * 0.19
		var centre := p + axis * radius * 0.53 + Vector3(0, 0, depth)
		_triangle("limestone", a, b, centre)
		_triangle("limestone", b, c, centre)
		_triangle("limestone", c, d, centre)
		_triangle("limestone", d, a, centre)
	_counts.rosettes += 1

func _bead(p: Vector3, radius: float, material: String) -> void:
	_lathe(material, p - Vector3.UP * radius, [Vector2(0.005, 0), Vector2(radius * 0.75, radius * 0.35), Vector2(radius, radius), Vector2(radius * 0.75, radius * 1.65), Vector2(0.005, radius * 2)], 12)

func _arch(material: String, centre: Vector3, radius: float, width: float, depth: float, segments: int) -> void:
	# Eight-sided bevel cross-section gives narrow edge catches and a quiet face.
	var bevel := minf(width * 0.22, depth * 0.20)
	var section: Array[Vector2] = [Vector2(0, -depth / 2 + bevel), Vector2(bevel, -depth / 2), Vector2(width - bevel, -depth / 2), Vector2(width, -depth / 2 + bevel), Vector2(width, depth / 2 - bevel), Vector2(width - bevel, depth / 2), Vector2(bevel, depth / 2), Vector2(0, depth / 2 - bevel)]
	for i in range(segments):
		var a := PI * float(i) / segments
		var b := PI * float(i + 1) / segments
		for j in range(section.size()):
			var next := (j + 1) % section.size()
			_quad(material, _arch_point(centre, a, radius, section[j]), _arch_point(centre, b, radius, section[j]), _arch_point(centre, b, radius, section[next]), _arch_point(centre, a, radius, section[next]))

func _arch_point(centre: Vector3, angle: float, radius: float, profile: Vector2) -> Vector3:
	var scallop := 0.022 * pow(sin(angle * 9.0), 2.0)
	var effective := radius + profile.x + scallop
	return centre + Vector3(cos(angle) * effective, sin(angle) * effective, profile.y)

func _lintel(p: Vector3, width: float, height: float, depth: float, material: String) -> void:
	# Closed chamfered extrusion; deliberately not a stock hard-edged box.
	var b := minf(height * 0.28, 0.055)
	var ring: Array[Vector2] = [Vector2(-width / 2 + b, -height / 2), Vector2(width / 2 - b, -height / 2), Vector2(width / 2, -height / 2 + b), Vector2(width / 2, height / 2 - b), Vector2(width / 2 - b, height / 2), Vector2(-width / 2 + b, height / 2), Vector2(-width / 2, height / 2 - b), Vector2(-width / 2, -height / 2 + b)]
	for i in range(ring.size()):
		var j := (i + 1) % ring.size()
		var a := p + Vector3(ring[i].x, ring[i].y, -depth / 2)
		var c := p + Vector3(ring[j].x, ring[j].y, depth / 2)
		_quad(material, a, p + Vector3(ring[j].x, ring[j].y, -depth / 2), c, p + Vector3(ring[i].x, ring[i].y, depth / 2))
		_triangle(material, p + Vector3(0, 0, -depth / 2), p + Vector3(ring[j].x, ring[j].y, -depth / 2), a)
		_triangle(material, p + Vector3(0, 0, depth / 2), p + Vector3(ring[i].x, ring[i].y, depth / 2), c)

func _lathe(material: String, centre: Vector3, profile: Array[Vector2], segments: int, rib_depth: float = 0.0, ribs: int = 1) -> void:
	for row in range(profile.size() - 1):
		var tangent0 := profile[mini(row + 1, profile.size() - 1)] - profile[maxi(0, row - 1)]
		var tangent1 := profile[mini(row + 2, profile.size() - 1)] - profile[row]
		for segment in range(segments):
			var a := TAU * float(segment) / segments
			var b := TAU * float(segment + 1) / segments
			var points: Array[Vector3] = [_lathe_point(centre, profile[row], a, rib_depth, ribs), _lathe_point(centre, profile[row], b, rib_depth, ribs), _lathe_point(centre, profile[row + 1], b, rib_depth, ribs), _lathe_point(centre, profile[row + 1], a, rib_depth, ribs)]
			var normals: Array[Vector3] = [_lathe_normal(tangent0, a, rib_depth, ribs), _lathe_normal(tangent0, b, rib_depth, ribs), _lathe_normal(tangent1, b, rib_depth, ribs), _lathe_normal(tangent1, a, rib_depth, ribs)]
			_smooth_triangle(material, points[0], points[1], points[2], normals[0], normals[1], normals[2])
			_smooth_triangle(material, points[0], points[2], points[3], normals[0], normals[2], normals[3])

func _lathe_point(centre: Vector3, point: Vector2, angle: float, rib_depth: float, ribs: int) -> Vector3:
	var radius := point.x * (1.0 + rib_depth * cos(angle * ribs))
	return centre + Vector3(cos(angle) * radius, point.y, sin(angle) * radius)

func _lathe_normal(tangent: Vector2, angle: float, rib_depth: float, ribs: int) -> Vector3:
	var radial := 1.0 + rib_depth * cos(angle * ribs)
	var derivative := -rib_depth * ribs * sin(angle * ribs)
	var along_ring := Vector3(derivative * cos(angle) - radial * sin(angle), 0, derivative * sin(angle) + radial * cos(angle))
	var along_profile := Vector3(tangent.x * radial * cos(angle), tangent.y, tangent.x * radial * sin(angle))
	return along_profile.cross(along_ring).normalized()

func _quad(material: String, a: Vector3, b: Vector3, c: Vector3, d: Vector3, color: Color = Color.WHITE) -> void:
	_triangle(material, a, b, c, color)
	_triangle(material, a, c, d, color)

func _triangle(material: String, a: Vector3, b: Vector3, c: Vector3, color: Color = Color.WHITE) -> void:
	var normal := (c - a).cross(b - a).normalized()
	_smooth_triangle(material, a, b, c, normal, normal, normal, color)

func _smooth_triangle(material: String, a: Vector3, b: Vector3, c: Vector3, na: Vector3, nb: Vector3, nc: Vector3, color: Color = Color.WHITE) -> void:
	if (c - a).cross(b - a).length_squared() < 0.00000000001: return
	if not _surfaces.has(material):
		_surfaces[material] = {"vertices": PackedVector3Array(), "normals": PackedVector3Array(), "colors": PackedColorArray()}
	_surfaces[material].vertices.append_array(PackedVector3Array([a, b, c]))
	_surfaces[material].normals.append_array(PackedVector3Array([na, nb, nc]))
	_surfaces[material].colors.append_array(PackedColorArray([color, color, color]))

func _finish(district: Node3D) -> void:
	for key: String in _surfaces:
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = _surfaces[key].vertices
		arrays[Mesh.ARRAY_NORMAL] = _surfaces[key].normals
		arrays[Mesh.ARRAY_COLOR] = _surfaces[key].colors
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		var instance := MeshInstance3D.new()
		instance.name = key
		instance.mesh = mesh
		instance.material_override = _material(key)
		instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if key in ["stone", "limestone", "indigo"] else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		district.add_child(instance)

func _material(key: String) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.resource_name = "Original belvedere " + key
	material.albedo_color = PALETTE[key]
	material.vertex_color_use_as_albedo = true
	material.roughness = 0.84
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	if key in ["stone", "limestone", "indigo", "brass"]:
		var source: String = {"stone": "Warm_carved_sandstone", "limestone": "Pale_limestone", "indigo": "Indigo_glazed_stone", "brass": "Aged_brass"}[key]
		var albedo_path := TEXTURE_ROOT + source + "_albedo.png"
		var roughness_path := TEXTURE_ROOT + source + "_roughness.png"
		if ResourceLoader.exists(albedo_path):
			material.albedo_texture = load(albedo_path)
			# Existing source maps already contain colour; avoid tint-squared darkness.
			material.albedo_color = Color(0.94, 0.96, 1.0) if key == "indigo" else Color(1.0, 1.0, 1.0)
		if ResourceLoader.exists(roughness_path): material.roughness_texture = load(roughness_path)
		material.uv1_triplanar = true
		material.uv1_world_triplanar = true
		material.uv1_scale = Vector3(0.65, 0.65, 0.65)
		# Existing courtyard maps retain glTF ORM packing: roughness is GREEN.
		# RED is constant occlusion and would erase authored surface variation.
		material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
		material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		material.metallic = 0.46 if key == "brass" else 0.0
		material.roughness = 0.78 if key == "brass" else 1.0
	elif key in ["leaf", "leaf_light"]:
		material.roughness = 0.90
		material.backlight_enabled = true
		material.backlight = Color(0.08, 0.12, 0.05)
	elif key == "wick":
		material.emission_enabled = true
		material.emission = PALETTE[key]
		material.roughness = 1.0
	return material
