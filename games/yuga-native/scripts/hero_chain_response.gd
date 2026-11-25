extends SkeletonModifier3D
## Adds bounded movement response to a profiled imported bone chain.
## Runs after animation. Never changes translations, other bones or game state.

const MAX_DT := .10
const DRIVE_LIMITS := {
	"speed_reference_mps":Vector2(.5, 24.0),
	"speed_pitch_deg":Vector2(0.0, 22.0),
	"vertical_pitch_deg_per_mps":Vector2(0.0, 5.0),
	"lateral_yaw_deg_per_mps":Vector2(0.0, 5.0),
	"turn_yaw_deg_per_rad_s":Vector2(0.0, 10.0),
	"airborne_gain":Vector2(0.0, 2.0),
	"vault_pitch_deg":Vector2(0.0, 30.0),
	"landing_pitch_deg":Vector2(0.0, 30.0),
	"landing_min_speed_mps":Vector2(.5, 8.0),
	"landing_decay":Vector2(1.0, 35.0),
	"gate_seconds":Vector2(.04, .5),
	"cancel_settle_seconds":Vector2(.05, .5),
}
var configured := false
var last_error := ""
var _bones := PackedInt32Array()
var _names := PackedStringArray()
var _frequencies := PackedFloat32Array()
var _limits := PackedFloat32Array()
var _gains := PackedFloat32Array()
var _pitch_axes := PackedVector3Array()
var _yaw_axes := PackedVector3Array()
var _offsets := PackedVector2Array()
var _rates := PackedVector2Array()
var _drive := {}
var _clip_weights := {}
var _default_weight := 0.0
var _gate := 0.0
var _landing := 0.0
var _cancel_sec := 0.0
var _previous_yaw := 0.0
var _descent_speed := 0.0
var _previous_grounded := true
var _seeded := false
var _held := false
var _motion_kind := "idle"
var _elapsed := 0.0
var _landings := 0
var _resets := 0
var _modifier_samples := 0
var _max_applied := 0.0
var _applied := PackedFloat32Array()

static func _finite_number(value: Variant, range_: Vector2) -> bool:
	return (value is float or value is int) and is_finite(float(value)) and float(value) >= range_.x and float(value) <= range_.y

