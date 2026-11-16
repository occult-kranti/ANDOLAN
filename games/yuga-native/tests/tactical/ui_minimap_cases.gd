extends SceneTree
const UI=preload("res://scripts/tactical_ui.gd")
var checks:Array[Dictionary]=[]
var report_path:=""

func _initialize()->void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):report_path=argument.trim_prefix("--report=")
	call_deferred("run")

func check(name_:String,passed:bool)->void:
	checks.append({"name":name_,"passed":passed});print("PASS " if passed else "FAIL ",name_)

func run()->void:
	var map:=UI.TacticalMapView.new();map.size=Vector2(160,180);root.add_child(map)
	var shapes:=map.ground_shapes()
	check("Actual minimap includes both physical flank partitions",map.geometry.get("partitions",[]).size()==2 and map.geometry.partitions.all(func(item):return shapes.has(item)))
	check("Actual minimap includes all36 data-driven ground details",map.geometry.get("static_details",[]).size()==36 and map.geometry.static_details.all(func(item):return shapes.has(item)))
	check("Footprint inventory matches ground classes exactly",shapes.size()==map.geometry.buildings.size()+map.geometry.covers.size()+2+36)
	map.geometry.overhead_galleries=[{"id":"must-not-block-ground"}]
	check("Overhead galleries never draw as planar obstructions",not map.ground_shapes().any(func(item):return item.get("id")=="must-not-block-ground"))
	var local:={"id":0,"team":"sun","alive":true};var state:={"local_id":0,"actors":[local,{"id":1,"team":"sun","alive":false},{"id":5,"team":"moon","alive":true}],"map_bounds":Rect2(-50,-65,100,130),"actor_positions":{0:Vector3.ZERO,1:Vector3.ONE,5:Vector3.ONE}}
	map.refresh(state,local)
	check("Enemy and eliminated teammate positions remain hidden",map.visible_actor_ids==[0])
	check("Actual field bounds map to inset corners with consistent north",map.point(Vector3(-50,0,65)).is_equal_approx(Vector2(10,10)) and map.point(Vector3(50,0,-65)).is_equal_approx(Vector2(150,170)))
	root.remove_child(map);map.free()
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"ui_sha256":FileAccess.get_sha256("res://scripts/tactical_ui.gd"),"map_sha256":FileAccess.get_sha256("res://assets/tactical/map.json"),"scope":"Actual map data/planar minimap inventory and hidden-actor filtering. No render or ordinary input claim."}
	if not report_path.is_empty():var file:=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(result,"\t"))
	quit(0 if result.passed else 1)
