extends SceneTree
const Army=preload("res://scripts/lane_army.gd")
const Session=preload("res://scripts/ultimate_session.gd")
var army: Node3D
var session: Node3D
var events: Array=[]
func _initialize() -> void:call_deferred("run")
func on_event(event: Dictionary) -> void:events.append(event.duplicate(true))
func on_defeat(_unit: Node3D,_player: bool) -> void:army.reset()
func run() -> void:
	army=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	army.configure(JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json")),null)
	session=Session.new();root.add_child(session);session.configure(army);session.invocation_event.connect(on_event)
	var enemy=army.units.filter(func(u):return u.team=="moon")[0]
	for unit in army.units.duplicate():
		if unit!=enemy:army.units.erase(unit);unit.free()
	enemy.position=Vector3(-40,0,-8);enemy.previous_position=enemy.position;enemy.attack_time=100.0;enemy.attack_cooldown=100.0
	army._decision_clock=100.0;army._rebuild_buckets();enemy.defeated.connect(on_defeat)
	session.select_invocation("ravana")
	var accepted: Dictionary=session.request_cast(Vector3(-40,0,-10),Vector3(0,0,1),Vector3(-40,0,-10))
	for _index in range(20):army.step_simulation(.05)
	var rows: Array=[]
	for event in events:rows.append({"kind":event.kind,"epoch":event.epoch,"cast_id":event.cast_id,"receipts":event.receipts.size()})
	print("REENTRANT_PROBE ",JSON.stringify({"accepted":accepted,"events":rows,"session":session.report(),"alive":army.report().alive}))
	session.free();army.free();await process_frame;quit()