static func load_profile(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > 8192: return {}
	var profile: Variant = JSON.parse_string(file.get_as_text())
	return profile if profile is Dictionary else {}

func configure(rig: Skeleton3D, profile: Dictionary) -> bool:
	if configured: return false
	if rig == null or profile.get("schema_version") != 1 or not profile.get("anchor_bone") is String:
		last_error = "Invalid skeleton or response profile"
		return false
	var chain: Variant = profile.get("joints")
	var drive: Variant = profile.get("drive")
	var clip_weights: Variant = profile.get("clip_weights")
	var default_weight: Variant = profile.get("default_clip_weight")
	if not chain is Array or chain.size() < 2 or chain.size() > 8 or not drive is Dictionary or not clip_weights is Dictionary or clip_weights.size() > 32 or not _finite_number(default_weight, Vector2(0,1)):
		last_error = "Invalid chain, drive or clip weights"
		return false
	for key in DRIVE_LIMITS:
		if not _finite_number(drive.get(key), DRIVE_LIMITS[key]):
			last_error = "Response drive outside supported range: " + key
			return false
	for key in clip_weights:
		if not key is String or key.is_empty() or not _finite_number(clip_weights[key], Vector2(0,1)):
			last_error = "Invalid clip mask"
			return false
	var previous := rig.find_bone(profile.anchor_bone)
	var indices := PackedInt32Array()
	if previous < 0:
		last_error = "Missing chain anchor: " + profile.anchor_bone
		return false
	for row: Variant in chain:
		if not row is Dictionary or not row.get("bone") is String or not _finite_number(row.get("omega"), Vector2(1,35)) or not _finite_number(row.get("limit_deg"), Vector2(0,30)) or not _finite_number(row.get("gain"), Vector2(0,2)):
			last_error = "Invalid chain link"
			return false
		var index := rig.find_bone(row.bone)
		if index < 0 or rig.get_bone_parent(index) != previous:
			last_error = "Missing or disconnected chain role: " + row.bone
			return false
		var basis := rig.get_bone_global_rest(index).basis
		if not basis.is_finite() or absf(basis.determinant()) < .00001:
			last_error = "Invalid chain rest basis: " + row.bone
			return false
		indices.append(index)
		previous = index
	for i in range(indices.size()):
		var row: Dictionary = chain[i]
		var rest_inverse := rig.get_bone_global_rest(indices[i]).basis.orthonormalized().inverse()
		_names.append(row.bone)
		_pitch_axes.append((rest_inverse * Vector3.RIGHT).normalized())
		_yaw_axes.append((rest_inverse * Vector3.UP).normalized())
		_frequencies.append(float(row.omega))
		_limits.append(deg_to_rad(float(row.limit_deg)))
		_gains.append(float(row.gain))
		_offsets.append(Vector2.ZERO)
		_rates.append(Vector2.ZERO)
		_applied.append(0.0)
	_bones = indices
	_drive = drive.duplicate()
	_clip_weights = clip_weights.duplicate()
	_default_weight = float(default_weight)
	configured = true
	last_error = ""
	return true

func set_held(hold: bool) -> void:
	_held = hold

func cancel_response() -> void:
	_cancel_sec = float(_drive.get("cancel_settle_seconds", 0.0))
	_landing = 0.0
	_seeded = false
	_descent_speed = 0.0

func reset() -> void:
	_offsets.fill(Vector2.ZERO)
	_rates.fill(Vector2.ZERO)
	_applied.fill(0.0)
	_gate = 0.0
	_landing = 0.0
	_cancel_sec = 0.0
	_seeded = false
	_previous_grounded = true
	_descent_speed = 0.0
	_elapsed = 0.0
	_motion_kind = "idle"
	_max_applied = 0.0
	_resets += 1

func sample_motion(delta: float, local_velocity: Vector3, yaw: float, grounded: bool, vaulting: bool, clip: String) -> bool:
	if not configured: return false
	if _held: return true
	if not is_finite(delta) or delta <= 0.0 or delta > MAX_DT or not local_velocity.is_finite() or not is_finite(yaw):
		reset()
		return false
	yaw = wrapf(yaw, -PI, PI)
	var turn := clampf(wrapf(yaw - _previous_yaw, -PI, PI) / delta, -8.0, 8.0) if _seeded else 0.0
	var velocity := local_velocity.limit_length(24.0)
	_landing *= exp(-float(_drive.landing_decay) * delta)
	if not grounded:
		_descent_speed = maxf(_descent_speed, -velocity.y)
	else:
		if _seeded and not _previous_grounded and _descent_speed >= float(_drive.landing_min_speed_mps):
			_landing = clampf(_descent_speed / 6.0, 0.25, 1.0)
			_landings += 1
		_descent_speed = 0.0
	_previous_yaw = yaw
	_previous_grounded = grounded
	_seeded = true
	var speed := Vector2(velocity.x, velocity.z).length()
	var pace := clampf(speed / float(_drive.speed_reference_mps), 0.0, 1.0)
	var pitch := -pace * float(_drive.speed_pitch_deg) + clampf(-velocity.y, -9.0, 9.0) * float(_drive.vertical_pitch_deg_per_mps)
	pitch += _landing * float(_drive.landing_pitch_deg)
	if vaulting: pitch -= float(_drive.vault_pitch_deg)
	var lateral := -velocity.x * float(_drive.lateral_yaw_deg_per_mps) - turn * float(_drive.turn_yaw_deg_per_rad_s)
	var target := Vector2(deg_to_rad(pitch), deg_to_rad(lateral)) * (1.0 if grounded else float(_drive.airborne_gain))
	_motion_kind = "vault" if vaulting else ("landing" if _landing > .20 else ("air" if not grounded else ("moving" if speed > .4 else "idle")))
	var weight: float = _clip_weights.get(clip, _default_weight)
	# Fade both directions as animation blends. Protected clips (weight zero)
	# keep their authored pose after the brief entry blend through contact.
	_gate = move_toward(_gate, weight, delta / float(_drive.gate_seconds))
	if _cancel_sec > 0.0:
		_cancel_sec = maxf(0.0, _cancel_sec - delta)
		target = Vector2.ZERO
	for i in range(_bones.size()):
		var goal := (target * _gains[i]).limit_length(_limits[i])
		var frequency := float(_frequencies[i])
		var offset := _offsets[i] - goal
		var coefficient := _rates[i] + offset * frequency
		var decay := exp(-frequency * delta)
		# Closed-form critical spring adapted from Rama secondary motion.
		_offsets[i] = (goal + (offset + coefficient * delta) * decay).limit_length(_limits[i])
		_rates[i] = (_rates[i] - coefficient * frequency * delta) * decay
	_elapsed += delta
	return true

func _process_modification() -> void:
	var rig := get_skeleton()
	if not configured or rig == null: return
	for i in range(_bones.size()):
		var applied := _offsets[i] * _gate
		_applied[i] = rad_to_deg(applied.length())
		_max_applied = maxf(_max_applied, _applied[i])
		if applied.length_squared() > .0000000001:
			var base := rig.get_bone_pose_rotation(_bones[i])
			if base.is_finite():
				var bending := Quaternion(_pitch_axes[i], applied.x) * Quaternion(_yaw_axes[i], applied.y)
				rig.set_bone_pose_rotation(_bones[i], (base * bending).normalized())
	_modifier_samples += 1

func report() -> Dictionary:
	var offsets_deg: Array = []
	for v in _offsets: offsets_deg.append([rad_to_deg(v.x), rad_to_deg(v.y)])
	var limits_deg: Array = []
	for v in _limits: limits_deg.append(rad_to_deg(v))
	return {
		"configured":configured, "joints":Array(_names), "offsets_deg":offsets_deg, "limits_deg":limits_deg,
		"applied_deg":Array(_applied), "overlay_weight":_gate, "max_applied_degrees":_max_applied,
		"motion_kind":_motion_kind, "grounded":_previous_grounded, "elapsed_s":_elapsed,
		"landings":_landings, "resets":_resets, "modifier_samples":_modifier_samples,
		"held":_held, "cancel_settle_s":_cancel_sec, "last_error":last_error,
	}
