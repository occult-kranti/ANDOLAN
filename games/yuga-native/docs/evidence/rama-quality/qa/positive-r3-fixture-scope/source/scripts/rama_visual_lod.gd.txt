extends RefCounted
## A bounded screen-size selector. It does not load scenes or create skeletons.
## Integration must bind candidate MeshInstances to the ONE existing Rama rig.
## No automatic candidate is accepted merely by using this selector.

const NEAR_MID_PIXELS := 420.0
const MID_FAR_PIXELS := 160.0
const HYSTERESIS := 0.15
const MIN_HOLD_SECONDS := 0.15

var level := 0
var _initialized := false
var _held_seconds := 0.0

func reset() -> void:
	level = 0
	_initialized = false
	_held_seconds = 0.0

func choose_pixels(projected_height: float, delta: float) -> int:
	if not is_finite(projected_height) or projected_height <= 0.0 or not is_finite(delta) or delta < 0.0:
		reset()
		return level
	# Capped accumulated time prevents a suspended frame from becoming an
	# unbounded catch-up loop. At most one level changes in an update.
	_held_seconds = minf(_held_seconds + minf(delta, 0.25), MIN_HOLD_SECONDS)
	if not _initialized:
		_initialized = true
		level = 0 if projected_height >= NEAR_MID_PIXELS else (1 if projected_height >= MID_FAR_PIXELS else 2)
		_held_seconds = 0.0
		return level
	if _held_seconds < MIN_HOLD_SECONDS:
		return level
	var next_level := level
	if level == 0 and projected_height < NEAR_MID_PIXELS * (1.0 - HYSTERESIS):
		next_level = 1
	elif level == 1:
		if projected_height > NEAR_MID_PIXELS * (1.0 + HYSTERESIS):
			next_level = 0
		elif projected_height < MID_FAR_PIXELS * (1.0 - HYSTERESIS):
			next_level = 2
	elif level == 2 and projected_height > MID_FAR_PIXELS * (1.0 + HYSTERESIS):
		next_level = 1
	if next_level != level:
		level = next_level
		_held_seconds = 0.0
	return level

func choose_camera(camera: Variant, center_world: Vector3, hero_height_m: float, delta: float) -> int:
	if not is_instance_valid(camera) or not camera is Camera3D or not camera.is_inside_tree() or not center_world.is_finite() or not is_finite(hero_height_m) or hero_height_m <= 0.0:
		reset()
		return level
	var viewport: Viewport = camera.get_viewport()
	if not is_instance_valid(viewport):
		reset()
		return level
	var viewport_height := viewport.get_visible_rect().size.y
	var camera_position: Vector3 = camera.global_transform.affine_inverse() * center_world
	if viewport_height <= 0.0 or not camera_position.is_finite() or -camera_position.z <= camera.near:
		reset()
		return level
	# Projection includes vertical/horizontal FOV policy and orthographic size.
	var projection: Projection = camera.get_camera_projection()
	var projected_height := absf(projection.y.y) * viewport_height * hero_height_m * 0.5
	if camera.projection != Camera3D.PROJECTION_ORTHOGONAL:
		projected_height /= -camera_position.z
	return choose_pixels(projected_height, delta)
