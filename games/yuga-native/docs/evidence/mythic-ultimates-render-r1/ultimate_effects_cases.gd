extends SceneTree
const FX := preload("res://scripts/ultimate_effects.gd")
var checks: Array = []
var fx: Node3D
var rules: Array = []
var _id := 0

func _initialize() -> void:
	call_deferred("_run")

func check(name_: String, ok: bool, detail: Variant = "") -> void:
	checks.append({"name":name_,"passed":ok,"detail":detail})
	if not ok:push_error(name_+": "+str(detail))

func event(hero: String, kind := "begin", epoch := 1, cast_id := -1, sequence := 0) -> Dictionary:
	var rule: Dictionary = {}
	for r in rules:
		if r.hero_id == hero:rule = r.duplicate(true)
	var geometry: Dictionary = rule.geometry
	geometry.origin = Vector3(2,0,-4)
	geometry.center = Vector3(2,0,-4)
	geometry.forward = Vector3(0,0,1)
	if geometry.anchor == "ground_target":geometry.center = Vector3(2,0,5)
	if geometry.kind == "projectile_volley":
		geometry.projectiles = []
		for i in range(geometry.yaw_offsets_rad.size()):geometry.projectiles.append({"index":i,"origin":geometry.origin,"forward":geometry.forward.rotated(Vector3.UP,geometry.yaw_offsets_rad[i])})
	if geometry.kind == "summon_pair":geometry.placements = [Vector3(.7,0,-4),Vector3(3.3,0,-4)]
	if cast_id < 0:
		_id += 1
		cast_id = _id
	return {"schema":1,"kind":kind,"epoch":epoch,"cast_id":cast_id,"event_seq":sequence,"hero_id":hero,"effect_id":rule.effect_id,"team":"sun","time_s":0.0,"age_s":0.0,"origin":geometry.origin,"target":geometry.center,"forward":geometry.forward,"timing":rule.timing,"geometry":geometry,"receipts":[],"reason":"fixture"}

func _boundary_ok(cast: Dictionary) -> bool:
	var g: Dictionary = cast.geometry
	for local in cast.warning_vertices:
		var p: Vector3 = cast.warning_transform*local
		if absf(p.y-.055) > .001:return false
		match g.kind:
			"disk","zone_disk":
				if Vector2(p.x-g.center.x,p.z-g.center.z).length() > g.radius_m+.001:return false
			"sector":
				var d: Vector3 = p-g.origin
				d.y = 0
				if d.length() > g.range_m+.001:return false
				if d.length() > .001 and d.normalized().dot(g.forward) < g.half_angle_cos-.001:return false
			"projectile_volley":
				var inside := false
				for arrow in g.projectiles:
					var d: Vector3 = p-arrow.origin
					d.y = 0
					var along: float = clampf(d.dot(arrow.forward),0,g.range_m)
					if d.distance_to(arrow.forward*along) <= g.radius_m+.001:inside = true
				if not inside:return false
	return true

