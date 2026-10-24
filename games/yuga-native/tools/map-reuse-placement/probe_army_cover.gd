extends "res://tools/map-reuse-placement/capture.gd"
const RuntimeGate=preload("res://tools/map-reuse-placement/runtime_gate.gd")
func run()->void:
	var asset:="";var target:=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--asset="):asset=arg.trim_prefix("--asset=")
		elif arg.begins_with("--output="):target=arg.trim_prefix("--output=")
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene;await physics_frame;await physics_frame
	scene.set_paused(false);scene.set_process(false);scene.set_physics_process(false);hold_callbacks(scene.world)
	var result:Dictionary=RuntimeGate.build(scene.world,asset);await physics_frame;await physics_frame
	var space:PhysicsDirectSpaceState3D=scene.world.get_world_3d().direct_space_state
	var from:=Vector3(-49,0,-70);var to:=Vector3(-49,0,-38)
	var hit:=space.intersect_ray(PhysicsRayQueryParameters3D.create(from+Vector3.UP*1.2,to+Vector3.UP*1.2,1))
	var ai_clear:bool=scene.army.line_clear(from,to)
	var mismatch:bool=not hit.is_empty() and hit.collider==result.body and ai_clear
	var report:={"schema":1,"passed":not mismatch,"native_pier_blocks":not hit.is_empty() and hit.collider==result.body,"army_line_clear":ai_clear,"mismatch_reproduced":mismatch,"from":[-49,0,-70],"to":[-49,0,-38],"eye_height":1.2,"lane_army_sha256":FileAccess.get_sha256("res://scripts/lane_army.gd"),"scope":"Actual native source pier physics versus existing offline army2DLOS. A mismatch is an integration blocker, not art rejection."}
	FileAccess.open(target,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n");scene.queue_free();for unused in 8:await process_frame
	print(JSON.stringify(report));quit(1 if mismatch else 0)
