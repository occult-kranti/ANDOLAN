extends SceneTree
## W5 actual-rig continuous transitions and zero-time event/contact witnesses.
## Reuses current Rama controller, clip library and contact-sampling approach.
const HERO := "res://assets/heroes/rama-hero.glb"
var output := ""
var motion_path := "res://scripts/rama_motion.gd"
var trials: Array = []
var source_before := {}
var diagnostic_event_resample := false
var pending_event := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--motion-source="): motion_path = arg.trim_prefix("--motion-source=")
		elif arg=="--diagnostic-event-resample": diagnostic_event_resample=true
	call_deferred("run")

func find_node(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := find_node(child,kind)
		if found: return found
	return null

func pins() -> Dictionary:
	var result := {}
	for path in [HERO,"res://assets/animations/rama_hero_motion.tres",motion_path]: result[path] = FileAccess.get_sha256(path)
	return result

func snapshot(motion: Node) -> Dictionary:
	var result := {"bones":[],"sockets":{},"action":motion.action,"stage":motion.action_stage,"locomotion":motion.locomotion,"nocked":motion.nocked,"releases":motion.release_count,"finite":motion.finite}
	for index in motion.rig.get_bone_count():
		var transform: Transform3D = motion.last_globals[index]
		result.bones.append({"name":str(motion.rig.get_bone_name(index)),"position":transform.origin,"rotation":transform.basis.get_rotation_quaternion().normalized()})
		result.finite = result.finite and transform.origin.is_finite() and transform.basis.is_finite()
	for name_ in ["bow_grip","draw_hand","string_nock","arrow_muzzle","head"]:
		result.sockets[name_] = motion.socket_global(name_).origin
	return result

func difference(a: Dictionary,b: Dictionary) -> Dictionary:
	var displacement := 0.0; var angle := 0.0; var worst := ""; var socket := 0.0
	for index in a.bones.size():
		var delta: float = a.bones[index].position.distance_to(b.bones[index].position)
		if delta > displacement: displacement=delta; worst=a.bones[index].name
		angle=maxf(angle,a.bones[index].rotation.angle_to(b.bones[index].rotation))
	for name_ in a.sockets: socket=maxf(socket,a.sockets[name_].distance_to(b.sockets[name_]))
	return {"maximum_joint_delta_m":displacement,"maximum_joint_angle_rad":angle,"worst_joint":worst,"maximum_socket_delta_m":socket}

func tick(actor: Node3D,motion: Node,state: Dictionary,hz: float,frames: int,rows: Array) -> void:
	for frame in frames:
		var previous := snapshot(motion)
		actor.position += Vector3(state.velocity)/hz
		motion.update_motion(1.0/hz,state); motion.evaluate_pose()
		var now := snapshot(motion); var delta := difference(previous,now)
		if not pending_event.is_empty():
			pending_event.delta=difference(pending_event._before,now)
			pending_event.after_stage=now.stage;pending_event.after_action=now.action
			pending_event.after_sockets=vectors(now.sockets);pending_event.finite=now.finite
			pending_event.sample_dt=1.0/hz;pending_event.erase("_before");pending_event={}
		var string_error: float = now.sockets.string_nock.distance_to(now.sockets.draw_hand)
		rows.append({"frame":rows.size(),"stage":now.stage,"action":now.action,"locomotion":now.locomotion,"finite":now.finite,"nocked":now.nocked,"release_count":now.releases,"delta":delta,"held_string_contact_m":string_error if now.nocked and now.stage=="hold" else null,"support_error_m":motion.max_contact_error})

func event(motion: Node,label: String,kind: String,id: String,events: Array) -> void:
	var before := snapshot(motion); var accepted := true
	if kind=="request": accepted=motion.request_action(id,.18,.22)
	elif kind=="release": accepted=motion.release_action(id)
	elif kind=="cancel": motion.cancel_action(label)
	if diagnostic_event_resample:
		motion.evaluate_pose()
		var after := snapshot(motion);var delta:=difference(before,after)
		events.append({"label":label,"kind":kind,"id":id,"accepted":accepted,"before_stage":before.stage,"after_stage":after.stage,"before_action":before.action,"after_action":after.action,"delta":delta,"before_sockets":vectors(before.sockets),"after_sockets":vectors(after.sockets),"no_clock_advanced":true,"finite":after.finite})
	else:
		pending_event={"label":label,"kind":kind,"id":id,"accepted":accepted,"before_stage":before.stage,"before_action":before.action,"before_sockets":vectors(before.sockets),"no_clock_advanced":false,"_before":before}
		events.append(pending_event)

func vectors(data: Dictionary) -> Dictionary:
	var result := {}
	for key in data:result[key]=[data[key].x,data[key].y,data[key].z]
	return result

func execute(hz: float,mode: String) -> Dictionary:
	var actor: Node3D=load(HERO).instantiate();root.add_child(actor)
	var motion=load(motion_path).new()
	if not motion.configure(actor,find_node(actor,"AnimationPlayer")):
		actor.free();return {"configured":false,"hz":hz,"mode":mode}
	motion.evaluate_pose();var state:={"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"floor_y":0.0,"grounded":true,"aiming":false,"aim_pitch":0.0,"aim_yaw":0.0}
	if mode=="running":state.velocity=Vector3(0,0,6);state.local_velocity=state.velocity
	elif mode=="aimed_strafe":state.velocity=Vector3(4,0,2);state.local_velocity=state.velocity;state.aiming=true;state.aim_pitch=.45;state.aim_yaw=.3
	var rows:=[];var events:=[]
	tick(actor,motion,state,hz,int(hz*.5),rows)
	event(motion,"idle_or_run_to_draw","request","kodanda",events);tick(actor,motion,state,hz,int(hz*.5),rows)
	event(motion,"held_draw_to_release","release","kodanda",events);tick(actor,motion,state,hz,maxi(1,int(hz*.08)),rows)
	event(motion,"release_interrupted_by_hit","request","hit",events);tick(actor,motion,state,hz,int(hz*.25),rows)
	event(motion,"hit_release","release","hit",events);tick(actor,motion,state,hz,int(hz*.45),rows)
	event(motion,"living_to_death","request","death",events);tick(actor,motion,state,hz,int(hz*.4),rows)
	event(motion,"death_commit","release","death",events);tick(actor,motion,state,hz,int(hz*.4),rows)
	event(motion,"death_to_respawn","request","respawn",events);tick(actor,motion,state,hz,int(hz*.3),rows)
	event(motion,"respawn_release","release","respawn",events);tick(actor,motion,state,hz,int(hz*.5),rows)
	event(motion,"post_respawn_draw","request","piercing_dawn",events);tick(actor,motion,state,hz,int(hz*.3),rows)
	event(motion,"cancel_draw","cancel","piercing_dawn",events);tick(actor,motion,state,hz,int(hz*.4),rows)
	var finite:=true;var held_error:=0.0;var maximum_event:=0.0;var worst_event:={};var maximum_frame:=0.0
	for row in rows:
		finite=finite and row.finite;maximum_frame=maxf(maximum_frame,row.delta.maximum_joint_delta_m)
		if row.held_string_contact_m!=null:held_error=maxf(held_error,float(row.held_string_contact_m))
	for row in events:
		finite=finite and row.finite
		if row.delta.maximum_joint_delta_m>maximum_event:maximum_event=row.delta.maximum_joint_delta_m;worst_event=row
	var result:={"configured":true,"mode":mode,"hz":hz,"frame_count":rows.size(),"finite":finite,"maximum_held_string_contact_m":held_error,"maximum_event_joint_step_m":maximum_event,"maximum_per_frame_joint_step_m":maximum_frame,"worst_event":worst_event,"events":events,"frames":rows,"clip_count":motion.library.get_animation_list().size(),"final":motion.diagnostics()}
	actor.free();return result

func run() -> void:
	if not output.is_absolute_path() or FileAccess.file_exists(output):printerr("Use fresh absolute output path");quit(2);return
	source_before=pins()
	for hz in [30.0,60.0,120.0]:
		for mode in ["idle","running","aimed_strafe"]:
			var trial:=execute(hz,mode);trials.append(trial)
			print("MOTION_CONTINUITY_TRIAL ",mode," ",hz," finite=",trial.get("finite")," event_step=",trial.get("maximum_event_joint_step_m")," held_contact=",trial.get("maximum_held_string_contact_m"))
	var report:={"schema_version":1,"scope":"Actual accepted Rama164bone rig and23runtimeclips; continuous numerical transition/contact assessment only. No newhero, render or human-feel acceptance.","trials":trials,"source_sha256":source_before,"source_after_sha256":pins(),"sources_unchanged":source_before==pins(),"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"runtime_promoted":false}
	report.event_sampling="diagnostic_extra_evaluation_without_clock" if diagnostic_event_resample else "normal_next_update_once_per_frame"
	var file:=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");file.close();print("MOTION_CONTINUITY_ASSESSMENT_COMPLETE ",trials.size());quit(0 if report.sources_unchanged else 1)
