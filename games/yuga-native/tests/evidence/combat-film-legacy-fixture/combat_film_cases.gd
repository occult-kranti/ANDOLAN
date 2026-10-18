extends SceneTree
## Independent loaded-animation and viewer integration QA. Rendering is separate.

const FILM_PATH := "res://assets/cinematics/confluence-duel.json"
const REQUIRED_CLIPS := ["ready","draw","release","guard","recoil","evade","cast_windup","cast_release","defeat"]
const STATIONARY_CLIPS := ["ready","draw","release","guard","recoil","cast_windup","cast_release"]

class ProbeActor extends Node3D:
	var skeleton: Skeleton3D
	var animator: AnimationPlayer
	var model: Node3D

var checks: Array[Dictionary] = []
var manifest: Dictionary = {}
var sources: Dictionary = {}
var actors: Dictionary = {}
var soles: Dictionary = {}
var viewer: Node
var actors_only := false
var output := ""
var skin_root_influences := 0
const BODY_BRANCHES := ["pelvis.L","pelvis.R","spine05"]
const TRANSLATION_CONTROLS := ["pelvis.L","pelvis.R","spine05","bowstring"]

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg=="--actors-only": actors_only=true
		elif arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("_run")

func _run() -> void:
	manifest=JSON.parse_string(FileAccess.get_file_as_string(FILM_PATH))
	for path in [FILM_PATH,"res://tests/combat_film_cases.gd"]:
		sources[path]=FileAccess.get_sha256(path)
	for spec in manifest.actors:
		for path in [spec.model_path,spec.animation_library_path]: sources[path]=FileAccess.get_sha256(path)
	await _library_checks()
	if not actors_only:
		await _viewer_checks()
	var unchanged := true
	for path in sources: unchanged=unchanged and sources[path]==FileAccess.get_sha256(path)
	_record("sampled sources unchanged",unchanged,{})
	await _finish()

