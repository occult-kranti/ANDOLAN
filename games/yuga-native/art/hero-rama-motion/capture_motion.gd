extends "res://tools/capture-hero.gd"
const Motion = preload("res://scripts/rama_motion.gd")
var motion: SkeletonModifier3D
var sample_hz := 24.0
var pins := {}
var take := "preview"
var sequence := [
	{"id":"idle","seconds":.7},
	{"id":"walk","seconds":.8,"velocity":Vector3(0,0,2)},
	{"id":"run","seconds":1.0,"velocity":Vector3(0,0,6)},
	{"id":"kodanda","seconds":1.2,"velocity":Vector3(0,0,4),"action":"kodanda","windup":.18,"recovery":.22},
	{"id":"piercing","seconds":1.2,"action":"piercing_dawn","windup":.65,"recovery":.30},
	{"id":"idle","seconds":.5},
	{"id":"grip","seconds":.7,"close":true},
]
func _run() -> void:
	width=640; height=640; timeout_seconds=600
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output_path=arg.trim_prefix("--output=")
		elif arg.begins_with("--asset="): asset_path=arg.trim_prefix("--asset=")
		elif arg=="--full": take="full"
		elif arg=="--side": take="side"
		else: failure="Unknown argument: "+arg
	if take=="full":
		sequence.insert(3,{"id":"sprint","seconds":1.0,"velocity":Vector3(0,0,9)})
		sequence.insert(4,{"id":"strafe","seconds":1.0,"velocity":Vector3(4,0,0),"aiming":true})
		sequence.insert(5,{"id":"jump","seconds":.5,"velocity":Vector3(0,3,2),"grounded":false})
		sequence.insert(6,{"id":"fall","seconds":.5,"velocity":Vector3(0,-3,2),"grounded":false})
		sequence.insert(7,{"id":"land","seconds":.4})
		sequence.insert(8,{"id":"dash","seconds":.7,"action":"measured_step","windup":.1,"recovery":.25,"velocity":Vector3(0,0,3)})
		sequence.insert(9,{"id":"flight","seconds":1.0,"traversal":"flight","grounded":false})
		sequence.insert(10,{"id":"grapple","seconds":1.0,"traversal":"grapple","grounded":false})
		sequence.insert(13,{"id":"circle","seconds":1.2,"action":"guardian_circle","windup":.55,"recovery":.30})
		sequence.insert(14,{"id":"volley","seconds":1.8,"action":"dawn_volley","windup":.95,"recovery":.55})
		sequence.insert(15,{"id":"cancel","seconds":.7,"action":"piercing_dawn","windup":.65,"recovery":.30,"cancel_at":.28})
		sequence.append({"id":"draw_detail","seconds":1.5,"action":"piercing_dawn","windup":.85,"recovery":.30,"close":true})
		sequence.append({"id":"ready_draw_1","seconds":.42,"action":"kodanda","windup":.18,"recovery":.22,"aiming":true,"aim_pitch":.2,"aim_yaw":.4})
		sequence.append({"id":"ready_draw_2","seconds":.42,"action":"kodanda","windup":.18,"recovery":.22,"aiming":true,"aim_pitch":.2,"aim_yaw":.4})
		sequence.append({"id":"ready_draw_3","seconds":.42,"action":"kodanda","windup":.18,"recovery":.22,"aiming":true,"aim_pitch":.2,"aim_yaw":.4})
		sequence.append({"id":"hit","seconds":.6,"action":"hit","windup":.06,"recovery":.22,"immediate":true})
		sequence.append({"id":"death","seconds":1.2,"action":"death","windup":.12,"recovery":.8,"immediate":true})
		sequence.append({"id":"respawn","seconds":1.2,"action":"respawn","windup":.1,"recovery":.7,"immediate":true})
		sequence.append({"id":"idle_after_respawn","seconds":.5})
	elif take=="side":
		sequence=[{"id":"idle","seconds":.5},
			{"id":"strafe_right","seconds":1.2,"velocity":Vector3(4,0,0),"aiming":true},
			{"id":"return_idle","seconds":.3},
			{"id":"strafe_left","seconds":1.2,"velocity":Vector3(-4,0,0),"aiming":true},
			{"id":"return_idle","seconds":.3},
			{"id":"side_walk","seconds":.8,"velocity":Vector3(2,0,0)},
			{"id":"return_idle","seconds":.5}]
	if not failure.is_empty() or not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path):
		push_error("Require new absolute output and valid arguments. "+failure); quit(1); return
	DirAccess.make_dir_recursive_absolute(output_path)
	if DisplayServer.get_name()=="headless" or not _validate_import():
		failure="Require actual renderer/current import. "+failure; _finish(false); return
	for path in [asset_path,"res://scripts/rama_motion.gd",Motion.LIBRARY_PATH,"res://art/hero-rama-motion/capture_motion.gd","res://tools/capture-hero.gd"]:
		pins[path]=FileAccess.get_sha256(path)
	root.size=Vector2i(width,height); root.content_scale_size=root.size; root.msaa_3d=Viewport.MSAA_2X; root.show()
	_make_studio()
	# Actual world-space floor ticks make translated support/sliding inspectable.
	var mat:=StandardMaterial3D.new(); mat.albedo_color=Color(.36,.43,.47)
	for i in range(-15,16):
		var line:=MeshInstance3D.new(); var mesh:=BoxMesh.new(); mesh.size=Vector3(30,.002,.018)
		line.mesh=mesh; line.material_override=mat; line.position=Vector3(0,.002,float(i)); studio.add_child(line)
	hero=load(asset_path).instantiate(); studio.add_child(hero)
	animator=_find_animation(hero); _collect_skeletons(hero)
	motion=Motion.new()
	if not motion.configure(hero,animator): failure="Configure failed"; _finish(false); return
	motion.active=false
	await _draw_frames(3)
	var index:=0
	for part in sequence.size():
		var spec: Dictionary=sequence[part]
		if spec.has("action"): motion.request_action(spec.action,spec.windup,spec.recovery)
		var released:=false
		var cancelled:=false
		for frame in ceili(spec.seconds*sample_hz):
			var time:=frame/sample_hz
			if spec.has("cancel_at") and not cancelled and time>=spec.cancel_at:
				motion.cancel_action("staged interrupt"); cancelled=true
			if spec.has("action") and not released and not cancelled and (spec.get("immediate",false) or time>=spec.windup):
				motion.release_action(spec.action); released=true
			var velocity: Vector3=spec.get("velocity",Vector3.ZERO)
			var airborne_height:=0.0
			if spec.id=="jump": airborne_height=sin(time/.5*PI/2)*.6
			elif spec.id=="fall": airborne_height=cos(time/.5*PI/2)*.6
			elif spec.id in ["flight","grapple"]: airborne_height=.7
			hero.position.y=airborne_height
			hero.position+=Vector3(velocity.x,0,velocity.z)/sample_hz
			if hero.position.z>12: hero.position.z-=20; motion.foot_locks={"L":false,"R":false}
			motion.update_motion(1/sample_hz,{"velocity":velocity,"local_velocity":velocity,"grounded":spec.get("grounded",true),"traversal":spec.get("traversal","ground"),"aiming":spec.get("aiming",false),"aim_pitch":spec.get("aim_pitch",0.0),"aim_yaw":spec.get("aim_yaw",0.0),"floor_y":0.0})
			motion.evaluate_pose()
			if spec.get("close",false):
				var grip: Vector3=motion.socket_global("bow_grip").origin
				camera.position=grip+Vector3(-.65,.12,.85); camera.look_at(grip)
				if spec.id=="draw_detail": camera.position=grip+Vector3(-.95,.28,1.35); camera.look_at(grip+Vector3(.14,.04,-.13))
			else:
				camera.position=hero.position+Vector3(2.7,1.3,4.4); camera.look_at(hero.position+Vector3(0,1.02,0))
			footer.text="%s · %s / %s\nOriginal authored motion · 24 Hz staged continuous take"%[spec.id,motion.locomotion,motion.action_stage]
			await _draw_frames(1)
			var image:=root.get_texture().get_image()
			var filename:="frame-%05d.png"%index
			if image.is_empty() or image.save_png(output_path.path_join(filename))!=OK: failure="Frame write failed"; _finish(false); return
			shots.append({"file":filename,"sha256":FileAccess.get_sha256(output_path.path_join(filename)),"segment":spec.id,"time":time,"pose":motion.diagnostics(),"hero_position":_vector(hero.position),"rendered_frame_counter":Engine.get_frames_drawn()})
			index+=1
			if Time.get_ticks_msec()-started_ms>timeout_seconds*1000: failure="Timed out"; _finish(false); return
	for path in pins:
		if FileAccess.get_sha256(path)!=pins[path]: failure="Source changed: "+path
	_finish(failure.is_empty())
func _finish(success: bool) -> void:
	if completed: return
	completed=true
	var report:={"complete":success,"failure":failure,"sources":pins,"imported_resource":imported_resource,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"display":DisplayServer.get_name(),"width":width,"height":height,"sample_hz":sample_hz,"frames":shots,"scope":"Actual sequential staged render with translated ground. Separate from gameplay capture and hardware performance."}
	FileAccess.open(output_path.path_join("motion-capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	print("RAMA_MOTION_CAPTURE ",success," ",shots.size()," ",failure)
	quit(0 if success else 1)
