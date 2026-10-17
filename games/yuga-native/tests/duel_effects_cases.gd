extends SceneTree
const Effects = preload("res://scripts/duel_effects.gd")
var checks: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("_run")

func _record(id: String, passed: bool) -> void:
	checks.append({"id":id,"passed":passed})
	if not passed: push_error(id)

func _run() -> void:
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/cinematics/confluence-duel.json"))
	var effects := Effects.new()
	root.add_child(effects)
	_record("canonical_manifest_configures",effects.configure(manifest))
	var baseline: Dictionary = effects.diagnostics()
	_record("canonical_57_meshes_under_128",baseline.mesh_count==57 and baseline.mesh_count<=baseline.max_meshes)
	_record("all_ten_cues_preserved",baseline.cue_count==10)
	var ids := _node_ids(effects)
	var expected := {}
	var times := [0.0,2.95,3.5,4.4,4.76,6.8,7.5,8.5,9.0,14.2,15.5,15.9,24.0]
	for time in times:
		effects.sample(time)
		expected[time]=JSON.stringify(effects.diagnostics().state)
	var reversed := times.duplicate()
	reversed.reverse()
	var exact := true
	for time in reversed:
		effects.sample(time)
		exact=exact and JSON.stringify(effects.diagnostics().state)==expected[time]
	_record("reverse_seek_exact_state",exact)
	var finite := true
	for i in range(241):
		effects.sample(float((i*137)%241)/10.0)
		finite=finite and _finite(effects.diagnostics().state)
	_record("241_nonmonotonic_samples_finite",finite)
	_record("seek_never_adds_or_replaces_nodes",ids==_node_ids(effects))
	effects.sample(4.75)
	var boundary: Array=effects.diagnostics().active_ids
	_record("release_end_hands_to_block_impact",not boundary.has("cue-rama-first-arrow") and boundary.has("cue-opening-block"))
	effects.sample(24.0)
	_record("all_effects_decayed_at_end",effects.diagnostics().active_ids.is_empty())
	effects.sample(NAN)
	_record("nonfinite_seek_resets_to_zero",effects.diagnostics().time==0.0 and effects.diagnostics().active_ids.is_empty())
	effects.sample(-40.0)
	_record("negative_seek_clamped",effects.diagnostics().time==0.0)
	effects.sample(1e300)
	_record("large_finite_seek_clamped",effects.diagnostics().time==24.0)
	effects.set_accessibility(false,false)
	effects.sample(6.8)
	var full_state: Dictionary=effects.diagnostics()
	effects.set_accessibility(true,true)
	effects.sample(6.8)
	var reduced_state: Dictionary=effects.diagnostics()
	_record("reduced_effects_preserve_danger_cue",reduced_state.active_ids==full_state.active_ids and reduced_state.active_ids.has("cue-ravana-wave-warning"))
	_record("reduced_flash_lowers_visible_opacity",_opacity_sum(reduced_state.state)<_opacity_sum(full_state.state))
	effects.sample(4.4)
	var reduced_projectile: Dictionary=effects.diagnostics()
	_record("reduced_motion_keeps_projectile",reduced_projectile.active_ids.has("cue-rama-first-arrow"))
	_record("reconfigure_does_not_accumulate",effects.configure(manifest) and _node_ids(effects).size()==ids.size())
	var release_anchor := Vector3(-2.6,1.62,-5.55)
	var socket_calls: Array=[]
	effects.configure(manifest,func(actor: String,socket: String,time: float) -> Vector3:
		socket_calls.append([actor,socket,time])
		return release_anchor)
	effects.sample(4.4)
	var expected_head := release_anchor.lerp(Vector3(3,1.15,6),(4.4-4.15)/0.6)
	_record("cached_bow_overrides_authored_solar_start",_head_position(effects.diagnostics().state,"cue-rama-first-arrow").distance_to(expected_head)<0.00001)
	var correct_time := not socket_calls.is_empty()
	for call in socket_calls:
		correct_time=correct_time and call==["rama","bow",4.15]
	_record("socket_queries_release_time_not_present_time",correct_time)
	effects.configure(manifest,func(_actor: String,_socket: String,_time: float) -> Vector3: return Vector3(INF,0,0))
	effects.sample(4.4)
	var fallback_head := Vector3(-3,1.35,-6).lerp(Vector3(3,1.15,6),(4.4-4.15)/0.6)
	_record("invalid_cached_socket_uses_authored_fallback",_head_position(effects.diagnostics().state,"cue-rama-first-arrow").distance_to(fallback_head)<0.00001)
	for invalid in _invalid_cases(manifest):
		var accepted := effects.configure(invalid.manifest)
		effects.sample(4.4)
		var result: Dictionary=effects.diagnostics()
		_record(invalid.id,not accepted and not result.errors.is_empty() and result.mesh_count==0 and effects.get_child_count()==0)
	_record("valid_configuration_recovers_after_rejection",effects.configure(manifest))
	var passed:=true
	for check in checks: passed=passed and check.passed
	var report:={"passed":passed,"engine":Engine.get_version_info().string,"checks":checks,
		"effect_sha256":FileAccess.get_sha256("res://scripts/duel_effects.gd"),
		"shader_sha256":FileAccess.get_sha256("res://scripts/duel_energy.gdshader"),
		"manifest_sha256":FileAccess.get_sha256("res://assets/cinematics/confluence-duel.json"),
		"test_sha256":FileAccess.get_sha256("res://tests/duel_effects_cases.gd"),
		"scope":"Headless deterministic effect state, resource bounds and input rejection. Not real-render shader compilation, contact accuracy or multiplayer gameplay."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file:=FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(report,"\t")+"\n")
			else: passed=false
	print("YUGA_DUEL_EFFECTS_CASES ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	effects.free()
	quit(0 if passed else 1)

func _invalid_cases(manifest: Dictionary) -> Array[Dictionary]:
	var result: Array[Dictionary]=[]
	for kind in ["nan_start","negative_duration","late_end","invalid_type","non_string_type","duplicate_id","bad_position","missing_endpoint","overflow_position","bad_radius","bad_film_duration","cue_cap","mesh_cap"]:
		var bad:=manifest.duplicate(true)
		match kind:
			"nan_start": bad.cues[0].t_seconds=NAN
			"negative_duration": bad.cues[0].duration_seconds=-1.0
			"late_end": bad.cues[0].duration_seconds=25.0
			"invalid_type": bad.cues[0].type="unbounded_particles"
			"non_string_type": bad.cues[0].type={"bad":"value"}
			"duplicate_id": bad.cues[1].id=bad.cues[0].id
			"bad_position": bad.cues[0].position=[0,1]
			"missing_endpoint": bad.cues[2].erase("to_position")
			"overflow_position": bad.cues[0].position=[1e300,1,0]
			"bad_radius": bad.cues[4].radius=-2
			"bad_film_duration": bad.duration_seconds={"not":"numeric"}
			"cue_cap":
				bad.cues=[]
				for i in range(33): bad.cues.append({"id":"cue%d"%i,"type":"telegraph","t_seconds":0.0,"duration_seconds":1.0})
			"mesh_cap":
				bad.cues=[]
				for i in range(12): bad.cues.append({"id":"cue%d"%i,"type":"impact","t_seconds":0.0,"duration_seconds":1.0})
		result.append({"id":"reject_"+kind,"manifest":bad})
	return result

func _node_ids(node: Node) -> Array:
	var result: Array=[node.get_instance_id()]
	for child in node.get_children(): result.append_array(_node_ids(child))
	return result

func _finite(value: Variant) -> bool:
	if value is float: return is_finite(value)
	if value is Array:
		for item in value:
			if not _finite(item): return false
	if value is Dictionary:
		for item in value.values():
			if not _finite(item): return false
	return true

func _opacity_sum(state: Array) -> float:
	var total:=0.0
	for cue in state:
		for part in cue.parts:
			if part.visible: total+=float(part.opacity)
	return total

func _head_position(state: Array,id: String) -> Vector3:
	for cue in state:
		if cue.id==id:
			var transform_: Array=cue.parts[1].transform
			return Vector3(transform_[0],transform_[1],transform_[2])
	return Vector3(INF,INF,INF)
