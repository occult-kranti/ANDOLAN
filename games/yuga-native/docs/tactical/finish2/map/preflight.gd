extends SceneTree
func _initialize() -> void:
 call_deferred("run")
func run() -> void:
 var map = load("res://scripts/tactical_map.gd").new()
 root.add_child(map)
 await physics_frame
 await physics_frame
 var report: Dictionary = map.report()
 var details: Array = JSON.parse_string(FileAccess.get_file_as_string("res://assets/tactical/map.json")).get("static_details",[])
 var checked := 0
 for detail in details:
  var body = map.find_child(detail.id,false,false)
  var size_ := Vector3(detail.size[0],detail.size[1],detail.size[2])
  var base := Vector3(detail.position[0],detail.position[1],detail.position[2])
  if body == null or not body is StaticBody3D or not body.get_child(0).shape is BoxShape3D:
   report.errors.append("missing_static_detail:"+detail.id)
  elif not body.position.is_equal_approx(base+Vector3.UP*size_.y*.5) or not body.get_child(0).shape.size.is_equal_approx(size_):
   report.errors.append("wrong_static_detail:"+detail.id)
  else: checked += 1
 report["static_detail_footprints_checked"] = checked
 report.ready = report.ready and report.errors.is_empty()
 print(JSON.stringify(report))
 var report_path := "res://docs/tactical/finish2/map/preflight-r1.json"
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
 var stream = FileAccess.open(report_path,FileAccess.WRITE)
 stream.store_string(JSON.stringify(report,"\t")+"\n")
 map.queue_free()
 quit(0 if report.ready else 1)
