extends SceneTree
## Real kit/receiver attempt history with replay and false-feedback counterexamples.
const Record = preload("res://scripts/rama_practice_record.gd")
const Practice = preload("res://scripts/rama_practice_army.gd")
const Target = preload("res://scripts/target.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
var logbook := Record.new()
var checks: Array = []
var events: Array[Dictionary] = []
var targets: Array = []
var army: Node3D
var kit: Node3D
var vitals: Node
var output := ""
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)
func advance(seconds: float) -> void:
	for unused in ceili(seconds/.05): army.step_simulation(.05)
func cast(id: String, direction := Vector3(0,0,1)) -> Dictionary:
	return kit.request_ability(id,Vector3.ZERO,direction,Vector3.ZERO)
func run() -> void:
	var before_sources := {}
	for path in ["res://scripts/rama_practice_record.gd","res://scripts/rama_practice_army.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_vitals.gd",get_script().resource_path]: before_sources[path]=FileAccess.get_sha256(path)
	for distance in [5,8,11]:
		var target := Target.new()
		root.add_child(target)
		target.position=Vector3(0,0,distance)
		targets.append(target)
	army=Practice.new();root.add_child(army);army.set_physics_process(false)
	check("Real courtyard receiver configures",army.configure(targets))
	kit=Kit.new();root.add_child(kit)
	check("Actual kit configures",kit.configure(army))
	vitals=Vitals.new();root.add_child(vitals)
	check("Actual hero receiver configures",vitals.configure(army))
	kit.set_hero_receiver(vitals,func():return Vector3.ZERO)
	kit.set_movement_receiver(func(_start,finish,_seconds):return {"accepted":true,"destination":finish})
	logbook.reset(kit.generation)
	kit.ability_event.connect(func(event: Dictionary):events.append(event.duplicate(true));logbook.observe(event))
	check("Empty attempt has five named rows and zero invented output",logbook.report().configured and logbook.report().by_ability.size()==5 and logbook.report().casts_started==0 and logbook.report().damage_dealt==0)
	check("Miss cast is actually admitted",cast("kodanda",Vector3.RIGHT).accepted)
	advance(1.1)
	check("Miss records accepted cast without a hit",logbook.report().casts_started==1 and logbook.report().hits==0 and logbook.report().damage_dealt==0)
	check("Primary cast accepted",cast("kodanda").accepted)
	advance(.6)
	check("Real primary effect records only28 effective damage",logbook.report().hits==1 and logbook.report().damage_dealt==28 and logbook.report().by_ability[0].damage_dealt==28)
	var replay: Dictionary=events.filter(func(e):return e.kind=="impact" and e.get("reason")=="unit")[0]
	var prior := logbook.report()
	check("Replayed event cannot inflate the attempt",not logbook.observe(replay) and logbook.report()==prior)
	check("Piercing admitted",cast("piercing_dawn").accepted)
	advance(1.4)
	var health_removed := 0.0
	for unit in army.units: health_removed+=float(unit.max_health-unit.health)
	check("Damage equals actual receiver health removed including capped killing hit",is_equal_approx(logbook.report().damage_dealt,health_removed) and logbook.report().defeats==1,logbook.report())
	check("Step admitted",cast("measured_step",Vector3.RIGHT).accepted)
	advance(.7)
	check("Only actual accepted displacement is recorded",is_equal_approx(logbook.report().step_distance_m,4.5))
	vitals.receive_damage(50,"record test",vitals.generation,0)
	check("Guardian admitted",cast("guardian_circle").accepted)
	advance(5.0)
	check("Guardian records actual shield grant and bounded effective healing",logbook.report().shield_granted==55 and is_equal_approx(logbook.report().healing_applied,vitals.health-250) and logbook.report().healing_applied>0,logbook.report())
	check("Volley admitted",cast("dawn_volley").accepted)
	advance(2)
	health_removed=0
	for unit in army.units: health_removed+=float(unit.max_health-unit.health)
	check("All observed projectile effects conserve receiver loss",is_equal_approx(logbook.report().damage_dealt,health_removed))
	prior=logbook.report()
	var authority_before: Dictionary=kit.report()
	for unused in 100: logbook.report()
	check("Opening and reading the record cannot advance combat",kit.report()==authority_before and logbook.report()==prior)
	var copy:=logbook.report();copy.by_ability[0].damage_dealt=99999
	check("Returned rows do not expose mutable internal state",logbook.report()==prior)
	paused=true
	check("Paused clock stays frozen",not army.step_simulation(.05) and logbook.report()==prior)
	paused=false
	army.reset("new attempt")
	check("New attempt retires all previous totals",logbook.report().generation==kit.generation and logbook.report().casts_started==0 and logbook.report().damage_dealt==0 and logbook.report().step_distance_m==0)
	check("Old generation receipts stay retired",not logbook.observe(replay) and logbook.report().hits==0)
	# Exercise later-sequence copies during one live cast, rather than only replaying an old packet.
	check("Counterexample primary admitted",cast("kodanda").accepted)
	advance(.15)
	var begin: Dictionary=events.filter(func(e):return e.generation==kit.generation and e.kind=="begin")[-1].duplicate(true)
	var sequence: int=logbook.last_sequence+1
	var hit:=begin.duplicate(true)
	hit.kind="impact";hit.event_seq=sequence;hit.time_s=kit.elapsed;hit.reason="unit";hit.projectile_index=0
	hit.receipts=[{"kind":"damage","unit_id":1,"health_before":90.0,"health_after":62.0,"shield_before":0.0,"shield_after":0.0,"damage_applied":28.0}]
	check("Coherent supplied receipt is recorded in a live cast",logbook.observe(hit) and logbook.report().damage_dealt==28)
	hit.event_seq+=1
	check("Higher-sequence duplicate contact cannot double count",not logbook.observe(hit) and logbook.report().damage_dealt==28)
	hit.event_seq+=1;hit.receipts[0].unit_id=2;hit.receipts[0].damage_applied=999
	check("Contradictory positive damage is rejected",not logbook.observe(hit) and logbook.report().damage_dealt==28)
	for value in [NAN,INF,-1.0,"9",[],{}]:
		var bad:=begin.duplicate(true);bad.event_seq=logbook.last_sequence+1;bad.time_s=value
		check("Malformed clock is rejected "+str(value),not logbook.observe(bad))
	var after_sources := {}
	for path in before_sources: after_sources[path]=FileAccess.get_sha256(path)
	check("Tested sources remained stable",before_sources==after_sources)
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks,"source_before":before_sources,"source_after":after_sources,"scope":"Actual kit/receivers and independent replay/coherence counterexamples. Movement is an admitted receiver fixture, not ordinary navigation or art acceptance."}
	if not output.is_empty():
		DirAccess.make_dir_recursive_absolute(output.get_base_dir())
		FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	kit.free();vitals.free();army.free()
	for target in targets:target.free()
	quit(0 if report.passed else 1)