func _find(node: Node,kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var result := _find(child,kind)
		if result: return result
	return null

func _finite_transform(transform_: Transform3D) -> bool:
	return transform_.origin.is_finite() and transform_.basis.x.is_finite() and transform_.basis.y.is_finite() and transform_.basis.z.is_finite()

func _capture_bones(skeleton: Skeleton3D) -> Array:
	skeleton.force_update_all_bone_transforms()
	var result := []
	for bone in skeleton.get_bone_count(): result.append(skeleton.get_bone_global_pose(bone))
	return result

func _collect_skin(node: Node,skeleton: Skeleton3D,result: Array) -> void:
	if node is MeshInstance3D and node.skin:
		var binds := []
		for index in node.skin.get_bind_count():
			var bone_name := String(node.skin.get_bind_name(index))
			var bone: int=skeleton.find_bone(bone_name) if not bone_name.is_empty() else node.skin.get_bind_bone(index)
			binds.append({"bone":bone,"inverse":node.skin.get_bind_pose(index)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array=node.mesh.surface_get_arrays(surface)
			var points: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var joints: PackedInt32Array=arrays[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			if points.is_empty(): continue
			var stride: int=joints.size()/points.size()
			for vi in points.size():
				var influences := []
				var rest_point := Vector3.ZERO
				var largest := -1.0
				var dominant := -1
				for slot in stride:
					var weight: float=weights[vi*stride+slot]
					if weight<=0: continue
					var bind: Dictionary=binds[joints[vi*stride+slot]]
					if bind.bone<0: continue
					if String(skeleton.get_bone_name(bind.bone))=="root": skin_root_influences+=1
					var local: Vector3=bind.inverse*points[vi]
					influences.append({"bone":bind.bone,"local":local,"weight":weight})
					rest_point+=(skeleton.get_bone_global_rest(bind.bone)*local)*weight
					if weight>largest:
						largest=weight
						dominant=bind.bone
				var name_:=String(skeleton.get_bone_name(dominant)) if dominant>=0 else ""
				if name_.begins_with("foot") or name_.begins_with("toe"):
					result.append({"influences":influences,"side":"L" if name_.ends_with(".L") else "R","rest_y":rest_point.y})
	for child in node.get_children(): _collect_skin(child,skeleton,result)

func _sole_cohort(actor: Node3D,skeleton: Skeleton3D) -> Array:
	var candidates := []
	skin_root_influences=0
	_collect_skin(actor,skeleton,candidates)
	var lowest := {"L":INF,"R":INF}
	for point in candidates: lowest[point.side]=minf(lowest[point.side],point.rest_y)
	var selected := []
	for point in candidates:
		if point.rest_y<=lowest[point.side]+.015: selected.append(point)
	return selected

func _sole_positions(cohort: Array,skeleton: Skeleton3D,bones: Array) -> Dictionary:
	var result := {"L":[],"R":[]}
	for point in cohort:
		var vertex:=Vector3.ZERO
		for influence in point.influences: vertex+=(bones[influence.bone]*influence.local)*influence.weight
		result[point.side].append(skeleton.global_transform*vertex)
	return result

func _minimum_y(points: Array) -> float:
	var result:=INF
	for point: Vector3 in points: result=minf(result,point.y)
	return result

func _centroid(points: Array) -> Vector3:
	var result:=Vector3.ZERO
	for point: Vector3 in points: result+=point
	return result/maxi(1,points.size())

func _frames(count: int) -> void:
	for _i in count: await process_frame

func _library_checks() -> void:
	for spec in manifest.actors:
		var packed=load(spec.model_path)
		var library=load(spec.animation_library_path)
		if not packed is PackedScene or not library is AnimationLibrary:
			_record(spec.id+" actor resources load",false,{})
			continue
		var probe:=ProbeActor.new()
		probe.name="IndependentActorProbe"
		root.add_child(probe)
		probe.model=packed.instantiate()
		probe.add_child(probe.model)
		probe.skeleton=_find(probe.model,"Skeleton3D")
		for player in probe.model.find_children("*","AnimationPlayer",true,false):
			player.stop()
			player.active=false
		probe.animator=AnimationPlayer.new()
		probe.animator.name="IndependentFilmAnimation"
		probe.animator.root_node=NodePath("..")
		probe.animator.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		probe.model.add_child(probe.animator)
		probe.animator.add_animation_library("film",library)
		var present := true
		for clip in REQUIRED_CLIPS: present=present and probe.animator.has_animation("film/"+clip)
		_record(spec.id+" imported rig and clip coverage",is_instance_valid(probe.skeleton) and probe.skeleton.get_bone_count()==164 and present,{"bones":probe.skeleton.get_bone_count() if probe.skeleton else 0,"clips":library.get_animation_list()})
		if not probe.skeleton or not present:
			probe.queue_free()
			await _frames(2)
			continue
		probe.skeleton.reset_bone_poses()
		probe.skeleton.force_update_all_bone_transforms()
		var cohort := _sole_cohort(probe,probe.skeleton)
		_record(spec.id+" actual skinned sole cohort exists",cohort.size()>20,{"lowest_rest_foot_vertex_count":cohort.size(),"selection_depth_metres":.015})
		var root_influence_count:=skin_root_influences
		var branch_parents:={}
		for branch in BODY_BRANCHES:
			var index:=probe.skeleton.find_bone(branch)
			branch_parents[branch]=String(probe.skeleton.get_bone_name(probe.skeleton.get_bone_parent(index)))
		var finite_failures:=0
		var bone_samples:=0
		var path_errors:=[]
		var maximum_segment_error:=0.0
		var segment_errors_by_bone:={}
		var maximum_anatomical_segment_error:=0.0
		var maximum_branch_translation_disagreement:=0.0
		var maximum_body_control_offset:=0.0
		var minimum_stationary_sole:=INF
		var maximum_stationary_sole:=-INF
		var maximum_stationary_slip:=0.0
		var clip_metrics:=[]
		for clip: String in REQUIRED_CLIPS:
			var animation: Animation=library.get_animation(clip)
			for track in animation.get_track_count():
				var path: NodePath=animation.track_get_path(track)
				if path.get_subname_count()!=1 or probe.skeleton.find_bone(path.get_subname(0))<0 or probe.model.get_node_or_null(NodePath(path.get_concatenated_names()))!=probe.skeleton:
					path_errors.append({"clip":clip,"track":str(path)})
			probe.animator.stop()
			probe.skeleton.reset_bone_poses()
			probe.animator.play("film/"+clip,0)
			var anchor := {}
			var control_baselines:={}
			var control_metrics:={}
			for control in TRANSLATION_CONTROLS: control_metrics[control]={"phase0_rest_offset":0.0,"max_rest_offset":0.0,"max_within_clip_displacement":0.0}
			var low:=INF
			var high:=-INF
			var slip:=0.0
			for index in range(41):
				probe.animator.seek(animation.length*index/40.0,true)
				probe.animator.advance(0)
				var bones := _capture_bones(probe.skeleton)
				for bone in bones.size():
					bone_samples+=1
					if not _finite_transform(bones[bone]): finite_failures+=1
					if probe.skeleton.get_bone_parent(bone)>=0:
						var segment_error:=absf(probe.skeleton.get_bone_pose_position(bone).length()-probe.skeleton.get_bone_rest(bone).origin.length())
						var bone_name:=String(probe.skeleton.get_bone_name(bone))
						if segment_error>.005: segment_errors_by_bone[bone_name]=maxf(segment_errors_by_bone.get(bone_name,0),segment_error)
						maximum_segment_error=maxf(maximum_segment_error,segment_error)
						if not bone_name in TRANSLATION_CONTROLS: maximum_anatomical_segment_error=maxf(maximum_anatomical_segment_error,segment_error)
				var branch_deltas:=[]
				for control in TRANSLATION_CONTROLS:
					var bone:=probe.skeleton.find_bone(control)
					var delta: Vector3=probe.skeleton.get_bone_pose_position(bone)-probe.skeleton.get_bone_rest(bone).origin
					if index==0:
						control_baselines[control]=delta
						control_metrics[control].phase0_rest_offset=delta.length()
					control_metrics[control].max_rest_offset=maxf(control_metrics[control].max_rest_offset,delta.length())
					control_metrics[control].max_within_clip_displacement=maxf(control_metrics[control].max_within_clip_displacement,delta.distance_to(control_baselines[control]))
					if control in BODY_BRANCHES:
						branch_deltas.append(delta)
						maximum_body_control_offset=maxf(maximum_body_control_offset,delta.length())
				for delta: Vector3 in branch_deltas: maximum_branch_translation_disagreement=maxf(maximum_branch_translation_disagreement,delta.distance_to(branch_deltas[0]))
				var contacts:=_sole_positions(cohort,probe.skeleton,bones)
				for side in ["L","R"]:
					var floor_y:=_minimum_y(contacts[side])
					low=minf(low,floor_y)
					high=maxf(high,floor_y)
					var center:=_centroid(contacts[side])
					if index==0: anchor[side]=center
					var delta: Vector3=center-anchor[side]
					slip=maxf(slip,Vector2(delta.x,delta.z).length())
			if clip in STATIONARY_CLIPS:
				minimum_stationary_sole=minf(minimum_stationary_sole,low)
				maximum_stationary_sole=maxf(maximum_stationary_sole,high)
				maximum_stationary_slip=maxf(maximum_stationary_slip,slip)
			clip_metrics.append({"clip":clip,"length":animation.length,"minimum_sole_y":low,"maximum_foot_minimum_y":high,"maximum_sole_centroid_horizontal_drift":slip,"translation_controls":control_metrics})
		_record(spec.id+" all loaded animation bone poses finite",finite_failures==0 and path_errors.is_empty(),{"bone_samples":bone_samples,"invalid_transforms":finite_failures,"max_local_segment_length_error":maximum_segment_error,"segment_errors_by_bone":segment_errors_by_bone,"track_path_errors":path_errors})
		_record(spec.id+" anatomical segments retain length",maximum_anatomical_segment_error<=.005,{"maximum_anatomical_local_segment_length_error":maximum_anatomical_segment_error,"limit_metres":.005,"separately_disclosed_translation_controls":TRANSLATION_CONTROLS})
		_record(spec.id+" root branch translations are coordinated controls",root_influence_count==0 and branch_parents.values().all(func(value):return value=="root") and maximum_branch_translation_disagreement<=.005,{"root_weighted_vertex_influences":root_influence_count,"branch_parents":branch_parents,"maximum_branch_translation_disagreement":maximum_branch_translation_disagreement,"maximum_body_control_offset":maximum_body_control_offset,"scope":"These three child branches translate together under an unweighted root for authored crouch. They are not treated as physical limb segments; their rest offsets and within-clip variations remain explicitly reported. Bowstring translation is separately intentional."})
		_record(spec.id+" stationary clips have grounded fixed soles",minimum_stationary_sole>=-.02 and maximum_stationary_sole<=.03 and maximum_stationary_slip<=.025,{"minimum_stationary_sole_y":minimum_stationary_sole,"maximum_stationary_foot_minimum_y":maximum_stationary_sole,"maximum_stationary_horizontal_drift":maximum_stationary_slip,"clips":clip_metrics,"scope":"CPU skinning of actual loaded lowest-rest foot/toe vertex cohort at41phases perclip; numerical contact evidence, not visual acceptance."})
		probe.queue_free()
		await _frames(2)

func _wait_scene(path: String) -> bool:
	for _i in range(120):
		await process_frame
		if is_instance_valid(current_scene) and current_scene.scene_file_path==path:
			await _frames(3)
			return true
	return false

func _hash_variant(value: Variant) -> String:
	var hash_:=HashingContext.new()
	hash_.start(HashingContext.HASH_SHA256)
	hash_.update(var_to_bytes(value))
	return hash_.finish().hex_encode()

func _actual_snapshot() -> Dictionary:
	var result:={"actors":{},"camera":viewer.camera.global_transform,"fov":viewer.camera.fov,"effects":viewer.effects.diagnostics().state,"health":viewer.visual_health.duplicate(true)}
	for id in viewer.actors:
		var actor: Node3D=viewer.actors[id]
		result.actors[id]={"root":actor.global_transform,"bones":_capture_bones(actor.skeleton)}
	return result

func _inventory(node: Node,result: Dictionary) -> void:
	result.nodes.append(node.get_instance_id())
	if node is MeshInstance3D and node.mesh:
		result.resources[node.mesh.get_instance_id()]=true
		for surface in node.mesh.get_surface_count():
			var material: Material=node.get_active_material(surface)
			if material: result.resources[material.get_instance_id()]=true
	if node is AudioStreamPlayer: result.audio_players+=1
	for child in node.get_children(): _inventory(child,result)

func _expected_active_cues(time: float) -> Array:
	var result:=[]
	for cue in manifest.cues:
		if time>=cue.t_seconds and time<cue.t_seconds+cue.duration_seconds: result.append(cue.id)
	result.sort()
	return result

func _expected_health(time: float) -> Dictionary:
	var result:={}
	for spec in manifest.actors: result[spec.id]=spec.visual_health
	for receipt in manifest.visual_receipts:
		if receipt.t_seconds<=time: result[receipt.target_id]=receipt.health_after
	return result

func _runtime_validation() -> void:
	var cases:=[]
	var changed: Dictionary=manifest.duplicate(true)
	changed.actors.pop_back(); cases.append({"name":"missing actor","data":changed})
	changed=manifest.duplicate(true); changed.actions[0].t_seconds=-1; cases.append({"name":"negative action time","data":changed})
	changed=manifest.duplicate(true); changed.actions[0].duration_seconds=0; cases.append({"name":"zero action duration","data":changed})
	changed=manifest.duplicate(true); changed.actors[0].position[0]=NAN; cases.append({"name":"nonfinite actor coordinate","data":changed})
	changed=manifest.duplicate(true); changed.cues.append(changed.cues[0].duplicate(true)); cases.append({"name":"duplicate event","data":changed})
	changed=manifest.duplicate(true); changed.actors[1].model_path=changed.actors[0].model_path; cases.append({"name":"duplicate actor resource","data":changed})
	changed=manifest.duplicate(true); changed.motion_tracks[0].keys[1].t_seconds=0; cases.append({"name":"duplicate motion time","data":changed})
	changed=manifest.duplicate(true); changed.actions=[]; cases.append({"name":"missing actions","data":changed})
	changed=manifest.duplicate(true); changed.actors[0].model_path="res://assets/cinematics/does-not-exist.glb"; cases.append({"name":"missing model resource","data":changed})
	changed=manifest.duplicate(true); changed.actions[0].clip_id="missing_clip"; cases.append({"name":"missing animation clip","data":changed})
	changed=manifest.duplicate(true); changed.actions[1].t_seconds=1; cases.append({"name":"overlapping actor actions","data":changed})
	changed=manifest.duplicate(true); changed.cameras[0].look_at=changed.cameras[0].position.duplicate(); cases.append({"name":"camera target equals position","data":changed})
	for fixture in cases:
		var rejected: Array=viewer.validate_script(fixture.data)
		_record("runtime rejects "+fixture.name,not rejected.is_empty(),{"errors":rejected})

func _viewer_checks() -> void:
	for path in ["res://scripts/combat_film.gd","res://scripts/cinematic_actor.gd","res://scripts/duel_effects.gd","res://scripts/film_lighting.gd","res://scripts/courtyard.gd","res://scenes/combat_film.tscn"]:
		if FileAccess.file_exists(path): sources[path]=FileAccess.get_sha256(path)
	root.size=Vector2i(1280,720)
	root.content_scale_size=Vector2i(1280,720)
	change_scene_to_file("res://scenes/courtyard.tscn")
	if not await _wait_scene("res://scenes/courtyard.tscn"):
		_record("title loads for film flow",false,{})
		return
	var title:=current_scene
	var title_ref: WeakRef=weakref(title)
	var watch:=title.find_child("WatchConfluenceDuel",true,false) as Button
	if not is_instance_valid(watch):
		_record("title WatchConfluenceDuel button exists",false,{})
		return
	watch.pressed.emit()
	if not await _wait_scene("res://scenes/combat_film.tscn"):
		_record("watch button enters actual film scene",false,{})
		return
	viewer=current_scene
	viewer.set_playing(false)
	_record("watch button enters ready film and frees title",viewer.ready_to_play and viewer.errors.is_empty() and not is_instance_valid(title_ref.get_ref()),{"errors":viewer.errors,"scene":viewer.scene_file_path})
	if not viewer.ready_to_play: return
	_runtime_validation()
	viewer.sample_time(0,true)
	for id in viewer.actors:
		var actor: Node3D=viewer.actors[id]
		soles[id]=_sole_cohort(actor,actor.skeleton)
	var times:=[]
	for i in range(289): times.append(i/12.0)
	for section in [manifest.actions,manifest.cues,manifest.visual_receipts]:
		for event in section:
			for delta in [-.000001,0,.000001]: times.append(clampf(event.t_seconds+delta,0,24))
	times.append(8.55)
	times.sort()
	var invalid_bones:=0
	var bone_samples:=0
	var out_of_bounds:=[]
	var timing_errors:=[]
	var silent:=true
	var contact_metrics:={}
	for contact in manifest.contact_windows:
		if contact.mode=="planted": contact_metrics[contact.id]={"actor":contact.actor_id,"samples":0,"minimum_sole_y":INF,"maximum_foot_minimum_y":-INF,"maximum_horizontal_drift":0.0,"anchors":{}}
	var at_855:={}
	for time: float in times:
		viewer.sample_time(time,true)
		silent=silent and not viewer.audio_player.playing and not viewer.playing
		var effect_ids: Array=viewer.effects.diagnostics().active_ids.duplicate()
		effect_ids.sort()
		if effect_ids!=_expected_active_cues(time) or viewer.visual_health!=_expected_health(time): timing_errors.append(time)
		for id in viewer.actors:
			var actor: Node3D=viewer.actors[id]
			if not actor.global_position.is_finite() or abs(actor.global_position.x)>67.35 or abs(actor.global_position.z)>81.35: out_of_bounds.append({"time":time,"actor":id})
			var bones:=_capture_bones(actor.skeleton)
			for bone in bones:
				bone_samples+=1
				if not _finite_transform(bone): invalid_bones+=1
			var positions:=_sole_positions(soles[id],actor.skeleton,bones)
			if is_equal_approx(time,8.55): at_855[id]={"left_sole_y":_minimum_y(positions.L),"right_sole_y":_minimum_y(positions.R),"actor_origin_y":actor.global_position.y}
			for contact in manifest.contact_windows:
				if contact.mode!="planted" or contact.actor_id!=id or time<contact.t_seconds or time>contact.end_seconds: continue
				var metrics: Dictionary=contact_metrics[contact.id]
				metrics.samples+=1
				for side in ["L","R"]:
					var y:=_minimum_y(positions[side])
					metrics.minimum_sole_y=minf(metrics.minimum_sole_y,y)
					metrics.maximum_foot_minimum_y=maxf(metrics.maximum_foot_minimum_y,y)
					var center:=_centroid(positions[side])
					if not metrics.anchors.has(side): metrics.anchors[side]=center
					var delta: Vector3=center-metrics.anchors[side]
					metrics.maximum_horizontal_drift=maxf(metrics.maximum_horizontal_drift,Vector2(delta.x,delta.z).length())
	_record("integrated timeline bones finite and actors in bounds",invalid_bones==0 and out_of_bounds.is_empty(),{"sample_times":times.size(),"bone_samples":bone_samples,"invalid_bones":invalid_bones,"out_of_bounds":out_of_bounds})
	_record("exact cue and health chronology including event boundaries",timing_errors.is_empty(),{"mismatched_times":timing_errors,"receipt_times":[4.75,8.9,15.85]})
	_record("absolute capture sampling remains silent and paused",silent,{})
	var contact_ok:=true
	for id in contact_metrics:
		var metrics: Dictionary=contact_metrics[id]
		contact_ok=contact_ok and metrics.samples>0 and metrics.minimum_sole_y>=-.02 and metrics.maximum_foot_minimum_y<=.03 and metrics.maximum_horizontal_drift<=.025
		metrics.erase("anchors")
	_record("actual viewer stationary contact windows",contact_ok,{"windows":contact_metrics,"actual_world_geometry_at_8_55_seconds":at_855,"ground_contract_y":0,"scope":"CPU-skinned loaded shoe/toe cohort in actual director world transforms. This checks geometric clearance and horizontal drift, not the visual appearance of shadow contact."})
	var key_times:=[0.0,2.9,4.749999,4.75,7.6,8.55,8.9,15.849999,15.85,24.0]
	var signatures:={}
	for time: float in key_times:
		viewer.sample_time(time,true)
		signatures[time]=_hash_variant(_actual_snapshot())
	var inventory_before:={"nodes":[],"resources":{},"audio_players":0}
	_inventory(viewer,inventory_before)
	var replay_errors:=[]
	for round_index in range(5):
		for i in range(key_times.size()-1,-1,-1):
			var time: float=key_times[i]
			viewer.sample_time(time,true)
			if _hash_variant(_actual_snapshot())!=signatures[time]: replay_errors.append({"round":round_index,"time":time})
	var inventory_after:={"nodes":[],"resources":{},"audio_players":0}
	_inventory(viewer,inventory_after)
	_record("rewind replay reproduces actual bones camera effects and health",replay_errors.is_empty(),{"repeated_seeks":50,"errors":replay_errors})
	_record("seeking does not allocate scene nodes or mesh materials",inventory_before==inventory_after and inventory_after.audio_players==1,{"nodes":inventory_after.nodes.size(),"unique_mesh_material_resources":inventory_after.resources.size(),"audio_players":inventory_after.audio_players})
	viewer.set_accessibility(true,true)
	viewer.sample_time(8.2,true)
	var static_camera: Transform3D=viewer.camera.global_transform
	var active_before: Array=viewer.effects.diagnostics().active_ids.duplicate()
	viewer.sample_time(13.9,true)
	_record("reduced motion fixes camera while preserving critical effects",viewer.camera.global_transform.is_equal_approx(static_camera) and active_before.has("cue-ravana-wave"),{})
	viewer.set_accessibility(true,false)
	await _viewer_ui_flow()

func _viewer_ui_flow() -> void:
	viewer.set_playing(false)
	viewer.seek(3)
	for dimensions in [Vector2i(1280,720),Vector2i(960,600)]:
		root.size=dimensions
		root.content_scale_size=dimensions
		await _frames(4)
		var outside:=[]
		var rects:={}
		var controls: Array[Control]=[]
		for name_ in ["FilmPlayPause","FilmReplay","FilmReturn","FilmTimeline","FilmReducedEffects","FilmReducedMotion","FilmCaptions","CaptionPanel"]:
			var item:=viewer.find_child(name_,true,false) as Control
			if not is_instance_valid(item): outside.append(name_+" missing"); continue
			var rect:=item.get_global_rect()
			rects[name_]=[rect.position.x,rect.position.y,rect.size.x,rect.size.y]
			if not root.get_visible_rect().encloses(rect): outside.append(name_)
			controls.append(item)
		var overlaps:=[]
		for i in controls.size():
			for j in range(i+1,controls.size()):
				if controls[i].get_global_rect().intersects(controls[j].get_global_rect()): overlaps.append([controls[i].name,controls[j].name])
		_record("film viewer controls fit "+str(dimensions),outside.is_empty() and overlaps.is_empty(),{"outside":outside,"overlaps":overlaps,"rectangles":rects})
	viewer.seek(0)
	viewer.play_button.pressed.emit()
	await create_timer(.12).timeout
	var advanced: float=viewer.current_time
	viewer.play_button.pressed.emit()
	var paused_time: float=viewer.current_time
	await create_timer(.08).timeout
	_record("actual play and pause buttons advance then freeze",advanced>0 and not viewer.playing and is_equal_approx(viewer.current_time,paused_time) and viewer.audio_player.stream_paused,{"advanced_seconds":advanced,"paused_seconds":paused_time})
	viewer.timeline_slider.value=8.55
	await _frames(2)
	_record("actual scrub slider seeks paused film without audio",abs(viewer.current_time-8.55)<.001 and not viewer.playing and not viewer.audio_player.playing,{"time":viewer.current_time})
	var replay:=viewer.find_child("FilmReplay",true,false) as Button
	replay.pressed.emit()
	await create_timer(.05).timeout
	_record("actual replay button restarts single timeline",viewer.playing and viewer.current_time>=0 and viewer.current_time<.5,{"time":viewer.current_time})
	viewer.set_playing(false)
	viewer.sample_time(24,true)
	_record("film endpoint holds both survivors and final receipt",not viewer.playing and not viewer.audio_player.playing and float(viewer.visual_health.get("rama",-1))==100.0 and float(viewer.visual_health.get("ravana",-1))==55.0,{"health":viewer.visual_health,"playing":viewer.playing,"audio_playing":viewer.audio_player.playing})
	viewer.set_playing(false)
	var previous: WeakRef=weakref(viewer)
	var back:=viewer.find_child("FilmReturn",true,false) as Button
	back.pressed.emit()
	var returned:=await _wait_scene("res://scenes/courtyard.tscn")
	_record("actual return button restores title and frees film",returned and not is_instance_valid(previous.get_ref()) and current_scene.main_panel.visible and not current_scene.started,{})
	await create_timer(.1).timeout
	# Exercise the real fatal path with a missing resource. One intentional
	# YUGA_COMBAT_FILM error diagnostic is expected for this negative fixture.
	var old:=current_scene
	current_scene=null
	old.queue_free()
	await _frames(2)
	var invalid: Node3D=load("res://scripts/combat_film.gd").new()
	invalid.manifest_override=manifest.duplicate(true)
	invalid.manifest_override.actors[0].model_path="res://assets/cinematics/does-not-exist.glb"
	root.add_child(invalid)
	current_scene=invalid
	await _frames(2)
	_record("invalid resource viewer fails visibly without placeholders",not invalid.ready_to_play and not invalid.errors.is_empty() and invalid.actors.is_empty() and invalid.play_button.disabled and invalid.caption_panel.visible and invalid.caption_label.text.begins_with("Film cannot start"),{"errors":invalid.errors,"intentional_error_diagnostic":true})
	var invalid_back:=invalid.find_child("FilmReturn",true,false) as Button
	invalid_back.pressed.emit()
	returned=await _wait_scene("res://scenes/courtyard.tscn")
	_record("fatal viewer return remains usable",returned and current_scene.main_panel.visible,{})
	if is_instance_valid(current_scene):
		current_scene.queue_free()
		await _frames(3)

func _record(label: String,passed: bool,details: Dictionary) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func _finish() -> void:
	var passed:=true
	for check in checks: passed=passed and check.passed
	var report:={"passed":passed,"engine":Engine.get_version_info().string,"actors_only":actors_only,"sources":sources,"checks":checks,"scope":"Actual imported rigs and animation libraries evaluated numerically. CPU-skinned sole samples are bounded numerical evidence, not rendered art quality or gameplay physics. Viewer integration recorded separately when actors_only=false."}
	if not output.is_empty():
		var file:=FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed=false
	print("YUGA_COMBAT_FILM_CASES ",JSON.stringify(report))
	quit(0 if passed else 1)
