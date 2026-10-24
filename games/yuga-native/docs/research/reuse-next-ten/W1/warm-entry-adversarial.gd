extends SceneTree
## Small independent black-box event/pose check, not rendered motion acceptance.
var output := ""
var motion_source := "res://scripts/rama_motion.gd"
var rows := []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
		elif arg.begins_with("--motion-source="): motion_source = arg.trim_prefix("--motion-source=")
	call_deferred("run")

func find_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer: return node
	for child in node.get_children():
		var found := find_animation(child)
		if found != null: return found
	return null

func tick(motion: Node, state: Dictionary, hz: float, seconds: float) -> void:
	for unused in maxi(1,roundi(seconds*hz)):
		motion.update_motion(1.0/hz,state)
		motion.evaluate_pose()

func execute(label: String, hz: float) -> Dictionary:
	var actor: Node3D = load("res://assets/heroes/rama-hero.glb").instantiate()
	root.add_child(actor)
	var motion = load(motion_source).new()
	if not motion.configure(actor,find_animation(actor)):
		actor.free()
		return {"label":label,"hz":hz,"passed":false,"configured":false}
	motion.evaluate_pose()
	var state := {"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"floor_y":0.0,"grounded":true,"aiming":label!="cold","aim_pitch":.3,"aim_yaw":.2}
	tick(motion,state,hz,.6)
	if label in ["after_cancel","after_reset","retrigger"]:
		motion.request_action("kodanda",.18,.22)
		tick(motion,state,hz,.04 if label!="retrigger" else .3)
		if label=="after_cancel": motion.cancel_action("review-cancel")
		elif label=="after_reset": motion.cancel("review-reset")
		else: motion.release_action("kodanda")
		tick(motion,state,hz,.05 if label=="retrigger" else .4)
	elif label=="after_respawn":
		motion.request_action("death",.18,.22)
		tick(motion,state,hz,.3)
		motion.release_action("death")
		tick(motion,state,hz,.3)
		motion.request_action("respawn",.18,.22)
		tick(motion,state,hz,.3)
		motion.release_action("respawn")
		tick(motion,state,hz,.6)
	elif label=="reaim":
		state.aiming=false
		tick(motion,state,hz,.6)
		state.aiming=true
		tick(motion,state,hz,.6)
	var nock: int = motion.rig.find_bone("bowstring")
	var before: Vector3 = motion.rig.get_bone_global_pose(nock).origin
	var releases: int = motion.release_count
	var requested: bool = motion.request_action("kodanda",.18,.22)
	motion.update_motion(1.0/hz,state)
	motion.evaluate_pose()
	var step: float = before.distance_to(motion.rig.get_bone_global_pose(nock).origin)
	var before_rejected: Dictionary = motion.diagnostics().duplicate(true)
	var rejected: bool = not motion.request_action("kodanda",.18,.22) and not motion.request_action("unreviewed",.18,.22) and not motion.request_action("hit",INF,.22)
	var reject_unchanged: bool = motion.diagnostics()==before_rejected
	tick(motion,state,hz,.3)
	var held_contact: float = motion.socket_global("string_nock").origin.distance_to(motion.socket_global("draw_hand").origin)
	var result := {"label":label,"hz":hz,"requested":requested,"warm":motion.warm_bow,"entry_nock_step_m":step,"held_contact_m":held_contact,"finite":motion.finite,"rejected_events_preserve_public_state":rejected and reject_unchanged,"no_synthetic_release":motion.release_count==releases,"passed":requested and step<.05 and held_contact<.0001 and motion.finite and rejected and reject_unchanged and motion.release_count==releases}
	actor.free()
	return result

func run() -> void:
	for hz in [30.0,60.0,120.0]: rows.append(execute("warm",hz))
	for label in ["cold","after_cancel","after_reset","after_respawn","reaim","retrigger"]:
		rows.append(execute(label,120.0))
	var report := {"schema":1,"scope":"Actual accepted rig, normal one-update/one-evaluation frames in a synchronous black-box controller fixture. Nine targeted entry/reset/cancel/respawn/reaim/retrigger cases, public rejected-event invariance and hold contact. No rendered or human-feel pass.","motion_source":motion_source,"motion_sha256":FileAccess.get_sha256(motion_source),"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"checks":rows,"passed":rows.all(func(row):return row.passed)}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	quit(0 if report.passed else 1)
