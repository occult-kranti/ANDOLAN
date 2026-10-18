extends SceneTree
## Counterfactual options check: the exact SAME accepted source events feed both
## effect owners. No actor reset/pose equivalence is assumed between trials.
const EFFECTS := preload("res://scripts/rama_ability_effects.gd")
const INPUT := "res://docs/evidence/visual-rounds/round4/role11/warning-lifecycle-r3.json"
const VECTOR_KEYS := ["origin","forward","target","center","position","contact_position","step_direction"]
var output := ""
var checks := []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")

func hydrate(value: Variant, key := "") -> Variant:
	if key in VECTOR_KEYS and value is Array and value.size()==3:return Vector3(value[0],value[1],value[2])
	if value is Dictionary:
		var result := {}
		for name in value:result[name]=hydrate(value[name],String(name))
		return result
	if value is Array:
		var result := []
		for item in value:result.append(hydrate(item))
		return result
	# JSON reads numbers as float; the event contract deliberately requires ints.
	if key in ["schema","generation","cast_id","event_seq","epoch","index","unit_id","projectile_index"]:return int(value)
	return value

func hash_value(value: Variant) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(var_to_bytes(value))
	return context.finish().hex_encode()

func essentials(fx: Node3D) -> Dictionary:
	var result := {"casts":{},"impacts":[]}
	for id in fx._casts:
		var cast: Dictionary=fx._casts[id]
		var arrows := []
		for arrow in cast.arrows:
			arrows.append({"visible":arrow.root.visible,"transform":arrow.root.global_transform,"shaft_arrays":hash_value(arrow.shaft.mesh.surface_get_arrays(0))})
		result.casts[id]={"geometry":cast.geometry,"timing":cast.timing,"age":cast.age,"authority_age":cast.authority_age,"released":cast.released,"warning_visible":cast.warning.visible,"warning_transform":cast.warning.global_transform,"warning_arrays":hash_value(cast.warning.mesh.surface_get_arrays(0)) if cast.warning.mesh.get_surface_count()>0 else "empty","warning_opacity":cast.warning_material.get_shader_parameter("opacity"),"contacts":cast.contacts,"arrows":arrows}
	for impact in fx._impacts:result.impacts.append({"position":impact.root.global_position,"visible":impact.root.visible,"age":impact.age,"hit":impact.hit})
	return result

func run() -> void:
	var source: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(INPUT))
	for trial in source.trials:
		var normal := EFFECTS.new()
		var reduced := EFFECTS.new()
		root.add_child(normal)
		root.add_child(reduced)
		normal.set_process(false)
		reduced.set_process(false)
		normal.set_options({"reduced_motion":false,"reduced_effects":false})
		reduced.set_options({"reduced_motion":true,"reduced_effects":true})
		var mismatches := []
		var rejected := []
		var last_time := 0.0
		var sampled := 0
		for raw in trial.events:
			var event: Dictionary=hydrate(raw)
			var remaining := maxf(0,float(event.time_s)-last_time)
			while remaining>.000001:
				var dt := minf(1.0/60.0,remaining)
				normal.step(dt)
				reduced.step(dt)
				if essentials(normal)!=essentials(reduced):mismatches.append({"stage":"step","time_s":last_time,"event_seq":event.event_seq})
				sampled+=1
				remaining-=dt
			last_time=float(event.time_s)
			var accepted_normal: bool=normal.consume_event(event.duplicate(true))
			var accepted_reduced: bool=reduced.consume_event(event.duplicate(true))
			if not accepted_normal or not accepted_reduced:rejected.append({"kind":event.kind,"sequence":event.event_seq,"normal":accepted_normal,"reduced":accepted_reduced})
			if essentials(normal)!=essentials(reduced):mismatches.append({"stage":"event","time_s":last_time,"event_seq":event.event_seq})
			sampled+=1
		var row := {"ability":trial.ability,"source_mode_reduced":trial.reduced_effects_and_motion,"kind":trial.kind,"passed":mismatches.is_empty() and rejected.is_empty(),"events":trial.events.size(),"paired_observations":sampled,"mismatches":mismatches,"rejected":rejected}
		checks.append(row)
		print("PASS " if row.passed else "FAIL ",trial.ability," ",trial.kind," source_reduced=",trial.reduced_effects_and_motion)
		normal.free()
		reduced.free()
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_event_report_sha256":FileAccess.get_sha256(INPUT),"script_sha256":FileAccess.get_sha256(get_script().resource_path),"effects_sha256":FileAccess.get_sha256("res://scripts/rama_ability_effects.gd"),"scope":"Exact accepted event replay into normal/reduced effect owners. Compares warning geometry/transform/opacity/visibility, cast authority state, projectile shaft geometry/positions/visibility and contact position/hit/age. Decorative wakes, ornament geometry, opacity and impact scale may differ. No actor pose equality, pixel visibility, rendering or gameplay-authority reexecution claim."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if result.passed else 1)
