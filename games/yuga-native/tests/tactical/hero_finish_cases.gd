extends SceneTree
## Real imported firearm + original casting rig. No renderer or gameplay spoof.
const Weapon = preload("res://scripts/tactical_weapon.gd")
var checks: Array[Dictionary] = []
var metrics: Array[Dictionary] = []
var source_hashes: Dictionary = {}
var output := ""
var weapon: Node3D
var camera: Camera3D

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	for path in ["res://scripts/tactical_weapon.gd", "res://scripts/tactical_cast_motion.gd", "res://assets/tactical/surya-carbine.glb"]:
		source_hashes[path] = FileAccess.get_sha256(path)
	root.size = Vector2i(1280, 720); root.content_scale_size = root.size
	camera = Camera3D.new(); root.add_child(camera); camera.make_current()
	weapon = Weapon.new(); root.add_child(weapon); weapon.equip("carbine", true)
	await process_frame
	_check("actual SURYA imported magazine exists", is_instance_valid(weapon.magazine) and weapon.magazine.name == "Magazine")
	_check("casting hand is independent of rifle model", weapon.cast_motion.get_parent() == weapon and not weapon.model.is_ancestor_of(weapon.cast_motion))
	var fields: Dictionary = weapon.cast_motion.report()
	_check("articulated pose diagnostics are available", fields.has_all(["hand_position", "hand_rotation", "finger_angles", "digit_count", "active", "slot", "phase", "age_s", "finite"]))
	_check("original hand has five articulated digits", int(fields.get("digit_count", 0)) == 5)
	var distinct: Dictionary = {}
	for fps in [30, 60, 120]:
		for slot in ["q", "c", "e", "x"]:
			weapon.reset_presentation(); weapon.recoil = 0; weapon.moving = 0; weapon.ads = false
			var ammunition: Array = [weapon.ammo, weapon.reserve, weapon.reload_remaining, weapon.recovery]
			_check("%s/%d accepted presentation leaves firearm authority untouched" % [slot, fps], weapon.present_ability(slot) and ammunition == [weapon.ammo, weapon.reserve, weapon.reload_remaining, weapon.recovery])
			var previous: Dictionary = weapon.cast_motion.report()
			var previous_weapon: Dictionary = weapon.cast_motion.sample()
			var max_hand_step := 0.0
			var max_weapon_step := 0.0
			var minimum_weapon_y := 0.0
			var maximum_weight := 0.0
			var finite := true
			var last_active := 0.0
			for index in int(ceil(1.9 * fps)):
				weapon.step(1.0 / fps)
				var pose: Dictionary = weapon.cast_motion.report()
				var sample: Dictionary = weapon.cast_motion.sample()
				finite = finite and bool(pose.get("finite", false)) and weapon.model.transform.is_finite()
				if pose.get("hand_position") is Vector3 and previous.get("hand_position") is Vector3:
					max_hand_step = maxf(max_hand_step, pose.hand_position.distance_to(previous.hand_position))
				max_weapon_step = maxf(max_weapon_step, sample.weapon_position.distance_to(previous_weapon.weapon_position))
				minimum_weapon_y = minf(minimum_weapon_y, float(sample.weapon_position.y))
				maximum_weight = maxf(maximum_weight, float(sample.cast_weight))
				if bool(sample.active): last_active = float(index + 1) / fps
				if fps == 60 and index == 11: distinct[slot] = {"hand":pose.get("hand_position"), "fingers":pose.get("finger_angles")}
				previous = pose; previous_weapon = sample
			_check("%s/%d remains finite with bounded consecutive motion" % [slot, fps], finite and max_hand_step < .18 and max_weapon_step < .12)
			_check("%s/%d lowers rifle and enters readable cast weight" % [slot, fps], minimum_weapon_y < -.015 and maximum_weight > .6)
			_check("%s/%d returns completely to ordinary hold" % [slot, fps], not previous_weapon.active and previous_weapon.weapon_position.length() < .00001 and previous_weapon.weapon_rotation.length() < .00001 and float(previous_weapon.cast_weight) == 0 and weapon.support_hand.visible)
			metrics.append({"slot":slot, "fps":fps, "maximum_hand_step_m":max_hand_step, "maximum_weapon_step_m":max_weapon_step, "minimum_weapon_y_m":minimum_weapon_y, "maximum_cast_weight":maximum_weight, "last_active_sample_s":last_active})
	_check("Q/C/E/X use distinct visible pose channels", distinct.size() == 4 and distinct.q != distinct.c and distinct.c != distinct.e and distinct.e != distinct.x and distinct.x != distinct.q)
	# A new accepted utility must inherit its outgoing pose, not reset to rest.
	weapon.present_ability("q"); weapon.step(.14)
	var before: Dictionary = weapon.cast_motion.report()
	var offset_before: Dictionary = weapon.cast_motion.sample()
	weapon.present_ability("c")
	var after: Dictionary = weapon.cast_motion.report()
	_check("Q to C interruption preserves outgoing hand position", before.hand_position.distance_to(after.hand_position) < .00001)
	_check("Q to C interruption preserves outgoing weapon offset", offset_before.weapon_position.distance_to(weapon.cast_motion.sample().weapon_position) < .00001)
	weapon.step(1.0 / 60)
	_check("interrupted entry has no one-frame hand jump", before.hand_position.distance_to(weapon.cast_motion.report().hand_position) < .10)
	# Presentation has no free-running process callback: pausing the host freezes it.
	var paused: Dictionary = weapon.cast_motion.report().duplicate(true)
	await process_frame; await process_frame
	_check("no autonomous animation while host clock pauses", paused == weapon.cast_motion.report())
	var phase_before: Dictionary = weapon.cast_motion.report().duplicate(true)
	_check("unknown slot rejected without changing active pose", not weapon.present_ability("unknown") and phase_before == weapon.cast_motion.report())
	var clock_before: float = weapon.clock
	weapon.step(0); weapon.step(-1); weapon.step(NAN)
	_check("invalid deltas do not corrupt weapon or cast clock", weapon.clock == clock_before and phase_before == weapon.cast_motion.report())
	# Accepted weapon actions keep their existing timers and ammo semantics.
	weapon.equip("carbine", true); weapon.present_ability("c"); weapon.step(.15)
	var ready_pose: Dictionary = weapon.cast_motion.report().duplicate(true)
	_check("full-magazine reload rejection keeps cast pose", not weapon.reload() and ready_pose == weapon.cast_motion.report())
	_check("fire accepted during cosmetic cast keeps normal cost/rate", weapon.fire() and weapon.ammo == 23 and is_equal_approx(weapon.recovery, .12))
	var recoil_pose: Dictionary = weapon.cast_motion.report().duplicate(true)
	_check("recovery rejection does not restart visual cancellation", not weapon.fire() and recoil_pose == weapon.cast_motion.report())
	for index in 20: weapon.step(1.0 / 60)
	_check("accepted primary smoothly clears casting pose", not weapon.cast_motion.sample().active and weapon.cast_motion.sample().weapon_position.length() < .00001)
	weapon.present_ability("x"); weapon.step(.15)
	_check("reload during X presentation is accepted normally", weapon.reload() and is_equal_approx(weapon.reload_remaining, 2.1))
	for index in 150: weapon.step(1.0 / 60)
	_check("reload preserves finite ammo transfer and returns geometry", weapon.ammo == 24 and weapon.reserve == 71 and weapon.reload_remaining == 0 and weapon.model.position.length() < .00001 and weapon.support_hand.visible)
	# Starting an allowed utility during an already running reload cannot extend it.
	weapon.fire(); weapon.step(.15); weapon.reload(); weapon.step(.4)
	var reload_before: float = weapon.reload_remaining
	weapon.present_ability("q")
	_check("utility presentation cannot retime ongoing reload", weapon.reload_remaining == reload_before and weapon.ammo == 23)
	for index in 120: weapon.step(1.0 / 60)
	_check("overlapping utility/reload converges without stuck hand", weapon.ammo == 24 and weapon.reserve == 70 and weapon.reload_remaining == 0 and not weapon.cast_motion.sample().active and weapon.support_hand.visible)
	weapon.present_ability("x"); weapon.step(.3); weapon.reset_presentation()
	_check("death/round reset clears all cosmetic channels immediately", not weapon.cast_motion.sample().active and weapon.cast_motion.sample().weapon_position.length() < .00001 and weapon.cast_motion.sample().weapon_rotation.length() < .00001 and weapon.support_hand.visible)
	weapon.present_ability("q"); weapon.step(.2); weapon.equip("pistol", true)
	_check("equipment rebuild clears cast and keeps one rig", not weapon.cast_motion.sample().active and weapon.get_child_count() == 2 and weapon.ammo == 12 and weapon.reserve == 36)
	weapon.present_ability("c"); weapon.step(.2)
	_check("pistol also receives independent casting presentation", weapon.cast_motion.sample().active and weapon.cast_motion.sample().weapon_position.y < -.015)
	weapon.reset_presentation(); weapon.equip("carbine", true); weapon.ads = true
	weapon.present_ability("x"); weapon.step(.2)
	_check("ADS gameplay flag survives cosmetic ability", weapon.ads and weapon.cast_motion.report().finite)
	weapon.reset_presentation(); weapon.ads = false
	weapon.reduced_motion = false; weapon.present_ability("c"); weapon.step(.2)
	var normal_offset: Vector3 = weapon.cast_motion.sample().weapon_position
	weapon.reset_presentation(); weapon.reduced_motion = true; weapon.present_ability("c"); weapon.step(.2)
	_check("reduced motion retains pose while reducing rifle movement", weapon.cast_motion.sample().active and weapon.cast_motion.sample().cast_weight > .6 and weapon.cast_motion.sample().weapon_position.length() < normal_offset.length() and weapon.cast_motion.report().finite)
	for index in 90: weapon.step(1.0 / 60)
	_check("reduced motion also returns to exact rest", not weapon.cast_motion.sample().active and weapon.cast_motion.sample().weapon_position == Vector3.ZERO)
	_handoff_checks()
	var changed: Array = []
	for path: String in source_hashes:
		if FileAccess.get_sha256(path) != source_hashes[path]: changed.append(path)
	_check("reviewed source and actual asset unchanged", changed.is_empty())
	weapon.queue_free(); camera.queue_free(); await process_frame; await process_frame
	var passed := checks.all(func(row): return row.passed)
	var receipt := {"task":"HERO-FINISH2", "suite":"hero_finish", "passed":passed, "count":checks.size(), "checks":checks, "metrics":metrics, "source_sha256":source_hashes, "changed_sources":changed, "scope":"Actual imported SURYA/ARKA weapon and original articulated casting rig stepped at30/60/120. Source, finite/continuity, cancellation and firearm-authority checks. Does not establish rendered art/contact quality, ordinary input or performance."}
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE); file.store_string(JSON.stringify(receipt, "\t") + "\n")
	print("HERO_FINISH_RESULT ", JSON.stringify(receipt))
	quit(0 if passed else 1)

