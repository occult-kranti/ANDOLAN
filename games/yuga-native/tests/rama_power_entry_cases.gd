extends SceneTree
## Actual imported skin/contact/authority-boundary checks for power preparation.
const Motion = preload("res://scripts/rama_motion.gd")
const Contacts = preload("res://tools/hero-family-reuse/motion_skin_contacts.gd")
const HERO := "res://assets/heroes/rama-hero.glb"
var checks: Array=[]
var samples: Dictionary={}
var trials: Array=[]

func _initialize() -> void:call_deferred("run")
func check(label: String, passed: bool, evidence: Dictionary={}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	if not passed:push_error("RAMA POWER ENTRY: "+label)
func find_node(node: Node,kind: String) -> Node:
	if node.is_class(kind):return node
	for child in node.get_children():
		var found:=find_node(child,kind)
		if found:return found
	return null
func tick(actor: Node3D,motion: Node,state: Dictionary,hz: float) -> void:
	actor.position+=Vector3(state.velocity)/hz
	motion.update_motion(1.0/hz,state);motion.evaluate_pose()
func execute(id: String,mode: String,hz: float) -> void:
	var actor: Node3D=load(HERO).instantiate();root.add_child(actor)
	var motion=Motion.new()
	var label:="%s_%s_%sHz"%[id,mode,hz]
	check(label+"_rig_configures",motion.configure(actor,find_node(actor,"AnimationPlayer")))
	if samples.is_empty():samples=Contacts.collect(actor,motion.rig)
	var state:={"velocity":Vector3(3,0,4) if mode=="moving" else Vector3.ZERO,"local_velocity":Vector3(3,0,4) if mode=="moving" else Vector3.ZERO,"grounded":true,"floor_y":0.0,"aiming":mode!="cold","aim_pitch":.45 if mode!="cold" else 0.0,"aim_yaw":.3 if mode!="cold" else 0.0}
	for frame in int(hz):tick(actor,motion,state,hz)
	var previous:=Contacts.skin(samples.string,motion)
	var windup:=.65 if id=="piercing_dawn" else .95
	var recovery:=.30 if id=="piercing_dawn" else .55
	check(label+"_action_accepted",motion.request_action(id,windup,recovery))
	# RamaHeroRuntime commits Q/X and zeros horizontal velocity on begin.
	# Exercise moving into that real stop, not an impossible sliding power cast.
	if mode=="moving":
		state.velocity=Vector3.ZERO;state.local_velocity=Vector3.ZERO
	var maximum:=0.0;var first:=0.0;var held_gap:=0.0;var skin_gap:=0.0;var finite:=true
	for frame in int(ceil(hz*(windup+.12))):
		tick(actor,motion,state,hz)
		var posed:=Contacts.skin(samples.string,motion)
		var difference: Dictionary=Contacts.max_step(previous,posed)
		maximum=maxf(maximum,float(difference.maximum_m))
		if frame==0:first=float(difference.maximum_m)
		for point in posed:finite=finite and point.is_finite()
		finite=finite and motion.finite
		if motion.action_stage=="hold":
			var nock: Vector3=motion.socket_global("string_nock").origin
			var hand: Vector3=motion.socket_global("draw_hand").origin
			held_gap=maxf(held_gap,nock.distance_to(hand))
			var local: Vector3=motion.rig.global_transform.affine_inverse()*nock
			skin_gap=maxf(skin_gap,Contacts.minimum_gap(Contacts.skin(samples.draw_fingers,motion),local))
		previous=posed
	var limit: float=(.16 if mode=="cold" else (.10 if mode=="moving" else .03))*30.0/hz
	check(label+"_continuous_skin_preparation_is_bounded",finite and maximum<limit,{"maximum_string_vertex_step_m":maximum,"limit_m":limit,"first_frame_m":first})
	check(label+"_held_string_meets_actual_fingertips",held_gap<.00001 and skin_gap<.002,{"socket_gap_m":held_gap,"nearest_finger_skin_m":skin_gap})
	check(label+"_presentation_never_releases_itself",motion.action_stage=="hold" and motion.release_count==0 and motion.windup==windup and motion.recovery==recovery)
	check(label+"_accepted_release_occurs_once",motion.release_action(id) and motion.release_count==1 and not motion.release_action(id))
	for frame in int(ceil(hz*(recovery+.2))):tick(actor,motion,state,hz)
	check(label+"_recovery_returns_to_locomotion",motion.action_stage=="none" and not motion.nocked and motion.world_velocity==Vector3(state.velocity))
	motion.request_action(id,windup,recovery)
	for frame in int(hz*.15):tick(actor,motion,state,hz)
	motion.cancel_action("power_entry_interruption")
	for frame in int(hz*.2):tick(actor,motion,state,hz)
	check(label+"_cancel_does_not_release_or_leave_nock",motion.action_stage=="none" and not motion.nocked and motion.release_count==1 and not motion.release_action(id))
	motion.request_action(id,windup,recovery)
	check(label+"_hit_interrupts_preparation",motion.request_action("hit",.06,.22) and motion.release_action("hit"))
	for frame in int(hz*.5):tick(actor,motion,state,hz)
	check(label+"_hit_recovers_finitely",motion.finite and motion.action_stage=="none")
	motion.cancel("power_test_reset")
	check(label+"_reset_clears_action_and_nock",motion.action_stage=="none" and not motion.nocked and not motion.release_action(id))
	check(label+"_reset_cannot_reuse_warm_entry",motion.request_action(id,windup,recovery) and not motion.warm_bow)
	trials.append({"ability_id":id,"mode":mode,"hz":hz,"maximum_string_vertex_step_m":maximum,"first_frame_m":first,"held_socket_gap_m":held_gap,"nearest_finger_skin_m":skin_gap})
	actor.free()
func run() -> void:
	for hz in [30.0,60.0,120.0]:
		for id in ["piercing_dawn","dawn_volley"]:
			for mode in ["cold","warm","moving"]:execute(id,mode,hz)
	check("actual_skin_samples_are_used",samples.string.size()==10 and samples.draw_fingers.size()>2000,{"string_vertices":samples.string.size(),"distal_finger_vertices":samples.draw_fingers.size()})
	var source_sha256: Dictionary={}
	for path in [get_script().resource_path,"res://scripts/rama_motion.gd","res://tools/hero-family-reuse/motion_skin_contacts.gd",HERO,"res://assets/animations/rama_hero_motion.tres"]:source_sha256[path]=FileAccess.get_sha256(path)
	var passed:=checks.all(func(item):return item.passed)
	var report:={"schema":1,"suite":"rama_power_entry_cases","passed":passed,"checks":checks,"trials":trials,"source_sha256":source_sha256,"scope":"Actual imported Rama skin at 30/60/120 Hz, cold/warm/moving power preparation, held contact, explicit release, cancel/hit/reset. No rendered quality, human feel or hardware performance claim."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path:=argument.trim_prefix("--report=");DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			var file:=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("Rama power entry checks: %d/%d"%[checks.filter(func(item):return item.passed).size(),checks.size()])
	quit(0 if passed else 1)
