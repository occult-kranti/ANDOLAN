extends SkeletonModifier3D
## Original upper-body carry overlay. Native lower-body animation stays intact.
## Targets use this hero's own rest rig and authored fire-grip rotations.
const ARM_PARTS := ["clavicle", "shoulder01", "upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "wrist"]
const FADE_SECONDS := 0.22
const GRIP_CENTER := Vector3(0.0,0.105,0.025)
const GRIP_RADIUS := 0.022
const GRIP_HALF_LENGTH := 0.046
# Per-finger closure calibrated against actual distal skin and the 22 mm handle.
# Reusing full authored closure causes up to 10 mm penetration in carry space.
const FINGER_CLOSURE := [0.25,0.90,1.0,0.80,1.0]
var mapping: Array[Dictionary] = []
var bowstring := -1
var weight := 0.0
var requested_clip := ""
var suppressed := false
var configured := false
var modified_samples := 0
var rejected_states := 0

func _find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D: return node
	for child in node.get_children():
		var found := _find_skeleton(child)
		if found: return found
	return null

func configure(visual: Node, animator: AnimationPlayer) -> bool:
	if configured or visual==null or animator==null or get_parent()!=null: return false
	var skeleton := _find_skeleton(visual)
	if not skeleton: return false
	var fire: Animation
	for clip: StringName in animator.get_animation_list():
		if String(clip).get_file().to_lower()=="fire": fire=animator.get_animation(clip)
	if not fire or not is_finite(fire.length) or fire.length<=0.0: return false
	var prepared: Array[Dictionary] = []
	for side in ["L","R"]:
		for part in ARM_PARTS:
			var bone := skeleton.find_bone(part+"."+side)
			if bone<0: return false
			var target := skeleton.get_bone_rest(bone).basis.get_rotation_quaternion().normalized()
			# Modest adduction and elbow flexion soften the original rest carry.
			var world_axis := Vector3.FORWARD
			var angle := 0.0
			if part=="upperarm01": angle=deg_to_rad(10.0 if side=="L" else -12.0)
			elif part=="lowerarm01":
				world_axis=Vector3.RIGHT
				angle=deg_to_rad(-10.0 if side=="L" else -8.0)
			var axis := (skeleton.get_bone_global_rest(bone).basis.inverse()*world_axis).normalized()
			target=(target*Quaternion(axis,angle)).normalized()
			prepared.append({"bone":bone,"name":part+"."+side,"rotation":target})
	for finger in range(1,6):
		for segment in range(1,4):
			var name_ := "finger%d-%d.R" % [finger,segment]
			var bone := skeleton.find_bone(name_)
			if bone<0: return false
			var found := false
			for track in fire.get_track_count():
				var path := fire.track_get_path(track)
				if fire.track_get_type(track)!=Animation.TYPE_ROTATION_3D or path.get_subname_count()!=1 or String(path.get_subname(0))!=name_: continue
				var authored := fire.rotation_track_interpolate(track,fire.length*.25).normalized()
				var rest := skeleton.get_bone_rest(bone).basis.get_rotation_quaternion().normalized()
				var target := rest.slerp(authored,FINGER_CLOSURE[finger-1]).normalized()
				if not target.is_finite(): return false
				prepared.append({"bone":bone,"name":name_,"rotation":target})
				found=true
				break
			if not found: return false
	var string_index := skeleton.find_bone("bowstring")
	if string_index<0 or skeleton.get_bone_parent(string_index)!=skeleton.find_bone("wrist.R"): return false
	mapping=prepared
	bowstring=string_index
	skeleton.add_child(self)
	name="OriginalHeroCarryPose"
	configured=true
	return true

func set_state(clip: String, delta: float, traversal_mode := "ground", action_active := false) -> void:
	if not is_finite(delta) or delta<0.0 or delta>0.1:
		rejected_states+=1
		cancel()
		return
	requested_clip=clip.get_file().to_lower()
	suppressed=action_active or traversal_mode!="ground" or requested_clip not in ["idle","run","tps_idle","tps_run"]
	# Attacks emit immediately in player.gd. Their existing AnimationPlayer blend
	# owns the raise/release; a second carry fade must not delay that first shot.
	if action_active or requested_clip in ["fire","cast","cast1","cast2","cast3"]:
		weight=0.0
	else:
		weight=move_toward(weight,0.0 if suppressed else 1.0,delta/FADE_SECONDS)

func cancel() -> void:
	weight=0.0
	requested_clip=""
	suppressed=true

func _process_modification() -> void:
	var skeleton := get_skeleton()
	if not configured or not skeleton or weight<=0.0: return
	for entry in mapping:
		var source := skeleton.get_bone_pose_rotation(entry.bone)
		if not source.is_finite(): continue
		skeleton.set_bone_pose_rotation(entry.bone,source.slerp(entry.rotation,weight).normalized())
	# This sole translation exception returns the string to the authored neutral
	# position while carrying. All body translations/scales remain animation-owned.
	var source := skeleton.get_bone_pose_position(bowstring)
	if source.is_finite():
		skeleton.set_bone_pose_position(bowstring,source.lerp(skeleton.get_bone_rest(bowstring).origin,weight))
	modified_samples+=1

func diagnostics() -> Dictionary:
	return {"configured":configured,"mapped_rotations":mapping.size(),"weight":weight,
		"clip":requested_clip,"suppressed":suppressed,"modified_samples":modified_samples,
		"rejected_states":rejected_states,"fade_seconds":FADE_SECONDS,
		"scope":"Original optional upper-body carry and authored grip; native lower body is unchanged. Rendering/contact acceptance is separate."}
