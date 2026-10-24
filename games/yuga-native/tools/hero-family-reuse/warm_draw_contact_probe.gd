extends SceneTree
## Focused actual-string-mesh witness for warm/cold/retrigger/reset/respawn draws.
const HERO:="res://assets/heroes/rama-hero.glb"
const Contacts=preload("res://tools/hero-family-reuse/motion_skin_contacts.gd")
var output:=""
var motion_path:="res://scripts/rama_motion.gd"
var sample_cache:={}
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg.begins_with("--motion-source="):motion_path=arg.trim_prefix("--motion-source=")
	call_deferred("run")
func find_node(node: Node,kind: String) -> Node:
	if node.is_class(kind):return node
	for child in node.get_children():
		var found:=find_node(child,kind)
		if found:return found
	return null
func tick(motion: Node,state: Dictionary,hz: float,frames: int) -> void:
	for frame in frames:motion.update_motion(1.0/hz,state);motion.evaluate_pose()
func execute(mode: String,hz: float) -> Dictionary:
	var actor: Node3D=load(HERO).instantiate();root.add_child(actor);var motion=load(motion_path).new()
	if not motion.configure(actor,find_node(actor,"AnimationPlayer")):actor.free();return {"configured":false}
	if sample_cache.is_empty():sample_cache=Contacts.collect(actor,motion.rig)
	var sampled: Dictionary=sample_cache
	var cold:={"velocity":Vector3.ZERO,"grounded":true,"floor_y":0.,"aiming":false}
	var aimed:={"velocity":Vector3.ZERO,"grounded":true,"floor_y":0.,"aiming":true,"aim_pitch":.45,"aim_yaw":.3}
	var state: Dictionary=cold if mode=="cold" else aimed
	tick(motion,state,hz,int(hz))
	var setup_ok:=true;var rejected_cache_unchanged:=true
	if mode=="retrigger":
		setup_ok=motion.request_action("kodanda",.18,.22);tick(motion,state,hz,int(hz*.3));setup_ok=setup_ok and motion.release_action("kodanda");tick(motion,state,hz,maxi(1,int(hz*.08)))
	elif mode=="reset_cold":
		setup_ok=motion.request_action("kodanda",.18,.22);tick(motion,state,hz,int(hz*.3));motion.cancel("W5rigreset");state=cold;tick(motion,state,hz,int(hz*.4))
	elif mode=="cancel_reaim":
		setup_ok=motion.request_action("kodanda",.18,.22);tick(motion,state,hz,int(hz*.08));motion.cancel_action("W5cancel");tick(motion,state,hz,int(hz*.4))
	elif mode=="respawn_reaim":
		setup_ok=motion.request_action("death",.18,.22);tick(motion,state,hz,int(hz*.3));setup_ok=setup_ok and motion.release_action("death");tick(motion,state,hz,int(hz*.3));setup_ok=setup_ok and motion.request_action("respawn",.18,.22);tick(motion,state,hz,int(hz*.3));setup_ok=setup_ok and motion.release_action("respawn");tick(motion,state,hz,int(hz*.6))
	var before_request: Array=motion.action_from_positions.duplicate()
	var rejected: bool=not motion.request_action("not_an_ability",.18,.22)
	rejected_cache_unchanged=motion.action_from_positions==before_request
	var before:=Contacts.skin(sampled.string,motion);var previous:=before
	var requested: bool=motion.request_action("kodanda",.18,.22)
	var rows:=[];var held_socket:=0.;var held_finger:=0.;var finite:=true
	for frame in int(hz*.32):
		tick(motion,state,hz,1)
		var posed:=Contacts.skin(sampled.string,motion);var step:=Contacts.max_step(previous,posed)
		var nock: Vector3=motion.rig.global_transform.affine_inverse()*motion.socket_global("string_nock").origin
		var hand: Vector3=motion.rig.global_transform.affine_inverse()*motion.socket_global("draw_hand").origin
		var fingers:=Contacts.skin(sampled.draw_fingers,motion);var finger_gap:=Contacts.minimum_gap(fingers,nock)
		var socket_gap:=nock.distance_to(hand)
		if motion.action_stage=="hold":held_socket=maxf(held_socket,socket_gap);held_finger=maxf(held_finger,finger_gap)
		for point in posed:finite=finite and point.is_finite()
		finite=finite and motion.finite
		rows.append({"frame":frame,"t":float(frame+1)/hz,"stage":motion.action_stage,"warm_bow":motion.warm_bow,"maximum_actual_string_vertex_step_m":step.maximum_m,"worst_string_sample":step.sample_index,"nock_local":[nock.x,nock.y,nock.z],"nock_hand_gap_m":socket_gap,"nearest_draw_finger_skin_m":finger_gap,"release_count":motion.release_count})
		previous=posed
	var result:={"mode":mode,"hz":hz,"configured":true,"setup_ok":setup_ok,"requested":requested,"invalid_request_rejected":rejected,"rejected_request_preserves_entry_cache":rejected_cache_unchanged,"actual_string_vertices":sampled.string.size(),"actual_distal_draw_vertices":sampled.draw_fingers.size(),"first_frame_string_vertex_step_m":rows[0].maximum_actual_string_vertex_step_m,"maximum_held_socket_gap_m":held_socket,"maximum_held_finger_skin_gap_m":held_finger,"finite":finite,"rows":rows,"string_samples":sampled.string.map(func(p):return {"mesh":p.mesh,"surface":p.surface,"vertex":p.vertex}),"bone_parent":str(motion.rig.get_bone_name(motion.rig.get_bone_parent(motion.rig.find_bone("bowstring"))))}
	actor.free();return result
func run() -> void:
	if not output.is_absolute_path() or FileAccess.file_exists(output):printerr("Usefreshabsoluteoutput");quit(2);return
	var before:=FileAccess.get_sha256(motion_path);var trials:=[]
	for hz in [30.,60.,120.]:
		for mode in ["cold","warm_aim","retrigger","reset_cold","cancel_reaim","respawn_reaim"]:
			var trial:=execute(mode,hz);trials.append(trial);print("WARM_DRAW_CONTACT ",mode," ",hz," actual_string_step=",trial.get("first_frame_string_vertex_step_m"))
	var report:={"schema_version":1,"scope":"Actual accepted RamaBow skin vertices and distal finger contact over normal advancing draws. No newhero or rendered-quality acceptance.","trials":trials,"motion_source":motion_path,"motion_sha256":before,"motion_unchanged":before==FileAccess.get_sha256(motion_path),"hero_sha256":FileAccess.get_sha256(HERO),"library_sha256":FileAccess.get_sha256("res://assets/animations/rama_hero_motion.tres"),"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"sampler_sha256":FileAccess.get_sha256("res://tools/hero-family-reuse/motion_skin_contacts.gd"),"runtime_promoted":false}
	var file:=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");file.close();print("WARM_DRAW_CONTACT_COMPLETE ",trials.size());quit(0 if report.motion_unchanged else 1)
