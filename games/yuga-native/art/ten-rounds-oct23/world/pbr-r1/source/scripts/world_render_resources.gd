extends RefCounted
## Per-builder primitive meshes, published without embedded materials.
## Consumers only read shared geometry; duplicate a mesh before editing it.
## No static cache: another builder owns independent mesh/material lifetimes.
var _meshes: Dictionary = {}

func box(size_: Vector3, subdivisions: Vector3i = Vector3i.ZERO, flip: bool = false) -> BoxMesh:
	var key := [&"box", size_, subdivisions, flip]
	if not _meshes.has(key):
		var value := BoxMesh.new()
		value.size = size_
		value.subdivide_width = subdivisions.x
		value.subdivide_height = subdivisions.y
		value.subdivide_depth = subdivisions.z
		value.flip_faces = flip
		_meshes[key] = value
	return _meshes[key]

func sphere(radius: float, height: float, radial: int, rings: int, hemisphere: bool = false, flip: bool = false) -> SphereMesh:
	var key := [&"sphere", radius, height, radial, rings, hemisphere, flip]
	if not _meshes.has(key):
		var value := SphereMesh.new()
		value.radius = radius
		value.height = height
		value.radial_segments = radial
		value.rings = rings
		value.is_hemisphere = hemisphere
		value.flip_faces = flip
		_meshes[key] = value
	return _meshes[key]

func cylinder(top: float, bottom: float, height: float, radial: int, rings: int = 4, cap_top: bool = true, cap_bottom: bool = true, flip: bool = false) -> CylinderMesh:
	var key := [&"cylinder", top, bottom, height, radial, rings, cap_top, cap_bottom, flip]
	if not _meshes.has(key):
		var value := CylinderMesh.new()
		value.top_radius = top
		value.bottom_radius = bottom
		value.height = height
		value.radial_segments = radial
		value.rings = rings
		value.cap_top = cap_top
		value.cap_bottom = cap_bottom
		value.flip_faces = flip
		_meshes[key] = value
	return _meshes[key]

func torus(inner: float, outer: float, rings: int, segments: int, flip: bool = false) -> TorusMesh:
	var key := [&"torus", inner, outer, rings, segments, flip]
	if not _meshes.has(key):
		var value := TorusMesh.new()
		value.inner_radius = inner
		value.outer_radius = outer
		value.rings = rings
		value.ring_segments = segments
		value.flip_faces = flip
		_meshes[key] = value
	return _meshes[key]
