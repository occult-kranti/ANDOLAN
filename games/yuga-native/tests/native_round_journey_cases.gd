extends SceneTree
## Authority-level reachability test with scripted hero origins, not human play.
## Uses normal paired waves and real kit damage; never edits unit/core health,
## route progress, winner, rewards, cooldowns or simulation tuning.
const Army = preload("res://scripts/lane_army.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Unit = preload("res://scripts/lane_minion.gd")
const STEP := .05
const MAX_SIMULATION_SECONDS := 1800.0
const MAX_WALL_MS := 20000
const FILES := ["res://scripts/lane_army.gd", "res://scripts/lane_minion.gd", "res://scripts/lane_unit_art.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/ultimate_rules.gd", "res://assets/design/rama-ability-kit.json", "res://assets/world/confluence-map.json"]
var army
var kit
var output := ""
var checks: Array[Dictionary] = []
var snapshots: Array[Dictionary] = []
var casts: Array[Dictionary] = []
var event_counts := {}
var damage_receipts := 0
var damage_total := 0.0
var guardian_receipts := 0
var confirmed_last_hits := {}
var expected_gold := 0
var outcomes: Array[Dictionary] = []
var hero_origin := Vector3.ZERO

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ", label)

func point(value: Vector3) -> Array:
	return [value.x,value.y,value.z]

func event(value: Dictionary) -> void:
	var kind := String(value.kind)
	event_counts[kind] = int(event_counts.get(kind,0))+1
	for receipt: Dictionary in value.receipts:
		if receipt.kind == "guardian": guardian_receipts += 1
		if receipt.kind != "damage": continue
		damage_receipts += 1
		damage_total += float(receipt.damage_applied)
		if float(receipt.health_after) > 0 or confirmed_last_hits.has(receipt.unit_id): continue
		for unit in army.units:
			if unit.unit_id == int(receipt.unit_id) and unit.team == "moon" and not unit.practice_summon:
				confirmed_last_hits[receipt.unit_id] = {"time_s":army.elapsed,"role":unit.role,"lane":unit.lane_id}
				expected_gold += int(Unit.STATS[unit.role].gold)
				break

func candidate(team: String):
	var selected = null
	for unit in army.units:
		if not unit.alive or unit.team != team or unit.lane_id != 1: continue
		# The closest front of the normal middle lane is selected, never moved.
		if selected == null or unit.progress > selected.progress: selected = unit
	return selected

func bot_action() -> void:
	var state: Dictionary = kit.report()
	if state.action_locked: return
	var enemy = candidate("moon")
	var ally = candidate("sun")
	var id := ""
	var target := Vector3.ZERO
	var forward := Vector3(0,0,1)
	if enemy != null and float(state.cooldowns.dawn_volley) <= .000001:
		id = "dawn_volley"
		# Three fixed spread lanes are aimed from the street behind the front.
		hero_origin = Vector3(enemy.position.x,0,enemy.position.z-10)
		target = enemy.position
	elif enemy != null and float(state.cooldowns.piercing_dawn) <= .000001:
		id = "piercing_dawn"
		hero_origin = Vector3(enemy.position.x,0,enemy.position.z-5)
		target = enemy.position
	elif ally != null and float(state.cooldowns.guardian_circle) <= .000001:
		id = "guardian_circle"
		hero_origin = Vector3(ally.position.x,0,ally.position.z-4)
		target = ally.position
	if id.is_empty(): return
	var accepted: Dictionary = kit.request_ability(id,hero_origin,forward,target)
	casts.append({"simulation_s":army.elapsed,"ability_id":id,"origin":point(hero_origin),"target":point(target),"accepted":accepted.get("accepted",false),"reason":accepted.get("reason",""),"cast_id":accepted.get("cast_id",0),"position_policy":"Scripted relocation to a real unit in the middle lane; no navigation/input claim."})

func run() -> void:
	if not output.is_absolute_path() or FileAccess.file_exists(output):
		push_error("Use a fresh absolute --report path"); quit(1); return
	DirAccess.make_dir_recursive_absolute(output.get_base_dir())
	var source_before := {}
	for path in FILES: source_before[path] = FileAccess.get_sha256(path)
	source_before[get_script().resource_path] = FileAccess.get_sha256(get_script().resource_path)
	army = Army.new()
	army.visual_enabled = false
	root.add_child(army)
	army.set_physics_process(false)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	check("Normal unmodified map and paired army configure",army.configure(manifest,null),{"initial":army.report()})
	kit = Kit.new()
	root.add_child(kit)
	check("Actual Rama kit connects to the army clock",kit.configure(army))
	kit.ability_event.connect(event)
	army.outcome.connect(func(winner: String): outcomes.append({"winner":winner,"time_s":army.elapsed,"cores":army.cores.duplicate(),"arrivals":army.core_arrivals.duplicate()}))
	var started := Time.get_ticks_msec()
	var ticks := 0
	var core_mutations_follow_arrivals := true
	var bounded := true
	var stopped := "simulation_limit"
	while ticks < int(MAX_SIMULATION_SECONDS/STEP) and army.winner.is_empty():
		if ticks%10 == 0: bot_action()
		var before_cores: Dictionary = army.cores.duplicate()
		var before_arrivals: int = int(army.core_arrivals[0])+int(army.core_arrivals[1])+int(army.core_arrivals[2])
		army.step_simulation(STEP)
		ticks += 1
		if army.cores != before_cores:
			var after_arrivals: int = int(army.core_arrivals[0])+int(army.core_arrivals[1])+int(army.core_arrivals[2])
			core_mutations_follow_arrivals = core_mutations_follow_arrivals and after_arrivals > before_arrivals and army.cores.sun <= before_cores.sun and army.cores.moon <= before_cores.moon
		if ticks%600 == 0:
			var sample: Dictionary = army.report()
			snapshots.append(sample)
			bounded = bounded and sample.finite and sample.alive<=72 and sample.pending_cleanup<=24 and sample.unit_nodes<=96
		if ticks%100 == 0:
			if Time.get_ticks_msec()-started >= MAX_WALL_MS:
				stopped = "wall_budget"; break
			await process_frame
	if not army.winner.is_empty(): stopped = "natural_core_outcome"
	var final: Dictionary = army.report()
	check("Scripted valid kit actions released real troop damage",kit.accepted_casts>0 and kit.release_count>0 and damage_receipts>0,{"accepted":kit.accepted_casts,"released":kit.release_count,"damage_receipts":damage_receipts,"damage_total":damage_total,"guardian_receipts":guardian_receipts})
	check("Confirmed kit last hits account for all earned gold",army.kills==confirmed_last_hits.size() and army.gold==expected_gold,{"army_kills":army.kills,"confirmed_last_hits":confirmed_last_hits.size(),"army_gold":army.gold,"expected_gold":expected_gold})
	check("Only real lane arrivals reduced core health",core_mutations_follow_arrivals,{"core_arrivals":army.core_arrivals,"cores":army.cores})
	check("Normal populations remain finite and bounded",bounded and final.finite and final.alive<=72 and final.unit_nodes<=96,final)
	check("Complete local core outcome reached within the budget",not army.winner.is_empty() and outcomes.size()==1,{"stop_reason":stopped,"simulated_s":army.elapsed,"wall_ms":Time.get_ticks_msec()-started,"outcomes":outcomes})
	if not army.winner.is_empty():
		var terminal_clock: float = army.elapsed
		var terminal_cores: Dictionary = army.cores.duplicate()
		var terminal_gold: int = army.gold
		var rejected: Dictionary = kit.request_ability("dawn_volley",hero_origin,Vector3(0,0,1),hero_origin+Vector3(0,0,4))
		for unused in 20: army.step_simulation(STEP)
		check("Terminal army and kit reject continued progression",not rejected.accepted and army.elapsed==terminal_clock and army.cores==terminal_cores and army.gold==terminal_gold and outcomes.size()==1)
	var source_after := {}
	for path in source_before: source_after[path] = FileAccess.get_sha256(path)
	check("All tested sources remained unchanged",source_before==source_after)
	var result := {"passed":checks.all(func(row):return row.passed),"checks":checks,"stop_reason":stopped,"fixed_step_s":STEP,"ticks":ticks,"simulation_limit_s":MAX_SIMULATION_SECONDS,"wall_budget_ms":MAX_WALL_MS,"wall_ms":Time.get_ticks_msec()-started,"source_before":source_before,"source_after":source_after,"engine":Engine.get_version_info().string,"final_army":final,"kit":kit.report(),"casts":casts,"ability_event_counts":event_counts,"confirmed_last_hits":confirmed_last_hits,"checkpoints_30s":snapshots,"scope":"Actual normal army plus configured Rama kit. Hero origins are scripted relocations, not player movement, physics eligibility, ammo/reload, incoming hero damage, OS input, rendering or human game feel. Only Piercing Dawn, Dawn Volley and Guardian Circle are requested. No unit/core health, route progress, winner, cooldown or reward injection."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	kit.free()
	army.free()
	await process_frame
	quit(0 if result.passed else 1)
