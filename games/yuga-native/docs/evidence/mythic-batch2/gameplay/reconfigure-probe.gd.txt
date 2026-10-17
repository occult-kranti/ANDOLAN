extends SceneTree
const Army=preload("res://scripts/lane_army.gd")
const Session=preload("res://scripts/ultimate_session.gd")
func _initialize() -> void:call_deferred("run")
func make_army() -> Node3D:
	var value=Army.new();value.visual_enabled=false;root.add_child(value);value.set_physics_process(false)
	value.configure(JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json")),null)
	value._decision_clock=100.0
	for unit in value.units:unit.attack_time=100.0;unit.attack_cooldown=100.0
	return value
func run() -> void:
	var first=make_army();var second=make_army();var session=Session.new();root.add_child(session);session.configure(first)
	var ally=first.units.filter(func(u):return u.team=="sun")[0]
	ally.position=Vector3(-40,0,-8);ally.previous_position=ally.position
	session.select_invocation("chitrangada");var cast: Dictionary=session.request_cast(Vector3(-40,0,-10),Vector3(0,0,1),Vector3(-40,0,-10))
	for _index in range(14):first.step_simulation(.05)
	var before: float=ally.shield;var configured: bool=session.configure(second)
	print("RECONFIGURE_PROBE ",JSON.stringify({"cast":cast,"old_shield_before":before,"configure_second":configured,"old_shield_after":ally.shield,"old_step_connections":first.simulation_stepped.get_connections().size(),"new_step_connections":second.simulation_stepped.get_connections().size()}))
	session.free();first.free();second.free();await process_frame;quit()
