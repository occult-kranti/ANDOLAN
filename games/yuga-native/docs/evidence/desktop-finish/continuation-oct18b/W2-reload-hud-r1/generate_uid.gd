extends SceneTree
func _initialize() -> void:
	var path := "res://tests/ui_hud_reload_availability_cases.gd.uid"
	if FileAccess.file_exists(path):
		print("EXISTING_UID ",FileAccess.get_file_as_string(path).strip_edges())
	else:
		var value := ResourceUID.id_to_text(ResourceUID.create_id())
		FileAccess.open(path,FileAccess.WRITE).store_string(value+"\n")
		print("GENERATED_UID ",value)
	quit(0)
