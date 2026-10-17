extends SkeletonModifier3D
## Original additive body poses; no imported clips are edited or replaced.
## Arms, wrists, bone positions and scales remain owned by the original animation.

const MAX_ANGLE := deg_to_rad(42.0)
const BONES := ["spine01", "spine03", "spine05", "neck01", "upperleg01.L", "upperleg01.R", "lowerleg01.L", "lowerleg01.R", "foot.L", "foot.R"]
var mapping: Array[Dictionary] = []
var mode := "ground"
var weight := 0.0
var phase := 0.0
var movement_speed := 0.0
var vertical_speed := 0.0
var suppressed := false
var modified_samples := 0
var maximum_angle := 0.0

func configure(visual: Node, _animator: AnimationPlayer = null) -> bool:
	var skeleton := _find_skeleton(visual)
	if not skeleton:
		return false
	skeleton.add_child(self)
	name = "OriginalTraversalPose"
	for bone_name in BONES:
		var bone := skeleton.find_bone(bone_name)
		if bone < 0:
			continue
		var rest := skeleton.get_bone_global_rest(bone)
		mapping.append({"bone": bone, "name": bone_name, "axis": (rest.basis.inverse() * Vector3.RIGHT).normalized()})
	return mapping.size() == BONES.size()

func _find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:
		return node
	for child in node.get_children():
		var found := _find_skeleton(child)
		if found:
			return found
	return null

func set_state(value: String, speed: float, vertical: float, delta: float, action_weight := 0.0) -> void:
	if not is_finite(speed) or not is_finite(vertical) or not is_finite(delta) or not is_finite(action_weight) or delta < 0 or delta > 0.1:
		cancel()
		return
	mode = value if value in ["flight", "grapple", "ground"] else "ground"
	movement_speed = clampf(speed, 0, 18)
	vertical_speed = clampf(vertical, -18, 18)
	suppressed = action_weight > 0.001
	var desired := 1.0 if mode != "ground" and not suppressed else 0.0
	weight = move_toward(weight, desired, delta * (12.0 if suppressed else 5.0))
	if suppressed:
		weight = 0.0
	phase = fposmod(phase + delta * 2.0, TAU)

func cancel() -> void:
	mode = "ground"
	weight = 0.0
	phase = 0.0
	suppressed = false

func _process_modification() -> void:
	var skeleton := get_skeleton()
	if not skeleton or weight <= 0 or mapping.is_empty():
		return
	for entry in mapping:
		var degrees := 0.0
		var bone_name: String = entry.name
		if bone_name.begins_with("spine"):
			degrees = -8.0 if mode == "flight" else -12.0
		elif bone_name.begins_with("neck"):
			degrees = 8.0
		elif bone_name.begins_with("upperleg"):
			degrees = 18.0 if mode == "flight" else 28.0
			degrees += sin(phase + (PI if bone_name.ends_with(".R") else 0.0)) * 3.0
		elif bone_name.begins_with("lowerleg"):
			degrees = -30.0 if mode == "flight" else -38.0
		elif bone_name.begins_with("foot"):
			degrees = 10.0
		var angle := clampf(deg_to_rad(degrees) * weight, -MAX_ANGLE, MAX_ANGLE)
		var original := skeleton.get_bone_pose_rotation(entry.bone)
		skeleton.set_bone_pose_rotation(entry.bone, (original * Quaternion(entry.axis, angle)).normalized())
		maximum_angle = maxf(maximum_angle, absf(angle))
	modified_samples += 1

func diagnostics() -> Dictionary:
	return {"mode": mode, "weight": weight, "phase": phase, "mapped_bones": mapping.size(), "maximum_angle_radians": maximum_angle, "hard_angle_limit": MAX_ANGLE, "modified_samples": modified_samples, "action_suppressed": suppressed, "scope": "Original additive body pose; upper-body grip and continuous visual quality require rendered review."}
