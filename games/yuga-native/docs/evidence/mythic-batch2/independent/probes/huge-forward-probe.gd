extends SceneTree
const Army=preload("res://scripts/lane_army.gd")
const Session=preload("res://scripts/ultimate_session.gd")
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var army=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	army.configure(JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json")),null)
	var session=Session.new();root.add_child(session);session.configure(army)
	var huge:=Vector3(1e30,0,1e30);var answer: Dictionary=session.request_cast(Vector3(-40,0,-10),huge,Vector3(-40,0,-10))
	var geometry: Dictionary=session._active.get("geometry",{})
	print("HUGE_FORWARD_PROBE ",JSON.stringify({"finite_input":huge.is_finite(),"finite_length":is_finite(huge.length_squared()),"cast":answer,"normalized":str(geometry.get("forward")),"normalized_length":geometry.get("forward",Vector3.ZERO).length()}))
	session.free();army.free();await process_frame;quit()
