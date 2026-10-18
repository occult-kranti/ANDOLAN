extends SceneTree
## Actual imported mesh + runtime state samples. CPU skinning is independently
## evaluated by role05/analyze_deformation.py; this script does no GLTF import.
var output := "/tmp/visual-round-face-cases.json"
var checks: Array[Dictionary] = []
var samples: Array[Dictionary] = []
var scene: Node3D
var face: Node
var motion: Node
var rig: Skeleton3D
var face_mesh: MeshInstance3D
var events: Array[Dictionary] = []

func vectors(data: PackedVector3Array) -> Array:
	var result := []
	for v in data: result.append([v.x,v.y,v.z])
	return result

func export_imported_meshes() -> Dictionary:
	var result := {"meshes":[],"scope":"Actual ResourceLoader imported arrays before any test mutation; skin matrices use named bones."}
	var body: MeshInstance3D=scene.player.visual.find_child("RamaHero",true,false)
	for node: MeshInstance3D in [face_mesh,body]:
		var binds := []
		for i in node.skin.get_bind_count():
			var name_: String=String(node.skin.get_bind_name(i))
			if name_.is_empty(): name_=String(rig.get_bone_name(node.skin.get_bind_bone(i)))
			binds.append({"name":name_,"inverse":matrix(node.skin.get_bind_pose(i))})
		for s in node.mesh.get_surface_count():
			var material: Material=node.mesh.surface_get_material(s)
			var material_name: String=material.resource_name if material else ""
			if node!=face_mesh and material_name not in ["Rama warm skin","Warm sclera","Deep brown iris","Pupil","Natural lips"]: continue
			var a: Array=node.mesh.surface_get_arrays(s)
			var morphs := []
			for m: Array in node.mesh.surface_get_blend_shape_arrays(s): morphs.append(vectors(m[Mesh.ARRAY_VERTEX]))
			var names := []
			for i in node.mesh.get_blend_shape_count(): names.append(String(node.mesh.get_blend_shape_name(i)))
			result.meshes.append({"node":String(node.name),"surface":s,"material":material_name,"positions":vectors(a[Mesh.ARRAY_VERTEX]),"indices":Array(a[Mesh.ARRAY_INDEX]),"joints":Array(a[Mesh.ARRAY_BONES]),"weights":Array(a[Mesh.ARRAY_WEIGHTS]),"binds":binds,"shape_names":names,"shape_positions":morphs,"blend_shape_mode":node.mesh.blend_shape_mode})
	return result

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, ok: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":ok,"details":detail})
	print("PASS " if ok else "FAIL ",label)

func matrix(t: Transform3D) -> Array:
	return [[t.basis.x.x,t.basis.y.x,t.basis.z.x,t.origin.x],
		[t.basis.x.y,t.basis.y.y,t.basis.z.y,t.origin.y],
		[t.basis.x.z,t.basis.y.z,t.basis.z.z,t.origin.z],[0,0,0,1]]

func morph_weights() -> Dictionary:
	var result := {}
	for i in face_mesh.mesh.get_blend_shape_count():
		result[String(face_mesh.mesh.get_blend_shape_name(i))]=face_mesh.get_blend_shape_value(i)
	return result

func pose() -> Dictionary:
	var result := {}
	for i in rig.get_bone_count(): result[String(rig.get_bone_name(i))]=matrix(rig.get_bone_global_pose(i))
	return result

func sample(label: String, extra: Dictionary={}) -> void:
	var current := {"id":label,"face":face.report(),"morph_weights":morph_weights(),"motion":motion.diagnostics(),"bone_global_poses":pose(),"extra":extra}
	samples.append(current)
	var valid := true
	for i in rig.get_bone_count():
		var t := rig.get_bone_global_pose(i)
		valid=valid and t.origin.is_finite() and t.basis.x.is_finite() and t.basis.y.is_finite() and t.basis.z.is_finite()
	check(label+": finite actual 164-bone pose and four target weights",valid and rig.get_bone_count()==164 and morph_weights().size()==4)