func _check(id: String, passed: bool) -> void:
	checks.append({"id":id, "passed":passed})

func _handoff_checks() -> void:
	# Actual mesh corners include every fingertip, palm and sleeve. Before either
	# visibility toggle, the outgoing geometry must already be below the viewport.
	# 110-degree hip FOV is the widest supported view; ADS uses its actual .72 factor.
	weapon.reduced_motion = false; weapon.moving = 0; weapon.recoil = 0
	for mode in ["hip", "ads"]:
		weapon.ads = mode == "ads"
		camera.fov = 110.0 * (.72 if weapon.ads else 1.0)
		weapon.position = Vector3(0, -.104, -.70) if weapon.ads else weapon.base_position
		for fps in [15, 60]:
			for slot in ["q", "c", "e", "x"]:
				weapon.reset_presentation(); weapon.present_ability(slot)
				var safe := true
				var toggles := 0
				var min_y := INF
				for index in int(ceil(1.9 * fps)):
					var visible_before: bool = weapon.cast_motion.report().visible
					var support_before: bool = weapon.support_hand.visible
					var before: PackedVector3Array = weapon.cast_motion.handoff_points()
					weapon.step(1.0 / fps)
					if (visible_before and not weapon.cast_motion.report().visible) or (not support_before and weapon.support_hand.visible):
						toggles += 1
						for points: PackedVector3Array in [before, weapon.cast_motion.handoff_points()]:
							for point: Vector3 in points:
								var screen: Vector2 = camera.unproject_position(point)
								min_y = minf(min_y, screen.y)
								safe = safe and screen.is_finite() and not camera.is_position_behind(point) and screen.y > 722.0
				_check("%s/%s/%d fingertips and complete hand leave view before grip switch" % [slot, mode, fps], safe and toggles > 0)
				metrics.append({"handoff_slot":slot, "view":mode, "fps":fps, "minimum_geometry_screen_y_at_toggle":min_y, "viewport_height":720, "toggles":toggles})
	# Accepted firearm/reload interruptions use the same physical withdrawal.
	weapon.ads = false; camera.fov = 110; weapon.position = weapon.base_position
	for slot in ["q", "c", "e", "x"]:
		weapon.reset_presentation(); weapon.present_ability(slot)
		for index in 18: weapon.step(1.0 / 60)
		weapon.cast_motion.cancel()
		var safe := true
		var max_step := 0.0
		var toggles := 0
		for index in 24:
			var pose: Dictionary = weapon.cast_motion.report()
			var before: PackedVector3Array = weapon.cast_motion.handoff_points()
			weapon.step(1.0 / 60)
			var next: Dictionary = weapon.cast_motion.report()
			max_step = maxf(max_step, pose.hand_position.distance_to(next.hand_position))
			if pose.visible and not next.visible:
				toggles += 1
				for point: Vector3 in before:
					var screen: Vector2 = camera.unproject_position(point)
					safe = safe and screen.is_finite() and screen.y > 722
		_check(slot + " cancellation withdraws fingertips before visibility toggle", safe and toggles == 1 and max_step < .18)