func _run() -> void:
	rules = JSON.parse_string(FileAccess.get_file_as_string("res://assets/design/native-ultimate-rules.json")).rules
	fx = FX.new()
	root.add_child(fx)
	fx.set_process(false)
	var motif_signatures := {}
	var max_triangles := 0
	for rule in rules:
		fx.reset()
		var e := event(rule.hero_id)
		var accepted: bool = fx.consume_event(e)
		fx.step(.25)
		var report: Dictionary = fx.report()
		var cast: Dictionary = report.casts[0] if report.active else {}
		check("Accepted original motif: "+rule.hero_id,accepted and report.active==1 and report.finite and cast.instances<=48 and cast.draw_calls_upper_bound<=16 and cast.triangles<=18000,cast.get("triangles"))
		check("Authority warning inside exact geometry: "+rule.hero_id,_boundary_ok(cast))
		max_triangles = maxi(max_triangles,cast.triangles)
		var signature := ""
		for node in fx.get_child(0).get_children():
			if str(node.name).begins_with("OriginalMotif"):signature += str(hash(node.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]))+":"
		motif_signatures[signature] = true
		var before: PackedVector3Array = cast.warning_vertices
		fx.set_options({"reduced_effects":true,"reduced_motion":true})
		check("Low/reduced retains exact warning: "+rule.hero_id,fx.report().casts[0].warning_visible and fx.report().casts[0].warning_vertices==before)
		fx.set_options({"reduced_effects":false,"reduced_motion":false})
	check("All fourteen motifs have distinct geometry",motif_signatures.size()==14,motif_signatures.size())
	for rule in rules:
		fx.reset()
		var begin := event(rule.hero_id)
		fx.consume_event(begin)
		var seq := 0
		var released := false
		var impacted := false
		var finite_all := true
		var elapsed := 0.0
		var total := 0.0
		for seconds in rule.timing.values():total += float(seconds)
		while elapsed < total:
			elapsed += 1.0/60.0
			fx.step(1.0/60.0)
			if not released and elapsed >= rule.timing.windup_s:
				seq += 1
				var e := begin.duplicate(true)
				e.kind = "release"
				e.event_seq = seq
				e.time_s = elapsed
				finite_all = finite_all and fx.consume_event(e)
				released = true
			if not impacted and elapsed >= rule.timing.windup_s+rule.timing.travel_s:
				seq += 1
				var e := begin.duplicate(true)
				e.kind = "impact"
				e.event_seq = seq
				e.time_s = elapsed
				finite_all = finite_all and fx.consume_event(e)
				impacted = true
			finite_all = finite_all and fx.report().finite and fx.report().active == 1
		seq += 1
		var end := begin.duplicate(true)
		end.kind = "end"
		end.event_seq = seq
		end.time_s = elapsed
		check("Complete 60Hz finite choreography and event cleanup: "+rule.hero_id,finite_all and released and impacted and fx.consume_event(end) and fx.get_child_count()==0)

	fx.reset()
	var base := event("rama")
	check("Accepted seed before invalid input",fx.consume_event(base))
	var state: Dictionary = fx.report()
	for delta in [NAN,INF,-1.0,2.0]:fx.step(delta)
	check("Invalid simulation deltas cannot mutate elapsed/age",fx.report().elapsed==state.elapsed and fx.report().casts[0].age==state.casts[0].age)
	var invalid: Array = []
	for mut in ["nan_radius","bad_forward","bool_epoch","bad_receipt","huge_attachments","bad_projectile"]:
		var e := event("rama")
		match mut:
			"nan_radius":e.geometry.radius_m = NAN
			"bad_forward":e.geometry.forward = Vector3.ZERO
			"bool_epoch":e.epoch = true
			"bad_receipt":e.receipts = [{"unit_id":1,"amount":NAN}]
			"huge_attachments":e.geometry.attachments = range(73)
			"bad_projectile":e.geometry.projectiles[0].index = 9
		invalid.append(not fx.consume_event(e))
	check("Malformed/NaN/oversized events rejected atomically",not invalid.has(false) and fx.report().active==1)
	check("Duplicate begin rejected",not fx.consume_event(base))
	var release := base.duplicate(true)
	release.kind = "release"
	release.event_seq = 1
	release.time_s = 1.0
	check("Release starts exactly three visible arrows",fx.consume_event(release) and fx.report().casts[0].live_projectiles==3)
	var contact := release.duplicate(true)
	contact.kind = "impact"
	contact.event_seq = 2
	contact.time_s = 1.1
	contact.projectile_index = 1
	contact.contact_position = Vector3(2,0,0)
	contact.reason = "wall"
	check("Indexed wall contact retires exactly one arrow",fx.consume_event(contact) and fx.report().casts[0].live_projectiles==2)
	check("Duplicate impact rejected",not fx.consume_event(contact))
	var moved := contact.duplicate(true)
	moved.event_seq = 3
	moved.geometry.origin.x += 1
	check("Changed locked geometry rejected",not fx.consume_event(moved))
	fx.set_suspended(true)
	var age: float = fx.report().casts[0].age
	for i in range(30):fx.step(.1)
	check("Suspension freezes all presentation clocks",fx.report().casts[0].age==age)
	fx.set_suspended(false)
	root.get_tree().paused = true
	fx.step(.1)
	check("Scene pause freezes explicit step",fx.report().casts[0].age==age)
	root.get_tree().paused = false
	fx.reset()
	check("Reset immediately frees all children",fx.get_child_count()==0 and fx.report().nodes==0)
	check("Delayed same-epoch begin cannot revive reset cast",not fx.consume_event(base))
	var reset_event := {"schema":1,"kind":"reset","epoch":2,"cast_id":0,"event_seq":0}
	check("New epoch reset accepted",fx.consume_event(reset_event))
	var next_epoch := event("sita","begin",2)
	fx.consume_event(next_epoch)
	check("Replayed reset cannot erase a newer cast in its epoch",not fx.consume_event(reset_event) and fx.report().active==1)
	check("Old epoch events refused",not fx.consume_event(base))
	fx.reset()
	# Remaining fixtures enter a later epoch after the replay checks.
	fx.free()
	fx = FX.new()
	root.add_child(fx)
	fx.set_process(false)

	var ward := event("chitrangada")
	fx.consume_event(ward)
	var tick := ward.duplicate(true)
	tick.kind = "impact"
	tick.event_seq = 1
	tick.time_s = .65
	tick.geometry.attachments = []
	for i in range(72):tick.geometry.attachments.append({"unit_id":i,"position":Vector3(i%9,0,i/9),"kind":"shield","shield":80.0,"remaining_s":4.0})
	check("72 accepted wards merge within per-cast bounds",fx.consume_event(tick) and fx.report().casts[0].attachments.size()==72 and fx.report().casts[0].instances<=48 and fx.report().casts[0].triangles<=18000)
	tick.event_seq = 2
	tick.time_s = .7
	tick.geometry.attachments = []
	check("Omitted authoritative recipients retire all attached marks",fx.consume_event(tick) and fx.report().casts[0].attachments.is_empty() and fx.get_child(0).get_node("AcceptedRecipientMarks").mesh.get_surface_count()==0)
	fx.reset()
	for hero in ["rama","sita","ulupi","ravana"]:fx.consume_event(event(hero))
	check("Four-cast overlap capped before fifth allocation",fx.report().active==4 and not fx.consume_event(event("karna")) and fx.report().active==4)
	var peak_nodes: int = fx.report().nodes
	for cycle in range(100):
		fx.reset()
		for hero in ["subhadra","meghnad","ulupi","karna"]:fx.consume_event(event(hero))
		for i in range(240):fx.step(.05)
		peak_nodes = maxi(peak_nodes,fx.report().nodes)
		if not fx.report().finite:break
	check("Twenty minutes accelerated lifecycle remain finite/bounded",fx.report().finite and fx.report().active==0 and fx.get_child_count()==0 and peak_nodes<=36,{"seconds":1200,"steps":24000,"peak_nodes":peak_nodes,"max_single_triangles":max_triangles})
	fx.free()
	var passed := true
	for c in checks:passed = passed and c.passed
	var output := {"passed":passed,"checks":checks,"effect_source_sha256":FileAccess.get_sha256("res://scripts/ultimate_effects.gd"),"rules_source_sha256":FileAccess.get_sha256("res://assets/design/native-ultimate-rules.json"),"scope":"Headless geometry/event/lifetime cases; no visual or performance acceptance."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path := argument.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(output,"  ")+"\n")
	print("ULTIMATE_EFFECTS_CASES ",checks.filter(func(c):return c.passed).size(),"/",checks.size())
	quit(0 if passed else 1)