func advance_face(seconds: float, state: Dictionary={}) -> void:
	var left := seconds
	while left>0.0000001:
		var dt := minf(left,1.0/120.0)
		face.update_facial(dt,state)
		left-=dt

func disable_steps() -> void:
	scene.set_process(false); scene.set_physics_process(false)
	scene.player.set_physics_process(false)
	scene.practice_army.set_physics_process(false)
	scene.rama_runtime.effects.set_process(false)

func advance_play(seconds: float) -> void:
	var left := seconds
	while left>0.000001:
		var dt := minf(.05,left)
		scene.practice_army.step_simulation(dt)
		var visual_left := dt
		while visual_left>0.000001:
			var vd := minf(1.0/60.0,visual_left)
			scene.player._physics_process(vd)
			motion.evaluate_pose()
			visual_left-=vd
		left-=dt

func neutral() -> void:
	scene.reset_training()
	scene.start_training()
	disable_steps()
	for i in 12:
		scene.player._physics_process(1.0/60.0)
		motion.evaluate_pose()
	face.reset("face probe")
	events.clear()

func event_count(kind: String) -> int:
	var count := 0
	for event in events:
		if event.get("kind")==kind: count+=1
	return count

func run() -> void:
	scene=load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	face=scene.player.rama_face; motion=scene.player.rama_motion; rig=motion.rig
	face_mesh=face._mesh
	disable_steps()
	scene.rama_runtime.combat_event.connect(func(event: Dictionary): events.append(event.duplicate(true)))
	check("Actual imported near mesh has one configured face writer and authored half targets",face.configured and face.report().owned_meshes==1 and face.report().half_correctives and face_mesh.get_meta(face.OWNER_META)==face.get_instance_id())
	var duplicate=load("res://scripts/rama_facial_performance.gd").new()
	scene.player.visual.add_child(duplicate)
	check("A second face writer cannot bind the actual mesh",not duplicate.configure(scene.player.visual))
	duplicate.free()
	check("Actual rig and external runtime library retain 164 bones and 23 clips",rig.get_bone_count()==164 and motion.library.get_animation_list().size()==23)
	var imported_mesh_path := output.get_basename()+"-meshes.json"
	FileAccess.open(imported_mesh_path,FileAccess.WRITE).store_string(JSON.stringify(export_imported_meshes())+"\n")
	neutral()
	var original_pose := pose()
	sample("rest")
	for target in [0.25,0.5,0.75,1.0]:
		face.reset("public blink timeline")
		var time: float=3.15+.055*target if target<1 else 3.215
		advance_face(time)
		var value: float=face.report().weights.rama_blink_left
		var expected: float=target*target*(3-2*target) if target<1 else 1.0
		var weights := morph_weights()
		check("Blink %s uses max/full/half interpolation"%target,absf(value-expected)<.000001 and absf(float(weights.rama_blink_left)-maxf(0,2*value-1))<.000001 and absf(float(weights.rama_blink_half_left)-(1-absf(2*value-1)))<.000001)
		sample("blink_%s"%target)
	check("Actual facial updates do not change skeleton poses",pose()==original_pose)
	for time in [.6,3.16375,3.1775,3.215]:
		face.reset("combined blink effort")
		advance_face(time,{"effort":1.0})
		var age: float=time-3.15
		var b := 0.0
		if age>=0 and age<.055:
			var t: float=age/.055; b=t*t*(3-2*t)
		elif age>=.055 and age<.080: b=1
		var expected := maxf(b,float(face.report().effort)*.14)
		check("Combined blink/effort uses maximum at %s"%time,absf(float(face.report().weights.rama_blink_left)-expected)<.000001)
		sample("combined_%s"%time)
	face.reset("pause partial"); advance_face(3.1775,{"effort":1.0})
	var before: Dictionary=face.report(); var weights_before := morph_weights()
	for i in 30: face.update_facial(.1,{"paused":true,"alive":false,"effort":1.0})
	check("Pausing actual partial blink freezes clocks and all four weights",before==face.report() and weights_before==morph_weights())
	face.update_facial(1.0/60,{"teleported":true})
	check("Teleport clears actual blink state",face.report().blink_index==0 and face.report().blink_clock==0 and morph_weights().values().all(func(v):return v==0))
	face.update_facial(.1,{"effort":1.0}); face.update_facial(.1,{"reset":true})
	check("Reset restores zero clocks and actual target values",face.report().elapsed==0 and face.report().blink_clock==0 and morph_weights().values().all(func(v):return v==0))
	for aim in [Vector2(-.85,-.70),Vector2(-.85,.70),Vector2(.65,-.70),Vector2(.65,.70)]:
		motion.cancel("aim extreme"); face.reset("aim extreme")
		for i in 90:
			motion.update_motion(1.0/60,{"grounded":true,"aiming":true,"aim_pitch":aim.x,"aim_yaw":aim.y})
			motion.evaluate_pose()
		for target in [0.0,.5,1.0]:
			face.reset("aim blink")
			if target>0: advance_face(3.1775 if target==.5 else 3.215,{"effort":1.0})
			sample("aim_%s_%s_blink_%s"%[aim.x,aim.y,target])
	for id in ["kodanda","piercing_dawn","measured_step","guardian_circle","dawn_volley"]:
		neutral()
		var result: Dictionary=scene.rama_runtime.cast_ability(id)
		check(id+": real gameplay cast accepted",result.get("accepted",false))
		if not result.get("accepted",false): continue
		var begin: Dictionary=events[0]
		var release_tick := ceilf(float(begin.timing.windup_s)/.05-.0000001)*.05
		advance_play(maxf(0,release_tick-.05))
		sample(id+"_windup",{"authority_release_count":event_count("release")})
		advance_play(.05)
		check(id+": authority owns one release",event_count("release")==1 and motion.action_stage=="recovery")
		sample(id+"_release",{"authority_release_count":event_count("release")})
		advance_play(.10)
		sample(id+"_recoil")
		var held_pose := pose(); var held_face: Dictionary=face.report(); var held_weights := morph_weights()
		scene.set_paused(true)
		await process_frame
		await process_frame
		check(id+": real scene pause holds head/neck and eyelids",held_pose==pose() and held_face==face.report() and held_weights==morph_weights())
		scene.set_paused(false)
		scene.reset_training()
		check(id+": gameplay reset clears actual eyelids",face.report().blink_clock==0 and face.report().blink_index==0 and morph_weights().values().all(func(v):return v==0))
	neutral()
	scene.rama_runtime.cast_ability("piercing_dawn"); advance_play(.25)
	scene.rama_runtime.kit.cancel_active("face probe cancellation")
	advance_play(.6)
	check("Actual cancellation fades effort and leaves no action",event_count("cancel")==1 and event_count("release")==0 and motion.action_stage=="none" and float(face.report().weights.rama_blink_left)<.001)
	sample("cancel_recovered")
	var rest_poses := {}
	for i in rig.get_bone_count(): rest_poses[String(rig.get_bone_name(i))]=matrix(rig.get_bone_global_rest(i))
	var paths := ["res://assets/heroes/rama-hero.glb","res://scripts/rama_facial_performance.gd","res://scripts/rama_motion.gd","res://scripts/player.gd","res://scripts/rama_hero_runtime.gd","res://assets/animations/rama_hero_motion.tres",get_script().resource_path]
	var pins := {}
	for path in paths: pins[path]=FileAccess.get_sha256(path)
	var passed := checks.all(func(c):return c.passed)
	var report := {"task":"R2-05","passed":passed,"count":checks.size(),"checks":checks,"samples":samples,"bone_global_rests":rest_poses,"source_pins":pins,"imported_mesh_path":imported_mesh_path,"imported_mesh_sha256":FileAccess.get_sha256(imported_mesh_path),"scope":"Actual existing imported scene; public face clock/effort and gameplay casts, pause/reset/cancel. Matrices and actual imported target weights feed separate CPU-skinning checks. No render or new import in this test."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	scene.queue_free()
	await process_frame
	quit(0 if passed else 1)
